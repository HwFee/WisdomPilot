"""
Judge0 代码执行服务。

本模块是 WisdomPilot 平台与 Judge0 在线评测引擎之间的「业务层」。
Judge0 是一个开源的在线代码评测系统，支持 60+ 种编程语言的编译和运行。

架构分层说明：
    judge0_client.py  -- 底层 HTTP 客户端：负责与 Judge0 REST API 通信
    judge0.py（本文件）-- 业务服务层：负责代码执行的判定逻辑、结果格式化

    这种分层使得业务逻辑（判定通过/失败、中文化错误消息）与网络通信
    （HTTP 请求、轮询、Base64 编解码）解耦，便于测试和维护。

在项目中的角色：
    训练舱（deck）模块中的「竞技场（Arena）」与「认证（certification）code 题」
    调用本服务来执行用户提交的代码，并根据执行结果判定是否通过测试用例。
"""

import httpx
from typing import Protocol

from app.services.judge0_client import Judge0Client

# Judge0 公共实例的 API 基地址
# 使用 Judge0 官方提供的免费公共 CE（Community Edition）实例
JUDGE0_BASE_URL = "https://ce.judge0.com"

# Judge0 用数字 ID 标识编程语言，以下是平台支持的常用语言映射
LANGUAGE_PYTHON = 71       # Python 3
LANGUAGE_JAVASCRIPT = 63   # Node.js
LANGUAGE_TYPESCRIPT = 74   # TypeScript
LANGUAGE_C = 50            # C (GCC 9.2)
LANGUAGE_CPP = 54          # C++ (GCC 9.2)
LANGUAGE_JAVA = 62         # Java (OpenJDK 13.0)
LANGUAGE_RUST = 73         # Rust (1.40)

# Judge0 的状态码及对应的中英文消息
# key: 状态码（整数）  value: (英文描述, 中文描述)
# 这些状态码是 Judge0 API 的标准定义，详见 Judge0 官方文档
STATUS_MESSAGES = {
    1: ("In Queue", "排队中"),                    # 提交后等待分配资源
    2: ("Processing", "处理中"),                  # 正在编译或运行
    3: ("Accepted", "✅ Accepted"),               # 运行成功，输出正确
    4: ("Wrong Answer", "❌ Wrong Answer"),       # 运行成功，但输出与预期不符
    5: ("Compilation Error", "⚠️ Compilation Error"),  # 编译失败
    6: ("Runtime Error (SIGSEGV)", "⚠️ Runtime Error"),   # 段错误（非法内存访问）
    7: ("Runtime Error (SIGXFSZ)", "⚠️ Runtime Error"),   # 文件大小超限
    8: ("Time Limit Exceeded", "🕛 Time Limit Exceeded"),  # 运行超时
    9: ("Memory Limit Exceeded", "💾 Memory Limit Exceeded"),  # 内存超限
    10: ("Runtime Error (SIGABRT)", "⚠️ Runtime Error"),  # 程序主动中止
    11: ("Runtime Error (NZEC)", "⚠️ Runtime Error"),     # 非零退出码
    12: ("Internal Error", "🔴 System Error"),    # Judge0 内部错误
    13: ("Executive Format Error", "🔴 Invalid Execution"),  # 可执行文件格式错误
}


class _Judge0Client(Protocol):
    """
    Judge0 客户端协议（Protocol）。

    Protocol 是 Python 的结构化子类型（Structural Subtyping）机制。
    它定义了一组方法签名，任何实现了这些方法的类都被视为符合此协议，
    无需显式继承。这类似于 Go 的接口或 TypeScript 的结构类型。

    设计意图：
        Judge0Service 依赖此协议而非具体的 Judge0Client 类，
        这样在单元测试中可以注入 Mock 对象，无需真实网络请求。
    """

    async def submit(
        self, code: str, language_id: int, stdin: str = "", expected_output: str = ""
    ) -> dict[str, object]: ...
    """提交单次代码执行请求并返回结果。"""

    async def submit_batch(
        self, code: str, language_id: int, test_cases: list[dict[str, str]]
    ) -> list[dict[str, object]]: ...
    """批量提交代码执行请求（多个测试用例）并返回结果列表。"""

    async def close(self) -> None: ...
    """关闭底层 HTTP 连接，释放资源。"""


class Judge0Service:
    """
    Judge0 代码执行业务服务。

    本类是业务层封装，负责：
    - 调用底层 Judge0Client 提交代码执行请求
    - 对执行结果进行判定（通过/失败/错误）
    - 将 Judge0 的原始响应转换为面向前端的友好格式（含中文消息）

    依赖注入:
        构造函数接受 _Judge0Client 协议（Protocol），默认使用 Judge0Client。
        在测试中可注入 Mock 对象，避免真实网络请求。

    属性:
        _client: 底层的 Judge0 客户端实例，负责 HTTP 通信
    """

    def __init__(self, client: _Judge0Client | None = None) -> None:
        """
        初始化 Judge0Service。

        Args:
            client: 可选的 Judge0 客户端实例。如果不提供，则自动创建
                    一个连接到公共 Judge0 实例的默认客户端。
        """
        # 如果外部未传入客户端，则使用默认配置创建一个
        self._client = client or Judge0Client(JUDGE0_BASE_URL)

    async def execute_code(
        self,
        code: str,
        language_id: int,
        stdin: str = "",
        poll_interval: float = 0.5,
        max_polls: int = 40,
    ) -> dict[str, object]:
        """
        执行单次代码并等待结果。

        将代码提交给 Judge0，使用 wait=true 参数让 Judge0 在服务端等待
        执行完成后直接返回结果，无需客户端轮询。

        Args:
            code: 用户提交的源代码
            language_id: 编程语言 ID（如 71 = Python 3）
            stdin: 标准输入内容（可选）
            poll_interval: 轮询间隔（已废弃，Judge0 的 wait 参数替代了轮询）
            max_polls: 最大轮询次数（已废弃，同上）

        Returns:
            Judge0 标准化后的执行结果字典，包含 status_id、stdout、stderr 等。
        """
        # poll_interval 和 max_polls 参数已不再使用（Judge0 的 wait=true 替代了轮询），
        # 用 del 显式标记这些参数被「有意忽略」，避免 linter 警告
        del poll_interval, max_polls
        # 直接委托给底层客户端提交，wait=true 会让 Judge0 阻塞直到执行完成
        return await self._client.submit(code, language_id, stdin)

    async def execute_batch(
        self,
        code: str,
        language_id: int,
        test_cases: list[dict],
    ) -> dict:
        """
        批量执行代码：用同一份代码运行多个测试用例。

        这是竞技场（Arena）功能的核心方法。用户的代码会针对所有测试用例
        分别运行，然后逐个判定通过/失败，最终汇总为整体结果。

        Args:
            code: 用户提交的源代码
            language_id: 编程语言 ID（如 50 = C, 71 = Python 3）
            test_cases: 测试用例列表，每个元素为
                {"input": str, "expected_output": str}

        Returns:
            包含整体状态和每个测试用例判定结果的字典，结构如下：
            {
                "token": str,           # Judge0 提交令牌
                "status_id": int,        # 整体状态码（3=全部通过, 4=有失败）
                "status": str,           # 状态文字（"Accepted" / "Wrong Answer"）
                "passed_count": int,     # 通过的测试用例数
                "total_count": int,      # 测试用例总数
                "results": list[dict],   # 每个测试用例的详细判定结果
                "time": str | None,      # 执行耗时（取第一个用例）
                "memory": str | None,    # 内存使用（取第一个用例）
                "message": str | None,   # 辅助消息（如 "通过 3/5 个测试点"）
            }
        """
        # 边界情况：没有测试用例时返回空结果
        if not test_cases:
            return {
                "token": "",
                "status_id": 13,
                "status": "No Test Cases",
                "passed_count": 0,
                "total_count": 0,
                "results": [],
            }

        # 调用底层客户端批量提交所有测试用例
        results = await self._client.submit_batch(code, language_id, test_cases)

        # 安全检查：确保返回的结果数量与提交的测试用例数量一致
        if len(results) < len(test_cases):
            raise httpx.RequestError(
                f"Judge0 batch result count mismatch: expected {len(test_cases)}, got {len(results)}"
            )

        processed_results = []  # 每个测试用例的判定结果
        passed_count = 0        # 通过的测试用例计数

        # 逐个处理测试用例结果：将 Judge0 原始结果转换为业务判定
        for result, tc in zip(results, test_cases):
            case_result = self._build_case_result(result, tc)
            processed_results.append(case_result)
            if case_result["passed"]:
                passed_count += 1

        # 汇总所有测试用例结果为整体响应
        return self._build_batch_response(
            results, test_cases, passed_count, processed_results
        )

    def _build_case_result(self, result: dict, tc: dict) -> dict:
        """
        根据 Judge0 返回的单个测试用例结果构建判定结果。

        判定逻辑：
        - 状态 3（Accepted）：代码运行成功，比对 actual vs expected 输出
          -- 输出完全匹配 → 通过（passed=True），消息 "通过"
          -- 输出不匹配 → 失败（passed=False），消息 "输出错误"
        - 状态 4（Wrong Answer）：Judge0 判定不通过（如果有 expected_output）
          -- 与 expected 比对不符，消息 "输出错误"
        - 其他状态：编译错误/运行错误/超时等
          -- 全部判定为失败，消息来自 _get_status_message 翻译

        注意：输出比对的空白处理由 Judge0Client 负责（客户端做 strip 比较），
        服务层不做额外处理。

        Args:
            result: Judge0 返回的单个测试用例原始结果
            tc: 对应的测试用例 {"input": str, "expected_output": str}

        Returns:
            标准化的判定结果字典：
            {
                "passed": bool,     # 是否通过
                "input": str,       # 测试用例输入
                "expected": str,    # 期望输出
                "actual": str,      # 实际输出
                "message": str,     # 中文判定消息
            }
        """
        # 获取 Judge0 执行状态码（已由底层客户端标准化为扁平字段 status_id）
        status_id = result.get("status_id", 13)
        # 获取期望输出和实际输出，strip() 去除首尾空白（容忍多余换行/空格）
        expected = tc.get("expected_output", "").strip()
        actual = (result.get("stdout") or "").strip()

        # 情况1：代码运行成功（Accepted, status_id=3）
        if status_id == 3:
            # 核心判定：实际输出是否与期望输出完全匹配
            passed = actual == expected
            return {
                "passed": passed,
                "input": tc.get("input", ""),
                "expected": expected,
                "actual": actual,
                "message": "通过" if passed else "输出错误",
            }

        # 情况2：Judge0 判定答案错误（Wrong Answer, status_id=4）
        if status_id == 4:
            return {
                "passed": False,
                "input": tc.get("input", ""),
                "expected": expected,
                "actual": actual,
                "message": "输出错误",
            }

        # 情况3：其他所有错误状态（编译错误/运行时错误/超时/内存超限等）
        # 优先获取编译错误信息，其次获取标准错误输出
        error_detail = result.get("compile_output") or result.get("stderr") or ""
        # 将状态码翻译为中文错误消息
        error_msg = self._get_status_message(status_id, error_detail)
        return {
            "passed": False,
            "input": tc.get("input", ""),
            "expected": expected,
            "actual": "",
            "message": error_msg,
        }

    def _build_batch_response(
        self,
        results: list[dict],
        test_cases: list[dict],
        passed_count: int,
        processed_results: list[dict],
    ) -> dict:
        """
        汇总所有测试用例的判定结果为整体响应。

        计算整体通过状态：只有当所有测试用例都通过时，整体才判定为 Accepted。

        Args:
            results: Judge0 返回的原始结果列表
            test_cases: 测试用例列表
            passed_count: 通过的测试用例数量
            processed_results: 处理后的每个测试用例判定结果列表

        Returns:
            结构化的整体响应字典，包含整体状态、时间消耗、内存使用、
            通过数量/总数、每用例结果和提示消息。
        """
        # 全部通过：所有测试用例状态都是 passed=True
        all_passed = passed_count == len(test_cases)
        overall_status = "Accepted" if all_passed else "Wrong Answer"
        overall_status_id = 3 if all_passed else 4

        return {
            # 从第一个结果取 token（所有提交继承同一个 token）
            "token": results[0].get("token", "") if results else "",
            "status_id": overall_status_id,
            "status": overall_status,
            "passed_count": passed_count,
            "total_count": len(test_cases),
            "results": processed_results,
            # 时间和内存取第一个用例的数据（参考值）
            "time": results[0].get("time") if results else None,
            "memory": results[0].get("memory") if results else None,
            # compile_output 仅对单次执行有意义，批次结果中置为 None
            "compile_output": None,
            # 未全部通过时，显示进度提示（如 "通过 3/5 个测试点"）
            "message": f"通过 {passed_count}/{len(test_cases)} 个测试点"
            if not all_passed
            else None,
        }

    def _get_status_message(self, status_id: int, detail: str = "") -> str:
        """
        获取面向用户的中文状态消息。

        根据 Judge0 返回的状态码，从 STATUS_MESSAGES 字典查找对应的
        中文描述。对于编译错误和运行时错误，会附加错误详情的前若干字符。

        Args:
            status_id: Judge0 状态码（1-13）
            detail: 错误详细信息（如编译器输出或标准错误输出）

        Returns:
            中文状态描述字符串。对于已知状态码返回中文翻译；
            对于未知状态码返回 "执行错误 (status=N)"。

        截断策略：
            - 编译错误（status=5）：显示前 200 字符
            - 运行时错误（status=6,7,10,11）：显示前 100 字符
            - 截断是为了防止超长错误输出（如大段堆栈追踪）塞满前端界面
        """
        if status_id in STATUS_MESSAGES:
            # 取中文描述（索引 1）
            msg = STATUS_MESSAGES[status_id][1]  # Chinese message
            # 编译错误：附加编译输出摘要，帮助用户排查语法问题
            if status_id == 5 and detail:
                return f"{msg}: {detail[:200]}"
            # 运行时错误：附加错误输出摘要
            if status_id in (6, 7, 10, 11) and detail:
                return f"{msg}: {detail[:100]}"
            return msg
        return f"执行错误 (status={status_id})"

    def parse_status(self, status_id: int) -> tuple[str, str]:
        """
        解析状态码为 (英文, 中英混合) 消息对。

        用于需要同时展示英文状态码含义和中英双语说明的场景。

        Args:
            status_id: Judge0 状态码（1-13）

        Returns:
            (english_message, formatted_message) 元组。
            例如状态 3 返回 ("Accepted", "Accepted - ✅ Accepted")
        """
        if status_id in STATUS_MESSAGES:
            eng, chn = STATUS_MESSAGES[status_id]
            return eng, f"{eng} - {chn}"
        return f"Unknown ({status_id})", f"❓ Unknown Error ({status_id})"

    def format_output(self, result: dict) -> dict:
        """
        格式化单次代码执行结果为前端友好的结构。

        将 Judge0 的原始响应字段提取出来，附加状态解析和中文化错误消息，
        便于前端直接渲染。

        Args:
            result: Judge0 返回的原始执行结果字典

        Returns:
            格式化后的结果字典，额外包含：
            - formatted_status：中英混合状态描述
            - message：面向用户的中文错误提示

        消息生成规则（按状态码）：
            - 3 (Accepted)：无消息（运行成功）
            - 4 (Wrong Answer)：答案错误
            - 5 (Compilation Error)：编译错误 + 编译输出
            - 6/7/10/11 (Runtime Error)：运行时错误 + 标准错误输出
            - 8 (TLE)：运行超时，可能存在无限循环
            - 9 (MLE)：内存超限，建议优化算法
            - 12 (Internal Error)：Judge0 系统错误
            - 13 (Format Error)：执行格式错误
        """
        status_id = result.get("status_id", 13)  # 默认 13：状态码缺失时按「执行格式错误」兜底处理
        eng_status, formatted_status = self.parse_status(status_id)

        # 提取并标准化各字段
        formatted_result = {
            "token": result.get("token", ""),
            "status_id": status_id,
            "status": eng_status,           # 英文状态
            "formatted_status": formatted_status,  # 中英混合状态
            "stdout": result.get("stdout"),
            "stderr": result.get("stderr"),
            "compile_output": result.get("compile_output"),
            "time": result.get("time"),
            "memory": result.get("memory"),
            "exit_code": result.get("exit_code"),
        }

        # 根据状态码生成面向用户的中文消息
        message = None
        if status_id == 3:
            # Accepted：不需要额外消息
            message = None
        elif status_id == 4:
            # 运行成功但输出与预期不符，直接点明答案错误
            message = "答案错误"
        elif status_id == 5:
            compile_output = result.get("compile_output")
            # 附上编译器输出摘要，帮助用户定位语法/类型错误
            message = "编译错误: " + compile_output if compile_output else "编译错误"
        elif status_id == 8:
            # TLE 的最常见诱因是死循环，给出可操作提示比原始状态码更易理解
            message = "运行超时，您的程序可能在无限循环"
        elif status_id == 9:
            # MLE：提示用户优化算法空间复杂度
            message = "内存超限，请优化算法"
        elif status_id in (6, 7, 10, 11):
            stderr = result.get("stderr")
            # 运行时错误种类较多，附上 stderr 让用户看到具体异常信息
            message = "运行时错误: " + stderr if stderr else "运行时错误"
        elif status_id == 12:
            # Judge0 服务端内部故障，与用户代码无关，提示重试即可
            message = "Judge0 系统错误"
        elif status_id == 13:
            message = "执行格式错误"
        else:
            # 兜底分支：未知状态码也给出可读消息，避免前端拿到空提示
            message = f"未知错误 (status_id={status_id})"

        formatted_result["message"] = message
        return formatted_result

    async def close(self) -> None:
        """关闭底层的 Judge0 客户端连接，释放 HTTP 资源。"""
        await self._client.close()

"""
Judge0 API 客户端（底层 HTTP 通信层）。

本模块是 WisdomPilot 平台与 Judge0 REST API 之间的「传输层」客户端。
所有与 Judge0 服务器的 HTTP 通信细节都封装在此：
    - 请求构建（Base64 编码源代码和输入）
    - 提交单个/批量执行请求
    - 轮询执行结果（Judge0 是异步的，提交后需要轮询获取结果）
    - 响应解码（Base64 解码输出内容）

与 judge0.py（业务服务层）的关系：
    本模块只关心「如何与 Judge0 服务器通信」，不关心「判定是否通过」。
    判定逻辑（如输出比对）由上层的 Judge0Service 负责。

Base64 编码说明：
    Judge0 API 要求源代码、标准输入、标准输出等字段使用 Base64 编码传输，
    以避免特殊字符（如换行符、Unicode）导致 JSON 解析问题。
"""

import asyncio
import base64

import httpx

# === Judge0 客户端配置常量 ===

# HTTP 请求超时时间（秒）--包括连接、读取、写入超时
JUDGE0_TIMEOUT_SECONDS = 60.0
# CPU 时间限制（秒）--用户代码的最大 CPU 运行时间，超时则判定 TLE
JUDGE0_CPU_TIME_LIMIT_SECONDS = 10
# 内存限制（KB）--用户代码可使用的最大内存，超限则判定 MLE
# 256_000 KB = 256 MB
JUDGE0_MEMORY_LIMIT_KILOBYTES = 256_000
# Judge0 的「等待中」状态码集合--状态 1(排队) 和 2(处理中) 表示尚未完成
JUDGE0_PENDING_STATUS_IDS = frozenset({1, 2})
# 轮询最大尝试次数--超过此次数仍未完成则判定为超时
JUDGE0_POLL_ATTEMPTS = 20
# 每次轮询之间的间隔时间（秒）--避免过于频繁地请求 API
JUDGE0_POLL_INTERVAL_SECONDS = 0.3


class Judge0Client:
    """
    Judge0 API 的异步 HTTP 客户端。

    职责：
        - 构建 Judge0 API 请求（Base64 编码、构造 payload）
        - 发送 HTTP 请求（单次提交、批量提交）
        - 轮询执行结果直到完成或超时
        - 解码响应中的 Base64 字段

    属性:
        _base_url (str): Judge0 API 的基地址（已去除尾部斜杠）
        _client (httpx.AsyncClient | None): httpx 异步 HTTP 客户端实例
        _owns_client (bool): 是否由本实例创建并拥有 HTTP 客户端
            （如果外部传入客户端，则本实例不负责关闭它）

    设计意图:
        支持依赖注入--外部可传入自定义的 httpx.AsyncClient（如用于测试），
        也可让本类自行创建和管理客户端实例。
    """

    def __init__(self, base_url: str, client: httpx.AsyncClient | None = None) -> None:
        # 去除尾部斜杠，避免拼接 URL 时出现双斜杠（如 "https://x.com//submissions"）
        self._base_url = base_url.rstrip("/")
        self._client = client
        # 记录是否由本实例自行创建客户端，用于决定是否在 close() 时关闭它
        self._owns_client = client is None

    def _get_client(self) -> httpx.AsyncClient:
        """惰性初始化 httpx 异步客户端。如果尚未创建，则创建一个新实例。"""
        if self._client is None:
            # 创建带超时配置的异步客户端
            self._client = httpx.AsyncClient(timeout=JUDGE0_TIMEOUT_SECONDS)
        return self._client

    def _encode_text(self, text: str) -> str:
        """
        将文本编码为 Base64 字符串。

        Judge0 API 要求源代码、标准输入等字段使用 Base64 编码传输，
        以确保特殊字符（换行、Unicode、二进制数据）不会破坏 JSON 结构。

        编码流程: 文本 -> UTF-8 字节 -> Base64 字节 -> ASCII 字符串
        """
        return base64.b64encode(text.encode()).decode()

    def _submission_payload(
        self, code: str, language_id: int, stdin: str, expected_output: str
    ) -> dict[str, object]:
        """
        构建 Judge0 提交请求的 JSON payload。

        Args:
            code: 用户提交的源代码
            language_id: 编程语言 ID（如 71 = Python 3）
            stdin: 标准输入内容（测试用例的输入数据）
            expected_output: 期望的标准输出（可选，用于 Judge0 端判定）

        Returns:
            符合 Judge0 API 规范的字典，包含编码后的源代码、输入、资源限制等。
        """
        payload: dict[str, object] = {
            "source_code": self._encode_text(code),   # 源代码（Base64 编码）
            "language_id": language_id,                # 编程语言 ID
            "stdin": self._encode_text(stdin),         # 标准输入（Base64 编码）
            "cpu_time_limit": JUDGE0_CPU_TIME_LIMIT_SECONDS,    # CPU 时间上限
            "memory_limit": JUDGE0_MEMORY_LIMIT_KILOBYTES,       # 内存上限
        }
        # 仅当提供了期望输出时才加入 payload
        # 注意：实际项目中，输出比对由 Judge0Service 负责，这里通常不传 expected_output
        if expected_output:
            payload["expected_output"] = self._encode_text(expected_output)
        return payload

    def _status_id(self, result: dict) -> int:
        """
        从 Judge0 响应中提取状态码。

        Judge0 API 的状态可能出现在两种位置：
        - result["status"]["id"]（嵌套对象格式，较新版本）
        - result["status_id"]（扁平格式，兼容旧版本）

        默认返回 13（执行格式错误），表示无法识别状态。
        """
        status = result.get("status")
        if isinstance(status, dict):
            return int(status.get("id", 13))
        return int(result.get("status_id", 13))

    def _decode_output_fields(self, result: dict) -> dict:
        """
        解码响应中的 Base64 编码字段。

        Judge0 返回的 stdout（标准输出）、stderr（标准错误）、
        compile_output（编译输出）都是 Base64 编码的，需要解码为明文。

        解码是原地修改 result 字典并返回。
        """
        for field in ("stdout", "stderr", "compile_output"):
            value = result.get(field)
            # 仅解码非空字符串值
            if value and isinstance(value, str):
                result[field] = base64.b64decode(value).decode()
        return result

    def _normalize_result(self, result: dict) -> dict[str, object]:
        """
        标准化 Judge0 响应：解码 Base64 字段 + 提取状态码。

        将原始 API 响应转换为统一的内部格式，方便上层业务逻辑使用。
        """
        # 先复制一份再解码，避免修改原始数据
        result = self._decode_output_fields(dict(result))
        # 统一状态码字段为 status_id（扁平格式）
        result["status_id"] = self._status_id(result)
        return result

    async def submit(
        self, code: str, language_id: int, stdin: str = "", expected_output: str = ""
    ) -> dict[str, object]:
        """
        提交单次代码执行请求（同步等待模式）。

        使用 Judge0 的 wait=true 参数，提交后服务端会阻塞直到执行完成，
        然后直接返回完整结果，无需客户端轮询。

        Args:
            code: 用户提交的源代码
            language_id: 编程语言 ID
            stdin: 标准输入内容（可选）
            expected_output: 期望输出（可选，用于 Judge0 端判定）

        Returns:
            标准化后的执行结果字典
        """
        response = await self._get_client().post(
            f"{self._base_url}/submissions",
            # base64_encoded=true 告诉 Judge0 请求体中的字段是 Base64 编码的
            # wait=true 让 Judge0 同步等待执行完成后再返回（而非立即返回 token）
            params={"base64_encoded": "true", "wait": "true"},
            json=self._submission_payload(code, language_id, stdin, expected_output),
        )
        # 如果 HTTP 状态码不是 2xx，抛出异常
        response.raise_for_status()
        # 标准化响应（解码 Base64 字段 + 提取状态码）
        return self._normalize_result(response.json())

    async def _poll_submission(self, token: str) -> dict:
        """
        轮询单次提交的执行结果。

        批量提交时 Judge0 不会同步等待，而是返回 token。客户端需要
        用 token 反复查询，直到状态不再是「排队中」或「处理中」。

        Args:
            token: Judge0 返回的提交令牌

        Returns:
            执行结果字典。如果轮询超时，会返回最后一次获取的结果并附加
            "Polling timeout" 消息。
        """
        client = self._get_client()
        last_result: dict | None = None  # 保存最后一次获取的结果（用于超时返回）

        for attempt in range(JUDGE0_POLL_ATTEMPTS):
            # 用 token 查询提交状态
            response = await client.get(
                f"{self._base_url}/submissions/{token}",
                params={"base64_encoded": "true"},
            )
            response.raise_for_status()
            result = self._normalize_result(response.json())
            last_result = result

            # 如果状态不再是「排队中(1)」或「处理中(2)」，说明执行已完成
            if result["status_id"] not in JUDGE0_PENDING_STATUS_IDS:
                return result

            # 如果不是最后一次尝试，则等待间隔后再次轮询
            if attempt < JUDGE0_POLL_ATTEMPTS - 1:
                await asyncio.sleep(JUDGE0_POLL_INTERVAL_SECONDS)

        # 轮询超时：返回最后一次获取的结果，并标记超时
        if last_result is not None:
            last_result["message"] = "Polling timeout"
            return last_result
        # 理论上不会走到这里，但作为防御性编程返回错误状态
        return {"status_id": 13, "message": "Invalid token"}

    async def submit_batch(
        self, code: str, language_id: int, test_cases: list[dict[str, str]]
    ) -> list[dict[str, object]]:
        """
        批量提交代码执行请求。

        将同一份代码针对多个测试用例分别提交到 Judge0 的批量 API。
        Judge0 会为每个测试用例返回一个 token，随后需要逐个轮询获取结果。

        注意：expected_output 不传给 Judge0，输出比对由上层 Judge0Service
        负责（支持空白容忍等自定义判定逻辑）。

        Args:
            code: 用户提交的源代码
            language_id: 编程语言 ID
            test_cases: 测试用例列表，每个元素为 {"input": str, "expected_output": str}

        Returns:
            每个测试用例的执行结果列表，顺序与 test_cases 一一对应。
        """
        # 为每个测试用例构建提交 payload
        # 注意：expected_output 传空字符串 -- 判定逻辑由 Judge0Service 负责
        submissions = [
            self._submission_payload(
                code, language_id, tc.get("input", ""), ""
            )
            for tc in test_cases
        ]

        # 调用 Judge0 批量提交 API
        response = await self._get_client().post(
            f"{self._base_url}/submissions/batch",
            params={"base64_encoded": "true"},
            json={"submissions": submissions},
        )
        response.raise_for_status()
        tokens_data = response.json()

        # Judge0 批量 API 的响应格式可能是列表或包含 "submissions" 键的对象
        # 两种格式都兼容处理
        if isinstance(tokens_data, list):
            tokens = [item.get("token") for item in tokens_data]
        else:
            tokens = [item.get("token") for item in tokens_data.get("submissions", [])]

        if not tokens:
            return []

        # 并发轮询所有 token 的执行结果
        return await self._poll_tokens(tokens)

    async def _poll_tokens(self, tokens: list[str | None]) -> list[dict[str, object]]:
        """
        并发轮询多个 token 的执行结果。

        使用 asyncio.create_task 为每个 token 创建独立的轮询任务，
        所有任务并发执行，大幅缩短批量执行的总体等待时间。

        错误处理策略：
        - 如果任意一个任务抛出异常，立即取消所有未完成的任务
        - 最终无论成功还是失败，都会清理所有任务，防止资源泄漏

        Args:
            tokens: Judge0 返回的 token 列表，可能包含 None（表示无效提交）

        Returns:
            所有 token 对应的执行结果列表，顺序与 tokens 一一对应。
        """
        # 为每个 token 创建轮询协程
        # 如果 token 为 None，直接返回无效结果，不发起网络请求
        coros = [
            self._poll_submission(token) if token else self._invalid_token_result()
            for token in tokens
        ]
        # 将协程包装为 asyncio Task，使其在事件循环中并发执行
        tasks = [asyncio.create_task(coro) for coro in coros]
        try:
            # return_when=FIRST_EXCEPTION：任意一个任务失败就立即返回
            done, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_EXCEPTION
            )
            # 检查已完成的任务中是否有异常
            first_exception: BaseException | None = None
            for task in done:
                exc = task.exception()
                if exc is not None:
                    first_exception = exc
                    break
            # 如果有异常，取消所有待处理的任务并重新抛出异常
            if first_exception is not None:
                for task in pending:
                    task.cancel()
                # 等待被取消的任务完成清理（忽略 CancelledError）
                await asyncio.gather(*pending, return_exceptions=True)
                raise first_exception
            # 如果还有待处理的任务（没有异常但还有未完成的），等待它们完成
            if pending:
                await asyncio.gather(*pending)
            # 按原顺序收集所有结果
            return [task.result() for task in tasks]
        finally:
            # 确保所有任务都被清理：取消任何尚未完成的任务
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _invalid_token_result(self) -> dict[str, object]:
        """
        返回无效 token 对应的结果。

        当批量提交中某个测试用例返回的 token 为空时，使用此占位结果，
        不影响其他正常测试用例的轮询。
        """
        return {"status_id": 13, "message": "Invalid token"}

    async def close(self) -> None:
        """
        关闭底层 HTTP 连接，释放资源。

        仅当本实例自行创建了 HTTP 客户端时（_owns_client=True）才执行关闭。
        如果客户端是外部注入的，则由调用者负责管理其生命周期。
        """
        if self._owns_client and self._client is not None:
            # aclose() 是 httpx.AsyncClient 的异步关闭方法
            await self._client.aclose()
            self._client = None

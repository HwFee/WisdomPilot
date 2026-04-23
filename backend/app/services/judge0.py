"""Judge0 API service for code execution"""

import httpx
import asyncio
import base64
import logging

# Judge0 API configuration
JUDGE0_BASE_URL = "https://ce.judge0.com"

# Language IDs
LANGUAGE_PYTHON = 71
LANGUAGE_JAVASCRIPT = 63
LANGUAGE_TYPESCRIPT = 74
LANGUAGE_C = 50
LANGUAGE_CPP = 54

# Status code meanings
STATUS_MESSAGES = {
    1: ("In Queue", "排队中"),
    2: ("Processing", "处理中"),
    3: ("Accepted", "✅ Accepted"),
    4: ("Wrong Answer", "❌ Wrong Answer"),
    5: ("Compilation Error", "⚠️ Compilation Error"),
    6: ("Runtime Error (SIGSEGV)", "⚠️ Runtime Error"),
    7: ("Runtime Error (SIGXFSZ)", "⚠️ Runtime Error"),
    8: ("Time Limit Exceeded", "🕛 Time Limit Exceeded"),
    9: ("Memory Limit Exceeded", "💾 Memory Limit Exceeded"),
    10: ("Runtime Error (SIGABRT)", "⚠️ Runtime Error"),
    11: ("Runtime Error (NZEC)", "⚠️ Runtime Error"),
    12: ("Internal Error", "🔴 System Error"),
    13: ("Executive Format Error", "🔴 Invalid Execution"),
}


class Judge0Service:
    """Service for interacting with Judge0 API"""

    def __init__(self):
        self.base_url = JUDGE0_BASE_URL
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazily initialized HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    async def create_submission(
        self,
        code: str,
        language_id: int,
        stdin: str = "",
        expected_output: str = "",
        wait: bool = False,
    ) -> dict:
        """Create a new code submission with base64 encoding."""
        # Judge0 需要 base64 编码来正确处理非 ASCII 字符
        payload = {
            "source_code": base64.b64encode(code.encode()).decode(),
            "language_id": language_id,
            "stdin": base64.b64encode(stdin.encode()).decode(),
            "cpu_time_limit": 10,
            "memory_limit": 256000,
        }

        # 如果有期望输出，也添加
        if expected_output:
            payload["expected_output"] = base64.b64encode(expected_output.encode()).decode()

        url = f"{self.base_url}/submissions"
        # 使用 base64_encoded=true
        url += "?base64_encoded=true&wait=true"

        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        result = response.json()

        # 解码输出
        if result.get("stdout"):
            result["stdout"] = base64.b64decode(result["stdout"]).decode()
        if result.get("stderr"):
            result["stderr"] = base64.b64decode(result["stderr"]).decode()
        if result.get("compile_output"):
            result["compile_output"] = base64.b64decode(result["compile_output"]).decode()

        return result

    async def create_batch_submissions(
        self,
        code: str,
        language_id: int,
        test_cases: list[dict],
    ) -> list[dict]:
        """
        Create multiple submissions in a single batch request.

        Uses Judge0's /submissions/batch endpoint to create multiple
        submissions at once, then waits for all to complete.

        Args:
            code: Source code to execute
            language_id: Language ID
            test_cases: List of {"input": str, "expected_output": str}

        Returns:
            List of submission results (in same order as test_cases)
        """
        # 构建批量提交请求
        submissions = []
        for tc in test_cases:
            submissions.append({
                "source_code": base64.b64encode(code.encode()).decode(),
                "language_id": language_id,
                "stdin": base64.b64encode(tc.get("input", "").encode()).decode(),
                "cpu_time_limit": 10,
                "memory_limit": 256000,
            })

        # 使用批量创建端点
        url = f"{self.base_url}/submissions/batch?base64_encoded=true"

        logger.info(f"[Judge0] Creating batch submissions: {len(submissions)} test cases")
        logger.info(f"[Judge0] URL: {url}")

        try:
            response = await self.client.post(url, json={"submissions": submissions})
            logger.info(f"[Judge0] Batch create response status: {response.status_code}")
            response.raise_for_status()
            tokens_data = response.json()
            logger.info(f"[Judge0] Batch create response: {str(tokens_data)[:200]}")
        except Exception as e:
            logger.error(f"[Judge0] Batch create FAILED: {e}")
            raise

        # Judge0 CE 直接返回列表，不是 {"submissions": [...]}
        if isinstance(tokens_data, list):
            tokens = [item.get("token") for item in tokens_data]
        else:
            tokens = [item.get("token") for item in tokens_data.get("submissions", [])]

        if not tokens:
            return []

        # 等待所有 submission 完成
        # Judge0 批量获取结果，需要轮询直到完成
        results = []
        for token in tokens:
            if not token:
                results.append({"status_id": 13, "message": "Invalid token"})
                continue

            # 轮询获取结果，直到完成或超时
            max_attempts = 20
            result = None
            for attempt in range(max_attempts):
                get_url = f"{self.base_url}/submissions/{token}?base64_encoded=true&wait=true"
                get_response = await self.client.get(get_url)
                get_response.raise_for_status()
                result = get_response.json()

                # 提取 status_id
                if "status" in result and isinstance(result["status"], dict):
                    status_id = result["status"].get("id", 13)
                else:
                    status_id = result.get("status_id", 13)

                # status_id <= 2 表示还在队列或处理中
                if status_id > 2:
                    break

                # 等待一小段时间再重试
                await asyncio.sleep(0.3)

            # 解码输出
            if result.get("stdout"):
                result["stdout"] = base64.b64decode(result["stdout"]).decode()
            if result.get("stderr"):
                result["stderr"] = base64.b64decode(result["stderr"]).decode()
            if result.get("compile_output"):
                result["compile_output"] = base64.b64decode(result["compile_output"]).decode()

            # 提取 status_id
            if "status" in result and isinstance(result["status"], dict):
                result["status_id"] = result["status"].get("id", 13)
            elif "status_id" not in result:
                result["status_id"] = 13

            results.append(result)

        return results

    async def get_submission(self, token: str) -> dict:
        """Get submission result by token"""
        url = f"{self.base_url}/submissions/{token}?base64_encoded=false"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    async def execute_code(
        self,
        code: str,
        language_id: int,
        stdin: str = "",
        poll_interval: float = 0.5,
        max_polls: int = 40,
    ) -> dict:
        """Execute code and wait for result."""
        result = await self.create_submission(code, language_id, stdin, wait=True)
        if "status" in result and isinstance(result["status"], dict):
            result["status_id"] = result["status"].get("id", 13)
        elif "status_id" not in result:
            result["status_id"] = 13
        return result

    async def execute_batch(
        self,
        code: str,
        language_id: int,
        test_cases: list[dict],
    ) -> dict:
        """
        Execute code against multiple test cases using Judge0 batch API.

        Uses the official /submissions/batch endpoint to create multiple
        independent submissions in one request. Each test case runs
        independently with its own stdin.

        Args:
            code: Source code to execute
            language_id: Language ID (e.g., 50 for C, 71 for Python)
            test_cases: List of {"input": str, "expected_output": str}

        Returns:
            dict with overall status and per-test-case results
        """
        if not test_cases:
            return {
                "token": "",
                "status_id": 13,
                "status": "No Test Cases",
                "passed_count": 0,
                "total_count": 0,
                "results": [],
            }

        # 使用 Judge0 批量提交 API
        try:
            results = await self.create_batch_submissions(
                code=code,
                language_id=language_id,
                test_cases=test_cases,
            )
        except Exception as e:
            # 如果批量提交失败，返回错误
            import traceback
            error_detail = traceback.format_exc()
            logger.error(f"Judge0 batch execution error: {error_detail}")
            return {
                "token": "",
                "status_id": 13,
                "status": "Batch Execution Failed",
                "passed_count": 0,
                "total_count": len(test_cases),
                "results": [],
                "message": f"批量执行失败: {str(e)}",
            }

        # 处理每个测试用例的结果
        processed_results = []
        passed_count = 0

        for i, (result, tc) in enumerate(zip(results, test_cases)):
            status_id = result.get("status_id", 13)
            expected = tc.get("expected_output", "").strip()
            actual = (result.get("stdout") or "").strip()

            # 编译错误或运行时错误
            if status_id != 3:
                error_msg = self._get_status_message(
                    status_id,
                    result.get("compile_output") or result.get("stderr") or ""
                )
                processed_results.append({
                    "passed": False,
                    "input": tc.get("input", ""),
                    "expected": expected,
                    "actual": "",
                    "message": error_msg,
                })
                continue

            # 检查输出是否匹配
            passed = actual == expected
            if passed:
                passed_count += 1

            processed_results.append({
                "passed": passed,
                "input": tc.get("input", ""),
                "expected": expected,
                "actual": actual,
                "message": "通过" if passed else "输出错误",
            })

        # 计算总体状态
        all_passed = passed_count == len(test_cases)
        overall_status = "Accepted" if all_passed else "Wrong Answer"
        overall_status_id = 3 if all_passed else 4

        return {
            "token": results[0].get("token", "") if results else "",
            "status_id": overall_status_id,
            "status": overall_status,
            "passed_count": passed_count,
            "total_count": len(test_cases),
            "results": processed_results,
            "time": results[0].get("time") if results else None,
            "memory": results[0].get("memory") if results else None,
            "compile_output": None,
            "message": f"通过 {passed_count}/{len(test_cases)} 个测试点" if not all_passed else None,
        }

    def _get_status_message(self, status_id: int, detail: str = "") -> str:
        """Get human-readable status message."""
        if status_id in STATUS_MESSAGES:
            msg = STATUS_MESSAGES[status_id][1]  # Chinese message
            # Append detail for compilation/runtime errors
            if status_id == 5 and detail:
                return f"{msg}: {detail[:200]}"
            if status_id in (6, 7, 10, 11) and detail:
                return f"{msg}: {detail[:100]}"
            return msg
        return f"执行错误 (status={status_id})"

    def parse_status(self, status_id: int) -> tuple[str, str]:
        """Parse status ID to (english, chinese) message."""
        if status_id in STATUS_MESSAGES:
            eng, chn = STATUS_MESSAGES[status_id]
            return eng, f"{eng} - {chn}"
        return f"Unknown ({status_id})", f"❓ Unknown Error ({status_id})"

    def format_output(self, result: dict) -> dict:
        """Format execution result with status and message."""
        status_id = result.get("status_id", 13)
        eng_status, formatted_status = self.parse_status(status_id)

        formatted_result = {
            "token": result.get("token", ""),
            "status_id": status_id,
            "status": eng_status,
            "formatted_status": formatted_status,
            "stdout": result.get("stdout"),
            "stderr": result.get("stderr"),
            "compile_output": result.get("compile_output"),
            "time": result.get("time"),
            "memory": result.get("memory"),
            "exit_code": result.get("exit_code"),
        }

        message = None
        if status_id == 3:
            message = None
        elif status_id == 4:
            message = "答案错误"
        elif status_id == 5:
            compile_output = result.get("compile_output")
            message = "编译错误: " + compile_output if compile_output else "编译错误"
        elif status_id == 8:
            message = "运行超时，您的程序可能在无限循环"
        elif status_id == 9:
            message = "内存超限，请优化算法"
        elif status_id in (6, 7, 10, 11):
            stderr = result.get("stderr")
            message = "运行时错误: " + stderr if stderr else "运行时错误"
        elif status_id == 12:
            message = "Judge0 系统错误"
        elif status_id == 13:
            message = "执行格式错误"
        else:
            message = f"未知错误 (status_id={status_id})"

        formatted_result["message"] = message
        return formatted_result

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self.client.aclose()
            self._client = None


logger = logging.getLogger(__name__)
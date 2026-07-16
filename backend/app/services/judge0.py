"""Judge0 API service for code execution"""

import httpx
from typing import Protocol

from app.services.judge0_client import Judge0Client

# Judge0 API configuration
JUDGE0_BASE_URL = "https://ce.judge0.com"

# Language IDs
LANGUAGE_PYTHON = 71
LANGUAGE_JAVASCRIPT = 63
LANGUAGE_TYPESCRIPT = 74
LANGUAGE_C = 50
LANGUAGE_CPP = 54
LANGUAGE_JAVA = 62
LANGUAGE_RUST = 73

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


class _Judge0Client(Protocol):
    async def submit(
        self, code: str, language_id: int, stdin: str = "", expected_output: str = ""
    ) -> dict[str, object]: ...

    async def submit_batch(
        self, code: str, language_id: int, test_cases: list[dict[str, str]]
    ) -> list[dict[str, object]]: ...

    async def close(self) -> None: ...


class Judge0Service:
    """Service for interacting with Judge0 API"""

    def __init__(self, client: _Judge0Client | None = None) -> None:
        self._client = client or Judge0Client(JUDGE0_BASE_URL)

    async def execute_code(
        self,
        code: str,
        language_id: int,
        stdin: str = "",
        poll_interval: float = 0.5,
        max_polls: int = 40,
    ) -> dict[str, object]:
        """Execute code and wait for result."""
        del poll_interval, max_polls
        return await self._client.submit(code, language_id, stdin)

    async def execute_batch(
        self,
        code: str,
        language_id: int,
        test_cases: list[dict],
    ) -> dict:
        """
        Execute code against multiple test cases using Judge0 batch API.

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

        results = await self._client.submit_batch(code, language_id, test_cases)

        if len(results) < len(test_cases):
            raise httpx.RequestError(
                f"Judge0 batch result count mismatch: expected {len(test_cases)}, got {len(results)}"
            )

        processed_results = []
        passed_count = 0

        for result, tc in zip(results, test_cases):
            case_result = self._build_case_result(result, tc)
            processed_results.append(case_result)
            if case_result["passed"]:
                passed_count += 1

        return self._build_batch_response(
            results, test_cases, passed_count, processed_results
        )

    def _build_case_result(self, result: dict, tc: dict) -> dict:
        """Build a single test-case verdict from a Judge0 result."""
        status_id = result.get("status_id", 13)
        expected = tc.get("expected_output", "").strip()
        actual = (result.get("stdout") or "").strip()

        if status_id == 3:
            passed = actual == expected
            return {
                "passed": passed,
                "input": tc.get("input", ""),
                "expected": expected,
                "actual": actual,
                "message": "通过" if passed else "输出错误",
            }

        if status_id == 4:
            return {
                "passed": False,
                "input": tc.get("input", ""),
                "expected": expected,
                "actual": actual,
                "message": "输出错误",
            }

        error_detail = result.get("compile_output") or result.get("stderr") or ""
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
        """Aggregate individual case results into the overall batch response."""
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
            "message": f"通过 {passed_count}/{len(test_cases)} 个测试点"
            if not all_passed
            else None,
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

    async def close(self) -> None:
        """Close the underlying Judge0 client."""
        await self._client.close()

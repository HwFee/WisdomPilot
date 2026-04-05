"""Judge0 API service for code execution"""

import httpx
import asyncio
from typing import Optional

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
        wait: bool = False,
    ) -> dict:
        """Create a new code submission."""
        payload = {
            "source_code": code,
            "language_id": language_id,
            "stdin": stdin,
            "cpu_time_limit": 10,
            "memory_limit": 256000,
        }

        url = f"{self.base_url}/submissions"
        if wait:
            url += "?base64_encoded=false&wait=true"
        else:
            url += "?base64_encoded=false"

        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

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

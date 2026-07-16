"""
Tests for Code Execution API (Judge0 Integration)

Covers:
- POST /api/code/execute - Single code execution
- POST /api/code/execute-batch - Batch test case execution
- GET /api/code/languages - Supported languages

Mocks Judge0 API to avoid external dependencies during testing.
"""

import httpx
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import contextmanager

from app.routers.code import get_judge0_service
import app.routers.code as code_router
from app.services.judge0 import Judge0Service
from app.main import app


class FakeJudge0ClientRaisingRequestError:
    """Simulates a Judge0 client that fails at the transport layer."""

    async def submit(
        self, code: str, language_id: int, stdin: str = "", expected_output: str = ""
    ) -> dict[str, object]:
        raise httpx.RequestError("Connection refused")

    async def submit_batch(
        self, code: str, language_id: int, test_cases: list[dict[str, str]]
    ) -> list[dict[str, object]]:
        raise httpx.RequestError("Connection refused")

    async def close(self) -> None:
        pass


def _http_status_error(status_code: int) -> httpx.HTTPStatusError:
    """Build an httpx.HTTPStatusError with the given status code."""
    request = httpx.Request("POST", "https://judge0.example.com")
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError("Judge0 error", request=request, response=response)


@contextmanager
def override_judge0_service(mock_service):
    """Temporarily override the Judge0 service dependency for tests."""
    app.dependency_overrides[get_judge0_service] = lambda: mock_service
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_judge0_service, None)


class TestCodeLanguages:
    """Tests for GET /api/code/languages"""

    @pytest.mark.asyncio
    async def test_get_supported_languages(
        self, client: AsyncClient, auth_headers: dict
    ):
        """TC-CE-01: Should return list of supported programming languages"""
        response = await client.get(
            "/api/code/languages",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 5

        for lang in data:
            assert "id" in lang
            assert "name" in lang
            assert "monaco_language" in lang

    @pytest.mark.asyncio
    async def test_languages_include_python(
        self, client: AsyncClient, auth_headers: dict
    ):
        """TC-CE-02: Python should be in supported languages"""
        response = await client.get(
            "/api/code/languages",
            headers=auth_headers,
        )

        data = response.json()
        language_names = [lang["name"] for lang in data]
        assert any("Python" in name for name in language_names)

    @pytest.mark.asyncio
    async def test_languages_include_c_cpp(
        self, client: AsyncClient, auth_headers: dict
    ):
        """TC-CE-03: C and C++ should be supported"""
        response = await client.get(
            "/api/code/languages",
            headers=auth_headers,
        )

        data = response.json()
        language_names = [lang["name"] for lang in data]
        assert any("C" in name for name in language_names)
        assert any("C++" in name for name in language_names)


class TestCodeExecute:
    """Tests for POST /api/code/execute"""

    @pytest.mark.asyncio
    async def test_execute_python_code(self, client: AsyncClient, auth_headers: dict):
        """TC-CE-04: Execute Python code successfully"""
        mock_result = {
            "token": "test-token-123",
            "status_id": 3,
            "stdout": "Hello World\n",
            "stderr": "",
            "compile_output": "",
            "message": "",
            "time": "0.01",
            "memory": 6400,
            "exit_code": 0,
        }

        judge0 = MagicMock(spec=Judge0Service)
        judge0.execute_code = AsyncMock(return_value=mock_result)
        judge0.format_output.return_value = {
            "token": "test-token-123",
            "status": "Accepted",
            "status_id": 3,
            "stdout": "Hello World\n",
            "stderr": "",
            "compile_output": "",
            "message": "",
            "time": "0.01",
            "memory": 6400,
            "exit_code": 0,
        }

        with override_judge0_service(judge0):
            response = await client.post(
                "/api/code/execute",
                headers=auth_headers,
                json={
                    "code": "print('Hello World')",
                    "language_id": 71,
                    "stdin": "",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["stdout"] == "Hello World\n"
            assert data["status_id"] == 3

    @pytest.mark.asyncio
    async def test_execute_with_stdin(self, client: AsyncClient, auth_headers: dict):
        """TC-CE-05: Execute code with stdin input"""
        mock_result = {
            "token": "test-token-456",
            "status_id": 3,
            "stdout": "5\n",
            "stderr": "",
            "compile_output": "",
            "message": "",
            "time": "0.02",
            "memory": 6400,
            "exit_code": 0,
        }

        judge0 = MagicMock(spec=Judge0Service)
        judge0.execute_code = AsyncMock(return_value=mock_result)
        judge0.format_output.return_value = {
            "token": "test-token-456",
            "status": "Accepted",
            "status_id": 3,
            "stdout": "5\n",
            "stderr": "",
            "compile_output": "",
            "message": "",
            "time": "0.02",
            "memory": 6400,
            "exit_code": 0,
        }

        with override_judge0_service(judge0):
            response = await client.post(
                "/api/code/execute",
                headers=auth_headers,
                json={
                    "code": "x = int(input())\nprint(x + 3)",
                    "language_id": 71,
                    "stdin": "2",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["stdout"] == "5\n"

    @pytest.mark.asyncio
    async def test_execute_unsupported_language(
        self, client: AsyncClient, auth_headers: dict
    ):
        """TC-CE-06: Unsupported language should return 400"""
        response = await client.post(
            "/api/code/execute",
            headers=auth_headers,
            json={
                "code": "print('test')",
                "language_id": 99999,  # Invalid
                "stdin": "",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert (
            data["detail"] == "Unsupported language_id. Supported: [50, 54, 63, 71, 74]"
        )

    @pytest.mark.asyncio
    async def test_execute_compilation_error(
        self, client: AsyncClient, auth_headers: dict
    ):
        """TC-CE-07: Compilation error should be handled gracefully"""
        mock_result = {
            "token": "test-token-789",
            "status_id": 6,
            "stdout": "",
            "stderr": "Segmentation fault",
            "compile_output": "",
            "message": "",
            "time": "0.00",
            "memory": 0,
            "exit_code": 139,
        }

        judge0 = MagicMock(spec=Judge0Service)
        judge0.execute_code = AsyncMock(return_value=mock_result)
        judge0.format_output.return_value = {
            "token": "test-token-789",
            "status": "Runtime Error (SIGSEGV)",
            "status_id": 6,
            "stdout": "",
            "stderr": "Segmentation fault",
            "compile_output": "",
            "message": "",
            "time": "0.00",
            "memory": 0,
            "exit_code": 139,
        }

        with override_judge0_service(judge0):
            response = await client.post(
                "/api/code/execute",
                headers=auth_headers,
                json={
                    "code": "int main() { int *p = NULL; *p = 1; }",
                    "language_id": 50,
                    "stdin": "",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status_id"] == 6

    @pytest.mark.asyncio
    async def test_execute_time_limit_exceeded(
        self, client: AsyncClient, auth_headers: dict
    ):
        """TC-CE-08: Time limit exceeded should return TLE status"""
        mock_result = {
            "token": "test-token-tle",
            "status_id": 8,
            "stdout": "",
            "stderr": "",
            "compile_output": "",
            "message": "Time limit exceeded",
            "time": "5.00",
            "memory": 6400,
            "exit_code": 0,
        }

        judge0 = MagicMock(spec=Judge0Service)
        judge0.execute_code = AsyncMock(return_value=mock_result)
        judge0.format_output.return_value = {
            "token": "test-token-tle",
            "status": "Time Limit Exceeded",
            "status_id": 8,
            "stdout": "",
            "stderr": "",
            "compile_output": "",
            "message": "Time limit exceeded",
            "time": "5.00",
            "memory": 6400,
            "exit_code": 0,
        }

        with override_judge0_service(judge0):
            response = await client.post(
                "/api/code/execute",
                headers=auth_headers,
                json={
                    "code": "while True: pass",
                    "language_id": 71,
                    "stdin": "",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status_id"] == 8

    @pytest.mark.asyncio
    async def test_execute_judge0_unavailable(
        self, client: AsyncClient, auth_headers: dict
    ):
        """TC-CE-09: Judge0 unavailable should return 503"""
        from httpx import RequestError

        judge0 = MagicMock(spec=Judge0Service)
        judge0.execute_code = AsyncMock(side_effect=RequestError("Connection refused"))

        with override_judge0_service(judge0):
            response = await client.post(
                "/api/code/execute",
                headers=auth_headers,
                json={
                    "code": "print('test')",
                    "language_id": 71,
                    "stdin": "",
                },
            )

            assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_execute_request_scoped_judge0_request_error_returns_503_and_closes_once(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Request-scoped Judge0Service raising RequestError returns 503 and closes once."""
        judge0 = MagicMock(spec=Judge0Service)
        judge0.execute_code = AsyncMock(
            side_effect=httpx.RequestError("Connection refused")
        )
        judge0.close = AsyncMock()

        with patch("app.routers.code.Judge0Service", return_value=judge0):
            response = await client.post(
                "/api/code/execute",
                headers=auth_headers,
                json={"code": "print('test')", "language_id": 71, "stdin": ""},
            )

            assert response.status_code == 503
            assert response.json()["detail"] == (
                "Code execution service is unavailable. Please try again later."
            )
            judge0.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_judge0_rate_limited_returns_429(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Judge0 429 in single route must be surfaced as 429."""
        judge0 = MagicMock(spec=Judge0Service)
        judge0.execute_code = AsyncMock(side_effect=_http_status_error(429))

        with override_judge0_service(judge0):
            response = await client.post(
                "/api/code/execute",
                headers=auth_headers,
                json={"code": "print('test')", "language_id": 71, "stdin": ""},
            )

            assert response.status_code == 429
            assert response.json()["detail"] == (
                "请求过于频繁，请稍后再试。Judge0 API 有限流保护。"
            )

    @pytest.mark.asyncio
    async def test_execute_judge0_non_429_http_error_returns_503(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Non-429 Judge0 HTTPStatusError in single route must map to 503."""
        judge0 = MagicMock(spec=Judge0Service)
        judge0.execute_code = AsyncMock(side_effect=_http_status_error(500))

        with override_judge0_service(judge0):
            response = await client.post(
                "/api/code/execute",
                headers=auth_headers,
                json={"code": "print('test')", "language_id": 71, "stdin": ""},
            )

            assert response.status_code == 503
            assert response.json()["detail"] == (
                "Code execution service returned an error. Please try again later."
            )

    @pytest.mark.asyncio
    async def test_execute_closes_request_scoped_judge_service(
        self, client: AsyncClient, auth_headers: dict
    ):
        """TC-CE-19: Request-scoped Judge0Service must be closed after execution."""
        judge0 = MagicMock(spec=Judge0Service)
        judge0.execute_code = AsyncMock(return_value={"token": "run", "status_id": 3})
        judge0.format_output.return_value = {
            "token": "run",
            "status": "Accepted",
            "status_id": 3,
            "stdout": "",
            "stderr": None,
            "compile_output": None,
            "message": None,
            "time": None,
            "memory": None,
            "exit_code": 0,
        }
        judge0.close = AsyncMock()

        with patch("app.routers.code.Judge0Service", return_value=judge0):
            response = await client.post(
                "/api/code/execute",
                headers=auth_headers,
                json={"code": "print('ok')", "language_id": 71, "stdin": ""},
            )

            assert response.status_code == 200
            judge0.close.assert_awaited_once()


class TestCodeExecuteBatch:
    """Tests for POST /api/code/execute-batch"""

    @pytest.mark.asyncio
    async def test_execute_batch_all_pass(
        self, client: AsyncClient, auth_headers: dict
    ):
        """TC-CE-10: Batch execution with all test cases passing"""
        mock_result = {
            "token": "batch-token-1",
            "status": "Accepted",
            "status_id": 3,
            "passed_count": 3,
            "total_count": 3,
            "results": [
                {
                    "passed": True,
                    "input": "1",
                    "expected": "1",
                    "actual": "1",
                    "status_id": 3,
                    "message": "",
                },
                {
                    "passed": True,
                    "input": "2",
                    "expected": "4",
                    "actual": "4",
                    "status_id": 3,
                    "message": "",
                },
                {
                    "passed": True,
                    "input": "3",
                    "expected": "9",
                    "actual": "9",
                    "status_id": 3,
                    "message": "",
                },
            ],
            "time": "0.05",
            "memory": 6400,
            "compile_output": "",
            "message": "",
        }

        judge0 = MagicMock(spec=Judge0Service)
        judge0.execute_batch = AsyncMock(return_value=mock_result)

        with override_judge0_service(judge0):
            response = await client.post(
                "/api/code/execute-batch",
                headers=auth_headers,
                json={
                    "code": "x = int(input())\nprint(x * x)",
                    "language_id": 71,
                    "test_cases": [
                        {"input": "1", "expected_output": "1"},
                        {"input": "2", "expected_output": "4"},
                        {"input": "3", "expected_output": "9"},
                    ],
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["passed_count"] == 3
            assert data["total_count"] == 3
            assert len(data["results"]) == 3

            for result in data["results"]:
                assert result["passed"] is True

    @pytest.mark.asyncio
    async def test_execute_batch_some_fail(
        self, client: AsyncClient, auth_headers: dict
    ):
        """TC-CE-11: Batch execution with some test cases failing"""
        mock_result = {
            "token": "batch-token-2",
            "status": "Wrong Answer",
            "status_id": 4,
            "passed_count": 1,
            "total_count": 3,
            "results": [
                {
                    "passed": True,
                    "input": "1",
                    "expected": "1",
                    "actual": "1",
                    "status_id": 3,
                    "message": "",
                },
                {
                    "passed": False,
                    "input": "2",
                    "expected": "4",
                    "actual": "5",
                    "status_id": 4,
                    "message": "Wrong Answer",
                },
                {
                    "passed": False,
                    "input": "3",
                    "expected": "9",
                    "actual": "10",
                    "status_id": 4,
                    "message": "Wrong Answer",
                },
            ],
            "time": "0.05",
            "memory": 6400,
            "compile_output": "",
            "message": "",
        }

        judge0 = MagicMock(spec=Judge0Service)
        judge0.execute_batch = AsyncMock(return_value=mock_result)

        with override_judge0_service(judge0):
            response = await client.post(
                "/api/code/execute-batch",
                headers=auth_headers,
                json={
                    "code": "x = int(input())\nprint(x + 3)",  # Wrong: should be x * x
                    "language_id": 71,
                    "test_cases": [
                        {"input": "1", "expected_output": "1"},
                        {"input": "2", "expected_output": "4"},
                        {"input": "3", "expected_output": "9"},
                    ],
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["passed_count"] == 1
            assert data["total_count"] == 3

    @pytest.mark.asyncio
    async def test_execute_batch_empty_test_cases(
        self, client: AsyncClient, auth_headers: dict
    ):
        """TC-CE-12: Empty test cases should return 400"""
        response = await client.post(
            "/api/code/execute-batch",
            headers=auth_headers,
            json={
                "code": "print('hello')",
                "language_id": 71,
                "test_cases": [],
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "test case" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_execute_batch_too_many_test_cases(
        self, client: AsyncClient, auth_headers: dict
    ):
        """TC-CE-13: More than 50 test cases should return 400"""
        response = await client.post(
            "/api/code/execute-batch",
            headers=auth_headers,
            json={
                "code": "print('hello')",
                "language_id": 71,
                "test_cases": [
                    {"input": str(i), "expected_output": str(i)} for i in range(51)
                ],
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "50" in data["detail"] or "too many" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_execute_batch_unsupported_language(
        self, client: AsyncClient, auth_headers: dict
    ):
        """TC-CE-14: Unsupported language in batch should return 400"""
        response = await client.post(
            "/api/code/execute-batch",
            headers=auth_headers,
            json={
                "code": "print('hello')",
                "language_id": 99999,
                "test_cases": [
                    {"input": "1", "expected_output": "1"},
                ],
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert (
            data["detail"] == "Unsupported language_id. Supported: [50, 54, 63, 71, 74]"
        )

    @pytest.mark.asyncio
    async def test_execute_batch_compilation_error(
        self, client: AsyncClient, auth_headers: dict
    ):
        """TC-CE-15: Compilation error in batch should be reported"""
        mock_result = {
            "token": "batch-token-ce",
            "status": "Compilation Error",
            "status_id": 5,
            "passed_count": 0,
            "total_count": 2,
            "results": [],
            "time": "0.00",
            "memory": 0,
            "compile_output": "SyntaxError: invalid syntax",
            "message": "Compilation failed",
        }

        judge0 = MagicMock(spec=Judge0Service)
        judge0.execute_batch = AsyncMock(return_value=mock_result)

        with override_judge0_service(judge0):
            response = await client.post(
                "/api/code/execute-batch",
                headers=auth_headers,
                json={
                    "code": "print('missing paren",  # Syntax error
                    "language_id": 71,
                    "test_cases": [
                        {"input": "1", "expected_output": "1"},
                        {"input": "2", "expected_output": "2"},
                    ],
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status_id"] == 5
            assert "compile_output" in data

    @pytest.mark.asyncio
    async def test_execute_batch_unexpected_exception_returns_500_and_logs_exception(
        self, client: AsyncClient, auth_headers: dict
    ):
        """execute_batch unexpected exception returns 500 and logs Batch execution error."""
        judge0 = MagicMock(spec=Judge0Service)
        judge0.execute_batch = AsyncMock(side_effect=RuntimeError("Unexpected failure"))

        with (
            override_judge0_service(judge0),
            patch.object(code_router.logger, "exception") as mock_exception,
        ):
            response = await client.post(
                "/api/code/execute-batch",
                headers=auth_headers,
                json={
                    "code": "print('test')",
                    "language_id": 71,
                    "test_cases": [{"input": "1", "expected_output": "1"}],
                },
            )

            assert response.status_code == 500
            assert response.json()["detail"] == "代码执行服务内部错误，请稍后重试。"
            mock_exception.assert_called_once_with("Batch execution error")

    @pytest.mark.asyncio
    async def test_execute_batch_judge0_rate_limited_returns_429(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Judge0 429 in batch route must be surfaced as 429."""
        judge0 = MagicMock(spec=Judge0Service)
        judge0.execute_batch = AsyncMock(side_effect=_http_status_error(429))

        with override_judge0_service(judge0):
            response = await client.post(
                "/api/code/execute-batch",
                headers=auth_headers,
                json={
                    "code": "print('test')",
                    "language_id": 71,
                    "test_cases": [{"input": "1", "expected_output": "1"}],
                },
            )

            assert response.status_code == 429
            assert response.json()["detail"] == "请求过于频繁，请稍后再试。"

    @pytest.mark.asyncio
    async def test_execute_batch_judge0_non_429_http_error_returns_503(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Non-429 Judge0 HTTPStatusError in batch route must map to 503."""
        judge0 = MagicMock(spec=Judge0Service)
        judge0.execute_batch = AsyncMock(side_effect=_http_status_error(500))

        with override_judge0_service(judge0):
            response = await client.post(
                "/api/code/execute-batch",
                headers=auth_headers,
                json={
                    "code": "print('test')",
                    "language_id": 71,
                    "test_cases": [{"input": "1", "expected_output": "1"}],
                },
            )

            assert response.status_code == 503
            assert (
                response.json()["detail"] == "Code execution service returned an error."
            )

    @pytest.mark.asyncio
    async def test_execute_batch_judge0_request_error_returns_503(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Judge0 RequestError in batch route must map to 503."""
        judge0 = MagicMock(spec=Judge0Service)
        judge0.execute_batch = AsyncMock(
            side_effect=httpx.RequestError("Connection refused")
        )

        with override_judge0_service(judge0):
            response = await client.post(
                "/api/code/execute-batch",
                headers=auth_headers,
                json={
                    "code": "print('test')",
                    "language_id": 71,
                    "test_cases": [{"input": "1", "expected_output": "1"}],
                },
            )

            assert response.status_code == 503
            assert response.json()["detail"] == "Code execution service is unavailable."

    @pytest.mark.asyncio
    async def test_execute_batch_real_service_request_error_returns_503(
        self, client: AsyncClient, auth_headers: dict
    ):
        """A real Judge0Service whose client raises RequestError propagates to 503."""
        real_service = Judge0Service(client=FakeJudge0ClientRaisingRequestError())

        with patch("app.routers.code.Judge0Service", return_value=real_service):
            response = await client.post(
                "/api/code/execute-batch",
                headers=auth_headers,
                json={
                    "code": "print('test')",
                    "language_id": 71,
                    "test_cases": [{"input": "1", "expected_output": "1"}],
                },
            )

            assert response.status_code == 503
            assert response.json()["detail"] == "Code execution service is unavailable."


class TestCodeExecutionSecurity:
    """Security-focused tests for code execution"""

    @pytest.mark.asyncio
    async def test_execute_requires_auth(self, client: AsyncClient):
        """TC-CE-16: Code execution requires authentication"""
        response = await client.post(
            "/api/code/execute",
            json={
                "code": "print('test')",
                "language_id": 71,
                "stdin": "",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_batch_requires_auth(self, client: AsyncClient):
        """TC-CE-17: Batch execution requires authentication"""
        response = await client.post(
            "/api/code/execute-batch",
            json={
                "code": "print('test')",
                "language_id": 71,
                "test_cases": [{"input": "1", "expected_output": "1"}],
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_languages_requires_auth(self, client: AsyncClient):
        """TC-CE-18: Languages endpoint requires authentication"""
        response = await client.get("/api/code/languages")

        assert response.status_code == 401

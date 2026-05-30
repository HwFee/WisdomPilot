"""
Tests for Code Execution API (Judge0 Integration)

Covers:
- POST /api/code/execute - Single code execution
- POST /api/code/execute-batch - Batch test case execution
- GET /api/code/languages - Supported languages

Mocks Judge0 API to avoid external dependencies during testing.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock


class TestCodeLanguages:
    """Tests for GET /api/code/languages"""

    @pytest.mark.asyncio
    async def test_get_supported_languages(self, client: AsyncClient, auth_headers: dict):
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
    async def test_languages_include_python(self, client: AsyncClient, auth_headers: dict):
        """TC-CE-02: Python should be in supported languages"""
        response = await client.get(
            "/api/code/languages",
            headers=auth_headers,
        )

        data = response.json()
        language_names = [lang["name"] for lang in data]
        assert any("Python" in name for name in language_names)

    @pytest.mark.asyncio
    async def test_languages_include_c_cpp(self, client: AsyncClient, auth_headers: dict):
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

        with patch("app.services.judge0.Judge0Service.execute_code", new_callable=AsyncMock) as mock_execute:
            with patch("app.services.judge0.Judge0Service.format_output", return_value={
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
            }):
                mock_execute.return_value = mock_result

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

        with patch("app.services.judge0.Judge0Service.execute_code", new_callable=AsyncMock) as mock_execute:
            with patch("app.services.judge0.Judge0Service.format_output", return_value={
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
            }):
                mock_execute.return_value = mock_result

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
    async def test_execute_unsupported_language(self, client: AsyncClient, auth_headers: dict):
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
        assert "Unsupported" in data["detail"] or "unsupported" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_execute_compilation_error(self, client: AsyncClient, auth_headers: dict):
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

        with patch("app.services.judge0.Judge0Service.execute_code", new_callable=AsyncMock) as mock_execute:
            with patch("app.services.judge0.Judge0Service.format_output", return_value={
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
            }):
                mock_execute.return_value = mock_result

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
    async def test_execute_time_limit_exceeded(self, client: AsyncClient, auth_headers: dict):
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

        with patch("app.services.judge0.Judge0Service.execute_code", new_callable=AsyncMock) as mock_execute:
            with patch("app.services.judge0.Judge0Service.format_output", return_value={
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
            }):
                mock_execute.return_value = mock_result

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
    async def test_execute_judge0_unavailable(self, client: AsyncClient, auth_headers: dict):
        """TC-CE-09: Judge0 unavailable should return 503"""
        from httpx import RequestError

        with patch("app.services.judge0.Judge0Service.execute_code", new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = RequestError("Connection refused")

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


class TestCodeExecuteBatch:
    """Tests for POST /api/code/execute-batch"""

    @pytest.mark.asyncio
    async def test_execute_batch_all_pass(self, client: AsyncClient, auth_headers: dict):
        """TC-CE-10: Batch execution with all test cases passing"""
        mock_result = {
            "token": "batch-token-1",
            "status": "Accepted",
            "status_id": 3,
            "passed_count": 3,
            "total_count": 3,
            "results": [
                {"passed": True, "input": "1", "expected": "1", "actual": "1", "status_id": 3, "message": ""},
                {"passed": True, "input": "2", "expected": "4", "actual": "4", "status_id": 3, "message": ""},
                {"passed": True, "input": "3", "expected": "9", "actual": "9", "status_id": 3, "message": ""},
            ],
            "time": "0.05",
            "memory": 6400,
            "compile_output": "",
            "message": "",
        }

        with patch("app.services.judge0.Judge0Service.execute_batch", new_callable=AsyncMock) as mock_batch:
            mock_batch.return_value = mock_result

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
    async def test_execute_batch_some_fail(self, client: AsyncClient, auth_headers: dict):
        """TC-CE-11: Batch execution with some test cases failing"""
        mock_result = {
            "token": "batch-token-2",
            "status": "Wrong Answer",
            "status_id": 4,
            "passed_count": 1,
            "total_count": 3,
            "results": [
                {"passed": True, "input": "1", "expected": "1", "actual": "1", "status_id": 3, "message": ""},
                {"passed": False, "input": "2", "expected": "4", "actual": "5", "status_id": 4, "message": "Wrong Answer"},
                {"passed": False, "input": "3", "expected": "9", "actual": "10", "status_id": 4, "message": "Wrong Answer"},
            ],
            "time": "0.05",
            "memory": 6400,
            "compile_output": "",
            "message": "",
        }

        with patch("app.services.judge0.Judge0Service.execute_batch", new_callable=AsyncMock) as mock_batch:
            mock_batch.return_value = mock_result

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
    async def test_execute_batch_empty_test_cases(self, client: AsyncClient, auth_headers: dict):
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
    async def test_execute_batch_too_many_test_cases(self, client: AsyncClient, auth_headers: dict):
        """TC-CE-13: More than 50 test cases should return 400"""
        response = await client.post(
            "/api/code/execute-batch",
            headers=auth_headers,
            json={
                "code": "print('hello')",
                "language_id": 71,
                "test_cases": [
                    {"input": str(i), "expected_output": str(i)}
                    for i in range(51)
                ],
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "50" in data["detail"] or "too many" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_execute_batch_unsupported_language(self, client: AsyncClient, auth_headers: dict):
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

    @pytest.mark.asyncio
    async def test_execute_batch_compilation_error(self, client: AsyncClient, auth_headers: dict):
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

        with patch("app.services.judge0.Judge0Service.execute_batch", new_callable=AsyncMock) as mock_batch:
            mock_batch.return_value = mock_result

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

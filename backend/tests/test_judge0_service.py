"""Tests for Judge0Service as an execution facade."""

import httpx
import pytest

from app.services.judge0 import Judge0Service, LANGUAGE_PYTHON, JUDGE0_BASE_URL
from app.services.judge0_client import Judge0Client


class FakeJudge0Client:
    def __init__(self, results: list[dict[str, object]] | None = None) -> None:
        self.results = results or []
        self.submit_calls: list[tuple[str, int, str, str]] = []
        self.submit_batch_calls: list[tuple[str, int, list[dict[str, str]]]] = []
        self.closed = False

    async def submit(
        self, code: str, language_id: int, stdin: str = "", expected_output: str = ""
    ) -> dict[str, object]:
        self.submit_calls.append((code, language_id, stdin, expected_output))
        return {"token": "single-token", "status_id": 3, "stdout": "ok\n"}

    async def submit_batch(
        self, code: str, language_id: int, test_cases: list[dict[str, str]]
    ) -> list[dict[str, object]]:
        self.submit_batch_calls.append((code, language_id, test_cases))
        return self.results

    async def close(self) -> None:
        self.closed = True


class FakeJudge0ClientWithSingleResult:
    def __init__(self, result: dict[str, object]) -> None:
        self.result = result
        self.submit_calls: list[tuple[str, int, str, str]] = []
        self.closed = False

    async def submit(
        self, code: str, language_id: int, stdin: str = "", expected_output: str = ""
    ) -> dict[str, object]:
        self.submit_calls.append((code, language_id, stdin, expected_output))
        return self.result

    async def submit_batch(
        self, code: str, language_id: int, test_cases: list[dict[str, str]]
    ) -> list[dict[str, object]]:
        raise NotImplementedError

    async def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_execute_code_delegates_to_client_submit() -> None:
    fake = FakeJudge0ClientWithSingleResult(
        {"token": "single-token", "status_id": 3, "stdout": "hello\n"}
    )
    service = Judge0Service(client=fake)

    result = await service.execute_code(
        code="print(input())",
        language_id=LANGUAGE_PYTHON,
        stdin="hello",
        poll_interval=0.1,
        max_polls=5,
    )

    assert fake.submit_calls == [("print(input())", LANGUAGE_PYTHON, "hello", "")]
    assert result["status_id"] == 3
    assert result["stdout"] == "hello\n"
    assert "token" in result


@pytest.mark.asyncio
async def test_close_delegates_to_client_close() -> None:
    fake = FakeJudge0Client()
    service = Judge0Service(client=fake)

    await service.close()

    assert fake.closed is True


@pytest.mark.asyncio
async def test_execute_batch_reports_each_case_and_aggregates_verdict() -> None:
    fake = FakeJudge0Client(
        [
            {"token": "one", "status_id": 3, "stdout": " 4\n"},
            {"token": "two", "status_id": 4, "stdout": "5\n"},
        ]
    )
    service = Judge0Service(client=fake)

    result = await service.execute_batch(
        "print(input())",
        LANGUAGE_PYTHON,
        [
            {"input": "2", "expected_output": "4"},
            {"input": "3", "expected_output": "9"},
        ],
    )

    assert fake.submit_batch_calls == [
        (
            "print(input())",
            LANGUAGE_PYTHON,
            [
                {"input": "2", "expected_output": "4"},
                {"input": "3", "expected_output": "9"},
            ],
        )
    ]
    assert result["status"] == "Wrong Answer"
    assert result["status_id"] == 4
    assert result["passed_count"] == 1
    assert result["total_count"] == 2
    assert result["results"] == [
        {
            "passed": True,
            "input": "2",
            "expected": "4",
            "actual": "4",
            "message": "通过",
        },
        {
            "passed": False,
            "input": "3",
            "expected": "9",
            "actual": "5",
            "message": "输出错误",
        },
    ]


@pytest.mark.asyncio
async def test_execute_batch_empty_test_cases_returns_no_case_response() -> None:
    service = Judge0Service(client=FakeJudge0Client([]))

    result = await service.execute_batch("print(1)", LANGUAGE_PYTHON, [])

    assert result == {
        "token": "",
        "status_id": 13,
        "status": "No Test Cases",
        "passed_count": 0,
        "total_count": 0,
        "results": [],
    }


@pytest.mark.asyncio
async def test_execute_batch_all_passed_sets_accepted_status() -> None:
    service = Judge0Service(
        client=FakeJudge0Client(
            [
                {"token": "a", "status_id": 3, "stdout": "2\n"},
                {"token": "b", "status_id": 3, "stdout": "4\n"},
            ]
        )
    )

    result = await service.execute_batch(
        "print(int(input()) + 1)",
        LANGUAGE_PYTHON,
        [
            {"input": "1", "expected_output": "2"},
            {"input": "3", "expected_output": "4"},
        ],
    )

    assert result["status"] == "Accepted"
    assert result["status_id"] == 3
    assert result["passed_count"] == 2
    assert result["message"] is None


@pytest.mark.asyncio
async def test_execute_batch_raises_when_client_returns_fewer_results_than_test_cases() -> (
    None
):
    service = Judge0Service(
        client=FakeJudge0Client(
            [
                {"token": "one", "status_id": 3, "stdout": "4\n"},
            ]
        )
    )

    with pytest.raises(httpx.RequestError, match="Judge0 batch result count mismatch"):
        await service.execute_batch(
            "print(input())",
            LANGUAGE_PYTHON,
            [
                {"input": "2", "expected_output": "4"},
                {"input": "3", "expected_output": "9"},
            ],
        )


def test_format_output_includes_compiler_detail_for_compilation_error() -> None:
    service = Judge0Service(client=FakeJudge0Client([]))

    formatted = service.format_output(
        {
            "token": "compile-token",
            "status_id": 5,
            "compile_output": "main.c:1: error",
            "stdout": None,
            "stderr": None,
            "time": None,
            "memory": None,
            "exit_code": None,
        }
    )

    assert formatted["status"] == "Compilation Error"
    assert formatted["message"] == "编译错误: main.c:1: error"


def test_format_output_preserves_time_limit_exceeded_message() -> None:
    service = Judge0Service(client=FakeJudge0Client([]))

    formatted = service.format_output(
        {
            "token": "tle-token",
            "status_id": 8,
            "stdout": None,
            "stderr": None,
            "compile_output": None,
            "time": "5.00",
            "memory": 6400,
            "exit_code": 0,
        }
    )

    assert formatted["status"] == "Time Limit Exceeded"
    assert formatted["message"] == "运行超时，您的程序可能在无限循环"
    assert formatted["time"] == "5.00"
    assert formatted["memory"] == 6400


def test_format_output_runtime_error_uses_stderr() -> None:
    service = Judge0Service(client=FakeJudge0Client([]))

    formatted = service.format_output(
        {
            "token": "re-token",
            "status_id": 11,
            "stdout": None,
            "stderr": "index out of range",
            "compile_output": None,
            "time": None,
            "memory": None,
            "exit_code": 1,
        }
    )

    assert formatted["status"] == "Runtime Error (NZEC)"
    assert formatted["message"] == "运行时错误: index out of range"


def test_judge0_service_default_client_is_judge0_client() -> None:
    service = Judge0Service()

    assert isinstance(service._client, Judge0Client)
    assert service._client._base_url == JUDGE0_BASE_URL


class FakeJudge0ClientRaisingRequestError:
    def __init__(self) -> None:
        pass

    async def submit(
        self, code: str, language_id: int, stdin: str = "", expected_output: str = ""
    ) -> dict[str, object]:
        raise NotImplementedError

    async def submit_batch(
        self, code: str, language_id: int, test_cases: list[dict[str, str]]
    ) -> list[dict[str, object]]:
        raise httpx.RequestError("Connection refused")

    async def close(self) -> None:
        pass


@pytest.mark.asyncio
async def test_execute_batch_propagates_transport_error_to_caller() -> None:
    service = Judge0Service(client=FakeJudge0ClientRaisingRequestError())

    with pytest.raises(httpx.RequestError, match="Connection refused"):
        await service.execute_batch(
            "print(1)",
            LANGUAGE_PYTHON,
            [{"input": "1", "expected_output": "1"}],
        )

import asyncio
import base64
import json

import httpx
import pytest

from app.services import judge0_client as judge0_client_module
from app.services.judge0_client import Judge0Client


@pytest.mark.asyncio
async def test_submit_encodes_request_and_decodes_execution_output() -> None:
    captured_request: httpx.Request | None = None

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return httpx.Response(
            201,
            json={
                "token": "submission-token",
                "stdout": "SGVsbG8K",
                "stderr": None,
                "compile_output": None,
                "status": {"id": 3},
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = Judge0Client("https://judge.test", http_client)
        result = await client.submit("print('Hello')", 71, "", "Hello\n")

    assert captured_request is not None
    assert captured_request.url.path == "/submissions"
    assert captured_request.url.params["base64_encoded"] == "true"
    assert captured_request.url.params["wait"] == "true"

    payload = json.loads(captured_request.content)
    assert (
        payload["source_code"] == base64.b64encode("print('Hello')".encode()).decode()
    )
    assert payload["stdin"] == base64.b64encode("".encode()).decode()
    assert payload["expected_output"] == base64.b64encode("Hello\n".encode()).decode()
    assert result["stdout"] == "Hello\n"
    assert result["status_id"] == 3


@pytest.mark.asyncio
async def test_submit_decodes_stderr_and_compile_output() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            201,
            json={
                "token": "err-token",
                "stdout": None,
                "stderr": base64.b64encode("runtime error".encode()).decode(),
                "compile_output": base64.b64encode("compile failure".encode()).decode(),
                "status": {"id": 5},
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = Judge0Client("https://judge.test", http_client)
        result = await client.submit("bad code", 71)

    assert result["stderr"] == "runtime error"
    assert result["compile_output"] == "compile failure"
    assert result["status_id"] == 5


@pytest.mark.asyncio
async def test_submit_batch_polls_pending_result_and_preserves_token_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_sleep(delay: float) -> None:
        pass

    monkeypatch.setattr(judge0_client_module.asyncio, "sleep", fake_sleep)

    requests: list[str] = []
    token_responses = {
        "first": iter(
            [
                httpx.Response(200, json={"status": {"id": 1}}),
                httpx.Response(200, json={"status": {"id": 3}, "stdout": "MQ=="}),
            ]
        ),
        "second": iter(
            [
                httpx.Response(200, json={"status": {"id": 4}, "stdout": "Mg=="}),
            ]
        ),
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        requests.append(path)
        if path == "/submissions/batch":
            return httpx.Response(201, json=[{"token": "first"}, {"token": "second"}])
        token = path.split("/")[-1]
        return next(token_responses[token])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = Judge0Client("https://judge.test", http_client)
        results = await client.submit_batch(
            "print(input())",
            71,
            [
                {"input": "1", "expected_output": "1"},
                {"input": "2", "expected_output": "2"},
            ],
        )

    assert requests[0] == "/submissions/batch"
    assert {"/submissions/first", "/submissions/second"} <= set(requests)
    assert [result["stdout"] for result in results] == ["1", "2"]
    assert [result["status_id"] for result in results] == [3, 4]


@pytest.mark.asyncio
async def test_submit_batch_cancels_and_drains_sibling_polls_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_sleep(delay: float) -> None:
        pass

    monkeypatch.setattr(judge0_client_module.asyncio, "sleep", fake_sleep)

    second_started = asyncio.Event()
    sibling_cancelled = asyncio.Event()
    sibling_done = asyncio.Event()

    async def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/submissions/batch":
            return httpx.Response(
                201,
                json=[{"token": "first"}, {"token": "second"}],
            )
        if "first" in path:
            await second_started.wait()
            raise httpx.ConnectError("first poll failed")
        second_started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            sibling_cancelled.set()
            raise
        finally:
            sibling_done.set()

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = Judge0Client("https://judge.test", http_client)
        with pytest.raises(httpx.RequestError, match="first poll failed"):
            await asyncio.wait_for(
                client.submit_batch(
                    "print(1)",
                    71,
                    [
                        {"input": "", "expected_output": ""},
                        {"input": "", "expected_output": ""},
                    ],
                ),
                timeout=1.0,
            )

    assert sibling_cancelled.is_set()
    assert sibling_done.is_set()


@pytest.mark.asyncio
async def test_submit_batch_polls_tokens_concurrently_and_preserves_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_sleep(delay: float) -> None:
        pass

    monkeypatch.setattr(judge0_client_module.asyncio, "sleep", fake_sleep)

    started = asyncio.Event()
    gate = asyncio.Event()
    active_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal active_count
        path = request.url.path
        if path == "/submissions/batch":
            return httpx.Response(201, json=[{"token": "first"}, {"token": "second"}])
        active_count += 1
        if active_count == 2:
            started.set()
        await gate.wait()
        if "first" in path:
            return httpx.Response(200, json={"status": {"id": 3}, "stdout": "MQ=="})
        return httpx.Response(200, json={"status": {"id": 4}, "stdout": "Mg=="})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = Judge0Client("https://judge.test", http_client)
        task = asyncio.create_task(
            client.submit_batch(
                "print(input())",
                71,
                [
                    {"input": "1", "expected_output": "1"},
                    {"input": "2", "expected_output": "2"},
                ],
            )
        )
        await started.wait()
        assert active_count == 2, (
            "Both token polls should be in-flight before either completes"
        )
        gate.set()
        results = await asyncio.wait_for(task, timeout=1.0)

    assert [result["stdout"] for result in results] == ["1", "2"]
    assert [result["status_id"] for result in results] == [3, 4]


@pytest.mark.asyncio
async def test_submit_batch_accepts_wrapped_submissions_response() -> None:
    requests: list[str] = []
    responses = iter(
        [
            httpx.Response(201, json={"submissions": [{"token": "only"}]}),
            httpx.Response(200, json={"status": {"id": 3}, "stdout": "b3V0"}),
        ]
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request.url.path)
        return next(responses)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = Judge0Client("https://judge.test", http_client)
        results = await client.submit_batch(
            "print('out')", 71, [{"input": "", "expected_output": "out"}]
        )

    assert requests == ["/submissions/batch", "/submissions/only"]
    assert len(results) == 1
    assert results[0]["stdout"] == "out"
    assert results[0]["status_id"] == 3


@pytest.mark.asyncio
async def test_submit_batch_returns_invalid_token_for_missing_token() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(201, json=[{"token": None}])

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = Judge0Client("https://judge.test", http_client)
        results = await client.submit_batch(
            "print(1)", 71, [{"input": "", "expected_output": ""}]
        )

    assert len(results) == 1
    assert results[0]["status_id"] == 13
    assert results[0]["message"] == "Invalid token"


@pytest.mark.asyncio
async def test_submit_batch_returns_empty_results_for_empty_token_list() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(201, json=[])

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = Judge0Client("https://judge.test", http_client)
        results = await client.submit_batch(
            "print(1)", 71, [{"input": "", "expected_output": "1"}]
        )

    assert results == []


@pytest.mark.asyncio
async def test_submit_batch_leaves_output_comparison_to_service() -> None:
    batch_payload: dict[str, object] | None = None

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal batch_payload
        if request.url.path == "/submissions/batch":
            batch_payload = json.loads(request.content)
            return httpx.Response(201, json=[{"token": "one"}])
        return httpx.Response(
            200,
            json={"status": {"id": 3}, "stdout": "IDQK"},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = Judge0Client("https://judge.test", http_client)
        await client.submit_batch(
            "print(' 4')", 71, [{"input": "", "expected_output": "4"}]
        )

    assert batch_payload is not None
    submissions = batch_payload["submissions"]
    assert isinstance(submissions, list)
    assert "expected_output" not in submissions[0]


@pytest.mark.asyncio
async def test_poll_submission_returns_timeout_message_after_exhaustion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleep_calls: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    monkeypatch.setattr(judge0_client_module.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(judge0_client_module, "JUDGE0_POLL_ATTEMPTS", 3)

    poll_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal poll_count
        poll_count += 1
        return httpx.Response(
            200,
            json={
                "token": "pending-token",
                "status": {"id": 1},
                "stdout": "c3RpbGwgcGVuZGluZw==",
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = Judge0Client("https://judge.test", http_client)
        result = await client._poll_submission("pending-token")

    assert poll_count == 3
    assert len(sleep_calls) == 2
    assert result["status_id"] == 1
    assert result["stdout"] == "still pending"
    assert result["message"] == "Polling timeout"


@pytest.mark.asyncio
async def test_close_does_not_close_an_injected_http_client() -> None:
    async with httpx.AsyncClient() as http_client:
        client = Judge0Client("https://judge.test", http_client)
        await client.close()
        assert http_client.is_closed is False


@pytest.mark.asyncio
async def test_close_closes_internally_owned_http_client() -> None:
    client = Judge0Client("https://judge.test")
    internal_client = client._get_client()
    assert internal_client.is_closed is False
    await client.close()
    assert internal_client.is_closed is True
    assert client._client is None

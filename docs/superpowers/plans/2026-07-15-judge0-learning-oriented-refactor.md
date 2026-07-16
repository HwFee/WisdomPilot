# Judge0 Learning-Oriented Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Separate Judge0 HTTP protocol handling from code-execution result handling, close request-scoped clients reliably, and preserve existing API and challenge-submission contracts.

**Architecture:** `Judge0Client` owns Judge0 URLs, base64 serialization, polling, decoding, timeout configuration, and HTTP client lifetime. `Judge0Service` remains the stable application-facing facade consumed by `routers/code.py` and challenge submission; it converts execution records into single-run and batch verdicts. The FastAPI dependency becomes an async generator so every request closes the service client.

**Tech Stack:** Python 3.10, FastAPI, HTTPX, Pydantic v2, pytest, pytest-asyncio, Pyright.

## Global Constraints

- Do not modify frontend code, database schema, migrations, or reward algorithms.
- Preserve successful response schemas for `POST /api/code/execute`, `POST /api/code/execute-batch`, and `GET /api/code/languages`.
- Preserve the `Judge0Service.execute_code`, `Judge0Service.execute_batch`, and `Judge0Service.close` interfaces used by `challenge_path/submission.py`.
- Router code handles HTTP validation and error-to-status mapping only; Judge0 protocol details remain below the service boundary.
- Fix only defects demonstrated by a regression test or an explicit contract test.
- Run the affected tests, complete backend test suite, `pyright`, FastAPI startup, and the affected authenticated routes before declaring completion.

---

## File Structure

- Create: `backend/app/services/judge0_client.py` - Judge0 protocol client: request construction, base64 handling, polling, response normalization, and HTTP resource lifecycle.
- Modify: `backend/app/services/judge0.py` - Stable application facade: language/status constants, single-run response formatting, batch verdict aggregation, and delegation to `Judge0Client`.
- Modify: `backend/app/routers/code.py` - Request-scoped service dependency, named validation constants, and response-model construction without duplicate execution logic.
- Modify: `backend/tests/test_code_execution.py` - API contract tests and resource-lifecycle regression coverage.
- Create: `backend/tests/test_judge0_client.py` - Isolated HTTP protocol and polling tests using `httpx.MockTransport`.
- Create: `backend/tests/test_judge0_service.py` - Service-level batch verdict and formatting tests using a fake Judge0 client.
- Modify: `backend/tests/test_challenge_authoritative_submission.py` - Confirm challenge authoritative judging still accepts the stable `Judge0Service` protocol after the refactor.

## Task 1: Establish Judge0 Protocol Contracts

**Files:**
- Create: `backend/tests/test_judge0_client.py`
- Modify: `backend/app/services/judge0_client.py`

**Interfaces:**
- Produces: `Judge0Client(base_url: str, client: httpx.AsyncClient | None = None)`.
- Produces: `async Judge0Client.submit(code: str, language_id: int, stdin: str = "", expected_output: str = "") -> dict[str, object]`.
- Produces: `async Judge0Client.submit_batch(code: str, language_id: int, test_cases: list[dict[str, str]]) -> list[dict[str, object]]`.
- Produces: `async Judge0Client.close() -> None`.

- [ ] **Step 1: Write a failing single-submission protocol test**

```python
import json


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
    assert json.loads(captured_request.content)["source_code"] == "cHJpbnQoJ0hlbGxvJyk="
    assert result["stdout"] == "Hello\n"
    assert result["status_id"] == 3
```

- [ ] **Step 2: Run the focused test and confirm it fails because the client does not exist**

Run: `py -3 -m pytest tests/test_judge0_client.py::test_submit_encodes_request_and_decodes_execution_output -v`

Expected: FAIL during collection with `ModuleNotFoundError: No module named 'app.services.judge0_client'`.

- [ ] **Step 3: Add the minimal client implementation and shared protocol helpers**

```python
# backend/app/services/judge0_client.py
JUDGE0_TIMEOUT_SECONDS = 60.0
JUDGE0_CPU_TIME_LIMIT_SECONDS = 10
JUDGE0_MEMORY_LIMIT_KILOBYTES = 256_000
JUDGE0_PENDING_STATUS_IDS = frozenset({1, 2})
JUDGE0_POLL_ATTEMPTS = 20
JUDGE0_POLL_INTERVAL_SECONDS = 0.3


class Judge0Client:
    def __init__(self, base_url: str, client: httpx.AsyncClient | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client
        self._owns_client = client is None

    async def submit(
        self, code: str, language_id: int, stdin: str = "", expected_output: str = ""
    ) -> dict[str, object]:
        response = await self._get_client().post(
            f"{self._base_url}/submissions",
            params={"base64_encoded": "true", "wait": "true"},
            json=self._submission_payload(code, language_id, stdin, expected_output),
        )
        response.raise_for_status()
        return self._normalize_result(response.json())
```

Implement `_get_client`, `_submission_payload`, `_encode_text`, `_decode_output_fields`, `_status_id`, `_normalize_result`, `submit_batch`, `_poll_submission`, and `close` in the same module. `submit_batch` must accept both Judge0 batch token response shapes (`[{"token": ...}]` and `{"submissions": [{"token": ...}]}`), return one normalized result for every token, and use `status_id=13` with `message="Invalid token"` for missing tokens. `close` only closes an internally created HTTPX client; injected test clients remain owned by the test.

- [ ] **Step 4: Add failing batch-shape, polling, and resource ownership tests**

```python
@pytest.mark.asyncio
async def test_submit_batch_polls_pending_result_and_preserves_token_order() -> None:
    requests: list[str] = []
    responses = iter([
        httpx.Response(201, json=[{"token": "first"}, {"token": "second"}]),
        httpx.Response(200, json={"status": {"id": 1}}),
        httpx.Response(200, json={"status": {"id": 3}, "stdout": "MQ=="}),
        httpx.Response(200, json={"status": {"id": 4}, "stdout": "Mg=="}),
    ])

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request.url.path)
        return next(responses)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = Judge0Client("https://judge.test", http_client)
        results = await client.submit_batch("print(input())", 71, [{"input": "1", "expected_output": "1"}, {"input": "2", "expected_output": "2"}])

    assert requests == ["/submissions/batch", "/submissions/first", "/submissions/first", "/submissions/second"]
    assert [result["stdout"] for result in results] == ["1", "2"]
    assert [result["status_id"] for result in results] == [3, 4]


@pytest.mark.asyncio
async def test_close_does_not_close_an_injected_http_client() -> None:
    async with httpx.AsyncClient() as http_client:
        client = Judge0Client("https://judge.test", http_client)
        await client.close()
        assert http_client.is_closed is False
```

- [ ] **Step 5: Implement polling and ownership handling, then run the client test module**

Run: `py -3 -m pytest tests/test_judge0_client.py -v`

Expected: PASS. The test must not issue a real network request.

## Task 2: Make `Judge0Service` a Focused Execution Facade

**Files:**
- Modify: `backend/app/services/judge0.py`
- Create: `backend/tests/test_judge0_service.py`

**Interfaces:**
- Consumes: `Judge0Client.submit(...)` and `Judge0Client.submit_batch(...)` from Task 1.
- Produces: `Judge0Service.execute_code(code: str, language_id: int, stdin: str = "", poll_interval: float = 0.5, max_polls: int = 40) -> dict[str, object]`.
- Produces: `Judge0Service.execute_batch(code: str, language_id: int, test_cases: list[dict[str, str]]) -> dict[str, object]`.
- Produces: `Judge0Service.format_output(result: dict[str, object]) -> dict[str, object]`.

- [ ] **Step 1: Write failing service tests against a fake client**

```python
class FakeJudge0Client:
    def __init__(self, results: list[dict[str, object]]) -> None:
        self.results = results

    async def submit_batch(
        self, code: str, language_id: int, test_cases: list[dict[str, str]]
    ) -> list[dict[str, object]]:
        return self.results


@pytest.mark.asyncio
async def test_execute_batch_reports_each_case_and_aggregates_verdict() -> None:
    service = Judge0Service(client=FakeJudge0Client([
        {"token": "one", "status_id": 3, "stdout": " 4\n"},
        {"token": "two", "status_id": 4, "stdout": "5\n"},
    ]))

    result = await service.execute_batch(
        "print(input())",
        71,
        [{"input": "2", "expected_output": "4"}, {"input": "3", "expected_output": "9"}],
    )

    assert result["status"] == "Wrong Answer"
    assert result["status_id"] == 4
    assert result["passed_count"] == 1
    assert result["results"] == [
        {"passed": True, "input": "2", "expected": "4", "actual": "4", "message": "通过"},
        {"passed": False, "input": "3", "expected": "9", "actual": "5", "message": "输出错误"},
    ]
```

- [ ] **Step 2: Run the focused service test and confirm the constructor cannot accept a client**

Run: `py -3 -m pytest tests/test_judge0_service.py::test_execute_batch_reports_each_case_and_aggregates_verdict -v`

Expected: FAIL with `TypeError` because the current `Judge0Service` constructor does not accept `client`.

- [ ] **Step 3: Replace mixed protocol logic with facade delegation**

```python
class Judge0Service:
    def __init__(self, client: Judge0Client | None = None) -> None:
        self._client = client or Judge0Client(JUDGE0_BASE_URL)

    async def execute_code(
        self,
        code: str,
        language_id: int,
        stdin: str = "",
        poll_interval: float = 0.5,
        max_polls: int = 40,
    ) -> dict[str, object]:
        del poll_interval, max_polls
        return await self._client.submit(code, language_id, stdin)

    async def close(self) -> None:
        await self._client.close()
```

Keep language IDs and `STATUS_MESSAGES` in `judge0.py`, because they are application-facing constants imported by the router and challenge path. Extract batch comparison into private helpers named `_build_case_result` and `_build_batch_response`; neither helper performs HTTP I/O. Preserve the existing empty-input batch result and public message text. Remove `create_submission`, `create_batch_submissions`, `get_submission`, and the raw HTTPX client property because their protocol role moves to `Judge0Client` and no application code calls them.

- [ ] **Step 4: Add formatting and error-result regression tests**

```python
def test_format_output_includes_compiler_detail_for_compilation_error() -> None:
    service = Judge0Service(client=FakeJudge0Client([]))

    formatted = service.format_output({
        "token": "compile-token",
        "status_id": 5,
        "compile_output": "main.c:1: error",
        "stdout": None,
        "stderr": None,
        "time": None,
        "memory": None,
        "exit_code": None,
    })

    assert formatted["status"] == "Compilation Error"
    assert formatted["message"] == "编译错误: main.c:1: error"
```

- [ ] **Step 5: Run service tests and existing authoritative challenge tests**

Run: `py -3 -m pytest tests/test_judge0_service.py tests/test_challenge_authoritative_submission.py -v`

Expected: PASS. The challenge tests prove the unchanged `execute_batch` contract still supplies Java and Rust Judge0 language IDs.

## Task 3: Make Code Router Lifetime and Validation Explicit

**Files:**
- Modify: `backend/app/routers/code.py`
- Modify: `backend/tests/test_code_execution.py`

**Interfaces:**
- Consumes: `Judge0Service` stable facade from Task 2.
- Produces: `async get_judge0_service() -> AsyncGenerator[Judge0Service, None]`.
- Produces: `validate_supported_language(language_id: int) -> None` and `validate_batch_size(test_case_count: int) -> None`.

- [ ] **Step 1: Write a failing request-lifecycle regression test**

```python
@pytest.mark.asyncio
async def test_execute_closes_request_scoped_judge_service(
    client: AsyncClient, auth_headers: dict
) -> None:
    judge0 = MagicMock(spec=Judge0Service)
    judge0.execute_code = AsyncMock(return_value={"token": "run", "status_id": 3})
    judge0.format_output.return_value = {
        "token": "run", "status": "Accepted", "status_id": 3,
        "stdout": "", "stderr": None, "compile_output": None,
        "message": None, "time": None, "memory": None, "exit_code": 0,
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
```

- [ ] **Step 2: Run the lifecycle test and confirm it fails because the dependency returns instead of yielding**

Run: `py -3 -m pytest tests/test_code_execution.py::test_execute_closes_request_scoped_judge_service -v`

Expected: FAIL because `get_judge0_service` is not an async-generator dependency and cannot guarantee cleanup.

- [ ] **Step 3: Implement the request-scoped dependency and remove duplicated validation**

```python
MAX_BATCH_TEST_CASES = 50
SUPPORTED_LANGUAGE_IDS = frozenset(language["id"] for language in SUPPORTED_LANGUAGES)


async def get_judge0_service() -> AsyncGenerator[Judge0Service, None]:
    service = Judge0Service()
    try:
        yield service
    finally:
        await service.close()


def validate_supported_language(language_id: int) -> None:
    if language_id not in SUPPORTED_LANGUAGE_IDS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language_id. Supported: {sorted(SUPPORTED_LANGUAGE_IDS)}",
        )
```

Add `validate_batch_size` that rejects zero cases and counts above `MAX_BATCH_TEST_CASES` with the existing response text. Both execution endpoints call `validate_supported_language`; only the batch endpoint calls `validate_batch_size`. Keep `httpx.HTTPStatusError` mapped to `429` or `503` and `httpx.RequestError` mapped to `503`. Keep the unexpected batch exception mapping to `500`, but log it with `logger.exception`.

- [ ] **Step 4: Update API tests to mock the stable facade and assert validation contracts**

Replace nested patches of `Judge0Service.execute_code` and `Judge0Service.format_output` with a dependency override returning a `MagicMock(spec=Judge0Service)`. Retain the existing success, runtime-error, unavailable-service, empty-batch, over-limit, unsupported-language, and auth tests. Add this assertion to the unsupported-language tests:

```python
assert response.json()["detail"] == "Unsupported language_id. Supported: [50, 54, 63, 71, 74]"
```

- [ ] **Step 5: Run route tests**

Run: `py -3 -m pytest tests/test_code_execution.py tests/test_rate_limit.py -v`

Expected: PASS, including the request-scoped client close regression test.

## Task 4: Validate, Document, and Index the Completed Batch

**Files:**
- Modify: `docs/superpowers/specs/2026-07-15-backend-learning-oriented-governance-design.md`
- Modify: `docs/superpowers/plans/2026-07-15-judge0-learning-oriented-refactor.md`

**Interfaces:**
- Consumes: completed Tasks 1-3.
- Produces: recorded validation evidence and a concise completed-batch learning note.

- [ ] **Step 1: Run the full backend quality gate**

Run: `py -3 -m pytest -q`

Expected: all backend tests pass with zero skipped tests.

Run: `pyright`

Expected: `0 errors, 0 warnings, 0 informations`.

- [ ] **Step 2: Start FastAPI and verify protected routes without external Judge0 access**

Run: `py -3 -m uvicorn app.main:app --host 127.0.0.1 --port 8001`

Expected: startup completes without traceback and logs that the application startup is complete.

In a second terminal, run: `curl -i http://127.0.0.1:8001/health`

Expected: HTTP `200` health response.

In a second terminal, run: `curl -i http://127.0.0.1:8001/api/code/languages`

Expected: HTTP `401`, proving the router loads and authentication remains required. Stop the server with `Ctrl+C` after both checks.

- [ ] **Step 3: Record the completed learning note**

Append a `## Judge0 首批实施记录` section to the design document containing exactly these points:

```markdown
- 重构前：`Judge0Service` 同时处理 HTTP 协议、base64 编解码、轮询、结果判定和 API 格式化；路由创建的实例没有请求结束清理保证。
- 重构后：`Judge0Client` 负责外部协议和资源生命周期，`Judge0Service` 负责执行语义和结果聚合，Router 只处理 HTTP 契约。
- 修复：异步生成器依赖在每次代码执行请求结束时调用 `Judge0Service.close()`；注入的测试 HTTP 客户端不会被客户端关闭。
- 证明：客户端模拟 HTTP 测试、服务聚合测试、路由契约测试、挑战权威判题回归测试、完整后端测试、Pyright 和服务启动检查均通过。
```

- [ ] **Step 4: Synchronize CodeGraph after source movement and inspect change impact**

Run: `npx codegraph sync`

Expected: index synchronization succeeds.

Run: `npx codegraph impact Judge0Service`

Expected: output includes `routers/code.py` and `services/challenge_path/submission.py`, with no removed public method referenced by either caller.

## Plan Self-Review

- Spec coverage: Tasks 1-3 implement external-client isolation, stable service boundary, router-only HTTP concerns, resource cleanup, validation, and regression tests. Task 4 validates and documents the batch.
- Completeness scan: no incomplete-work markers or ambiguous handling instructions remain.
- Type consistency: the public `Judge0Service` methods used by `routers/code.py` and `challenge_path/submission.py` retain their names and argument contracts; `Judge0Client` is internal and injected only through the service constructor in tests.

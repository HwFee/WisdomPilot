# AI Provider Protocol Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract a typed, testable OpenAI-compatible protocol boundary with one retry owner and explicit HTTP client shutdown while preserving every existing AI business and Router contract.

**Architecture:** `app.services.ai_provider` owns external protocol errors, request/retry/SSE parsing, and the teaching-provider adapter. `AIService` remains the public business facade, reuses one lazily-created protocol client across reconfiguration, and closes only internally-owned HTTP resources during FastAPI shutdown.

**Tech Stack:** Python 3.10, FastAPI, HTTPX, asyncio, Pytest, Pyright, SQLAlchemy-free provider modules.

## Global Constraints

- Preserve all current AI Router status codes, response fields, prompts, model/temperature values, default base URL, and Authorization format.
- Retry at most 3 total attempts with backoff delays `[1, 2]`; retry only connect/timeout and HTTP 5xx failures.
- Never retry HTTP 4xx, JSON/SSE protocol failures, or a stream after a successful handshake begins reading content.
- A stream ending before `[DONE]` is a typed interruption; all stream exit paths close the upstream response.
- Provider errors must be FastAPI-independent and must not expose API keys, Authorization headers, or more than 500 response characters.
- `AIService` must preserve existing friendly unconfigured returns before using `_require_provider()`.
- Keep `OpenAIProvider` as a temporary compatibility alias for `OpenAICompatibleProvider`.
- Do not change hint cost, Core transactions, cache models, refund behavior, quota endpoints, embedding, frontend, database schema, or configuration persistence.
- Run focused tests, the complete backend suite with zero skips, Pyright, FastAPI and Next.js startup, affected live routes, CodeGraph synchronization, and the project Rule 10 checklist.

---

## File Structure

- Create `backend/app/services/ai_provider/__init__.py`: stable provider package exports and compatibility surface.
- Create `backend/app/services/ai_provider/base.py`: provider and completion-client ports.
- Create `backend/app/services/ai_provider/errors.py`: typed external/configuration failures.
- Create `backend/app/services/ai_provider/client.py`: OpenAI-compatible HTTP, retry, JSON, SSE, and resource ownership.
- Create `backend/app/services/ai_provider/openai.py`: teaching-message adapter over the protocol client.
- Modify `backend/app/services/ai.py`: retain domain prompts/facade, import the provider package, own/reuse the protocol client, remove raw HTTP code.
- Modify `backend/app/core/lifespan.py`: close the global AI service in `finally`.
- Create `backend/tests/test_ai_provider_client.py`: protocol, retry, parsing, streaming, and close tests.
- Modify `backend/tests/test_ai.py`: provider adapter, service configuration, compatibility, and unconfigured behavior.
- Create `backend/tests/test_ai_lifespan.py`: application lifecycle close tests.
- Modify `docs/superpowers/specs/2026-07-15-backend-learning-oriented-governance-design.md`: append the completed 4A record.
- Modify this plan: append exact completion evidence.

---

## Task 1: Type Provider Failures And Extract Non-Streaming HTTP

**Files:**
- Create: `backend/app/services/ai_provider/__init__.py`
- Create: `backend/app/services/ai_provider/errors.py`
- Create: `backend/app/services/ai_provider/base.py`
- Create: `backend/app/services/ai_provider/client.py`
- Create: `backend/tests/test_ai_provider_client.py`

**Interfaces:**
- Produces: `AIProviderError`, `AIProviderConfigurationError`, `AIProviderNetworkError`, `AIProviderHTTPError`, `AIProviderProtocolError`, and `AIProviderStreamError`.
- Produces: `AIProvider` and `AICompletionClient` ports.
- Produces: `OpenAICompatibleClient.complete(...)`, `configure(...)`, and `close()`.
- Guarantees: exact request construction, one retry owner, typed failures, injected-client ownership.

- [ ] **Step 1: Add failing non-streaming protocol tests**

Create `backend/tests/test_ai_provider_client.py` with these helpers and tests:

```python
from collections.abc import Awaitable, Callable

import httpx
import pytest

from app.schemas.ai import AIProviderConfig
from app.services.ai_provider.client import OpenAICompatibleClient
from app.services.ai_provider.errors import (
    AIProviderConfigurationError,
    AIProviderHTTPError,
    AIProviderNetworkError,
    AIProviderProtocolError,
)


def provider_config(**overrides) -> AIProviderConfig:
    values = {
        "provider": "deepseek",
        "api_key": "secret-key",
        "model": "deepseek-test",
        "temperature": 0.25,
        "base_url": "https://provider.test/v1/",
    }
    values.update(overrides)
    return AIProviderConfig(**values)


def recording_sleep(delays: list[float]) -> Callable[[float], Awaitable[None]]:
    async def sleep(delay: float) -> None:
        delays.append(delay)

    return sleep


@pytest.mark.asyncio
async def test_complete_builds_openai_request_and_extracts_content() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "answer"}}]},
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as http_client:
        client = OpenAICompatibleClient(provider_config(), http_client=http_client)
        result = await client.complete([{"role": "user", "content": "question"}])

    request = captured["request"]
    assert str(request.url) == "https://provider.test/v1/chat/completions"
    assert request.headers["Authorization"] == "Bearer secret-key"
    assert request.headers["Content-Type"] == "application/json"
    assert request.read()
    payload = __import__("json").loads(request.content)
    assert payload == {
        "model": "deepseek-test",
        "messages": [{"role": "user", "content": "question"}],
        "temperature": 0.25,
    }
    assert result == "answer"


@pytest.mark.asyncio
async def test_complete_retries_5xx_three_total_attempts() -> None:
    attempts = 0
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503, text="provider unavailable", request=request)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as http_client:
        client = OpenAICompatibleClient(
            provider_config(),
            http_client=http_client,
            sleep=recording_sleep(delays),
        )
        with pytest.raises(AIProviderHTTPError) as captured:
            await client.complete([])

    assert attempts == 3
    assert delays == [1, 2]
    assert captured.value.status_code == 503
    assert captured.value.response_summary == "provider unavailable"


@pytest.mark.asyncio
async def test_complete_retries_network_failure_three_total_attempts() -> None:
    attempts = 0
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ConnectError("offline", request=request)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as http_client:
        client = OpenAICompatibleClient(
            provider_config(),
            http_client=http_client,
            sleep=recording_sleep(delays),
        )
        with pytest.raises(AIProviderNetworkError, match="3 attempts"):
            await client.complete([])

    assert attempts == 3
    assert delays == [1, 2]


@pytest.mark.asyncio
async def test_complete_retry_keeps_initial_configuration_snapshot() -> None:
    requests: list[httpx.Request] = []
    client: OpenAICompatibleClient

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(503, text="retry", request=request)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "answer"}}]},
            request=request,
        )

    async def reconfigure_during_backoff(_delay: float) -> None:
        client.configure(provider_config(
            api_key="new-key",
            model="new-model",
            base_url="https://new.test",
        ))

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as http_client:
        client = OpenAICompatibleClient(
            provider_config(),
            http_client=http_client,
            sleep=reconfigure_during_backoff,
        )
        assert await client.complete([]) == "answer"

    assert [str(request.url) for request in requests] == [
        "https://provider.test/v1/chat/completions",
        "https://provider.test/v1/chat/completions",
    ]
    assert [request.headers["Authorization"] for request in requests] == [
        "Bearer secret-key",
        "Bearer secret-key",
    ]
    assert [__import__("json").loads(request.content)["model"] for request in requests] == [
        "deepseek-test",
        "deepseek-test",
    ]


@pytest.mark.asyncio
async def test_complete_does_not_retry_4xx() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(401, text="invalid secret-key", request=request)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as http_client:
        client = OpenAICompatibleClient(provider_config(), http_client=http_client)
        with pytest.raises(AIProviderHTTPError) as captured:
            await client.complete([])

    assert attempts == 1
    assert captured.value.status_code == 401
    assert captured.value.response_summary == "invalid <redacted>"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body",
    [
        {},
        {"choices": []},
        {"choices": [{"message": {}}]},
        {"choices": [{"message": {"content": 7}}]},
    ],
)
async def test_complete_rejects_malformed_success_without_retry(body: dict) -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(200, json=body, request=request)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as http_client:
        client = OpenAICompatibleClient(provider_config(), http_client=http_client)
        with pytest.raises(AIProviderProtocolError):
            await client.complete([])

    assert attempts == 1


@pytest.mark.asyncio
async def test_complete_rejects_closed_injected_client() -> None:
    http_client = httpx.AsyncClient()
    await http_client.aclose()
    client = OpenAICompatibleClient(provider_config(), http_client=http_client)

    with pytest.raises(
        AIProviderConfigurationError,
        match="Injected AI HTTP client is closed",
    ):
        await client.complete([])
```

- [ ] **Step 2: Run the tests and confirm the package is absent**

Run from `backend`:

```powershell
py -3 -m pytest tests/test_ai_provider_client.py -q
```

Expected: collection fails with `ModuleNotFoundError: No module named 'app.services.ai_provider'`.

- [ ] **Step 3: Add the provider ports and typed errors**

Create an empty `backend/app/services/ai_provider/__init__.py` so Task 1 uses a regular package. Task 3 replaces it with the stable export surface.

Create `backend/app/services/ai_provider/base.py`:

```python
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Protocol

AIMessage = dict[str, str]


class AICompletionClient(Protocol):
    async def complete(self, messages: list[AIMessage]) -> str: ...

    def stream(self, messages: list[AIMessage]) -> AsyncGenerator[str, None]: ...


class AIProvider(ABC):
    @abstractmethod
    async def generate_explanation(self, prompt: str) -> str: ...

    @abstractmethod
    async def review_code(self, code: str, language: str) -> str: ...

    @abstractmethod
    def stream_generate(
        self, messages: list[AIMessage]
    ) -> AsyncGenerator[str, None]: ...
```

Create `backend/app/services/ai_provider/errors.py`:

```python
class AIProviderError(Exception):
    """Base class for expected AI provider failures."""


class AIProviderConfigurationError(AIProviderError):
    """AI provider configuration is absent or unsupported."""


class AIProviderNetworkError(AIProviderError):
    def __init__(self, attempts: int) -> None:
        self.attempts = attempts
        super().__init__(f"AI provider network request failed after {attempts} attempts")


class AIProviderHTTPError(AIProviderError):
    def __init__(self, status_code: int, response_summary: str) -> None:
        self.status_code = status_code
        self.response_summary = response_summary
        super().__init__(f"AI provider returned HTTP {status_code}")


class AIProviderProtocolError(AIProviderError):
    def __init__(self, message: str, *, content_started: bool = False) -> None:
        self.content_started = content_started
        super().__init__(message)


class AIProviderStreamError(AIProviderError):
    def __init__(self, message: str, *, content_started: bool) -> None:
        self.content_started = content_started
        super().__init__(message)
```

- [ ] **Step 4: Implement non-streaming protocol and ownership primitives**

Create `backend/app/services/ai_provider/client.py` with named constants and these public methods:

```python
import asyncio
from collections.abc import AsyncGenerator, Awaitable, Callable
import json

import httpx

from app.schemas.ai import AIProviderConfig
from app.services.ai_provider.base import AIMessage
from app.services.ai_provider.errors import (
    AIProviderConfigurationError,
    AIProviderHTTPError,
    AIProviderNetworkError,
    AIProviderProtocolError,
)

DEFAULT_AI_BASE_URL = "https://api.deepseek.com"
CHAT_COMPLETIONS_PATH = "/chat/completions"
MAX_PROVIDER_ATTEMPTS = 3
RETRYABLE_STATUS_CODE = 500
ERROR_SUMMARY_LIMIT = 500
DEFAULT_TIMEOUT_SECONDS = 60.0
MAX_KEEPALIVE_CONNECTIONS = 5
MAX_CONNECTIONS = 10

Sleep = Callable[[float], Awaitable[None]]


class OpenAICompatibleClient:
    def __init__(
        self,
        config: AIProviderConfig,
        *,
        http_client: httpx.AsyncClient | None = None,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        self._config = config
        self._http_client = http_client
        self._owns_http_client = http_client is None
        self._sleep = sleep

    def configure(self, config: AIProviderConfig) -> None:
        self._config = config

    def _get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            if not self._owns_http_client:
                raise AIProviderConfigurationError(
                    "Injected AI HTTP client is closed"
                )
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(DEFAULT_TIMEOUT_SECONDS),
                limits=httpx.Limits(
                    max_keepalive_connections=MAX_KEEPALIVE_CONNECTIONS,
                    max_connections=MAX_CONNECTIONS,
                ),
            )
        return self._http_client

    def _url(self) -> str:
        base_url = self._config.base_url or DEFAULT_AI_BASE_URL
        return f"{base_url.rstrip('/')}{CHAT_COMPLETIONS_PATH}"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }

    def _payload(
        self, messages: list[AIMessage], *, stream: bool = False
    ) -> dict:
        payload = {
            "model": self._config.model,
            "messages": messages,
            "temperature": self._config.temperature,
        }
        if stream:
            payload["stream"] = True
        return payload

    def _http_error(self, response: httpx.Response) -> AIProviderHTTPError:
        try:
            response_text = response.text
            if self._config.api_key:
                response_text = response_text.replace(
                    self._config.api_key, "<redacted>"
                )
            summary = response_text[:ERROR_SUMMARY_LIMIT]
        except Exception:
            summary = "<unavailable>"
        return AIProviderHTTPError(response.status_code, summary)

    @staticmethod
    def _extract_content(response: httpx.Response) -> str:
        try:
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise AIProviderProtocolError(
                "AI provider returned an invalid completion payload"
            ) from error
        if not isinstance(content, str):
            raise AIProviderProtocolError(
                "AI provider completion content must be a string"
            )
        return content

    async def complete(self, messages: list[AIMessage]) -> str:
        client = self._get_http_client()
        url = self._url()
        headers = self._headers()
        payload = self._payload(messages)
        for attempt in range(MAX_PROVIDER_ATTEMPTS):
            try:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                )
            except httpx.RequestError as error:
                if attempt == MAX_PROVIDER_ATTEMPTS - 1:
                    raise AIProviderNetworkError(MAX_PROVIDER_ATTEMPTS) from error
                await self._sleep(attempt + 1)
                continue

            if response.is_error:
                provider_error = self._http_error(response)
                if (
                    response.status_code >= RETRYABLE_STATUS_CODE
                    and attempt < MAX_PROVIDER_ATTEMPTS - 1
                ):
                    await self._sleep(attempt + 1)
                    continue
                raise provider_error
            return self._extract_content(response)
        raise AssertionError("provider retry loop must return or raise")

    def stream(self, messages: list[AIMessage]) -> AsyncGenerator[str, None]:
        raise NotImplementedError

    async def close(self) -> None:
        if (
            self._owns_http_client
            and self._http_client is not None
            and not self._http_client.is_closed
        ):
            await self._http_client.aclose()
        if self._owns_http_client:
            self._http_client = None
```

- [ ] **Step 5: Verify Task 1 and commit**

```powershell
py -3 -m pytest tests/test_ai_provider_client.py -q
pyright
rg -n "from fastapi|HTTPException|api_key.*message|Authorization.*raise" app/services/ai_provider
git diff --check
git add app/services/ai_provider/__init__.py app/services/ai_provider/base.py app/services/ai_provider/errors.py app/services/ai_provider/client.py tests/test_ai_provider_client.py
git commit -m "refactor: extract ai provider protocol"
```

Expected: non-stream tests pass, Pyright is clean, and provider modules contain no FastAPI dependency.

---

## Task 2: Govern Streaming Protocol And Response Closure

**Files:**
- Modify: `backend/app/services/ai_provider/client.py`
- Modify: `backend/tests/test_ai_provider_client.py`

**Interfaces:**
- Consumes: Task 1 typed errors and request helpers.
- Produces: `OpenAICompatibleClient.stream(...)` with connection-only retries and `content_started` failures.
- Guarantees: `[DONE]` is required and every upstream response is closed.

- [ ] **Step 1: Add failing stream tests**

Append:

```python
class InterruptingStream(httpx.AsyncByteStream):
    def __init__(self, chunks: list[bytes], *, interrupt: bool = False) -> None:
        self.chunks = chunks
        self.interrupt = interrupt
        self.closed = False

    async def __aiter__(self):
        for chunk in self.chunks:
            yield chunk
        if self.interrupt:
            raise httpx.ReadError("stream interrupted")

    async def aclose(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_stream_yields_content_and_closes_response() -> None:
    upstream = InterruptingStream(
        [
            b'data: {"choices":[{"delta":{"content":"one"}}]}\n\n',
            b'data: {"choices":[{"delta":{"content":"two"}}]}\n\n',
            b"data: [DONE]\n\n",
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, stream=upstream)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as http_client:
        client = OpenAICompatibleClient(provider_config(), http_client=http_client)
        chunks = [chunk async for chunk in client.stream([])]

    assert chunks == ["one", "two"]
    assert upstream.closed is True


@pytest.mark.asyncio
async def test_stream_retries_5xx_handshake_only() -> None:
    attempts = 0
    delays: list[float] = []
    upstream = InterruptingStream([b"data: [DONE]\n\n"])

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return httpx.Response(503, request=request, text="retry")
        return httpx.Response(200, request=request, stream=upstream)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as http_client:
        client = OpenAICompatibleClient(
            provider_config(),
            http_client=http_client,
            sleep=recording_sleep(delays),
        )
        assert [chunk async for chunk in client.stream([])] == []

    assert attempts == 3
    assert delays == [1, 2]


@pytest.mark.asyncio
async def test_stream_retry_keeps_initial_configuration_snapshot() -> None:
    requests: list[httpx.Request] = []
    upstream = InterruptingStream([b"data: [DONE]\n\n"])
    client: OpenAICompatibleClient

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(503, request=request, text="retry")
        return httpx.Response(200, request=request, stream=upstream)

    async def reconfigure_during_backoff(_delay: float) -> None:
        client.configure(provider_config(
            api_key="new-key",
            model="new-model",
            base_url="https://new.test",
        ))

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as http_client:
        client = OpenAICompatibleClient(
            provider_config(),
            http_client=http_client,
            sleep=reconfigure_during_backoff,
        )
        assert [chunk async for chunk in client.stream([])] == []

    assert [str(request.url) for request in requests] == [
        "https://provider.test/v1/chat/completions",
        "https://provider.test/v1/chat/completions",
    ]
    assert [request.headers["Authorization"] for request in requests] == [
        "Bearer secret-key",
        "Bearer secret-key",
    ]


@pytest.mark.asyncio
async def test_stream_does_not_retry_4xx_and_redacts_summary() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(401, request=request, text="bad secret-key")

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as http_client:
        client = OpenAICompatibleClient(provider_config(), http_client=http_client)
        with pytest.raises(AIProviderHTTPError) as captured:
            [chunk async for chunk in client.stream([])]

    assert attempts == 1
    assert captured.value.status_code == 401
    assert captured.value.response_summary == "bad <redacted>"


@pytest.mark.asyncio
async def test_stream_does_not_restart_after_partial_read_failure() -> None:
    attempts = 0
    upstream = InterruptingStream(
        [b'data: {"choices":[{"delta":{"content":"partial"}}]}\n\n'],
        interrupt=True,
    )

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(200, request=request, stream=upstream)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as http_client:
        client = OpenAICompatibleClient(provider_config(), http_client=http_client)
        with pytest.raises(AIProviderStreamError) as captured:
            [chunk async for chunk in client.stream([])]

    assert captured.value.content_started is True
    assert attempts == 1
    assert upstream.closed is True


@pytest.mark.asyncio
async def test_stream_requires_done_marker() -> None:
    upstream = InterruptingStream(
        [b'data: {"choices":[{"delta":{"content":"partial"}}]}\n\n']
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, stream=upstream)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as http_client:
        client = OpenAICompatibleClient(provider_config(), http_client=http_client)
        with pytest.raises(AIProviderStreamError) as captured:
            [chunk async for chunk in client.stream([])]

    assert captured.value.content_started is True
    assert upstream.closed is True


@pytest.mark.asyncio
async def test_stream_protocol_error_records_content_state() -> None:
    upstream = InterruptingStream([b"data: not-json\n\n"])

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, stream=upstream)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as http_client:
        client = OpenAICompatibleClient(provider_config(), http_client=http_client)
        with pytest.raises(AIProviderProtocolError) as captured:
            [chunk async for chunk in client.stream([])]

    assert captured.value.content_started is False
    assert upstream.closed is True


@pytest.mark.asyncio
async def test_stream_consumer_close_closes_upstream() -> None:
    upstream = InterruptingStream(
        [
            b'data: {"choices":[{"delta":{"content":"first"}}]}\n\n',
            b'data: {"choices":[{"delta":{"content":"second"}}]}\n\n',
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, stream=upstream)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as http_client:
        client = OpenAICompatibleClient(provider_config(), http_client=http_client)
        generator = client.stream([])
        assert await anext(generator) == "first"
        await generator.aclose()

    assert upstream.closed is True
```

Import `AIProviderStreamError` in the test module.

- [ ] **Step 2: Run and confirm stream is absent**

```powershell
py -3 -m pytest tests/test_ai_provider_client.py -q
```

Expected: stream tests fail at the `NotImplementedError`.

- [ ] **Step 3: Implement connection-only retry and SSE parsing**

Add `_connect_stream`, `_parse_stream_content`, and replace `stream`:

```python
    async def _connect_stream(
        self, messages: list[AIMessage]
    ) -> httpx.Response:
        client = self._get_http_client()
        url = self._url()
        headers = self._headers()
        payload = self._payload(messages, stream=True)
        for attempt in range(MAX_PROVIDER_ATTEMPTS):
            request = client.build_request(
                "POST",
                url,
                headers=headers,
                json=payload,
            )
            response: httpx.Response | None = None
            try:
                response = await client.send(request, stream=True)
                if response.is_error:
                    await response.aread()
            except httpx.RequestError as error:
                if response is not None:
                    await response.aclose()
                if attempt == MAX_PROVIDER_ATTEMPTS - 1:
                    raise AIProviderNetworkError(MAX_PROVIDER_ATTEMPTS) from error
                await self._sleep(attempt + 1)
                continue

            if response.is_error:
                provider_error = self._http_error(response)
                await response.aclose()
                if (
                    response.status_code >= RETRYABLE_STATUS_CODE
                    and attempt < MAX_PROVIDER_ATTEMPTS - 1
                ):
                    await self._sleep(attempt + 1)
                    continue
                raise provider_error
            return response
        raise AssertionError("stream retry loop must return or raise")

    @staticmethod
    def _parse_stream_content(data: str, *, content_started: bool) -> str:
        try:
            payload = json.loads(data)
            delta = payload["choices"][0]["delta"]
            content = delta.get("content", "")
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise AIProviderProtocolError(
                "AI provider returned an invalid stream payload",
                content_started=content_started,
            ) from error
        if not isinstance(content, str):
            raise AIProviderProtocolError(
                "AI provider stream content must be a string",
                content_started=content_started,
            )
        return content

    async def stream(
        self, messages: list[AIMessage]
    ) -> AsyncGenerator[str, None]:
        response = await self._connect_stream(messages)
        content_started = False
        done = False
        try:
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    done = True
                    break
                content = self._parse_stream_content(
                    data, content_started=content_started
                )
                if content:
                    content_started = True
                    yield content
            if not done:
                raise AIProviderStreamError(
                    "AI provider stream ended before completion",
                    content_started=content_started,
                )
        except AIProviderError:
            raise
        except (httpx.RequestError, httpx.StreamError) as error:
            raise AIProviderStreamError(
                "AI provider stream was interrupted",
                content_started=content_started,
            ) from error
        finally:
            await response.aclose()
```

Import `AIProviderError` and `AIProviderStreamError` in `client.py`.

- [ ] **Step 4: Add close ownership tests**

Append:

```python
@pytest.mark.asyncio
async def test_close_does_not_close_injected_http_client() -> None:
    http_client = httpx.AsyncClient()
    client = OpenAICompatibleClient(provider_config(), http_client=http_client)

    await client.close()

    assert http_client.is_closed is False
    await http_client.aclose()


@pytest.mark.asyncio
async def test_close_closes_and_clears_owned_http_client() -> None:
    client = OpenAICompatibleClient(provider_config())
    internal = client._get_http_client()

    await client.close()
    await client.close()

    assert internal.is_closed is True
    assert client._http_client is None
```

- [ ] **Step 5: Verify Task 2 and commit**

```powershell
py -3 -m pytest tests/test_ai_provider_client.py -q
pyright
rg -n "for attempt|sleep\(|aclose\(|\[DONE\]" app/services/ai_provider/client.py
git diff --check
git add app/services/ai_provider/client.py tests/test_ai_provider_client.py
git commit -m "refactor: govern ai provider streaming"
```

Expected: stream tests and ownership tests pass with no raw response leak.

---

## Task 3: Extract The Provider Adapter And Rewire `AIService`

**Files:**
- Create: `backend/app/services/ai_provider/openai.py`
- Modify: `backend/app/services/ai_provider/__init__.py`
- Modify: `backend/app/services/ai.py`
- Modify: `backend/tests/test_ai.py`

**Interfaces:**
- Consumes: `AIProvider`, `AICompletionClient`, and `OpenAICompatibleClient`.
- Produces: `OpenAICompatibleProvider` and compatibility alias `OpenAIProvider`.
- Produces: `AIService(http_client=None)`, `_require_provider()`, reused protocol client, and typed unsupported-provider failure.
- Preserves: every existing public `AIService` method and unconfigured fallback.

- [ ] **Step 1: Add failing adapter and service tests**

Add imports and tests to `test_ai.py`:

```python
import httpx
from collections.abc import AsyncGenerator

from app.services.ai_provider import (
    AIProviderConfigurationError,
    OpenAICompatibleProvider,
)


class RecordingCompletionClient:
    def __init__(self) -> None:
        self.messages: list[list[dict[str, str]]] = []

    async def complete(self, messages: list[dict[str, str]]) -> str:
        self.messages.append(messages)
        return "provider answer"

    async def stream(
        self, messages: list[dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        self.messages.append(messages)
        yield "streamed"


@pytest.mark.asyncio
async def test_openai_adapter_builds_existing_explanation_messages() -> None:
    client = RecordingCompletionClient()
    provider = OpenAICompatibleProvider(client)

    assert await provider.generate_explanation("question") == "provider answer"
    assert client.messages == [[
        {
            "role": "system",
            "content": "你是一位耐心的编程老师，擅长分析学生的错误并给出建设性的反馈。",
        },
        {"role": "user", "content": "question"},
    ]]


@pytest.mark.asyncio
async def test_openai_adapter_builds_existing_code_review_messages() -> None:
    client = RecordingCompletionClient()
    provider = OpenAICompatibleProvider(client)

    assert await provider.review_code("print(1)", "python") == "provider answer"
    assert client.messages[0][0]["content"] == (
        "你是一位资深的代码审查专家，擅长发现代码问题并给出优化建议。"
    )
    assert client.messages[0][1]["content"] == "请审查以下python代码：\n\nprint(1)"


@pytest.mark.asyncio
async def test_openai_adapter_delegates_stream_messages() -> None:
    client = RecordingCompletionClient()
    provider = OpenAICompatibleProvider(client)
    messages = [{"role": "user", "content": "hello"}]

    assert [chunk async for chunk in provider.stream_generate(messages)] == [
        "streamed"
    ]
    assert client.messages == [messages]


@pytest.mark.asyncio
async def test_ai_service_reconfigure_reuses_protocol_client() -> None:
    http_client = httpx.AsyncClient()
    service = AIService(http_client=http_client)
    first = AIProviderConfig(
        provider="deepseek",
        api_key="one",
        model="model-one",
        temperature=0.1,
        base_url="https://one.test",
    )
    second = first.model_copy(
        update={"api_key": "two", "model": "model-two", "base_url": "https://two.test"}
    )

    service.configure(first)
    protocol_client = service._protocol_client
    service.configure(second)

    assert service._protocol_client is protocol_client
    assert service._protocol_client._config == second
    assert isinstance(service.provider, OpenAICompatibleProvider)
    await http_client.aclose()


def test_ai_service_rejects_unsupported_provider_without_mutating_state() -> None:
    service = AIService()
    valid = AIProviderConfig(
        provider="deepseek",
        api_key="one",
        model="model-one",
        temperature=0.1,
    )
    service.configure(valid)
    original_provider = service.provider

    with pytest.raises(AIProviderConfigurationError, match="Unsupported AI provider"):
        service.configure(valid.model_copy(update={"provider": "unknown"}))

    assert service.provider is original_provider


@pytest.mark.asyncio
async def test_ai_service_preserves_unconfigured_friendly_response() -> None:
    service = AIService()

    assert await service.generate_chat("hello") == "AI 服务未配置，请联系管理员。"
```

Convert `test_ai_service_configure_deepseek_provider` to assert the new adapter and close any locally-created service in async tests where its owned HTTP client was opened.

- [ ] **Step 2: Run and confirm adapter package exports are absent**

```powershell
py -3 -m pytest tests/test_ai.py -q
```

Expected: import fails for `OpenAICompatibleProvider`.

- [ ] **Step 3: Implement the teaching adapter**

Create `backend/app/services/ai_provider/openai.py`:

```python
from collections.abc import AsyncGenerator

from app.services.ai_provider.base import (
    AICompletionClient,
    AIMessage,
    AIProvider,
)

EXPLANATION_SYSTEM_PROMPT = (
    "你是一位耐心的编程老师，擅长分析学生的错误并给出建设性的反馈。"
)
CODE_REVIEW_SYSTEM_PROMPT = (
    "你是一位资深的代码审查专家，擅长发现代码问题并给出优化建议。"
)
CODE_REVIEW_USER_TEMPLATE = "请审查以下{language}代码：\n\n{code}"


class OpenAICompatibleProvider(AIProvider):
    def __init__(self, client: AICompletionClient) -> None:
        self._client = client

    @staticmethod
    def _message(role: str, content: str) -> AIMessage:
        return {"role": role, "content": content}

    async def generate_explanation(self, prompt: str) -> str:
        return await self._client.complete([
            self._message("system", EXPLANATION_SYSTEM_PROMPT),
            self._message("user", prompt),
        ])

    async def review_code(self, code: str, language: str) -> str:
        return await self._client.complete([
            self._message("system", CODE_REVIEW_SYSTEM_PROMPT),
            self._message(
                "user",
                CODE_REVIEW_USER_TEMPLATE.format(language=language, code=code),
            ),
        ])

    async def stream_generate(
        self, messages: list[AIMessage]
    ) -> AsyncGenerator[str, None]:
        async for chunk in self._client.stream(messages):
            yield chunk
```

Replace the empty `backend/app/services/ai_provider/__init__.py` with exports for every port, error, client, and adapter.

- [ ] **Step 4: Rewire `AIService` without changing teaching methods**

In `ai.py`:

1. remove raw `asyncio`, `json`, and `httpx` imports only when no remaining domain method needs them;
2. delete old `AIProvider` and `OpenAIProvider` class bodies;
3. import package types and define `OpenAIProvider = OpenAICompatibleProvider`;
4. implement the service constructor and configure flow:

```python
class AIService:
    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        self._provider: AIProvider | None = None
        self._config: AIProviderConfig | None = None
        self._protocol_client: OpenAICompatibleClient | None = None
        self._http_client = http_client

    def configure(self, config: AIProviderConfig) -> None:
        if config.provider not in {"openai", "siliconflow", "deepseek"}:
            raise AIProviderConfigurationError(
                f"Unsupported AI provider: {config.provider}"
            )
        if self._protocol_client is None:
            self._protocol_client = OpenAICompatibleClient(
                config,
                http_client=self._http_client,
            )
        else:
            self._protocol_client.configure(config)
        self._provider = OpenAICompatibleProvider(self._protocol_client)
        self._config = config

    def _require_provider(self) -> AIProvider:
        if self._provider is None:
            raise AIProviderConfigurationError("AI service is not configured")
        return self._provider
```

After every existing unconfigured guard, replace `assert self._provider is not None` with a local `provider = self._require_provider()` and call that local. Do not remove or alter any friendly fallback text/dict/yield.

- [ ] **Step 5: Verify compatibility and commit Task 3**

```powershell
py -3 -m pytest tests/test_ai.py tests/test_ai_mastery_quiz.py tests/test_ai_policy.py -q
pyright
rg -n "class OpenAIProvider|class AIProvider|assert self\._provider|_call_api|_stream_connect" app/services/ai.py
rg -n "OpenAIProvider" app tests
git diff --check
git add app/services/ai_provider/__init__.py app/services/ai_provider/openai.py app/services/ai.py tests/test_ai.py
git commit -m "refactor: isolate ai provider adapter"
```

Expected: no old provider implementation or provider asserts remain in `ai.py`; the compatibility alias and tests remain.

---

## Task 4: Close Provider Resources In Application Lifespan

**Files:**
- Modify: `backend/app/services/ai.py`
- Modify: `backend/app/core/lifespan.py`
- Modify: `backend/tests/test_ai.py`
- Create: `backend/tests/test_ai_lifespan.py`

**Interfaces:**
- Consumes: Task 3 reused `OpenAICompatibleClient`.
- Produces: idempotent `AIService.aclose()`.
- Guarantees: FastAPI shutdown closes the global service even when lifespan body raises; injected HTTP clients remain open.

- [ ] **Step 1: Add failing service-close tests**

Append to `test_ai.py`:

```python
@pytest.mark.asyncio
async def test_ai_service_close_closes_owned_protocol_client() -> None:
    service = AIService()
    service.configure(AIProviderConfig(
        provider="deepseek",
        api_key="key",
        model="model",
        temperature=0.1,
    ))
    internal = service._protocol_client._get_http_client()

    await service.aclose()
    await service.aclose()

    assert internal.is_closed is True


@pytest.mark.asyncio
async def test_ai_service_close_preserves_injected_http_client() -> None:
    http_client = httpx.AsyncClient()
    service = AIService(http_client=http_client)
    service.configure(AIProviderConfig(
        provider="deepseek",
        api_key="key",
        model="model",
        temperature=0.1,
    ))

    await service.aclose()

    assert http_client.is_closed is False
    await http_client.aclose()
```

- [ ] **Step 2: Add failing lifespan-finally tests**

Create `backend/tests/test_ai_lifespan.py`:

```python
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.config import Settings
from app.core.lifespan import create_lifespan


def lifespan_settings() -> Settings:
    return Settings(
        SECRET_KEY="test-secret-key-that-is-long-enough-123",
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        AI_PROVIDER="deepseek",
        AI_API_KEY="",
        AI_MODEL="deepseek-test",
    )


@pytest.mark.asyncio
async def test_lifespan_closes_ai_service_after_normal_exit() -> None:
    with patch("app.core.lifespan.init_db", new=AsyncMock()) as init_db:
        with patch("app.core.lifespan.configure_ai_service", new=Mock()) as configure:
            with patch(
                "app.core.lifespan.ai_service.aclose", new=AsyncMock()
            ) as close:
                async with create_lifespan(lifespan_settings())(Mock()):
                    pass

    init_db.assert_awaited_once()
    configure.assert_called_once()
    close.assert_awaited_once()


@pytest.mark.asyncio
async def test_lifespan_closes_ai_service_when_application_body_fails() -> None:
    with patch("app.core.lifespan.init_db", new=AsyncMock()):
        with patch("app.core.lifespan.configure_ai_service", new=Mock()):
            with patch(
                "app.core.lifespan.ai_service.aclose", new=AsyncMock()
            ) as close:
                with pytest.raises(RuntimeError, match="application failed"):
                    async with create_lifespan(lifespan_settings())(Mock()):
                        raise RuntimeError("application failed")

    close.assert_awaited_once()
```

- [ ] **Step 3: Run and confirm `aclose` is absent**

```powershell
py -3 -m pytest tests/test_ai.py tests/test_ai_lifespan.py -q
```

Expected: failures because `AIService.aclose` does not exist and lifespan does not close it.

- [ ] **Step 4: Implement service close and lifespan `finally`**

In `AIService`:

```python
    async def aclose(self) -> None:
        if self._protocol_client is not None:
            await self._protocol_client.close()
```

In `create_lifespan`:

```python
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        configure_logging()
        await init_db()
        configure_ai_service(settings)
        try:
            yield
        finally:
            await ai_service.aclose()
```

- [ ] **Step 5: Verify Task 4 and commit**

```powershell
py -3 -m pytest tests/test_ai_provider_client.py tests/test_ai.py tests/test_ai_lifespan.py tests/test_ai_mastery_quiz.py tests/test_ai_policy.py -q
pyright
rg -n "ai_service\.aclose|finally:" app/core/lifespan.py tests/test_ai_lifespan.py
git diff --check
git add app/services/ai.py app/core/lifespan.py tests/test_ai.py tests/test_ai_lifespan.py
git commit -m "fix: close ai provider resources"
```

Expected: all focused tests pass and external clients remain caller-owned.

---

## Task 5: Validate, Document, And Maintain AI Provider 4A

**Files:**
- Modify: `docs/superpowers/specs/2026-07-15-backend-learning-oriented-governance-design.md`
- Modify: `docs/superpowers/plans/2026-07-17-ai-provider-protocol-governance.md`

**Interfaces:**
- Consumes: completed Tasks 1-4.
- Produces: durable 4A completion evidence and CodeGraph ownership record.

- [ ] **Step 1: Run the full backend gate**

From repository root:

```powershell
py -3 -m pytest backend/tests -q -rs
pyright -p backend/pyrightconfig.json
```

Expected: every backend test passes, no skipped section is printed, and Pyright reports zero diagnostics.

- [ ] **Step 2: Run scope, protocol, and secret-safety searches**

```powershell
rg -n "class OpenAIProvider|class AIProvider|_call_api|_stream_connect|assert self\._provider|from fastapi|HTTPException" backend/app/services/ai.py backend/app/services/ai_provider
rg -n "MAX_PROVIDER_ATTEMPTS|RETRYABLE_STATUS_CODE|AIProvider(Network|HTTP|Protocol|Stream|Configuration)Error|aclose" backend/app backend/tests
rg -n "quota_service|CoreService|AIHintCache|deduct|refund" backend/app/services/ai_provider backend/app/services/ai.py
$mergeBase = git merge-base main HEAD
git diff --name-only "$mergeBase..HEAD"
git diff --check "$mergeBase..HEAD"
```

Confirm no Router response, hint cost/cache/refund, Core, embedding, frontend, schema, or database source changed. Complete Rule 10 DRY, dependency, naming, magic-value, function-length, dead-code, and type-safety review.

- [ ] **Step 3: Start FastAPI and Next.js and request live contracts**

Use a test-only secret, isolated SQLite database, hidden managed processes, and free ports. Verify:

```text
GET  /health                         -> 200
GET  /                               -> 200 after compile
GET  /arena                          -> 200 after compile
POST /api/auth/register              -> 201 bearer token
GET  /api/ai/exercise-hint/cache/ex1/light -> 200 existing cache-miss fields
```

Also run a deterministic in-process `httpx.MockTransport` smoke through `AIService.generate_chat` and `AIService.stream_chat` rather than calling a real paid provider. Inspect logs and listener command lines, stop only owned process trees, prove ports free, remove only resolved worktree-local artifacts, and preserve the `frontend/node_modules` junction.

- [ ] **Step 4: Synchronize and inspect CodeGraph**

```powershell
npx codegraph init .
npx codegraph sync .
npx codegraph impact -p . OpenAICompatibleClient
npx codegraph impact -p . OpenAICompatibleProvider
npx codegraph impact -p . AIService
npx codegraph query -p . _call_api
npx codegraph query -p . _stream_connect
```

Expected: `AIService -> OpenAICompatibleProvider -> OpenAICompatibleClient -> httpx` is the external call chain; old raw protocol methods have no result.

- [ ] **Step 5: Record completion evidence**

Append a fourth-stage 4A record to the global governance design. Add `## Completion Evidence` here with exact TDD red/green output, focused/full counts, Pyright, live statuses, MockTransport evidence, CodeGraph edges, commits, review findings, the temporary alias, and remaining 4B/multi-worker risks.

- [ ] **Step 6: Commit the completion records**

```powershell
git add docs/superpowers/specs/2026-07-15-backend-learning-oriented-governance-design.md docs/superpowers/plans/2026-07-17-ai-provider-protocol-governance.md
git commit -m "docs: record ai provider governance batch"
```

---

## Plan Self-Review

- Spec coverage: Tasks 1-4 cover typed errors, request construction, retry ownership, protocol parsing, stream closure, provider adapter, service reconfiguration, compatibility fallback, and application shutdown. Task 5 covers every project validation and maintenance gate.
- Scope: hint billing/cache/refund, Core, quota admin, embedding, frontend, database/schema, and configuration persistence remain unchanged.
- Type consistency: `AIMessage`, `AICompletionClient`, `AIProvider`, `OpenAICompatibleClient`, `OpenAICompatibleProvider`, `AIService._protocol_client`, and every error name match across tasks.
- Retry consistency: all tests and implementation use exactly 3 total attempts and delays `[1, 2]`; no post-handshake stream restart is introduced.
- TDD order: every production behavior or extraction has an explicit failing import, missing method, or `NotImplementedError` test before implementation.
- Placeholder scan: no unfinished implementation instruction remains.

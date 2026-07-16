from collections.abc import Awaitable, Callable
import traceback

import httpx
import pytest

from app.schemas.ai import AIProviderConfig
from app.services.ai_provider.client import OpenAICompatibleClient
from app.services.ai_provider.errors import (
    AIProviderConfigurationError,
    AIProviderHTTPError,
    AIProviderNetworkError,
    AIProviderProtocolError,
    AIProviderStreamError,
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
async def test_complete_retries_timeout_three_total_attempts() -> None:
    attempts = 0
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ReadTimeout("slow provider", request=request)

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
async def test_complete_does_not_retry_or_expose_request_protocol_error() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.LocalProtocolError(
            "Authorization: Bearer secret-key",
            request=request,
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as http_client:
        client = OpenAICompatibleClient(provider_config(), http_client=http_client)
        with pytest.raises(AIProviderProtocolError) as captured:
            await client.complete([])

    formatted = "".join(traceback.format_exception(captured.value))
    assert attempts == 1
    assert "secret-key" not in formatted
    assert "Authorization" not in formatted


@pytest.mark.asyncio
async def test_complete_does_not_retry_non_5xx_extension_status() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(600, text="extension failure", request=request)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as http_client:
        client = OpenAICompatibleClient(provider_config(), http_client=http_client)
        with pytest.raises(AIProviderHTTPError) as captured:
            await client.complete([])

    assert attempts == 1
    assert captured.value.status_code == 600


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


class InterruptingStream(httpx.AsyncByteStream):
    def __init__(
        self,
        chunks: list[bytes],
        *,
        interrupt: bool = False,
        interruption_message: str = "stream interrupted",
    ) -> None:
        self.chunks = chunks
        self.interrupt = interrupt
        self.interruption_message = interruption_message
        self.closed = False

    async def __aiter__(self):
        for chunk in self.chunks:
            yield chunk
        if self.interrupt:
            raise httpx.ReadError(self.interruption_message)

    async def aclose(self) -> None:
        self.closed = True


class TimeoutStream(InterruptingStream):
    async def __aiter__(self):
        for chunk in self.chunks:
            yield chunk
        raise httpx.ReadTimeout("slow error body")


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
async def test_stream_does_not_retry_4xx_when_error_body_times_out() -> None:
    attempts = 0
    upstream = TimeoutStream([])

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(401, request=request, stream=upstream)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as http_client:
        client = OpenAICompatibleClient(
            provider_config(),
            http_client=http_client,
            sleep=recording_sleep([]),
        )
        with pytest.raises(AIProviderHTTPError) as captured:
            [chunk async for chunk in client.stream([])]

    assert attempts == 1
    assert captured.value.status_code == 401
    assert upstream.closed is True


@pytest.mark.asyncio
async def test_stream_does_not_retry_or_expose_request_protocol_error() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.LocalProtocolError(
            "Authorization: Bearer secret-key",
            request=request,
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as http_client:
        client = OpenAICompatibleClient(provider_config(), http_client=http_client)
        with pytest.raises(AIProviderProtocolError) as captured:
            [chunk async for chunk in client.stream([])]

    formatted = "".join(traceback.format_exception(captured.value))
    assert attempts == 1
    assert "secret-key" not in formatted
    assert "Authorization" not in formatted


@pytest.mark.asyncio
async def test_stream_does_not_retry_non_5xx_extension_status() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(600, text="extension failure", request=request)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as http_client:
        client = OpenAICompatibleClient(provider_config(), http_client=http_client)
        with pytest.raises(AIProviderHTTPError) as captured:
            [chunk async for chunk in client.stream([])]

    assert attempts == 1
    assert captured.value.status_code == 600


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
async def test_stream_interruption_does_not_expose_request_details() -> None:
    upstream = InterruptingStream(
        [b'data: {"choices":[{"delta":{"content":"partial"}}]}\n\n'],
        interrupt=True,
        interruption_message="Authorization: Bearer secret-key",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, stream=upstream)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as http_client:
        client = OpenAICompatibleClient(provider_config(), http_client=http_client)
        with pytest.raises(AIProviderStreamError) as captured:
            [chunk async for chunk in client.stream([])]

    formatted = "".join(traceback.format_exception(captured.value))
    assert captured.value.content_started is True
    assert "secret-key" not in formatted
    assert "Authorization" not in formatted
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

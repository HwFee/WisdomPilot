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

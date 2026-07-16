import asyncio
from collections.abc import AsyncGenerator, Awaitable, Callable

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

    @staticmethod
    def _url(config: AIProviderConfig) -> str:
        base_url = config.base_url or DEFAULT_AI_BASE_URL
        return f"{base_url.rstrip('/')}{CHAT_COMPLETIONS_PATH}"

    @staticmethod
    def _headers(config: AIProviderConfig) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _payload(
        config: AIProviderConfig,
        messages: list[AIMessage],
        *,
        stream: bool = False,
    ) -> dict:
        payload = {
            "model": config.model,
            "messages": messages,
            "temperature": config.temperature,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def _http_error(
        response: httpx.Response,
        api_key: str,
    ) -> AIProviderHTTPError:
        try:
            response_text = response.text
            if api_key:
                response_text = response_text.replace(api_key, "<redacted>")
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
        config = self._config
        client = self._get_http_client()
        url = self._url(config)
        headers = self._headers(config)
        payload = self._payload(config, messages)
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
                provider_error = self._http_error(response, config.api_key)
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

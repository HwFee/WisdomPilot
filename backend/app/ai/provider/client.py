import asyncio
from collections.abc import AsyncGenerator, Awaitable, Callable
import json

import httpx

from app.ai.config import AIProviderConfig
from app.ai.provider.base import AIMessage
from app.ai.provider.errors import (
    AIProviderConfigurationError,
    AIProviderHTTPError,
    AIProviderNetworkError,
    AIProviderProtocolError,
    AIProviderStreamError,
)

DEFAULT_AI_BASE_URL = "https://api.deepseek.com"
CHAT_COMPLETIONS_PATH = "/chat/completions"
MAX_PROVIDER_ATTEMPTS = 3
HTTP_ERROR_STATUS_CODE = 400
RETRYABLE_STATUS_CODE = 500
SERVER_ERROR_STATUS_CODE_LIMIT = 600
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
    def _is_http_error(response: httpx.Response) -> bool:
        return response.status_code >= HTTP_ERROR_STATUS_CODE

    @staticmethod
    def _is_retryable_status(status_code: int) -> bool:
        return RETRYABLE_STATUS_CODE <= status_code < SERVER_ERROR_STATUS_CODE_LIMIT

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

    async def _send_request(
        self,
        client: httpx.AsyncClient,
        request: httpx.Request,
        *,
        stream: bool,
    ) -> tuple[httpx.Response | None, bool]:
        response: httpx.Response | None = None
        try:
            response = await client.send(request, stream=stream)
        except (httpx.ConnectError, httpx.TimeoutException):
            if response is not None:
                await response.aclose()
            return None, True
        except httpx.RequestError:
            if response is not None:
                await response.aclose()
            return None, False
        if stream and self._is_http_error(response):
            try:
                await response.aread()
            except (httpx.RequestError, httpx.StreamError):
                pass
        return response, False

    async def _request_with_retries(
        self,
        messages: list[AIMessage],
        *,
        stream: bool,
    ) -> httpx.Response:
        config = self._config
        client = self._get_http_client()
        url = self._url(config)
        headers = self._headers(config)
        payload = self._payload(config, messages, stream=stream)
        for attempt in range(MAX_PROVIDER_ATTEMPTS):
            request = client.build_request("POST", url, headers=headers, json=payload)
            response, retryable_failure = await self._send_request(
                client, request, stream=stream
            )
            if response is None:
                if not retryable_failure:
                    raise AIProviderProtocolError(
                        "AI provider request failed before receiving a response"
                    )
                if attempt == MAX_PROVIDER_ATTEMPTS - 1:
                    raise AIProviderNetworkError(MAX_PROVIDER_ATTEMPTS)
                await self._sleep(attempt + 1)
                continue
            if self._is_http_error(response):
                provider_error = self._http_error(response, config.api_key)
                await response.aclose()
                if (
                    self._is_retryable_status(response.status_code)
                    and attempt < MAX_PROVIDER_ATTEMPTS - 1
                ):
                    await self._sleep(attempt + 1)
                    continue
                raise provider_error
            return response
        raise AssertionError("provider retry loop must return or raise")

    async def complete(self, messages: list[AIMessage]) -> str:
        response = await self._request_with_retries(messages, stream=False)
        return self._extract_content(response)

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
        response = await self._request_with_retries(messages, stream=True)
        content_started = False
        done = False
        stream_interrupted = False
        try:
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
            except (httpx.RequestError, httpx.StreamError):
                stream_interrupted = True
            if stream_interrupted:
                raise AIProviderStreamError(
                    "AI provider stream was interrupted",
                    content_started=content_started,
                )
            if not done:
                raise AIProviderStreamError(
                    "AI provider stream ended before completion",
                    content_started=content_started,
                )
        finally:
            await response.aclose()

    async def close(self) -> None:
        if (
            self._owns_http_client
            and self._http_client is not None
            and not self._http_client.is_closed
        ):
            await self._http_client.aclose()
        if self._owns_http_client:
            self._http_client = None

"""OpenAI 兼容的底层 HTTP 客户端。

本文件实现 ``OpenAICompatibleClient`` -- 负责与 AI 大模型 API 进行实际
HTTP 通信的底层客户端。它兼容所有实现了 OpenAI Chat Completions API
规范的服务商（DeepSeek、SiliconFlow、OpenAI 本身等）。

核心职责：
1. **请求构造**：将配置 + messages 组装为符合 OpenAI 格式的 HTTP 请求。
2. **重试机制**：对网络错误和 5xx 服务端错误自动重试（最多 3 次）。
3. **响应解析**：
   - 非流式：从 JSON 响应中提取 ``choices[0].message.content``。
   - 流式：解析 SSE（Server-Sent Events）数据流，逐块 yield 文本。
4. **错误处理**：将 httpx 异常转化为语义化的 ``AIProvider*Error`` 异常。
5. **连接管理**：懒初始化 httpx.AsyncClient，支持外部注入或自建。

设计要点：
- 所有 HTTP 通信通过 ``httpx.AsyncClient`` 异步执行，不阻塞事件循环。
- API Key 在错误日志中自动脱敏，防止密钥泄露。
- 流式解析严格遵循 SSE 协议（``data: <json>\\n`` 格式），正确处理 ``[DONE]`` 标记。
"""

import asyncio
from collections.abc import AsyncGenerator, Awaitable, Callable
import json

# 第三方异步 HTTP 客户端：承载本模块全部网络通信（httpx.AsyncClient）
import httpx

# 内部模块：AI 提供商配置（config）、对话消息类型（base）、语义化异常（errors）
from app.ai.config import AIProviderConfig
from app.ai.provider.base import AIMessage
from app.ai.provider.errors import (
    AIProviderConfigurationError,
    AIProviderHTTPError,
    AIProviderNetworkError,
    AIProviderProtocolError,
    AIProviderStreamError,
)

# ---- 常量定义 ----
# 这些常量集中管理 HTTP 通信的参数，避免魔法数字散落在代码中。

DEFAULT_AI_BASE_URL = "https://api.deepseek.com"  # 默认 AI API 根地址（DeepSeek）
CHAT_COMPLETIONS_PATH = "/chat/completions"  # Chat Completions 端点路径
MAX_PROVIDER_ATTEMPTS = 3  # 最大重试次数（含首次请求）
HTTP_ERROR_STATUS_CODE = 400  # HTTP 错误状态码下限（>=400 视为错误）
RETRYABLE_STATUS_CODE = 500  # 可重试的状态码下限（5xx 服务端错误才重试）
SERVER_ERROR_STATUS_CODE_LIMIT = 600  # 服务端错误状态码上限（5xx 范围）
ERROR_SUMMARY_LIMIT = 500  # 错误响应体摘要的最大字符数
DEFAULT_TIMEOUT_SECONDS = 60.0  # HTTP 请求默认超时时间（秒）
MAX_KEEPALIVE_CONNECTIONS = 5  # 连接池最大保活连接数
MAX_CONNECTIONS = 10  # 连接池最大连接数

# Sleep 函数类型别名，用于依赖注入（测试时可替换为 mock）
Sleep = Callable[[float], Awaitable[None]]


# ---------------------------------------------------------------------------
# OpenAICompatibleClient - OpenAI 兼容 AI HTTP 客户端
# ---------------------------------------------------------------------------


class OpenAICompatibleClient:
    """OpenAI 兼容的 AI HTTP 客户端。

    本类是 AI 通信的底层实现，负责构造 HTTP 请求、管理重试、解析响应。
    它实现了 ``AICompletionClient`` 协议（鸭子类型，无需显式继承）。

    两种工作模式：
    1. **自建 HTTP 客户端**（默认）：内部懒创建 ``httpx.AsyncClient``，
       在 ``close()`` 时负责销毁。
    2. **外部注入 HTTP 客户端**：由调用方传入已配置好的 ``httpx.AsyncClient``，
       本类不负责其生命周期管理（适合在应用级别共享连接池）。

    Attributes:
        _config: AI 提供商配置（API Key、模型、base_url 等）。
        _http_client: httpx 异步客户端实例，可能为 None（懒初始化）。
        _owns_http_client: 是否由本类创建 HTTP 客户端（决定 close 时是否销毁）。
        _sleep: sleep 函数，用于重试间隔（测试时可注入 mock）。
    """

    def __init__(
        self,
        config: AIProviderConfig,
        *,
        http_client: httpx.AsyncClient | None = None,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        """初始化客户端。

        Args:
            config: AI 提供商配置。
            http_client: 可选的外部 httpx 客户端。若为 None，则在首次
                请求时懒创建内部客户端。传入外部客户端时本类不负责关闭。
            sleep: sleep 函数，用于重试退避。默认为 ``asyncio.sleep``，
                测试时可注入同步 mock 来加速测试。
        """
        self._config = config
        self._http_client = http_client
        # 记录是否由本类拥有 HTTP 客户端，决定 close() 时是否需要销毁
        self._owns_http_client = http_client is None
        self._sleep = sleep

    def configure(self, config: AIProviderConfig) -> None:
        """更新 AI 提供商配置（运行时热切换）。

        在应用重新加载配置时调用，无需重建客户端实例即可更新 API Key、
        模型等参数。

        Args:
            config: 新的 AI 提供商配置。
        """
        # 仅替换配置引用：API Key/模型/温度热切换时无需重建 HTTP 客户端，连接池继续复用
        self._config = config

    def _get_http_client(self) -> httpx.AsyncClient:
        """获取可用的 HTTP 客户端实例（懒初始化）。

        如果内部客户端不存在或已关闭，则创建新的实例。
        若外部注入的客户端已关闭，则抛出配置异常（不应自行重建）。

        Returns:
            可用的 ``httpx.AsyncClient`` 实例。

        Raises:
            AIProviderConfigurationError: 外部注入的客户端已关闭。
        """
        if self._http_client is None or self._http_client.is_closed:
            if not self._owns_http_client:
                # 外部注入的客户端被关闭了，不能自行重建
                raise AIProviderConfigurationError(
                    "Injected AI HTTP client is closed"
                )
            # 创建新的 HTTP 客户端，配置超时和连接池参数
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(DEFAULT_TIMEOUT_SECONDS),  # 连接/读/写统一 60s 超时
                limits=httpx.Limits(
                    max_keepalive_connections=MAX_KEEPALIVE_CONNECTIONS,  # 空闲保活连接数（复用可减少 TCP 握手开销）
                    max_connections=MAX_CONNECTIONS,                      # 连接池总连接数上限
                ),
            )
        return self._http_client

    @staticmethod
    def _url(config: AIProviderConfig) -> str:
        """构造完整的 Chat Completions API URL。

        Args:
            config: AI 提供商配置。

        Returns:
            完整 URL，如 ``"https://api.deepseek.com/chat/completions"``。
        """
        base_url = config.base_url or DEFAULT_AI_BASE_URL  # 回退到默认地址
        # rstrip('/') 去掉末尾斜杠：防止 base_url 以 / 结尾时拼出 //chat/completions 双斜杠
        return f"{base_url.rstrip('/')}{CHAT_COMPLETIONS_PATH}"

    @staticmethod
    def _headers(config: AIProviderConfig) -> dict[str, str]:
        """构造 HTTP 请求头。

        包含 Bearer Token 鉴头和 JSON 内容类型声明。

        Args:
            config: AI 提供商配置（从中取 API Key）。

        Returns:
            包含 ``Authorization`` 和 ``Content-Type`` 的请求头字典。
        """
        return {
            "Authorization": f"Bearer {config.api_key}",  # Bearer Token 鉴权
            "Content-Type": "application/json",  # 请求体为 JSON 格式
        }

    @staticmethod
    def _payload(
        config: AIProviderConfig,
        messages: list[AIMessage],
        *,
        stream: bool = False,
    ) -> dict:
        """构造 OpenAI Chat Completions 请求体。

        Args:
            config: AI 提供商配置（模型名、温度）。
            messages: 对话消息列表。
            stream: 是否启用流式输出。

        Returns:
            符合 OpenAI API 格式的请求体字典。
        """
        payload = {
            "model": config.model,  # 指定使用的模型
            "messages": messages,  # 对话消息列表
            "temperature": config.temperature,  # 采样温度
        }
        if stream:
            payload["stream"] = True  # 启用流式响应（SSE）
        return payload

    @staticmethod
    def _http_error(
        response: httpx.Response,
        api_key: str,
    ) -> AIProviderHTTPError:
        """从 HTTP 错误响应构造异常对象。

        提取响应体文本作为错误摘要，并自动将 API Key 替换为
        ``<redacted>`` 以防止密钥泄露到日志中。

        Args:
            response: httpx 错误响应对象。
            api_key: 当前配置的 API Key（用于脱敏替换）。

        Returns:
            包含状态码和脱敏摘要的 ``AIProviderHTTPError``。
        """
        try:
            response_text = response.text
            if api_key:
                # 将响应文本中出现的 API Key 替换为 <redacted>，防止密钥泄露
                response_text = response_text.replace(api_key, "<redacted>")
            summary = response_text[:ERROR_SUMMARY_LIMIT]  # 截取前 500 字符
        except Exception:
            summary = "<unavailable>"  # 响应体读取失败时的兜底
        return AIProviderHTTPError(response.status_code, summary)

    @staticmethod
    def _is_http_error(response: httpx.Response) -> bool:
        """判断 HTTP 响应是否为错误（状态码 >= 400）。

        Args:
            response: httpx 响应对象。

        Returns:
            True 表示响应为错误状态。
        """
        return response.status_code >= HTTP_ERROR_STATUS_CODE

    @staticmethod
    def _is_retryable_status(status_code: int) -> bool:
        """判断 HTTP 状态码是否可重试（5xx 服务端错误）。

        4xx 客户端错误（如 401 鉴权失败、400 请求格式错误）不可重试，
        只有 5xx 表示服务端临时故障，重试有可能成功。

        Args:
            status_code: HTTP 状态码。

        Returns:
            True 表示该状态码可重试（500-599 范围内）。
        """
        return RETRYABLE_STATUS_CODE <= status_code < SERVER_ERROR_STATUS_CODE_LIMIT

    @staticmethod
    def _extract_content(response: httpx.Response) -> str:
        """从非流式响应中提取 AI 生成的文本内容。

        解析 OpenAI Chat Completions 响应格式：
        ``{"choices": [{"message": {"content": "文本"}}]}``

        Args:
            response: httpx 响应对象。

        Returns:
            AI 生成的文本内容。

        Raises:
            AIProviderProtocolError: 响应格式不符合预期（缺少字段或类型错误）。
        """
        try:
            payload = response.json()
            # 按 OpenAI 格式逐层提取：choices[0].message.content
            content = payload["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as error:
            # ValueError=JSON 解析失败；KeyError/IndexError=嵌套字段缺失；TypeError=字段类型不符
            # 响应 JSON 格式不符合 OpenAI 规范
            raise AIProviderProtocolError(
                "AI provider returned an invalid completion payload"
            ) from error
        if not isinstance(content, str):
            # content 字段存在但不是字符串类型
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
        """发送单个 HTTP 请求，处理传输层异常。

        本方法是重试循环的内部步骤，只负责「发一次请求」并处理网络异常，
        不做重试决策。

        Args:
            client: httpx 异步客户端。
            request: 已构造好的 httpx 请求对象。
            stream: 是否为流式请求（影响错误响应的读取方式）。

        Returns:
            元组 ``(response, retryable_failure)``：
            - response: 成功时为 httpx.Response，失败时为 None。
            - retryable_failure: True 表示失败可重试（网络超时等），
              False 表示不可重试（其他请求错误）。
        """
        response: httpx.Response | None = None
        try:
            # stream=True 时响应体不预读：SSE 需要边接收边解析，发送本身不抛错
            response = await client.send(request, stream=stream)
        except (httpx.ConnectError, httpx.TimeoutException):
            # 连接错误或超时 -- 这类错误重试有可能成功
            if response is not None:
                await response.aclose()  # 异常发生在响应创建之后，需关闭以释放连接
            return None, True  # 可重试
        except httpx.RequestError:
            # 其他请求错误（如 DNS 解析失败）-- 重试也不太可能成功
            if response is not None:
                await response.aclose()  # 同上：清理半成品响应，防止连接泄漏
            return None, False  # 不可重试
        if stream and self._is_http_error(response):
            # 流式请求返回了错误状态码，需要先读取响应体才能释放连接
            try:
                await response.aread()
            except (httpx.RequestError, httpx.StreamError):
                pass  # 读取失败也无所谓，主要目的是释放连接
        return response, False

    async def _request_with_retries(
        self,
        messages: list[AIMessage],
        *,
        stream: bool,
    ) -> httpx.Response:
        """带重试机制的 HTTP 请求发送。

        执行最多 ``MAX_PROVIDER_ATTEMPTS`` 次请求，遇到可重试的错误
        （网络超时、5xx 服务端错误）时自动退避重试，不可重试的错误
        （4xx 客户端错误、非网络请求错误）则立即抛出。

        重试退避策略：第 N 次重试前 sleep N 秒（线性退避，非指数）。

        Args:
            messages: 对话消息列表。
            stream: 是否为流式请求。

        Returns:
            成功的 httpx 响应对象。

        Raises:
            AIProviderNetworkError: 所有重试均因网络错误失败。
            AIProviderHTTPError: 收到不可重试的 HTTP 错误状态码。
            AIProviderProtocolError: 请求在收到响应前失败。
        """
        config = self._config
        client = self._get_http_client()
        url = self._url(config)
        headers = self._headers(config)
        payload = self._payload(config, messages, stream=stream)

        # 重试循环：最多尝试 MAX_PROVIDER_ATTEMPTS 次
        for attempt in range(MAX_PROVIDER_ATTEMPTS):
            # 每轮都重新构建请求对象：httpx.Request 发送后不可复用，不能跨重试共享
            request = client.build_request("POST", url, headers=headers, json=payload)
            response, retryable_failure = await self._send_request(
                client, request, stream=stream
            )
            if response is None:
                # 请求未收到响应（网络层失败）
                if not retryable_failure:
                    # 不可重试的请求错误，直接抛出协议异常
                    raise AIProviderProtocolError(
                        "AI provider request failed before receiving a response"
                    )
                # 可重试的网络错误 -- 判断是否还有重试机会
                if attempt == MAX_PROVIDER_ATTEMPTS - 1:
                    # 已用完所有重试次数
                    raise AIProviderNetworkError(MAX_PROVIDER_ATTEMPTS)
                # 线性退避：第 1 次重试 sleep 1s，第 2 次 sleep 2s
                await self._sleep(attempt + 1)
                continue
            if self._is_http_error(response):
                # 收到了 HTTP 错误状态码 (>=400)
                provider_error = self._http_error(response, config.api_key)
                await response.aclose()  # 释放连接
                if (
                    self._is_retryable_status(response.status_code)
                    and attempt < MAX_PROVIDER_ATTEMPTS - 1
                ):
                    # 5xx 服务端错误且还有重试次数 -- 退避后重试
                    await self._sleep(attempt + 1)
                    continue
                # 4xx 客户端错误或已用完重试次数 -- 直接抛出
                raise provider_error
            # 请求成功，返回响应
            return response
        # 理论上不会到达此处（循环内必定 return 或 raise）
        raise AssertionError("provider retry loop must return or raise")

    async def complete(self, messages: list[AIMessage]) -> str:
        """非流式补全 -- 发送 messages 并等待完整响应。

        Args:
            messages: 对话消息列表。

        Returns:
            AI 生成的完整文本内容。
        """
        response = await self._request_with_retries(messages, stream=False)
        return self._extract_content(response)  # 非流式：等待完整响应后一次性提取文本

    # ---------------------------------------------------------------------------
    # 流式响应处理：SSE 帧解析 + 逐块输出
    # ---------------------------------------------------------------------------
    @staticmethod
    def _parse_stream_content(data: str, *, content_started: bool) -> str:
        """解析单个 SSE 数据帧中的文本内容。

        流式响应中每个 ``data:`` 行包含一个 JSON 对象，格式为：
        ``{"choices": [{"delta": {"content": "文本片段"}}]}``

        Args:
            data: SSE 数据帧的 JSON 字符串（已去掉 ``data: `` 前缀）。
            content_started: 在本帧之前是否已输出过内容（用于错误标记）。

        Returns:
            本帧的文本片段（可能为空字符串）。

        Raises:
            AIProviderProtocolError: 数据帧格式不符合 OpenAI 流式规范。
        """
        try:
            payload = json.loads(data)
            # OpenAI 流式格式：choices[0].delta.content
            delta = payload["choices"][0]["delta"]
            # 某些帧（如首帧）只带 role 字段没有 content，用 get 兜底视为空片段
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
        """流式补全 -- 逐块 yield AI 生成的文本。

        发送流式请求，解析 SSE 响应流，每个 ``data:`` 行解析出一个文本片段。
        正常结束的标志是收到 ``data: [DONE]`` 标记。

        Args:
            messages: 对话消息列表。

        Yields:
            AI 生成的文本片段（每个 chunk 通常是几个字到一句话）。

        Raises:
            AIProviderStreamError: 流被中断或未收到 ``[DONE]`` 就结束。
            AIProviderProtocolError: SSE 数据帧格式错误。
        """
        response = await self._request_with_retries(messages, stream=True)
        content_started = False  # 标记是否已开始输出内容（用于错误 UX）
        done = False  # 标记是否收到 [DONE] 结束标记
        stream_interrupted = False  # 标记是否因网络错误中断
        try:
            try:
                # 逐行读取 SSE 数据流
                async for line in response.aiter_lines():
                    # SSE 格式：每行以 "data: " 开头
                    if not line.startswith("data: "):
                        continue  # 跳过非数据行（如注释、空行）
                    data = line[6:]  # 去掉 "data: " 前缀
                    if data == "[DONE]":
                        # OpenAI 流式结束标记
                        done = True
                        break
                    # 解析 JSON 数据帧，提取文本片段
                    content = self._parse_stream_content(
                        data, content_started=content_started
                    )
                    if content:
                        content_started = True  # 标记已开始输出
                        yield content  # 将文本片段传递给调用方
            except (httpx.RequestError, httpx.StreamError):
                # 网络错误导致流中断
                stream_interrupted = True
            if stream_interrupted:
                # 流被网络错误中断 -- 抛出流异常
                raise AIProviderStreamError(
                    "AI provider stream was interrupted",
                    content_started=content_started,
                )
            if not done:
                # 流自然结束但未收到 [DONE] 标记 -- 也视为异常
                raise AIProviderStreamError(
                    "AI provider stream ended before completion",
                    content_started=content_started,
                )
        finally:
            # 无论成功还是异常，都要释放 HTTP 连接
            await response.aclose()

    # ---------------------------------------------------------------------------
    # 连接管理：关闭 HTTP 客户端，释放连接池
    # ---------------------------------------------------------------------------
    async def close(self) -> None:
        """关闭底层 HTTP 客户端。

        仅当 HTTP 客户端由本类创建（``_owns_http_client=True``）时才关闭，
        外部注入的客户端由调用方负责生命周期管理。
        """
        if (
            self._owns_http_client
            and self._http_client is not None
            and not self._http_client.is_closed
        ):
            await self._http_client.aclose()
        if self._owns_http_client:
            self._http_client = None  # 清除引用，允许下次 _get_http_client 重建

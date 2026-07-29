"""AI 提供商异常体系。

定义了所有 AI 调用过程中可能抛出的异常类型。它们全部继承自
``AIProviderError``，形成一棵清晰的异常树，方便上层代码用
``except AIProviderError`` 统一捕获，或按需精细处理特定异常类型。

异常层级：
::

    AIProviderError (基类)
    ├── AIProviderConfigurationError  -- 配置缺失或不支持的 provider
    ├── AIProviderNetworkError        -- 网络层失败（连接超时、DNS 等）
    ├── AIProviderHTTPError           -- HTTP 响应返回错误状态码 (>=400)
    ├── AIProviderProtocolError       -- 响应体格式不符合预期
    └── AIProviderStreamError         -- 流式传输中断或未正常结束

设计意图：将底层 HTTP/协议细节转化为语义化的业务异常，让调用方
无需理解 httpx 错误细节即可做出合理的错误处理决策。
"""


class AIProviderError(Exception):
    """Base class for expected AI provider failures.

    所有 AI 提供商异常的基类。上层代码可捕获此异常来统一处理所有 AI 相关错误，
    无需逐一列举子类。
    """


class AIProviderConfigurationError(AIProviderError):
    """AI provider configuration is absent or unsupported.

    配置异常 -- 当 ``AIService`` 尚未调用 ``configure()`` 就被使用，
    或传入了不支持的 provider 名称时抛出。
    """


class AIProviderNetworkError(AIProviderError):
    """网络异常 -- HTTP 请求在传输层失败（连接超时、DNS 解析失败等）。

    Attributes:
        attempts: 在放弃前总共尝试了多少次请求（含重试）。
    """

    def __init__(self, attempts: int) -> None:
        self.attempts = attempts  # 记录重试次数，方便排查是偶发还是持续网络问题
        super().__init__(f"AI provider network request failed after {attempts} attempts")


class AIProviderHTTPError(AIProviderError):
    """HTTP 错误异常 -- 服务器返回了错误状态码 (>= 400)。

    区分两种情况：
    - 4xx (客户端错误)：如 API Key 无效、请求格式错误，不可重试。
    - 5xx (服务端错误)：如 AI 服务过载，可重试。

    Attributes:
        status_code: HTTP 状态码（如 401, 429, 500）。
        response_summary: 错误响应体的前 N 个字符摘要（API Key 已脱敏）。
    """

    def __init__(self, status_code: int, response_summary: str) -> None:
        self.status_code = status_code  # HTTP 状态码，用于判断错误类型和是否可重试
        self.response_summary = response_summary  # 响应体摘要，用于日志排查（已脱敏）
        super().__init__(f"AI provider returned HTTP {status_code}")


class AIProviderProtocolError(AIProviderError):
    """协议错误异常 -- AI 返回的响应体格式不符合 OpenAI Chat Completions 规范。

    例如响应 JSON 中缺少 ``choices[0].message.content`` 字段，或内容不是字符串。

    Attributes:
        content_started: 在流式场景中，标记错误发生前是否已经输出了部分内容。
            若为 True，说明用户已经看到了部分文本，前端可据此决定是否提示
            「回答被中断」。
    """

    def __init__(self, message: str, *, content_started: bool = False) -> None:
        self.content_started = content_started  # 标记流式输出是否已开始，用于前端 UX 决策
        super().__init__(message)


class AIProviderStreamError(AIProviderError):
    """流式传输异常 -- 流式响应被中断或未正常结束。

    两种触发场景：
    1. 传输过程中发生网络错误（``httpx.RequestError`` / ``httpx.StreamError``）。
    2. 流未收到 ``[DONE]`` 标记就结束了。

    Attributes:
        content_started: 错误发生前是否已输出部分内容（同 ProtocolError 语义）。
    """

    def __init__(self, message: str, *, content_started: bool) -> None:
        self.content_started = content_started  # 标记是否已部分输出，前端可据此显示中断提示
        super().__init__(message)

"""provider 子包 —— AI 提供商的抽象接口、具体实现与底层 HTTP 客户端。

本子包采用「接口/实现分离」的分层设计：

- ``base.py``：定义抽象接口 —— ``AIProvider``（业务层调用的 AI 能力）
  和 ``AICompletionClient``（底层 HTTP 文本补全协议）。
- ``errors.py``：定义所有 AI 调用可能抛出的异常类型，形成统一的错误体系。
- ``client.py``：``OpenAICompatibleClient`` —— 负责实际 HTTP 请求、重试、
  流式 SSE 解析的底层客户端，兼容所有 OpenAI Chat Completions API 格式的服务商。
- ``openai.py``：``OpenAICompatibleProvider`` —— 实现 ``AIProvider`` 接口，
  将业务语义（生成解析、代码审查、流式生成）翻译为 chat messages 并委托给 client。

外部导入时统一从此 ``__init__`` 导出，避免直接引用内部模块路径。
"""

from app.ai.provider.base import (
    AICompletionClient,
    AIMessage,
    AIProvider,
)
from app.ai.provider.client import OpenAICompatibleClient
from app.ai.provider.errors import (
    AIProviderConfigurationError,
    AIProviderError,
    AIProviderHTTPError,
    AIProviderNetworkError,
    AIProviderProtocolError,
    AIProviderStreamError,
)
from app.ai.provider.openai import OpenAICompatibleProvider

# OpenAIProvider 是 OpenAICompatibleProvider 的别名，
# 方便外部代码用更简洁的名字引用（两者实现完全一致）。
OpenAIProvider = OpenAICompatibleProvider

__all__ = [
    "AICompletionClient",
    "AIMessage",
    "AIProvider",
    "AIProviderConfigurationError",
    "AIProviderError",
    "AIProviderHTTPError",
    "AIProviderNetworkError",
    "AIProviderProtocolError",
    "AIProviderStreamError",
    "OpenAICompatibleClient",
    "OpenAICompatibleProvider",
    "OpenAIProvider",
]

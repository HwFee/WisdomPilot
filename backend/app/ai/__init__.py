"""AI 基础设施模块 -- 提供商配置、统一服务入口与协议适配器。

本包是 WisdomPilot 后端与外部 AI 大语言模型（LLM）之间的桥梁层。
它将 AI 调用封装为结构化的三层架构，让上层业务代码无需关心底层 HTTP 细节：

1. **config** (`AIProviderConfig`)：用 Pydantic 模型描述「使用哪个 AI 提供商、
   用什么模型、温度多少」等配置信息。
2. **provider** 子包：定义 AI 提供商的抽象接口（`AIProvider`）、具体实现
   （`OpenAICompatibleProvider`）以及底层 HTTP 客户端（`OpenAICompatibleClient`）。
3. **service** (`AIService`)：面向业务的高层入口，封装了生成题目解析、
   代码审查、流式问答、练习题生成等教育场景方法。

模块级单例 ``ai_service`` 在应用启动时由 ``lifespan`` 注入配置，全局共享。
"""

# 配置模型：集中描述连接 LLM 所需的全部参数（provider / api_key / model 等）
from app.ai.config import AIProviderConfig
# 服务入口：面向业务的高层封装 AIService 及其全局单例 ai_service
from app.ai.service import ai_service, AIService
# provider 子包：抽象接口、异常体系与 OpenAI 兼容实现
from app.ai.provider import (
    AICompletionClient,
    AIMessage,
    AIProvider,
    AIProviderConfigurationError,
    AIProviderError,
    AIProviderHTTPError,
    AIProviderNetworkError,
    AIProviderProtocolError,
    AIProviderStreamError,
    OpenAICompatibleClient,
    OpenAICompatibleProvider,
    OpenAIProvider,
)

# 公开 API 清单：声明本包的对外导出符号，便于 from app.ai import * 与 IDE 补全
__all__ = [
    "AIService",
    "ai_service",
    "AIProviderConfig",
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

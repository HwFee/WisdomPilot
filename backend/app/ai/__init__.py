"""AI infrastructure — provider configuration, service, and protocol adapters."""

from app.ai.config import AIProviderConfig
from app.ai.service import ai_service, AIService
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

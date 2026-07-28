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

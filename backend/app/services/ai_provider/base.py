from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Protocol

AIMessage = dict[str, str]


class AICompletionClient(Protocol):
    async def complete(self, messages: list[AIMessage]) -> str: ...

    def stream(self, messages: list[AIMessage]) -> AsyncGenerator[str, None]: ...


class AIProvider(ABC):
    @abstractmethod
    async def generate_explanation(self, prompt: str) -> str: ...

    @abstractmethod
    async def review_code(self, code: str, language: str) -> str: ...

    @abstractmethod
    def stream_generate(
        self, messages: list[AIMessage]
    ) -> AsyncGenerator[str, None]: ...

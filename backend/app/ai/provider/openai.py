from collections.abc import AsyncGenerator

from app.ai.provider.base import (
    AICompletionClient,
    AIMessage,
    AIProvider,
)

EXPLANATION_SYSTEM_PROMPT = (
    "你是一位耐心的编程老师，擅长分析学生的错误并给出建设性的反馈。"
)
CODE_REVIEW_SYSTEM_PROMPT = (
    "你是一位资深的代码审查专家，擅长发现代码问题并给出优化建议。"
)
CODE_REVIEW_USER_TEMPLATE = "请审查以下{language}代码：\n\n{code}"


class OpenAICompatibleProvider(AIProvider):
    def __init__(self, client: AICompletionClient) -> None:
        self._client = client

    @staticmethod
    def _message(role: str, content: str) -> AIMessage:
        return {"role": role, "content": content}

    async def generate_explanation(self, prompt: str) -> str:
        return await self._client.complete([
            self._message("system", EXPLANATION_SYSTEM_PROMPT),
            self._message("user", prompt),
        ])

    async def review_code(self, code: str, language: str) -> str:
        return await self._client.complete([
            self._message("system", CODE_REVIEW_SYSTEM_PROMPT),
            self._message(
                "user",
                CODE_REVIEW_USER_TEMPLATE.format(language=language, code=code),
            ),
        ])

    async def stream_generate(
        self, messages: list[AIMessage]
    ) -> AsyncGenerator[str, None]:
        async for chunk in self._client.stream(messages):
            yield chunk

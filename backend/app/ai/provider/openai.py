"""OpenAI 兼容的 AI Provider 实现。

本文件实现 ``OpenAICompatibleProvider`` -- 它是 ``AIProvider`` 抽象基类
的具体实现，将业务语义（生成解析、代码审查、流式生成）翻译为符合
OpenAI Chat Completions 格式的 messages 列表，然后委托给底层的
``AICompletionClient``（通常是 ``OpenAICompatibleClient``）执行实际的
HTTP 请求。

设计意图：将「提示词工程」与「HTTP 通信」分离 -- 本文件只负责构造
合适的 system/user 消息，不关心网络重试、SSE 解析等底层细节。
"""

from collections.abc import AsyncGenerator

from app.ai.provider.base import (
    AICompletionClient,
    AIMessage,
    AIProvider,
)

# ---- 系统提示词（System Prompt）常量 ----
# 系统提示词用于设定 AI 的角色和行为基调，在每次请求中作为第一条
# {"role": "system"} 消息发送，引导模型以特定身份和风格回答。

EXPLANATION_SYSTEM_PROMPT = (
    "你是一位耐心的编程老师，擅长分析学生的错误并给出建设性的反馈。"
)
CODE_REVIEW_SYSTEM_PROMPT = (
    "你是一位资深的代码审查专家，擅长发现代码问题并给出优化建议。"
)
# 代码审查的用户消息模板，用 .format() 填入语言和代码内容
CODE_REVIEW_USER_TEMPLATE = "请审查以下{language}代码：\n\n{code}"


class OpenAICompatibleProvider(AIProvider):
    """OpenAI 兼容的 AI Provider 实现。

    本类实现了 ``AIProvider`` 抽象接口，是业务层与底层 HTTP 客户端之间的
    「翻译层」。它将每个业务方法（生成解析、代码审查、流式生成）转换为
    符合 OpenAI Chat Completions API 格式的 messages 列表，然后委托给
    持有的 ``AICompletionClient`` 执行。

    Attributes:
        _client: 底层文本补全客户端实例，负责实际的 HTTP 请求和响应解析。
    """

    def __init__(self, client: AICompletionClient) -> None:
        """初始化 Provider，注入底层客户端。

        Args:
            client: 实现了 ``AICompletionClient`` 协议的客户端实例
                （通常是 ``OpenAICompatibleClient``）。
        """
        self._client = client

    @staticmethod
    def _message(role: str, content: str) -> AIMessage:
        """构造一条标准的 chat message 字典。

        Args:
            role: 消息角色，可选 ``"system"`` / ``"user"`` / ``"assistant"``。
            content: 消息文本内容。

        Returns:
            ``{"role": role, "content": content}`` 格式的字典。
        """
        return {"role": role, "content": content}

    async def generate_explanation(self, prompt: str) -> str:
        """生成教育性文本（题目解析、知识讲解等）。

        构造 [system: 编程老师角色, user: 业务提示词] 两条消息，
        调用底层客户端的 ``complete()`` 获取完整响应。

        Args:
            prompt: 业务层构造的用户提示词，通常包含题目、选项、学生答案等。

        Returns:
            AI 生成的完整教育性文本。
        """
        return await self._client.complete([
            self._message("system", EXPLANATION_SYSTEM_PROMPT),  # 设定 AI 角色
            self._message("user", prompt),  # 业务提示词
        ])

    async def review_code(self, code: str, language: str) -> str:
        """审查学生代码并生成反馈报告。

        构造 [system: 代码审查专家角色, user: 代码内容] 两条消息，
        调用底层客户端的 ``complete()`` 获取审查结果。

        Args:
            code: 学生提交的源代码。
            language: 编程语言名称。

        Returns:
            AI 生成的代码审查报告。
        """
        return await self._client.complete([
            self._message("system", CODE_REVIEW_SYSTEM_PROMPT),  # 设定审查专家角色
            self._message(
                "user",
                CODE_REVIEW_USER_TEMPLATE.format(language=language, code=code),
            ),
        ])

    async def complete_messages(self, messages: list[AIMessage]) -> str:
        """按完整 messages 列表非流式生成文本（不自动加 system 消息）。

        与 ``generate_explanation`` 的区别：调用方自行构造全部消息
        （system / user / assistant 多轮历史），原样委托给底层客户端执行。
        用于苏格拉底导师等需要把多轮对话历史传给 LLM 的场景。

        Args:
            messages: 完整的对话消息列表。

        Returns:
            AI 生成的完整文本。
        """
        return await self._client.complete(messages)

    async def stream_generate(
        self, messages: list[AIMessage]
    ) -> AsyncGenerator[str, None]:
        """流式生成文本，逐块 yield。

        直接将传入的 messages 委托给底层客户端的 ``stream()`` 方法，
        逐块产出 AI 生成的文本片段。与 ``generate_explanation`` 不同，
        此方法不自动添加 system 消息 -- 调用方需在 messages 中自行构造。

        Args:
            messages: 完整的对话消息列表（含 system/user 等）。

        Yields:
            AI 生成的文本片段（每个 chunk 通常是几个字到一句话）。
        """
        async for chunk in self._client.stream(messages):
            yield chunk

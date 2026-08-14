"""AI 提供商抽象接口定义。

本文件定义了两个核心抽象：
1. ``AICompletionClient``：底层「文本补全客户端」协议 -- 只关心「发送
   messages，接收文本」，是 ``OpenAICompatibleClient`` 实现的接口契约。
2. ``AIProvider``：高层「AI 能力提供者」抽象类 -- 面向业务语义，定义了
   生成解析、代码审查、流式生成三个教育场景方法。

这种分层让上层业务代码依赖 ``AIProvider`` 抽象而非具体实现，
未来若要接入非 OpenAI 兼容的 AI 服务，只需新写一个 Provider 子类即可。
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Protocol

# AIMessage 是一条 chat 消息的类型别名。
# 常见格式：{"role": "system"|"user"|"assistant", "content": "文本内容"}
# 与 OpenAI Chat Completions API 的 messages 字段格式一致。
# function calling 场景下消息可携带额外字段（assistant 的 tool_calls、
# tool 角色的 tool_call_id），故值类型放宽为 object。
AIMessage = dict[str, object]


class AICompletionClient(Protocol):
    """底层文本补全客户端协议（鸭子类型接口）。

    定义了与 AI 大模型通信的最小契约：发送一组 messages，接收生成的文本。
    任何实现了 ``complete()`` 和 ``stream()`` 方法的类都自动满足此协议，
    无需显式继承。

    设计意图：用 ``Protocol`` 而非 ``ABC``，允许 ``OpenAICompatibleClient``
    不继承此类即满足接口约束，降低耦合。
    """

    async def complete(self, messages: list[AIMessage]) -> str:
        """非流式补全 -- 一次性发送全部 messages，等待完整响应后返回。

        Args:
            messages: 对话消息列表，格式为 ``[{"role": ..., "content": ...}]``。

        Returns:
            AI 生成的完整文本内容。
        """
        ...

    def stream(self, messages: list[AIMessage]) -> AsyncGenerator[str, None]:
        """流式补全 -- 发送 messages 后逐块返回生成内容。

        Args:
            messages: 对话消息列表。

        Yields:
            AI 生成的文本片段（每次 yield 一个 chunk，通常是几个字到一句话）。
        """
        ...

    async def complete_with_tools(
        self, messages: list[AIMessage], tools: list[dict]
    ) -> dict:
        """带工具声明的非流式补全（function calling）。

        Args:
            messages: 对话消息列表。
            tools: 工具声明列表（OpenAI ``tools`` 字段格式）。

        Returns:
            ``{"content": str, "tool_calls": list[dict]}``——模型直接回答时
            tool_calls 为空列表；请求调用工具时 content 可能为空串。
        """
        ...


class AIProvider(ABC):
    """高层 AI 能力提供者抽象基类。

    面向业务语义定义了三个核心方法，由具体子类（如
    ``OpenAICompatibleProvider``）实现。上层 ``AIService`` 通过此抽象
    调用 AI 能力，不关心底层 HTTP 细节。

    三个方法覆盖了 WisdomPilot 的核心 AI 场景：
    - ``generate_explanation``：生成题目解析、知识讲解等教育文本。
    - ``review_code``：对学生提交的代码进行审查和反馈。
    - ``stream_generate``：流式生成文本（用于前端实时打字效果）。
    """

    @abstractmethod
    async def generate_explanation(self, prompt: str) -> str:
        """生成教育性文本（解析、讲解等）。

        Args:
            prompt: 业务层构造的用户提示词（包含题目、选项等上下文）。

        Returns:
            AI 生成的完整文本。
        """
        ...

    @abstractmethod
    async def review_code(self, code: str, language: str) -> str:
        """审查学生代码并给出反馈。

        Args:
            code: 学生提交的源代码文本。
            language: 编程语言（如 ``"python"``、``"javascript"``）。

        Returns:
            AI 生成的代码审查报告。
        """
        ...

    @abstractmethod
    def stream_generate(
        self, messages: list[AIMessage]
    ) -> AsyncGenerator[str, None]:
        """流式生成文本（支持前端实时展示）。

        Args:
            messages: 对话消息列表。

        Yields:
            AI 生成的文本片段。
        """
        ...

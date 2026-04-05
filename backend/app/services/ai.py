"""AI 服务层 - 支持多种 AI 提供商，与原有代码完全隔离"""

import httpx
from typing import Optional
from app.config import get_settings
from app.schemas.ai import AIProviderConfig


class AIProvider:
    """AI 提供商基类 - 独立模块"""

    async def generate_explanation(self, prompt: str) -> str:
        raise NotImplementedError

    async def review_code(self, code: str, language: str) -> str:
        raise NotImplementedError


class OpenAIProvider(AIProvider):
    """OpenAI API 实现 - 独立模块"""

    def __init__(self, config: AIProviderConfig):
        self.config = config
        self.base_url = config.base_url or "https://api.openai.com/v1"

    async def _call_api(self, messages: list) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.config.model,
                    "messages": messages,
                    "temperature": self.config.temperature,
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    async def generate_explanation(self, prompt: str) -> str:
        return await self._call_api(
            [
                {
                    "role": "system",
                    "content": "你是一位耐心的编程老师，擅长分析学生的错误并给出建设性的反馈。",
                },
                {"role": "user", "content": prompt},
            ]
        )

    async def review_code(self, code: str, language: str) -> str:
        return await self._call_api(
            [
                {
                    "role": "system",
                    "content": "你是一位资深的代码审查专家，擅长发现代码问题并给出优化建议。",
                },
                {"role": "user", "content": f"请审查以下{language}代码：\n\n{code}"},
            ]
        )


class LocalAIProvider(AIProvider):
    """本地 AI 模型实现（预留接口）- 独立模块"""

    def __init__(self, config: AIProviderConfig):
        self.config = config

    async def generate_explanation(self, prompt: str) -> str:
        # TODO: 接入本地模型
        return "本地AI模型接口待实现"

    async def review_code(self, code: str, language: str) -> str:
        # TODO: 接入本地模型
        return "本地AI模型接口待实现"


class AIService:
    """AI 服务统一入口 - 独立模块"""

    def __init__(self):
        self._provider: Optional[AIProvider] = None
        self._config: Optional[AIProviderConfig] = None

    def configure(self, config: AIProviderConfig):
        """配置 AI 提供商"""
        self._config = config
        if config.provider == "openai":
            self._provider = OpenAIProvider(config)
        elif config.provider == "local":
            self._provider = LocalAIProvider(config)
        else:
            raise ValueError(f"不支持的 AI 提供商: {config.provider}")

    def is_configured(self) -> bool:
        return self._provider is not None and self._config is not None

    async def generate_choice_explanation(
        self,
        question: str,
        options: list[str],
        user_selected_index: int,
        correct_index: int,
    ) -> str:
        """生成选择题 AI 解答"""
        if not self.is_configured():
            return "AI 服务未配置，请联系管理员。"

        user_option = options[user_selected_index]
        correct_option = options[correct_index]

        prompt = f"""学生做错了以下选择题，请分析错误原因并给出解释：

题目：{question}
选项：
{chr(10).join([f"{chr(65 + i)}. {opt}" for i, opt in enumerate(options)])}

学生选择了：{chr(65 + user_selected_index)}. {user_option}
正确答案是：{chr(65 + correct_index)}. {correct_option}

请：
1. 分析学生选择这个选项可能的误解点
2. 解释为什么正确答案是正确的
3. 给出学习建议"""

        return await self._provider.generate_explanation(prompt)

    async def generate_code_review(
        self,
        code: str,
        language: str,
        chapter_id: Optional[int] = None,
        subsection_index: Optional[int] = None,
    ) -> str:
        """生成代码审查报告"""
        if not self.is_configured():
            return "AI 服务未配置，请联系管理员。"

        context = ""
        if chapter_id is not None:
            context += f"\n所属章节：第{chapter_id}章"
        if subsection_index is not None:
            context += f"\n小节索引：{subsection_index}"

        prompt = f"""请审查以下{language}代码{context}：

```{language}
{code}
```

请从以下方面进行分析：
1. 代码功能理解
2. 潜在问题或漏洞
3. 代码风格和规范
4. 性能优化建议
5. 时间/空间复杂度分析（如适用）

给出具体、可操作的改进建议。"""

        return await self._provider.review_code(code, language)


# 全局单例 - 独立模块
ai_service = AIService()

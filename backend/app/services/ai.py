"""AI 服务层 - 支持多种 AI 提供商，与原有代码完全隔离"""

import json
import logging
import httpx
from typing import Optional, AsyncGenerator, Any
from app.config import get_settings
from app.schemas.ai import AIProviderConfig

logger = logging.getLogger(__name__)


class AIProvider:
    """AI 提供商基类 - 独立模块"""

    async def generate_explanation(self, prompt: str) -> str:
        raise NotImplementedError

    async def review_code(self, code: str, language: str) -> str:
        raise NotImplementedError


class OpenAIProvider(AIProvider):
    """OpenAI API 实现 - 独立模块"""

    _client: Optional[httpx.AsyncClient] = None

    def __init__(self, config: AIProviderConfig):
        self.config = config
        self.base_url = config.base_url or "https://api.openai.com/v1"

    def _get_client(self) -> httpx.AsyncClient:
        """获取共享的 AsyncClient（连接池复用）"""
        if OpenAIProvider._client is None or OpenAIProvider._client.is_closed:
            OpenAIProvider._client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )
        return OpenAIProvider._client

    async def _call_api(self, messages: list) -> str:
        client = self._get_client()
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

    async def stream_generate(self, messages: list) -> AsyncGenerator[str, None]:
        client = self._get_client()
        async with client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.config.model,
                "messages": messages,
                "temperature": self.config.temperature,
                "stream": True,
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    chunk = json.loads(data)
                    content = chunk["choices"][0]["delta"].get("content", "")
                    if content:
                        yield content


class MiniMaxProvider(AIProvider):
    """MiniMax API 实现 - Anthropic Claude 兼容格式"""

    BASE_URL = "https://api.minimaxi.com/anthropic"
    _client: Optional[httpx.AsyncClient] = None

    def __init__(self, config: AIProviderConfig):
        self.config = config
        self.base_url = config.base_url or self.BASE_URL

    def _get_client(self) -> httpx.AsyncClient:
        """获取共享的 AsyncClient（连接池复用）"""
        if MiniMaxProvider._client is None or MiniMaxProvider._client.is_closed:
            MiniMaxProvider._client = httpx.AsyncClient(
                timeout=httpx.Timeout(120.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )
        return MiniMaxProvider._client

    async def _call_anthropic(self, system: str, messages: list) -> str:
        client = self._get_client()
        try:
            response = await client.post(
                f"{self.base_url}/v1/messages",
                headers={
                    "x-api-key": self.config.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.config.model,
                    "system": system,
                    "messages": messages,
                    "max_tokens": 8192,
                    "temperature": self.config.temperature,
                },
            )
            response.raise_for_status()
            # MiniMax returns thinking + text blocks; find the text block
            for block in response.json()["content"]:
                if block.get("type") == "text":
                    return block["text"]
            return response.json()["content"][-1].get("text", "")
        except httpx.HTTPStatusError as e:
            # Log detailed error for debugging
            logger.error(f"[MiniMax API Error] Status: {e.response.status_code}")
            logger.error(f"[MiniMax API Error] URL: {e.request.url}")
            try:
                logger.error(f"[MiniMax API Error] Response: {e.response.text}")
            except Exception:
                pass
            raise

    async def generate_explanation(self, prompt: str) -> str:
        return await self._call_anthropic(
            "你是一位耐心的编程老师，擅长分析学生的错误并给出建设性的反馈。",
            [{"role": "user", "content": prompt}],
        )

    async def review_code(self, code: str, language: str) -> str:
        return await self._call_anthropic(
            "你是一位资深的代码审查专家，擅长发现代码问题并给出优化建议。",
            [{"role": "user", "content": f"请审查以下{language}代码：\n\n{code}"}],
        )

    async def stream_generate(self, messages: list) -> AsyncGenerator[str, None]:
        # MiniMax uses Anthropic format - stream via text event
        client = self._get_client()
        async with client.stream(
            "POST",
            f"{self.base_url}/v1/messages",
            headers={
                "x-api-key": self.config.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": self.config.model,
                "messages": messages,
                "max_tokens": 8192,
                "temperature": self.config.temperature,
                "stream": True,
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                # Skip non-data lines (e.g. "event: ping")
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    break
                chunk = json.loads(data)
                # MiniMax streaming: content_block_delta contains text
                if chunk.get("type") == "content_block_delta":
                    content = chunk.get("delta", {}).get("text", "")
                    if content:
                        yield content


class OllamaProvider(AIProvider):
    """Ollama 本地模型实现"""

    DEFAULT_BASE_URL = "http://localhost:11434"
    PROVIDER_TYPE = "ollama"
    _client: Optional[httpx.AsyncClient] = None

    def __init__(self, config: AIProviderConfig):
        self.config = config
        self.base_url = (config.local_base_url or self.DEFAULT_BASE_URL).rstrip("/")

    def _get_client(self) -> httpx.AsyncClient:
        """获取共享的 AsyncClient（连接池复用）"""
        if OllamaProvider._client is None or OllamaProvider._client.is_closed:
            OllamaProvider._client = httpx.AsyncClient(
                timeout=httpx.Timeout(120.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )
        return OllamaProvider._client

    async def _call_api(self, messages: list) -> str:
        client = self._get_client()
        response = await client.post(
            f"{self.base_url}/v1/chat/completions",
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

    async def stream_generate(self, messages: list) -> AsyncGenerator[str, None]:
        client = self._get_client()
        async with client.stream(
            "POST",
            f"{self.base_url}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.config.model,
                "messages": messages,
                "temperature": self.config.temperature,
                "stream": True,
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    chunk = json.loads(data)
                    content = chunk["choices"][0]["delta"].get("content", "")
                    if content:
                        yield content

    @staticmethod
    async def health_check(base_url: str) -> tuple[bool, str, list[str]]:
        """检查 Ollama 服务状态，返回 (是否可用, 当前模型, 可用模型列表)"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # 获取模型列表
                resp = await client.get(f"{base_url}/v1/models")
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m.get("id", "") for m in data.get("data", [])]
                    current = models[0] if models else ""
                    return True, current, models
                return False, "", []
        except Exception:
            return False, "", []

    @staticmethod
    async def is_available(base_url: str) -> bool:
        """快速可用性检查"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{base_url}/v1/models")
                return resp.status_code == 200
        except Exception:
            return False


class LMStudioProvider(AIProvider):
    """LM Studio 本地模型实现"""

    DEFAULT_BASE_URL = "http://localhost:1234"
    PROVIDER_TYPE = "lmstudio"
    _client: Optional[httpx.AsyncClient] = None

    def __init__(self, config: AIProviderConfig):
        self.config = config
        self.base_url = (config.local_base_url or self.DEFAULT_BASE_URL).rstrip("/")

    def _get_client(self) -> httpx.AsyncClient:
        """获取共享的 AsyncClient（连接池复用）"""
        if LMStudioProvider._client is None or LMStudioProvider._client.is_closed:
            LMStudioProvider._client = httpx.AsyncClient(
                timeout=httpx.Timeout(120.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )
        return LMStudioProvider._client

    async def _call_api(self, messages: list) -> str:
        client = self._get_client()
        response = await client.post(
            f"{self.base_url}/v1/chat/completions",
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

    async def stream_generate(self, messages: list) -> AsyncGenerator[str, None]:
        client = self._get_client()
        async with client.stream(
            "POST",
            f"{self.base_url}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.config.model,
                "messages": messages,
                "temperature": self.config.temperature,
                "stream": True,
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    chunk = json.loads(data)
                    content = chunk["choices"][0]["delta"].get("content", "")
                    if content:
                        yield content

    @staticmethod
    async def health_check(base_url: str) -> tuple[bool, str, list[str]]:
        """检查 LM Studio 服务状态，返回 (是否可用, 当前模型, 可用模型列表)"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{base_url}/v1/models")
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m.get("id", "") for m in data.get("data", [])]
                    current = models[0] if models else ""
                    return True, current, models
                return False, "", []
        except Exception:
            return False, "", []

    @staticmethod
    async def is_available(base_url: str) -> bool:
        """快速可用性检查"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{base_url}/v1/models")
                return resp.status_code == 200
        except Exception:
            return False


class AIService:
    """AI 服务统一入口 - 独立模块"""

    def __init__(self):
        self._provider: Optional[AIProvider] = None
        self._config: Optional[AIProviderConfig] = None
        # MiniMax provider for enhanced quiz generation (独立配置)
        self._minimax_provider: Optional[MiniMaxProvider] = None

    def configure(self, config: AIProviderConfig):
        """配置 AI 提供商"""
        self._config = config
        if config.provider == "openai":
            self._provider = OpenAIProvider(config)
        elif config.provider == "minimax":
            self._provider = MiniMaxProvider(config)
        elif config.provider == "ollama":
            self._provider = OllamaProvider(config)
        elif config.provider == "lmstudio":
            self._provider = LMStudioProvider(config)
        elif config.provider == "local":
            # 兼容旧的 "local" provider，自动检测 Ollama 或 LM Studio
            self._provider = OllamaProvider(config)
        else:
            raise ValueError(f"不支持的 AI 提供商: {config.provider}")

    def configure_minimax(self, api_key: str, model: str = "MiniMax-M2.7", temperature: float = 0.7):
        """配置 MiniMax Provider (用于强化测试题生成)"""
        if api_key:
            config = AIProviderConfig(
                provider="minimax",
                api_key=api_key,
                model=model,
                temperature=temperature,
            )
            self._minimax_provider = MiniMaxProvider(config)
        else:
            self._minimax_provider = None

    def is_configured(self) -> bool:
        return self._provider is not None and self._config is not None

    def is_minimax_configured(self) -> bool:
        """检查 MiniMax 是否已配置"""
        return self._minimax_provider is not None

    @property
    def provider(self) -> Optional[AIProvider]:
        """获取当前 provider"""
        return self._provider

    @property
    def minimax_provider(self) -> Optional[MiniMaxProvider]:
        """获取 MiniMax provider"""
        return self._minimax_provider

    async def get_provider_status(self) -> dict:
        """获取所有已配置 provider 的连接状态"""
        from app.schemas.ai import ProviderStatus

        settings = get_settings()
        results: list[dict] = []
        current_type = self._config.provider if self._config else settings.AI_PROVIDER

        # 检查 Ollama
        ollama_url = settings.AI_BASE_URL or OllamaProvider.DEFAULT_BASE_URL
        ollama_ok, ollama_model, ollama_models = await OllamaProvider.health_check(ollama_url)
        results.append(ProviderStatus(
            type="ollama",
            address=ollama_url,
            status="connected" if ollama_ok else "disconnected",
            model=ollama_model or None,
            available_models=ollama_models or None,
        ).model_dump())

        # 检查 LM Studio
        lm_url = LMStudioProvider.DEFAULT_BASE_URL
        lm_ok, lm_model, lm_models = await LMStudioProvider.health_check(lm_url)
        results.append(ProviderStatus(
            type="lmstudio",
            address=lm_url,
            status="connected" if lm_ok else "disconnected",
            model=lm_model or None,
            available_models=lm_models or None,
        ).model_dump())

        return {
            "current_provider": current_type,
            "current_model": self._config.model if self._config else settings.AI_MODEL,
            "is_local_first": self._config.is_local_first if self._config else False,
            "providers": results,
        }

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

        return await self._provider.review_code(code, language)

    async def generate_chat(
        self,
        message: str,
    ) -> str:
        """生成 AI 问答"""
        if not self.is_configured():
            return "AI 服务未配置，请联系管理员。"

        return await self._provider.generate_explanation(
            f"你是一位耐心的编程老师。学生的问题是：\n\n{message}\n\n请给出简洁、有帮助的回答。"
        )

    async def stream_chat(
        self,
        message: str,
        context: Optional[dict] = None,
    ) -> AsyncGenerator[str, None]:
        """流式生成 AI 问答（支持题目上下文）"""
        if not self.is_configured():
            yield "AI 服务未配置，请联系管理员。"
            return

        if context:
            q_type = context.get("type", "")
            q_text = context.get("question", "")
            q_opts = context.get("options", [])
            q_code = context.get("code", "")

            opts_str = ""
            if q_opts:
                opts_str = "\n".join([f"{chr(65+i)}. {opt}" for i, opt in enumerate(q_opts)])

            code_line = f"代码：\n{q_code}" if q_code else ""
            opts_line = f"选项：\n{opts_str}" if opts_str else ""

            context_parts = [
                "学生正在学习数据结构与算法。",
                f"题目类型：{q_type}",
                f"题目：{q_text}",
            ]
            if opts_line:
                context_parts.append(opts_line)
            if code_line:
                context_parts.append(code_line)

            context_str = "\n".join(context_parts)

            prompt = f"""{context_str}

学生问题：{message}

请根据以上题目信息，用中文给出有帮助的回答。"""
        else:
            prompt = f"你是一位耐心的编程老师。学生的问题是：\n\n{message}\n\n请给出简洁、有帮助的回答。"

        messages = [
            {"role": "user", "content": prompt},
        ]

        async for chunk in self._provider.stream_generate(messages):
            yield chunk

    async def generate_choice_analysis(
        self,
        question_text: str,
        options: list[str],
        user_selected: int,
        correct_answer: int,
    ) -> dict:
        """生成选择题 AI 分析 —— 针对错误选项进行详细分析"""
        if not self.is_configured():
            return {"analysis": "AI 服务未配置，请联系管理员。", "is_correct": False}

        is_correct = user_selected == correct_answer
        selected_label = chr(65 + user_selected)
        correct_label = chr(65 + correct_answer)
        selected_text = options[user_selected]
        correct_text = options[correct_answer]

        if is_correct:
            prompt = f"""学生选择了正确答案，请给予简短肯定并强化理解：

题目：{question_text}
{chr(10).join([f"{chr(65 + i)}. {opt}" for i, opt in enumerate(options)])}

学生选择了：{selected_label}. {selected_text}

请用2-3句话肯定学生的答案，并简要解释为什么这个答案是正确的。"""
        else:
            prompt = f"""学生做错了以下选择题，请详细分析：

题目：{question_text}
{chr(10).join([f"{chr(65 + i)}. {opt}" for i, opt in enumerate(options)])}

学生选择了：{selected_label}. {selected_text}
正确答案是：{correct_label}. {correct_text}

请：
1. 分析学生选择 {selected_label} 的可能误解点，为什么会被这个选项迷惑？
2. 逐步推导为什么 {correct_label} 是正确答案
3. 指出学习这个概念时常见的陷阱和记忆技巧"""

        analysis = await self._provider.generate_explanation(prompt)
        return {"analysis": analysis, "is_correct": is_correct}

    async def generate_code_feedback(
        self,
        code: str,
        language: str,
        exercise_description: str,
        expected_output: str,
        actual_output: str = "",
        status: str = "",
        error_message: str = "",
    ) -> dict:
        """生成编程题 AI 反馈 —— 纠错 + 优化 + 建议 三段合一"""
        if not self.is_configured():
            return {
                "diagnosis": "AI 服务未配置，请联系管理员。",
                "suggestions": "",
                "optimized_code": code,
            }

        runtime_info = ""
        if status:
            runtime_info += f"\n运行状态：{status}"
        if error_message:
            runtime_info += f"\n错误信息：{error_message}"
        if actual_output:
            runtime_info += f"\n实际输出：{actual_output}"
        if expected_output:
            runtime_info += f"\n期望输出：{expected_output}"

        prompt = f"""你是一位耐心的编程老师。学生完成了以下编程练习：

练习要求：{exercise_description}
语言：{language}

学生提交的代码：
```{language}
{code}
```
{runtime_info}

请从以下三个方面给出反馈，每部分用 ## 开头作为分隔：

【错误诊断】
指出代码中的语法错误、逻辑错误、运行时错误。如果没有错误，说明代码为什么正确。

【优化建议】
给出代码风格、规范、可读性、性能方面的改进建议。

【参考代码】
给出优化后的完整代码示例，语言保持 {language}。

请输出 Markdown 格式。"""

        analysis = await self._provider.generate_explanation(prompt)

        # Parse the response into three parts by section headers
        # Try markdown headers like "##" or "【" markers first
        diagnosis = analysis
        suggestions = ""
        optimized_code = code

        # Split by "---" or "## " or section markers
        if "###" in analysis or "##" in analysis:
            sections = analysis.split("\n## ")
            if len(sections) >= 2:
                diagnosis = sections[0].strip().replace("【错误诊断】", "").replace("**错误诊断**", "")
            if len(sections) >= 3:
                suggestions = sections[1].strip().replace("【优化建议】", "").replace("**优化建议**", "")
            if len(sections) >= 4:
                optimized_code = sections[2].strip()
        elif "---" in analysis:
            parts = analysis.split("---")
            diagnosis = parts[0].strip()
            if len(parts) > 1:
                suggestions = parts[1].strip()
            if len(parts) > 2:
                optimized_code = parts[2].strip()

        # Clean code blocks
        optimized_code = optimized_code.replace(f"```{language}\n", "").replace("```\n", "").replace("```", "").strip()

        # Fallback: if diagnosis is empty, use full response
        if not diagnosis.strip():
            diagnosis = analysis.strip()
        if not suggestions.strip():
            suggestions = "无额外建议"

        return {
            "diagnosis": diagnosis,
            "suggestions": suggestions if suggestions else "无额外建议",
            "optimized_code": optimized_code,
        }

    async def generate_exercises(
        self,
        chapter_title: str,
        chapter_description: str,
        topic: Optional[str] = None,
        count: int = 5,
        exercise_type: str = "choice",
        difficulty: int = 1,
    ) -> list[dict]:
        """使用 AI 生成练习题"""
        if not self.is_configured():
            return []

        difficulty_labels = {
            1: "入门",
            2: "基础",
            3: "中等",
            4: "较难",
            5: "困难",
        }
        difficulty_label = difficulty_labels.get(difficulty, "基础")

        type_mapping = {
            "choice": "选择题",
            "programming": "编程题",
            "fill_blank": "填空题",
        }

        topic_context = f"\n重点关注主题：{topic}" if topic else ""

        prompt = f"""你是一位专业的编程练习题出题老师。请为以下章节生成 {count} 道{difficulty_label}难度的{type_mapping.get(exercise_type, "选择题")}。

章节标题：{chapter_title}
章节描述：{chapter_description}{topic_context}

难度等级：{difficulty_label} (1=入门, 2=基础, 3=中等, 4=较难, 5=困难)
题目类型：{exercise_type}

请以 JSON 数组格式返回，格式如下：
```json
[
  {{
    "content": {{
      "text": "题目描述",
      "options": ["选项A", "选项B", "选项C", "选项D"],  // 选择题必须有4个选项
      "correct_index": 0  // 正确答案的索引
    }},
    "solution": {{
      "answer": 0,  // 或具体答案值
      "explanation": "解题思路和答案解释"
    }},
    "hints": ["提示1", "提示2"],
    "source_id": "unique_id_for_this_question"
  }}
]
```

要求：
1. 每道题必须有明确的知识点考查
2. 答案必须正确
3. 解释要清晰、有教育意义
4. 难度与{difficulty_label}相符
5. JSON 格式必须合法

请直接返回 JSON，不要有其他内容："""

        response = await self._provider.generate_explanation(prompt)

        # Parse JSON response
        try:
            # Try to extract JSON from response
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                exercises = json.loads(json_str)
                return exercises
            else:
                # Try parsing the whole response
                exercises = json.loads(response)
                return exercises
        except json.JSONDecodeError:
            # Return empty list if parsing fails
            return []


    async def generate_knowledge_content(
        self,
        chapter_title: str,
        chapter_description: str,
        course_name: str = "编程",
        knowledge_points: Optional[list[str]] = None,
    ) -> dict:
        """
        生成章节知识点内容

        Args:
            chapter_title: 章节标题
            chapter_description: 章节描述
            course_name: 课程名称
            knowledge_points: 可选的知识点列表（用于扩展）

        Returns:
            包含知识点列表的字典
        """
        if not self.is_configured():
            return {}

        kp_context = ""
        if knowledge_points:
            kp_context = f"\n已有知识点提示：{', '.join(knowledge_points)}"

        prompt = f"""你是一位专业的{course_name}教师。请为以下章节生成详细的知识点讲解内容：

章节标题：{chapter_title}
章节描述：{chapter_description}{kp_context}

请以 JSON 格式返回，格式如下：
```json
{{
  "knowledge_points": [
    {{
      "id": "kp_001",
      "title": "知识点标题",
      "content": "知识点详细讲解（Markdown格式，可以包含代码示例）",
      "examples": ["代码示例1", "代码示例2"],
      "difficulty": 1,
      "related_points": ["kp_002"]
    }}
  ],
  "summary": "章节总结",
  "estimated_time": 15
}}
```

要求：
1. 每个知识点必须有清晰的标题和详细内容
2. 内容使用 Markdown 格式，包含代码示例
3. examples 列表提供可运行的代码示例
4. difficulty 为 1-5 的难度等级
5. related_points 可以为空或包含相关知识点ID
6. 知识点数量根据章节复杂度，通常 3-8 个
7. JSON 格式必须合法

请直接返回 JSON，不要有其他内容："""

        response = await self._provider.generate_explanation(prompt)

        try:
            # Try to extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                return json.loads(response)
        except json.JSONDecodeError:
            return {}

    async def generate_personalized_quiz(
        self,
        chapter_title: str,
        chapter_description: str,
        user_profile: Optional[Any] = None,
        question_count: int = 5,
        question_types: list[str] = None,
        difficulty_range: tuple[int, int] = (1, 5),
        knowledge_points: Optional[list[str]] = None,
    ) -> list[dict]:
        """
        根据用户画像生成个性化测试题

        Args:
            chapter_title: 章节标题
            chapter_description: 章节描述
            user_profile: 用户画像（UserProfileForQuiz）
            question_count: 题目数量
            question_types: 题目类型列表
            difficulty_range: 难度范围 (min, max)
            knowledge_points: 考查的知识点

        Returns:
            测试题列表
        """
        if not self.is_configured():
            return []

        if question_types is None:
            question_types = ["choice"]

        # 构建用户画像上下文
        profile_context = ""
        if user_profile:
            weak_points = getattr(user_profile, 'weak_knowledge_points', []) or []
            current_level = getattr(user_profile, 'current_level', 1.0)
            recent_accuracy = getattr(user_profile, 'recent_accuracy', 0.5)

            profile_context = f"""
学生画像：
- 当前水平：{current_level:.1f}/5
- 近期正确率：{recent_accuracy:.0%}
- 薄弱知识点：{', '.join(weak_points) if weak_points else '无'}
"""
            # 如果有薄弱点，优先考查
            if weak_points:
                knowledge_points = weak_points

        # 难度标签映射
        difficulty_labels = {1: "入门", 2: "基础", 3: "中等", 4: "较难", 5: "困难"}
        min_diff = difficulty_labels.get(difficulty_range[0], "入门")
        max_diff = difficulty_labels.get(difficulty_range[1], "困难")

        # 题型映射
        type_names = {
            "choice": "选择题",
            "programming": "编程题",
            "fill_blank": "填空题",
        }
        type_str = "、".join([type_names.get(t, t) for t in question_types])

        # 知识点上下文
        kp_context = ""
        if knowledge_points:
            kp_context = f"\n重点考查知识点：{', '.join(knowledge_points)}"

        prompt = f"""你是一位专业的编程测试题出题老师。请根据以下信息生成 {question_count} 道测试题：

章节标题：{chapter_title}
章节描述：{chapter_description}{kp_context}
{profile_context}
题目类型：{type_str}
难度范围：{min_diff} 到 {max_diff}

请以 JSON 数组格式返回，格式如下：
```json
[
  {{
    "id": "q_001",
    "type": "choice",
    "difficulty": 2,
    "content": {{
      "text": "题目描述",
      "options": ["选项A", "选项B", "选项C", "选项D"]
    }},
    "solution": {{
      "answer": "B",
      "explanation": "答案解析"
    }},
    "knowledge_points": ["知识点1", "知识点2"],
    "hints": ["提示1"]
  }},
  {{
    "id": "q_002",
    "type": "programming",
    "difficulty": 3,
    "content": {{
      "title": "编程题标题",
      "description": "题目详细描述",
      "code_template": "代码模板",
      "input_format": "输入格式说明",
      "output_format": "输出格式说明",
      "sample_input": "示例输入",
      "sample_output": "示例输出"
    }},
    "solution": {{
      "answer": "参考答案代码",
      "explanation": "解题思路"
    }},
    "knowledge_points": ["知识点"],
    "test_cases": [
      {{"input": "测试输入1", "output": "期望输出1"}},
      {{"input": "测试输入2", "output": "期望输出2"}}
    ]
  }}
]
```

要求：
1. 题目难度应在 {min_diff} 到 {max_diff} 范围内
2. 选择题必须有 4 个选项，答案为选项字母（A/B/C/D）
3. 编程题必须有 test_cases
4. 每道题必须标注考查的知识点
5. 如果学生有薄弱点，优先针对薄弱点出题
6. JSON 格式必须合法
7. 题目要有教育意义，不能太简单或太难

请直接返回 JSON 数组，不要有其他内容："""

        response = await self._provider.generate_explanation(prompt)

        try:
            # Try to extract JSON from response
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                return json.loads(response)
        except json.JSONDecodeError:
            return []

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        通用的 AI 文本生成方法

        Args:
            prompt: 用户提示词
            system_prompt: 可选的系统提示词

        Returns:
            AI 生成的文本
        """
        if not self.is_configured():
            return "AI 服务未配置，请联系管理员。"

        # 对于所有 provider，直接使用 generate_explanation
        # 它会将 prompt 发送给 AI，让 AI 生成内容
        # 如果需要 system_prompt，可以在 prompt 中包含
        if system_prompt:
            combined_prompt = f"{system_prompt}\n\n{prompt}"
            return await self._provider.generate_explanation(combined_prompt)
        else:
            return await self._provider.generate_explanation(prompt)

    async def generate_question_analysis(
        self,
        question_text: str,
        options: list[str],
        user_answer: str,
        correct_answer: str,
        is_correct: bool,
        knowledge_points: Optional[list[str]] = None,
    ) -> dict:
        """
        生成题目解析

        Args:
            question_text: 题目文本
            options: 选项列表
            user_answer: 用户答案
            correct_answer: 正确答案
            is_correct: 是否正确
            knowledge_points: 相关知识点

        Returns:
            包含解析的字典
        """
        if not self.is_configured():
            return {"analysis": "AI 服务未配置", "is_correct": is_correct}

        kp_context = ""
        if knowledge_points:
            kp_context = f"\n相关知识点：{', '.join(knowledge_points)}"

        if is_correct:
            prompt = f"""学生答对了以下题目，请给予肯定并强化理解：

题目：{question_text}
选项：
{chr(10).join([f"  {opt}" for opt in options])}
学生选择：{user_answer}（正确）{kp_context}

请用 2-3 句话：
1. 肯定学生的答案
2. 简要解释为什么这个答案正确
3. 给出一个相关的拓展提示"""
        else:
            prompt = f"""学生做错了以下题目，请详细分析：

题目：{question_text}
选项：
{chr(10).join([f"  {opt}" for opt in options])}
学生选择：{user_answer}
正确答案：{correct_answer}{kp_context}

请：
1. 分析学生选择 {user_answer} 的可能误解
2. 解释为什么正确答案是 {correct_answer}
3. 给出学习建议"""

        analysis = await self._provider.generate_explanation(prompt)
        return {"analysis": analysis, "is_correct": is_correct}

    async def stream_exercise_hint(
        self,
        exercise_title: str,
        exercise_description: str,
        difficulty: int,
        knowledge_points: list[str],
        hint_level: str,
        code_template: str = "",
        sample_input: str = "",
        sample_output: str = "",
    ) -> AsyncGenerator[str, None]:
        """
        流式生成编程题 AI 提示 - 挑战之路使用

        Args:
            exercise_title: 题目标题
            exercise_description: 题目描述
            difficulty: 难度 1-5
            knowledge_points: 相关知识点
            hint_level: 提示级别 light/medium/deep
            code_template: 代码模板
            sample_input: 示例输入
            sample_output: 示例输出

        Yields:
            AI 生成的提示内容（流式）
        """
        if not self.is_configured():
            yield "AI 服务未配置，请联系管理员。"
            return

        difficulty_labels = {1: "入门", 2: "基础", 3: "中等", 4: "较难", 5: "困难"}
        diff_label = difficulty_labels.get(difficulty, "中等")

        kp_context = ""
        if knowledge_points:
            kp_context = f"\n涉及知识点：{', '.join(knowledge_points)}"

        sample_context = ""
        if sample_input and sample_output:
            sample_context = f"""

示例：
输入：{sample_input}
输出：{sample_output}"""

        code_context = ""
        if code_template:
            code_context = f"""

代码模板：
```
{code_template}
```"""

        if hint_level == "light":
            prompt = f"""你是一位耐心的编程老师。学生正在做一道编程题，需要思路引导（不要直接给出答案）。

题目：{exercise_title}
难度：{diff_label}
描述：{exercise_description}{kp_context}{sample_context}{code_context}

请给出轻度提示：
1. 分析题目要求什么
2. 指出应该使用什么类型的数据结构和算法思路
3. 提醒需要注意的边界情况

注意：只给思路方向，不要写出完整代码！"""
        elif hint_level == "medium":
            prompt = f"""你是一位耐心的编程老师。学生正在做一道编程题，需要关键步骤提示。

题目：{exercise_title}
难度：{diff_label}
描述：{exercise_description}{kp_context}{sample_context}{code_context}

请给出中度提示：
1. 分析问题的核心算法思路
2. 给出伪代码框架（不要完整实现）
3. 说明关键步骤的实现要点

注意：可以给出代码框架，但关键实现部分用注释代替！"""
        else:  # deep
            prompt = f"""你是一位耐心的编程老师。学生正在做一道编程题，需要详细的解题思路。

题目：{exercise_title}
难度：{diff_label}
描述：{exercise_description}{kp_context}{sample_context}{code_context}

请给出深度解析：
1. 完整的问题分析和算法设计
2. 带注释的参考代码框架
3. 复杂度分析（时间和空间）
4. 可能的优化方向

注意：代码框架要有详细注释，但不要直接给出完整可运行的答案！"""

        messages = [{"role": "user", "content": prompt}]

        async for chunk in self._provider.stream_generate(messages):
            yield chunk


# 全局单例 - 独立模块
ai_service = AIService()

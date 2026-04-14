"""AI 服务层 - 支持多种 AI 提供商，与原有代码完全隔离"""

import json
import httpx
from typing import Optional, AsyncGenerator
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

    def is_configured(self) -> bool:
        return self._provider is not None and self._config is not None

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


# 全局单例 - 独立模块
ai_service = AIService()

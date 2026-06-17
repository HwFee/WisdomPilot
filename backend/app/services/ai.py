"""AI 服务层 - 支持多种 AI 提供商，与原有代码完全隔离"""

import asyncio
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
    """DeepSeek 兼容 API 实现 - 独立模块"""

    _client: Optional[httpx.AsyncClient] = None

    CHAT_COMPLETIONS_ENDPOINT = "/chat/completions"
    HEADER_AUTHORIZATION = "Authorization"
    HEADER_CONTENT_TYPE = "Content-Type"
    MEDIA_TYPE_JSON = "application/json"
    JSON_KEY_MODEL = "model"
    JSON_KEY_MESSAGES = "messages"
    JSON_KEY_TEMPERATURE = "temperature"
    JSON_KEY_CHOICES = "choices"
    JSON_KEY_MESSAGE = "message"
    JSON_KEY_CONTENT = "content"
    MAX_RETRIES = 3
    RETRYABLE_STATUS_THRESHOLD = 500
    ERROR_BODY_TRUNCATION_LENGTH = 500

    def __init__(self, config: AIProviderConfig):
        self.config = config
        self.base_url = config.base_url or "https://api.deepseek.com"

    def _get_client(self) -> httpx.AsyncClient:
        """获取共享的 AsyncClient（连接池复用）"""
        if OpenAIProvider._client is None or OpenAIProvider._client.is_closed:
            OpenAIProvider._client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )
        return OpenAIProvider._client

    def _build_chat_headers(self) -> dict:
        return {
            self.HEADER_AUTHORIZATION: f"Bearer {self.config.api_key}",
            self.HEADER_CONTENT_TYPE: self.MEDIA_TYPE_JSON,
        }

    def _build_chat_payload(self, messages: list) -> dict:
        return {
            self.JSON_KEY_MODEL: self.config.model,
            self.JSON_KEY_MESSAGES: messages,
            self.JSON_KEY_TEMPERATURE: self.config.temperature,
        }

    def _extract_content(self, response: httpx.Response) -> str:
        return response.json()[self.JSON_KEY_CHOICES][0][self.JSON_KEY_MESSAGE][self.JSON_KEY_CONTENT]

    def _log_http_error(self, error: httpx.HTTPStatusError) -> None:
        try:
            err_body = error.response.text[:self.ERROR_BODY_TRUNCATION_LENGTH]
        except Exception:
            err_body = "<unable to read response body>"
        logger.error(
            f"[OpenAIProvider] HTTP {error.response.status_code} "
            f"from {error.request.url}: {err_body}"
        )

    def _should_retry_network_error(self, attempt: int) -> bool:
        return attempt < self.MAX_RETRIES - 1

    def _should_retry_http_error(self, error: httpx.HTTPStatusError, attempt: int) -> bool:
        return error.response.status_code >= self.RETRYABLE_STATUS_THRESHOLD and attempt < self.MAX_RETRIES - 1

    async def _call_api(self, messages: list) -> str:
        client = self._get_client()
        last_exception = None
        for attempt in range(self.MAX_RETRIES):
            try:
                response = await client.post(
                    f"{self.base_url}{self.CHAT_COMPLETIONS_ENDPOINT}",
                    headers=self._build_chat_headers(),
                    json=self._build_chat_payload(messages),
                )
                response.raise_for_status()
                return self._extract_content(response)
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_exception = e
                if not self._should_retry_network_error(attempt):
                    break
                logger.warning(
                    f"[OpenAIProvider] API call attempt {attempt + 1} failed ({e}), "
                    f"retrying in {attempt + 1}s..."
                )
                await asyncio.sleep(attempt + 1)
            except httpx.HTTPStatusError as e:
                self._log_http_error(e)
                if not self._should_retry_http_error(e, attempt):
                    raise
                logger.warning(
                    f"[OpenAIProvider] API call attempt {attempt + 1} got "
                    f"{e.response.status_code}, retrying in {attempt + 1}s..."
                )
                await asyncio.sleep(attempt + 1)
        raise last_exception

    SYSTEM_ROLE = "system"
    USER_ROLE = "user"
    CONTENT_KEY = "content"
    ROLE_KEY = "role"
    EXPLANATION_SYSTEM_PROMPT = "你是一位耐心的编程老师，擅长分析学生的错误并给出建设性的反馈。"
    CODE_REVIEW_SYSTEM_PROMPT = "你是一位资深的代码审查专家，擅长发现代码问题并给出优化建议。"
    CODE_REVIEW_USER_TEMPLATE = "请审查以下{language}代码：\n\n{code}"

    def _build_system_message(self, prompt_text: str) -> dict:
        return {self.ROLE_KEY: self.SYSTEM_ROLE, self.CONTENT_KEY: prompt_text}

    def _build_user_message(self, prompt_text: str) -> dict:
        return {self.ROLE_KEY: self.USER_ROLE, self.CONTENT_KEY: prompt_text}

    async def generate_explanation(self, prompt: str) -> str:
        return await self._call_api(
            [
                self._build_system_message(self.EXPLANATION_SYSTEM_PROMPT),
                self._build_user_message(prompt),
            ]
        )

    async def review_code(self, code: str, language: str) -> str:
        return await self._call_api(
            [
                self._build_system_message(self.CODE_REVIEW_SYSTEM_PROMPT),
                self._build_user_message(self.CODE_REVIEW_USER_TEMPLATE.format(language=language, code=code)),
            ]
        )

    async def _stream_connect(self, messages: list) -> httpx.Response:
        """建立流式连接，带重试。只对连接/握手阶段重试，避免内容重复。"""
        import time
        t0 = time.time()
        client = self._get_client()
        t1 = time.time()
        logger.info(f"[PERF-AI] get_client took {(t1-t0)*1000:.1f}ms")

        request = client.build_request(
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
        )
        t2 = time.time()
        logger.info(f"[PERF-AI] build_request took {(t2-t1)*1000:.1f}ms")

        for attempt in range(3):
            t_attempt = time.time()
            try:
                logger.info(f"[PERF-AI] sending request (attempt {attempt+1}) to {self.base_url}...")
                response = await client.send(request, stream=True)
                t_after_send = time.time()
                logger.info(f"[PERF-AI] client.send completed in {(t_after_send-t_attempt)*1000:.1f}ms")
                response.raise_for_status()
                t_after_raise = time.time()
                logger.info(f"[PERF-AI] raise_for_status completed in {(t_after_raise-t_after_send)*1000:.1f}ms")
                logger.info(f"[PERF-AI] total _stream_connect took {(t_after_raise-t0)*1000:.1f}ms, status={response.status_code}")
                return response
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.error(f"[PERF-AI] attempt {attempt+1} connect failed after {(time.time()-t_attempt)*1000:.1f}ms: {e}")
                if attempt < 2:
                    logger.warning(f"[OpenAIProvider] Stream connect attempt {attempt + 1} failed ({e}), retrying in {attempt + 1}s...")
                    import asyncio
                    await asyncio.sleep(attempt + 1)
                else:
                    raise
            except httpx.HTTPStatusError as e:
                # Log detailed error for 4xx/5xx to help diagnose model/key issues
                logger.error(f"[PERF-AI] attempt {attempt+1} HTTP error after {(time.time()-t_attempt)*1000:.1f}ms: {e.response.status_code}")
                try:
                    err_body = e.response.text[:500]
                except Exception:
                    err_body = "<unable to read response body>"
                logger.error(f"[OpenAIProvider] HTTP {e.response.status_code} from {e.request.url}: {err_body}")
                if e.response.status_code >= 500 and attempt < 2:
                    logger.warning(f"[OpenAIProvider] Stream connect attempt {attempt + 1} got {e.response.status_code}, retrying in {attempt + 1}s...")
                    import asyncio
                    await asyncio.sleep(attempt + 1)
                else:
                    raise
        raise RuntimeError("Failed to start stream after all retries")

    async def stream_generate(self, messages: list) -> AsyncGenerator[str, None]:
        import time
        t0 = time.time()
        response = await self._stream_connect(messages)
        t1 = time.time()
        logger.info(f"[PERF-AI] _stream_connect returned, TTFB={(t1-t0)*1000:.1f}ms")

        chunk_count = 0
        total_chars = 0
        last_log_time = t1
        try:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    chunk = json.loads(data)
                    content = chunk["choices"][0]["delta"].get("content", "")
                    if content:
                        chunk_count += 1
                        total_chars += len(content)
                        now = time.time()
                        # 每 20 个 chunk 或每 5 秒打一次日志
                        if chunk_count % 20 == 0 or (now - last_log_time) > 5:
                            logger.info(
                                f"[PERF-AI] streaming progress: chunks={chunk_count}, "
                                f"chars={total_chars}, elapsed={(now-t0)*1000:.1f}ms, "
                                f"chunk_interval={(now-last_log_time)*1000:.1f}ms"
                            )
                            last_log_time = now
                        yield content
        except Exception as e:
            logger.error(f"[PERF-AI] stream interrupted after {(time.time()-t0)*1000:.1f}ms, chunks={chunk_count}: {e}")
            raise
        finally:
            await response.aclose()
            t_end = time.time()
            logger.info(
                f"[PERF-AI] stream finished: total={(t_end-t0)*1000:.1f}ms, "
                f"chunks={chunk_count}, chars={total_chars}"
            )


def _build_exercise_hint_prompt(
    exercise_title: str,
    exercise_description: str,
    difficulty: int,
    knowledge_points: list[str],
    hint_level: str,
    code_template: str = "",
    sample_input: str = "",
    sample_output: str = "",
) -> str:
    """Build the prompt for a pedagogical exercise hint.

    The three hint levels form a progressive disclosure boundary:
    - light: high-level direction, no code.
    - medium: pseudo-code framework, key steps as comments.
    - deep: full analysis with annotated reference code framework, but still
      not a complete runnable answer.
    """
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

    return prompt


class AIService:
    """AI 服务统一入口 - 独立模块"""

    def __init__(self):
        self._provider: Optional[AIProvider] = None
        self._config: Optional[AIProviderConfig] = None

    def configure(self, config: AIProviderConfig):
        """配置 AI 提供商（仅支持 DeepSeek / OpenAI 兼容 API）"""
        self._config = config
        if config.provider in ("openai", "siliconflow", "deepseek"):
            self._provider = OpenAIProvider(config)
        else:
            raise ValueError(f"不支持的 AI 提供商: {config.provider}")

    def is_configured(self) -> bool:
        return self._provider is not None and self._config is not None

    @property
    def provider(self) -> Optional[AIProvider]:
        """获取当前 provider"""
        return self._provider

    async def get_provider_status(self) -> dict:
        """获取当前 provider 的连接状态"""
        settings = get_settings()
        current_type = self._config.provider if self._config else settings.AI_PROVIDER

        return {
            "current_provider": current_type,
            "current_model": self._config.model if self._config else settings.AI_MODEL,
            "is_local_first": False,
            "providers": [],
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

            opts_str = ""
            if q_opts:
                opts_str = "\n".join([f"{chr(65+i)}. {opt}" for i, opt in enumerate(q_opts)])

            opts_line = f"选项：\n{opts_str}" if opts_str else ""

            context_parts = [
                "学生正在学习数据结构与算法。",
                f"题目类型：{q_type}",
                f"题目：{q_text}",
            ]
            if opts_line:
                context_parts.append(opts_line)

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
            "fill_blank": "填空题",
        }

        if exercise_type not in type_mapping:
            logger.warning(f"[AIService] Unsupported exercise type '{exercise_type}', skipping generation.")
            return []

        topic_context = f"\n重点关注主题：{topic}" if topic else ""

        prompt = f"""你是一位专业的编程练习题出题老师。请为以下章节生成 {count} 道{difficulty_label}难度的{type_mapping[exercise_type]}。

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
        import time
        t_service_start = time.time()
        if not self.is_configured():
            logger.error("[PERF-AI] stream_exercise_hint: AI not configured!")
            yield "AI 服务未配置，请联系管理员。"
            return

        difficulty_labels = {1: "入门", 2: "基础", 3: "中等", 4: "较难", 5: "困难"}
        diff_label = difficulty_labels.get(difficulty, "中等")
        logger.info(f"[PERF-AI] stream_exercise_hint starting: level={hint_level}, difficulty={diff_label}, title={exercise_title[:30]}...")

        prompt = _build_exercise_hint_prompt(
            exercise_title=exercise_title,
            exercise_description=exercise_description,
            difficulty=difficulty,
            knowledge_points=knowledge_points,
            hint_level=hint_level,
            code_template=code_template,
            sample_input=sample_input,
            sample_output=sample_output,
        )
        messages = [{"role": "user", "content": prompt}]
        t_prompt_done = time.time()
        logger.info(f"[PERF-AI] prompt built in {(t_prompt_done-t_service_start)*1000:.1f}ms, prompt_len={len(prompt)}")

        t_stream_start = time.time()
        chunk_count = 0
        try:
            async for chunk in self._provider.stream_generate(messages):
                chunk_count += 1
                yield chunk
        finally:
            logger.info(f"[PERF-AI] stream_exercise_hint total={(time.time()-t_service_start)*1000:.1f}ms, prompt_build={(t_prompt_done-t_service_start)*1000:.1f}ms, stream={(time.time()-t_stream_start)*1000:.1f}ms, chunks={chunk_count}")


# 全局单例 - 独立模块
ai_service = AIService()

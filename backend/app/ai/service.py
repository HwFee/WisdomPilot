"""AI 服务层 - 支持多种 AI 提供商，与原有代码完全隔离

本文件定义了 ``AIService`` -- 面向业务层的统一 AI 服务入口。
它在 ``AIProvider``（抽象接口）之上封装了丰富的教育场景方法：
生成题目解析、代码审查、流式问答、练习题生成、个性化测试、编程题提示等。

架构定位：
::

    业务路由 (training/router.py)
        ↓ 调用
    AIService (本文件) -- 构造 prompt、解析 JSON、业务逻辑
        ↓ 委托
    AIProvider (provider/openai.py) -- 翻译为 chat messages
        ↓ 委托
    AICompletionClient (provider/client.py) -- HTTP 请求 + 重试 + SSE 解析

模块底部创建全局单例 ``ai_service``，在应用启动时由 ``core.lifespan``
注入配置（``configure()``），之后所有路由共享此实例。
"""

import json
import logging
from typing import Any, AsyncGenerator, Optional

# httpx：异步 HTTP 客户端，此处仅用于类型标注（支持外部注入共享连接池）
import httpx

# 读取全局配置（AI_PROVIDER / AI_MODEL 等），供状态查询等方法回退使用
from app.config import get_settings
# AIProviderConfig：AI 配置数据类（configure() 的入参）
from app.ai.config import AIProviderConfig
# provider 模块：AIProvider 抽象接口 + OpenAI 兼容实现 + 配置异常类型
from app.ai.provider import (
    AIProvider,
    AIProviderConfigurationError,
    OpenAICompatibleClient,
    OpenAICompatibleProvider,
)

# 模块级日志器：以模块全名命名，便于按包名过滤日志级别
logger = logging.getLogger(__name__)

# OpenAIProvider 是 OpenAICompatibleProvider 的别名，
# 当前所有兼容 OpenAI API 的服务商都使用同一个 Provider 实现。
OpenAIProvider = OpenAICompatibleProvider


# ---------------------------------------------------------------------------
# 模块级纯函数：构造编程题提示 prompt（与 AIService 实例无关，可单独测试）
# ---------------------------------------------------------------------------
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

    构造编程题 AI 提示的 prompt 文本。这是模块级纯函数，与 AIService
    实例无关，便于单独测试。

    三级提示形成渐进式引导（progressive disclosure）：
    - light: 轻度提示 -- 只给思路方向，不写代码。
    - medium: 中度提示 -- 给出伪代码框架，关键步骤用注释占位。
    - deep: 深度解析 -- 完整的算法设计 + 带注释的参考代码框架，
      但仍不直接给出完整可运行答案（教育场景下的刻意设计）。

    Args:
        exercise_title: 题目标题。
        exercise_description: 题目描述文本。
        difficulty: 难度等级 1-5。
        knowledge_points: 相关知识点列表。
        hint_level: 提示级别，``"light"`` / ``"medium"`` / ``"deep"``。
        code_template: 代码模板（可选）。
        sample_input: 示例输入（可选）。
        sample_output: 示例输出（可选）。

    Returns:
        构造好的中文 prompt 字符串，可直接作为 user message 发送给 AI。
    """
    # 难度数字到中文标签的映射
    difficulty_labels = {1: "入门", 2: "基础", 3: "中等", 4: "较难", 5: "困难"}
    # 难度越界（<1 或 >5）时回退到"中等"，保证 prompt 始终有难度标签
    diff_label = difficulty_labels.get(difficulty, "中等")

    # 拼接知识点上下文（若有）
    kp_context = ""
    if knowledge_points:
        kp_context = f"\n涉及知识点：{', '.join(knowledge_points)}"

    # 拼接示例输入输出上下文（若有）
    sample_context = ""
    if sample_input and sample_output:
        sample_context = f"""

示例：
输入：{sample_input}
输出：{sample_output}"""

    # 拼接代码模板上下文（若有）
    code_context = ""
    if code_template:
        code_context = f"""

代码模板：
```
{code_template}
```"""

    # 按提示级别分支构造不同深度的 prompt（light 最简，deep 最详细）
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

    # 返回构造好的 prompt 字符串，作为 user 消息交给 provider
    return prompt


# ---------------------------------------------------------------------------
# AIService 类：AI 服务统一入口（业务层的 AI 能力聚合器）
# ---------------------------------------------------------------------------
class AIService:
    """AI 服务统一入口 -- 面向业务层的 AI 能力聚合器。

    本类是 WisdomPilot 后台与 AI 大模型交互的「总闸门」。它不直接处理
    HTTP 请求，而是将业务语义（选择题分析、代码审查、练习题生成等）
    转化为合适的 prompt，然后委托给底层的 ``AIProvider`` 执行。

    职责：
    1. **配置管理**：通过 ``configure()`` 注入 ``AIProviderConfig``，
       自动创建 ``OpenAICompatibleClient`` → ``OpenAICompatibleProvider`` 链路。
    2. **配置检查**：每个业务方法内部先检查 ``is_configured()``，
       未配置则返回友好的中文提示而非抛出异常。
    3. **Prompt 工程**：将业务上下文（题目、选项、用户答案、知识点等）
       拼接为结构化的中文 prompt，引导 AI 按教育场景输出。
    4. **JSON 解析容错**：对 AI 返回的 JSON 做防御性解析，解析失败
       返回空结果而非抛出异常（因为 AI 输出不可完全预测）。
    5. **性能监控**：关键方法（如 ``stream_exercise_hint``）记录各阶段
       耗时日志，便于排查性能瓶颈。

    Attributes:
        _provider: AI 能力提供者实例（``OpenAICompatibleProvider``），
            需要先调用 ``configure()`` 才会被创建。
        _config: 当前生效的 AI 配置快照。
        _protocol_client: 底层 HTTP 客户端（``OpenAICompatibleClient``），
            负责请求重试和 SSE 解析。
        _http_client: 可选的共享 httpx 客户端（外部注入时使用）。
    """

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        """初始化 AI 服务。

        Args:
            http_client: 可选的外部 httpx AsyncClient，用于共享连接池。
                若为 None，则内部自行为每个 provider 创建独立客户端。
        """
        self._provider: Optional[AIProvider] = None
        self._config: Optional[AIProviderConfig] = None
        self._protocol_client: OpenAICompatibleClient | None = None
        self._http_client = http_client

    def configure(self, config: AIProviderConfig) -> None:
        """配置 AI 提供商（仅支持 DeepSeek / OpenAI 兼容 API）.

        根据传入的配置创建或更新底层的 provider 链路：
        ``OpenAICompatibleClient`` → ``OpenAICompatibleProvider``。

        设计决策：只允许 OpenAI 兼容的服务商，因为内部 prompt 和响应
        解析都基于 OpenAI Chat Completions 格式。

        Args:
            config: AI 提供商配置对象。

        Raises:
            AIProviderConfigurationError: 传入了不支持的 provider 名称。
        """
        # 白名单校验：只放行 OpenAI 兼容的服务商（内部 prompt 与响应解析均
        # 基于 Chat Completions 格式，其他厂商格式不兼容）
        if config.provider not in {"openai", "siliconflow", "deepseek"}:
            raise AIProviderConfigurationError(
                f"Unsupported AI provider: {config.provider}"
            )
        if self._protocol_client is None:
            # 首次配置：创建新的 HTTP 客户端
            self._protocol_client = OpenAICompatibleClient(
                config,
                http_client=self._http_client,
            )
        else:
            # 重新配置：复用已有客户端实例，只更新配置参数（运行时热切换）
            self._protocol_client.configure(config)
        self._provider = OpenAICompatibleProvider(self._protocol_client)
        # 保存配置快照，供 is_configured() / get_provider_status() 判断与回退
        self._config = config

    def _require_provider(self) -> AIProvider:
        """断言 provider 已配置，否则抛出异常。

        所有业务方法在调用底层 provider 前必须先调用此方法，
        避免 ``NoneType`` 访问错误。

        Returns:
            已配置的 AIProvider 实例。

        Raises:
            AIProviderConfigurationError: AI 服务尚未配置。
        """
        if self._provider is None:
            raise AIProviderConfigurationError("AI service is not configured")
        return self._provider

    async def aclose(self) -> None:
        """关闭底层 HTTP 客户端，释放网络资源。

        在应用关闭时由 lifespan 调用，确保连接池被正确回收。
        外部注入的 HTTP 客户端不由本方法管理生命周期。
        """
        if self._protocol_client is not None:
            await self._protocol_client.close()

    def is_configured(self) -> bool:
        """检查 AI 服务是否已配置完成。

        配置完成的标志是 provider 和 config 均不为 None。
        业务方法以此判断是「正常调用 AI」还是「返回兜底提示」。

        Returns:
            True 表示已配置，可以安全调用 AI。
        """
        return self._provider is not None and self._config is not None

    @property
    def provider(self) -> Optional[AIProvider]:
        """获取当前 provider 实例（只读属性）.

        Returns:
            若已配置则返回 AIProvider，否则返回 None。
        """
        return self._provider

    async def get_provider_status(self) -> dict:
        """获取当前 provider 的连接状态信息。

        用于管理后台或状态检查接口，返回当前使用的服务商标识和模型名。

        Returns:
            包含 ``current_provider``、``current_model``、``is_local_first``
            和 ``providers`` 的状态字典。
        """
        settings = get_settings()
        # 未配置时回退到环境变量中的默认值，保证状态接口始终可读
        current_type = self._config.provider if self._config else settings.AI_PROVIDER

        return {
            "current_provider": current_type,
            "current_model": self._config.model if self._config else settings.AI_MODEL,
            # 以下两个字段为兼容旧接口保留（当前仅走云端 OpenAI 兼容通道）
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
        """生成选择题 AI 解答（错题分析场景）。

        将题目、选项、学生选择和正确答案拼接为结构化 prompt，
        引导 AI 从「误解分析 → 正确答案解释 → 学习建议」三层输出。

        Args:
            question: 选择题题干文本。
            options: 选项列表，如 ``["选项A", "选项B", "选项C", "选项D"]``。
            user_selected_index: 学生选择的选项索引（0-based）。
            correct_index: 正确答案的选项索引（0-based）。

        Returns:
            AI 生成的解答文本。若未配置则返回 ``"AI 服务未配置，请联系管理员。"``。
        """
        if not self.is_configured():
            return "AI 服务未配置，请联系管理员。"

        provider = self._require_provider()
        # 取出学生所选与正确选项的文本，供 prompt 展示
        user_option = options[user_selected_index]
        correct_option = options[correct_index]

        # chr(10)=换行、chr(65)='A'：将选项列表格式化为 "A. xxx\nB. yyy" 题面
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

        return await provider.generate_explanation(prompt)

    async def generate_code_review(
        self,
        code: str,
        language: str,
    ) -> str:
        """生成代码审查报告。

        将学生代码和语言类型委托给 provider 的 ``review_code()`` 方法，
        由该方法自动添加代码审查专家的 system prompt。

        Args:
            code: 学生提交的源代码文本。
            language: 编程语言（如 ``"python"``、``"javascript"``）。

        Returns:
            AI 生成的代码审查报告。若未配置则返回兜底提示。
        """
        if not self.is_configured():
            return "AI 服务未配置，请联系管理员。"

        provider = self._require_provider()

        return await provider.review_code(code, language)

    async def generate_chat(
        self,
        message: str,
    ) -> str:
        """生成 AI 问答（导师对话场景）。

        构造一个包含「编程老师」角色的 prompt，包裹学生问题后
        发送给 AI 生成回答。非流式，等待完整响应后返回。

        Args:
            message: 学生输入的问题文本。

        Returns:
            AI 生成的回答文本。若未配置则返回兜底提示。
        """
        if not self.is_configured():
            return "AI 服务未配置，请联系管理员。"

        provider = self._require_provider()

        return await provider.generate_explanation(
            f"你是一位耐心的编程老师。学生的问题是：\n\n{message}\n\n请给出简洁、有帮助的回答。"
        )

    async def stream_chat(
        self,
        message: str,
        context: Optional[dict] = None,
    ) -> AsyncGenerator[str, None]:
        """流式生成 AI 问答（支持题目上下文）。

        与 ``generate_chat()`` 的区别：本方法使用 ``stream_generate()``
        而非 ``generate_explanation()``，逐个 chunk yield 文本，前端可
        实现实时打字机效果。

        当提供 ``context`` 时，会拼接题目类型、题目文本、选项等信息
        作为上下文，让 AI 在理解题目的基础上回答学生的追问。

        Args:
            message: 学生输入的问题文本。
            context: 可选的题目上下文字典，包含：
                - ``type``: 题目类型（如 "choice"）
                - ``question``: 题目文本
                - ``options``: 选项列表

        Yields:
            AI 生成的文本片段（每个 chunk 通常是几个字到一句话）。
            若未配置，则 yield 兜底提示文本后立即返回。
        """
        if not self.is_configured():
            yield "AI 服务未配置，请联系管理员。"
            return

        provider = self._require_provider()

        if context:
            # 从 context 字典中提取题目上下文信息
            q_type = context.get("type", "")
            q_text = context.get("question", "")
            q_opts = context.get("options", [])

            # 将选项列表格式化为 "A. xxx\nB. yyy" 的形式
            opts_str = ""
            if q_opts:
                # chr(65)='A'：选项索引转字母标签
                opts_str = "\n".join(
                    [f"{chr(65 + i)}. {opt}" for i, opt in enumerate(q_opts)]
                )

            # 无选项时不输出"选项："行，避免 prompt 中出现空块
            opts_line = f"选项：\n{opts_str}" if opts_str else ""

            # 拼接上下文信息
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
            # 无上下文时，用简单的编程老师角色 prompt
            prompt = f"你是一位耐心的编程老师。学生的问题是：\n\n{message}\n\n请给出简洁、有帮助的回答。"

        # 单条 user 消息即可：多轮历史由调用方拼进 context/prompt 文本
        messages = [
            {"role": "user", "content": prompt},
        ]

        async for chunk in provider.stream_generate(messages):
            yield chunk

    async def generate_choice_analysis(
        self,
        question_text: str,
        options: list[str],
        user_selected: int,
        correct_answer: int,
    ) -> dict:
        """生成选择题 AI 分析 -- 针对错误选项进行详细分析。

        根据学生答案是否正确，构造两种不同的 prompt 策略：
        - **答对**：简短肯定 + 强化理解，2-3 句话。
        - **答错**：详细分析误解点 + 逐步推导正确答案 + 记忆技巧。

        返回值是字典格式，便于前端区分渲染「答对」和「答错」两种 UI。

        Args:
            question_text: 题目文本。
            options: 选项列表。
            user_selected: 学生选择的选项索引（0-based）。
            correct_answer: 正确答案的选项索引（0-based）。

        Returns:
            形如 ``{"analysis": "...", "is_correct": True/False}`` 的字典。
        """
        if not self.is_configured():
            return {"analysis": "AI 服务未配置，请联系管理员。", "is_correct": False}

        provider = self._require_provider()

        # 判断答案是否正确
        is_correct = user_selected == correct_answer
        # 将数字索引转换为字母标签（0→A, 1→B, ...）
        # 0→A、1→B：字母标签更适合出现在面向学生的 prompt 里
        selected_label = chr(65 + user_selected)
        correct_label = chr(65 + correct_answer)
        selected_text = options[user_selected]
        correct_text = options[correct_answer]

        if is_correct:
            # 答对场景：简短肯定 + 强化理解
            prompt = f"""学生选择了正确答案，请给予简短肯定并强化理解：

题目：{question_text}
{chr(10).join([f"{chr(65 + i)}. {opt}" for i, opt in enumerate(options)])}

学生选择了：{selected_label}. {selected_text}

请用2-3句话肯定学生的答案，并简要解释为什么这个答案是正确的。"""
        else:
            # 答错场景：三步分析法 -- 误解点 → 推导过程 → 学习技巧
            prompt = f"""学生做错了以下选择题，请详细分析：

题目：{question_text}
{chr(10).join([f"{chr(65 + i)}. {opt}" for i, opt in enumerate(options)])}

学生选择了：{selected_label}. {selected_text}
正确答案是：{correct_label}. {correct_text}

请：
1. 分析学生选择 {selected_label} 的可能误解点，为什么会被这个选项迷惑？
2. 逐步推导为什么 {correct_label} 是正确答案
3. 指出学习这个概念时常见的陷阱和记忆技巧"""

        analysis = await provider.generate_explanation(prompt)
        # 返回结构化结果：前端据此区分渲染"答对/答错"两种 UI
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
        """使用 AI 自动生成练习题。

        根据章节信息构造 detailed prompt，引导 AI 以 JSON 格式返回
        结构化练习题数据。支持选择题和填空题两种题型。

        设计要点：
        - 只支持 ``"choice"`` 和 ``"fill_blank"`` 两种类型，其他类型
          会记录警告日志并返回空列表。
        - AI 返回的 JSON 可能被 ```json``` 代码块包裹，解析时先尝试
          提取 ``[...]`` 片段，失败则尝试解析整个响应。
        - JSON 解析失败时返回空列表（防御性容错，因为 AI 输出不可 100% 可控）。

        Args:
            chapter_title: 章节标题。
            chapter_description: 章节描述。
            topic: 可选的主题关键词（用于聚焦题目范围）。
            count: 生成题目数量，默认 5。
            exercise_type: 题目类型，``"choice"`` 或 ``"fill_blank"``。
            difficulty: 难度等级 1-5。

        Returns:
            练习题字典列表，每道题包含 content、solution、hints 等字段。
            生成失败时返回空列表 []。
        """
        if not self.is_configured():
            return []

        provider = self._require_provider()

        # 难度数字→中文标签映射（1-5 级，与 _build_exercise_hint_prompt 保持一致）
        difficulty_labels = {
            1: "入门",
            2: "基础",
            3: "中等",
            4: "较难",
            5: "困难",
        }
        difficulty_label = difficulty_labels.get(difficulty, "基础")

        # 题型白名单：AI 仅按此返回 choice / fill_blank 两种结构
        type_mapping = {
            "choice": "选择题",
            "fill_blank": "填空题",
        }

        # 只支持已定义的题型，不支持的类型直接返回空列表
        if exercise_type not in type_mapping:
            logger.warning(
                f"[AIService] Unsupported exercise type '{exercise_type}', skipping generation."
            )
            return []

        # 可选主题：追加到 prompt 中聚焦出题范围
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

        response = await provider.generate_explanation(prompt)

        # 防御性 JSON 解析：AI 返回的内容不可完全预测
        try:
            # 先尝试从响应中提取 JSON 数组片段（AI 常包裹在 ```json``` 中）
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                exercises = json.loads(json_str)
                return exercises
            else:
                # 未找到数组标记，尝试将整个响应作为 JSON 解析
                exercises = json.loads(response)
                return exercises
        except json.JSONDecodeError:
            # AI 返回了不合法的 JSON，返回空列表（容错）
            return []

    async def generate_knowledge_content(
        self,
        chapter_title: str,
        chapter_description: str,
        course_name: str = "编程",
        knowledge_points: Optional[list[str]] = None,
    ) -> dict:
        """
        生成章节知识点内容。

        引导 AI 以结构化 JSON 返回知识点的标题、详细讲解（Markdown 格式）、
        代码示例、难度等级和关联知识点。用于自动为课程章节填充教学内容。

        Args:
            chapter_title: 章节标题。
            chapter_description: 章节描述。
            course_name: 课程名称（嵌入到 prompt 中设定 AI 角色）。
            knowledge_points: 可选的知识点线索列表，用于提示 AI 扩展。

        Returns:
            包含 ``knowledge_points`` 列表、``summary`` 和 ``estimated_time``
            的字典。生成失败时返回空字典 {}。
        """
        if not self.is_configured():
            return {}

        provider = self._require_provider()

        # 已有知识点线索：作为提示注入，让 AI 在其基础上扩展讲解
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

        response = await provider.generate_explanation(prompt)

        # 防御性 JSON 解析（AI 输出不可完全预测）
        try:
            # 先尝试提取 {...} 片段（AI 常包裹在 ```json``` 中）
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                return json.loads(response)
        except json.JSONDecodeError:
            # 解析失败返回空字典（容错）
            return {}

    async def generate_personalized_quiz(
        self,
        chapter_title: str,
        chapter_description: str,
        user_profile: Optional[Any] = None,
        question_count: int = 5,
        question_types: list[str] | None = None,
        difficulty_range: tuple[int, int] = (1, 5),
        knowledge_points: Optional[list[str]] = None,
    ) -> list[dict]:
        """
        根据用户画像生成个性化测试题。

        与 ``generate_exercises()`` 的区别：本方法支持用户画像上下文，
        会根据学生的当前水平、近期正确率和薄弱知识点来定制题目，
        实现「因材施教」的自适应出题策略。

        核心设计：
        - 从 ``user_profile`` 中提取薄弱知识点，自动作为优先考查目标。
        - 支持选择题、编程题、填空题的混合出题。
        - 难度范围通过 ``(min, max)`` 元组控制。

        Args:
            chapter_title: 章节标题。
            chapter_description: 章节描述。
            user_profile: 用户画像对象，包含 ``weak_knowledge_points``、
                ``current_level``、``recent_accuracy`` 等属性。
            question_count: 题目数量。
            question_types: 题目类型列表，如 ``["choice", "programming"]``。
            difficulty_range: 难度范围 ``(min, max)``，如 ``(2, 4)``。
            knowledge_points: 考查的知识点列表。

        Returns:
            测试题字典列表。生成失败时返回空列表 []。
        """
        if not self.is_configured():
            return []

        provider = self._require_provider()

        # 调用方未指定题型时默认只出选择题（与 generate_exercises 默认行为一致）
        if question_types is None:
            question_types = ["choice"]

        # ---- 构建用户画像上下文 ----
        profile_context = ""
        if user_profile:
            # 用 getattr 安全获取用户画像字段（用户可能来自不同数据模型）
            weak_points = getattr(user_profile, "weak_knowledge_points", []) or []
            current_level = getattr(user_profile, "current_level", 1.0)
            recent_accuracy = getattr(user_profile, "recent_accuracy", 0.5)

            # 构造学生画像文本块
            profile_context = f"""
学生画像：
- 当前水平：{current_level:.1f}/5
- 近期正确率：{recent_accuracy:.0%}
- 薄弱知识点：{", ".join(weak_points) if weak_points else "无"}
"""
            # 如果有薄弱点，用薄弱点覆盖 knowledge_points -- 优先强化弱点
            if weak_points:
                knowledge_points = weak_points

        # 难度数字到中文标签的映射
        difficulty_labels = {1: "入门", 2: "基础", 3: "中等", 4: "较难", 5: "困难"}
        # 难度范围取首尾两个标签，prompt 中呈现为"入门 到 困难"
        min_diff = difficulty_labels.get(difficulty_range[0], "入门")
        max_diff = difficulty_labels.get(difficulty_range[1], "困难")

        # 题型映射（支持比 generate_exercises 更多的题型）
        type_names = {
            "choice": "选择题",
            "programming": "编程题",
            "fill_blank": "填空题",
        }
        # 未映射到的题型原样保留（如自定义类型），避免 prompt 丢失信息
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

        response = await provider.generate_explanation(prompt)

        # 防御性 JSON 解析（AI 输出不可完全预测）
        try:
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
        通用的 AI 文本生成方法。

        这是最低抽象级别的入口，直接将 prompt 发送给 AI 并返回结果。
        如果提供了 ``system_prompt``，会将其拼接在 prompt 前面，
        利用 ``generate_explanation`` 的 system 消息机制实现角色设定。

        Args:
            prompt: 用户提示词（User 消息内容）。
            system_prompt: 可选的系统提示词（会拼接在 prompt 前方）。

        Returns:
            AI 生成的文本。若未配置则返回兜底提示。
        """
        if not self.is_configured():
            return "AI 服务未配置，请联系管理员。"

        provider = self._require_provider()

        # 如有 system_prompt，拼接后整个作为 prompt 发送
        # generate_explanation 内部会将此 prompt 包装为 user 消息
        # 并在前面自动添加编程老师 system prompt
        if system_prompt:
            combined_prompt = f"{system_prompt}\n\n{prompt}"
            return await provider.generate_explanation(combined_prompt)
        else:
            return await provider.generate_explanation(prompt)

    async def generate_messages(
        self,
        messages: list[dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> str:
        """多轮对话生成：直接发送完整 messages 列表，可选前置 system 消息。

        与 ``generate()`` 的区别：调用方可以自由构造多轮对话（user/assistant
        交替、system 角色设定），适合苏格拉底导师等需要把最近对话历史传给
        LLM 的场景。未配置时返回兜底提示文本（与 ``generate()`` 行为一致）。

        Args:
            messages: 对话消息列表，格式 ``[{"role": "user", "content": "..."}]``。
            system_prompt: 可选的系统提示词，会作为第一条 system 消息插入。

        Returns:
            AI 生成的完整文本。若未配置则返回兜底提示。
        """
        if not self.is_configured():
            return "AI 服务未配置，请联系管理员。"

        provider = self._require_provider()

        if system_prompt:
            # 将 system 提示前置为第一条消息（Chat Completions 要求 system 消息在最前）
            messages = [{"role": "system", "content": system_prompt}, *messages]
        return await provider.complete_messages(messages)

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
        生成题目解析。

        与 ``generate_choice_analysis()`` 类似但接口不同：本方法接收
        文本格式的答案（而非数字索引），适用于非选择题或已转换格式的场景。

        Args:
            question_text: 题目文本。
            options: 选项列表。
            user_answer: 用户答案（文本）。
            correct_answer: 正确答案（文本）。
            is_correct: 答案是否正确。
            knowledge_points: 相关知识点列表。

        Returns:
            形如 ``{"analysis": "...", "is_correct": True/False}`` 的字典。
        """
        if not self.is_configured():
            return {"analysis": "AI 服务未配置", "is_correct": is_correct}

        provider = self._require_provider()

        # 拼接知识点上下文
        kp_context = ""
        if knowledge_points:
            kp_context = f"\n相关知识点：{', '.join(knowledge_points)}"

        if is_correct:
            # 答对：简短肯定 + 强化理解 + 拓展提示
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
            # 答错：误解分析 + 正确答案推导 + 学习建议
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

        analysis = await provider.generate_explanation(prompt)
        # 返回结构化结果：前端据此区分渲染"答对/答错"两种 UI
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
        流式生成编程题 AI 提示 -- 挑战之路使用的核心方法。

        这是 AIService 中性能最敏感的方法之一：构造 prompt 后通过
        ``stream_generate()`` 逐块 yield 提示内容，让前端实时展示
        AI 的「思考过程」打字效果。

        在方法出入口记录了详细的性能日志（[PERF-AI]），包括：
        - prompt 构造耗时
        - prompt 长度
        - 流式传输耗时
        - 总 chunk 数

        Args:
            exercise_title: 题目标题。
            exercise_description: 题目描述。
            difficulty: 难度 1-5。
            knowledge_points: 相关知识点。
            hint_level: 提示级别 ``"light"`` / ``"medium"`` / ``"deep"``。
            code_template: 代码模板（可选）。
            sample_input: 示例输入（可选）。
            sample_output: 示例输出（可选）。

        Yields:
            AI 生成的提示内容（流式）。
        """
        import time

        t_service_start = time.time()
        if not self.is_configured():
            logger.error("[PERF-AI] stream_exercise_hint: AI not configured!")
            yield "AI 服务未配置，请联系管理员。"
            return

        provider = self._require_provider()

        difficulty_labels = {1: "入门", 2: "基础", 3: "中等", 4: "较难", 5: "困难"}
        diff_label = difficulty_labels.get(difficulty, "中等")
        # 起始日志：标题截断到 30 字符，避免超长标题刷屏（[PERF-AI] 前缀便于 grep）
        logger.info(
            f"[PERF-AI] stream_exercise_hint starting: level={hint_level}, difficulty={diff_label}, title={exercise_title[:30]}..."
        )

        # 调用模块级纯函数构造结构化 prompt
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
        # 构造单条 user 消息，交给 provider 流式生成
        messages = [{"role": "user", "content": prompt}]
        t_prompt_done = time.time()
        logger.info(
            f"[PERF-AI] prompt built in {(t_prompt_done - t_service_start) * 1000:.1f}ms, prompt_len={len(prompt)}"
        )

        t_stream_start = time.time()
        chunk_count = 0
        try:
            async for chunk in provider.stream_generate(messages):
                chunk_count += 1
                yield chunk
        finally:
            # 无论成功或失败，都记录完整的性能指标
            logger.info(
                f"[PERF-AI] stream_exercise_hint total={(time.time() - t_service_start) * 1000:.1f}ms, prompt_build={(t_prompt_done - t_service_start) * 1000:.1f}ms, stream={(time.time() - t_stream_start) * 1000:.1f}ms, chunks={chunk_count}"
            )


# ---- 全局单例 ----
# ai_service 是 AIService 的唯一实例，在应用启动时由 core.lifespan
# 读取环境变量配置并调用 ai_service.configure()，之后所有业务路由
# 通过 ``from app.ai import ai_service`` 共享此实例。
# 单例模式避免了重复创建 HTTP 连接池和 AI 客户端实例的开销。
ai_service = AIService()

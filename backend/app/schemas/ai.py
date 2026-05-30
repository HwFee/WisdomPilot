"""AI 模块 Pydantic Schemas"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class ChoiceExplanationRequest(BaseModel):
    """选择题 AI 解答请求"""

    chapter_id: int
    subsection_index: int
    exercise_id: int
    question: str = Field(..., max_length=1000)
    options: List[str] = Field(..., max_length=10)
    user_selected_index: int
    correct_index: int


class ChoiceExplanationResponse(BaseModel):
    """选择题 AI 解答响应"""

    explanation: str


class CodeReviewRequest(BaseModel):
    """代码审查请求"""

    code: str = Field(..., max_length=5000)
    language: str = Field(..., max_length=20)
    chapter_id: Optional[int] = None
    subsection_index: Optional[int] = None


class CodeReviewResponse(BaseModel):
    """代码审查响应"""

    review: str
    score: Optional[int] = None
    suggestions: Optional[List[str]] = None


class AIProviderConfig(BaseModel):
    """AI 提供商配置"""

    provider: str = "deepseek"
    api_key: str = ""
    model: str = "deepseek-v4-flash"
    temperature: float = 0.7
    base_url: Optional[str] = None
    local_base_url: Optional[str] = None  # 本地服务地址（自动检测）
    is_local_first: bool = False  # 本地优先模式


class AIConfigResponse(BaseModel):
    """AI 配置响应"""

    provider: str
    model: str
    temperature: float
    is_configured: bool
    has_api_key: bool = False  # 是否有 API Key 已保存（不返回 key 本身）
    api_key_preview: Optional[str] = None  # 已保存 Key 的预览，如 "sk-cp****abcd"
    api_key_length: Optional[int] = None  # 已保存 Key 的长度
    connection_status: Optional[str] = None  # "connected" | "disconnected" | "unknown"
    connection_address: Optional[str] = None
    is_local_first: bool = False


class UpdateAIConfigRequest(BaseModel):
    """更新 AI 配置请求"""

    provider: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    base_url: Optional[str] = None
    local_base_url: Optional[str] = None
    is_local_first: Optional[bool] = None


class AIChatRequest(BaseModel):
    """AI 问答请求"""

    message: str = Field(..., max_length=10000)


class AIChatResponse(BaseModel):
    """AI 问答响应"""

    reply: str


class ChoiceAnalysisRequest(BaseModel):
    """选择题 AI 分析请求 —— 学生答错后触发"""

    question_text: str = Field(..., max_length=1000)
    options: list[str] = Field(..., max_length=10)
    user_selected: int
    correct_answer: int
    chapter_id: int
    exercise_id: str = Field(..., max_length=50)


class ChoiceAnalysisResponse(BaseModel):
    """选择题 AI 分析响应"""

    analysis: str
    is_correct: bool


class CodeFeedbackRequest(BaseModel):
    """编程题 AI 反馈请求 —— 代码纠错 + 优化 + 建议 三合一"""

    code: str = Field(..., max_length=5000)
    language: str = Field(..., max_length=20)
    exercise_description: str = Field(..., max_length=1000)
    expected_output: str = Field(default="", max_length=500)
    actual_output: str = Field(default="", max_length=500)
    status: str = Field(default="", max_length=50)
    error_message: str = Field(default="", max_length=500)
    chapter_id: int
    exercise_id: str = Field(..., max_length=50)


class CodeFeedbackResponse(BaseModel):
    """编程题 AI 反馈响应"""

    diagnosis: str
    suggestions: str
    optimized_code: str


class ChatStreamRequest(BaseModel):
    """AI 流式问答请求"""

    message: str = Field(..., max_length=10000)
    context: Optional[dict] = Field(default=None, description="题目上下文 {type, question, options?, code?}")


class ProviderStatus(BaseModel):
    """单个 Provider 的状态"""

    type: str  # "ollama" | "lmstudio" | "minimax" | "deepseek"
    address: str
    status: str  # "connected" | "disconnected" | "unknown"
    model: Optional[str] = None
    available_models: Optional[list[str]] = None


class AIStatusResponse(BaseModel):
    """AI 服务状态响应"""

    current_provider: str
    current_model: str
    is_local_first: bool
    providers: list[ProviderStatus]


class TestConnectionRequest(BaseModel):
    """测试 AI 连接请求"""

    provider: str = Field(..., description="ollama | lmstudio | minimax | deepseek")
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    local_base_url: Optional[str] = None


class TestConnectionResponse(BaseModel):
    """测试 AI 连接响应"""

    success: bool
    message: str
    model: Optional[str] = None
    address: Optional[str] = None
    latency_ms: Optional[int] = None


class ExerciseHintRequest(BaseModel):
    """编程题 AI 提示请求 - 挑战之路使用"""

    exercise_id: Optional[str] = Field(default=None, max_length=100, description="题目唯一标识（优先使用）")
    exercise_title: str = Field(..., max_length=200, description="题目标题")
    exercise_description: str = Field(..., max_length=5000, description="题目描述")
    difficulty: int = Field(..., ge=1, le=5, description="难度 1-5")
    knowledge_points: list[str] = Field(default=[], description="相关知识点")
    hint_level: Literal["light", "medium", "deep"] = Field(..., description="提示级别")
    code_template: str = Field(default="", max_length=5000, description="代码模板")
    sample_input: str = Field(default="", max_length=500, description="示例输入")
    sample_output: str = Field(default="", max_length=500, description="示例输出")


class ExerciseHintResponse(BaseModel):
    """编程题 AI 提示响应"""

    hint: str
    cost: int

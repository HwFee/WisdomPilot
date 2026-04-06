"""AI 模块 Pydantic Schemas"""

from pydantic import BaseModel, Field
from typing import Optional, List


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

    provider: str = "openai"
    api_key: str = ""
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    base_url: Optional[str] = None


class AIConfigResponse(BaseModel):
    """AI 配置响应"""

    provider: str
    model: str
    temperature: float
    is_configured: bool


class UpdateAIConfigRequest(BaseModel):
    """更新 AI 配置请求"""

    provider: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    base_url: Optional[str] = None


class AIChatRequest(BaseModel):
    """AI 问答请求"""

    message: str = Field(..., max_length=2000)


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

    message: str = Field(..., max_length=2000)
    context: Optional[dict] = Field(default=None, description="题目上下文 {type, question, options?, code?}")

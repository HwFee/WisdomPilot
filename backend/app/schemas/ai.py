"""AI 模块 Pydantic Schemas"""

from pydantic import BaseModel, Field
from typing import Optional, List


class ChoiceExplanationRequest(BaseModel):
    """选择题 AI 解答请求"""

    chapter_id: int
    subsection_index: int
    exercise_id: int
    question: str
    options: List[str]
    user_selected_index: int
    correct_index: int


class ChoiceExplanationResponse(BaseModel):
    """选择题 AI 解答响应"""

    explanation: str


class CodeReviewRequest(BaseModel):
    """代码审查请求"""

    code: str
    language: str
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

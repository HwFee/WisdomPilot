"""
Mastery Quiz Schemas - 精进之路学习模式的数据模型

用于支持新的精进之路功能：
1. 知识点展示
2. AI 生成个性化测试题
3. 测试结果提交与反馈
"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


# ========================================
# Knowledge Point Schemas (知识点)
# ========================================

class KnowledgePoint(BaseModel):
    """知识点模型"""
    id: str = Field(..., description="知识点唯一标识")
    title: str = Field(..., description="知识点标题")
    content: str = Field(..., description="知识点内容（Markdown格式）")
    examples: Optional[list[str]] = Field(default=None, description="代码示例")
    difficulty: int = Field(default=1, ge=1, le=5, description="难度等级 1-5")
    related_points: Optional[list[str]] = Field(default=None, description="相关知识点ID")
    order_index: int = Field(default=0, description="排序索引")


class KnowledgeContentResponse(BaseModel):
    """章节知识点内容响应"""
    chapter_id: int
    chapter_title: str
    knowledge_points: list[KnowledgePoint]
    total_points: int
    estimated_time: int = Field(..., description="预计学习时间（分钟）")
    prerequisites: Optional[list[str]] = Field(default=None, description="前置知识点")
    next_chapters: Optional[list[str]] = Field(default=None, description="下一章节")


# ========================================
# Mastery Quiz Question Schemas (测试题)
# ========================================

class MasteryQuizQuestion(BaseModel):
    """精进之路测试题模型"""
    id: str = Field(..., description="题目唯一标识")
    type: str = Field(..., description="题目类型：choice/programming/fill_blank")
    difficulty: int = Field(default=1, ge=1, le=5, description="难度等级 1-5")
    content: dict = Field(..., description="题目内容，结构因类型而异")
    solution: Optional[dict] = Field(default=None, description="答案和解析")
    knowledge_points: list[str] = Field(default_factory=list, description="考查的知识点")
    hints: Optional[list[str]] = Field(default=None, description="提示")
    test_cases: Optional[list[dict]] = Field(default=None, description="编程题的测试用例")
    generated_at: Optional[datetime] = Field(default=None, description="AI生成时间")


# ========================================
# Generate Quiz Schemas (生成测试题)
# ========================================

class MasteryQuizGenerateRequest(BaseModel):
    """生成测试题请求"""
    course_id: int = Field(..., description="课程ID")
    chapter_id: int = Field(..., description="章节ID")
    question_count: int = Field(default=5, ge=1, le=20, description="题目数量")
    question_types: list[str] = Field(
        default=["choice", "programming"],
        description="题目类型列表"
    )
    difficulty_range: tuple[int, int] = Field(
        default=(1, 5),
        description="难度范围 (min, max)"
    )
    focus_weak_points: bool = Field(
        default=True,
        description="是否根据薄弱点出题"
    )
    custom_instructions: Optional[str] = Field(
        default=None,
        description="自定义出题要求"
    )


class MasteryQuizGenerateResponse(BaseModel):
    """生成测试题响应"""
    success: bool
    session_id: str = Field(default="", description="测试会话ID")
    questions: list[MasteryQuizQuestion] = Field(default_factory=list)
    user_profile_used: bool = Field(
        default=False,
        description="是否使用了用户画像"
    )
    weak_points_addressed: list[str] = Field(
        default_factory=list,
        description="针对的薄弱点"
    )
    message: str = Field(default="", description="结果消息")


# ========================================
# Submit Quiz Schemas (提交测试)
# ========================================

class QuizAnswer(BaseModel):
    """单个题目答案"""
    question_id: str
    answer: Any = Field(..., description="用户答案")
    time_spent: int = Field(default=0, ge=0, description="答题用时（秒）")


class MasteryQuizSubmitRequest(BaseModel):
    """提交测试请求"""
    session_id: str = Field(..., description="测试会话ID")
    answers: list[QuizAnswer] = Field(..., description="答案列表")
    total_time: Optional[int] = Field(default=None, description="总用时（秒）")


class QuestionResult(BaseModel):
    """单题结果"""
    question_id: str
    is_correct: bool
    user_answer: Any
    correct_answer: Optional[Any] = None
    explanation: Optional[str] = None
    knowledge_points: list[str] = Field(default_factory=list)


class MasteryQuizSubmitResponse(BaseModel):
    """提交测试响应"""
    session_id: str
    total_questions: int
    correct_answers: int
    accuracy: float = Field(..., ge=0, le=1, description="正确率")
    xp_earned: int = Field(default=0, description="获得的经验值")
    mastery_points_earned: int = Field(default=0, description="获得的掌握点数")
    results: list[QuestionResult] = Field(default_factory=list)
    recommendations: list[str] = Field(
        default_factory=list,
        description="学习建议"
    )
    passed: bool = Field(
        default=False,
        description="是否通过（正确率>=80%）"
    )


# ========================================
# User Profile for Quiz Generation (用户画像)
# ========================================

class UserProfileForQuiz(BaseModel):
    """用于生成测试题的用户画像"""
    user_id: str
    course_id: int
    current_level: float = Field(default=1.0, description="当前水平 1-5")
    weak_knowledge_points: list[str] = Field(
        default_factory=list,
        description="薄弱知识点"
    )
    strong_knowledge_points: list[str] = Field(
        default_factory=list,
        description="擅长知识点"
    )
    recent_accuracy: float = Field(default=0.5, description="近期正确率")
    preferred_question_types: list[str] = Field(
        default=["choice"],
        description="偏好题型"
    )
    learning_style: Optional[str] = Field(
        default=None,
        description="学习风格偏好"
    )

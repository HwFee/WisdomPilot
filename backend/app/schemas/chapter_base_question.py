"""Chapter Base Question Schemas - 章节基础测试题数据模型"""

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


# ========================================
# Base Question Schemas
# ========================================

class BaseQuestionResponse(BaseModel):
    """基础测试题响应"""
    id: int
    chapter_id: int
    order_index: int
    type: str = Field(..., description="题目类型: choice, programming, fill_blank")
    text: str = Field(..., description="题目内容")
    options: Optional[List[str]] = Field(default=None, description="选择题选项")
    knowledge_points: List[str] = Field(default_factory=list)
    difficulty: int = Field(default=1, description="难度 1-2")
    code_template: Optional[str] = Field(default=None, description="编程题代码模板")
    test_cases: Optional[List[dict]] = Field(default=None, description="编程题测试用例")


class BaseQuestionListResponse(BaseModel):
    """章节基础题列表响应"""
    chapter_id: int
    chapter_title: str
    total_questions: int
    questions: List[BaseQuestionResponse]


# ========================================
# Answer Submission Schemas
# ========================================

class BaseAnswerSubmit(BaseModel):
    """基础题答案提交"""
    question_id: int
    answer: str = Field(..., description="用户答案")
    time_spent: int = Field(default=0, ge=0, description="答题用时（秒）")


class BaseAnswersSubmitRequest(BaseModel):
    """批量提交基础题答案"""
    answers: List[BaseAnswerSubmit]


class BaseQuestionResult(BaseModel):
    """单题结果"""
    question_id: int
    is_correct: bool
    user_answer: str
    correct_answer: str
    explanation: Optional[str] = None
    knowledge_points: List[str] = Field(default_factory=list)


class BaseAnswersSubmitResponse(BaseModel):
    """基础题提交结果"""
    total_questions: int
    correct_answers: int
    accuracy: float = Field(..., ge=0, le=1, description="正确率")
    results: List[BaseQuestionResult]
    weak_points: List[str] = Field(
        default_factory=list,
        description="识别的薄弱知识点"
    )
    strong_points: List[str] = Field(
        default_factory=list,
        description="掌握较好的知识点"
    )


# ========================================
# AI Enhanced Quiz Schemas
# ========================================

class EnhancedQuizGenerateRequest(BaseModel):
    """生成强化测试题请求"""
    course_id: int
    chapter_id: int
    weak_points: List[str] = Field(
        default_factory=list,
        description="需要强化的薄弱知识点"
    )
    strong_points: List[str] = Field(
        default_factory=list,
        description="已掌握的知识点（用于避免重复）"
    )
    question_count: int = Field(default=3, ge=1, le=10, description="生成题目数量")
    question_types: List[str] = Field(
        default=["choice"],
        description="题目类型列表"
    )


class EnhancedQuizQuestion(BaseModel):
    """强化测试题"""
    id: str
    type: str
    difficulty: int
    text: str
    options: Optional[List[str]] = None
    correct_answer: str = Field(default="", description="正确答案")
    explanation: Optional[str] = Field(default=None, description="答案解析")
    code_template: Optional[str] = None
    test_cases: Optional[List[dict]] = None
    knowledge_points: List[str] = Field(default_factory=list)


class EnhancedQuizGenerateResponse(BaseModel):
    """生成强化测试题响应"""
    success: bool
    session_id: str = Field(default="", description="测试会话ID")
    questions: List[EnhancedQuizQuestion] = Field(default_factory=list)
    weak_points_addressed: List[str] = Field(
        default_factory=list,
        description="针对的薄弱点"
    )
    message: str = Field(default="", description="结果消息")


class EnhancedQuizSubmitRequest(BaseModel):
    """提交强化测试题答案"""
    session_id: str
    answers: List[dict]  # [{question_id: str, answer: str}]


class EnhancedQuizSubmitResponse(BaseModel):
    """提交强化测试题结果"""
    success: bool
    session_id: str
    total_questions: int
    correct_answers: int
    accuracy: float
    xp_earned: int = Field(default=0, description="获得的经验值")
    mastery_points_earned: int = Field(default=0, description="获得的掌握点数")
    results: List[dict] = Field(default_factory=list)
    recommendations: List[str] = Field(
        default_factory=list,
        description="学习建议"
    )
    passed: bool = Field(
        default=False,
        description="是否通过（正确率>=80%）"
    )
    message: str = Field(default="", description="结果消息")

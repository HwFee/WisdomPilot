"""Mastery Progress Schemas - 精进之路进度数据模型"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class MasteryExerciseProgressSaveRequest(BaseModel):
    """保存精进之路做题进度"""
    course_id: int
    chapter_id: int
    question_id: int
    question_type: str = Field(default="base", description="base=基础测试, enhanced=强化测试")
    exercise_key: Optional[str] = Field(default=None, description="错题本关联key")
    is_completed: bool = Field(default=False, description="是否完成提交")
    is_correct: bool = Field(default=False, description="是否答对")
    user_answer: Optional[str] = Field(default=None, description="用户答案")
    correct_answer: Optional[str] = Field(default=None, description="正确答案")
    attempt_count: int = Field(default=1, description="尝试次数")


class MasteryExerciseProgressResponse(BaseModel):
    """精进之路做题进度响应"""
    success: bool
    progress_id: Optional[str] = None
    message: str = ""


class MasteryChapterProgressResponse(BaseModel):
    """精进之路章节进度响应"""
    chapter_id: int
    total_questions: int
    completed_questions: int
    correct_questions: int
    mastery_score: float
    is_passed: bool


class MasteryQuizCompleteRequest(BaseModel):
    """完成章节quiz请求"""
    course_id: int
    chapter_id: int
    results: List[dict]  # [{question_id: int, is_correct: bool, user_answer: str, correct_answer: str}]


class MasteryExerciseProgressItem(BaseModel):
    """单个题目的进度信息"""
    question_id: int
    question_index: int = 0
    question_type: str = "base"
    is_completed: bool = False
    is_correct: bool = False
    user_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    saved_code: Optional[str] = None
    current_language: str = "python"
    attempt_count: int = 0


class MasteryChapterDetailProgressResponse(BaseModel):
    """精进之路章节详细进度响应 - 包含每道题的进度"""
    chapter_id: int
    total_questions: int
    completed_questions: int
    correct_questions: int
    mastery_score: float
    is_passed: bool
    progress_items: List[MasteryExerciseProgressItem] = []

"""Pydantic schemas for learning statistics"""

from datetime import datetime
from typing import Optional
from app.models.stats import ProgressStatus
from pydantic import BaseModel, Field


class ChapterProgressBase(BaseModel):
    """Base schema for chapter progress"""
    chapter_id: int
    status: str = "not_started"
    progress_percent: int = Field(default=0, ge=0, le=100)
    completed_subsections: list[int] = Field(default_factory=list)
    completed_exercise_count: int = 0
    completed_exercises_by_subsection: dict[str, list[int]] = Field(default_factory=dict)
    # 存储每道题的答题结果：{chapterId}-{subsectionIndex}-{exerciseId}: "correct" | "wrong"
    exercise_results: dict[str, str] = Field(default_factory=dict)


class ChapterProgressResponse(ChapterProgressBase):
    """Schema for chapter progress response"""
    id: str
    user_id: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class UpdateProgressRequest(BaseModel):
    """Schema for updating chapter progress"""
    status: Optional[str] = None  # Accepts: "not_started", "in_progress", "completed"
    progress_percent: Optional[int] = Field(default=None, ge=0, le=100)
    completed_subsections: Optional[list[int]] = None
    completed_exercise_count: Optional[int] = None
    total_exercises: Optional[int] = None
    completed_exercises_by_subsection: Optional[dict[str, list[int]]] = None
    exercise_results: Optional[dict[str, str]] = None  # {exerciseKey: "correct" | "wrong"}


class LearningSessionResponse(BaseModel):
    """Schema for learning session response"""
    id: str
    user_id: str
    chapter_id: int
    subsection_index: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: int = 0
    is_active: bool

    model_config = {"from_attributes": True}


class StartSessionRequest(BaseModel):
    """Schema for starting a learning session"""
    chapter_id: int
    subsection_index: int = 0


class EndSessionRequest(BaseModel):
    """Schema for ending a learning session"""
    duration_seconds: int


class UpdateSubsectionRequest(BaseModel):
    """Schema for updating current subsection"""
    subsection_index: int


class LearningStatistics(BaseModel):
    """Schema for aggregated learning statistics"""
    total_learning_time_seconds: int = 0
    total_sessions: int = 0
    completed_chapters: int = 0
    in_progress_chapters: int = 0
    total_subsections_completed: int = 0
    current_streak: int = 0
    longest_streak: int = 0


class ActivityResponse(BaseModel):
    """Schema for activity log response"""
    id: str
    activity_type: str
    chapter_id: Optional[int] = None
    subsection_index: Optional[int] = None
    description: str
    extra_data: dict = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}


class ExerciseAnswer(BaseModel):
    """Schema for a single exercise answer"""
    subsection_index: int
    exercise_id: int
    correct_answer_index: int


class ChapterExerciseAnswersResponse(BaseModel):
    """Schema for chapter exercise answers response"""
    chapter_id: int
    answers: list[ExerciseAnswer]


# ========================================
# Trend Schemas
# ========================================

class DailyTrendPoint(BaseModel):
    """Single day data point for trend charts"""
    date: str  # ISO date string YYYY-MM-DD
    count: int = 0


class DailyExercisesTrendResponse(BaseModel):
    """Response for daily exercises trend"""
    trends: list[DailyTrendPoint]


class DailyAccuracyTrendPoint(BaseModel):
    """Single day accuracy data point"""
    date: str
    accuracy: float = 0.0
    total: int = 0
    correct: int = 0


class DailyAccuracyTrendResponse(BaseModel):
    """Response for daily accuracy trend"""
    trends: list[DailyAccuracyTrendPoint]


class DailyTimeTrendPoint(BaseModel):
    """Single day learning time data point"""
    date: str
    minutes: int = 0


class DailyTimeTrendResponse(BaseModel):
    """Response for daily learning time trend"""
    trends: list[DailyTimeTrendPoint]
"""Exercise API Schemas - Question Bank and AI Generation"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


class ExerciseBase(BaseModel):
    """Base exercise schema"""
    type: str = Field(..., description="Type: choice, programming, fill_blank")
    difficulty: int = Field(default=1, ge=1, le=5)
    content: dict
    hints: Optional[list[str]] = None


class ExerciseSummary(BaseModel):
    """Exercise summary"""
    id: int
    chapter_id: int
    source: str = "manual"
    source_id: Optional[str] = None  # Add missing field for consistency
    type: str
    difficulty: int
    content: dict
    hints: Optional[list[str]] = None

    model_config = {"from_attributes": True}


class ExerciseDetail(BaseModel):
    """Exercise detail"""
    id: int
    chapter_id: int
    source: str
    type: str
    difficulty: int
    content: dict
    solution: Optional[dict] = None
    hints: Optional[list[str]] = None
    test_cases: Optional[list] = None

    model_config = {"from_attributes": True}


class ExerciseListResponse(BaseModel):
    """Response for exercise list"""
    exercises: list[ExerciseSummary]
    total: int


class ExerciseGenerateRequest(BaseModel):
    """Request to generate exercises with AI"""
    chapter_id: int = Field(..., description="Chapter to generate exercises for")
    count: int = Field(default=5, ge=1, le=20, description="Number of exercises to generate")
    exercise_type: str = Field(
        default="choice",
        description="Type: choice, programming, fill_blank"
    )
    difficulty: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Difficulty level 1-5"
    )
    topic: Optional[str] = Field(
        default=None,
        description="Specific topic to focus on"
    )


class ExerciseGenerateResponse(BaseModel):
    """Response from AI exercise generation"""
    success: bool
    generated: int
    exercises: list[dict]
    message: str


class ExerciseSubmitRequest(BaseModel):
    """Request to submit an exercise answer"""
    answer: Any = Field(..., description="User's answer")
    language: Optional[str] = Field(
        default=None,
        description="Programming language if applicable"
    )


class ExerciseSubmitResponse(BaseModel):
    """Response from exercise submission"""
    is_correct: bool
    correct_answer: Optional[Any] = None
    explanation: Optional[str] = None
    xp_earned: int = 0
    points: int = 0
    wrong_question_updated: bool = False


class ExerciseVerifyRequest(BaseModel):
    """Request to verify an exercise"""
    verified: bool = Field(default=True, description="Verification status")


class ExerciseVerifyResponse(BaseModel):
    """Response from exercise verification"""
    id: int
    is_verified: bool
    message: str


class ExerciseRecommendRequest(BaseModel):
    """Request for exercise recommendations"""
    limit: int = Field(default=10, ge=1, le=50, description="Max recommendations")
    min_difficulty: int = Field(default=1, ge=1, le=5, description="Min difficulty")
    max_difficulty: int = Field(default=5, ge=1, le=5, description="Max difficulty")
    exclude_completed: bool = Field(default=True, description="Exclude completed exercises")
    chapter_id: Optional[int] = Field(default=None, description="Chapter ID for mastery path")
    learning_path: str = Field(default="mastery", description="mastery or challenge")


class ExerciseRecommendItem(BaseModel):
    """Single recommended exercise"""
    exercise_id: int
    source_id: str
    similarity: float
    difficulty: int
    difficulty_label: str = ""
    type: str
    knowledge_points: list[str]
    title: str
    reason: str = ""  # Human-readable recommendation reason
    matched_weak_points: list[str] = []  # Weak points this exercise addresses


class KnowledgeStateInfo(BaseModel):
    """User's knowledge state information"""
    estimated_level: float
    target_difficulty: int
    target_difficulty_label: str
    total_attempts: int
    accuracy: float


class ExerciseRecommendResponse(BaseModel):
    """Response for exercise recommendations"""
    user_vector_generated: bool
    weak_points: list[str]
    user_weak_point_count: int
    recommendations: list[ExerciseRecommendItem]
    total_candidates: int
    knowledge_state: Optional[KnowledgeStateInfo] = None

"""Course API Schemas"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


class ChapterBase(BaseModel):
    """Base chapter schema"""
    title: str
    description: Optional[str] = None
    order_index: int
    learning_objectives: Optional[Any] = None  # Can be dict or list
    difficulty_tags: Optional[list[str]] = None
    skill_tags: Optional[list[str]] = None
    estimated_minutes: int = 30


class ChapterSummary(ChapterBase):
    """Chapter summary for course listing"""
    id: int
    course_id: int
    is_active: bool = True

    model_config = {"from_attributes": True}


class ChapterDetail(ChapterBase):
    """Chapter detail with exercises"""
    id: int
    course_id: int
    is_active: bool = True
    content: Optional[str] = None

    model_config = {"from_attributes": True}


class ExerciseBase(BaseModel):
    """Base exercise schema"""
    type: str = Field(..., description="Type: choice, programming, fill_blank")
    difficulty: int = Field(default=1, ge=1, le=5)
    content: dict
    hints: Optional[list[str]] = None


class ExerciseSummary(ExerciseBase):
    """Exercise summary"""
    id: int
    chapter_id: int
    source: str = "manual"
    source_id: Optional[str] = None

    model_config = {"from_attributes": True}


class ExerciseDetail(ExerciseSummary):
    """Exercise detail with solution hints"""
    solution: Optional[dict] = None
    test_cases: Optional[list] = None
    common_errors: Optional[list[str]] = None

    model_config = {"from_attributes": True}


class ChapterWithExercises(ChapterBase):
    """Chapter with embedded exercises"""
    id: int
    course_id: int
    exercises: list[ExerciseSummary] = []

    model_config = {"from_attributes": True}


class CourseBase(BaseModel):
    """Base course schema"""
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    difficulty_level: int = Field(default=1, ge=1, le=5)
    icon: Optional[str] = None


class CourseSummary(CourseBase):
    """Course summary for listing"""
    id: int
    is_active: bool
    chapter_count: int = 0

    model_config = {"from_attributes": True}


class CourseDetail(CourseBase):
    """Course detail with chapters"""
    id: int
    is_active: bool
    created_at: datetime
    chapters: list[ChapterSummary] = []

    model_config = {"from_attributes": True}


class CourseListResponse(BaseModel):
    """Response for course list endpoint"""
    courses: list[CourseSummary]
    total: int


class CourseDetailResponse(BaseModel):
    """Response for course detail endpoint"""
    course: CourseDetail
    enrolled: bool = False  # Whether current user is enrolled


class ChapterDetailResponse(BaseModel):
    """Response for chapter detail endpoint"""
    chapter: ChapterDetail
    exercises: list[ExerciseSummary]


# Re-export for convenience
CourseCreate = CourseBase
ChapterCreate = ChapterBase
ExerciseCreate = ExerciseBase

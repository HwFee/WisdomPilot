from typing import Any

from pydantic import BaseModel, Field


class InfiniteSessionStartRequest(BaseModel):
    difficulty_level: int = Field(default=3, ge=1, le=5)
    initial_count: int = Field(default=3, ge=1, le=50)


class ChallengeSessionResponse(BaseModel):
    session_id: str
    difficulty_level: int
    exercises: list[dict[str, Any]]
    time_limit: int
    score_multiplier: float
    status: str


class ChallengeProgressResponse(BaseModel):
    total_exercises: int
    exercises: list[dict[str, Any]]
    correct_count: int
    completed_count: int
    total_stars_earned: int
    current_index: int


class SaveCodeRequest(BaseModel):
    exercise_id: int
    code: str
    language: str


class SaveCodeResponse(BaseModel):
    success: bool


class SwitchExerciseRequest(BaseModel):
    target_index: int


class SwitchExerciseResponse(BaseModel):
    exercise_id: int
    saved_code: str
    current_language: str
    is_completed: bool
    is_correct: bool
    exercise: dict[str, Any]


class AppendExercisesRequest(BaseModel):
    count: int = Field(default=5, ge=1, le=20)
    difficulty_level: int | None = Field(
        default=None,
        ge=1,
        le=8,
        description="难度等级，不传则从用户现有题目推断",
    )


class AppendExercisesResponse(BaseModel):
    new_exercise_ids: list[int]
    count: int


class ExitSaveRequest(BaseModel):
    current_exercise_id: int
    current_code: str
    current_language: str


class ExitChallengeResponse(BaseModel):
    success: bool
    message: str


class ChallengeExerciseDetailResponse(BaseModel):
    exercise: dict[str, Any]
    exercise_index: int
    is_unlocked: bool
    is_completed: bool
    is_correct: bool
    saved_code: str
    current_language: str
    total_exercises: int


class RecentArenaExercise(BaseModel):
    exercise_id: int
    title: str
    is_correct: bool
    difficulty: int

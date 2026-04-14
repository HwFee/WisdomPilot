"""Exercise API Router - Question Bank and AI Generation"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.models.exercise import Exercise
from app.models.chapter import Chapter
from app.models.user_weak_point import UserWeakPoint
from app.schemas.exercise import (
    ExerciseListResponse,
    ExerciseGenerateRequest,
    ExerciseGenerateResponse,
    ExerciseSubmitRequest,
    ExerciseSubmitResponse,
    ExerciseVerifyRequest,
    ExerciseVerifyResponse,
    ExerciseSummary,
    ExerciseRecommendRequest,
    ExerciseRecommendResponse,
    ExerciseRecommendItem,
)
from app.services.exercise import exercise_service
from app.services.vector_match import VectorMatchService, get_vector_match_service
from app.utils.deps import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/api/exercises", tags=["exercises"])

db_dependency = Annotated[AsyncSession, Depends(get_db)]
auth_dependency = Annotated[User, Depends(get_current_active_user)]
admin_dependency = Annotated[User, Depends(get_current_admin_user)]


@router.get("/chapter/{chapter_id}", response_model=ExerciseListResponse)
async def get_chapter_exercises(
    chapter_id: int,
    db: db_dependency,
    subsection: Optional[int] = Query(default=None, description="Subsection index"),
    difficulty: Optional[int] = Query(default=None, ge=1, le=5, description="Filter by difficulty"),
    limit: int = Query(default=50, ge=1, le=100),
):
    """
    Get exercises for a chapter.

    Public endpoint - no authentication required.
    """
    query = select(Exercise).where(
        Exercise.chapter_id == chapter_id,
        Exercise.is_verified == True,
    )

    if subsection is not None:
        # Filter by subsection using content metadata
        pass  # subsection filtering would need content.subsection_index

    if difficulty is not None:
        query = query.where(Exercise.difficulty == difficulty)

    query = query.order_by(Exercise.difficulty, Exercise.id).limit(limit)

    result = await db.execute(query)
    exercises = list(result.scalars().all())

    return ExerciseListResponse(
        exercises=[ExerciseSummary.model_validate(e) for e in exercises],
        total=len(exercises),
    )


@router.get("/detail/{exercise_id}")
async def get_exercise_detail(
    exercise_id: int,
    db: db_dependency,
):
    """
    Get single exercise details.

    Public endpoint - no authentication required.
    """
    result = await db.execute(
        select(Exercise).where(Exercise.id == exercise_id)
    )
    exercise = result.scalar_one_or_none()

    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exercise {exercise_id} not found",
        )

    return {
        "exercise": ExerciseSummary.model_validate(exercise)
    }


# Keep old route for backward compatibility
@router.get("/{chapter_id}", response_model=ExerciseListResponse)
async def get_chapter_exercises_compat(
    chapter_id: int,
    db: db_dependency,
    subsection: Optional[int] = Query(default=None, description="Subsection index"),
    difficulty: Optional[int] = Query(default=None, ge=1, le=5, description="Filter by difficulty"),
    limit: int = Query(default=50, ge=1, le=100),
):
    """
    Get exercises for a chapter.

    Public endpoint - no authentication required.
    """
    query = select(Exercise).where(
        Exercise.chapter_id == chapter_id,
        Exercise.is_verified == True,
    )

    if subsection is not None:
        # Filter by subsection using content metadata
        pass  # subsection filtering would need content.subsection_index

    if difficulty is not None:
        query = query.where(Exercise.difficulty == difficulty)

    query = query.order_by(Exercise.difficulty, Exercise.id).limit(limit)

    result = await db.execute(query)
    exercises = list(result.scalars().all())

    return ExerciseListResponse(
        exercises=[ExerciseSummary.model_validate(e) for e in exercises],
        total=len(exercises),
    )


@router.post("/generate", response_model=ExerciseGenerateResponse)
async def generate_exercises(
    request: ExerciseGenerateRequest,
    db: db_dependency,
    current_user: admin_dependency,
):
    """
    Generate exercises using AI.

    Requires admin authentication.
    """
    try:
        result = await exercise_service.generate_exercises(
            db=db,
            chapter_id=request.chapter_id,
            count=request.count,
            exercise_type=request.exercise_type,
            difficulty=request.difficulty,
            topic=request.topic,
        )
        return ExerciseGenerateResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成失败: {str(e)}",
        )


@router.post("/{exercise_id}/verify", response_model=ExerciseVerifyResponse)
async def verify_exercise(
    exercise_id: int,
    request: ExerciseVerifyRequest,
    db: db_dependency,
    current_user: admin_dependency,
):
    """
    Verify or unverify an exercise.

    Requires admin authentication.
    """
    try:
        exercise = await exercise_service.verify_exercise(
            db=db,
            exercise_id=exercise_id,
            verified=request.verified,
        )
        return ExerciseVerifyResponse(
            id=exercise.id,
            is_verified=exercise.is_verified,
            message="Exercise verified successfully" if exercise.is_verified else "Exercise unverified",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/{exercise_id}/submit", response_model=ExerciseSubmitResponse)
async def submit_exercise_answer(
    exercise_id: int,
    request: ExerciseSubmitRequest,
    db: db_dependency,
    current_user: auth_dependency,
):
    """
    Submit answer for an exercise and get feedback.

    Requires authentication.
    """
    exercise = await db.execute(
        select(Exercise).where(Exercise.id == exercise_id)
    )
    exercise = exercise.scalar_one_or_none()

    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found",
        )

    result = await exercise_service.check_answer(
        db=db,
        user=current_user,
        exercise=exercise,
        user_answer=request.answer,
    )
    return ExerciseSubmitResponse(**result)


@router.post("/recommend", response_model=ExerciseRecommendResponse)
async def recommend_exercises(
    request: ExerciseRecommendRequest,
    db: db_dependency,
    current_user: auth_dependency,
):
    """
    Get personalized exercise recommendations using adaptive learning algorithm.

    Uses:
    - Knowledge Tracing to estimate user's knowledge state
    - Zone of Proximal Development (ZPD) for difficulty matching
    - Diversity filtering to ensure variety
    - Chapter context for mastery path learning

    Learning Paths:
    - mastery: Chapter-based learning, recommends exercises from specified chapter
    - challenge: Difficulty-based learning, recommends exercises across chapters

    Requires authentication.
    """
    from app.services.adaptive_recommendation import get_adaptive_recommendation_service

    service = get_adaptive_recommendation_service(db)

    result = await service.get_recommendations(
        user=current_user,
        limit=request.limit,
        min_difficulty=request.min_difficulty,
        max_difficulty=request.max_difficulty,
        chapter_id=request.chapter_id,
        learning_path=request.learning_path,
    )

    # Convert to response format
    recommendations = [
        ExerciseRecommendItem(**r) for r in result["recommendations"]
    ]

    return ExerciseRecommendResponse(
        user_vector_generated=result["user_vector_generated"],
        weak_points=result["weak_points"],
        user_weak_point_count=result["user_weak_point_count"],
        recommendations=recommendations,
        total_candidates=result["total_candidates"],
        knowledge_state=result.get("knowledge_state"),
    )

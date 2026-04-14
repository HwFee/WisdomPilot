"""Review API Router - 复习系统路由"""

from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.exercise import Exercise
from app.models.user_weak_point import UserWeakPoint
from app.models.spaced_repetition import SpacedRepetition
from app.schemas.review import (
    ReviewQueueResponse,
    ReviewQueueItem,
    SpacedRepetitionResponse,
    CompleteReviewRequest,
    CompleteReviewResponse,
    WeakPointListResponse,
    WeakPointResponse,
    TargetPracticeRequest,
    TargetPracticeResponse,
    ReviewStatsResponse,
)

router = APIRouter(prefix="/api/review", tags=["review"])

db_dependency = Annotated[AsyncSession, Depends(get_db)]

# Import the actual dependency function
from app.utils.deps import get_current_active_user as _get_current_active_user

auth_dependency = Annotated[User, Depends(_get_current_active_user)]


@router.get("/queue", response_model=ReviewQueueResponse)
async def get_review_queue(
    db: db_dependency,
    user: auth_dependency,
    limit: int = 20
):
    """
    Get the review queue for the current user.

    Returns exercises due for review, prioritized by:
    1. Overdue items
    2. Weak point priority
    3. Difficulty
    """
    from app.utils.time import utc_now

    now = utc_now()

    # Get all due repetitions
    result = await db.execute(
        select(SpacedRepetition)
        .where(
            SpacedRepetition.user_id == user.id,
            SpacedRepetition.next_review_at <= now
        )
        .order_by(SpacedRepetition.next_review_at)
        .limit(limit)
    )
    due_repetitions = result.scalars().all()

    # Get exercise details
    exercise_ids = [r.exercise_id for r in due_repetitions]
    exercises_result = await db.execute(
        select(Exercise).where(Exercise.id.in_(exercise_ids))
    )
    exercises = {e.id: e for e in exercises_result.scalars().all()}

    # Get weak points for priority calculation
    weak_result = await db.execute(
        select(UserWeakPoint).where(UserWeakPoint.user_id == user.id)
    )
    weak_points = {wp.knowledge_point: wp for wp in weak_result.scalars().all()}

    # Build queue items
    items = []
    for rep in due_repetitions:
        exercise = exercises.get(rep.exercise_id)
        if not exercise:
            continue

        # Calculate priority
        priority = 0.0
        # Overdue factor
        days_overdue = (now - rep.next_review_at).days
        priority += days_overdue * 0.5
        # Weak point factor
        for kp in exercise.knowledge_points:
            if kp in weak_points:
                priority += weak_points[kp].weakness_score * 2

        items.append(ReviewQueueItem(
            repetition=SpacedRepetitionResponse.model_validate(rep),
            exercise_id=exercise.id,
            exercise_type=exercise.type,
            exercise_difficulty=exercise.difficulty,
            knowledge_points=exercise.knowledge_points,
            stage_id=rep.stage_id,
            priority=priority
        ))

    # Sort by priority (higher first)
    items.sort(key=lambda x: x.priority, reverse=True)

    # Get total counts
    total_result = await db.execute(
        select(SpacedRepetition)
        .where(SpacedRepetition.user_id == user.id)
    )
    all_repetitions = total_result.scalars().all()
    total_scheduled = len(all_repetitions)
    total_due = len([r for r in all_repetitions if r.next_review_at <= now])

    return ReviewQueueResponse(
        items=items,
        total_due=total_due,
        total_scheduled=total_scheduled
    )


@router.post("/complete/{exercise_id}", response_model=CompleteReviewResponse)
async def complete_review(
    exercise_id: int,
    request: CompleteReviewRequest,
    db: db_dependency,
    user: auth_dependency
):
    """
    Complete a review for an exercise.

    Updates spaced repetition schedule and weak point tracking.
    """
    from app.utils.time import utc_now

    # Get repetition record
    result = await db.execute(
        select(SpacedRepetition).where(
            SpacedRepetition.user_id == user.id,
            SpacedRepetition.exercise_id == exercise_id
        )
    )
    repetition = result.scalar_one_or_none()

    if not repetition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repetition record not found"
        )

    # Update spaced repetition
    repetition.calculate_next_review(request.quality)

    # Get exercise for knowledge points
    exercise_result = await db.execute(
        select(Exercise).where(Exercise.id == exercise_id)
    )
    exercise = exercise_result.scalar_one_or_none()

    weak_point_updated = False
    mastery_change = 0

    if exercise:
        # Update weak points
        for kp in exercise.knowledge_points:
            wp_result = await db.execute(
                select(UserWeakPoint).where(
                    UserWeakPoint.user_id == user.id,
                    UserWeakPoint.course_id == exercise.chapter.course_id
                    if hasattr(exercise, 'chapter') and exercise.chapter else 0,
                    UserWeakPoint.knowledge_point == kp
                )
            )
            weak_point = wp_result.scalar_one_or_none()

            if weak_point:
                old_mastery = weak_point.mastery_level
                weak_point.record_review(request.success)
                weak_point_updated = True
                mastery_change += weak_point.mastery_level - old_mastery

    await db.flush()

    return CompleteReviewResponse(
        repetition=SpacedRepetitionResponse.model_validate(repetition),
        weak_point_updated=weak_point_updated,
        mastery_change=mastery_change,
        message="Review completed successfully"
    )


@router.get("/weak-points", response_model=WeakPointListResponse)
async def get_weak_points(
    db: db_dependency,
    user: auth_dependency,
    course_id: int = None,
    limit: int = 20
):
    """
    Get list of user's weak knowledge points.

    Optionally filtered by course.
    """
    query = select(UserWeakPoint).where(UserWeakPoint.user_id == user.id)

    if course_id:
        query = query.where(UserWeakPoint.course_id == course_id)

    query = query.order_by(UserWeakPoint.mastery_level, UserWeakPoint.error_count.desc()).limit(limit)

    result = await db.execute(query)
    weak_points = result.scalars().all()

    return WeakPointListResponse(
        weak_points=[WeakPointResponse.model_validate(wp) for wp in weak_points],
        total=len(weak_points)
    )


@router.post("/weak-points/target", response_model=TargetPracticeResponse)
async def target_weak_points(
    request: TargetPracticeRequest,
    db: db_dependency,
    user: auth_dependency
):
    """
    Get exercises for targeted practice on weak points.

    Returns exercises that target the specified weak knowledge points.
    """
    # Get weak points
    query = select(UserWeakPoint).where(UserWeakPoint.user_id == user.id)

    if request.course_id:
        query = query.where(UserWeakPoint.course_id == request.course_id)

    if request.knowledge_points:
        query = query.where(UserWeakPoint.knowledge_point.in_(request.knowledge_points))

    query = query.order_by(UserWeakPoint.mastery_level).limit(10)

    result = await db.execute(query)
    weak_points = result.scalars().all()

    if not weak_points:
        return TargetPracticeResponse(
            exercises=[],
            weak_points=[],
            total=0
        )

    # Find exercises targeting these knowledge points
    kp_list = [wp.knowledge_point for wp in weak_points]

    # Use JSON query to find exercises with matching knowledge points
    exercise_result = await db.execute(
        select(Exercise).limit(request.limit)
    )
    all_exercises = exercise_result.scalars().all()

    # Filter by knowledge points (SQLite JSON query is limited, filter in Python)
    exercises = []
    for ex in all_exercises:
        if any(kp in ex.knowledge_points for kp in kp_list):
            exercises.append({
                "id": ex.id,
                "type": ex.type,
                "difficulty": ex.difficulty,
                "content": ex.content,
                "knowledge_points": ex.knowledge_points
            })
            if len(exercises) >= request.limit:
                break

    return TargetPracticeResponse(
        exercises=exercises,
        weak_points=[WeakPointResponse.model_validate(wp) for wp in weak_points],
        total=len(exercises)
    )


@router.get("/stats", response_model=ReviewStatsResponse)
async def get_review_stats(
    db: db_dependency,
    user: auth_dependency
):
    """
    Get review statistics for the current user.
    """
    from app.utils.time import utc_now

    now = utc_now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Get all repetitions
    result = await db.execute(
        select(SpacedRepetition).where(SpacedRepetition.user_id == user.id)
    )
    all_repetitions = result.scalars().all()

    # Calculate stats
    total_due = len([r for r in all_repetitions if r.next_review_at <= now])
    total_scheduled = len(all_repetitions)

    # Reviewed today
    reviewed_today = len([
        r for r in all_repetitions
        if r.last_review_at and r.last_review_at >= today_start
    ])

    # Get weak points count
    weak_result = await db.execute(
        select(UserWeakPoint).where(UserWeakPoint.user_id == user.id)
    )
    weak_points = weak_result.scalars().all()

    # Mastery distribution
    mastery_dist = {}
    for wp in weak_points:
        level = wp.mastery_level
        mastery_dist[str(level)] = mastery_dist.get(str(level), 0) + 1

    return ReviewStatsResponse(
        total_due=total_due,
        total_scheduled=total_scheduled,
        reviewed_today=reviewed_today,
        streak_days=user.current_streak or 0,
        weak_points_count=len(weak_points),
        mastery_distribution=mastery_dist
    )

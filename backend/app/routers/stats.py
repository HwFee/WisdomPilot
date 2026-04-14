"""Router for learning statistics endpoints"""

from datetime import datetime, date
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.utils.deps import get_current_active_user
from app.models.user import User
from app.schemas.stats import (
    ChapterProgressResponse,
    UpdateProgressRequest,
    LearningSessionResponse,
    StartSessionRequest,
    EndSessionRequest,
    UpdateSubsectionRequest,
    LearningStatistics,
    ActivityResponse,
    ChapterExerciseAnswersResponse,
    DailyExercisesTrendResponse,
    DailyAccuracyTrendResponse,
    DailyTimeTrendResponse,
)
from app.services.stats import StatsService
from app.services.stats_service import stats_service

router = APIRouter(prefix="/api/stats", tags=["stats"])


async def get_stats_service(db: AsyncSession = Depends(get_db)) -> StatsService:
    return StatsService(db)


@router.get("/progress", response_model=list[ChapterProgressResponse])
async def get_user_progress(
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: StatsService = Depends(get_stats_service),
):
    """Get all chapter progress for current user"""
    return await service.get_user_progress(current_user.id)


@router.get("/progress/{chapter_id}", response_model=ChapterProgressResponse)
async def get_chapter_progress(
    chapter_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: StatsService = Depends(get_stats_service),
):
    """Get progress for a specific chapter"""
    progress = await service.get_chapter_progress(current_user.id, chapter_id)
    if progress is None:
        # Return default progress if none exists
        progress = await service.get_or_create_progress(current_user.id, chapter_id)
    return progress


@router.put("/progress/{chapter_id}", response_model=ChapterProgressResponse)
async def update_chapter_progress(
    chapter_id: int,
    data: UpdateProgressRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: StatsService = Depends(get_stats_service),
):
    """Update chapter progress"""
    if chapter_id < 1 or chapter_id > 12:
        raise HTTPException(status_code=400, detail="Invalid chapter ID")

    return await service.update_chapter_progress(current_user.id, chapter_id, data)


@router.post("/sessions/start", response_model=LearningSessionResponse)
async def start_session(
    data: StartSessionRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: StatsService = Depends(get_stats_service),
):
    """Start a new learning session"""
    return await service.start_session(current_user.id, data)


@router.post("/sessions/end", response_model=LearningSessionResponse)
async def end_session(
    data: EndSessionRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: StatsService = Depends(get_stats_service),
):
    """End current active session"""
    active_session = await service.get_active_session(current_user.id)
    if active_session is None:
        raise HTTPException(status_code=404, detail="No active session found")

    return await service.end_session(current_user.id, active_session.id, data)


@router.get("/sessions/active", response_model=LearningSessionResponse | None)
async def get_active_session(
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: StatsService = Depends(get_stats_service),
):
    """Get current active session"""
    return await service.get_active_session(current_user.id)


@router.post("/sessions/subsection", response_model=LearningSessionResponse)
async def update_session_subsection(
    data: UpdateSubsectionRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: StatsService = Depends(get_stats_service),
):
    """Update the current session's subsection index"""
    active_session = await service.get_active_session(current_user.id)
    if active_session is None:
        raise HTTPException(status_code=404, detail="No active session found")

    # Log subsection changed activity
    await service.log_activity(
        user_id=current_user.id,
        activity_type="subsection_changed",
        chapter_id=active_session.chapter_id,
        subsection_index=data.subsection_index,
        description=f"学习小节 {active_session.chapter_id}-{data.subsection_index}",
    )

    # Update the session's subsection
    updated_session = await service.update_session_subsection(
        current_user.id, active_session.id, data.subsection_index
    )
    return updated_session


@router.get("/sessions", response_model=list[LearningSessionResponse])
async def get_sessions(
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: StatsService = Depends(get_stats_service),
    limit: int = 50,
):
    """Get user's learning sessions"""
    return await service.get_user_sessions(current_user.id, limit)


@router.get("/statistics", response_model=LearningStatistics)
async def get_statistics(
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: StatsService = Depends(get_stats_service),
):
    """Get aggregated learning statistics"""
    return await service.get_statistics(current_user.id)


@router.get("/activities", response_model=list[ActivityResponse])
async def get_activities(
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: StatsService = Depends(get_stats_service),
    limit: int = 20,
):
    """Get recent activity history"""
    return await service.get_activities(current_user.id, limit)


@router.get("/exercises/answers/{chapter_id}", response_model=ChapterExerciseAnswersResponse)
async def get_chapter_exercise_answers(
    chapter_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: StatsService = Depends(get_stats_service),
):
    """Get exercise answers for a chapter (for grading choice questions)"""
    answers = await service.get_chapter_exercise_answers(chapter_id)
    return ChapterExerciseAnswersResponse(chapter_id=chapter_id, answers=answers)


# Additional stats endpoints using the new stats_service
db_dependency = Annotated[AsyncSession, Depends(get_db)]
auth_dependency = Annotated[User, Depends(get_current_active_user)]


@router.get("/user/me")
async def get_my_stats(
    db: db_dependency,
    current_user: auth_dependency,
):
    """
    Get current user's learning statistics.

    Requires authentication.
    """
    return await stats_service.get_user_stats(db, current_user.id)


@router.get("/courses/{course_id}")
async def get_course_stats(
    db: db_dependency,
    course_id: int = Path(gt=0, description="Course ID"),
):
    """
    Get statistics for a specific course.

    Public endpoint - no authentication required.
    """
    return await stats_service.get_course_stats(db, course_id)


@router.get("/leaderboard")
async def get_leaderboard(
    db: db_dependency,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """
    Get XP-based leaderboard.

    Public endpoint - no authentication required.
    """
    return await stats_service.get_leaderboard(db, limit=limit, offset=offset)


@router.get("/activity/me")
async def get_my_recent_activity(
    db: db_dependency,
    current_user: auth_dependency,
    limit: int = Query(default=10, ge=1, le=50),
):
    """
    Get recent activity for current user.

    Requires authentication.
    """
    return await stats_service.get_recent_activity(db, current_user.id, limit=limit)


# ========================================
# Trend Endpoints
# ========================================

@router.get("/trends/exercises", response_model=DailyExercisesTrendResponse)
async def get_exercises_trend(
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: StatsService = Depends(get_stats_service),
    days: int = Query(default=7, ge=1, le=30),
):
    """Get daily exercises count trend for the past N days"""
    trends = await service.get_daily_exercises_trend(current_user.id, days)
    return DailyExercisesTrendResponse(trends=trends)


@router.get("/trends/accuracy", response_model=DailyAccuracyTrendResponse)
async def get_accuracy_trend(
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: StatsService = Depends(get_stats_service),
    days: int = Query(default=7, ge=1, le=30),
):
    """Get daily accuracy rate trend for the past N days"""
    trends = await service.get_daily_accuracy_trend(current_user.id, days)
    return DailyAccuracyTrendResponse(trends=trends)


@router.get("/trends/time", response_model=DailyTimeTrendResponse)
async def get_time_trend(
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: StatsService = Depends(get_stats_service),
    days: int = Query(default=7, ge=1, le=30),
):
    """Get daily learning time trend for the past N days"""
    trends = await service.get_daily_time_trend(current_user.id, days)
    return DailyTimeTrendResponse(trends=trends)


# ========================================
# Today Stats API
# ========================================

@router.get("/today")
async def get_today_stats(
    db: db_dependency,
    current_user: auth_dependency,
):
    """
    Get today's learning statistics.

    Returns:
    - exercises: Number of exercises completed today (deduplicated)
    - correct: Number of correct answers today (based on latest attempt)
    - accuracy: Accuracy rate today (percentage)
    - time_minutes: Total learning time today in minutes
    """
    from datetime import datetime, timezone
    from app.models.stats import ActivityLog, LearningSession

    # Use UTC time for consistency with database storage
    utc_now = datetime.now(timezone.utc)
    today_start = utc_now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Get today's exercises from activity log
    exercises_result = await db.execute(
        select(ActivityLog)
        .where(
            ActivityLog.user_id == current_user.id,
            ActivityLog.created_at >= today_start,
            ActivityLog.activity_type == 'exercise_complete'
        )
        .order_by(ActivityLog.created_at.desc())  # 按时间倒序，最新的在前面
    )
    today_activities = exercises_result.scalars().all()

    # 去重：每道题只取最新的一次状态
    seen_exercises = set()
    unique_exercises = []
    for a in today_activities:
        ex_id = a.extra_data.get('exercise_id')
        if ex_id and ex_id not in seen_exercises:
            seen_exercises.add(ex_id)
            unique_exercises.append(a)

    # Calculate stats - deduplicated count, correct based on latest attempt
    exercises = len(unique_exercises)
    correct = sum(1 for a in unique_exercises if a.extra_data.get('is_correct', False))
    accuracy = round((correct / exercises) * 100, 1) if exercises > 0 else 0.0

    # Get learning time from sessions
    sessions_result = await db.execute(
        select(LearningSession)
        .where(
            LearningSession.user_id == current_user.id,
            LearningSession.started_at >= today_start
        )
    )
    today_sessions = sessions_result.scalars().all()
    time_seconds = sum(s.duration_seconds or 0 for s in today_sessions)
    time_minutes = round(time_seconds / 60, 1)

    return {
        "exercises": exercises,
        "correct": correct,
        "accuracy": accuracy,
        "time_minutes": time_minutes,
    }

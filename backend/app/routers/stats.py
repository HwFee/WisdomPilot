"""Router for learning statistics endpoints"""

from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.stats import (
    ActivityResponse,
    ChapterExerciseAnswersResponse,
    ChapterProgressResponse,
    DailyAccuracyTrendResponse,
    DailyExercisesTrendResponse,
    DailyTimeTrendResponse,
    EndSessionRequest,
    LearningSessionResponse,
    LearningStatistics,
    StartSessionRequest,
    UpdateProgressRequest,
    UpdateSubsectionRequest,
)
from app.services.stats import StatsService
from app.services.stats_service import stats_service
from app.utils.deps import get_current_active_user

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
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"[学习时长-API] ========== POST /sessions/start ==========")
    logger.info(f"[学习时长-API] user_id: {current_user.id}")
    logger.info(f"[学习时长-API] chapter_id: {data.chapter_id}")
    logger.info(f"[学习时长-API] subsection_index: {data.subsection_index}")

    result = await service.start_session(current_user.id, data)
    logger.info(f"[学习时长-API] 会话已创建, session_id: {result.id}")
    return result


@router.post("/sessions/end", response_model=LearningSessionResponse)
async def end_session(
    data: EndSessionRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: StatsService = Depends(get_stats_service),
):
    """End current active session.
    If no active session found and chapter_id is provided, creates and immediately
    completes a session to preserve the recorded time.
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"[学习时长-API] ========== POST /sessions/end ==========")
    logger.info(f"[学习时长-API] user_id: {current_user.id}")
    logger.info(f"[学习时长-API] duration_seconds: {data.duration_seconds}")
    logger.info(f"[学习时长-API] chapter_id: {data.chapter_id}")

    active_session = await service.get_active_session(current_user.id)
    logger.info(f"[学习时长-API] active_session: {active_session.id if active_session else None}")

    if active_session is None:
        # No active session found — create a completed one to preserve the time
        logger.info("[学习时长-API] 没有找到活跃会话，创建已完成会话")
        chapter_id = data.chapter_id or 0
        result = await service.create_completed_session(
            current_user.id, chapter_id, data.duration_seconds
        )
    else:
        logger.info(f"[学习时长-API] 找到活跃会话 {active_session.id}，结束它")
        result = await service.end_session(current_user.id, active_session.id, data)

    logger.info(f"[学习时长-API] 会话结束完成, session_id: {result.id if result else None}")
    return result


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


@router.get(
    "/exercises/answers/{chapter_id}", response_model=ChapterExerciseAnswersResponse
)
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
    - exercises: Number of challenge-path exercises completed today
    - correct: Number of correct challenge-path answers today
    - accuracy: Challenge-path accuracy rate today (percentage)
    - time_minutes: Total learning time today in minutes across all paths
    """
    from datetime import datetime, timezone, timedelta
    import logging

    from app.models.stats import ActivityLog, LearningSession

    logger = logging.getLogger(__name__)

    # 使用北京时间 (UTC+8) 计算今天的起始时间
    # 用户在中国，所以"今天"应该按北京时区来计算
    beijing_tz = timezone(timedelta(hours=8))
    beijing_now = datetime.now(beijing_tz)
    # 北京时间的今天零点
    beijing_today_start = beijing_now.replace(hour=0, minute=0, second=0, microsecond=0)
    # 转换为 UTC 时间用于数据库查询
    today_start_utc = beijing_today_start.astimezone(timezone.utc)

    logger.info(f"[学习时长-Today] ========== 查询今日统计 ==========")
    logger.info(f"[学习时长-Today] user_id: {current_user.id}")
    logger.info(f"[学习时长-Today] 当前北京时间: {beijing_now}")
    logger.info(f"[学习时长-Today] 北京今天零点: {beijing_today_start}")
    logger.info(f"[学习时长-Today] 转换为UTC: {today_start_utc}")

    # Get today's exercise activities (using Beijing timezone adjusted start time)
    exercises_result = await db.execute(
        select(ActivityLog)
        .where(
            ActivityLog.user_id == current_user.id,
            ActivityLog.created_at >= today_start_utc,
            ActivityLog.activity_type == "exercise_complete",
        )
        .order_by(ActivityLog.created_at.desc())
    )
    today_activities = exercises_result.scalars().all()
    logger.info(f"[学习时长-Today] 今日活动记录数: {len(today_activities)}")

    # Only count challenge-path exercises here.
    # Rules:
    # - Explicit mastery logs are excluded
    # - Explicit challenge logs are included
    # - Legacy logs without learning_path are treated as challenge logs
    challenge_activities = [
        a
        for a in today_activities
        if (a.extra_data or {}).get("learning_path") != "mastery"
    ]

    per_exercise_activities = [
        a for a in challenge_activities if (a.extra_data or {}).get("exercise_id")
    ]
    aggregated_activities = [
        a for a in challenge_activities if not (a.extra_data or {}).get("exercise_id")
    ]

    exercises = 0
    correct = 0

    if per_exercise_activities:
        seen_exercises = set()
        for activity in per_exercise_activities:
            exercise_id = (activity.extra_data or {}).get("exercise_id")
            if exercise_id in seen_exercises:
                continue
            seen_exercises.add(exercise_id)
            exercises += 1
            if (activity.extra_data or {}).get("is_correct", False):
                correct += 1

    if aggregated_activities:
        exercises += sum(
            (a.extra_data or {}).get("exercises_completed", 1)
            for a in aggregated_activities
        )
        correct += sum(
            (a.extra_data or {}).get(
                "exercises_correct",
                1 if (a.extra_data or {}).get("is_correct", False) else 0,
            )
            for a in aggregated_activities
        )

    accuracy = round((correct / exercises) * 100, 1) if exercises > 0 else 0.0

    # Get total learning time from all sessions across both paths
    sessions_result = await db.execute(
        select(LearningSession).where(
            LearningSession.user_id == current_user.id,
            LearningSession.started_at >= today_start_utc,
        )
    )
    today_sessions = sessions_result.scalars().all()
    logger.info(f"[学习时长-Today] 今日会话记录数: {len(today_sessions)}")

    for i, s in enumerate(today_sessions):
        logger.info(f"[学习时长-Today]   会话 {i+1}: id={s.id}, duration={s.duration_seconds}秒, started_at={s.started_at}, ended_at={s.ended_at}, is_active={s.is_active}")

    time_seconds = sum(s.duration_seconds or 0 for s in today_sessions)
    time_minutes = round(time_seconds / 60, 1)

    logger.info(f"[学习时长-Today] ========== 结果 ==========")
    logger.info(f"[学习时长-Today] exercises: {exercises}")
    logger.info(f"[学习时长-Today] correct: {correct}")
    logger.info(f"[学习时长-Today] accuracy: {accuracy}%")
    logger.info(f"[学习时长-Today] time_seconds: {time_seconds}")
    logger.info(f"[学习时长-Today] time_minutes: {time_minutes}")

    return {
        "exercises": exercises,
        "correct": correct,
        "accuracy": accuracy,
        "time_minutes": time_minutes,
    }

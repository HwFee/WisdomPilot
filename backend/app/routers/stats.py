"""Router for learning statistics endpoints"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

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
)
from app.services.stats import StatsService

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
    # Log chapter started activity with subsection_index
    await service.log_activity(
        user_id=current_user.id,
        activity_type="chapter_started",
        chapter_id=data.chapter_id,
        subsection_index=data.subsection_index,
        description=f"开始学习章节 {data.chapter_id}",
    )

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

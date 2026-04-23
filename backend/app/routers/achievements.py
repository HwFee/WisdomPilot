"""Achievement API Router"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.achievement import achievement_service
from app.schemas.achievement import (
    AchievementListResponse,
    AchievementSummary,
    AchievementWithEarnedResponse,
    AchievementWithEarned,
    UserAchievementsResponse,
    UserAchievementDetail,
    UserRankResponse,
)
from app.utils.deps import get_current_active_user
import logging

router = APIRouter(prefix="/api/achievements", tags=["achievements"])

db_dependency = Annotated[AsyncSession, Depends(get_db)]
auth_dependency = Annotated[User, Depends(get_current_active_user)]


@router.get("", response_model=AchievementListResponse)
async def get_achievements(db: db_dependency):
    """
    Get all active achievements.

    Public endpoint - no authentication required.
    """
    achievements = await achievement_service.get_active_achievements(db)
    return AchievementListResponse(
        achievements=[AchievementSummary.model_validate(a) for a in achievements],
        total=len(achievements),
    )


@router.get("/me", response_model=AchievementWithEarnedResponse)
async def get_my_achievements(
    db: db_dependency,
    current_user: auth_dependency,
):
    """
    Get current user's achievements with earned status.

    Requires authentication.
    """
    achievements = await achievement_service.get_active_achievements(db)
    user_achievements = await achievement_service.get_user_achievements(
        db, current_user.id
    )
    earned_map = {ua.achievement_id: ua for ua in user_achievements}

    result = []
    earned_count = 0
    for ach in achievements:
        earned_ua = earned_map.get(ach.id)
        if earned_ua:
            earned_count += 1
            result.append(
                AchievementWithEarned(
                    id=ach.id,
                    code=ach.code,
                    title=ach.title,
                    description=ach.description,
                    icon=ach.icon,
                    type=ach.type,
                    category=ach.category,
                    xp_reward=ach.xp_reward,
                    quota_reward=ach.quota_reward,
                    requirements=ach.requirements,
                    is_secret=ach.is_secret,
                    difficulty=ach.difficulty,
                    is_active=ach.is_active,
                    display_order=ach.display_order,
                    earned=True,
                    earned_at=earned_ua.earned_at,
                    progress=earned_ua.progress,
                )
            )
        else:
            # Don't show secret achievements if not earned
            if ach.is_secret:
                continue
            result.append(
                AchievementWithEarned(
                    id=ach.id,
                    code=ach.code,
                    title=ach.title,
                    description=ach.description,
                    icon=ach.icon,
                    type=ach.type,
                    category=ach.category,
                    xp_reward=ach.xp_reward,
                    quota_reward=ach.quota_reward,
                    requirements=ach.requirements,
                    is_secret=ach.is_secret,
                    difficulty=ach.difficulty,
                    is_active=ach.is_active,
                    display_order=ach.display_order,
                    earned=False,
                    earned_at=None,
                    progress=0,
                )
            )

    return AchievementWithEarnedResponse(
        achievements=result,
        total=len(result),
        earned_count=earned_count,
    )


@router.get("/earned", response_model=UserAchievementsResponse)
async def get_earned_achievements(
    db: db_dependency,
    current_user: auth_dependency,
):
    """
    Get achievements earned by current user.

    Requires authentication.
    """
    user_achievements = await achievement_service.get_earned_achievements(
        db, current_user.id
    )

    details = []
    for ua in user_achievements:
        if ua.achievement:
            details.append(
                UserAchievementDetail(
                    id=ua.id,
                    user_id=ua.user_id,
                    achievement_id=ua.achievement_id,
                    earned_at=ua.earned_at,
                    progress=ua.progress,
                    is_notified=ua.is_notified,
                    achievement=ua.achievement,
                )
            )

    return UserAchievementsResponse(
        achievements=details,
        total=len(details),
        earned_count=len(details),
    )


@router.get("/leaderboard")
async def get_leaderboard(
    db: db_dependency,
    limit: int = Query(default=10, ge=1, le=100),
    current_user: auth_dependency = None,
):
    """
    Get leaderboard with top users by XP.

    Returns array of UserRankResponse for frontend compatibility.
    Public endpoint - authentication optional but helps track user's position.
    """
    from app.services.stats_service import stats_service

    leaderboard = await stats_service.get_leaderboard(db, limit=limit, offset=0)

    return leaderboard  # Return array directly for frontend compatibility


@router.get("/rank", response_model=UserRankResponse)
async def get_my_rank(
    db: db_dependency,
    current_user: auth_dependency,
):
    """
    Get current user's rank on the leaderboard.

    Requires authentication.
    """
    rank_data = await achievement_service.get_user_rank(db, current_user.id)
    if not rank_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserRankResponse(**rank_data)


@router.get("/{achievement_id}")
async def get_achievement(
    achievement_id: int,
    db: db_dependency,
    current_user: auth_dependency = None,
):
    """
    Get single achievement details.

    Public endpoint - authentication optional for earned status.
    """
    achievements = await achievement_service.get_active_achievements(db)
    achievement = next((a for a in achievements if a.id == achievement_id), None)

    if not achievement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Achievement {achievement_id} not found",
        )

    # Check if user has earned this achievement
    earned = False
    earned_at = None
    progress = 0

    if current_user:
        user_achievements = await achievement_service.get_user_achievements(
            db, current_user.id
        )
        ua = next((ua for ua in user_achievements if ua.achievement_id == achievement_id), None)
        if ua:
            earned = True
            earned_at = ua.earned_at
            progress = ua.progress or 0

    return {
        "achievement": AchievementWithEarned(
            id=achievement.id,
            code=achievement.code,
            title=achievement.title,
            description=achievement.description,
            icon=achievement.icon,
            type=achievement.type,
            category=achievement.category,
            xp_reward=achievement.xp_reward,
            quota_reward=achievement.quota_reward,
            requirements=achievement.requirements,
            is_secret=achievement.is_secret,
            difficulty=achievement.difficulty,
            is_active=achievement.is_active,
            display_order=achievement.display_order,
            earned=earned,
            earned_at=earned_at,
            progress=progress,
        )
    }


logger = logging.getLogger(__name__)
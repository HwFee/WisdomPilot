from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas import UserResponse
from app.schemas.profile import (
    CheckinDetailsResponse,
    CheckinResponse,
    CheckinStatsResponse,
    CheckinStatusResponse,
    UpdateProfileRequest,
    UserProfileResponse,
)
from app.services.profile import profile_service
from app.utils.deps import get_current_active_user
import logging

router = APIRouter(prefix="/api/users", tags=["users"])

db_dependency = Annotated[AsyncSession, Depends(get_db)]
auth_dependency = Annotated[User, Depends(get_current_active_user)]


# IMPORTANT: Specific routes MUST come BEFORE /{user_id} catch-all
# Otherwise /profile, /me/profile, /me/activities, /xp, etc. get matched as user_id="profile"


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_my_profile(
    db: db_dependency,
    current_user: auth_dependency,
):
    """Get current user's learning profile (requires authentication)"""
    user = await profile_service.get_profile(db, current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.put("/me/profile", response_model=UserProfileResponse)
async def update_my_profile(
    db: db_dependency,
    current_user: auth_dependency,
    request: UpdateProfileRequest,
):
    """Update current user's learning profile (requires authentication)"""
    user = await profile_service.get_profile(db, current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if request.preferred_languages is not None:
        user = await profile_service.set_preferred_languages(
            db, user, request.preferred_languages
        )

    return user


@router.get("/me/activities")
async def get_my_activities(
    db: db_dependency,
    current_user: auth_dependency,
    limit: int = Query(default=10, ge=1, le=100),
):
    """Get current user's recent activities"""
    from app.models import ActivityLog

    result = await db.execute(
        select(ActivityLog)
        .where(ActivityLog.user_id == current_user.id)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
    )
    activities = result.scalars().all()

    return {
        "activities": [
            {
                "id": a.id,
                "activity_type": a.activity_type,
                "description": a.description,
                "extra_data": {
                    **(a.extra_data or {}),
                    "learning_path": (a.extra_data or {}).get("learning_path"),
                    "learning_path_label": (a.extra_data or {}).get(
                        "learning_path_label"
                    ),
                },
                # 添加 UTC 时区标识，确保前端正确解析
                "created_at": a.created_at.isoformat() + "Z" if a.created_at else None,
            }
            for a in activities
        ],
        "total": len(activities),
    }


@router.post("/checkin", response_model=CheckinResponse)
async def checkin(
    db: db_dependency,
    current_user: auth_dependency,
):
    """Daily check-in - earn XP and maintain streak"""
    result = await profile_service.checkin(db, current_user)
    return CheckinResponse(**result)


@router.get("/checkin/status", response_model=CheckinStatusResponse)
async def get_checkin_status(
    db: db_dependency,
    current_user: auth_dependency,
):
    """Get current check-in status"""
    checked_in = profile_service.is_checked_in_today(current_user)
    return CheckinStatusResponse(
        streak_days=current_user.streak_days,
        checked_in_today=checked_in,
        last_checkin_date=current_user.last_activity_date,
        total_checkin_days=current_user.total_checkin_days,
    )


@router.get("/checkin/details", response_model=CheckinDetailsResponse)
async def get_checkin_details(
    db: db_dependency,
    current_user: auth_dependency,
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
):
    """Get check-in details with lunar calendar info for a specific date"""
    from datetime import date as date_type

    from app.utils.lunar import get_checkin_details_full

    if year and month and day:
        target_date = date_type(year, month, day)
    else:
        target_date = date_type.today()

    details = get_checkin_details_full(
        target_date.year, target_date.month, target_date.day
    )
    streak_multiplier = profile_service._get_streak_multiplier(current_user.streak_days)

    return CheckinDetailsResponse(
        date=details["date"],
        lunar_str=details["lunar_str"],
        solar_term_str=details["solar_term_str"],
        holiday_str=details["holiday_str"],
        streak_days=current_user.streak_days,
        total_checkin_days=current_user.total_checkin_days,
        streak_multiplier=streak_multiplier,
        checked_in_today=profile_service.is_checked_in_today(current_user),
    )


@router.get("/checkin/stats", response_model=CheckinStatsResponse)
async def get_checkin_stats(
    db: db_dependency,
    current_user: auth_dependency,
):
    """Get check-in statistics"""
    streak_multiplier = profile_service._get_streak_multiplier(current_user.streak_days)

    # Calculate next tier
    next_tier = None
    if current_user.streak_days < 7:
        next_tier = 7 - current_user.streak_days
    elif current_user.streak_days < 14:
        next_tier = 14 - current_user.streak_days
    elif current_user.streak_days < 30:
        next_tier = 30 - current_user.streak_days
    elif current_user.streak_days < 100:
        next_tier = 100 - current_user.streak_days

    return CheckinStatsResponse(
        streak_days=current_user.streak_days,
        total_checkin_days=current_user.total_checkin_days,
        streak_multiplier=streak_multiplier,
        checked_in_today=profile_service.is_checked_in_today(current_user),
        next_tier_days=next_tier,
    )


@router.post("/me/xp")
async def add_xp(
    db: db_dependency,
    current_user: auth_dependency,
    xp_amount: int = Query(gt=0, le=10000, description="XP amount to add (1-10000)"),
):
    """Add XP to current user's profile (requires authentication)"""
    user = await profile_service.get_profile(db, current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user = await profile_service.add_xp(db, user, xp_amount)
    return {
        "xp": user.xp,
        "mastery_xp": user.mastery_xp,
        "mastery_level": user.mastery_level,
    }


# Alias routes for frontend compatibility - MUST come BEFORE /{user_id}
@router.get("/profile", response_model=UserProfileResponse)
async def get_my_profile_alias(
    db: db_dependency,
    current_user: auth_dependency,
):
    """Alias for /me/profile - Get current user's learning profile"""
    user = await profile_service.get_profile(db, current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.put("/profile", response_model=UserProfileResponse)
async def update_my_profile_alias(
    db: db_dependency,
    current_user: auth_dependency,
    request: UpdateProfileRequest,
):
    """Alias for /me/profile - Update current user's learning profile"""
    user = await profile_service.get_profile(db, current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if request.preferred_languages is not None:
        user = await profile_service.set_preferred_languages(
            db, user, request.preferred_languages
        )

    return user


@router.post("/xp")
async def add_xp_alias(
    db: db_dependency,
    current_user: auth_dependency,
    xp_amount: int = Query(gt=0, le=10000, description="XP amount to add (1-10000)"),
):
    """Alias for /me/xp - Add XP to current user's profile"""
    user = await profile_service.get_profile(db, current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user = await profile_service.add_xp(db, user, xp_amount)
    return {
        "xp": user.xp,
        "mastery_xp": user.mastery_xp,
        "mastery_level": user.mastery_level,
    }


# Catch-all route for /{user_id} - MUST be last
# This route is placed last because FastAPI matches routes in order
# All specific routes like /profile, /me/profile, /xp, /me/activities must be defined BEFORE this one
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: db_dependency,
    current_user: auth_dependency,
):
    """Get user by ID (requires authentication)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse.model_validate(user)


logger = logging.getLogger(__name__)
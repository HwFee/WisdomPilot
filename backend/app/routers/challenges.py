"""Challenge API Router"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.challenge import challenge_service
from app.schemas.challenge import (
    ChallengeListResponse,
    ChallengeDetailResponse,
    ChallengeSummary,
    ChallengeDetail,
    UserChallengeResponse,
    UserChallengesResponse,
    UserChallengeSummary,
    UserChallengeDetail,
)
from app.utils.deps import get_current_active_user
import logging

router = APIRouter(prefix="/api/challenges", tags=["challenges"])

db_dependency = Annotated[AsyncSession, Depends(get_db)]
auth_dependency = Annotated[User, Depends(get_current_active_user)]


@router.get("", response_model=ChallengeListResponse)
async def get_challenges(db: db_dependency):
    """
    Get all active challenges.

    Public endpoint - no authentication required.
    """
    challenges = await challenge_service.get_active_challenges(db)
    return ChallengeListResponse(
        challenges=[ChallengeSummary.model_validate(c) for c in challenges],
        total=len(challenges),
    )


# IMPORTANT: /user/me MUST come BEFORE /{challenge_id} to avoid route conflicts
# Otherwise "user" gets matched as challenge_id
@router.get("/user/me", response_model=UserChallengesResponse)
async def get_my_challenges(
    db: db_dependency,
    current_user: auth_dependency,
):
    """
    Get current user's challenge progress.

    Requires authentication.
    """
    user_challenges = await challenge_service.get_user_challenges(db, current_user.id)
    completed = [uc for uc in user_challenges if uc.status == "completed"]

    details = []
    for uc in user_challenges:
        if uc.challenge:
            details.append(
                UserChallengeDetail(
                    id=uc.id,
                    user_id=uc.user_id,
                    challenge_id=uc.challenge_id,
                    status=uc.status,
                    current_progress=uc.current_progress,
                    target_value=uc.target_value,
                    attempts=uc.attempts,
                    started_at=uc.started_at,
                    completed_at=uc.completed_at,
                    challenge=ChallengeSummary.model_validate(uc.challenge),
                )
            )

    return UserChallengesResponse(
        challenges=details, total=len(user_challenges), completed_count=len(completed)
    )


# Catch-all route for challenge_id - MUST come AFTER specific routes like /user/me
@router.get("/{challenge_id}", response_model=ChallengeDetailResponse)
async def get_challenge(challenge_id: int, db: db_dependency):
    """
    Get challenge details by ID.

    Public endpoint - no authentication required.
    """
    challenge = await challenge_service.get_challenge_by_id(db, challenge_id)
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Challenge {challenge_id} not found",
        )
    return ChallengeDetailResponse(challenge=ChallengeDetail.model_validate(challenge))


@router.post("/{challenge_id}/start", response_model=UserChallengeResponse)
async def start_challenge(
    challenge_id: int,
    db: db_dependency,
    current_user: auth_dependency,
):
    """
    Start a challenge.

    Requires authentication.
    """
    try:
        user_challenge = await challenge_service.start_challenge(
            db, current_user, challenge_id
        )
        return UserChallengeResponse(
            user_challenge=UserChallengeSummary.model_validate(user_challenge),
            is_completed=user_challenge.status == "completed",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{challenge_id}/progress")
async def update_challenge_progress(
    challenge_id: int,
    db: db_dependency,
    current_user: auth_dependency,
    progress: int = 1,
):
    """
    Update progress on a challenge.

    Requires authentication.
    """
    try:
        user_challenge = await challenge_service.update_progress(
            db, current_user, challenge_id, progress
        )
        return {
            "challenge_id": challenge_id,
            "current_progress": user_challenge.current_progress,
            "target_value": user_challenge.target_value,
            "is_completed": user_challenge.status == "completed",
            "status": user_challenge.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


logger = logging.getLogger(__name__)

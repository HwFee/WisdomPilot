"""Challenge API Router"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.challenge import challenge_service
from app.services.challenge_errors import (
    ChallengeAlreadyCompletedError,
    ChallengeNotFoundError,
    ChallengeNotStartedError,
    InvalidProgressDeltaError,
)
from app.schemas.challenge import (
    ChallengeProgressResponse,
    ChallengeListResponse,
    ChallengeDetailResponse,
    ChallengeSummary,
    ChallengeDetail,
    UserChallengeResponse,
    UserChallengesResponse,
)
from app.utils.deps import get_current_active_user
from app.services.challenge_responses import (
    build_challenge_progress_response,
    build_user_challenge_response,
    build_user_challenges_response,
)

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
    return build_user_challenges_response(user_challenges)


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
        return build_user_challenge_response(user_challenge)
    except (ChallengeNotFoundError, ChallengeAlreadyCompletedError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.post("/{challenge_id}/progress", response_model=ChallengeProgressResponse)
async def update_challenge_progress(
    challenge_id: int,
    db: db_dependency,
    current_user: auth_dependency,
    progress: int = Query(default=1, ge=1),
):
    """
    Update progress on a challenge.

    Requires authentication.
    """
    try:
        user_challenge = await challenge_service.update_progress(
            db, current_user, challenge_id, progress
        )
        return build_challenge_progress_response(user_challenge)
    except (ChallengeNotStartedError, InvalidProgressDeltaError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

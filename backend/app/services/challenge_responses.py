from app.models.user_challenge import UserChallenge, UserChallengeStatus
from app.schemas.challenge import (
    ChallengeProgressResponse,
    ChallengeSummary,
    UserChallengeDetail,
    UserChallengeResponse,
    UserChallengesResponse,
    UserChallengeSummary,
)


def _build_user_challenge_detail(record: UserChallenge) -> UserChallengeDetail:
    if record.challenge is None:
        raise ValueError("User challenge is missing its challenge relationship")
    return UserChallengeDetail(
        id=record.id,
        user_id=record.user_id,
        challenge_id=record.challenge_id,
        status=record.status,
        current_progress=record.current_progress,
        target_value=record.target_value,
        attempts=record.attempts,
        started_at=record.started_at,
        completed_at=record.completed_at,
        challenge=ChallengeSummary.model_validate(record.challenge),
    )


def build_user_challenges_response(
    records: list[UserChallenge],
) -> UserChallengesResponse:
    details = [
        _build_user_challenge_detail(record)
        for record in records
        if record.challenge is not None
    ]
    completed_count = sum(
        record.status == UserChallengeStatus.COMPLETED.value for record in records
    )
    return UserChallengesResponse(
        challenges=details,
        total=len(records),
        completed_count=completed_count,
    )


def build_user_challenge_response(record: UserChallenge) -> UserChallengeResponse:
    return UserChallengeResponse(
        user_challenge=UserChallengeSummary.model_validate(record),
        is_completed=record.status == UserChallengeStatus.COMPLETED.value,
    )


def build_challenge_progress_response(
    record: UserChallenge,
) -> ChallengeProgressResponse:
    return ChallengeProgressResponse(
        challenge_id=record.challenge_id,
        current_progress=record.current_progress,
        target_value=record.target_value,
        is_completed=record.status == UserChallengeStatus.COMPLETED.value,
        status=record.status,
    )

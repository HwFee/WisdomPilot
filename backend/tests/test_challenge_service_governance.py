from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.challenge import Challenge, ChallengeType
from app.models.user import User
from app.services.challenge import ChallengeService, resolve_challenge_target
from app.services.challenge_errors import (
    InvalidChallengeDefinitionError,
    InvalidProgressDeltaError,
)


def challenge_definition(
    challenge_type: ChallengeType,
    requirements: dict[str, object],
) -> Challenge:
    return Challenge(
        code=f"TEST_{challenge_type.value}",
        title="Target test",
        type=challenge_type.value,
        requirements=requirements,
        rewards={},
    )


@pytest.mark.parametrize(
    ("challenge_type", "requirements", "expected"),
    [
        (ChallengeType.EXERCISE_COUNT, {"exercise_count": 5}, 5),
        (ChallengeType.STREAK, {"days": 7}, 7),
        (ChallengeType.TIME_SPENT, {"minutes": 30}, 30),
        (ChallengeType.ACCURACY, {"accuracy": 80}, 80),
        (ChallengeType.CHAPTER_COMPLETE, {"chapter_id": 1}, 1),
        (ChallengeType.COURSE_COMPLETE, {"course_id": 1}, 1),
        (ChallengeType.STREAK, {"target": 4, "days": 7}, 4),
    ],
)
def test_resolve_challenge_target_uses_type_specific_requirement(
    challenge_type: ChallengeType,
    requirements: dict[str, object],
    expected: int,
) -> None:
    assert resolve_challenge_target(
        challenge_definition(challenge_type, requirements)
    ) == expected


@pytest.mark.parametrize("invalid_target", [None, True, 0, -1, "5"])
def test_resolve_challenge_target_rejects_invalid_definition(
    invalid_target: object,
) -> None:
    challenge = challenge_definition(
        ChallengeType.EXERCISE_COUNT,
        {} if invalid_target is None else {"exercise_count": invalid_target},
    )

    with pytest.raises(InvalidChallengeDefinitionError):
        resolve_challenge_target(challenge)


@pytest.mark.asyncio
async def test_start_streak_challenge_uses_days_target(
    db_session: AsyncSession, auth_user: User
) -> None:
    challenge = challenge_definition(ChallengeType.STREAK, {"days": 7})
    db_session.add(challenge)
    await db_session.commit()
    service = ChallengeService()

    user_challenge = await service.start_challenge(
        db_session, auth_user, challenge.id
    )

    assert user_challenge.target_value == 7


@pytest.mark.asyncio
async def test_default_initialization_fills_missing_codes_without_committing(
    db_session: AsyncSession,
) -> None:
    service = ChallengeService()
    db_session.add(
        Challenge(
            code="FIRST_STEPS",
            title="Existing",
            type=ChallengeType.EXERCISE_COUNT.value,
            requirements={"exercise_count": 5},
            rewards={"quota_bonus": 10},
        )
    )
    await db_session.commit()

    with patch.object(db_session, "commit", new=AsyncMock()) as commit_mock:
        await service.create_default_challenges(db_session)

    codes = set(
        (await db_session.execute(select(Challenge.code))).scalars().all()
    )
    assert codes == {"FIRST_STEPS", "CHAPTER_MASTER", "STREAK_7"}
    commit_mock.assert_not_awaited()


async def persisted_challenge(
    db_session: AsyncSession,
    *,
    code: str = "STATE_TEST",
    target: int = 2,
) -> Challenge:
    challenge = Challenge(
        code=code,
        title="State test",
        type=ChallengeType.EXERCISE_COUNT.value,
        requirements={"target": target},
        rewards={},
    )
    db_session.add(challenge)
    await db_session.commit()
    await db_session.refresh(challenge)
    return challenge


@pytest.mark.asyncio
async def test_start_retry_returns_same_record_without_commit(
    db_session: AsyncSession, auth_user: User
) -> None:
    challenge = await persisted_challenge(db_session)
    service = ChallengeService()
    with patch.object(db_session, "commit", new=AsyncMock()) as commit_mock:
        first = await service.start_challenge(db_session, auth_user, challenge.id)
        second = await service.start_challenge(db_session, auth_user, challenge.id)

    assert second.id == first.id
    assert second.attempts == 1
    commit_mock.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("progress_delta", [0, -1])
async def test_update_progress_rejects_non_positive_delta_without_mutation(
    db_session: AsyncSession,
    auth_user: User,
    progress_delta: int,
) -> None:
    challenge = await persisted_challenge(db_session)
    service = ChallengeService()
    user_challenge = await service.start_challenge(db_session, auth_user, challenge.id)

    with pytest.raises(InvalidProgressDeltaError):
        await service.update_progress(
            db_session, auth_user, challenge.id, progress_delta
        )

    assert user_challenge.current_progress == 0


@pytest.mark.asyncio
async def test_update_progress_flushes_without_committing(
    db_session: AsyncSession, auth_user: User
) -> None:
    challenge = await persisted_challenge(db_session, target=3)
    service = ChallengeService()
    await service.start_challenge(db_session, auth_user, challenge.id)
    await db_session.commit()

    with patch.object(db_session, "commit", new=AsyncMock()) as commit_mock:
        result = await service.update_progress(
            db_session, auth_user, challenge.id, 1
        )

    assert result.current_progress == 1
    commit_mock.assert_not_awaited()

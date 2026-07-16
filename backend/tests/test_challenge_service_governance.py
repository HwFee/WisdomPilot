from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.challenge import Challenge, ChallengeType
from app.models.core_transaction import CoreTransaction
from app.models.user import User
from app.models.user_challenge import UserChallenge
from app.services.challenge import ChallengeService, resolve_challenge_target
from app.services.challenge_errors import (
    InvalidChallengeDefinitionError,
    InvalidProgressDeltaError,
)
from app.services.core_service import CoreService


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


@pytest.mark.asyncio
async def test_completion_reward_updates_balance_total_and_ledger_once(
    db_session: AsyncSession, auth_user: User
) -> None:
    challenge = await persisted_challenge(db_session, target=2)
    challenge.rewards = {"quota_bonus": 10}
    await db_session.commit()
    service = ChallengeService()
    progress = await service.start_challenge(db_session, auth_user, challenge.id)
    await db_session.commit()
    initial_balance = auth_user.cores
    initial_total_earned = auth_user.cores_total_earned

    incomplete = await service.update_progress(
        db_session, auth_user, challenge.id, 1
    )
    assert incomplete.status == "in_progress"
    assert list(
        (await db_session.execute(select(CoreTransaction))).scalars().all()
    ) == []

    completed = await service.update_progress(
        db_session, auth_user, challenge.id, 1
    )
    first_completed_at = completed.completed_at
    transactions = list(
        (await db_session.execute(select(CoreTransaction))).scalars().all()
    )
    assert auth_user.cores == initial_balance + 10
    assert auth_user.cores_total_earned == initial_total_earned + 10
    assert len(transactions) == 1
    assert transactions[0].amount == 10
    assert transactions[0].balance_after == auth_user.cores
    assert transactions[0].category == "bonus"
    assert transactions[0].reference_type == "challenge"
    assert transactions[0].reference_id == progress.id

    retried = await service.update_progress(
        db_session, auth_user, challenge.id, 2
    )
    repeated_transactions = list(
        (await db_session.execute(select(CoreTransaction))).scalars().all()
    )
    assert retried.current_progress == 2
    assert retried.completed_at == first_completed_at
    assert auth_user.cores == initial_balance + 10
    assert auth_user.cores_total_earned == initial_total_earned + 10
    assert len(repeated_transactions) == 1


@pytest.mark.asyncio
async def test_reward_failure_rolls_back_progress_balance_and_ledger(
    db_session: AsyncSession, auth_user: User
) -> None:
    challenge = await persisted_challenge(db_session, code="ROLLBACK_TEST", target=1)
    challenge.rewards = {"quota_bonus": 10}
    service = ChallengeService()
    progress = await service.start_challenge(db_session, auth_user, challenge.id)
    await db_session.commit()
    progress_id = progress.id
    initial_balance = auth_user.cores
    initial_total_earned = auth_user.cores_total_earned
    original_earn = CoreService.earn_cores

    async def earn_then_fail(core_service, *args, **kwargs):
        await original_earn(core_service, *args, **kwargs)
        raise RuntimeError("reward persistence failed")

    with patch.object(CoreService, "earn_cores", new=earn_then_fail):
        with pytest.raises(RuntimeError, match="reward persistence failed"):
            await service.update_progress(db_session, auth_user, challenge.id, 1)
    await db_session.rollback()

    restored_progress = (
        await db_session.execute(
            select(UserChallenge).where(UserChallenge.id == progress_id)
        )
    ).scalar_one()
    await db_session.refresh(auth_user)
    transactions = list(
        (await db_session.execute(select(CoreTransaction))).scalars().all()
    )
    assert restored_progress.status == "in_progress"
    assert restored_progress.current_progress == 0
    assert restored_progress.completed_at is None
    assert auth_user.cores == initial_balance
    assert auth_user.cores_total_earned == initial_total_earned
    assert transactions == []

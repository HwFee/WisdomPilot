from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.core_transaction import CoreTransaction
from app.models.exercise import Exercise
from app.models.spaced_repetition import SpacedRepetition
from app.models.stats import ActivityLog
from app.models.tier_transaction import TierTransaction
from app.models.user_arena import UserArenaProfile
from app.models.wrong_question import WrongQuestion
from app.services.challenge_path.errors import (
    ChallengeExerciseNotFoundError,
    ChallengeProgressNotFoundError,
    MissingChallengeTestCasesError,
)
from app.services.challenge_path.submission import ChallengeSubmissionService
from app.services.challenge_path.submission_state import (
    ChallengeSubmissionStateService,
)
from app.services.core_service import CoreService
from app.services.tier_transaction_service import TierTransactionService


async def persist_arena_pair(db_session, user_id: str):
    exercise = Exercise(
        content={"title": "Atomic Arena"},
        type="programming",
        difficulty=3,
        is_verified=True,
        test_cases=[{"input": "", "output": "42"}],
    )
    next_exercise = Exercise(
        content={"title": "Next Arena"},
        type="programming",
        difficulty=3,
        is_verified=True,
        test_cases=[{"input": "", "output": "7"}],
    )
    db_session.add_all([exercise, next_exercise])
    await db_session.flush()
    progress = ArenaExerciseProgress(
        user_id=user_id,
        exercise_id=exercise.id,
        exercise_index=0,
        is_unlocked=True,
    )
    next_progress = ArenaExerciseProgress(
        user_id=user_id,
        exercise_id=next_exercise.id,
        exercise_index=1,
        is_unlocked=False,
    )
    db_session.add_all([progress, next_progress])
    await db_session.commit()
    return exercise, progress, next_progress


def passing_judge_result() -> dict:
    return {
        "passed_count": 1,
        "total_count": 1,
        "results": [
            {
                "passed": True,
                "input": "",
                "expected": "42",
                "actual": "42",
                "message": None,
            }
        ],
    }


def failing_judge_result() -> dict:
    return {
        "passed_count": 0,
        "total_count": 1,
        "results": [
            {
                "passed": False,
                "input": "",
                "expected": "42",
                "actual": "0",
                "message": "Wrong Answer",
            }
        ],
    }


@pytest.mark.asyncio
async def test_state_service_updates_attempt_and_unlocks_without_commit(
    db_session, auth_user
) -> None:
    exercise, progress, next_progress = await persist_arena_pair(
        db_session, auth_user.id
    )
    service = ChallengeSubmissionStateService(db_session)

    with patch.object(db_session, "commit", new=AsyncMock()) as commit_mock:
        state = await service.apply_attempt(
            user_id=auth_user.id,
            exercise=exercise,
            code="print(42)",
            language="python",
            is_correct=True,
            time_spent=None,
            hint_used=False,
        )

    assert state.progress.id == progress.id
    assert state.progress.attempt_count == 1
    assert state.progress.is_correct is True
    assert state.next_unlocked is True
    assert next_progress.is_unlocked is True
    activities = list(
        (await db_session.execute(select(ActivityLog))).scalars().all()
    )
    assert len(activities) == 1
    commit_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_state_service_rejects_missing_progress_with_typed_error(
    db_session, auth_user
) -> None:
    exercise = Exercise(
        content={"title": "No progress"},
        type="programming",
        difficulty=3,
        is_verified=True,
        test_cases=[{"input": "", "output": "1"}],
    )
    db_session.add(exercise)
    await db_session.commit()

    with pytest.raises(ChallengeProgressNotFoundError):
        await ChallengeSubmissionStateService(db_session).apply_attempt(
            user_id=auth_user.id,
            exercise=exercise,
            code="print(1)",
            language="python",
            is_correct=True,
            time_spent=None,
            hint_used=False,
        )


@pytest.mark.asyncio
async def test_missing_exercise_raises_typed_error(db_session) -> None:
    service = ChallengeSubmissionService(db_session)

    with pytest.raises(ChallengeExerciseNotFoundError, match="Exercise 99999 not found"):
        await service.submit_exercise(
            user_id="user-id",
            exercise_id=99999,
            code="print(1)",
            language="python",
            test_results=[],
        )


@pytest.mark.asyncio
async def test_missing_backend_cases_raises_typed_error(db_session) -> None:
    exercise = Exercise(
        content={"title": "Missing cases"},
        type="programming",
        difficulty=3,
        is_verified=True,
        test_cases=[],
    )
    db_session.add(exercise)
    await db_session.commit()
    service = ChallengeSubmissionService(db_session)

    with pytest.raises(MissingChallengeTestCasesError):
        await service.submit_exercise(
            user_id="user-id",
            exercise_id=exercise.id,
            code="print(1)",
            language="python",
            test_results=[],
        )


@pytest.mark.asyncio
async def test_unexpected_submit_value_error_is_not_mapped_to_400(
    client, auth_headers
) -> None:
    with patch.object(
        ChallengeSubmissionService,
        "submit_exercise",
        new=AsyncMock(side_effect=ValueError("unexpected persistence failure")),
    ):
        with pytest.raises(ValueError, match="unexpected persistence failure"):
            await client.post(
                "/api/learning-path/challenge/submit",
                headers=auth_headers,
                json={
                    "exercise_id": 1,
                    "code": "print(1)",
                    "language": "python",
                    "test_results": [],
                },
            )


@pytest.mark.asyncio
async def test_core_failure_rolls_back_entire_submission(
    db_session, auth_user
) -> None:
    exercise, progress, next_progress = await persist_arena_pair(
        db_session, auth_user.id
    )
    service = ChallengeSubmissionService(db_session)
    original_earn = CoreService.earn_cores
    initial_cores = auth_user.cores

    async def earn_then_fail(core_service, *args, **kwargs):
        await original_earn(core_service, *args, **kwargs)
        raise RuntimeError("core ledger failed")

    with patch(
        "app.services.challenge_path.submission.run_authoritative_judge",
        new=AsyncMock(return_value=passing_judge_result()),
    ), patch.object(CoreService, "earn_cores", new=earn_then_fail):
        with pytest.raises(RuntimeError, match="core ledger failed"):
            await service.submit_exercise(
                user_id=auth_user.id,
                exercise_id=exercise.id,
                code="print(42)",
                language="python",
                test_results=[],
            )
    await db_session.rollback()

    await db_session.refresh(progress)
    await db_session.refresh(next_progress)
    await db_session.refresh(auth_user)
    assert progress.attempt_count == 0
    assert progress.is_correct is False
    assert next_progress.is_unlocked is False
    assert auth_user.cores == initial_cores
    assert list((await db_session.execute(select(ActivityLog))).scalars()) == []
    assert list((await db_session.execute(select(UserArenaProfile))).scalars()) == []
    assert list((await db_session.execute(select(CoreTransaction))).scalars()) == []
    assert list((await db_session.execute(select(TierTransaction))).scalars()) == []


@pytest.mark.asyncio
async def test_tier_failure_rolls_back_wrong_attempt_side_effects(
    db_session, auth_user
) -> None:
    exercise, progress, _ = await persist_arena_pair(db_session, auth_user.id)
    service = ChallengeSubmissionService(db_session)
    original_record = TierTransactionService.record_transaction

    async def record_then_fail(transaction_service, *args, **kwargs):
        await original_record(transaction_service, *args, **kwargs)
        raise RuntimeError("tier ledger failed")

    with patch(
        "app.services.challenge_path.submission.run_authoritative_judge",
        new=AsyncMock(return_value=failing_judge_result()),
    ), patch.object(
        TierTransactionService, "record_transaction", new=record_then_fail
    ):
        with pytest.raises(RuntimeError, match="tier ledger failed"):
            await service.submit_exercise(
                user_id=auth_user.id,
                exercise_id=exercise.id,
                code="print(0)",
                language="python",
                test_results=[],
            )
    await db_session.rollback()

    await db_session.refresh(progress)
    assert progress.attempt_count == 0
    assert list((await db_session.execute(select(ActivityLog))).scalars()) == []
    assert list((await db_session.execute(select(WrongQuestion))).scalars()) == []
    assert list((await db_session.execute(select(SpacedRepetition))).scalars()) == []
    assert list((await db_session.execute(select(UserArenaProfile))).scalars()) == []
    assert list((await db_session.execute(select(TierTransaction))).scalars()) == []


@pytest.mark.asyncio
async def test_repeat_correct_does_not_duplicate_reward_ledgers(
    db_session, auth_user
) -> None:
    exercise, progress, _ = await persist_arena_pair(db_session, auth_user.id)
    service = ChallengeSubmissionService(db_session)
    judge = AsyncMock(return_value=passing_judge_result())

    with patch(
        "app.services.challenge_path.submission.run_authoritative_judge",
        new=judge,
    ):
        first = await service.submit_exercise(
            user_id=auth_user.id,
            exercise_id=exercise.id,
            code="print(42)",
            language="python",
            test_results=[],
        )
        await db_session.commit()
        second = await service.submit_exercise(
            user_id=auth_user.id,
            exercise_id=exercise.id,
            code="print(42)",
            language="python",
            test_results=[],
        )

    core_transactions = list(
        (await db_session.execute(select(CoreTransaction))).scalars().all()
    )
    tier_transactions = list(
        (await db_session.execute(select(TierTransaction))).scalars().all()
    )
    assert first["cores_earned"] == 3
    assert second["stars_earned"] == 0
    assert second["cores_earned"] == 0
    assert len(core_transactions) == 1
    assert len(tier_transactions) == 1

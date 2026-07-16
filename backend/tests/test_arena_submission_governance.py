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
from app.routers.learning_path import SubmitExerciseResponse, router as learning_path_router
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
from app.services.user_profile import UserProfileService


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


async def persist_arena_streak_chain(db_session, user_id: str) -> list[Exercise]:
    first_exercise, _, next_progress = await persist_arena_pair(db_session, user_id)
    second_exercise = await db_session.get(Exercise, next_progress.exercise_id)
    assert second_exercise is not None

    extra_exercises = [
        Exercise(
            content={"title": f"Arena Streak {exercise_number}"},
            type="programming",
            difficulty=3,
            is_verified=True,
            test_cases=[{"input": "", "output": "42"}],
        )
        for exercise_number in range(3, 6)
    ]
    db_session.add_all(extra_exercises)
    await db_session.flush()
    db_session.add_all(
        [
            ArenaExerciseProgress(
                user_id=user_id,
                exercise_id=exercise.id,
                exercise_index=exercise_index,
                is_unlocked=False,
            )
            for exercise_index, exercise in enumerate(extra_exercises, start=2)
        ]
    )
    await db_session.commit()
    return [first_exercise, second_exercise, *extra_exercises[:2]]


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
async def test_profile_failure_rolls_back_entire_correct_submission(
    db_session, auth_user
) -> None:
    exercise, progress, next_progress = await persist_arena_pair(
        db_session, auth_user.id
    )
    service = ChallengeSubmissionService(db_session)
    initial_cores = auth_user.cores
    initial_cores_total_earned = auth_user.cores_total_earned
    profile_failure = AsyncMock(side_effect=RuntimeError("profile update failed"))

    with patch(
        "app.services.challenge_path.submission.run_authoritative_judge",
        new=AsyncMock(return_value=passing_judge_result()),
    ), patch.object(
        UserProfileService, "update_after_exercise", new=profile_failure
    ):
        with pytest.raises(RuntimeError, match="profile update failed"):
            await service.submit_exercise(
                user_id=auth_user.id,
                exercise_id=exercise.id,
                code="print(42)",
                language="python",
                test_results=[],
            )
    profile_failure.assert_awaited_once()
    await db_session.rollback()

    await db_session.refresh(progress)
    await db_session.refresh(next_progress)
    await db_session.refresh(auth_user)
    assert progress.attempt_count == 0
    assert progress.is_completed is False
    assert progress.is_correct is False
    assert next_progress.is_unlocked is False
    assert auth_user.cores == initial_cores
    assert auth_user.cores_total_earned == initial_cores_total_earned
    assert list((await db_session.execute(select(ActivityLog))).scalars()) == []
    assert list((await db_session.execute(select(WrongQuestion))).scalars()) == []
    assert list((await db_session.execute(select(SpacedRepetition))).scalars()) == []
    assert list((await db_session.execute(select(UserArenaProfile))).scalars()) == []
    assert list((await db_session.execute(select(CoreTransaction))).scalars()) == []
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


@pytest.mark.asyncio
async def test_first_correct_updates_profile_streak_once(
    db_session, auth_user
) -> None:
    exercise, _, _ = await persist_arena_pair(db_session, auth_user.id)
    service = ChallengeSubmissionService(db_session)

    with patch(
        "app.services.challenge_path.submission.run_authoritative_judge",
        new=AsyncMock(return_value=passing_judge_result()),
    ):
        await service.submit_exercise(
            user_id=auth_user.id,
            exercise_id=exercise.id,
            code="print(42)",
            language="python",
            test_results=[],
        )

    profile = await UserProfileService(db_session).get_or_create_profile(auth_user.id)
    assert profile.current_streak == 1
    assert profile.best_streak == 1
    assert profile.total_challenges == 1
    assert profile.wins == 1
    assert profile.losses == 0
    assert profile.avg_accuracy == 1.0
    assert profile.highest_difficulty == exercise.difficulty


@pytest.mark.asyncio
async def test_first_wrong_counts_as_attempted_profile_result(
    db_session, auth_user
) -> None:
    exercise, _, _ = await persist_arena_pair(db_session, auth_user.id)
    service = ChallengeSubmissionService(db_session)

    with patch(
        "app.services.challenge_path.submission.run_authoritative_judge",
        new=AsyncMock(return_value=failing_judge_result()),
    ):
        await service.submit_exercise(
            user_id=auth_user.id,
            exercise_id=exercise.id,
            code="print(0)",
            language="python",
            test_results=[],
        )

    profile = await UserProfileService(db_session).get_or_create_profile(auth_user.id)
    assert profile.total_challenges == 1
    assert profile.wins == 0
    assert profile.losses == 1
    assert profile.avg_accuracy == 0.0
    assert profile.highest_difficulty == exercise.difficulty


@pytest.mark.asyncio
async def test_attempted_wrong_splits_streak_and_future_rows_are_ignored(
    db_session, auth_user
) -> None:
    submitted_exercises = await persist_arena_streak_chain(db_session, auth_user.id)
    service = ChallengeSubmissionService(db_session)
    judge_results = [
        passing_judge_result(),
        passing_judge_result(),
        failing_judge_result(),
        passing_judge_result(),
    ]
    with patch(
        "app.services.challenge_path.submission.run_authoritative_judge",
        new=AsyncMock(side_effect=judge_results),
    ):
        for exercise in submitted_exercises:
            await service.submit_exercise(
                user_id=auth_user.id,
                exercise_id=exercise.id,
                code="print(42)",
                language="python",
                test_results=[],
            )

    profile = await UserProfileService(db_session).get_or_create_profile(auth_user.id)
    assert profile.best_streak == 2
    assert profile.current_streak == 1


def test_submit_route_declares_complete_response_model() -> None:
    route = next(
        route
        for route in learning_path_router.routes
        if getattr(route, "path", None) == "/api/learning-path/challenge/submit"
        and "POST" in getattr(route, "methods", set())
    )
    assert route.response_model is SubmitExerciseResponse
    assert "cores_earned" in SubmitExerciseResponse.model_fields


@pytest.mark.asyncio
async def test_submission_flushes_without_committing(
    db_session, auth_user
) -> None:
    exercise, _, _ = await persist_arena_pair(db_session, auth_user.id)
    service = ChallengeSubmissionService(db_session)
    with patch(
        "app.services.challenge_path.submission.run_authoritative_judge",
        new=AsyncMock(return_value=passing_judge_result()),
    ), patch.object(db_session, "commit", new=AsyncMock()) as commit_mock:
        result = await service.submit_exercise(
            user_id=auth_user.id,
            exercise_id=exercise.id,
            code="print(42)",
            language="python",
            test_results=[],
        )
    assert result["cores_earned"] == 3
    commit_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_submit_api_preserves_exact_success_fields(
    client, auth_headers, db_session, auth_user
) -> None:
    exercise, _, _ = await persist_arena_pair(db_session, auth_user.id)
    with patch(
        "app.services.challenge_path.submission.run_authoritative_judge",
        new=AsyncMock(return_value=passing_judge_result()),
    ):
        response = await client.post(
            "/api/learning-path/challenge/submit",
            headers=auth_headers,
            json={
                "exercise_id": exercise.id,
                "code": "print(42)",
                "language": "python",
                "test_results": [],
            },
        )
    assert response.status_code == 200
    assert set(response.json()) == {
        "is_correct",
        "test_results",
        "stars_earned",
        "cores_earned",
        "next_unlocked",
        "added_to_wrong_book",
        "tier_changed",
        "new_tier",
        "new_sub_tier",
        "new_stars",
        "promoted",
        "demoted",
        "first_time_correct",
        "first_time_wrong",
    }

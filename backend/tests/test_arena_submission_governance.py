from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.exercise import Exercise
from app.models.stats import ActivityLog
from app.services.challenge_path.errors import (
    ChallengeExerciseNotFoundError,
    ChallengeProgressNotFoundError,
    MissingChallengeTestCasesError,
)
from app.services.challenge_path.submission import ChallengeSubmissionService
from app.services.challenge_path.submission_state import (
    ChallengeSubmissionStateService,
)


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

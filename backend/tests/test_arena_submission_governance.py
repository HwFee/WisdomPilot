from unittest.mock import AsyncMock, patch

import pytest

from app.models.exercise import Exercise
from app.services.challenge_path.errors import (
    ChallengeExerciseNotFoundError,
    MissingChallengeTestCasesError,
)
from app.services.challenge_path.submission import ChallengeSubmissionService


@pytest.mark.asyncio
async def test_missing_exercise_raises_typed_error(db_session) -> None:
    service = ChallengeSubmissionService(db_session, legacy_service=AsyncMock())

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
    service = ChallengeSubmissionService(db_session, legacy_service=AsyncMock())

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

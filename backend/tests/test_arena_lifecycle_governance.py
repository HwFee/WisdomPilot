from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.challenge_path.errors import (
    ChallengeExerciseLockedError,
    ChallengeProgressIndexNotFoundError,
    InsufficientChallengeExercisesError,
    InvalidChallengeExerciseIndexError,
)
from app.services.challenge_path.progress import ChallengeProgressService
from app.services.challenge_path.selection import ChallengeSelectionService


@pytest.mark.asyncio
async def test_empty_selection_raises_typed_capacity_error(
    db_session, auth_user
) -> None:
    with pytest.raises(
        InsufficientChallengeExercisesError,
        match=r"Not enough verified exercises available \(found 0, need 1\)",
    ):
        await ChallengeSelectionService(db_session)._create_initial_exercises(
            user_id=auth_user.id,
            difficulty_level=3,
            count=1,
        )


@pytest.mark.asyncio
async def test_empty_switch_raises_typed_index_error(
    db_session, auth_user
) -> None:
    with pytest.raises(
        InvalidChallengeExerciseIndexError,
        match="Invalid exercise index",
    ):
        await ChallengeProgressService(db_session).switch_exercise(
            user_id=auth_user.id,
            target_index=0,
        )


@pytest.mark.asyncio
async def test_valid_index_without_progress_raises_typed_error() -> None:
    db = AsyncMock()
    count_result = MagicMock()
    count_result.scalar.return_value = 1
    progress_result = MagicMock()
    progress_result.scalar_one_or_none.return_value = None
    db.execute.side_effect = [count_result, progress_result]

    with pytest.raises(
        ChallengeProgressIndexNotFoundError,
        match="Progress not found",
    ):
        await ChallengeProgressService(db).switch_exercise(
            user_id="user-id",
            target_index=0,
        )


@pytest.mark.asyncio
async def test_locked_switch_raises_typed_error() -> None:
    db = AsyncMock()
    count_result = MagicMock()
    count_result.scalar.return_value = 1
    locked_progress = MagicMock(is_unlocked=False)
    progress_result = MagicMock()
    progress_result.scalar_one_or_none.return_value = locked_progress
    db.execute.side_effect = [count_result, progress_result]

    with pytest.raises(ChallengeExerciseLockedError, match="Exercise is locked"):
        await ChallengeProgressService(db).switch_exercise(
            user_id="user-id",
            target_index=0,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("service_method", "path", "payload"),
    [
        (
            "get_or_create_challenge_path",
            "/api/learning-path/challenge/infinite/start",
            {"difficulty_level": 3, "initial_count": 1},
        ),
        (
            "append_exercises",
            "/api/learning-path/challenge/append",
            {"difficulty_level": 3, "count": 1},
        ),
    ],
)
async def test_unknown_selection_value_error_is_not_mapped_to_400(
    client,
    auth_headers,
    service_method: str,
    path: str,
    payload: dict,
) -> None:
    with patch.object(
        ChallengeSelectionService,
        service_method,
        new=AsyncMock(side_effect=ValueError("unexpected selection failure")),
    ):
        with pytest.raises(ValueError, match="unexpected selection failure"):
            await client.post(path, headers=auth_headers, json=payload)


@pytest.mark.asyncio
async def test_unknown_switch_value_error_is_not_mapped_to_400(
    client, auth_headers
) -> None:
    with patch.object(
        ChallengeProgressService,
        "switch_exercise",
        new=AsyncMock(side_effect=ValueError("unexpected navigation failure")),
    ):
        with pytest.raises(ValueError, match="unexpected navigation failure"):
            await client.post(
                "/api/learning-path/challenge/switch",
                headers=auth_headers,
                json={"target_index": 0},
            )

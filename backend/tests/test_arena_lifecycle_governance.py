from types import GenericAlias
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.exercise import Exercise
from app.routers.learning_path import router as learning_path_router
from app.schemas.arena import (
    AppendExercisesResponse,
    ChallengeExerciseDetailResponse,
    ChallengeProgressResponse,
    ChallengeSessionResponse,
    ExitChallengeResponse,
    RecentArenaExercise,
    SaveCodeResponse,
    SwitchExerciseResponse,
)
from app.services.challenge_path.errors import (
    ChallengeExerciseDetailNotFoundError,
    ChallengeExerciseLockedError,
    ChallengeProgressIndexNotFoundError,
    ChallengeProgressNotFoundError,
    InsufficientChallengeExercisesError,
    InvalidChallengeExerciseIndexError,
)
from app.services.challenge_path.lifecycle import (
    ChallengePathLifecycleService,
    challenge_owner_lock_query,
    challenge_progress_lock_query,
)
from app.services.challenge_path.progress import ChallengeProgressService
from app.services.challenge_path.responses import map_switch_response
from app.services.challenge_path.selection import ChallengeSelectionService


async def persist_verified_exercises(
    db_session, count: int = 2
) -> list[Exercise]:
    exercises = [
        Exercise(
            content={"title": f"Lifecycle {index}"},
            type="programming",
            difficulty=3,
            is_verified=True,
            test_cases=[{"input": "", "output": str(index)}],
        )
        for index in range(count)
    ]
    db_session.add_all(exercises)
    await db_session.commit()
    return exercises


@pytest.mark.asyncio
async def test_empty_selection_raises_typed_capacity_error(
    db_session, auth_user
) -> None:
    with pytest.raises(
        InsufficientChallengeExercisesError,
        match=r"Not enough verified exercises available \(found 0, need 1\)",
    ):
        await ChallengeSelectionService(db_session).select_initial_exercises(
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
async def test_switch_missing_exercise_raises_typed_detail_error() -> None:
    db = AsyncMock()
    count_result = MagicMock()
    count_result.scalar.return_value = 1
    unlocked_progress = MagicMock(is_unlocked=True, exercise_id=999)
    progress_result = MagicMock()
    progress_result.scalar_one_or_none.return_value = unlocked_progress
    exercise_result = MagicMock()
    exercise_result.scalar_one_or_none.return_value = None
    db.execute.side_effect = [count_result, progress_result, exercise_result]

    with pytest.raises(
        ChallengeExerciseDetailNotFoundError,
        match="Exercise not found in challenge path",
    ):
        await ChallengeProgressService(db).switch_exercise(
            user_id="user-id",
            target_index=0,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("service_method", "path", "payload"),
    [
        (
            "start_path",
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
        ChallengePathLifecycleService,
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


@pytest.mark.asyncio
async def test_missing_switch_exercise_returns_exact_404(
    client, auth_headers
) -> None:
    with patch.object(
        ChallengeProgressService,
        "switch_exercise",
        new=AsyncMock(side_effect=ChallengeExerciseDetailNotFoundError()),
    ):
        response = await client.post(
            "/api/learning-path/challenge/switch",
            headers=auth_headers,
            json={"target_index": 0},
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Exercise not found in challenge path"
    }


@pytest.mark.asyncio
async def test_start_locks_owner_and_flushes_without_commit(
    db_session, auth_user
) -> None:
    exercises = await persist_verified_exercises(db_session)
    service = ChallengePathLifecycleService(db_session)

    with patch.object(
        service.selection,
        "select_initial_exercises",
        new=AsyncMock(return_value=exercises),
    ), patch.object(db_session, "commit", new=AsyncMock()) as commit_mock:
        selected, is_new = await service.start_path(
            user_id=auth_user.id,
            difficulty_level=3,
            initial_count=2,
        )

    assert [exercise.id for exercise in selected] == [
        exercise.id for exercise in exercises
    ]
    assert is_new is True
    commit_mock.assert_not_awaited()
    assert "FOR UPDATE" in str(
        challenge_owner_lock_query(auth_user.id).compile(
            dialect=postgresql.dialect()
        )
    )


@pytest.mark.asyncio
async def test_sequential_start_reuses_existing_path(
    db_session, auth_user
) -> None:
    exercises = await persist_verified_exercises(db_session)
    service = ChallengePathLifecycleService(db_session)
    selector = AsyncMock(return_value=exercises)

    with patch.object(
        service.selection,
        "select_initial_exercises",
        new=selector,
    ):
        first, first_is_new = await service.start_path(
            user_id=auth_user.id,
            difficulty_level=3,
            initial_count=2,
        )
        second, second_is_new = await service.start_path(
            user_id=auth_user.id,
            difficulty_level=3,
            initial_count=2,
        )

    assert first_is_new is True
    assert second_is_new is False
    assert [item.id for item in second] == [item.id for item in first]
    selector.assert_awaited_once()


@pytest.mark.asyncio
async def test_append_allocates_indexes_and_flushes_without_commit(
    db_session, auth_user
) -> None:
    existing, appended = await persist_verified_exercises(db_session, count=2)
    existing_progress = ArenaExerciseProgress(
        user_id=auth_user.id,
        exercise_id=existing.id,
        exercise_index=0,
        is_unlocked=True,
        is_completed=True,
    )
    db_session.add(existing_progress)
    await db_session.commit()
    service = ChallengePathLifecycleService(db_session)

    with patch.object(
        service.selection,
        "select_append_exercises",
        new=AsyncMock(return_value=[appended]),
    ), patch.object(db_session, "commit", new=AsyncMock()) as commit_mock:
        new_ids = await service.append_exercises(
            user_id=auth_user.id,
            difficulty_level=3,
            count=1,
        )

    assert new_ids == [appended.id]
    rows = list(
        (
            await db_session.execute(
                select(ArenaExerciseProgress)
                .where(ArenaExerciseProgress.user_id == auth_user.id)
                .order_by(ArenaExerciseProgress.exercise_index)
            )
        ).scalars()
    )
    assert [row.exercise_index for row in rows] == [0, 1]
    assert rows[1].is_unlocked is True
    commit_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_append_keeps_first_new_exercise_locked_after_incomplete_tail(
    db_session, auth_user
) -> None:
    existing, appended = await persist_verified_exercises(db_session, count=2)
    db_session.add(
        ArenaExerciseProgress(
            user_id=auth_user.id,
            exercise_id=existing.id,
            exercise_index=0,
            is_unlocked=True,
            is_completed=False,
        )
    )
    await db_session.commit()
    service = ChallengePathLifecycleService(db_session)

    with patch.object(
        service.selection,
        "select_append_exercises",
        new=AsyncMock(return_value=[appended]),
    ):
        await service.append_exercises(
            user_id=auth_user.id,
            difficulty_level=3,
            count=1,
        )

    appended_row = (
        await db_session.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == auth_user.id,
                ArenaExerciseProgress.exercise_id == appended.id,
            )
        )
    ).scalar_one()
    assert appended_row.is_unlocked is False


@pytest.mark.asyncio
async def test_save_code_locks_progress_replaces_json_and_does_not_commit(
    db_session, auth_user
) -> None:
    exercise = (await persist_verified_exercises(db_session, 1))[0]
    original_codes = {"python": "old"}
    progress = ArenaExerciseProgress(
        user_id=auth_user.id,
        exercise_id=exercise.id,
        exercise_index=0,
        is_unlocked=True,
        saved_codes=original_codes,
        current_language="python",
    )
    db_session.add(progress)
    await db_session.commit()
    service = ChallengePathLifecycleService(db_session)

    with patch.object(db_session, "commit", new=AsyncMock()) as commit_mock:
        await service.save_code(
            user_id=auth_user.id,
            exercise_id=exercise.id,
            code="print('new')",
            language="python",
        )

    assert progress.saved_codes == {"python": "print('new')"}
    assert progress.saved_codes is not original_codes
    assert progress.current_language == "python"
    assert "FOR UPDATE" in str(
        challenge_progress_lock_query(
            user_id=auth_user.id,
            exercise_id=exercise.id,
        ).compile(dialect=postgresql.dialect())
    )
    commit_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_save_progress_raises_typed_error(
    db_session, auth_user
) -> None:
    with pytest.raises(
        ChallengeProgressNotFoundError,
        match="Progress record for exercise 99999 not found",
    ):
        await ChallengePathLifecycleService(db_session).save_code(
            user_id=auth_user.id,
            exercise_id=99999,
            code="print(1)",
            language="python",
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "payload"),
    [
        (
            "/api/learning-path/challenge/save-code",
            {
                "exercise_id": 99999,
                "code": "print(1)",
                "language": "python",
            },
        ),
        (
            "/api/learning-path/challenge/exit",
            {
                "current_exercise_id": 99999,
                "current_code": "print(1)",
                "current_language": "python",
            },
        ),
    ],
)
async def test_missing_save_endpoints_return_exact_404(
    client, auth_headers, path: str, payload: dict
) -> None:
    response = await client.post(path, headers=auth_headers, json=payload)

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Progress record for exercise 99999 not found"
    }


@pytest.mark.asyncio
async def test_detail_attachment_flushes_without_commit(
    db_session, auth_user
) -> None:
    exercise = (await persist_verified_exercises(db_session, 1))[0]
    service = ChallengePathLifecycleService(db_session)

    with patch.object(db_session, "commit", new=AsyncMock()) as commit_mock:
        detail = await service.get_or_attach_exercise(
            user_id=auth_user.id,
            exercise_id=exercise.id,
        )

    assert detail["exercise_id"] == exercise.id
    assert detail["exercise_index"] == 0
    assert detail["is_unlocked"] is True
    commit_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_detail_raises_typed_error(
    db_session, auth_user
) -> None:
    with pytest.raises(
        ChallengeExerciseDetailNotFoundError,
        match="Exercise not found in challenge path",
    ):
        await ChallengePathLifecycleService(
            db_session
        ).get_or_attach_exercise(
            user_id=auth_user.id,
            exercise_id=99999,
        )


@pytest.mark.asyncio
async def test_detail_failure_after_flush_rolls_back_attachment(
    client, auth_headers, db_session, auth_user
) -> None:
    exercise = (await persist_verified_exercises(db_session, 1))[0]
    user_id = auth_user.id
    exercise_id = exercise.id
    with patch(
        "app.routers.learning_path.map_exercise_detail_response",
        side_effect=RuntimeError("response mapping failed"),
    ):
        with pytest.raises(RuntimeError, match="response mapping failed"):
            await client.get(
                f"/api/learning-path/challenge/exercise/{exercise_id}",
                headers=auth_headers,
            )

    attached = (
        await db_session.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.exercise_id == exercise_id,
            )
        )
    ).scalar_one_or_none()
    assert attached is None


def test_lifecycle_routes_declare_response_models() -> None:
    expected = {
        ("/api/learning-path/challenge/infinite/start", "POST"):
            ChallengeSessionResponse,
        ("/api/learning-path/challenge/progress", "GET"):
            ChallengeProgressResponse,
        ("/api/learning-path/challenge/save-code", "POST"):
            SaveCodeResponse,
        ("/api/learning-path/challenge/switch", "POST"):
            SwitchExerciseResponse,
        ("/api/learning-path/challenge/append", "POST"):
            AppendExercisesResponse,
        ("/api/learning-path/challenge/exit", "POST"):
            ExitChallengeResponse,
        ("/api/learning-path/challenge/exercise/{exercise_id:int}", "GET"):
            ChallengeExerciseDetailResponse,
        ("/api/learning-path/challenge/recent", "GET"):
            list[RecentArenaExercise],
    }
    routes = {
        (route.path, method): route.response_model
        for route in learning_path_router.routes
        for method in getattr(route, "methods", set())
    }
    for route_key, response_model in expected.items():
        if isinstance(response_model, GenericAlias):
            assert routes[route_key] == response_model
        else:
            assert routes[route_key] is response_model


def test_switch_mapper_does_not_mutate_service_result() -> None:
    exercise = Exercise(
        id=999,
        content={"title": "Mapper"},
        type="programming",
        difficulty=3,
        is_verified=True,
    )
    result = {
        "exercise_id": 999,
        "saved_code": "",
        "current_language": "python",
        "is_completed": False,
        "is_correct": False,
        "exercise": exercise,
    }

    mapped = map_switch_response(result)

    assert result["exercise"] is exercise
    assert mapped["exercise"]["id"] == 999


def test_legacy_arena_facade_is_absent() -> None:
    from pathlib import Path

    assert not Path("app/services/arena_infinite.py").exists()

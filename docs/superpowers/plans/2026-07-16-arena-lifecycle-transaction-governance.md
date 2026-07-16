# Arena Lifecycle Transaction Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every non-submit Arena lifecycle mutation one typed, locked, request-owned transaction while preserving selection algorithms and successful API payloads.

**Architecture:** `ChallengePathLifecycleService` becomes the only non-submit write use case. `ChallengeSelectionService` chooses exercises without persistence, `ChallengeProgressService` reads and validates navigation, and FastAPI maps only typed expected failures while `get_db` owns commit/rollback.

**Tech Stack:** Python 3.10, FastAPI, SQLAlchemy async ORM, Pydantic v2, pytest, pytest-asyncio, HTTPX, Pyright, CodeGraph.

## Global Constraints

- Scope only Arena start, progress, save-code, switch, append, exit, exercise detail, recent, and their lifecycle/selection/progress/response boundaries.
- Do not modify Arena submit, Judge0, reward/tier/core formulas, profile statistics, recommendation ordering, difficulty windows, fixed-exercise rules, random sampling, frontend code, database schema, migrations, Mastery, or `ChallengeSession`.
- Preserve all successful JSON field names and values, start/append selection results, detail auto-attachment, and first-new-row unlock behavior.
- Selection, progress, lifecycle, and response modules must not import FastAPI or call `commit()`.
- Unknown programming, recommendation, and database errors must propagate for request rollback; only typed expected lifecycle failures map to 400/404.
- Start, append, and detail attachment structurally lock the owner row before allocating progress; save/exit structurally lock the progress row.
- SQLite proves orchestration and rollback, not production row-lock contention.
- Run focused tests, the complete backend suite with zero skips, Pyright, FastAPI and Next.js startup, live affected routes, CodeGraph synchronization, and project Rule 10 quality checks.

---

## File Structure

- Create `backend/app/services/challenge_path/lifecycle.py`: non-submit mutation orchestration, locking, row creation, code persistence, and detail attachment.
- Create `backend/app/schemas/arena.py`: Arena request and top-level response contracts.
- Create `backend/tests/test_arena_lifecycle_governance.py`: typed-error, transaction, locking, rollback, and response-model governance.
- Modify `backend/app/services/challenge_path/errors.py`: shared lifecycle error hierarchy.
- Modify `backend/app/services/challenge_path/selection.py`: selection-only initial/append behavior and focused helpers.
- Modify `backend/app/services/challenge_path/progress.py`: read/navigation-only behavior and pure result helpers.
- Modify `backend/app/services/challenge_path/responses.py`: non-mutating response mapping.
- Modify `backend/app/services/challenge_path/__init__.py`: lifecycle/error exports.
- Modify `backend/app/routers/learning_path.py`: lifecycle calls, typed mapping, and explicit response models.
- Delete `backend/app/services/arena_infinite.py`: unused compatibility facade.
- Modify `backend/tests/test_learning_path_challenge.py`: exact error and response contracts.
- Modify `backend/tests/test_star_logic.py`: remove dead facade dependency and stale test narration.
- Modify `docs/superpowers/specs/2026-07-15-backend-learning-oriented-governance-design.md`: 3B-2 implementation record.
- Modify this plan: checked steps and completion evidence.

## Task 1: Introduce Typed Lifecycle Failures

**Files:**
- Modify: `backend/app/services/challenge_path/errors.py`
- Modify: `backend/app/services/challenge_path/selection.py`
- Modify: `backend/app/services/challenge_path/progress.py`
- Modify: `backend/app/services/challenge_path/__init__.py`
- Modify: `backend/app/routers/learning_path.py:1029-1176`
- Create: `backend/tests/test_arena_lifecycle_governance.py`

**Interfaces:**
- Produces: `ChallengePathError` and five lifecycle subclasses.
- Preserves: all Task 1 status codes and details.
- Guarantees: unrelated `ValueError` is not translated to HTTP 400.

- [ ] **Step 1: Add failing typed-error and Router tests**

Create `backend/tests/test_arena_lifecycle_governance.py`:

```python
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
```

- [ ] **Step 2: Run tests and confirm the lifecycle types are absent**

Run from `backend`:

```powershell
py -3 -m pytest tests/test_arena_lifecycle_governance.py -q
```

Expected: collection fails because the new error classes do not exist.

- [ ] **Step 3: Add the FastAPI-independent hierarchy**

Replace the hierarchy header in `errors.py` and retain existing submission
constructors below it:

```python
class ChallengePathError(Exception):
    """Base class for expected Arena lifecycle failures."""


class ChallengeSubmissionError(ChallengePathError):
    """Base class for expected Arena submission failures."""


class InsufficientChallengeExercisesError(ChallengePathError):
    def __init__(self, found: int, required: int) -> None:
        super().__init__(
            f"Not enough verified exercises available (found {found}, need {required})"
        )


class InvalidChallengeExerciseIndexError(ChallengePathError):
    def __init__(self) -> None:
        super().__init__("Invalid exercise index")


class ChallengeProgressIndexNotFoundError(ChallengePathError):
    def __init__(self) -> None:
        super().__init__("Progress not found")


class ChallengeExerciseLockedError(ChallengePathError):
    def __init__(self) -> None:
        super().__init__("Exercise is locked")


class ChallengeExerciseDetailNotFoundError(ChallengePathError):
    def __init__(self) -> None:
        super().__init__("Exercise not found in challenge path")
```

Change `ChallengeProgressNotFoundError` to inherit `ChallengePathError`
directly. Export every new class from `challenge_path/__init__.py`.

- [ ] **Step 4: Raise typed selection and switch failures**

In `selection.py`, replace the capacity `ValueError` with:

```python
raise InsufficientChallengeExercisesError(
    found=len(all_exercises),
    required=count,
)
```

In `progress.py`, replace the three switch failures exactly:

```python
if target_index < 0 or target_index >= total:
    raise InvalidChallengeExerciseIndexError()

if progress is None:
    raise ChallengeProgressIndexNotFoundError()

if not progress.is_unlocked:
    raise ChallengeExerciseLockedError()
```

- [ ] **Step 5: Map only known lifecycle failures**

Replace start and switch broad catches in `learning_path.py`:

```python
except InsufficientChallengeExercisesError as error:
    raise HTTPException(status_code=400, detail=str(error)) from error
```

```python
except (
    InvalidChallengeExerciseIndexError,
    ChallengeProgressIndexNotFoundError,
    ChallengeExerciseLockedError,
) as error:
    raise HTTPException(status_code=400, detail=str(error)) from error
```

Remove the unused append `try/except`; empty selection remains a successful
empty response and unknown failures propagate.

- [ ] **Step 6: Verify and commit Task 1**

```powershell
py -3 -m pytest tests/test_arena_lifecycle_governance.py tests/test_learning_path_challenge.py tests/test_arena_submission_governance.py -q
pyright
rg -n "except ValueError|from fastapi|HTTPException" app/services/challenge_path app/routers/learning_path.py
git diff --check
git add app/services/challenge_path/errors.py app/services/challenge_path/selection.py app/services/challenge_path/progress.py app/services/challenge_path/__init__.py app/routers/learning_path.py tests/test_arena_lifecycle_governance.py
git commit -m "refactor: type arena lifecycle failures"
```

Expected: focused tests and Pyright pass. Other unrelated Router sections may
still contain broad mappings, but the included Arena endpoints do not.

## Task 2: Extract Locked Start Lifecycle

**Files:**
- Create: `backend/app/services/challenge_path/lifecycle.py`
- Modify: `backend/app/services/challenge_path/selection.py`
- Modify: `backend/app/services/challenge_path/progress.py`
- Modify: `backend/app/services/challenge_path/__init__.py`
- Modify: `backend/app/routers/learning_path.py`
- Modify: `backend/tests/test_arena_lifecycle_governance.py`

**Interfaces:**
- Produces: `ChallengePathLifecycleService.start_path(...)`.
- Produces: `ChallengeSelectionService.select_initial_exercises(...)`.
- Produces: `ChallengeProgressService.list_user_progress(...)` and `get_exercises_for_progress(...)`.
- Guarantees: start locks the owner, flushes without commit, and is sequentially idempotent.

- [ ] **Step 1: Add failing lifecycle, lock, and no-commit tests**

Append:

```python
from sqlalchemy.dialects import postgresql

from app.models.exercise import Exercise
from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.services.challenge_path.lifecycle import (
    ChallengePathLifecycleService,
    challenge_owner_lock_query,
)


async def persist_verified_exercises(db_session, count: int = 2) -> list[Exercise]:
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
```

- [ ] **Step 2: Run and confirm the lifecycle module is absent**

```powershell
py -3 -m pytest tests/test_arena_lifecycle_governance.py -q
```

Expected: collection fails with `ModuleNotFoundError` for `lifecycle`.

- [ ] **Step 3: Make initial selection persistence-free**

In `selection.py`:

1. delete `_create_progress_for_selected_exercises`;
2. rename `_create_initial_exercises` to `select_initial_exercises`;
3. remove its three progress-creation calls and three `flush()` calls;
4. delete `get_or_create_challenge_path`.

Each selection branch returns `selected` immediately after
`_ensure_fixed_first_two(...)`. The fallback branch ends with:

```python
exercise_pool = list(all_exercises)
selected = random.sample(exercise_pool, min(count, len(exercise_pool)))
return self._ensure_fixed_first_two(
    selected,
    hello_world_ex,
    a_plus_b_ex,
    count,
)
```

- [ ] **Step 4: Expose focused progress reads**

Rename the two private methods without changing their queries:

```python
async def list_user_progress(
    self, user_id: str
) -> list[ArenaExerciseProgress]:
```

```python
async def get_exercises_for_progress(
    self,
    progress_records: list[ArenaExerciseProgress],
) -> list[Exercise]:
```

Update internal callers to the new names.

- [ ] **Step 5: Implement the locked start use case**

Create `lifecycle.py`:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.exercise import Exercise
from app.models.user import User
from app.services.challenge_path.progress import ChallengeProgressService
from app.services.challenge_path.selection import ChallengeSelectionService


def challenge_owner_lock_query(user_id: str) -> Select[tuple[str]]:
    return (
        select(User.id)
        .where(User.id == user_id)
        .with_for_update()
    )


class ChallengePathLifecycleService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.selection = ChallengeSelectionService(db)
        self.progress = ChallengeProgressService(db)

    async def _lock_owner(self, user_id: str) -> None:
        result = await self.db.execute(challenge_owner_lock_query(user_id))
        result.scalar_one()

    def _add_progress_rows(
        self,
        *,
        user_id: str,
        exercises: list[Exercise],
        start_index: int,
        unlock_first: bool,
    ) -> list[ArenaExerciseProgress]:
        created = []
        for index_offset, exercise in enumerate(exercises):
            progress = ArenaExerciseProgress(
                user_id=user_id,
                exercise_id=exercise.id,
                exercise_index=start_index + index_offset,
                is_unlocked=unlock_first and index_offset == 0,
            )
            self.db.add(progress)
            created.append(progress)
        return created

    async def start_path(
        self,
        *,
        user_id: str,
        difficulty_level: int,
        initial_count: int,
    ) -> tuple[list[Exercise], bool]:
        await self._lock_owner(user_id)
        progress_records = await self.progress.list_user_progress(user_id)
        if progress_records:
            exercises = await self.progress.get_exercises_for_progress(
                progress_records
            )
            return exercises, False

        exercises = await self.selection.select_initial_exercises(
            user_id=user_id,
            difficulty_level=difficulty_level,
            count=initial_count,
        )
        self._add_progress_rows(
            user_id=user_id,
            exercises=exercises,
            start_index=0,
            unlock_first=True,
        )
        await self.db.flush()
        return exercises, True
```

Export the service from `challenge_path/__init__.py`.

- [ ] **Step 6: Route start through lifecycle and update the unknown-error test**

Instantiate `ChallengePathLifecycleService(db)` and call `start_path(...)`.
Change the start case in the parameterized unknown-error test to patch
`ChallengePathLifecycleService.start_path`; keep the append case on selection
until Task 3. Also change the direct capacity test to call
`select_initial_exercises(...)` after the selection method rename.

- [ ] **Step 7: Verify and commit Task 2**

```powershell
py -3 -m pytest tests/test_arena_lifecycle_governance.py tests/test_learning_path_challenge.py tests/test_arena_submission_governance.py tests/test_hybrid_recommendation.py -q
pyright
rg -n "get_or_create_challenge_path|_create_initial_exercises|_create_progress_for_selected_exercises|commit\(" app/services/challenge_path
git diff --check
git add app/services/challenge_path/lifecycle.py app/services/challenge_path/selection.py app/services/challenge_path/progress.py app/services/challenge_path/__init__.py app/routers/learning_path.py tests/test_arena_lifecycle_governance.py
git commit -m "refactor: isolate arena start lifecycle"
```

Expected: focused tests and Pyright pass; old persistence methods have no
matches and lifecycle has no commit.

## Task 3: Move Append Into The Lifecycle Transaction

**Files:**
- Modify: `backend/app/services/challenge_path/lifecycle.py`
- Modify: `backend/app/services/challenge_path/selection.py`
- Modify: `backend/app/routers/learning_path.py`
- Modify: `backend/tests/test_arena_lifecycle_governance.py`
- Modify: `backend/tests/test_learning_path_challenge.py`

**Interfaces:**
- Produces: `ChallengePathLifecycleService.append_exercises(...)`.
- Produces: `ChallengeSelectionService.select_append_exercises(...)`.
- Guarantees: owner-locked index allocation, preserved selection and unlock behavior, no service commit.

- [ ] **Step 1: Add failing append transaction tests**

Append:

```python
from sqlalchemy import select


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
```

- [ ] **Step 2: Run and confirm lifecycle append is absent**

```powershell
py -3 -m pytest tests/test_arena_lifecycle_governance.py -q
```

Expected: append tests fail because lifecycle lacks `append_exercises` and
selection lacks `select_append_exercises`.

- [ ] **Step 3: Split append selection into focused helpers**

Add constants:

```python
APPEND_DIFFICULTY_WINDOW = 2
APPEND_CANDIDATE_MULTIPLIER = 2
MAX_EXISTING_DIFFICULTY_SAMPLE = 100
```

Replace the old `append_exercises` with selection-only helpers:

```python
async def _infer_append_difficulty(
    self,
    existing_ids: list[int],
    requested_difficulty: int | None,
) -> int:
    if requested_difficulty is not None:
        return requested_difficulty
    if not existing_ids:
        return MIN_CHALLENGE_DIFFICULTY
    result = await self.db.execute(
        select(Exercise)
        .where(Exercise.id.in_(existing_ids))
        .limit(MAX_EXISTING_DIFFICULTY_SAMPLE)
    )
    sampled = list(result.scalars().all())
    if not sampled:
        return MIN_CHALLENGE_DIFFICULTY
    average = sum(exercise.difficulty for exercise in sampled) / len(sampled)
    return max(
        MIN_CHALLENGE_DIFFICULTY,
        min(MAX_CHALLENGE_DIFFICULTY, round(average)),
    )

async def _recommended_append_exercises(
    self,
    *,
    user_id: str,
    difficulty_level: int,
    count: int,
    existing_ids: list[int],
) -> list[Exercise]:
    user_result = await self.db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        return []
    recommendation = await AdaptiveRecommendationService(
        self.db
    ).get_recommendations(
        user=user,
        limit=count,
        min_difficulty=max(
            MIN_CHALLENGE_DIFFICULTY,
            difficulty_level - APPEND_DIFFICULTY_WINDOW,
        ),
        max_difficulty=min(
            MAX_CHALLENGE_DIFFICULTY,
            difficulty_level + APPEND_DIFFICULTY_WINDOW,
        ),
        learning_path="challenge",
        exclude_ids=existing_ids,
    )
    recommended_ids = [
        item["exercise_id"]
        for item in recommendation.get("recommendations", [])
    ]
    if not recommended_ids:
        return []
    result = await self.db.execute(
        select(Exercise).where(Exercise.id.in_(recommended_ids))
    )
    exercises_by_id = {
        exercise.id: exercise for exercise in result.scalars().all()
    }
    return [
        exercises_by_id[exercise_id]
        for exercise_id in recommended_ids
        if exercise_id in exercises_by_id
    ]
```

Implement the existing three fallback query levels in the same order:

```python
async def _fallback_append_exercises(
    self,
    *,
    difficulty_level: int,
    remaining_count: int,
    requested_count: int,
    excluded_ids: list[int],
) -> list[Exercise]:
    candidate_limit = requested_count * APPEND_CANDIDATE_MULTIPLIER
    statements = (
        select(Exercise)
        .where(
            Exercise.is_verified,
            Exercise.difficulty == difficulty_level,
            ~Exercise.id.in_(excluded_ids),
        )
        .limit(candidate_limit),
        select(Exercise)
        .where(
            Exercise.is_verified,
            Exercise.difficulty
            >= max(
                MIN_CHALLENGE_DIFFICULTY,
                difficulty_level - APPEND_DIFFICULTY_WINDOW,
            ),
            Exercise.difficulty
            <= min(
                MAX_CHALLENGE_DIFFICULTY,
                difficulty_level + APPEND_DIFFICULTY_WINDOW,
            ),
            ~Exercise.id.in_(excluded_ids),
        )
        .limit(candidate_limit),
        select(Exercise)
        .where(
            Exercise.is_verified,
            Exercise.difficulty >= MIN_CHALLENGE_DIFFICULTY,
            Exercise.difficulty
            <= min(
                MAX_CHALLENGE_DIFFICULTY,
                difficulty_level + APPEND_DIFFICULTY_WINDOW,
            ),
            ~Exercise.id.in_(excluded_ids),
        )
        .limit(candidate_limit),
    )
    candidates: list[Exercise] = []
    for statement in statements:
        result = await self.db.execute(statement)
        candidates = list(result.scalars().all())
        if len(candidates) >= remaining_count:
            break
    if not candidates:
        return []
    return random.sample(
        candidates,
        min(remaining_count, len(candidates)),
    )
```

The public method is:

```python
async def select_append_exercises(
    self,
    *,
    user_id: str,
    existing_ids: list[int],
    difficulty_level: int | None,
    count: int,
) -> list[Exercise]:
    effective_difficulty = await self._infer_append_difficulty(
        existing_ids,
        difficulty_level,
    )
    selected = await self._recommended_append_exercises(
        user_id=user_id,
        difficulty_level=effective_difficulty,
        count=count,
        existing_ids=existing_ids,
    )
    if len(selected) >= count:
        return selected[:count]
    fallback = await self._fallback_append_exercises(
        difficulty_level=effective_difficulty,
        remaining_count=count - len(selected),
        requested_count=count,
        excluded_ids=existing_ids + [exercise.id for exercise in selected],
    )
    return selected + fallback
```

- [ ] **Step 4: Implement owner-locked lifecycle append**

Add:

```python
async def append_exercises(
    self,
    *,
    user_id: str,
    difficulty_level: int | None,
    count: int,
) -> list[int]:
    await self._lock_owner(user_id)
    progress_records = await self.progress.list_user_progress(user_id)
    existing_ids = [progress.exercise_id for progress in progress_records]
    selected = await self.selection.select_append_exercises(
        user_id=user_id,
        existing_ids=existing_ids,
        difficulty_level=difficulty_level,
        count=count,
    )
    if not selected:
        return []

    last_progress = max(
        progress_records,
        key=lambda progress: progress.exercise_index,
        default=None,
    )
    start_index = (
        last_progress.exercise_index + 1 if last_progress is not None else 0
    )
    unlock_first = (
        last_progress is None or bool(last_progress.is_completed)
    )
    self._add_progress_rows(
        user_id=user_id,
        exercises=selected,
        start_index=start_index,
        unlock_first=unlock_first,
    )
    await self.db.flush()
    return [exercise.id for exercise in selected]
```

- [ ] **Step 5: Route append through lifecycle**

Use `ChallengePathLifecycleService(db).append_exercises(...)`. Update the
unknown append `ValueError` test to patch the lifecycle method.

- [ ] **Step 6: Verify recommendation compatibility and commit Task 3**

```powershell
py -3 -m pytest tests/test_arena_lifecycle_governance.py tests/test_learning_path_challenge.py tests/test_hybrid_recommendation.py tests/test_arena_submission_governance.py -q
pyright
rg -n "async def append_exercises|await self\.db\.commit\(\)|MAX_EXISTING_DIFFICULTY_SAMPLE|APPEND_DIFFICULTY_WINDOW" app/services/challenge_path
git diff --check
git add app/services/challenge_path/lifecycle.py app/services/challenge_path/selection.py app/routers/learning_path.py tests/test_arena_lifecycle_governance.py tests/test_learning_path_challenge.py
git commit -m "refactor: govern arena append lifecycle"
```

Expected: selected tests and Pyright pass; append persistence exists only in
lifecycle and no service commit remains.

## Task 4: Govern Save, Exit, And Detail Attachment

**Files:**
- Modify: `backend/app/services/challenge_path/lifecycle.py`
- Modify: `backend/app/services/challenge_path/progress.py`
- Modify: `backend/app/routers/learning_path.py`
- Modify: `backend/tests/test_arena_lifecycle_governance.py`
- Modify: `backend/tests/test_learning_path_challenge.py`

**Interfaces:**
- Produces: `ChallengePathLifecycleService.save_code(...) -> None`.
- Produces: `ChallengePathLifecycleService.get_or_attach_exercise(...) -> dict`.
- Guarantees: progress-row lock for save, owner lock for attachment, exact 404s, request rollback.

- [ ] **Step 1: Add failing save/detail transaction tests**

Append:

```python
from app.services.challenge_path.errors import (
    ChallengeExerciseDetailNotFoundError,
    ChallengeProgressNotFoundError,
)
from app.services.challenge_path.lifecycle import challenge_progress_lock_query


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
        ).compile(
            dialect=postgresql.dialect()
        )
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
    with patch(
        "app.routers.learning_path.map_exercise_detail_response",
        side_effect=RuntimeError("response mapping failed"),
    ):
        with pytest.raises(RuntimeError, match="response mapping failed"):
            await client.get(
                f"/api/learning-path/challenge/exercise/{exercise.id}",
                headers=auth_headers,
            )

    attached = (
        await db_session.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == auth_user.id,
                ArenaExerciseProgress.exercise_id == exercise.id,
            )
        )
    ).scalar_one_or_none()
    assert attached is None
```

- [ ] **Step 2: Run and confirm lifecycle methods are absent or old save commits**

```powershell
py -3 -m pytest tests/test_arena_lifecycle_governance.py -q
```

Expected: tests fail because lifecycle lacks save/detail and old progress save
still owns persistence.

- [ ] **Step 3: Implement locked code saving**

Add this query builder above the lifecycle class:

```python
def challenge_progress_lock_query(
    *, user_id: str, exercise_id: int
) -> Select[tuple[ArenaExerciseProgress]]:
    return (
        select(ArenaExerciseProgress)
        .where(
            ArenaExerciseProgress.user_id == user_id,
            ArenaExerciseProgress.exercise_id == exercise_id,
        )
        .with_for_update()
    )
```

Then implement:

```python
async def save_code(
    self,
    *,
    user_id: str,
    exercise_id: int,
    code: str,
    language: str,
) -> None:
    result = await self.db.execute(
        challenge_progress_lock_query(
            user_id=user_id,
            exercise_id=exercise_id,
        )
    )
    progress = result.scalar_one_or_none()
    if progress is None:
        raise ChallengeProgressNotFoundError(exercise_id)
    progress.saved_codes = {
        **(progress.saved_codes or {}),
        language: code,
    }
    progress.current_language = language
    await self.db.flush()
```

Delete `ChallengeProgressService.save_code`.

- [ ] **Step 4: Implement owner-locked detail attachment**

Add private helpers that query an existing `(progress, exercise)` pair and map
the exact service dictionary. Implement:

```python
async def get_or_attach_exercise(
    self,
    *,
    user_id: str,
    exercise_id: int,
) -> dict:
    detail = await self.progress.get_existing_exercise_detail(
        user_id=user_id,
        exercise_id=exercise_id,
    )
    if detail is not None:
        return detail

    await self._lock_owner(user_id)
    detail = await self.progress.get_existing_exercise_detail(
        user_id=user_id,
        exercise_id=exercise_id,
    )
    if detail is not None:
        return detail

    exercise_result = await self.db.execute(
        select(Exercise).where(
            Exercise.id == exercise_id,
            Exercise.is_verified,
        )
    )
    exercise = exercise_result.scalar_one_or_none()
    if exercise is None:
        raise ChallengeExerciseDetailNotFoundError()

    progress_records = await self.progress.list_user_progress(user_id)
    exercise_index = len(progress_records)
    created_progress = self._add_progress_rows(
        user_id=user_id,
        exercises=[exercise],
        start_index=exercise_index,
        unlock_first=exercise_index == 0,
    )[0]
    await self.db.flush()
    return self.progress.build_exercise_detail(
        progress=created_progress,
        exercise=exercise,
    )
```

In `progress.py`, replace mutating `get_exercise_by_id` with:

```python
async def get_existing_exercise_detail(
    self,
    *,
    user_id: str,
    exercise_id: int,
) -> dict | None:
    result = await self.db.execute(
        select(ArenaExerciseProgress, Exercise)
        .join(Exercise, ArenaExerciseProgress.exercise_id == Exercise.id)
        .where(
            ArenaExerciseProgress.user_id == user_id,
            ArenaExerciseProgress.exercise_id == exercise_id,
        )
    )
    row = result.one_or_none()
    if row is None:
        return None
    progress, exercise = row
    return self.build_exercise_detail(progress=progress, exercise=exercise)
```

Move the existing dictionary construction into synchronous
`build_exercise_detail(*, progress, exercise) -> dict`.

- [ ] **Step 5: Route save, exit, and detail through lifecycle**

Both save endpoints call `save_code` and return success only after it returns.
Map `ChallengeProgressNotFoundError` to 404. Detail calls
`get_or_attach_exercise`, maps `ChallengeExerciseDetailNotFoundError` to the
existing 404 detail, and obtains `total_exercises` from
`ChallengeProgressService._get_exercise_count` until Task 5 exposes the count.

- [ ] **Step 6: Verify and commit Task 4**

```powershell
py -3 -m pytest tests/test_arena_lifecycle_governance.py tests/test_learning_path_challenge.py tests/test_arena_submission_governance.py tests/test_review_api.py -q
pyright
rg -n "commit\(|async def save_code|get_or_attach_exercise|get_exercise_by_id" app/services/challenge_path app/routers/learning_path.py
git diff --check
git add app/services/challenge_path/lifecycle.py app/services/challenge_path/progress.py app/routers/learning_path.py tests/test_arena_lifecycle_governance.py tests/test_learning_path_challenge.py
git commit -m "fix: make arena lifecycle writes atomic"
```

Expected: exact missing-progress/detail errors pass, rollback test passes, and
the lifecycle/progress services have no commit.

## Task 5: Enforce Read And Response Contracts, Remove The Facade

**Files:**
- Create: `backend/app/schemas/arena.py`
- Modify: `backend/app/services/challenge_path/progress.py`
- Modify: `backend/app/services/challenge_path/responses.py`
- Modify: `backend/app/routers/learning_path.py`
- Delete: `backend/app/services/arena_infinite.py`
- Modify: `backend/tests/test_arena_lifecycle_governance.py`
- Modify: `backend/tests/test_learning_path_challenge.py`
- Modify: `backend/tests/test_star_logic.py`

**Interfaces:**
- Produces: explicit request/response models for all included endpoints.
- Guarantees: progress/switch/recent are read-only, mappers do not mutate inputs, no compatibility facade remains.

- [ ] **Step 1: Add failing response-model, mapper, and facade tests**

Append:

```python
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
from app.services.challenge_path.responses import map_switch_response


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
```

- [ ] **Step 2: Run and confirm the schema exists only in the Router and facade remains**

```powershell
py -3 -m pytest tests/test_arena_lifecycle_governance.py -q
```

Expected: collection fails for `app.schemas.arena` and facade absence fails.

- [ ] **Step 3: Create Arena schemas and preserve dynamic payload shapes**

Create `backend/app/schemas/arena.py` with the moved request models plus:

```python
from typing import Any

from pydantic import BaseModel, Field


class InfiniteSessionStartRequest(BaseModel):
    difficulty_level: int = Field(default=3, ge=1, le=5)
    initial_count: int = Field(default=3, ge=1, le=50)


class ChallengeSessionResponse(BaseModel):
    session_id: str
    difficulty_level: int
    exercises: list[dict[str, Any]]
    time_limit: int
    score_multiplier: float
    status: str


class ChallengeProgressResponse(BaseModel):
    total_exercises: int
    exercises: list[dict[str, Any]]
    correct_count: int
    completed_count: int
    total_stars_earned: int
    current_index: int


class SaveCodeRequest(BaseModel):
    exercise_id: int
    code: str
    language: str


class SaveCodeResponse(BaseModel):
    success: bool


class SwitchExerciseRequest(BaseModel):
    target_index: int


class SwitchExerciseResponse(BaseModel):
    exercise_id: int
    saved_code: str
    current_language: str
    is_completed: bool
    is_correct: bool
    exercise: dict[str, Any]


class AppendExercisesRequest(BaseModel):
    count: int = Field(default=5, ge=1, le=20)
    difficulty_level: int | None = Field(
        default=None,
        ge=1,
        le=8,
        description="难度等级，不传则从用户现有题目推断",
    )


class AppendExercisesResponse(BaseModel):
    new_exercise_ids: list[int]
    count: int


class ExitSaveRequest(BaseModel):
    current_exercise_id: int
    current_code: str
    current_language: str


class ExitChallengeResponse(BaseModel):
    success: bool
    message: str


class ChallengeExerciseDetailResponse(BaseModel):
    exercise: dict[str, Any]
    exercise_index: int
    is_unlocked: bool
    is_completed: bool
    is_correct: bool
    saved_code: str
    current_language: str
    total_exercises: int


class RecentArenaExercise(BaseModel):
    exercise_id: int
    title: str
    is_correct: bool
    difficulty: int
```

Import every schema into the Router at module scope so existing imports from
`learning_path` continue to resolve. Delete the unused
`InfiniteProgressResponse` Router class after repository-wide search confirms
it has no consumer. Keep `SubmitExerciseRequest` and `SubmitExerciseResponse`
in the Router unchanged; moving or editing them is outside 3B-2.

- [ ] **Step 4: Declare response models and make progress helpers focused**

Set the exact response model on every route from the test table. Rename
`_get_exercise_count` to `get_exercise_count` and update Router/lifecycle
callers.

In `progress.py`, extract pure helpers without changing fields:

```python
@staticmethod
def _current_exercise_index(
    progress_records: list[ArenaExerciseProgress],
) -> int:
    current_index = 0
    for index, progress in enumerate(progress_records):
        if not progress.is_completed:
            return index
        current_index = index + 1
    return min(current_index, len(progress_records) - 1)
```

Move per-row lite/full mapping into `_build_progress_item(...)`; return `None`
when the exercise row is missing. `get_progress` uses these helpers and returns
the exact existing empty and populated dictionaries.

Extract switch progress lookup into `_get_switch_progress(...)`, keep typed
errors, and raise `ChallengeExerciseDetailNotFoundError` if the referenced
exercise row is unexpectedly absent so the response model cannot silently
drop `exercise`. Add a separate Router catch that maps this error to 404 with
its existing detail; do not add it to the 400 navigation-error tuple.

- [ ] **Step 5: Make response mapping non-mutating**

Replace `map_switch_response`:

```python
def map_switch_response(result: dict) -> dict:
    exercise = result.get("exercise")
    mapped = {
        key: value
        for key, value in result.items()
        if key != "exercise"
    }
    if exercise is not None:
        mapped["exercise"] = map_exercise_summary(exercise)
    return mapped
```

- [ ] **Step 6: Delete the compatibility facade and clean its stale test**

Delete `arena_infinite.py`. In `test_star_logic.py`:

- remove `ChallengePathService`, `AsyncMock`, `patch`, and `datetime` imports;
- delete the unused `service = ChallengePathService(db_session)` line;
- change the module docstring to say it tests tier/star calculation rather
  than `arena_infinite.py`;
- replace `== True` assertions with direct boolean assertions.

- [ ] **Step 7: Verify complete lifecycle contracts and commit Task 5**

```powershell
py -3 -m pytest tests/test_arena_lifecycle_governance.py tests/test_learning_path_challenge.py tests/test_arena_submission_governance.py tests/test_arena_submission_result.py tests/test_star_logic.py tests/test_hybrid_recommendation.py tests/test_user_profile.py -q
pyright
rg -n "arena_infinite|ChallengePathService|get_arena_infinite_service|await self\.db\.commit\(\)|except ValueError" app tests
git diff --check
git add app/schemas/arena.py app/services/challenge_path/progress.py app/services/challenge_path/responses.py app/routers/learning_path.py tests/test_arena_lifecycle_governance.py tests/test_learning_path_challenge.py tests/test_star_logic.py
git add -u app/services/arena_infinite.py
git commit -m "refactor: enforce arena lifecycle contracts"
```

Expected: selected tests and Pyright pass; no facade/import/service commit or
included-endpoint broad mapping remains.

## Task 6: Validate, Document, And Maintain Arena 3B-2

**Files:**
- Modify: `docs/superpowers/specs/2026-07-15-backend-learning-oriented-governance-design.md`
- Modify: `docs/superpowers/plans/2026-07-16-arena-lifecycle-transaction-governance.md`

- [ ] **Step 1: Run the full backend gate**

From the repository root:

```powershell
py -3 -m pytest backend/tests -q -rs
pyright -p backend/pyrightconfig.json
```

Expected: every backend test passes, no skipped section is printed, and
Pyright reports `0 errors, 0 warnings, 0 informations`.

- [ ] **Step 2: Run scope, transaction, and dead-code searches**

```powershell
rg -n "commit\(|except ValueError|from fastapi|HTTPException|arena_infinite|ChallengePathService|get_arena_infinite_service" backend/app/services/challenge_path backend/app/routers/learning_path.py backend/tests
rg -n "ChallengePathLifecycleService|InsufficientChallengeExercisesError|InvalidChallengeExerciseIndexError|ChallengeExerciseLockedError|ChallengeExerciseDetailNotFoundError" backend/app backend/tests
git diff --name-only dd50e05..HEAD
git diff --check dd50e05..HEAD
```

Confirm no submit/reward/profile, frontend, database, migration, Mastery,
`ChallengeSession`, or recommendation-algorithm source changed. Complete Rule
10 DRY, dependency, naming, magic-value, function-length, dead-code, and type
safety review.

- [ ] **Step 3: Start FastAPI and Next.js and request live contracts**

Use dedicated SQLite smoke data, a test-only secret, hidden managed processes,
and free ports. Verify:

```text
GET  /health                                             -> 200
GET  /                                                   -> 200 after compile
POST /api/auth/register                                  -> 201 bearer token
POST /api/learning-path/challenge/infinite/start         -> 400 exact capacity detail with empty DB
POST /api/learning-path/challenge/save-code missing row  -> 404 exact typed detail
POST /api/learning-path/challenge/exit missing row       -> 404 exact typed detail
POST /api/learning-path/challenge/switch invalid index   -> 400 exact typed detail
GET  /api/learning-path/challenge/exercise/99999         -> 404 existing detail
GET  /api/learning-path/challenge/progress               -> 200 exact top-level fields
GET  /api/learning-path/challenge/recent                 -> 200 list
```

Inspect logs and listener command lines, stop only managed process trees, prove
ports free, remove only resolved smoke artifacts inside the worktree, and keep
the `frontend/node_modules` junction intact.

- [ ] **Step 4: Synchronize and inspect CodeGraph**

```powershell
npx codegraph init .
npx codegraph sync .
npx codegraph impact -p . ChallengePathLifecycleService
npx codegraph impact -p . ChallengeSelectionService
npx codegraph impact -p . ChallengeProgressService
npx codegraph query -p . ChallengePathService
npx codegraph query -p . get_arena_infinite_service
```

Expected: Router write endpoints -> Lifecycle -> Selection/Progress edges
exist; Router read endpoints call Progress directly; no Router write endpoint
bypasses Lifecycle and legacy facade queries have no result.

- [ ] **Step 5: Record completion evidence**

Append an Arena 3B-2 record to the global governance design. Add
`## Completion Evidence` here with TDD red/green outputs, focused/full counts,
Pyright, live statuses/details, CodeGraph edges, commits, deviations, task/final
review findings, the mutating-GET compatibility debt, and SQLite lock risk.

- [ ] **Step 6: Commit completion records**

```powershell
git add docs/superpowers/specs/2026-07-15-backend-learning-oriented-governance-design.md docs/superpowers/plans/2026-07-16-arena-lifecycle-transaction-governance.md
git commit -m "docs: record arena lifecycle governance batch"
```

## Plan Self-Review

- Spec coverage: Tasks 1-5 cover every included endpoint, typed errors, owner/progress locks, request transaction ownership, response models, facade removal, rollback, and compatibility behavior. Task 6 covers all project validation and maintenance gates.
- Scope: submit/rewards/profile, recommendation decisions, frontend, database/schema, migrations, Mastery, and `ChallengeSession` remain excluded.
- Type consistency: lifecycle, selection, progress, error, and schema names/signatures match across tasks.
- TDD order: every production behavior change follows an explicit failing test; characterization-only contracts are identified when they already pass.
- Transaction proof: tests cover no service commit, structural locks, idempotent start, append index/unlock behavior, JSON replacement, typed missing-progress errors, and request rollback after detail attachment.
- Placeholder scan: no unfinished implementation instruction remains.

## Completion Evidence

### Result And Commits

Arena 3B-2 was implemented on `codex/arena-lifecycle-transaction-governance`
from the corrected plan baseline `63af5ee`:

- Task 1: `861e6f8` (`refactor: type arena lifecycle failures`).
- Task 2: `dde029b` (`refactor: isolate arena start lifecycle`).
- Task 3: `b714838` (`refactor: govern arena append lifecycle`).
- Task 4: `90487aa` (`fix: make arena lifecycle writes atomic`).
- Task 5: `ed885a7` (`refactor: enforce arena lifecycle contracts`).
- Task 6 gate repair: `33a3db6` (`style: clean arena router whitespace`).
  This changes only six blank-line end-of-line sequences; `git show
  --ignore-space-at-eol --exit-code` reports no semantic diff.

### TDD And Focused Gates

- Task 1 RED: lifecycle error imports failed collection; GREEN was `7 passed`,
  with the final focused gate `45 passed`.
- Task 2 RED: `ModuleNotFoundError` for the absent lifecycle module; GREEN was
  `9 passed`, final focused `78 passed`, and additional compatibility `16
  passed`.
- Task 3 RED: `2 failed, 9 passed` because
  `select_append_exercises` did not exist; GREEN was `11 passed`, final focused
  `80 passed`.
- Task 4 RED: collection failed for absent `challenge_progress_lock_query`;
  facade regression tests then failed on removed progress methods. GREEN was
  `20 passed`, final focused `67 passed`, and the complete backend gate at that
  checkpoint was `671 passed`.
- Task 5 RED progressed from the absent `app.schemas.arena` module to `3 failed,
  20 passed`, then focused missing-exercise and Router-mapping failures. GREEN
  was `23 passed`; the final focused compatibility gate was `117 passed`.
- After the Task 6 whitespace-only repair, the lifecycle and submission gate
  was rerun: `38 passed in 10.55s`; Pyright remained clean.
- The `test: close arena lifecycle review coverage` final review fix added
  four focused tests with one
  parameterized over two bounds, for five deterministic characterization
  cases total. They cover recommended-ID output ordering, the inference query
  `LIMIT 100`, all three fallback stages with the `count * 2` candidate limit,
  and both `random.sample` bounds: remaining request count and candidate-pool
  size. The final-form lifecycle governance module gate was `28 passed in
  6.87s`.

### Final Automated And Scope Gates

- Historical Task 6 checkpoint: `py -3 -m pytest backend/tests -q -rs` -> `674
  passed in 104.28s`; no skipped-test reason section was printed. Pyright was
  `0 errors, 0 warnings, 0 informations`.
- Latest post-review-fix gate: `py -3 -m pytest backend/tests -q -rs` -> `679
  passed in 103.67s`; no skipped-test reason section was printed. `pyright -p
  backend/pyrightconfig.json` -> `0 errors, 0 warnings, 0 informations`.
- `git diff --check dd50e05..HEAD` exits 0 after `33a3db6`. The initial Task 6
  run exposed six historical CRLF blank lines as trailing whitespace in the
  batch diff; they were repaired and committed separately so the documentation
  commit remains docs-only.
- Scoped search finds no `commit(`, FastAPI/HTTP dependency, broad
  `ValueError` mapping, or legacy facade symbol under
  `backend/app/services/challenge_path`; HTTP translation remains in the
  Router. Repository source has no `arena_infinite`, `ChallengePathService`, or
  legacy factory result.
- The batch changed no frontend, model/schema database definition, migration,
  Mastery, `ChallengeSession`, submission/state, profile, or recommendation
  engine file. `selection.py` structurally extracts append recommendation and
  fallback helpers while preserving recommendation decisions and ordering.

Rule 10 review found one-way Router -> Lifecycle -> Selection/Progress
dependencies with no cycle; shared row construction and response mapping are
centralized; new identifiers are descriptive; append windows, multipliers,
bounds, and sample size use named constants; new lifecycle and append helpers
are focused around one operation; legacy facade/stale callers are absent; and
the full type/runtime gates above are clean. The longer pre-existing initial
selection decision tree delegates query and fixed-exercise work to focused
helpers and was not expanded. No database or AGENTS.md maintenance was needed.

### Live Contracts

Dedicated free ports `18176` and `13176`, explicit secret
`task6-arena-lifecycle-smoke-secret-20260717`, and a worktree-local isolated
SQLite database produced:

| Contract | Status | Exact body/result |
|---|---:|---|
| `GET /health` | 200 | `{"status":"healthy"}` |
| `POST /api/auth/register` | 201 | bearer token present |
| `POST /api/learning-path/challenge/infinite/start` | 400 | `{"detail":"Not enough verified exercises available (found 0, need 1)"}` |
| `POST /api/learning-path/challenge/save-code` | 404 | `{"detail":"Progress record for exercise 99999 not found"}` |
| `POST /api/learning-path/challenge/exit` | 404 | `{"detail":"Progress record for exercise 99999 not found"}` |
| `POST /api/learning-path/challenge/switch` | 400 | `{"detail":"Invalid exercise index"}` |
| `GET /api/learning-path/challenge/exercise/99999` | 404 | `{"detail":"Exercise not found in challenge path"}` |
| `GET /api/learning-path/challenge/progress` | 200 | `{"total_exercises":0,"exercises":[],"correct_count":0,"completed_count":0,"total_stars_earned":0,"current_index":0}` |
| `GET /api/learning-path/challenge/recent` | 200 | `[]` |
| `POST /api/learning-path/challenge/append` | 200 | `{"new_exercise_ids":[],"count":0}` |

Next.js 15.5.18 compiled `/` in 3.5 seconds (1592 modules) and `/arena` in 4.3
seconds (2791 modules); both returned 200 (`13597` and `47920` bytes) and
frontend stderr was empty. Backend logs contained the existing expected
request-transaction rollback trace for handled 400/404 responses and no
`ResponseValidationError`.

Listener command lines and ownership were inspected before stopping only the
verified Python/Node process trees. Ports then had zero listeners. The resolved
`.tmp-task6-live` database/log directory was proven inside the worktree and
removed. The pre-existing `frontend/.next` directory was preserved, and
`frontend/node_modules` remains a junction to the main checkout dependency
tree.

### CodeGraph, Reviews, And Deviations

- At the historical Task 6 checkpoint, `npx codegraph init .` reported already
  initialized and `npx codegraph sync .` synchronized the one whitespace-only
  Router change (`67` nodes). Impact counts were Lifecycle `25`, Selection
  `20`, and Progress `39`.
- After the final review fix, `npx codegraph sync` indexed one changed test
  file (`42` nodes), and final Selection impact is `24`, including all four
  new focused test functions.
  Start/save/append/exit and the mutating detail GET enter Lifecycle;
  Lifecycle calls Selection/Progress. Progress/recent and the read-only switch
  POST call Progress directly. No mutating Router path bypasses Lifecycle.
- Queries for `ChallengePathService` and `get_arena_infinite_service` both
  return `No results found`.
- Task reviews 1, 2, 4, and 5 were clean. Task 3 was originally approved with
  one coverage Minor because no new focused tests locked recommendation
  ordering, fallback escalation, or the 100-row inference query bound. That
  prior Minor is closed by the `test: close arena lifecycle review coverage`
  commit through the five deterministic characterization cases above and is
  no longer outstanding. The Task 6
  pre-document read-only batch review found no other Critical or Important
  issue.
- Task 2 necessarily changed `challenge_path/rewards.py` only to rename the
  focused progress-read call; no reward behavior or formula changed. Task 4
  necessarily changed `tests/conftest.py` so the shared client database
  override mirrors production commit/rollback/re-raise and makes the prescribed
  post-flush rollback test real. Tasks 2-4 minimally redirected the legacy
  facade before Task 5 deleted it.
- Task 5 uses equality, not identity, for the recent route's `GenericAlias`
  response model because Python 3.10 creates a fresh alias for each
  `list[RecentArenaExercise]` subscription; concrete response-model assertions
  still use identity.

Two residual risks remain explicit. First,
`GET /challenge/exercise/{exercise_id}` can attach a verified exercise and is
therefore a compatibility mutating GET; a future API revision should move that
write behind an explicit command. Second, SQLite accepts the structural
`SELECT ... FOR UPDATE` statements and proves orchestration/rollback, but does
not provide production row-lock contention semantics; production-dialect
concurrency integration tests remain necessary.

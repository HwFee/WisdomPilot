# Arena Submission Transaction Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Arena authoritative submission path use typed failures, locked state transitions, one request-owned transaction, atomic ledger-backed rewards, single-owner profile statistics, retry-safe rewards, and an explicit response model.

**Architecture:** `ChallengeSubmissionService` becomes the only `/challenge/submit` use-case service. A focused state service owns locked progress/activity/unlock mutation, reward services own reward side effects without swallowing failures, and `UserProfileService` owns behavior embedding plus Arena statistics. FastAPI owns error mapping and request commit/rollback.

**Tech Stack:** Python 3.10, FastAPI, SQLAlchemy async ORM, Pydantic v2, pytest, pytest-asyncio, HTTPX, Pyright.

## Global Constraints

- Scope only `POST /api/learning-path/challenge/submit` and its submission/state/reward/profile/response boundaries.
- Do not modify Arena start/progress/save/switch/append/exit/detail/recent behavior, selection algorithms, Mastery, ChallengeSession, frontend, database schema, or migrations.
- Preserve Judge0 protocol and verdict rules, successful JSON field names, star/tier formulas, 3-core reward amount, wrong-question rules, and current latest-attempt progress semantics.
- Service modules must not import FastAPI or call `commit()` in the submission path.
- Unknown programming/database/reward/profile errors must propagate for request rollback; only typed expected failures map to 400/503.
- Sequential repeat-correct submissions must not create another core or tier transaction.
- Row-lock claims are structural under SQLite; do not claim production isolation beyond the target database's guarantees.
- Run focused tests, complete backend tests with zero skips, Pyright, FastAPI and Next.js startup, live affected routes, CodeGraph synchronization, and the project quality checklist.

---

## File Structure

- Create `backend/app/services/challenge_path/errors.py`: FastAPI-independent expected submission failures.
- Create `backend/app/services/challenge_path/submission_state.py`: locked progress, activity, code, attempt, and unlock mutation.
- Create `backend/tests/test_arena_submission_governance.py`: transaction, reward, retry, profile, and Router governance tests.
- Modify `backend/app/services/challenge_path/submission.py`: authoritative judge and complete submission orchestration.
- Modify `backend/app/services/challenge_path/rewards.py`: atomic reward side effects and typed result fields.
- Modify `backend/app/services/challenge_path/tier_rewards.py`: shared locked Arena profile acquisition.
- Modify `backend/app/services/challenge_path/__init__.py`: exported submission errors/services.
- Modify `backend/app/services/arena_infinite.py`: remove legacy submission implementation and dead imports.
- Modify `backend/app/services/user_profile.py`: request-owned, single-owner Arena profile update.
- Modify `backend/app/routers/learning_path.py`: exact error mapping and response model.
- Modify `backend/tests/test_challenge_authoritative_submission.py`: typed judge errors and preserved authoritative behavior.
- Modify `backend/tests/test_arena_submission_result.py`: pure verdict helper ownership.
- Modify `backend/tests/test_user_profile.py`: flush/no-commit and complete profile statistics.
- Modify `docs/superpowers/specs/2026-07-15-backend-learning-oriented-governance-design.md`: completed 3B-1 learning record.
- Modify this plan: checked steps and exact completion evidence.

## Task 1: Introduce Typed Submission Failures And Exact HTTP Mapping

**Files:**
- Create: `backend/app/services/challenge_path/errors.py`
- Modify: `backend/app/services/challenge_path/submission.py`
- Modify: `backend/app/services/challenge_path/__init__.py`
- Modify: `backend/app/routers/learning_path.py:1081-1102`
- Create: `backend/tests/test_arena_submission_governance.py`
- Modify: `backend/tests/test_challenge_authoritative_submission.py`

**Interfaces:**
- Produces: `ChallengeSubmissionError` and five exact subclasses.
- Preserves: `JudgeUnavailableError` importable from `challenge_path.submission`.
- Preserves: existing 400/503 details and authoritative judging behavior.

- [x] **Step 1: Add failing typed-error and Router tests**

Create `backend/tests/test_arena_submission_governance.py`:

```python
from unittest.mock import AsyncMock, patch

import pytest

from app.models.exercise import Exercise
from app.services.challenge_path.errors import (
    ChallengeExerciseNotFoundError,
    ChallengeProgressNotFoundError,
    MissingChallengeTestCasesError,
    UnsupportedChallengeLanguageError,
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
```

Update `test_challenge_authoritative_submission.py` to import `UnsupportedChallengeLanguageError` and replace the unsupported-language assertion with:

```python
@pytest.mark.asyncio
async def test_unsupported_language_raises_typed_error():
    with pytest.raises(
        UnsupportedChallengeLanguageError,
        match="Unsupported language for judging: kotlin",
    ):
        await run_authoritative_judge(
            code="println(42)",
            language="kotlin",
            test_cases=[{"input": "", "output": "42"}],
            judge0=_FakeJudge0Service(),
        )
```

- [x] **Step 2: Run the tests and confirm typed interfaces are absent**

Run from `backend`:

```powershell
py -3 -m pytest tests/test_arena_submission_governance.py tests/test_challenge_authoritative_submission.py -q
```

Expected: collection fails because `challenge_path.errors` does not exist.

- [x] **Step 3: Add FastAPI-independent errors**

Create `backend/app/services/challenge_path/errors.py`:

```python
class ChallengeSubmissionError(Exception):
    """Base class for expected Arena submission failures."""


class ChallengeExerciseNotFoundError(ChallengeSubmissionError):
    def __init__(self, exercise_id: int) -> None:
        super().__init__(f"Exercise {exercise_id} not found")


class ChallengeProgressNotFoundError(ChallengeSubmissionError):
    def __init__(self, exercise_id: int) -> None:
        super().__init__(f"Progress record for exercise {exercise_id} not found")


class UnsupportedChallengeLanguageError(ChallengeSubmissionError):
    def __init__(self, language: str) -> None:
        super().__init__(f"Unsupported language for judging: {language}")


class MissingChallengeTestCasesError(ChallengeSubmissionError):
    def __init__(self, exercise_id: int) -> None:
        super().__init__(
            f"Programming exercise {exercise_id} has no backend test cases"
        )


class JudgeUnavailableError(ChallengeSubmissionError):
    def __init__(self, message: str = "Judge service unavailable") -> None:
        super().__init__(message)
```

Export these classes from `challenge_path/__init__.py`.

- [x] **Step 4: Replace service HTTP/ValueError failures**

In `submission.py`, remove FastAPI imports, import the errors, remove the local `JudgeUnavailableError`, and use:

```python
language_id = LANGUAGE_NAME_TO_JUDGE0_ID.get(language.lower())
if language_id is None:
    raise UnsupportedChallengeLanguageError(language)
```

```python
if exercise is None:
    raise ChallengeExerciseNotFoundError(exercise_id)

backend_test_cases = exercise.test_cases or []
if exercise.type == "programming" and not backend_test_cases:
    raise MissingChallengeTestCasesError(exercise_id)
```

Do not translate `JudgeUnavailableError` inside the service; let it propagate to the Router. Re-export it from `submission.py` by importing it at module scope.

- [x] **Step 5: Map only known errors in the submit Router**

Import the five errors into `learning_path.py`. Replace the broad submit catch with:

```python
    except (
        ChallengeExerciseNotFoundError,
        ChallengeProgressNotFoundError,
        MissingChallengeTestCasesError,
        UnsupportedChallengeLanguageError,
    ) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except JudgeUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
```

- [x] **Step 6: Verify errors and commit Task 1**

```powershell
py -3 -m pytest tests/test_arena_submission_governance.py tests/test_challenge_authoritative_submission.py -q
pyright
rg -n "from fastapi|HTTPException|except ValueError" app/services/challenge_path/submission.py app/routers/learning_path.py
git diff --check
git add app/services/challenge_path/errors.py app/services/challenge_path/submission.py app/services/challenge_path/__init__.py app/routers/learning_path.py tests/test_arena_submission_governance.py tests/test_challenge_authoritative_submission.py
git commit -m "refactor: type arena submission failures"
```

Expected: tests and Pyright pass; submission service has no FastAPI match. Other non-submit Router endpoints may still contain `except ValueError` and remain 3B-2 scope.

## Task 2: Extract Locked Submission State And Remove Legacy Mutation

**Files:**
- Create: `backend/app/services/challenge_path/submission_state.py`
- Modify: `backend/app/services/challenge_path/submission.py`
- Modify: `backend/app/services/challenge_path/__init__.py`
- Modify: `backend/app/services/arena_infinite.py`
- Modify: `backend/app/routers/learning_path.py`
- Modify: `backend/tests/test_arena_submission_governance.py`
- Modify: `backend/tests/test_arena_submission_result.py`

**Interfaces:**
- Produces: `ChallengeSubmissionState(progress, next_unlocked)`.
- Produces: `ChallengeSubmissionStateService.apply_attempt(...)`.
- Produces: `all_test_cases_passed(test_results) -> bool` in `submission.py`.
- Changes: `ChallengeSubmissionService(db)` no longer consumes a legacy service.

- [x] **Step 1: Add failing state and no-commit tests**

Append helpers and tests to `test_arena_submission_governance.py`:

```python
from sqlalchemy import select

from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.exercise import Exercise
from app.models.stats import ActivityLog
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
```

- [x] **Step 2: Run and confirm the state module is absent**

```powershell
py -3 -m pytest tests/test_arena_submission_governance.py -q
```

Expected: collection fails with `ModuleNotFoundError` for `submission_state`.

- [x] **Step 3: Implement the focused state service**

Create `submission_state.py` with:

```python
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.exercise import Exercise
from app.models.stats import ActivityLog
from app.services.challenge_path.errors import ChallengeProgressNotFoundError


@dataclass(frozen=True)
class ChallengeSubmissionState:
    progress: ArenaExerciseProgress
    next_unlocked: bool


class ChallengeSubmissionStateService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def apply_attempt(
        self,
        *,
        user_id: str,
        exercise: Exercise,
        code: str,
        language: str,
        is_correct: bool,
        time_spent: int | None,
        hint_used: bool,
    ) -> ChallengeSubmissionState:
        result = await self.db.execute(
            select(ArenaExerciseProgress)
            .where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.exercise_id == exercise.id,
            )
            .with_for_update()
        )
        progress = result.scalar_one_or_none()
        if progress is None:
            raise ChallengeProgressNotFoundError(exercise.id)

        now = datetime.utcnow()
        progress.is_completed = is_correct
        progress.is_correct = is_correct
        progress.last_attempt_at = now
        progress.attempt_count += 1
        progress.current_language = language
        progress.saved_codes = {**(progress.saved_codes or {}), language: code}
        if progress.first_attempt_at is None:
            progress.first_attempt_at = now
        if is_correct and progress.correct_at is None:
            progress.correct_at = now
        if time_spent is not None:
            progress.time_spent = time_spent
        if hint_used:
            progress.hint_used = True
        if progress.attempt_count == 1:
            progress.first_attempt_correct = is_correct

        self.db.add(self._build_activity(user_id, exercise, progress, is_correct))
        next_unlocked = await self._unlock_next(user_id, progress, is_correct)
        await self.db.flush()
        return ChallengeSubmissionState(progress, next_unlocked)
```

Add these exact helpers to the class:

```python
    @staticmethod
    def _build_activity(
        user_id: str,
        exercise: Exercise,
        progress: ArenaExerciseProgress,
        is_correct: bool,
    ) -> ActivityLog:
        content = exercise.content or {}
        exercise_title = (
            content.get("title")
            or content.get("text")
            or f"挑战题目 {progress.exercise_index + 1}"
        )
        return ActivityLog(
            user_id=user_id,
            activity_type="exercise_complete",
            chapter_id=exercise.chapter_id,
            description=f"挑战之路完成练习：{exercise_title}",
            extra_data={
                "learning_path": "challenge",
                "learning_path_label": "挑战之路",
                "exercise_id": exercise.id,
                "exercise_index": progress.exercise_index,
                "exercise_title": exercise_title,
                "is_correct": is_correct,
                "difficulty": exercise.difficulty,
            },
        )

    async def _unlock_next(
        self,
        user_id: str,
        progress: ArenaExerciseProgress,
        is_correct: bool,
    ) -> bool:
        if not is_correct:
            return False
        result = await self.db.execute(
            select(ArenaExerciseProgress)
            .where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.exercise_index > progress.exercise_index,
            )
            .order_by(ArenaExerciseProgress.exercise_index)
            .limit(1)
            .with_for_update()
        )
        next_progress = result.scalar_one_or_none()
        if next_progress is None or next_progress.is_unlocked:
            return False
        next_progress.is_unlocked = True
        return True
```

- [x] **Step 4: Make submission.py the full use-case orchestrator**

Move strict pass parsing to these module-level functions:

```python
def is_strict_passed(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value == 1
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "pass", "passed", "ok"}
    return False


def all_test_cases_passed(test_results: list[dict]) -> bool:
    return bool(test_results) and all(
        is_strict_passed(result.get("passed")) for result in test_results
    )
```

Change the constructor and post-judge flow to:

```python
class ChallengeSubmissionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.state = ChallengeSubmissionStateService(db)
        self.rewards = ChallengeRewardService(db)
        self.profile = UserProfileService(db)

    # after authoritative_test_results is chosen:
    is_correct = all_test_cases_passed(authoritative_test_results)
    state = await self.state.apply_attempt(
        user_id=user_id,
        exercise=exercise,
        code=code,
        language=language,
        is_correct=is_correct,
        time_spent=None,
        hint_used=False,
    )
    reward_fields = await self.rewards.apply_submission_rewards(
        user_id=user_id,
        exercise=exercise,
        progress=state.progress,
        is_correct=is_correct,
        code=code,
    )
    await self.profile.update_after_exercise(
        user_id=user_id,
        exercise_id=exercise.id,
        is_correct=is_correct,
    )
    await self.db.flush()
    return {
        "is_correct": is_correct,
        "test_results": authoritative_test_results,
        "next_unlocked": state.next_unlocked,
        **reward_fields,
    }
```

- [x] **Step 5: Remove legacy submission and update callers/tests**

Delete `ChallengePathService._is_strict_passed`, `_all_test_cases_passed`, `submit_exercise`, and `_submit_exercise_impl`, plus their unused imports. Keep selection/progress/get_stats delegates and compatibility aliases.

In the Router, remove `get_arena_infinite_service` construction and use:

```python
service = ChallengeSubmissionService(db)
```

Update `test_arena_submission_result.py` to import and call `all_test_cases_passed` directly.

- [x] **Step 6: Verify state extraction and commit Task 2**

```powershell
py -3 -m pytest tests/test_arena_submission_governance.py tests/test_challenge_authoritative_submission.py tests/test_learning_path_challenge.py tests/test_arena_submission_result.py -q
pyright
rg -n "_submit_exercise_impl|legacy_service|async def submit_exercise" app/services/arena_infinite.py app/services/challenge_path/submission.py app/routers/learning_path.py
git diff --check
git add app/services/challenge_path/submission_state.py app/services/challenge_path/submission.py app/services/challenge_path/__init__.py app/services/arena_infinite.py app/routers/learning_path.py tests/test_arena_submission_governance.py tests/test_arena_submission_result.py
git commit -m "refactor: isolate arena submission state"
```

Expected: tests and Pyright pass; the legacy/private search has no matches in `arena_infinite.py` and no `legacy_service` anywhere.

## Task 3: Make Rewards Atomic And Retry-Safe

**Files:**
- Modify: `backend/app/services/challenge_path/rewards.py`
- Modify: `backend/app/services/challenge_path/tier_rewards.py`
- Modify: `backend/app/services/user_profile.py`
- Modify: `backend/tests/test_arena_submission_governance.py`

**Interfaces:**
- Produces: `UserProfileService.get_or_create_profile_for_update(user_id)`.
- Guarantees: reward/ledger failures propagate and roll back.
- Guarantees: repeat correct produces zero additional star/core/tier transactions.

- [x] **Step 1: Add failing atomic rollback and retry tests**

Append imports and two integration tests to `test_arena_submission_governance.py`:

```python
from app.models.core_transaction import CoreTransaction
from app.models.spaced_repetition import SpacedRepetition
from app.models.tier_transaction import TierTransaction
from app.models.user_arena import UserArenaProfile
from app.models.wrong_question import WrongQuestion
from app.services.core_service import CoreService
from app.services.tier_transaction_service import TierTransactionService


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
```

- [x] **Step 2: Run and confirm swallowed core failure commits partial state**

```powershell
py -3 -m pytest tests/test_arena_submission_governance.py -q
```

Expected: rollback test fails because `_award_cores` catches the injected error and the later profile commit persists partial state.

- [x] **Step 3: Stop swallowing reward and transaction failures**

In `rewards.py`, define:

```python
CORE_REWARD_CHALLENGE_CORRECT = 3
CORE_REWARD_CATEGORY = "arena"
CORE_REWARD_REFERENCE_TYPE = "exercise"
TIER_TRANSACTION_SOURCE = "arena_challenge"
```

Replace `_award_cores` with:

```python
    async def _award_cores(
        self,
        *,
        user_id: str,
        exercise: Exercise,
        is_correct: bool,
        stars_earned: int,
    ) -> int:
        if not is_correct or stars_earned <= 0:
            return 0
        await CoreService(self.db).earn_cores(
            user_id=user_id,
            amount=CORE_REWARD_CHALLENGE_CORRECT,
            category=CORE_REWARD_CATEGORY,
            reference_type=CORE_REWARD_REFERENCE_TYPE,
            reference_id=str(exercise.id),
            description="挑战之路答对题目",
        )
        return CORE_REWARD_CHALLENGE_CORRECT
```

Import `TierTransactionService` at module scope and replace `_record_tier_transaction` with:

```python
    async def _record_tier_transaction(
        self,
        *,
        user_id: str,
        exercise: Exercise,
        progress: ArenaExerciseProgress,
        is_correct: bool,
        reward_result: dict,
    ) -> None:
        stars_earned = reward_result["stars_earned"]
        promoted = reward_result["promoted"]
        demoted = reward_result["demoted"]
        if stars_earned == 0 and not promoted and not demoted:
            return

        tier_result = reward_result.get("tier_result")
        current_tier = reward_result.get("current_tier")
        profile = reward_result.get("profile")
        used_protection = bool(
            tier_result
            and stars_earned < 0
            and getattr(tier_result, "used_protection", False)
        )
        await TierTransactionService(self.db).record_transaction(
            user_id=user_id,
            course_id=None,
            tier_before=(
                current_tier.value if current_tier else TierRank.BRONZE.value
            ),
            sub_tier_before=int(reward_result.get("current_sub_tier") or 0),
            stars_before=int(reward_result.get("current_stars") or 0),
            tier_after=(reward_result.get("new_tier") or TierRank.BRONZE.value),
            sub_tier_after=int(reward_result.get("new_sub_tier") or 0),
            stars_after=int(reward_result.get("new_stars") or 0),
            stars_change=stars_earned,
            promoted=promoted,
            demoted=demoted,
            used_protection=used_protection,
            protection_remaining=(
                int(profile.protection_remaining or 0) if profile else 0
            ),
            source=TIER_TRANSACTION_SOURCE,
            reference_id=str(exercise.id),
            description=f"挑战之路答题 - {'答对' if is_correct else '答错'}",
        )
```

- [x] **Step 4: Centralize locked Arena profile acquisition**

Add to `UserProfileService`:

```python
async def get_or_create_profile_for_update(
    self, user_id: str
) -> UserArenaProfile:
    result = await self.db.execute(
        select(UserArenaProfile)
        .where(UserArenaProfile.user_id == user_id)
        .with_for_update()
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = UserArenaProfile(user_id=user_id)
        self.db.add(profile)
        await self.db.flush()
    return profile
```

Change `ChallengeTierRewardCalculator._get_or_create_profile` to the following and remove its duplicate creation logic:

```python
    async def _get_or_create_profile(self, user_id: str) -> UserArenaProfile:
        return await UserProfileService(
            self.db
        ).get_or_create_profile_for_update(user_id)
```

- [x] **Step 5: Verify atomic rewards and commit Task 3**

```powershell
py -3 -m pytest tests/test_arena_submission_governance.py tests/test_challenge_authoritative_submission.py tests/test_cores.py tests/test_tier_system.py tests/test_user_arena.py -q
pyright
rg -n "except Exception|commit\(" app/services/challenge_path/rewards.py app/services/challenge_path/tier_rewards.py app/services/challenge_path/submission.py app/services/challenge_path/submission_state.py
git diff --check
git add app/services/challenge_path/rewards.py app/services/challenge_path/tier_rewards.py app/services/user_profile.py tests/test_arena_submission_governance.py
git commit -m "fix: make arena submission rewards atomic"
```

Expected: selected tests pass; scoped services contain no broad catch or commit.

## Task 4: Make Arena Profile Updates Single-Owned And Request-Owned

**Files:**
- Modify: `backend/app/services/user_profile.py`
- Modify: `backend/app/services/challenge_path/rewards.py`
- Modify: `backend/tests/test_user_profile.py`
- Modify: `backend/tests/test_arena_submission_governance.py`

**Interfaces:**
- Preserves: `UserProfileService.update_after_exercise(...) -> dict`.
- Changes: the method flushes but does not commit.
- Produces: one complete recomputation of Arena statistics per submission.

- [x] **Step 1: Change tests to require flush/no-commit and one streak increment**

In `test_user_profile.py`, change the progress mock to match the new joined query:

```python
        progress_result = MagicMock()
        progress_result.all.return_value = [
            (mock_progress1, mock_exercise),
            (mock_progress2, mock_exercise),
        ]
```

Then replace the final assertion of `test_updates_statistics_on_correct_answer` with:

```python
        mock_db.commit = AsyncMock()
        mock_db.flush = AsyncMock()

        result = await service.update_after_exercise(
            user_id="user123",
            course_id=1,
            exercise_id=1,
            is_correct=True,
            time_spent=150,
        )

        mock_db.flush.assert_awaited_once()
        mock_db.commit.assert_not_awaited()
        assert result["total_submissions"] == 3
```

Append an integration assertion to `test_arena_submission_governance.py`:

```python
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
```

- [x] **Step 2: Run and confirm commit/double-streak failures**

```powershell
py -3 -m pytest tests/test_user_profile.py tests/test_arena_submission_governance.py -q
```

Expected: the mock test reports commit usage and the integration test sees `current_streak == 2`.

- [x] **Step 3: Consolidate complete statistics in UserProfileService**

Replace `update_after_exercise` with:

```python
    async def update_after_exercise(
        self,
        user_id: str,
        exercise_id: int,
        is_correct: bool,
        course_id: Optional[int] = None,
        time_spent: Optional[int] = None,
        hint_used: bool = False,
        first_attempt_correct: Optional[bool] = None,
    ) -> dict:
        profile = await self.get_or_create_profile_for_update(user_id)
        exercise_result = await self.db.execute(
            select(Exercise).where(Exercise.id == exercise_id)
        )
        exercise = exercise_result.scalar_one_or_none()
        exercise_embedding = None
        if exercise and exercise.embedding:
            try:
                exercise_embedding = json.loads(exercise.embedding)
            except json.JSONDecodeError:
                logger.warning(
                    "Failed to parse exercise embedding for %s", exercise_id
                )
        if exercise_embedding:
            await self._update_behavior_embedding(
                profile, exercise_embedding, is_correct, time_spent
            )
        await self._update_statistics(profile)
        await self.db.flush()
        return {
            "avg_accuracy": profile.avg_accuracy,
            "avg_time_spent": profile.avg_time_spent,
            "total_submissions": profile.total_submissions,
            "has_behavior_embedding": profile.behavior_embedding is not None,
        }
```

Keep `course_id`, `hint_used`, and `first_attempt_correct` in the signature for compatibility; do not use them to increment statistics outside the full recomputation.

Replace `_update_statistics` with one query joining progress to exercise, ordered by `exercise_index`, and compute exactly:

```python
rows = list((await self.db.execute(
    select(ArenaExerciseProgress, Exercise)
    .join(Exercise, ArenaExerciseProgress.exercise_id == Exercise.id)
    .where(ArenaExerciseProgress.user_id == profile.user_id)
    .order_by(ArenaExerciseProgress.exercise_index)
)).all())
progresses = [progress for progress, _ in rows]
exercise_by_id = {progress.exercise_id: exercise for progress, exercise in rows}
attempted_progresses = [
    progress for progress in progresses if progress.attempt_count > 0
]
correct = [progress for progress in attempted_progresses if progress.is_correct]
profile.total_challenges = len(attempted_progresses)
profile.wins = len(correct)
profile.losses = len(attempted_progresses) - len(correct)
profile.total_submissions = sum(progress.attempt_count for progress in progresses)
profile.avg_accuracy = (
    len(correct) / len(attempted_progresses) if attempted_progresses else 0.0
)
times = [
    progress.time_spent
    for progress in attempted_progresses
    if progress.time_spent
]
profile.avg_time_spent = sum(times) / len(times) if times else 0.0
profile.highest_difficulty = max(
    (
        exercise_by_id[progress.exercise_id].difficulty
        for progress in attempted_progresses
        if progress.exercise_id in exercise_by_id
    ),
    default=0,
)
```

Complete `_update_statistics` with these exact streak assignments. Do not increment either value again from `is_correct`:

```python
best_streak = 0
current_run = 0
for progress in attempted_progresses:
    if progress.is_correct:
        current_run += 1
        best_streak = max(best_streak, current_run)
    else:
        current_run = 0
profile.best_streak = best_streak

current_streak = 0
for progress in reversed(attempted_progresses):
    if not progress.is_correct:
        break
    current_streak += 1
profile.current_streak = current_streak
```

- [x] **Step 4: Remove duplicate reward profile statistics**

Delete the `_update_profile_stats` call and method from `ChallengeRewardService`, plus imports only used by that method. The submission orchestrator's `UserProfileService.update_after_exercise` call becomes the sole statistics owner.

- [x] **Step 5: Verify profile ownership and commit Task 4**

```powershell
py -3 -m pytest tests/test_user_profile.py tests/test_user_arena.py tests/test_hybrid_recommendation.py tests/test_arena_submission_governance.py tests/test_challenge_authoritative_submission.py -q
pyright
rg -n "_update_profile_stats|await self\.db\.commit\(\)" app/services/challenge_path/rewards.py app/services/user_profile.py
git diff --check
git add app/services/user_profile.py app/services/challenge_path/rewards.py tests/test_user_profile.py tests/test_arena_submission_governance.py
git commit -m "refactor: unify arena profile updates"
```

Expected: selected tests pass. The search may find commits in unrelated `UserProfileService` methods, but not inside `update_after_exercise`; `_update_profile_stats` has no matches.

## Task 5: Enforce The Submission Response Contract And Final Transaction Boundary

**Files:**
- Modify: `backend/app/routers/learning_path.py`
- Modify: `backend/tests/test_arena_submission_governance.py`
- Modify: `backend/tests/test_challenge_authoritative_submission.py`

**Interfaces:**
- Produces: complete `SubmitExerciseResponse` including `cores_earned`.
- Guarantees: Router success response is schema-validated and service commits remain absent.

- [x] **Step 1: Add failing exact response and no-service-commit tests**

Append:

```python
from app.main import app
from app.routers.learning_path import SubmitExerciseResponse


def test_submit_route_declares_complete_response_model() -> None:
    route = next(
        route
        for route in app.routes
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
        "is_correct", "test_results", "stars_earned", "cores_earned",
        "next_unlocked", "added_to_wrong_book", "tier_changed",
        "new_tier", "new_sub_tier", "new_stars", "promoted", "demoted",
        "first_time_correct", "first_time_wrong",
    }
```

- [x] **Step 2: Run and confirm the service still commits through the profile method or response schema is incomplete**

```powershell
py -3 -m pytest tests/test_arena_submission_governance.py -q
```

Expected: route response-model assertion fails because the decorator has no model and `cores_earned` is absent. The no-commit assertion also fails until Task 4 removes the nested profile commit.

- [x] **Step 3: Complete the response model**

Add to `SubmitExerciseResponse`:

```python
cores_earned: int
```

Change the decorator to:

```python
@router.post("/challenge/submit", response_model=SubmitExerciseResponse)
```

- [x] **Step 4: Run the complete focused governance gate**

```powershell
py -3 -m pytest tests/test_arena_submission_governance.py tests/test_challenge_authoritative_submission.py tests/test_learning_path_challenge.py tests/test_arena_submission_result.py tests/test_star_logic.py tests/test_cores.py tests/test_tier_system.py tests/test_user_arena.py tests/test_user_profile.py tests/test_review_api.py tests/test_hybrid_recommendation.py -q
pyright
```

Expected: all selected tests pass and Pyright reports zero errors.

- [x] **Step 5: Review and commit Task 5**

```powershell
rg -n "commit\(|except Exception|from fastapi|HTTPException|legacy_service|_submit_exercise_impl" app/services/challenge_path/submission.py app/services/challenge_path/submission_state.py app/services/challenge_path/rewards.py app/services/challenge_path/tier_rewards.py
rg -n "ChallengeSubmissionService\(db," app backend/tests
git diff --check
git add app/routers/learning_path.py tests/test_arena_submission_governance.py tests/test_challenge_authoritative_submission.py
git commit -m "refactor: enforce arena submission contract"
```

Expected: forbidden search has no submission-path commit/FastAPI/HTTPException or
legacy matches; the unchanged Judge0 transport catch in `submission.py` remains
the only `except Exception` match. Constructor search has no legacy two-argument
call.

## Task 6: Validate, Document, And Maintain 3B-1

**Files:**
- Modify: `docs/superpowers/specs/2026-07-15-backend-learning-oriented-governance-design.md`
- Modify: `docs/superpowers/plans/2026-07-16-arena-submission-transaction-governance.md`

- [x] **Step 1: Run the full backend gate from the repository root**

```powershell
py -3 -m pytest backend/tests -q -rs
pyright -p backend/pyrightconfig.json
```

Expected: every backend test passes with no skipped section; Pyright reports `0 errors, 0 warnings, 0 informations`.

- [x] **Step 2: Run scope and quality searches**

```powershell
rg -n "commit\(|except Exception|from fastapi|HTTPException|legacy_service|_submit_exercise_impl" backend/app/services/challenge_path/submission.py backend/app/services/challenge_path/submission_state.py backend/app/services/challenge_path/rewards.py backend/app/services/challenge_path/tier_rewards.py
rg -n "ChallengeExerciseNotFoundError|ChallengeProgressNotFoundError|UnsupportedChallengeLanguageError|MissingChallengeTestCasesError|JudgeUnavailableError" backend/app backend/tests
git diff --name-only 6eba9ea..HEAD
git diff --check 6eba9ea..HEAD
```

Confirm no frontend, database, migration, Mastery, ChallengeSession, selection, progress, or response-navigation source file changed. Complete DRY, dependency direction, naming, magic-value, function-length, dead-code, and type-safety review.

- [x] **Step 3: Start FastAPI and Next.js and request live contracts**

Use ports 8000/3000 if free, otherwise choose free alternatives. Set a dedicated SQLite smoke database and secret, start hidden processes with redirected logs, and verify:

```text
GET  /health                                           -> 200
GET  /                                                 -> frontend 200 after compile
POST /api/auth/register                                -> 201 bearer token
GET  /api/learning-path/challenge/progress             -> 200
POST /api/learning-path/challenge/submit exercise=99999 -> 400 exact typed detail
```

Inspect backend/frontend stdout and stderr, verify listener command lines, then stop only those processes and prove the ports are free.

- [x] **Step 4: Synchronize the worktree CodeGraph index**

```powershell
npx codegraph init .
npx codegraph sync .
npx codegraph impact -p . ChallengeSubmissionService
npx codegraph impact -p . ChallengeSubmissionStateService
npx codegraph impact -p . ChallengeRewardService
npx codegraph query -p . _submit_exercise_impl
```

Expected: Router -> Submission -> State/Reward/Profile edges exist and `_submit_exercise_impl` has no result.

- [x] **Step 5: Record learning and completion evidence**

Append a 3B-1 implementation record to the global governance design. Add `## Completion Evidence` here with red-green outputs, focused/full counts, Pyright, live statuses, CodeGraph edges, commits, deviations, review findings, and residual SQLite/3B-2 risks.

- [x] **Step 6: Commit completion records**

```powershell
git add docs/superpowers/specs/2026-07-15-backend-learning-oriented-governance-design.md docs/superpowers/plans/2026-07-16-arena-submission-transaction-governance.md
git commit -m "docs: record arena submission governance batch"
```

## Completion Evidence

### TDD And Focused Regression History

- Task 1 RED failed collection with `ModuleNotFoundError: app.services.challenge_path.errors`; GREEN was `12 passed in 2.30s`.
- Task 2 RED failed collection with `ModuleNotFoundError: app.services.challenge_path.submission_state`; focused GREEN was `5 passed in 1.40s`, and the four-file regression gate was `41 passed in 9.67s`.
- Task 3 RED was `2 failed, 6 passed in 2.53s`, proving core and tier ledger failures were swallowed; focused GREEN was `8 passed in 2.24s`, and the required reward regression gate was `59 passed in 7.42s`.
- Task 4 RED was `1 failed, 17 passed in 3.04s`, proving the profile path committed instead of flushing. Focused GREEN was `18 passed in 2.62s`; an explicit correct/correct/wrong/correct regression also failed when future unattempted rows were included and passed after the approved attempted-row filter. The final profile regression gate was `65 passed in 4.99s`.
- Task 5 produced two structural RED runs of `1 failed, 12 passed`: first the FastAPI lazy-router lookup was corrected, then the route correctly failed because `response_model` was `None`. GREEN was `13 passed`; the final focused governance gate was `152 passed in 19.73s`.
- Final review found that non-streak profile aggregates still mixed completed, correct, and all-row populations. Follow-up regressions now cover a wrong-only attempt, a correct attempt beside a future unattempted row, and rollback after a profile failure that occurs after state and rewards flush. All result statistics use attempted rows; `total_submissions` remains the sum of every row's `attempt_count`.

### Final Gates

- Task 6 pre-review gate `py -3 -m pytest backend/tests -q -rs`: `649 passed in 92.87s`, with no skipped section.
- Post-review final gate on `f19e4de`: `651 passed in 90.85s`, with no skipped section. Final Pyright remained `0 errors, 0 warnings, 0 informations`.
- `pyright -p backend/pyrightconfig.json`: `0 errors, 0 warnings, 0 informations`. A second Pyright run after the byte-only whitespace correction produced the same result.
- Scope search found no service commit, FastAPI/HTTP exception dependency, legacy service, or `_submit_exercise_impl` in the four submission services. The sole `except Exception` hit is the pre-existing Judge0 transport translator at `submission.py:115`, unchanged from the baseline and required to raise `JudgeUnavailableError`.
- `git diff --check 6eba9ea..HEAD` initially exposed one CRLF-only blank line in `user_profile.py`. Byte inspection proved the mixed-line-ending cause; commit `50fa5b7` changes only that separator line, after which the exact aggregate check exits zero.
- Changed-source inspection found no frontend, schema/database, migration, Mastery, ChallengeSession, selection, progress, response, or navigation source changes. `arena_infinite.py` only loses the legacy submit mutation while keeping selection/progress compatibility delegates.
- Rule 10 passed for DRY, one-way Router -> Submission -> State/Reward/Profile dependencies, descriptive naming, named business constants, explicit orchestration/section boundaries for longer functions, reachable symbols, and type safety. No database or AGENTS.md maintenance was required.

### Live Contracts And Maintenance

- Hidden managed FastAPI and Next.js processes used a dedicated SQLite database, a test-only secret, and preferred ports `8000` and `3000`.
- `GET /health` returned `200`; Next.js compiled `/` in `12.4s` and returned `200`; registration returned `201` with a bearer token; challenge progress returned `200`; missing exercise submission returned `400` with exact body `{"detail":"Exercise 99999 not found"}`.
- Backend startup completed and initialized/stamped the smoke database; frontend startup and compilation completed. Expected negative-request rollback traces were inspected. Only the managed Uvicorn PID and Next.js parent/listener PIDs were stopped, both ports were proven free, and the resolved in-worktree smoke database/log directory was removed. The intentional `frontend/node_modules` junction was not modified.
- The post-review smoke on clean HEAD `f19e4de` repeated the same five contracts: backend health `200`, registration `201` bearer, challenge progress `200`, exact missing-exercise `400`, and frontend `/` `200` after `Compiled / in 1888ms`. Managed processes were stopped, ports `8000`/`3000` were free, and `.final-smoke` artifacts were removed.
- CodeGraph was already initialized; `npx codegraph sync .` completed. Impacts contained 15 symbols for `ChallengeSubmissionService`, 24 for `ChallengeSubmissionStateService`, and 28 for `ChallengeRewardService`, showing the Router -> Submission -> State/Reward/Profile flow and governance tests. Querying `_submit_exercise_impl` returned `No results found`.

### Commits, Deviations, And Review

- Implementation and review-fix commits: `36edbff` (typed failures), `0b6461a` (corrected exception-contract text), `366bfd2` (locked state extraction), `835e8be` (atomic rewards), `6517680` (stale reward logger cleanup), `daa67dc` (single-owned profile updates), `53a65ff` (response/transaction contract), `50fa5b7` (aggregate whitespace gate correction), `ac58773` (completion record), `d88b366` (search-evidence correction), and `f19e4de` (attempted-result aggregates and profile-failure rollback proof).
- Approved Task 4 deviation: streaks use rows with `attempt_count > 0`. Future unattempted rows do not reset a streak, while attempted incorrect rows remain in sequence and do reset it. Unit and integration tests cover both cases.
- Task review findings for a stale docstring/logger and Task 4 P3 stale-import/mixed-state/attempted-wrong coverage were corrected before the original completion record. Final review then identified and corrected the remaining mixed-population aggregate defect and added the missing profile-failure rollback proof. Re-review reported no remaining findings and `Ready to merge: Yes`; the final 651-test gate and post-review live smoke both passed on the corrected branch.
- Residual SQLite risk: SQLite does not exercise production `SELECT ... FOR UPDATE` contention, so concurrency behavior still requires a production-dialect integration gate. Future 3B-2 work should govern the remaining non-submit challenge paths and broad/`ValueError` mappings without reopening this submission transaction or changing selection/navigation behavior opportunistically.

## Plan Self-Review

- Spec coverage: Tasks 1-5 cover typed errors, authoritative orchestration, locked state, request transaction ownership, atomic rewards, sequential retry, profile consolidation, and response validation. Task 6 covers every validation and maintenance gate.
- Scope: only Arena submit and shared profile code used exclusively by submit mutation change; selection/navigation, Mastery, frontend, schema, and migrations remain excluded.
- Type consistency: error names, constructor signatures, state dataclass, response fields, and service calls match across tasks.
- TDD order: each behavior change has a preceding red test; Task 5 is an explicit final regression gate after earlier red-green tasks.
- Transaction proof: tests cover no service commit, reward failure rollback, ledger counts, and profile single counting.
- Placeholder scan: no unfinished implementation instruction remains.

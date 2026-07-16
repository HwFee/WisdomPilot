# Challenge State And Reward Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the generic challenge lifecycle use explicit target rules, request-owned transactions, typed state failures, ledger-backed rewards, retry-safe completion, and pure response mapping.

**Architecture:** `ChallengeService` remains the generic challenge use-case service but no longer commits. It owns target resolution and state transitions, delegates currency mutation to `CoreService`, and raises FastAPI-independent errors. The challenge Router validates HTTP input and maps known errors; pure mapper functions construct Pydantic responses.

**Tech Stack:** Python 3.10, FastAPI, SQLAlchemy async ORM, Pydantic v2, pytest, pytest-asyncio, HTTPX, Pyright.

## Global Constraints

- Scope only `/api/challenges`, `backend/app/services/challenge.py`, generic `Challenge`/`UserChallenge`, and their response/ledger boundaries.
- Do not modify Arena challenge path, Mastery progress, ChallengeSession scoring, frontend code, database schema, or migrations.
- Preserve successful response fields, existing challenge definitions, quota bonus amounts, JWT behavior, and completed-challenge restart behavior.
- API progress must reject zero or negative values; direct service calls must raise a typed error for the same condition.
- Completion rewards must update `cores`, `cores_total_earned`, and one `CoreTransaction` in the same request transaction.
- Service methods must not call `commit()`; request `get_db` owns commit/rollback.
- Prove sequential retry idempotency. Do not claim database-level uniqueness for two concurrent first-start requests without a future unique-constraint migration.
- Run focused tests, complete backend tests with zero skips, Pyright, FastAPI and Next.js startup, live affected routes, CodeGraph synchronization, and the project quality checklist.

---

## File Structure

- Create `backend/app/services/challenge_errors.py`: typed generic challenge failures.
- Create `backend/app/services/challenge_responses.py`: pure ORM-to-Pydantic response mapping.
- Modify `backend/app/services/challenge.py`: named definitions, target resolution, request-owned state transitions, row locking, CoreService reward delegation.
- Modify `backend/app/routers/challenges.py`: exact error mapping, positive Query validation, pure response mapping.
- Modify `backend/app/schemas/challenge.py`: `ChallengeProgressResponse`.
- Create `backend/tests/test_challenge_service_governance.py`: target, transaction, ledger, idempotency, rollback tests.
- Create `backend/tests/test_challenge_responses.py`: pure mapper contracts.
- Modify `backend/tests/test_challenges.py`: API error, validation, and response contracts.
- Modify `docs/superpowers/specs/2026-07-15-backend-learning-oriented-governance-design.md`: completed 3A learning record.
- Modify this plan: checked steps and exact completion evidence.

## Task 1: Resolve Challenge Targets And Repair Default Initialization

**Files:**
- Create: `backend/app/services/challenge_errors.py`
- Create: `backend/tests/test_challenge_service_governance.py`
- Modify: `backend/app/services/challenge.py:1-193`

**Interfaces:**
- Produces: `InvalidChallengeDefinitionError(challenge_type: str, requirement: str)`.
- Produces: `resolve_challenge_target(challenge: Challenge) -> int`.
- Produces: `DEFAULT_CHALLENGE_DEFINITIONS: tuple[dict[str, object], ...]`.
- Preserves: `ChallengeService.start_challenge(db, user, challenge_id) -> UserChallenge`.

- [x] **Step 1: Add failing target and initialization tests**

Create `backend/tests/test_challenge_service_governance.py`:

```python
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.challenge import Challenge, ChallengeType
from app.models.user import User
from app.services.challenge import ChallengeService, resolve_challenge_target
from app.services.challenge_errors import InvalidChallengeDefinitionError


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
```

- [x] **Step 2: Run the module and confirm the new interfaces are absent**

Run from `backend`:

```powershell
py -3 -m pytest tests/test_challenge_service_governance.py -q
```

Expected: collection fails because `resolve_challenge_target` and `challenge_errors` do not exist.

- [x] **Step 3: Add the definition error and target resolver**

Create `backend/app/services/challenge_errors.py`:

```python
class ChallengeError(Exception):
    """Base class for expected generic challenge failures."""


class InvalidChallengeDefinitionError(ChallengeError):
    def __init__(self, challenge_type: str, requirement: str) -> None:
        super().__init__(
            f"Challenge type {challenge_type!r} requires a positive integer {requirement!r}"
        )
```

Add to `backend/app/services/challenge.py`:

```python
CHALLENGE_TARGET_KEYS = {
    ChallengeType.EXERCISE_COUNT.value: "exercise_count",
    ChallengeType.STREAK.value: "days",
    ChallengeType.TIME_SPENT.value: "minutes",
    ChallengeType.ACCURACY.value: "accuracy",
}
BINARY_CHALLENGE_TYPES = frozenset(
    {
        ChallengeType.CHAPTER_COMPLETE.value,
        ChallengeType.COURSE_COMPLETE.value,
    }
)


def _positive_integer(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return None
    return value


def resolve_challenge_target(challenge: Challenge) -> int:
    requirements = challenge.requirements or {}
    if "target" in requirements:
        explicit_target = _positive_integer(requirements["target"])
        if explicit_target is None:
            raise InvalidChallengeDefinitionError(str(challenge.type), "target")
        return explicit_target

    challenge_type = str(challenge.type)
    if challenge_type in BINARY_CHALLENGE_TYPES:
        return 1

    requirement_key = CHALLENGE_TARGET_KEYS.get(challenge_type)
    if requirement_key is None:
        raise InvalidChallengeDefinitionError(challenge_type, "target")

    target = _positive_integer(requirements.get(requirement_key))
    if target is None:
        raise InvalidChallengeDefinitionError(challenge_type, requirement_key)
    return target
```

- [x] **Step 4: Extract default definitions and make initialization incremental**

Move the existing three dictionaries unchanged into:

```python
DEFAULT_CHALLENGE_DEFINITIONS: tuple[dict[str, object], ...] = (
    {
        "code": "FIRST_STEPS",
        "title": "First Steps",
        "description": "Complete your first 5 exercises",
        "type": ChallengeType.EXERCISE_COUNT.value,
        "difficulty": 1,
        "requirements": {"exercise_count": 5},
        "rewards": {"quota_bonus": 10},
    },
    {
        "code": "CHAPTER_MASTER",
        "title": "Chapter Master",
        "description": "Complete a chapter",
        "type": ChallengeType.CHAPTER_COMPLETE.value,
        "difficulty": 2,
        "requirements": {"chapter_id": 1},
        "rewards": {"quota_bonus": 20},
    },
    {
        "code": "STREAK_7",
        "title": "7 Day Streak",
        "description": "Maintain a 7-day learning streak",
        "type": ChallengeType.STREAK.value,
        "difficulty": 3,
        "requirements": {"days": 7},
        "rewards": {"quota_bonus": 50},
    },
)
```

Replace `create_default_challenges` with:

```python
async def create_default_challenges(self, db: AsyncSession) -> None:
    codes = tuple(str(item["code"]) for item in DEFAULT_CHALLENGE_DEFINITIONS)
    result = await db.execute(select(Challenge.code).where(Challenge.code.in_(codes)))
    existing_codes = set(result.scalars().all())

    for definition in DEFAULT_CHALLENGE_DEFINITIONS:
        if definition["code"] not in existing_codes:
            db.add(Challenge(**definition))

    await db.flush()
```

Replace start's nested fallback with:

```python
target_value = resolve_challenge_target(challenge)
```

Do not change start's transaction handling until Task 2.

- [x] **Step 5: Verify target and initialization behavior**

Run:

```powershell
py -3 -m pytest tests/test_challenge_service_governance.py tests/test_challenges.py -q
pyright
```

Expected: target and incremental initialization tests pass; all existing challenge tests and Pyright pass.

- [x] **Step 6: Review and commit Task 1**

```powershell
git diff --check
git add app/services/challenge_errors.py app/services/challenge.py tests/test_challenge_service_governance.py
git commit -m "refactor: define generic challenge targets"
```

## Task 2: Make Challenge State Transitions Request-Owned And Typed

**Files:**
- Modify: `backend/app/services/challenge_errors.py`
- Modify: `backend/app/services/challenge.py`
- Modify: `backend/app/routers/challenges.py`
- Modify: `backend/tests/test_challenge_service_governance.py`
- Modify: `backend/tests/test_challenges.py`

**Interfaces:**
- Produces: `ChallengeNotFoundError`, `ChallengeNotStartedError`, `ChallengeAlreadyCompletedError`, `InvalidProgressDeltaError`.
- Produces: `ChallengeService.get_user_challenge_for_update(...) -> UserChallenge | None`.
- Preserves: start and progress successful response behavior.

- [x] **Step 1: Add failing state, transaction, and Router tests**

Append to `test_challenge_service_governance.py`:

```python
from app.services.challenge_errors import InvalidProgressDeltaError


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
```

Append to `backend/tests/test_challenges.py`:

```python
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_progress_rejects_non_positive_query_values(client, auth_headers):
    for progress in (0, -1):
        response = await client.post(
            f"/api/challenges/99999/progress?progress={progress}",
            headers=auth_headers,
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_unexpected_start_value_error_is_not_mapped_to_bad_request(
    client, auth_headers
):
    with patch(
        "app.routers.challenges.challenge_service.start_challenge",
        new=AsyncMock(side_effect=ValueError("unexpected storage failure")),
    ):
        with pytest.raises(ValueError, match="unexpected storage failure"):
            await client.post("/api/challenges/1/start", headers=auth_headers)
```

- [x] **Step 2: Run focused tests and confirm old commit/validation/error behavior fails**

```powershell
py -3 -m pytest tests/test_challenge_service_governance.py tests/test_challenges.py -q
```

Expected: tests fail because service commits, non-positive progress is accepted until lookup, and Router catches unexpected `ValueError`.

- [x] **Step 3: Add typed state errors**

Extend `challenge_errors.py`:

```python
class ChallengeNotFoundError(ChallengeError):
    def __init__(self, challenge_id: int) -> None:
        super().__init__(f"Challenge {challenge_id} not found")


class ChallengeNotStartedError(ChallengeError):
    def __init__(self) -> None:
        super().__init__("Challenge not started")


class ChallengeAlreadyCompletedError(ChallengeError):
    def __init__(self) -> None:
        super().__init__("Challenge already completed")


class InvalidProgressDeltaError(ChallengeError):
    def __init__(self) -> None:
        super().__init__("Progress delta must be a positive integer")
```

Use these exact exceptions in `start_challenge` and `update_progress` instead of `ValueError`.

- [x] **Step 4: Move state persistence to flush and lock progress rows**

Add:

```python
async def get_user_challenge_for_update(
    self, db: AsyncSession, user_id: str, challenge_id: int
) -> UserChallenge | None:
    result = await db.execute(
        select(UserChallenge)
        .where(
            UserChallenge.user_id == user_id,
            UserChallenge.challenge_id == challenge_id,
        )
        .with_for_update()
    )
    return result.scalar_one_or_none()
```

In `start_challenge`, replace commit with:

```python
db.add(user_challenge)
await db.flush()
await db.refresh(user_challenge)
```

At the beginning of `update_progress`:

```python
if progress_delta <= 0:
    raise InvalidProgressDeltaError

user_challenge = await self.get_user_challenge_for_update(
    db, user.id, challenge_id
)
```

Replace its commit with `await db.flush()` followed by refresh. Keep the completed early return and current reward implementation until Task 3.

- [x] **Step 5: Map exact errors and validate the Query parameter**

Import `Query` and the four request-state errors in `routers/challenges.py`. Change the progress parameter to:

```python
progress: int = Query(default=1, ge=1)
```

Use these exact mappings and remove broad `except ValueError`:

```python
except (ChallengeNotFoundError, ChallengeAlreadyCompletedError) as error:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(error),
    ) from error
```

```python
except (ChallengeNotStartedError, InvalidProgressDeltaError) as error:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(error),
    ) from error
```

Remove the unused logger.

- [x] **Step 6: Verify state and API behavior**

```powershell
py -3 -m pytest tests/test_challenge_service_governance.py tests/test_challenges.py tests/test_stats.py -q
pyright
```

Expected: all selected tests pass; no service `commit()` remains except none in `challenge.py`; Pyright is clean.

- [x] **Step 7: Review and commit Task 2**

```powershell
rg -n "commit\(|except ValueError" app/services/challenge.py app/routers/challenges.py
git diff --check
git add app/services/challenge_errors.py app/services/challenge.py app/routers/challenges.py tests/test_challenge_service_governance.py tests/test_challenges.py
git commit -m "refactor: make challenge transitions request owned"
```

Expected: the search has no matches and Task 2 files are committed.

## Task 3: Make Completion Rewards Atomic And Retry-Safe

**Files:**
- Modify: `backend/app/services/challenge.py`
- Modify: `backend/tests/test_challenge_service_governance.py`

**Interfaces:**
- Consumes: `CoreService.earn_cores(...)`.
- Produces: one `bonus` transaction with `reference_type="challenge"` and `reference_id=UserChallenge.id` on first completion.
- Guarantees: a sequential completed retry does not change progress, completion time, balance, total earned, or transaction count.

- [x] **Step 1: Add failing ledger and retry tests**

Append imports and tests:

```python
from app.models.core_transaction import CoreTransaction
from app.services.core_service import CoreService


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
```

- [x] **Step 2: Add a failing atomic rollback test**

```python
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
```

Also import `UserChallenge` in the test module.

- [x] **Step 3: Run the reward tests and confirm direct balance mutation fails the ledger contract**

```powershell
py -3 -m pytest tests/test_challenge_service_governance.py -q
```

Expected: ledger/total-earned assertions fail because the old `_apply_rewards` only mutates `user.cores`.

- [x] **Step 4: Delegate rewards to CoreService**

Import `CoreService` and replace `_apply_rewards` with:

```python
async def _apply_rewards(
    self,
    db: AsyncSession,
    user_challenge: UserChallenge,
) -> None:
    challenge = await self.get_challenge_by_id(db, user_challenge.challenge_id)
    if challenge is None:
        raise ChallengeNotFoundError(user_challenge.challenge_id)

    quota_bonus = (challenge.rewards or {}).get("quota_bonus", 0)
    if not isinstance(quota_bonus, int) or isinstance(quota_bonus, bool):
        raise InvalidChallengeDefinitionError(challenge.type, "quota_bonus")
    if quota_bonus <= 0:
        return

    await CoreService(db).earn_cores(
        user_id=user_challenge.user_id,
        amount=quota_bonus,
        category="bonus",
        reference_type="challenge",
        reference_id=user_challenge.id,
        description=f"Challenge completed: {challenge.code}",
    )
```

Call it with the locked `user_challenge` after setting completed state. Remove the now-unused direct `User` reward mutation and `db.add(user)`.

- [x] **Step 5: Verify reward consistency and adjacent core behavior**

```powershell
py -3 -m pytest tests/test_challenge_service_governance.py tests/test_challenges.py tests/test_cores.py tests/test_checkin.py -q
pyright
```

Expected: all selected tests pass, including exact one-transaction retry behavior and rollback.

- [x] **Step 6: Review and commit Task 3**

```powershell
git diff --check
git add app/services/challenge.py tests/test_challenge_service_governance.py
git commit -m "fix: make challenge rewards atomic and ledger backed"
```

## Task 4: Move Challenge Response Assembly To Pure Mappers

**Files:**
- Create: `backend/app/services/challenge_responses.py`
- Create: `backend/tests/test_challenge_responses.py`
- Modify: `backend/app/schemas/challenge.py`
- Modify: `backend/app/routers/challenges.py`
- Modify: `backend/tests/test_challenges.py`

**Interfaces:**
- Produces: `ChallengeProgressResponse`.
- Produces: `build_user_challenges_response`, `build_user_challenge_response`, `build_challenge_progress_response`.
- Preserves: all existing successful JSON field names and values.

- [x] **Step 1: Add failing pure mapper tests**

Create `backend/tests/test_challenge_responses.py`:

```python
from datetime import datetime, timezone

from app.models.challenge import Challenge, ChallengeType
from app.models.user_challenge import UserChallenge, UserChallengeStatus
from app.services.challenge_responses import (
    build_challenge_progress_response,
    build_user_challenge_response,
    build_user_challenges_response,
)


def completed_record() -> UserChallenge:
    challenge = Challenge(
        id=7,
        code="MAPPER_TEST",
        title="Mapper test",
        type=ChallengeType.EXERCISE_COUNT.value,
        requirements={"target": 2},
        rewards={},
        difficulty=2,
        is_active=True,
        min_level=0,
    )
    record = UserChallenge(
        id="record-id",
        user_id="user-id",
        challenge_id=7,
        status=UserChallengeStatus.COMPLETED.value,
        current_progress=2,
        target_value=2,
        attempts=1,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )
    record.challenge = challenge
    return record


def test_build_user_challenge_response_preserves_contract() -> None:
    response = build_user_challenge_response(completed_record())
    assert response.is_completed is True
    assert response.user_challenge.id == "record-id"
    assert response.user_challenge.current_progress == 2


def test_build_user_challenges_response_includes_detail_and_counts() -> None:
    response = build_user_challenges_response([completed_record()])
    assert response.total == 1
    assert response.completed_count == 1
    assert response.challenges[0].challenge.code == "MAPPER_TEST"


def test_build_progress_response_preserves_exact_fields() -> None:
    response = build_challenge_progress_response(completed_record())
    assert response.model_dump() == {
        "challenge_id": 7,
        "current_progress": 2,
        "target_value": 2,
        "is_completed": True,
        "status": "completed",
    }
```

- [x] **Step 2: Run mapper tests and confirm the module is absent**

```powershell
py -3 -m pytest tests/test_challenge_responses.py -q
```

Expected: collection fails with `ModuleNotFoundError` for `challenge_responses`.

- [x] **Step 3: Add the progress schema and pure mappers**

Add to `schemas/challenge.py`:

```python
class ChallengeProgressResponse(BaseModel):
    challenge_id: int
    current_progress: int
    target_value: int
    is_completed: bool
    status: str
```

Create `services/challenge_responses.py`:

```python
from app.models.user_challenge import UserChallenge, UserChallengeStatus
from app.schemas.challenge import (
    ChallengeProgressResponse,
    ChallengeSummary,
    UserChallengeDetail,
    UserChallengeResponse,
    UserChallengesResponse,
    UserChallengeSummary,
)


def _build_user_challenge_detail(record: UserChallenge) -> UserChallengeDetail:
    if record.challenge is None:
        raise ValueError("User challenge is missing its challenge relationship")
    return UserChallengeDetail(
        id=record.id,
        user_id=record.user_id,
        challenge_id=record.challenge_id,
        status=record.status,
        current_progress=record.current_progress,
        target_value=record.target_value,
        attempts=record.attempts,
        started_at=record.started_at,
        completed_at=record.completed_at,
        challenge=ChallengeSummary.model_validate(record.challenge),
    )


def build_user_challenges_response(
    records: list[UserChallenge],
) -> UserChallengesResponse:
    details = [
        _build_user_challenge_detail(record)
        for record in records
        if record.challenge is not None
    ]
    completed_count = sum(
        record.status == UserChallengeStatus.COMPLETED.value for record in records
    )
    return UserChallengesResponse(
        challenges=details,
        total=len(records),
        completed_count=completed_count,
    )


def build_user_challenge_response(record: UserChallenge) -> UserChallengeResponse:
    return UserChallengeResponse(
        user_challenge=UserChallengeSummary.model_validate(record),
        is_completed=record.status == UserChallengeStatus.COMPLETED.value,
    )


def build_challenge_progress_response(
    record: UserChallenge,
) -> ChallengeProgressResponse:
    return ChallengeProgressResponse(
        challenge_id=record.challenge_id,
        current_progress=record.current_progress,
        target_value=record.target_value,
        is_completed=record.status == UserChallengeStatus.COMPLETED.value,
        status=record.status,
    )
```

- [x] **Step 4: Replace Router response assembly**

Import `ChallengeProgressResponse` and the three mapper functions. Replace the user-list body after the service call with:

```python
return build_user_challenges_response(user_challenges)
```

Replace the successful start response with:

```python
return build_user_challenge_response(user_challenge)
```

Set `response_model=ChallengeProgressResponse` on the progress endpoint and replace its successful dictionary with:

```python
return build_challenge_progress_response(user_challenge)
```

Remove imports used only by the deleted manual assembly, list loops, string status comparisons, dictionary assembly, and logging.

- [x] **Step 5: Add API response-model assertions and run regressions**

Extend `test_challenges.py`:

```python
from app.models.challenge import Challenge, ChallengeType


@pytest.mark.asyncio
async def test_successful_progress_preserves_exact_response_contract(
    client, auth_headers, db_session
):
    challenge = Challenge(
        code="API_PROGRESS",
        title="API progress",
        type=ChallengeType.EXERCISE_COUNT.value,
        requirements={"target": 2},
        rewards={},
    )
    db_session.add(challenge)
    await db_session.commit()
    await db_session.refresh(challenge)
    start_response = await client.post(
        f"/api/challenges/{challenge.id}/start", headers=auth_headers
    )
    assert start_response.status_code == 200

    response = await client.post(
        f"/api/challenges/{challenge.id}/progress?progress=1",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == {
        "challenge_id": challenge.id,
        "current_progress": 1,
        "target_value": 2,
        "is_completed": False,
        "status": "in_progress",
    }
```

Run:

```powershell
py -3 -m pytest tests/test_challenge_responses.py tests/test_challenges.py tests/test_challenge_service_governance.py tests/test_stats.py -q
pyright
```

Expected: mapper, API, service, and stats tests pass; Pyright is clean.

- [x] **Step 6: Review and commit Task 4**

```powershell
git diff --check
git add app/services/challenge_responses.py app/schemas/challenge.py app/routers/challenges.py tests/test_challenge_responses.py tests/test_challenges.py
git commit -m "refactor: isolate generic challenge responses"
```

## Task 5: Validate, Document, And Maintain The Completed 3A Batch

**Files:**
- Modify: `docs/superpowers/specs/2026-07-15-backend-learning-oriented-governance-design.md`
- Modify: `docs/superpowers/plans/2026-07-16-challenge-state-reward-governance.md`

**Interfaces:**
- Consumes: Tasks 1-4.
- Produces: fresh full-suite, type, startup, live-route, CodeGraph, review, and maintenance evidence.

- [x] **Step 1: Run the full backend gate from the repository root**

```powershell
py -3 -m pytest backend/tests -q -rs
pyright -p backend/pyrightconfig.json
```

Expected: every backend test passes with no skipped section; Pyright reports `0 errors, 0 warnings, 0 informations`.

- [x] **Step 2: Run scope and quality searches**

```powershell
rg -n "commit\(|except ValueError|user\.cores \+=" backend/app/services/challenge.py backend/app/routers/challenges.py
rg -n "ChallengeNotFoundError|ChallengeNotStartedError|ChallengeAlreadyCompletedError|InvalidProgressDeltaError|InvalidChallengeDefinitionError" backend/app backend/tests
rg -n "challenge_path|mastery" backend/app/services/challenge.py backend/app/routers/challenges.py
git diff --check
```

Expected: the first and third searches have no matches; every typed error has a producer and test/Router consumer; diff check is clean.

Complete the mandatory DRY, dependency direction, naming, magic-value, function-length, dead-code, and type-safety review. Confirm no database, frontend, Arena, Mastery, or ChallengeSession file changed.

- [x] **Step 3: Start FastAPI and Next.js and request live contracts**

From the isolated worktree root, verify ports are free, then start both services with hidden windows and log redirection:

```powershell
$root = (Resolve-Path '.').Path
$commonGit = [IO.Path]::GetFullPath((git rev-parse --git-common-dir))
$mainRoot = [IO.Path]::GetDirectoryName($commonGit)
$logDir = Join-Path $root '.run_logs'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$env:SECRET_KEY = 'challenge-governance-smoke-secret-key-32-chars'
$env:DATABASE_URL = 'sqlite+aiosqlite:///./challenge_governance_smoke.db'
$backend = Start-Process -FilePath 'py' -ArgumentList '-3','-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory (Join-Path $root 'backend') -RedirectStandardOutput (Join-Path $logDir 'challenge-backend.out.log') -RedirectStandardError (Join-Path $logDir 'challenge-backend.err.log') -WindowStyle Hidden -PassThru
$next = Join-Path $mainRoot 'frontend/node_modules/.bin/next.CMD'
$frontend = Start-Process -FilePath $next -ArgumentList 'dev','--port','3000' -WorkingDirectory (Join-Path $root 'frontend') -RedirectStandardOutput (Join-Path $logDir 'challenge-frontend.out.log') -RedirectStandardError (Join-Path $logDir 'challenge-frontend.err.log') -WindowStyle Hidden -PassThru
```

Request and record:

```text
GET  /health                                      -> 200
GET  /                                            -> frontend 200 after compile
POST /api/auth/register                           -> 201 bearer token
GET  /api/challenges                              -> 200
GET  /api/challenges/user/me                      -> 200
POST /api/challenges/99999/start                  -> 400 typed not-found detail
POST /api/challenges/99999/progress?progress=0    -> 422
```

Use this request script after both listeners are ready:

```powershell
$health = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8000/health'
$frontendPage = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:3000/'
$stamp = Get-Date -Format 'yyyyMMddHHmmss'
$registration = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/api/auth/register' -ContentType 'application/json' -Body (@{email="challenge-$stamp@example.com";username="challengesmoke$stamp";password='Password123'} | ConvertTo-Json)
$headers = @{Authorization="Bearer $($registration.access_token)"}
$challengeList = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8000/api/challenges'
$userChallenges = Invoke-WebRequest -UseBasicParsing -Headers $headers 'http://127.0.0.1:8000/api/challenges/user/me'
$startStatus = 0
try { Invoke-WebRequest -UseBasicParsing -Method Post -Headers $headers 'http://127.0.0.1:8000/api/challenges/99999/start' | Out-Null } catch { $startStatus = [int]$_.Exception.Response.StatusCode }
$progressStatus = 0
try { Invoke-WebRequest -UseBasicParsing -Method Post -Headers $headers 'http://127.0.0.1:8000/api/challenges/99999/progress?progress=0' | Out-Null } catch { $progressStatus = [int]$_.Exception.Response.StatusCode }
if ($health.StatusCode -ne 200 -or $frontendPage.StatusCode -ne 200 -or $challengeList.StatusCode -ne 200 -or $userChallenges.StatusCode -ne 200 -or $startStatus -ne 400 -or $progressStatus -ne 422) { throw 'Live challenge contract check failed' }
```

Inspect the four redirected logs, then stop only verified listeners:

```powershell
$backendPid = (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction Stop).OwningProcess
$frontendPid = (Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction Stop).OwningProcess
Get-CimInstance Win32_Process -Filter "ProcessId=$backendPid OR ProcessId=$frontendPid" | Select-Object ProcessId,Name,CommandLine
Stop-Process -Id $backendPid,$frontendPid -Force
Start-Sleep -Seconds 2
if (Get-NetTCPConnection -LocalPort 8000,3000 -State Listen -ErrorAction SilentlyContinue) { throw 'Smoke-test services are still listening' }
```

- [x] **Step 4: Synchronize an explicit worktree CodeGraph index**

```powershell
npx codegraph init .
npx codegraph sync .
npx codegraph impact -p . ChallengeService
npx codegraph impact -p . CoreService
npx codegraph query -p . build_challenge_progress_response
```

Expected: generic ChallengeService callers are challenge Router/tests, CoreService records the new reward edge, and the response mapper is used by the challenge Router. Arena and Mastery source files are unchanged.

- [x] **Step 5: Record the 3A learning note**

Append to the governance design with exact fresh counts:

```markdown
## 通用挑战状态与奖励第三批 A 实施记录

- 重构前：通用 ChallengeService 内部提交事务、用裸 ValueError 表达状态失败、直接修改智核余额且不写账本，Router 手工拼装响应。
- 重构后：类型化错误描述状态机，目标按 ChallengeType 解析，行锁更新已存在进度，请求依赖统一提交，CoreService 在同一事务写余额/累计收入/账本，纯映射模块构造响应。
- 幂等边界：重复开始进行中挑战返回同一记录；完成后的顺序重试不改变完成时间或重复发奖励。并发首次启动唯一性明确留给独立数据库迁移批次。
- 证明：目标、状态、回滚、账本、映射、API、完整后端测试、Pyright、双服务启动、真实路由和 CodeGraph 影响检查均通过。
```

- [x] **Step 6: Perform final review and update completion evidence**

Review the exact git range against the design. Record red-green evidence, focused/full counts, Pyright, HTTP statuses, CodeGraph edges, commits, deviations, and residual risks in `## Completion Evidence`. Resolve all Critical and Important findings.

- [x] **Step 7: Commit completion records**

```powershell
git add docs/superpowers/specs/2026-07-15-backend-learning-oriented-governance-design.md docs/superpowers/plans/2026-07-16-challenge-state-reward-governance.md
git commit -m "docs: record generic challenge governance batch"
```

## Completion Evidence

### Implementation And TDD

- Implementation range: `aa2cec2..890594d`; commits `be1473b`, `6c990ff`, `8c9a58e`, `c1c8a56`, `ecfe7be`, `2a1c06d`, and `890594d`.
- Task 1 red: target resolver and challenge error module were absent. Green: target/default initialization suite and existing challenge tests passed; Pyright was clean.
- Task 2 red: 6 failures proved service commits, non-positive progress acceptance, missing Query validation, and broad `ValueError` mapping. Green: 68 focused tests passed and Pyright was clean.
- Task 3 red: 2 failures proved missing cumulative earnings/ledger writes and missing atomic reward delegation. Green: 54 challenge/core/check-in tests passed and Pyright was clean.
- Task 4 red: mapper test collection failed because `challenge_responses` was absent. Green: 78 mapper/API/service/stats tests passed after preserving the pre-existing Arena response tests; Pyright was clean.
- Review repair red: temporarily restoring the old completed-restart `ValueError` made the typed-error regression test fail. Green: 38 challenge service/API tests passed after restoring `ChallengeAlreadyCompletedError`.

### Final Gates

- Full backend: `py -3 -m pytest backend/tests -q -rs` -> `636 passed in 79.48s`; no skipped section was reported.
- Type safety: `pyright -p backend/pyrightconfig.json` -> `0 errors, 0 warnings, 0 informations`.
- Static scope: no `commit(`, broad `except ValueError`, or direct `user.cores +=` remains in generic challenge service/router; no Arena `challenge_path` or Mastery reference was introduced there.
- Quality review: DRY response construction, Router -> Service -> CoreService dependency direction, descriptive names, named reward metadata, functions under the approximate 40-effective-line limit, typed errors, and dead-code consumers all passed review.
- Changed source scope contains only generic challenge service/errors/responses, challenge Router/schema, and related tests. No frontend, database, migration, Arena source, Mastery source, or `ChallengeSession` file changed.
- Database maintenance: no schema or data migration was required; the smoke database initialized at the existing Alembic revision.
- `git diff --check aa2cec2..HEAD` passed after normalizing two mixed-line-ending blank lines in the challenge Router.

### Startup And Live Contracts

- FastAPI started on `127.0.0.1:8000`; Next.js 15.5.18 started on `127.0.0.1:3000`, compiled `/` in 9.2 seconds, and returned 200.
- Live results: `GET /health` 200; `GET /` 200; `POST /api/auth/register` 201 with a bearer token; `GET /api/challenges` 200; authenticated `GET /api/challenges/user/me` 200.
- Error results: authenticated missing challenge start returned 400 with `Challenge 99999 not found`; `progress=0` returned FastAPI validation 422.
- Both listener processes were identified by command line and stopped; ports 8000 and 3000 no longer listened.

### CodeGraph And Review

- Worktree-local CodeGraph initialized 479 files with 6,629 nodes and 14,775 edges, then synchronized the final test changes.
- `CoreService` impact includes `backend/app/services/challenge.py::_apply_rewards`; `build_challenge_progress_response` is imported by the challenge Router and its tests.
- `ChallengeService` is also the name of the separate `ChallengeSession` scoring class, so name-only impact output lists both; file-level edges distinguish the generic service and no `challenge_service.py` source changed.
- Final read-only review found one Important missing completed-restart typed-error test and one whitespace gate issue; both were fixed and reverified. No Critical or remaining Important findings.

### Deviations And Residual Risk

- `backend/tests/test_challenge_responses.py` already contained Batch 1 Arena mapper tests although the plan called it a new file. Those tests were preserved byte-for-byte and generic challenge mapper tests were appended.
- The isolated frontend initially lacked `node_modules`. A frozen pnpm install was blocked by the existing supply-chain policy after partial linking, so smoke validation used a worktree junction to the main checkout's already-installed dependencies; no lockfile or frontend source changed.
- Sequential retries are covered. Concurrent first-start uniqueness remains intentionally deferred to a `(user_id, challenge_id)` database constraint migration, and SQLite tests do not prove production row-lock isolation.
- Existing `get_db` behavior logs expected HTTP 400/422 exceptions as transaction rollback errors; changing that operational logging is outside this batch.

## Plan Self-Review

- Spec coverage: Tasks 1-4 cover all target, state, typed-error, transaction, reward, idempotency, initialization, response, and HTTP requirements. Task 5 covers every validation and maintenance gate.
- Scope: generic Challenge only; Arena, Mastery, ChallengeSession, frontend, and schema migrations remain excluded.
- Type consistency: error names, mapper names, response schema, reference fields, target keys, and service signatures match the design.
- TDD order: every production behavior change has a preceding test that fails on the current implementation.
- Transaction proof: tests cover no service commits, one ledger reward, completed retry, and rollback after reward mutation.
- Placeholder scan: no unfinished implementation instruction remains.

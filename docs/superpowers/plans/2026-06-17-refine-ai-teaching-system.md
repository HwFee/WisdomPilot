# Refine AI Teaching System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor WisdomPilot so challenge grading is backend-authoritative, AI assistance is policy-controlled, and oversized challenge-path files are split without changing the current user-facing flow.

**Architecture:** Keep deterministic course, judge, progress, reward, ranking, and analytics behavior as the system backbone. Add a small AI policy boundary for learner-facing AI features, then decompose the challenge path by responsibility while preserving `/api/learning-path/challenge/*` response compatibility.

**Tech Stack:** FastAPI, SQLAlchemy async sessions, pytest/httpx backend tests, Next.js/React/TypeScript frontend, pnpm tests/build, CodeGraph.

---

change: refine-ai-teaching-system
design-doc: docs/superpowers/specs/2026-06-17-refine-ai-teaching-system-design.md
base-ref: 3f1f3fe7754ab3aae60fe473103034c36d7eb6d6

---

## Scope And Guardrails

Do not archive this OpenSpec change. Final verification is reserved for the original reviewer in this Codex thread.

Do not remove or rename existing frontend-facing challenge endpoints:

- `POST /api/learning-path/challenge/infinite/start`
- `GET /api/learning-path/challenge/progress`
- `POST /api/learning-path/challenge/submit`
- `POST /api/learning-path/challenge/save-code`
- `POST /api/learning-path/challenge/switch`
- `POST /api/learning-path/challenge/append`
- `GET /api/learning-path/challenge/exercise/{exercise_id}`
- `GET /api/learning-path/challenge/recent`

Do not redesign arena UI visuals. Frontend work is extraction only.

Do not implement broad AI curriculum generation. Reflection prompts are optional after the backend authority and refactor tasks pass.

Use CodeGraph before changing symbols and run `npx codegraph sync` or `npx codegraph index` after code movement.

## File Structure

Expected backend files to create:

- `backend/app/services/ai_policy.py`
  - Contains small policy objects/constants for learner-facing AI features.
- `backend/app/services/challenge_path/__init__.py`
  - Exports focused challenge services.
- `backend/app/services/challenge_path/selection.py`
  - Exercise selection, fixed first exercises, append behavior.
- `backend/app/services/challenge_path/progress.py`
  - Progress records, save code, switch, unlock, exercise retrieval.
- `backend/app/services/challenge_path/submission.py`
  - Backend-authoritative final challenge submission.
- `backend/app/services/challenge_path/rewards.py`
  - Stars, tiers, cores, tier transactions, profile stats, wrong-question collection.
- `backend/app/services/challenge_path/responses.py`
  - API response mappers.

Expected backend files to modify:

- `backend/app/services/arena_infinite.py`
  - Gradually becomes compatibility facade or thin coordinator.
- `backend/app/routers/learning_path.py`
  - Challenge endpoints delegate to focused services.
- `backend/app/routers/ai.py`
  - Hint route uses `ai_policy.py`; general chat classification documented or policy-routed.
- `backend/app/services/ai.py`
  - Keep prompts pedagogically bounded; avoid expanding scope.
- `backend/app/routers/code.py` or existing code execution service only if needed for backend-authoritative judging.

Expected backend tests:

- `backend/tests/test_learning_path_challenge.py`
- `backend/tests/test_arena_submission_result.py`
- Create `backend/tests/test_challenge_authoritative_submission.py`
- Create `backend/tests/test_ai_policy.py`

Expected frontend files to modify or create:

- `frontend/app/arena/_components/arena-content.tsx`
- Create `frontend/app/arena/use-arena-submit.ts`
- Create `frontend/app/arena/use-arena-append.ts`
- `frontend/lib/api/code.ts` only if API types need tightening.
- Existing frontend tests under `frontend/__tests__/` or a new focused arena test.

## Task 1: Lock Current Challenge API Shapes

**Files:**
- Modify: `backend/tests/test_learning_path_challenge.py`

- [x] **Step 1: Inspect current challenge flow with CodeGraph**

Run:

```powershell
npx codegraph context "learning_path challenge progress submit switch save-code append arena_infinite ChallengePathService"
```

Expected: output references `backend/app/routers/learning_path.py` and `backend/app/services/arena_infinite.py`.

- [x] **Step 2: Add response-shape tests for save/switch/append/detail**

Append focused assertions to `backend/tests/test_learning_path_challenge.py`. Use existing fixtures (`client`, `auth_headers`, `db_session`) and follow existing async style.

Add tests that create verified exercises and progress records, then assert stable response fields:

```python
@pytest.mark.asyncio
async def test_save_code_preserves_existing_response_shape(client: AsyncClient, auth_headers: dict, db_session):
    exercise = Exercise(
        content={"title": "保存代码题", "text": "保存代码", "code_template": "print('x')"},
        type="programming",
        difficulty=2,
        is_verified=True,
        test_cases=[{"input": "", "output": "x"}],
    )
    db_session.add(exercise)
    await db_session.commit()
    await db_session.refresh(exercise)

    token = auth_headers["Authorization"].split(" ")[1]
    user_id = decode_token(token)["sub"]
    db_session.add(ArenaExerciseProgress(
        user_id=user_id,
        exercise_id=exercise.id,
        exercise_index=0,
        is_unlocked=True,
    ))
    await db_session.commit()

    response = await client.post(
        "/api/learning-path/challenge/save-code",
        headers=auth_headers,
        json={"exercise_id": exercise.id, "code": "print('saved')", "language": "python"},
    )

    assert response.status_code == 200
    assert response.json() == {"success": True}
```

Also add similar tests for:

- `GET /api/learning-path/challenge/exercise/{id}` includes `exercise`, `exercise_index`, `is_unlocked`, `is_completed`, `is_correct`, `saved_code`, `current_language`, `total_exercises`.
- `POST /api/learning-path/challenge/switch` returns compatible progress fields when target index is unlocked.
- `POST /api/learning-path/challenge/append` returns `new_exercise_ids` and `count`.

- [x] **Step 3: Run the characterization tests**

Run:

```powershell
cd backend
pytest tests/test_learning_path_challenge.py -q
```

Expected: current tests pass before refactor. If a new characterization assertion fails because current behavior is different, adjust the test to current behavior unless it conflicts with OpenSpec requirements.

- [x] **Step 4: Commit Task 1**

```powershell
git add backend/tests/test_learning_path_challenge.py
git commit -m "test: characterize challenge path api shapes"
```

## Task 2: Prove Client Results Cannot Be Trusted

**Files:**
- Create: `backend/tests/test_challenge_authoritative_submission.py`
- Later modify: `backend/app/services/challenge_path/submission.py`

- [x] **Step 1: Write failing forged-result test**

Create `backend/tests/test_challenge_authoritative_submission.py`:

```python
"""Tests that challenge rewards require backend-authoritative judging."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.exercise import Exercise
from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.user_arena import UserArenaProfile
from app.utils.security import decode_token


@pytest.mark.asyncio
async def test_forged_client_passing_results_do_not_award_progress(
    client: AsyncClient,
    auth_headers: dict,
    db_session,
    monkeypatch,
):
    exercise = Exercise(
        content={"title": "权威判题", "text": "输出 42", "code_template": "print(0)"},
        type="programming",
        difficulty=3,
        is_verified=True,
        test_cases=[{"input": "", "output": "42"}],
    )
    db_session.add(exercise)
    await db_session.commit()
    await db_session.refresh(exercise)

    user_id = decode_token(auth_headers["Authorization"].split(" ")[1])["sub"]
    progress = ArenaExerciseProgress(
        user_id=user_id,
        exercise_id=exercise.id,
        exercise_index=0,
        is_unlocked=True,
    )
    db_session.add(progress)
    await db_session.commit()

    async def fake_backend_judge(*args, **kwargs):
        return {
            "passed_count": 0,
            "total_count": 1,
            "results": [
                {"passed": False, "input": "", "expected": "42", "actual": "0", "message": "Wrong Answer"}
            ],
        }

    monkeypatch.setattr(
        "app.services.challenge_path.submission.run_authoritative_judge",
        fake_backend_judge,
        raising=False,
    )

    response = await client.post(
        "/api/learning-path/challenge/submit",
        headers=auth_headers,
        json={
            "exercise_id": exercise.id,
            "code": "print(0)",
            "language": "python",
            "test_results": [
                {"passed": True, "input": "", "expected": "42", "actual": "42"}
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_correct"] is False
    assert data["stars_earned"] <= 0

    await db_session.refresh(progress)
    assert progress.is_correct is False

    profile_result = await db_session.execute(
        select(UserArenaProfile).where(UserArenaProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()
    assert profile is None or profile.stars == 0
```

- [x] **Step 2: Run it and verify it fails for the right reason**

Run:

```powershell
cd backend
pytest tests/test_challenge_authoritative_submission.py -q
```

Expected before implementation: FAIL because `app.services.challenge_path.submission` does not exist or forged results are still trusted.

- [x] **Step 3: Commit failing test only if project convention allows red commits**

If using strict TDD in one commit, skip commit until implementation passes. If committing red tests is allowed by the executing agent, use:

```powershell
git add backend/tests/test_challenge_authoritative_submission.py
git commit -m "test: require backend-authoritative challenge submission"
```

## Task 3: Add AI Policy Service And Tests

**Files:**
- Create: `backend/app/services/ai_policy.py`
- Create: `backend/tests/test_ai_policy.py`
- Modify: `backend/app/routers/ai.py`

- [ ] **Step 1: Write AI policy tests**

Create `backend/tests/test_ai_policy.py`:

```python
from app.services.ai_policy import (
    AIFeature,
    AI_HINT_COSTS,
    get_ai_policy,
)


def test_challenge_hint_policy_costs_match_existing_behavior():
    assert get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level="light").cost == 1
    assert get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level="medium").cost == 3
    assert get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level="deep").cost == 5


def test_cached_challenge_hint_is_free():
    policy = get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level="deep", cached=True)
    assert policy.cost == 0
    assert policy.cached is True


def test_general_chat_policy_is_explicitly_classified():
    policy = get_ai_policy(AIFeature.GENERAL_CHAT)
    assert policy.feature == AIFeature.GENERAL_CHAT
    assert policy.demo_scope in {"controlled", "out_of_demo_scope"}


def test_unknown_hint_level_falls_back_to_light_cost():
    assert get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level="unknown").cost == AI_HINT_COSTS["light"]
```

- [ ] **Step 2: Run tests and verify failure**

```powershell
cd backend
pytest tests/test_ai_policy.py -q
```

Expected: FAIL because `app.services.ai_policy` does not exist.

- [ ] **Step 3: Implement minimal policy module**

Create `backend/app/services/ai_policy.py`:

```python
from dataclasses import dataclass
from enum import Enum


AI_HINT_COSTS = {
    "light": 1,
    "medium": 3,
    "deep": 5,
}


class AIFeature(str, Enum):
    CHALLENGE_HINT = "challenge_hint"
    GENERAL_CHAT = "general_chat"
    REFLECTION_PROMPT = "reflection_prompt"


@dataclass(frozen=True)
class AIPolicy:
    feature: AIFeature
    cost: int
    cached: bool = False
    admin_only: bool = False
    demo_scope: str = "controlled"


def get_ai_policy(
    feature: AIFeature,
    *,
    hint_level: str = "light",
    cached: bool = False,
) -> AIPolicy:
    if feature == AIFeature.CHALLENGE_HINT:
        cost = 0 if cached else AI_HINT_COSTS.get(hint_level, AI_HINT_COSTS["light"])
        return AIPolicy(feature=feature, cost=cost, cached=cached, demo_scope="controlled")

    if feature == AIFeature.GENERAL_CHAT:
        return AIPolicy(feature=feature, cost=0, demo_scope="out_of_demo_scope")

    if feature == AIFeature.REFLECTION_PROMPT:
        return AIPolicy(feature=feature, cost=0, demo_scope="controlled")

    raise ValueError(f"Unsupported AI feature: {feature}")
```

- [ ] **Step 4: Route existing hint cost through policy**

Modify `backend/app/routers/ai.py`:

- import `AIFeature`, `get_ai_policy`
- replace direct `HINT_COSTS.get(hint_level, 1)` lookups with `get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level=hint_level, cached=...)`
- keep the module-level `HINT_COSTS` only as a compatibility alias if existing tests import it

Implementation sketch:

```python
from app.services.ai_policy import AIFeature, AI_HINT_COSTS, get_ai_policy

HINT_COSTS = AI_HINT_COSTS
```

In `get_cached_hint`, return policy cost:

```python
if cached:
    policy = get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level=hint_level, cached=True)
    return {"cached": True, "hint": cached.hint_content, "cost": policy.cost}

policy = get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level=hint_level)
return {"cached": False, "cost": policy.cost}
```

In `stream_exercise_hint`, compute:

```python
policy = get_ai_policy(AIFeature.CHALLENGE_HINT, hint_level=request.hint_level)
cost = policy.cost
```

- [ ] **Step 5: Run AI policy and existing AI tests**

```powershell
cd backend
pytest tests/test_ai_policy.py tests/test_ai.py tests/test_quota.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit Task 3**

```powershell
git add backend/app/services/ai_policy.py backend/app/routers/ai.py backend/tests/test_ai_policy.py
git commit -m "feat: add controlled ai policy boundary"
```

## Task 4: Create Challenge Path Package Skeleton

**Files:**
- Create: `backend/app/services/challenge_path/__init__.py`
- Create: `backend/app/services/challenge_path/responses.py`
- Create: `backend/app/services/challenge_path/selection.py`
- Create: `backend/app/services/challenge_path/progress.py`
- Create: `backend/app/services/challenge_path/rewards.py`
- Create: `backend/app/services/challenge_path/submission.py`

- [ ] **Step 1: Create package exports**

Create `backend/app/services/challenge_path/__init__.py`:

```python
"""Focused services for the challenge path."""

from .progress import ChallengeProgressService
from .rewards import ChallengeRewardService
from .selection import ChallengeSelectionService
from .submission import ChallengeSubmissionService

__all__ = [
    "ChallengeProgressService",
    "ChallengeRewardService",
    "ChallengeSelectionService",
    "ChallengeSubmissionService",
]
```

- [ ] **Step 2: Create response mapper placeholders with real behavior moved first**

Create `backend/app/services/challenge_path/responses.py` with pure mapping helpers. Start with duplicated mapping logic from `learning_path.py`, then route tests will protect cleanup:

```python
from app.models.exercise import Exercise


def map_exercise_summary(exercise: Exercise, index: int | None = None) -> dict:
    content = exercise.content or {}
    fallback_title = f"题目 {index + 1}" if index is not None else f"题目 {exercise.id}"
    return {
        "id": exercise.id,
        "z_id": exercise.z_id,
        "title": content.get("title", "") or (content.get("text", "")[:50] if content.get("text") else fallback_title),
        "type": exercise.type,
        "difficulty": exercise.difficulty,
        "knowledge_points": exercise.knowledge_points or [],
        "content": {
            "text": content.get("text", ""),
            "title": content.get("title", ""),
            "options": content.get("options", []),
            "code_template": content.get("code_template"),
            "description": content.get("description"),
            "samples": content.get("samples", []),
        },
        "test_cases": exercise.test_cases if exercise.type == "programming" else None,
    }
```

- [ ] **Step 3: Create service shells that delegate to old service**

For the first commit, keep behavior stable by delegating to `ChallengePathService` methods. Later tasks move internals.

Example in `progress.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession


class ChallengeProgressService:
    def __init__(self, db: AsyncSession, legacy_service):
        self.db = db
        self.legacy_service = legacy_service

    async def get_progress(self, user_id: str, lite: bool = True) -> dict:
        return await self.legacy_service.get_progress(user_id=user_id, lite=lite)

    async def save_code(self, user_id: str, exercise_id: int, code: str, language: str) -> bool:
        return await self.legacy_service.save_code(
            user_id=user_id,
            exercise_id=exercise_id,
            code=code,
            language=language,
        )
```

Create analogous shells for selection, rewards, and submission. Keep constructor signatures simple and typed.

- [ ] **Step 4: Run tests**

```powershell
cd backend
pytest tests/test_learning_path_challenge.py tests/test_arena_submission_result.py -q
```

Expected: PASS because no route behavior has changed.

- [ ] **Step 5: Commit Task 4**

```powershell
git add backend/app/services/challenge_path
git commit -m "refactor: add challenge path service package"
```

## Task 5: Implement Backend-Authoritative Submission

**Files:**
- Modify: `backend/app/services/challenge_path/submission.py`
- Modify: `backend/app/services/arena_infinite.py`
- Modify: `backend/app/routers/learning_path.py`
- Modify: `backend/tests/test_challenge_authoritative_submission.py`

- [ ] **Step 1: Explore code execution service with CodeGraph**

Run:

```powershell
npx codegraph context "executeCodeBatch backend app routers code judge0 code execution"
```

Expected: identify current backend batch execution endpoint/service and reusable judge abstraction.

- [ ] **Step 2: Implement authoritative judge adapter**

In `backend/app/services/challenge_path/submission.py`, add a function the tests can monkeypatch:

```python
async def run_authoritative_judge(
    *,
    code: str,
    language: str,
    test_cases: list[dict],
) -> dict:
    """Run final challenge judging on backend-owned test cases."""
    raise NotImplementedError("Wire to existing code execution abstraction in this task")
```

Then wire it to the existing judge/code execution service discovered in Step 1. If the current code execution logic only exists in a router, extract a small reusable service instead of importing a route handler.

Expected result shape:

```python
{
    "passed_count": int,
    "total_count": int,
    "results": [
        {"passed": bool, "input": str, "expected": str, "actual": str, "message": str | None}
    ],
}
```

- [ ] **Step 3: Add submission service orchestration**

Create `ChallengeSubmissionService.submit_exercise(...)` in `submission.py`. It should:

1. Load `Exercise` and progress through existing/legacy helpers.
2. Call `run_authoritative_judge` with backend-owned `exercise.test_cases`.
3. Pass authoritative results into the existing mutation/reward path.
4. Return authoritative `test_results` in the API response.

Keep the old `test_results` request field accepted for compatibility, but do not use it for correctness.

- [ ] **Step 4: Update route to use submission service**

In `backend/app/routers/learning_path.py`, update `submit_challenge_exercise` so it delegates to `ChallengeSubmissionService` or the compatibility facade that uses it.

Preserve request and response field names.

- [ ] **Step 5: Handle judge unavailable**

If `run_authoritative_judge` raises or returns no valid result, return HTTP 503 or 400 with a clear detail such as `"Judge service unavailable"`. Do not mutate correctness-dependent state.

Add or update test:

```python
@pytest.mark.asyncio
async def test_unavailable_judge_does_not_award_progress(...):
    async def unavailable_judge(*args, **kwargs):
        raise RuntimeError("judge down")
    ...
    assert response.status_code in {400, 503}
    assert progress.is_correct is False
```

- [ ] **Step 6: Run authoritative submission tests**

```powershell
cd backend
pytest tests/test_challenge_authoritative_submission.py tests/test_learning_path_challenge.py tests/test_arena_submission_result.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit Task 5**

```powershell
git add backend/app/services/challenge_path/submission.py backend/app/services/arena_infinite.py backend/app/routers/learning_path.py backend/tests/test_challenge_authoritative_submission.py
git commit -m "fix: make challenge submission backend authoritative"
```

## Task 6: Move Selection And Progress Logic Out Of Monolith

**Files:**
- Modify: `backend/app/services/challenge_path/selection.py`
- Modify: `backend/app/services/challenge_path/progress.py`
- Modify: `backend/app/services/arena_infinite.py`
- Modify: `backend/app/routers/learning_path.py`

- [ ] **Step 1: Check impact before moving symbols**

Run:

```powershell
npx codegraph impact ChallengePathService
npx codegraph context "ChallengePathService get_or_create_challenge_path append_exercises get_progress get_exercise_by_id switch_exercise save_code"
```

Expected: understand current callers before moving code.

- [ ] **Step 2: Move selection methods**

Move these responsibilities from `ChallengePathService` into `ChallengeSelectionService`:

- `_select_verified_exercises_by_difficulty`
- `_ensure_fixed_first_two`
- `_create_initial_exercises`
- `get_or_create_challenge_path`
- `append_exercises`

Keep a compatibility method on `ChallengePathService` that calls the new service if needed by existing tests/imports.

- [ ] **Step 3: Move progress methods**

Move these responsibilities into `ChallengeProgressService`:

- `_get_user_progress`
- `_get_exercise_count`
- `_get_exercises_from_progress`
- `get_progress`
- `get_exercise_by_id`
- `get_exercise_by_index`
- `save_code`
- `switch_exercise`

Keep signatures compatible. Avoid changing response shapes in the same step.

- [ ] **Step 4: Run challenge tests**

```powershell
cd backend
pytest tests/test_learning_path_challenge.py tests/test_challenge_authoritative_submission.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit Task 6**

```powershell
git add backend/app/services/challenge_path/selection.py backend/app/services/challenge_path/progress.py backend/app/services/arena_infinite.py backend/app/routers/learning_path.py
git commit -m "refactor: split challenge selection and progress services"
```

## Task 7: Move Reward Logic Out Of Monolith

**Files:**
- Modify: `backend/app/services/challenge_path/rewards.py`
- Modify: `backend/app/services/challenge_path/submission.py`
- Modify: `backend/app/services/arena_infinite.py`
- Modify: backend reward tests as needed

- [ ] **Step 1: Explore reward dependencies**

Run:

```powershell
npx codegraph context "stars_earned tier_service CoreService wrong_question_service TierTransactionService UserArenaProfile submit_exercise"
```

Expected: identify reward-related imports and side effects.

- [ ] **Step 2: Extract reward application**

Move star/tier/core/tier-transaction/profile-stat/wrong-question behavior from `submit_exercise` into `ChallengeRewardService`.

Suggested method:

```python
async def apply_submission_rewards(
    self,
    *,
    user_id: str,
    exercise,
    progress,
    is_correct: bool,
    code: str,
) -> dict:
    ...
```

Return reward fields currently used by the API:

- `stars_earned`
- `cores_earned`
- `added_to_wrong_book`
- `tier_changed`
- `new_tier`
- `new_sub_tier`
- `new_stars`
- `promoted`
- `demoted`
- `first_time_correct`
- `first_time_wrong`

- [ ] **Step 3: Keep submission response stable**

`ChallengeSubmissionService.submit_exercise` should merge:

- authoritative judge result
- progress/unlock fields
- reward fields from `ChallengeRewardService`

Keep existing API keys stable.

- [ ] **Step 4: Run reward-related tests**

```powershell
cd backend
pytest tests/test_user_arena.py tests/test_tier_system.py tests/test_mastery_xp.py tests/test_learning_path_challenge.py tests/test_challenge_authoritative_submission.py -q
```

Expected: PASS. If unrelated tests fail, capture output and fix only regressions from this task.

- [ ] **Step 5: Commit Task 7**

```powershell
git add backend/app/services/challenge_path/rewards.py backend/app/services/challenge_path/submission.py backend/app/services/arena_infinite.py backend/tests
git commit -m "refactor: split challenge reward service"
```

## Task 8: Thin Challenge Routes And Response Mapping

**Files:**
- Modify: `backend/app/services/challenge_path/responses.py`
- Modify: `backend/app/routers/learning_path.py`
- Modify: `backend/app/services/arena_infinite.py`

- [ ] **Step 1: Move duplicate route mapping into response helpers**

Move repeated exercise mapping from `learning_path.py` to `responses.py`.

Functions should include:

```python
def map_challenge_session_exercise(exercise, index: int) -> dict: ...
def map_switch_exercise(exercise) -> dict: ...
def map_exercise_detail(result: dict, total: int) -> dict: ...
```

- [ ] **Step 2: Update learning path challenge endpoints**

Keep route functions in `learning_path.py`, but make each one:

1. Create focused service.
2. Call one service method.
3. Map response through `responses.py`.
4. Return.

Do not mix mastery endpoint refactors into this task.

- [ ] **Step 3: Check file-size direction**

Run:

```powershell
(Get-Content backend/app/services/arena_infinite.py).Count
(Get-Content backend/app/routers/learning_path.py).Count
```

Expected: both files should shrink or have challenge responsibility visibly reduced. Exact line-count target is less important than responsibility separation.

- [ ] **Step 4: Run route compatibility tests**

```powershell
cd backend
pytest tests/test_learning_path_challenge.py tests/test_challenge_authoritative_submission.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit Task 8**

```powershell
git add backend/app/services/challenge_path/responses.py backend/app/routers/learning_path.py backend/app/services/arena_infinite.py
git commit -m "refactor: thin challenge path routes"
```

## Task 9: Frontend Arena Extraction

**Files:**
- Modify: `frontend/app/arena/_components/arena-content.tsx`
- Create: `frontend/app/arena/use-arena-submit.ts`
- Create: `frontend/app/arena/use-arena-append.ts`

- [ ] **Step 1: Explore frontend arena dependencies**

Run:

```powershell
npx codegraph context "arena-content performSubmit appendChallengeExercises submitChallengeExercise useCodeRunner useArenaSession"
```

Expected: understand `performSubmit` dependencies and state setters before extraction.

- [ ] **Step 2: Extract submit orchestration**

Move `performSubmit` from `arena-content.tsx` into `frontend/app/arena/use-arena-submit.ts`.

Keep the function signature stable at first. Export:

```typescript
export async function performSubmit(args: PerformSubmitArgs): Promise<void>
```

Define `PerformSubmitArgs` in the new file with the same fields currently used by `performSubmit`.

- [ ] **Step 3: Extract append/progress helper if still large**

If `performSubmit` remains too large after extraction, move the append block into `frontend/app/arena/use-arena-append.ts`:

```typescript
export async function appendExercisesNearEnd(args: AppendExercisesArgs): Promise<void>
```

Keep behavior identical.

- [ ] **Step 4: Run frontend tests and type/build checks**

```powershell
cd frontend
pnpm test -- arena
pnpm build
```

Expected: PASS. If `pnpm test -- arena` has no matching tests, run relevant existing tests:

```powershell
pnpm test -- api-client
pnpm test -- mastery-quiz-api
```

- [ ] **Step 5: Commit Task 9**

```powershell
git add frontend/app/arena/_components/arena-content.tsx frontend/app/arena/use-arena-submit.ts frontend/app/arena/use-arena-append.ts
git commit -m "refactor: extract arena submission helpers"
```

## Task 10: Defense Documentation

**Files:**
- Create: `docs/defense/ai-controlled-teaching-architecture.md`

- [ ] **Step 1: Create defense architecture note**

Create `docs/defense/ai-controlled-teaching-architecture.md`:

```markdown
# AI-Controlled Teaching Architecture

## Positioning

WisdomPilot uses deterministic teaching workflows as the trusted backbone and GAI as a controlled assistant.

## Deterministic Backbone

- Course and chapter structure
- Exercise storage
- Backend-authoritative judging
- Progress unlocks
- Stars, tiers, cores
- Leaderboards and statistics

## Controlled GAI Assistant

- Light, medium, and deep hints
- Explanations and code feedback
- Optional reflection prompts
- Remedial practice drafts

AI output does not directly determine challenge correctness, rewards, or rankings.

## Demo Flow

1. Student enters challenge path.
2. Student writes and runs code.
3. Student can request tiered AI hints with core costs.
4. Backend judges final submission.
5. System updates progress, stars, cores, and ranking data.

## Why This Is Feasible

The system avoids relying on AI as an unstable judge or curriculum authority. AI improves interaction quality while deterministic services preserve verifiability.
```

- [ ] **Step 2: Commit Task 10**

```powershell
git add docs/defense/ai-controlled-teaching-architecture.md
git commit -m "docs: explain controlled ai teaching architecture"
```

## Task 11: Required Verification Before Handoff Back

**Files:**
- Modify only if failures require fixes.
- Update OpenSpec task checkboxes as tasks complete.

- [ ] **Step 1: Run backend targeted tests**

```powershell
cd backend
pytest tests/test_learning_path_challenge.py tests/test_challenge_authoritative_submission.py tests/test_arena_submission_result.py tests/test_ai_policy.py tests/test_ai.py tests/test_quota.py tests/test_user_arena.py tests/test_tier_system.py -q
```

Expected: PASS.

- [ ] **Step 2: Run frontend tests/build**

```powershell
cd frontend
pnpm test -- api-client
pnpm test -- mastery-quiz-api
pnpm build
```

Expected: PASS.

- [ ] **Step 3: Start services and smoke affected routes**

Run from repo root:

```powershell
python start_services.py
```

Then request at least:

- frontend `/arena`
- backend `/health`
- backend `/api/learning-path/challenge/progress` with an authenticated test user if the test harness supports it

Expected: backend starts, frontend compiles, affected route/page renders. Stop services when done:

```powershell
python stop_services.py
```

- [ ] **Step 4: Update CodeGraph after code movement**

```powershell
npx codegraph sync
```

If sync fails:

```powershell
npx codegraph index
```

Expected: CodeGraph completes without fatal error.

- [ ] **Step 5: Do not archive**

Leave the change active. Report:

- tests run and results
- files split
- remaining risks
- confirmation that final verification is ready for the original reviewer

Do not run `/comet-verify` or `/comet-archive` unless the original reviewer asks.

## Self-Review

Spec coverage:

- `controlled-ai-tutor`: covered by Tasks 3 and 10, plus verification in Task 11.
- `challenge-path-architecture`: covered by Tasks 1, 2, 4, 5, 6, 7, 8, 9, and 11.
- Backend-authoritative grading: covered by Tasks 2 and 5.
- Oversized module reduction: covered by Tasks 6, 7, 8, and 9.

Placeholder scan:

- No TBD/TODO placeholders are left for implementers.

Type consistency:

- `AIFeature`, `AIPolicy`, `ChallengeSubmissionService`, `ChallengeProgressService`, `ChallengeSelectionService`, and `ChallengeRewardService` names are introduced before use.

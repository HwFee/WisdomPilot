# Arena Lifecycle Transaction Governance Design

## Context

Arena 3B-1 established one request-owned transaction for
`POST /api/learning-path/challenge/submit`. The remaining non-submit Arena
endpoints still have a different ownership model:

- `ChallengeSelectionService.append_exercises()` commits internally.
- `ChallengeProgressService.save_code()` commits internally.
- start, append, and exercise-detail attachment allocate path rows without a
  shared serialization lock.
- `GET /challenge/exercise/{id}` can create progress as a hidden side effect.
- switch and start translate every `ValueError` into a client error, including
  unexpected programming or dependency failures.
- save and exit report success-shaped responses when the progress row does not
  exist; exit can say `Progress saved` after a failed save.
- `ChallengePathService` in `arena_infinite.py` is now an unused compatibility
  facade over the focused services.

These behaviors make the non-submit lifecycle harder to reason about than the
governed submit path and leave request rollback unable to cover every mutation.

## Goal

Make one lifecycle use-case service own every non-submit Arena mutation, keep
selection and progress reads focused, use typed expected failures, and let
`get_db` commit or roll back the complete request.

## Scope

Included endpoints:

- `POST /challenge/infinite/start`
- `GET /challenge/progress`
- `POST /challenge/save-code`
- `POST /challenge/switch`
- `POST /challenge/append`
- `POST /challenge/exit`
- `GET /challenge/exercise/{exercise_id}`
- `GET /challenge/recent`

Included boundaries:

- initial and appended progress-row creation;
- verified-exercise attachment performed by exercise detail;
- code persistence for save and exit;
- navigation validation;
- typed lifecycle errors and exact Router mapping;
- explicit top-level response models;
- removal of the unused compatibility facade.

## Non-Goals

- Do not modify `POST /challenge/submit` or its reward/profile transaction.
- Do not change recommendation ordering, difficulty windows, fixed exercises,
  candidate counts, random sampling, unlock rules, or successful response
  values.
- Do not modify frontend code, database schema, migrations, Mastery,
  `ChallengeSession`, Judge0, reward formulas, or profile statistics.
- Do not claim real row-lock exclusion from SQLite tests.

## Approaches Considered

### Router-only typed errors

This is the smallest diff but leaves service commits, hidden detail mutation,
and path-allocation races intact. It improves syntax without governing the
transaction.

### Endpoint-by-endpoint mutation fixes

This can isolate changes, but start, append, detail, save, and exit would each
reimplement locking and transaction rules. The repeated orchestration would be
harder to audit and easier to diverge.

### One lifecycle use-case boundary

This is the selected design. A lifecycle service owns all non-submit writes;
selection only chooses exercises and progress only reads or validates
navigation. It establishes one dependency direction and one place to audit
locking and flush behavior.

## Architecture

### `ChallengePathLifecycleService`

Create `backend/app/services/challenge_path/lifecycle.py` with four public use
cases:

```python
async def start_path(
    *, user_id: str, difficulty_level: int, initial_count: int
) -> tuple[list[Exercise], bool]

async def append_exercises(
    *, user_id: str, difficulty_level: int | None, count: int
) -> list[int]

async def save_code(
    *, user_id: str, exercise_id: int, code: str, language: str
) -> None

async def get_or_attach_exercise(
    *, user_id: str, exercise_id: int
) -> dict
```

The service depends on `ChallengeSelectionService` for selection reads and on
focused internal helpers for progress lookup/mapping. It flushes after a
successful mutation and never commits.

### `ChallengeSelectionService`

Selection becomes selection-only:

- initial selection returns `list[Exercise]` without creating progress rows;
- append selection returns `list[Exercise]` without calculating indexes,
  unlocking, inserting rows, or committing;
- existing recommendation fallbacks and random selection remain unchanged;
- long append logic is split into named helpers for existing IDs, inferred
  difficulty, recommendations, and fallback candidates.

### `ChallengeProgressService`

Progress becomes read/navigation-only:

- progress, recent, existing detail, index lookup, and switch stay here;
- detail lookup no longer inserts progress;
- code saving moves to lifecycle;
- switch raises typed expected errors and performs no mutation;
- long response construction is split into pure helpers without changing
  lite/full field presence.

### Arena schemas and responses

Move Arena request/response models from the large Router into
`backend/app/schemas/arena.py`. The Router imports them at module scope so
existing internal imports remain compatible. Dynamic exercise payloads stay
as dictionaries to preserve lite/full and programming/non-programming field
presence, while every endpoint gets an explicit top-level response model.

Pure response mappers must not mutate service dictionaries. In particular,
`map_switch_response()` returns a new mapping instead of calling `pop()`.

### Compatibility facade

Delete `backend/app/services/arena_infinite.py` after repository-wide search
proves no production caller remains. Update the stale star-logic test so it
tests the tier calculation it actually owns rather than instantiating an unused
facade.

## Transaction And Locking Model

`get_db` remains the only commit/rollback owner.

Lifecycle mutations use these structural locks:

1. start, append, and detail attachment lock the authenticated `User` row with
   `SELECT ... FOR UPDATE` before checking or allocating path indexes;
2. after acquiring that lock, each use case re-reads relevant progress so a
   waiting request observes rows created by the preceding transaction;
3. save and exit lock the target `ArenaExerciseProgress` row before replacing
   `saved_codes` and `current_language`;
4. JSON code updates assign a new dictionary instead of mutating the existing
   object in place;
5. switch, progress, and recent are read-only and acquire no write lock.

This serializes path allocation on databases that support row locks and avoids
lost code updates. SQLite validates orchestration and rollback only.

## Endpoint Behavior

### Start

- Lock owner, re-read current progress.
- If progress exists, return the existing ordered exercises unchanged.
- Otherwise select and insert the initial rows, then flush.
- Insufficient verified exercises remains HTTP 400 with the existing detail.
- Unknown `ValueError` and dependency failures propagate.

### Append

- Lock owner and re-read existing rows, last index, and last completion state.
- Preserve selection algorithms and the current first-new-row unlock rule.
- Empty selection remains a successful `200` response with an empty ID list.
- Insert selected rows and flush without committing.
- Unknown recommendation/database failures propagate.

### Save And Exit

- Lock the progress row, replace the language-specific code, and flush.
- Success responses remain `{ "success": true }` and
  `{ "success": true, "message": "Progress saved" }`.
- Missing progress becomes a typed HTTP 404 instead of a false success-shaped
  response.

### Exercise Detail

- Preserve the current behavior that a verified exercise can be attached on
  demand.
- Existing progress is returned without mutation.
- Otherwise lock owner, re-check progress, verify the exercise, allocate the
  next index, insert one row, and flush.
- Missing or unverified exercise remains HTTP 404 with
  `Exercise not found in challenge path`.

### Switch

- Invalid index, absent indexed progress, and locked exercise remain HTTP 400
  with their existing details.
- These are typed domain failures; unrelated `ValueError` is not translated.
- Successful nested exercise fields remain unchanged.

### Progress And Recent

- Both endpoints remain read-only.
- Exact successful top-level and nested fields remain unchanged.
- Recent continues to use the existing completed/latest-attempt filter and
  limit contract; changing its business semantics is outside this batch.

## Error Contract

Add a FastAPI-independent `ChallengePathError` base and lifecycle subclasses:

| Error | HTTP | Detail |
|---|---:|---|
| `InsufficientChallengeExercisesError` | 400 | existing found/need text |
| `InvalidChallengeExerciseIndexError` | 400 | `Invalid exercise index` |
| `ChallengeProgressIndexNotFoundError` | 400 | `Progress not found` |
| `ChallengeExerciseLockedError` | 400 | `Exercise is locked` |
| `ChallengeProgressNotFoundError` | 404 for save/exit | includes exercise ID |
| `ChallengeExerciseDetailNotFoundError` | 404 | `Exercise not found in challenge path` |

`ChallengeSubmissionError` becomes a subclass of `ChallengePathError`.
Submission keeps its existing explicit mappings. Router code catches only the
listed expected types; unknown failures reach `get_db` and roll back.

## Response Contracts

Declare response models for all included endpoints:

- start: existing `ChallengeSessionResponse`;
- progress: totals, counts, current index, and exercises;
- save: `success`;
- switch: progress fields and nested exercise;
- append: `new_exercise_ids` and `count`;
- exit: `success` and `message`;
- detail: nested exercise, progress fields, and total count;
- recent: existing list item model.

The successful JSON field names and values are compatibility requirements.

## Testing Strategy

Use TDD with real async database sessions where practical.

Required governance coverage:

- typed error classes exist before Router mappings;
- unknown `ValueError` from start, append, and switch is not converted to 400;
- start, append, save, exit, and detail attachment do not call `commit()`;
- save/exit missing progress returns exact 404;
- save replaces the JSON code dictionary and persists through request commit;
- failure after a flushed lifecycle mutation rolls the request back;
- sequential start remains idempotent;
- owner-lock query and progress-lock query structurally include
  `FOR UPDATE` for a production dialect;
- detail attachment re-check prevents a second row after lock acquisition;
- append preserves indexes, IDs, and unlock behavior;
- every route declares its response model and preserves exact success fields;
- no `arena_infinite` import or compatibility alias remains.

Focused tests cover learning-path challenge APIs, lifecycle governance,
selection/recommendation consumers, response mappers, star/tier logic, and the
3B-1 submission regression suite. Final validation runs the complete backend
suite with zero skips, Pyright, FastAPI and Next.js startup, live affected
routes, CodeGraph synchronization, and project quality gates.

## Risks And Controls

- Row locks are structural under SQLite. Record production-dialect contention
  as residual risk; do not overclaim concurrency proof.
- Moving persistence out of selection can accidentally change ordering or
  unlock behavior. Characterization tests compare exact IDs, indexes, and
  flags before and after.
- Explicit response models can inject optional fields. Models therefore govern
  only stable top-level structure where payload shape is intentionally dynamic.
- The detail endpoint remains a mutating GET for compatibility. The mutation is
  made explicit and transactional here; changing the HTTP method requires a
  coordinated frontend contract and is deferred.

## Completion Criteria

- Lifecycle is the sole owner of non-submit Arena writes.
- No challenge-path selection, progress, lifecycle, or response service calls
  `commit()` or imports FastAPI.
- Router catches only typed expected lifecycle/submission errors.
- All included routes have explicit response models and unchanged success
  payloads.
- Compatibility facade and dead test dependencies are removed.
- Focused/full tests, Pyright, service startup, live routes, CodeGraph, scope
  audit, and documentation maintenance all pass.

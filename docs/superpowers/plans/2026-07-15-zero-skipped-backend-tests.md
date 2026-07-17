# Zero-Skipped Backend Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate both backend test skips while proving that check-in rewards remain consistent across API responses, user balances, transaction records, and frontend types.

**Architecture:** Keep the existing request-level transaction boundary and reward algorithm unchanged. Activate and strengthen the existing check-in integration test, align the frontend response type with the backend Pydantic schema, and move FPS sample data into a version-controlled test fixture.

**Tech Stack:** FastAPI, SQLAlchemy async ORM, Pydantic, pytest/pytest-asyncio, Next.js, TypeScript, Jest.

## Global Constraints

- Final backend result must be `555 passed, 0 skipped`.
- Do not change check-in reward amounts, database schema, or FPS parser behavior.
- Do not add explicit commits inside check-in services; the existing request dependency owns commit/rollback.
- The FPS test must not depend on ignored `backend/data/` content or machine-local files.
- Do not commit or push unless the user explicitly requests it.

---

## File Map

- Modify `backend/tests/test_cores.py`: activate the check-in reward test and assert response/balance/ledger consistency, including duplicate check-in behavior.
- Modify `frontend/__tests__/checkin-api.test.ts`: encode `cores_earned` in successful and duplicate check-in examples.
- Modify `frontend/types/api.ts`: add the missing required `cores_earned: number` response property.
- Modify `backend/tests/test_import_fps.py`: use a repository-owned fixture and remove conditional skipping.
- Create `backend/tests/fixtures/sample_problems.xml`: deterministic multi-problem FPS input.
- No backend production file is expected to change; only modify one if the activated test proves a real defect.

---

### Task 1: Align The Frontend Check-In Contract

**Files:**
- Modify: `frontend/__tests__/checkin-api.test.ts:19-67`
- Modify: `frontend/types/api.ts:329-337`

**Interfaces:**
- Consumes: backend `CheckinResponse.cores_earned: int` from `backend/app/schemas/profile.py`.
- Produces: frontend `CheckinResponse.cores_earned: number` used by `checkin(token): Promise<CheckinResponse>`.

- [x] **Step 1: Add the backend field to frontend API test examples**

Add `cores_earned: 5` to the successful response and `cores_earned: 0` to the duplicate response. Assert both values explicitly:

```typescript
const mockResponse: CheckinResponse = {
  streak_days: 5,
  checked_in_today: true,
  xp_earned: 10,
  cores_earned: 5,
  last_checkin_date: '2024-01-15T10:30:00Z',
  total_checkin_days: 15,
  streak_multiplier: 1.0,
  new_achievements: [],
}

expect(result.cores_earned).toBe(5)
```

For the duplicate response:

```typescript
cores_earned: 0,
```

and:

```typescript
expect(result.cores_earned).toBe(0)
```

- [x] **Step 2: Run TypeScript to verify the contract is rejected**

Run: `frontend/node_modules/.bin/tsc.CMD --noEmit -p frontend/tsconfig.json`

Expected: FAIL with an excess-property error because `cores_earned` is not yet part of `CheckinResponse`.

- [x] **Step 3: Add the required frontend response property**

Update `frontend/types/api.ts`:

```typescript
export interface CheckinResponse {
  streak_days: number
  checked_in_today: boolean
  xp_earned: number
  cores_earned: number
  last_checkin_date?: string
  total_checkin_days: number
  streak_multiplier: number
  new_achievements: string[]
}
```

- [x] **Step 4: Verify frontend contract tests and types**

Run: `frontend/node_modules/.bin/jest.CMD --runInBand frontend/__tests__/checkin-api.test.ts`

Expected: `4 passed`.

Run: `frontend/node_modules/.bin/tsc.CMD --noEmit -p frontend/tsconfig.json`

Expected: exit code 0 with no output.

- [x] **Step 5: Prepare a review boundary**

Review `git diff -- frontend/types/api.ts frontend/__tests__/checkin-api.test.ts`. Do not commit without explicit user authorization.

---

### Task 2: Activate And Strengthen Check-In Ledger Verification

**Files:**
- Modify: `backend/tests/test_cores.py:7-12,156-174`

**Interfaces:**
- Consumes: `POST /api/users/checkin`, `GET /api/cores/balance`, `CoreTransaction` ORM model.
- Produces: integration coverage proving one response reward equals one balance increment and one ledger entry.

- [x] **Step 1: Replace the skipped test with exact consistency assertions**

Import SQLAlchemy `select`:

```python
from sqlalchemy import select
```

Remove `@pytest.mark.skip`. Replace the test body with assertions equivalent to:

```python
initial_balance = auth_user.cores

response = await client.post("/api/users/checkin", headers=auth_headers)
assert response.status_code == 200
data = response.json()
cores_earned = data["cores_earned"]
assert cores_earned >= 5

await db_session.refresh(auth_user)
assert auth_user.cores == initial_balance + cores_earned

result = await db_session.execute(
    select(CoreTransaction).where(
        CoreTransaction.user_id == auth_user.id,
        CoreTransaction.type == "earn",
        CoreTransaction.category == "checkin",
    )
)
transactions = list(result.scalars().all())
assert len(transactions) == 1
assert transactions[0].amount == cores_earned
assert transactions[0].balance_after == auth_user.cores
```

Then call the endpoint a second time on the same day:

```python
duplicate_response = await client.post("/api/users/checkin", headers=auth_headers)
assert duplicate_response.status_code == 200
assert duplicate_response.json()["cores_earned"] == 0

await db_session.refresh(auth_user)
assert auth_user.cores == initial_balance + cores_earned

duplicate_result = await db_session.execute(
    select(CoreTransaction).where(
        CoreTransaction.user_id == auth_user.id,
        CoreTransaction.type == "earn",
        CoreTransaction.category == "checkin",
    )
)
assert len(list(duplicate_result.scalars().all())) == 1
```

- [x] **Step 2: Run the activated integration test**

Run: `python -m pytest backend/tests/test_cores.py::TestCoreEarn::test_earn_cores_checkin -q`

Expected: PASS. A failure indicates a real cross-layer defect; inspect response, refreshed user balance, and ledger rows before changing production code.

- [x] **Step 3: Run adjacent check-in and core suites**

Run: `python -m pytest backend/tests/test_cores.py backend/tests/test_checkin.py -q`

Expected: all selected tests pass with no skips.

- [x] **Step 4: Prepare a review boundary**

Review `git diff -- backend/tests/test_cores.py`. Confirm no reward constants or transaction boundaries changed. Do not commit without explicit user authorization.

---

### Task 3: Make The FPS Parser Test Self-Contained

**Files:**
- Modify: `backend/tests/test_import_fps.py:35-46`
- Create: `backend/tests/fixtures/sample_problems.xml`

**Interfaces:**
- Consumes: `parse_fps_xml(file_path: Path) -> list[dict]`.
- Produces: a deterministic tracked fixture with two FPS `<item>` records.

- [x] **Step 1: Point the test at a repository-owned fixture**

Change the test before creating the fixture:

```python
def test_parse_sample_file(self):
    sample_path = Path(__file__).parent / "fixtures" / "sample_problems.xml"
    problems = parse_fps_xml(sample_path)

    assert len(problems) == 2
    assert problems[0]["title"] == "A+B Problem"
    assert problems[0]["time_limit"] == 1
    assert problems[0]["memory_limit"] == 128
    assert problems[0]["sample_input"] == "1 2"
    assert problems[0]["sample_output"] == "3"
    assert problems[1]["title"] == "Hello World"
```

Delete the `sample_path.exists()` branch and `pytest.skip()` call.

- [x] **Step 2: Verify the test fails because the fixture is absent**

Run: `python -m pytest backend/tests/test_import_fps.py::TestFPSParser::test_parse_sample_file -q`

Expected: FAIL with `FileNotFoundError` for `backend/tests/fixtures/sample_problems.xml`.

- [x] **Step 3: Add the deterministic FPS fixture**

Create `backend/tests/fixtures/sample_problems.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<fps version="1.1" url="https://github.com/zhblue/freeproblemset/">
  <item>
    <title><![CDATA[A+B Problem]]></title>
    <time_limit unit="s">1</time_limit>
    <memory_limit unit="mb">128</memory_limit>
    <description><![CDATA[Read two integers and print their sum.]]></description>
    <input><![CDATA[Two integers a and b.]]></input>
    <output><![CDATA[The sum of a and b.]]></output>
    <sample_input><![CDATA[1 2]]></sample_input>
    <sample_output><![CDATA[3]]></sample_output>
    <source><![CDATA[Fixture]]></source>
    <test_input name="sample"><![CDATA[1 2]]></test_input>
    <test_output name="sample"><![CDATA[3]]></test_output>
  </item>
  <item>
    <title><![CDATA[Hello World]]></title>
    <time_limit unit="s">2</time_limit>
    <memory_limit unit="mb">64</memory_limit>
    <description><![CDATA[Print Hello World.]]></description>
    <input><![CDATA[]]></input>
    <output><![CDATA[Hello World]]></output>
    <sample_output><![CDATA[Hello World]]></sample_output>
    <source><![CDATA[Fixture]]></source>
  </item>
</fps>
```

- [x] **Step 4: Verify all FPS import tests pass without skips**

Run: `python -m pytest backend/tests/test_import_fps.py -q -rs`

Expected: all tests pass and no `SKIPPED` section appears.

- [x] **Step 5: Prepare a review boundary**

Review `git diff -- backend/tests/test_import_fps.py backend/tests/fixtures/sample_problems.xml`. Do not commit without explicit user authorization.

---

### Task 4: Full Verification And Maintenance

**Files:**
- Verify only; update `AGENTS.md` only if a new durable project rule was discovered.

**Interfaces:**
- Consumes: all changes from Tasks 1-3.
- Produces: fresh evidence for zero skips, build validity, startup health, and CodeGraph synchronization.

- [x] **Step 1: Run the complete backend suite with skip reporting**

Run: `python -m pytest backend/tests -q -rs`

Expected: `555 passed` and no `skipped` count or `SKIPPED` entries.

- [x] **Step 2: Run frontend tests and changed-file lint**

Run: `frontend/node_modules/.bin/jest.CMD --runInBand`

Expected: all 19 suites and 156 tests pass.

Run: `frontend/node_modules/.bin/eslint.CMD frontend/__tests__/checkin-api.test.ts frontend/types/api.ts`

Expected: exit code 0 with no output.

- [x] **Step 3: Run frontend type and production build checks**

Run: `frontend/node_modules/.bin/tsc.CMD --noEmit -p frontend/tsconfig.json`

Expected: exit code 0 with no output.

Run from `frontend`: `./node_modules/.bin/next.CMD build`

Expected: exit code 0 and all application routes generated successfully.

- [x] **Step 4: Start and request both services**

Start `python start_services.py`, wait for readiness, then request:

```text
http://127.0.0.1:8000/
http://127.0.0.1:3000/
```

Expected: backend JSON health response, frontend HTTP 200, and no startup errors. Stop with `python stop_services.py` after verification.

- [x] **Step 5: Synchronize CodeGraph and inspect the final diff**

Run: `npx codegraph sync`

Run: `git diff --check`

Run: `git status --short --branch`

Expected: CodeGraph sync succeeds, diff check is clean, and only the design/plan plus intended implementation files are modified.

- [x] **Step 6: Request code review**

Review for response/balance/ledger consistency, duplicate reward prevention, fixture representativeness, test isolation, and scope. Resolve all Critical and Important findings before completion.

- [x] **Step 7: Await explicit commit or push instruction**

Report verification evidence and the exact modified files. Do not run `git commit` or `git push` without explicit user authorization.

## Completion Evidence

Completed on 2026-07-17 in commit `81d892c` (`test: eliminate skipped
backend coverage`). The final implementation keeps the backend/frontend
check-in reward contract aligned, replaces the skipped core consistency case
with response/balance/ledger assertions, and uses a deterministic tracked FPS
fixture instead of conditionally skipping.

- Focused backend verification for `test_cores.py`, `test_checkin.py`, and
  `test_import_fps.py`: `34 passed`.
- Full backend verification: `716 passed`; no skipped count or `SKIPPED`
  section was printed.
- Frontend Jest verification: `19/19` suites and `156/156` tests passed.
- Changed-file ESLint and frontend TypeScript checks exited 0 with no errors.
- Next.js production build exited 0 and generated the application routes.
- Isolated startup validation used ports `18178` and `13178`: FastAPI
  completed application startup and `GET /` returned 200; Next.js reached
  Ready, compiled `/` (1633 modules), and `GET /` returned 200. The verified
  Python/Node process trees were stopped, both ports had zero listeners, and
  the resolved smoke directory inside the repository was removed.
- `npx codegraph sync .` completed after the documentation reconciliation.
- Independent review found no Critical or Important findings and returned
  `Ready to merge`. The only Minor observation was historical line-ending
  churn in `81d892c`; it does not change runtime behavior.

Rule 10 review found no duplicated production logic, new coupling, unclear
naming, business magic values, oversized new functions, dead code, or type
safety regression. This batch changes tests, a tracked fixture, and the
frontend response contract only; it requires no database migration or durable
AGENTS.md rule change.

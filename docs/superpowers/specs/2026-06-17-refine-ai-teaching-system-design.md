---
comet_change: refine-ai-teaching-system
role: technical-design
canonical_spec: openspec
---

# Refine AI Teaching System Technical Design

## Summary

This change turns WisdomPilot's story from "AI automatically teaches programming practice" into a more defensible architecture: deterministic teaching workflows own correctness, progress, rewards, and analytics; GAI provides controlled assistance at explicit learning moments.

The implementation also includes a targeted refactor of oversized challenge-path files so future agents can safely modify the system without reasoning through thousand-line modules.

## Architecture Positioning

The system should be explained and implemented around three layers:

1. Deterministic backbone:
   - Courses, chapters, sections, exercises, judge results, progress, stars, tiers, cores, leaderboards, and statistics.
   - This layer is testable and authoritative.

2. Controlled GAI assistant:
   - Tiered hints, explanations, code feedback, optional reflection prompts, and remedial content drafts.
   - This layer is policy-gated and never directly authoritative for rewards or rankings.

3. Demonstration loop:
   - Student opens challenge path.
   - Student writes/runs code.
   - Backend authoritatively judges final submission.
   - System updates unlocks, stars, cores, wrong-question records, leaderboard/statistics.
   - AI hints are available through light/medium/deep controls and core costs.

## Backend Decomposition

The current challenge behavior is concentrated in `backend/app/services/arena_infinite.py` and challenge route sections in `backend/app/routers/learning_path.py`.

The implementer should extract by responsibility, not by arbitrary line count:

- `backend/app/services/challenge_path/selection.py`
  - Select verified exercises by difficulty.
  - Preserve fixed first-exercise behavior.
  - Append new exercises.

- `backend/app/services/challenge_path/progress.py`
  - Create and fetch progress records.
  - Save code by exercise/language.
  - Switch exercises and unlock next exercise.

- `backend/app/services/challenge_path/submission.py`
  - Orchestrate backend-authoritative final submission.
  - Call the existing judge/code execution abstraction.
  - Reject unavailable judge results without awarding rewards.

- `backend/app/services/challenge_path/rewards.py`
  - Apply stars, tiers, cores, tier transactions, profile stats, and wrong-question collection.

- `backend/app/services/challenge_path/responses.py`
  - Map internal Exercise and progress data to existing API response shapes.

These exact filenames can change if the implementer finds a better local convention, but the responsibility boundaries should remain.

`backend/app/routers/learning_path.py` should keep public endpoint paths stable while delegating challenge behavior to the focused services.

## AI Policy Boundary

The implementer should introduce a small policy layer before expanding AI behavior. It should cover current features first:

- challenge hint:
  - light cost 1
  - medium cost 3
  - deep cost 5
  - cached hint cost 0
  - insufficient cores returns the existing insufficient-core response

- general chat:
  - either route through policy, or explicitly document it as outside the controlled-learning demo flow for this change

- optional reflection:
  - policy entry exists only if reflection is implemented
  - reflection status stays separate from judge correctness

Avoid a broad permissions framework. A small enum or typed policy result is enough.

## Backend-Authoritative Grading

Final challenge submission must not trust `test_results` from the browser as the reward-bearing source of truth. The final submission service should:

1. Load the exercise and test cases from the backend.
2. Execute submitted code through the existing code/judge service.
3. Compute pass/fail from backend-owned results.
4. Save client-supplied results only as optional display/debug data if still useful.
5. Award progress, unlocks, stars, cores, and wrong-question collection only after backend-owned pass/fail is known.

If the judge is unavailable, the submit endpoint should return an error and not mutate correctness-dependent state.

## Frontend Cleanup

Frontend cleanup is lower priority than backend authority and service decomposition. Once backend contracts are stable, split `frontend/app/arena/_components/arena-content.tsx` by extracting:

- submit orchestration hook/helper
- append/progress refresh helper
- modal result construction helper if still large after the first two extractions

Do not redesign arena visuals in this change.

## Testing Strategy

The implementer should use TDD for behavior-changing tasks:

- Add failing tests for forged client-passing submissions before changing backend submission.
- Add characterization tests around existing challenge endpoints before moving code.
- Add AI policy tests before changing hint route code.
- Add frontend tests only after backend response shape is clear.

Relevant commands likely include:

```powershell
cd backend
pytest tests/test_learning_path_challenge.py tests/test_arena_submission_result.py tests/test_user_arena.py tests/test_ai.py tests/test_quota.py -q
```

```powershell
cd frontend
pnpm test -- arena
pnpm build
```

The final verifier should also start backend and frontend services and request affected routes. After code movement, run:

```powershell
npx codegraph sync
```

or:

```powershell
npx codegraph index
```

## Handoff Notes For Implementer

- Do not archive the OpenSpec change.
- Do not remove endpoint paths used by the current frontend.
- Do not treat reflection prompts as mandatory unless the core challenge path is stable first.
- Keep commits small: tests, backend authority, backend extraction, AI policy, frontend cleanup, docs/validation.
- Leave final verification to the original reviewer as requested by the user.

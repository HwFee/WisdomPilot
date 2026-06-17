## Why

The current system already covers courses, online practice, mastery tracking, challenge progression, AI hints, rewards, rankings, and statistics, but its product story still sounds like "AI automatically teaches everything," which is riskier than current AI reliability supports. The implementation also concentrates key challenge-path behavior in very large files, making future changes harder to verify and delegate safely.

This change reframes the system for graduation defense and project demonstration: deterministic teaching workflows provide the trusted backbone, while GAI acts as a controlled assistant at specific learning moments. It also plans a focused refactor of oversized challenge and learning-path modules without changing user-facing behavior.

## What Changes

- Reposition AI from an always-open tutor to a controlled teaching assistant used for tiered hints, explanations, code feedback, reflection prompts, and remedial practice drafts.
- Define the challenge path as the primary demonstration flow: write code, run/judge, submit, unlock progress, earn stars/cores, and show leaderboard/statistics impact.
- Add a planned enhancement path for post-pass reflection prompts, but keep it separate from the mandatory demo flow unless implementation capacity allows.
- Refactor oversized challenge-path and learning-path backend modules into smaller services/routers with clear responsibilities.
- Harden challenge submission planning so authoritative grading happens on the backend rather than trusting client-supplied test results.
- Preserve existing user-facing routes and frontend behavior unless a task explicitly states an API compatibility wrapper is required.
- Do not introduce a broad new AI-generated curriculum engine in this change.

## Capabilities

### New Capabilities
- `controlled-ai-tutor`: Covers AI access policy, tiered hint behavior, core-cost control, optional reflection prompts, and defense-ready explanation of AI boundaries.
- `challenge-path-architecture`: Covers challenge-path grading authority, progression/reward behavior preservation, and decomposition of large backend/frontend challenge modules.

### Modified Capabilities

No existing OpenSpec capabilities are present in `openspec/specs/`, so this change creates new capability specs.

## Impact

- Affected backend areas:
  - `backend/app/routers/ai.py`
  - `backend/app/routers/learning_path.py`
  - `backend/app/services/ai.py`
  - `backend/app/services/arena_infinite.py`
  - `backend/app/services/judge0.py`
  - `backend/app/services/tier_service.py`
  - `backend/app/services/core_service.py`
  - related tests under `backend/tests/`
- Affected frontend areas:
  - `frontend/app/arena/**`
  - `frontend/components/exercise/AIHintPanel/**`
  - `frontend/lib/api/**`
  - related tests under `frontend/__tests__/` and component test folders
- Affected docs:
  - OpenSpec artifacts for this change
  - Superpowers design and implementation plan
  - optional defense notes if added by the implementer
- External dependencies:
  - No new runtime dependency is required by default.
  - Existing Judge0/code execution integration must remain the authority for challenge grading if backend-side judging is implemented.

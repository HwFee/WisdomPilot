## Context

WisdomPilot already implements a broad teaching platform: authentication, course selection, mastery path, challenge path, online code execution, AI hints, core currency, tier rewards, leaderboards, notes, wrong-question collection, and statistics. The current architecture proves product breadth, but the original product story overstates AI reliability by implying that GAI can fully generate and evaluate individualized practice teaching.

The more defensible architecture is a deterministic learning system with controlled GAI assistance. Deterministic services own course structure, exercises, judging, progress, rewards, and analytics. AI supports bounded learning moments: hints, explanations, code feedback, optional reflection prompts, and remedial content drafts.

Code review also found large concentration points:

- `backend/app/services/arena_infinite.py` contains challenge selection, progress, submission, reward, wrong-question, profile, and stats behavior.
- `backend/app/routers/learning_path.py` contains mastery endpoints and a large challenge-path router section.
- `frontend/app/arena/_components/arena-content.tsx` contains a large arena orchestration component with code execution, submission, append, progress, and modal logic.

This change plans targeted decomposition while preserving behavior.

## Goals / Non-Goals

**Goals:**

- Reframe the system as "deterministic teaching workflow + controlled GAI assistant" for defense and implementation consistency.
- Centralize AI access policy so hint costs, cached hints, and general chat boundaries are explicit.
- Preserve and strengthen the primary demonstration flow: code challenge -> backend-authoritative judging -> progress unlock -> stars/cores -> leaderboard/statistics.
- Refactor oversized challenge-path files into focused modules with stable interfaces and focused tests.
- Make the implementation plan clear enough for another AI agent to execute, while leaving final verification to the user-requested verifier in this thread.

**Non-Goals:**

- Do not build a fully AI-generated curriculum engine.
- Do not redesign the entire UI or visual system.
- Do not replace the existing course/mastery system.
- Do not introduce a new judge provider unless the existing execution abstraction cannot support backend-authoritative challenge submissions.
- Do not archive the change before the user explicitly asks for final verification and archive.

## Decisions

### Decision 1: AI is an assistant, not the source of truth

AI output will not be treated as authoritative for curriculum correctness, challenge correctness, rewards, or ranking. Those remain deterministic and testable.

Alternatives considered:

- Full AI-generated practice path: more impressive but difficult to verify, prone to bad test cases, and risky for defense.
- Disable most AI features: safer but loses the project's GAI theme.

Chosen approach: keep AI in bounded nodes and document the boundary clearly.

### Decision 2: Add an AI policy boundary before expanding AI behavior

Existing hint behavior already has costs and caching. The plan should extract or formalize a policy service that answers:

- Which AI feature is being used?
- Is it learner-facing, admin-only, cached, free, or core-costed?
- What cost applies?
- What response should be returned when access is denied?

This enables the current hint system to remain intact while making general chat and future reflection prompts explicit.

### Decision 3: Make challenge submission backend-authoritative

The current frontend runs tests and sends `test_results` to the backend. That is useful for quick UI feedback, but rewards and progression should not rely solely on client-supplied results. The plan should add backend-side judging or verification in the challenge submission flow before updating correctness, rewards, wrong-question collection, or leaderboard-affecting state.

Compatibility requirement: existing frontend calls should continue to work, but backend correctness must be computed or verified server-side.

### Decision 4: Decompose challenge path by responsibility

The implementation plan should split challenge-path behavior into focused backend modules, for example:

- `challenge_selection_service`: initial exercise selection, fixed first exercises, append selection.
- `challenge_progress_service`: progress records, load/switch/save/unlock.
- `challenge_submission_service`: authoritative judging orchestration and submission result.
- `challenge_reward_service`: stars, tiers, cores, tier transactions, profile stats.
- `challenge_response_mapper`: API-compatible response mapping.

Exact names can vary if they match existing style, but responsibilities must be separated.

### Decision 5: Keep route compatibility while shrinking router files

The current `/api/learning-path/challenge/...` endpoints should remain stable for the existing frontend. Route handlers should become thin coordinators that call services and map results.

### Decision 6: Frontend arena refactor is secondary but planned

Backend correctness and decomposition are the highest-risk areas. Frontend arena decomposition should focus on extracting submission orchestration and append/progress handling from `arena-content.tsx` only after backend contracts are stable.

## Risks / Trade-offs

- Backend judging may duplicate frontend execution cost -> Mitigation: allow frontend sample runs for UX, but only final submission triggers authoritative backend judging.
- Refactoring large files can introduce behavior regressions -> Mitigation: write characterization tests for current API shapes and reward outcomes before moving code.
- AI policy centralization can become over-abstracted -> Mitigation: start with current features only: challenge hints, cached hints, general chat classification, optional reflection prompt policy.
- Reflection prompts may distract from core demo -> Mitigation: keep reflection as optional enhancement after the core challenge flow remains stable.
- Another AI implementer may over-split files -> Mitigation: tasks require preserving public API behavior and keeping extraction responsibility-based.

## Migration Plan

1. Add characterization tests around current challenge endpoints, reward behavior, hint policy behavior, and arena submission expectations.
2. Introduce focused services behind existing route behavior.
3. Move code in small slices, keeping old public endpoints stable.
4. Add backend-authoritative submission verification and update tests to reject forged client results.
5. Extract frontend arena orchestration only after backend responses are stable.
6. Run backend tests, frontend tests, frontend build, startup validation, and CodeGraph sync before verification.

Rollback strategy: because this is a refactor with compatibility preservation, revert individual extraction commits if behavior diverges. Do not remove old compatibility wrappers until tests prove existing frontend flows still work.

## Open Questions

- Whether final submission should call the existing `code` router/service directly or a lower-level `judge0` service from the challenge submission service.
- Whether general AI chat should be core-costed immediately or documented as outside the official defense demo flow for this change.
- Whether reflection prompts should be implemented now or left as a documented next-phase enhancement after the architecture refactor.

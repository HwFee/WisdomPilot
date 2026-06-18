# Comet Design Handoff

- Change: refine-ai-teaching-system
- Phase: design
- Mode: compact
- Context hash: d51087dfed0649d459f7c92aa5a05b91534128b4d8c645c43085bffe248f0ac8

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/refine-ai-teaching-system/proposal.md

- Source: openspec/changes/refine-ai-teaching-system/proposal.md
- Lines: 1-49
- SHA256: 5be599458920958fc4fbb10ba7a89a9aea16108f2c322fdee40a2c6b41c16e8c

```md
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
```

## openspec/changes/refine-ai-teaching-system/design.md

- Source: openspec/changes/refine-ai-teaching-system/design.md
- Lines: 1-106
- SHA256: 3f4f5ed016501ef14d5d04bb580802320673d0ca4a375da6618cca6b2f009467

[TRUNCATED]

```md
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

```

Full source: openspec/changes/refine-ai-teaching-system/design.md

## openspec/changes/refine-ai-teaching-system/tasks.md

- Source: openspec/changes/refine-ai-teaching-system/tasks.md
- Lines: 1-43
- SHA256: 775a40ff7bb7910a6bccd23c3ced24e121955cf09e3a52ae42af9837e33d425d

```md
## 1. Characterization And Safety Tests

- [ ] 1.1 Add backend characterization tests for challenge progress, save-code, switch, append, and exercise-detail response compatibility.
- [ ] 1.2 Add backend tests proving challenge rewards/progress are not awarded from forged client-supplied passing results.
- [ ] 1.3 Add backend tests for AI hint cost, cached hint reuse, insufficient core behavior, and general-chat policy classification.
- [ ] 1.4 Add frontend tests or focused integration tests for arena submission behavior against the preserved challenge API shape.

## 2. Controlled AI Tutor Boundary

- [ ] 2.1 Introduce a focused AI policy module/service for learner-facing AI feature access decisions.
- [ ] 2.2 Route challenge hint cost, cache, and insufficient-core behavior through the AI policy boundary without changing existing hint UX.
- [ ] 2.3 Classify general chat as policy-controlled or explicitly outside the defense demo flow, and document the decision in code/docs.
- [ ] 2.4 Preserve light/medium/deep hint pedagogical boundaries and add tests that inspect prompt construction or policy metadata.

## 3. Backend Challenge Path Decomposition

- [ ] 3.1 Extract challenge exercise selection and append behavior from `backend/app/services/arena_infinite.py` into a focused service.
- [ ] 3.2 Extract challenge progress loading, switching, code saving, and unlocking behavior into a focused service.
- [ ] 3.3 Extract challenge reward behavior for stars, tiers, cores, tier transactions, profile stats, and wrong-question collection into focused services/helpers.
- [ ] 3.4 Extract API response mapping for challenge exercises/progress/submission results so route handlers stay thin and compatible.
- [ ] 3.5 Reduce `backend/app/routers/learning_path.py` challenge endpoints to orchestration-only handlers while preserving current endpoint paths.

## 4. Backend-Authoritative Submission

- [ ] 4.1 Add a backend challenge submission service that runs or verifies code through the existing judge/code execution abstraction.
- [ ] 4.2 Update challenge submit endpoint to use backend-authoritative judge results before changing correctness, unlocks, rewards, wrong-question collection, or leaderboard-affecting state.
- [ ] 4.3 Keep client-supplied test results as optional display/debug input only, never the sole source of reward-bearing correctness.
- [ ] 4.4 Add unavailable-judge handling that returns a submission error without awarding correctness-dependent rewards.

## 5. Frontend Arena Cleanup

- [ ] 5.1 Extract arena submit orchestration from `frontend/app/arena/_components/arena-content.tsx` into a hook or helper module.
- [ ] 5.2 Extract append/progress refresh behavior from `arena-content.tsx` into a focused helper while preserving current UX.
- [ ] 5.3 Keep arena components visually unchanged unless required by API compatibility.

## 6. Documentation And Validation

- [ ] 6.1 Add or update defense-facing notes that explain deterministic backbone versus controlled GAI assistant.
- [ ] 6.2 Run backend tests covering challenge, AI hint policy, rewards, and learning-path compatibility.
- [ ] 6.3 Run frontend tests for arena/API clients plus `pnpm build`.
- [ ] 6.4 Start backend and frontend services and request affected routes to verify startup and rendering.
- [ ] 6.5 Run `npx codegraph sync` or `npx codegraph index` after code movement.
- [ ] 6.6 Leave the change ready for final verification by the original reviewer before archive.
```

## openspec/changes/refine-ai-teaching-system/specs/challenge-path-architecture/spec.md

- Source: openspec/changes/refine-ai-teaching-system/specs/challenge-path-architecture/spec.md
- Lines: 1-57
- SHA256: 3db01ae18893cbe28508c90440f864610194ca0054288a0fab29868ab3631d7a

```md
## ADDED Requirements

### Requirement: Challenge grading shall be backend-authoritative
The system SHALL make backend challenge submission the authoritative source for pass/fail, progress unlocks, star changes, core rewards, wrong-question collection, and ranking impact. Client-run test results MAY be displayed for responsiveness but MUST NOT be trusted as the sole authority for rewards.

#### Scenario: Learner submits code through challenge path
- **WHEN** a learner submits code for a programming challenge
- **THEN** the backend obtains or verifies judge results before updating completion, correctness, rewards, progress, or leaderboard-affecting state

#### Scenario: Client sends forged passing results
- **WHEN** a client sends passing test results that do not match backend-authoritative judging
- **THEN** the backend rejects or ignores the forged correctness and does not award challenge progress or rewards from the forged result

#### Scenario: Judge service is unavailable
- **WHEN** backend-authoritative judging cannot complete because the judge service is unavailable
- **THEN** the system returns a submission error and does not award correctness-dependent rewards

### Requirement: Challenge refactor shall preserve external behavior
The system SHALL split oversized challenge-path modules into focused services and routers while preserving existing public API contracts unless a compatibility layer and tests are provided.

#### Scenario: Existing frontend loads challenge progress
- **WHEN** the frontend calls the existing challenge progress endpoint
- **THEN** the response shape remains compatible with the current arena page expectations

#### Scenario: Existing frontend saves code
- **WHEN** the frontend calls the existing save-code endpoint
- **THEN** saved code remains associated with the same user, exercise, and language as before the refactor

#### Scenario: Existing frontend switches exercises
- **WHEN** the frontend calls the existing switch endpoint
- **THEN** locked/unlocked behavior and returned exercise content remain compatible with current arena behavior

### Requirement: Challenge services shall have clear boundaries
The system SHALL decompose challenge-path logic into services with single responsibilities. At minimum, selection/progress, judging/submission, rewards, and presentation mapping MUST be separable enough to test independently.

#### Scenario: Progress logic is tested
- **WHEN** progress creation, retrieval, unlocking, or append behavior changes
- **THEN** tests exercise that behavior without requiring reward calculation internals

#### Scenario: Reward logic is tested
- **WHEN** star, tier, or core reward behavior changes
- **THEN** tests exercise reward behavior without requiring route serialization internals

#### Scenario: Route mapping is tested
- **WHEN** router response mapping changes
- **THEN** tests verify API-compatible response fields without requiring direct knowledge of internal service storage

### Requirement: Oversized module reduction shall be measurable
The system SHALL reduce the size and responsibility concentration of the largest challenge-path files as part of this refactor. The implementation plan MUST identify target extraction files and verification commands before code changes begin.

#### Scenario: Refactor complete
- **WHEN** the refactor tasks are marked complete
- **THEN** `backend/app/services/arena_infinite.py` and `backend/app/routers/learning_path.py` no longer contain the full challenge-path implementation in a single monolithic class or router section

#### Scenario: CodeGraph is updated
- **WHEN** code movement is complete
- **THEN** CodeGraph index or sync has been run so later agents can inspect the new call graph
```

## openspec/changes/refine-ai-teaching-system/specs/controlled-ai-tutor/spec.md

- Source: openspec/changes/refine-ai-teaching-system/specs/controlled-ai-tutor/spec.md
- Lines: 1-53
- SHA256: ecc6ba8840de15ea6e7fadfc25c962dab8df81c8459fb20becf7fe033af76df1

```md
## ADDED Requirements

### Requirement: AI assistance shall be policy-controlled
The system SHALL expose AI assistance through explicit learning-context policies instead of unrestricted default access. Each AI entry point MUST declare whether it is free, core-costed, cached, admin-only, or disabled for learners.

#### Scenario: Learner requests a challenge hint
- **WHEN** a learner requests a light, medium, or deep hint for a challenge exercise
- **THEN** the system uses the configured hint policy to determine the core cost, checks the learner balance, and either streams the hint or returns an insufficient-core response

#### Scenario: Learner uses cached hint
- **WHEN** a learner requests a hint previously purchased for the same exercise and hint level
- **THEN** the system returns the cached hint without deducting additional cores

#### Scenario: General AI chat remains available
- **WHEN** a learner uses a general AI chat entry point
- **THEN** the implementation MUST either route it through the same policy service or document that it is intentionally excluded from the controlled-learning demo flow

### Requirement: AI hints shall remain pedagogically bounded
The system SHALL keep tiered hint prompts aligned with teaching support rather than direct answer disclosure. Light hints MUST guide direction, medium hints MUST provide structured steps or pseudocode, and deep hints MUST provide detailed reasoning without requiring a complete runnable answer.

#### Scenario: Light hint generation
- **WHEN** a light hint is requested for a programming exercise
- **THEN** the prompt asks for problem interpretation, data structure or algorithm direction, and boundary-case reminders without full code

#### Scenario: Medium hint generation
- **WHEN** a medium hint is requested for a programming exercise
- **THEN** the prompt may include pseudocode or skeleton structure but must not include a complete implementation

#### Scenario: Deep hint generation
- **WHEN** a deep hint is requested for a programming exercise
- **THEN** the prompt may include detailed reasoning, complexity analysis, and commented code structure while still avoiding a copy-paste final answer

### Requirement: Reflection prompts shall be optional enhancement work
The system SHALL treat post-pass AI reflection prompts as an optional enhancement module that can be enabled after the core challenge flow remains stable. Reflection prompts MUST be generated from the submitted code, exercise goal, and knowledge points, and MUST not replace deterministic judge results.

#### Scenario: Reflection disabled
- **WHEN** the reflection module is not enabled
- **THEN** a learner can complete the challenge flow using existing judge, progress, reward, and leaderboard behavior

#### Scenario: Reflection enabled after pass
- **WHEN** a learner passes all authoritative tests and reflection is enabled
- **THEN** the system can generate short follow-up questions to check whether the learner understands the experiment goal

#### Scenario: Reflection assessment recorded
- **WHEN** a learner answers reflection questions
- **THEN** the system records reflection status separately from judge correctness so code correctness and conceptual verification remain distinguishable

### Requirement: Defense positioning shall be explicit
The system SHALL document the product position as deterministic teaching workflow plus controlled GAI assistance. Documentation MUST avoid claiming that AI alone reliably generates and evaluates the full curriculum.

#### Scenario: Reviewer reads design artifacts
- **WHEN** a reviewer reads the proposal, design, or implementation plan
- **THEN** they can identify which parts are deterministic system behavior and which parts are AI-assisted enhancement behavior
```


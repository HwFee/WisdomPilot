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

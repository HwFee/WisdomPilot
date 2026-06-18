## 1. Characterization And Safety Tests

- [x] 1.1 Add backend characterization tests for challenge progress, save-code, switch, append, and exercise-detail response compatibility.
- [x] 1.2 Add backend tests proving challenge rewards/progress are not awarded from forged client-supplied passing results.
- [x] 1.3 Add backend tests for AI hint cost, cached hint reuse, insufficient core behavior, and general-chat policy classification.
- [x] 1.4 Add frontend tests or focused integration tests for arena submission behavior against the preserved challenge API shape.

## 2. Controlled AI Tutor Boundary

- [x] 2.1 Introduce a focused AI policy module/service for learner-facing AI feature access decisions.
- [x] 2.2 Route challenge hint cost, cache, and insufficient-core behavior through the AI policy boundary without changing existing hint UX.
- [x] 2.3 Classify general chat as policy-controlled or explicitly outside the defense demo flow, and document the decision in code/docs.
- [x] 2.4 Preserve light/medium/deep hint pedagogical boundaries and add tests that inspect prompt construction or policy metadata.

## 3. Backend Challenge Path Decomposition

- [x] 3.1 Extract challenge exercise selection and append behavior from `backend/app/services/arena_infinite.py` into a focused service.
- [x] 3.2 Extract challenge progress loading, switching, code saving, and unlocking behavior into a focused service.
- [x] 3.3 Extract challenge reward behavior for stars, tiers, cores, tier transactions, profile stats, and wrong-question collection into focused services/helpers.
- [x] 3.4 Extract API response mapping for challenge exercises/progress/submission results so route handlers stay thin and compatible.
- [x] 3.5 Reduce `backend/app/routers/learning_path.py` challenge endpoints to orchestration-only handlers while preserving current endpoint paths.

## 4. Backend-Authoritative Submission

- [x] 4.1 Add a backend challenge submission service that runs or verifies code through the existing judge/code execution abstraction.
- [x] 4.2 Update challenge submit endpoint to use backend-authoritative judge results before changing correctness, unlocks, rewards, wrong-question collection, or leaderboard-affecting state.
- [x] 4.3 Keep client-supplied test results as optional display/debug input only, never the sole source of reward-bearing correctness.
- [x] 4.4 Add unavailable-judge handling that returns a submission error without awarding correctness-dependent rewards.

## 5. Frontend Arena Cleanup

- [x] 5.1 Extract arena submit orchestration from `frontend/app/arena/_components/arena-content.tsx` into a hook or helper module.
- [x] 5.2 Extract append/progress refresh behavior from `arena-content.tsx` into a focused helper while preserving current UX.
- [x] 5.3 Keep arena components visually unchanged unless required by API compatibility.

## 6. Documentation And Validation

- [x] 6.1 Add or update defense-facing notes that explain deterministic backbone versus controlled GAI assistant.
- [x] 6.2 Run backend tests covering challenge, AI hint policy, rewards, and learning-path compatibility.
- [x] 6.3 Run frontend tests for arena/API clients plus `pnpm build`.
- [x] 6.4 Start backend and frontend services and request affected routes to verify startup and rendering.
- [x] 6.5 Run `npx codegraph sync` or `npx codegraph index` after code movement.
- [x] 6.6 Leave the change ready for final verification by the original reviewer before archive.

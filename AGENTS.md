# WisdomPilot Project Mandatory Rules

> AI Agents participating in coding, review, or maintenance for this project must follow these project-specific rules in addition to the global `~/.Codex/AGENTS.md`.
> Priority: explicit user instructions > this file > global AGENTS.md > platform default prompts.

---

## I. Project Wrap-Up Maintenance

### Rule 5: Task Wrap-Up Maintenance

After completing every task, **you MUST perform the following maintenance actions**:

1. **Maintain global AGENTS.md**: if the task produced cross-project behavioral guidelines, update them into global `~/.Codex/AGENTS.md`; if they only apply to this project, update this file.
2. **Maintain CodeGraph**: run `npx codegraph sync` or `npx codegraph index` to keep the index up to date.
3. **Maintain the database**: if the task involves database schema changes or data migration, ensure migration scripts have been executed, rollback scripts are prepared, and the database state matches the code.
4. **Code quality gate check** (see Rule 10): before committing, complete self-checks for DRY, naming, modularity, magic numbers, etc.

---

## II. Project Validation and Quality Gates

### Rule 8: Post-Refactor Startup Validation

**After every refactor, start the services to verify the system runs normally.**

- **Backend**: start the FastAPI service and confirm no startup errors and routes load correctly.
- **Frontend**: start the Next.js dev server and confirm no compile errors and pages render correctly.
- **Tests**: run relevant test suites and confirm no new failures.
- **Validation order**: start services → observe logs → continue if no errors; if errors occur, fix immediately and re-validate before proceeding.
- **Frontend note: full validation is more than `tsc --noEmit`**. `react-doctor` scores and bare `tsc` **cannot** replace real build validation:
  - Next.js App Router-specific constraints (`"use client"` + `export const metadata`, missing `export default` in `page.tsx`, dynamic route params, etc.) are only caught by tsc after `next dev` / `next build` triggers `.next/types/validator.ts`.
  - After subagent/AI refactoring, you must **actually run `next dev` and request an affected route once** (watch for `Compiled /` + `GET / 200`), not just look at `tsc` output.
  - Strictly forbidden: after deleting exports/files marked "dead" by a linter, declaring completion without first `grep`-ping the entire repo and running `next dev` — these symbols may be used by unread branches or dynamic imports.

### Rule 10: Code Quality Gate — Mandatory Self-Check After Every Change

**After any code change and before committing, you MUST perform the following self-check checklist. Do not proceed to the next step until it passes.**

| Check Item | Method | Pass Criteria |
|------------|--------|---------------|
| **DRY** | Visual inspection + CodeGraph search for similar patterns | No 2+ duplicated logics; similar logic extracted into shared modules |
| **Modularity / Low Coupling** | Check inter-function dependencies | No circular dependencies; unidirectional call chains; state separated from UI; one module change does not cascade to unrelated modules |
| **Naming Quality** | Line-by-line variable/function name review | No single-letter names (except loop-local vars); no mental-mapping abbreviations (`usr`, `cnt`, `tmp`); naming is documentation |
| **Magic Numbers/Strings** | Search for hardcoded literals | All business-meaning hardcoded values replaced with named constants or enums; only retained when absolutely self-evident (e.g., `i = 0`) |
| **Function Length** | Count effective code lines per function | Not exceeding ~40 lines; longer functions must have clear internal sub-functions or section comments |
| **Dead Code** | CodeGraph `impact` + `query` checks | No unused imports/variables/functions; no unreachable branches |
| **Type Safety** | `npx tsc --noEmit` (frontend) / start service (backend) | Zero type errors; zero startup errors |

- **Counter-example (arena `initChallenge` three duplications)**:
  ```typescript
  // Wrong: 3 copy-pastes
  const result = processProgressData(...)
  if (result.isLite && ...) { loadExerciseContent(...) }
  // Right: extract as setupAndMaybeLoad(), call it in one line from each of the 3 places
  ```
- **Counter-example (unstable dependency)**:
  ```typescript
  // Wrong: getSearchParam changes every render, causing useCallback to rebuild frequently
  const exerciseIndexFromReview = getSearchParam('exerciseIndex')
  useCallback(..., [exerciseIndexFromReview])
  // Right: use useRef, read only once on mount
  const exerciseIndexFromReviewRef = useRef(getSearchParam('exerciseIndex'))
  ```

### Rule 11: Mandatory Component Refactor Audit

**After completing every component refactor, you MUST audit the following elements. Do not commit until all pass.**

| Audit Item | Check Content | Pass Criteria |
|------------|---------------|---------------|
| **Visual Consistency** | Check colors, fonts, spacing, radii, borders | All use design system tokens; no hardcoded colors/fonts/spacing; no inconsistent border radii |
| **Icon Standards** | Check all icons | Unified use of lucide-react + Icon wrapper; no emoji; strokeWidth=1.5; consistent sizes |
| **Animation Restraint** | Check animations/transitions | No gradient backgrounds (`bg-gradient-to-*`); no blur decoration; no glass effects; hover only changes border/bg |
| **Functional Completeness** | Compare before and after refactor | All props interfaces preserved; all event handlers preserved; no functionality lost |
| **Responsive** | Check mobile adaptation | Layout does not break on small screens; text does not truncate; touch targets ≥ 44px |
| **Type Safety** | `npx tsc --noEmit` | Zero type errors |
| **Build Pass** | `pnpm build` | Build succeeds with no errors |

**Audit process**:
1. After component refactor, self-check all 7 items above
2. After all pass, mark commit message with `[Rule-11-audited]`
3. If any item fails, fix immediately and re-audit

---

## III. Scope

- This file applies to the `WisdomPilot` project root directory and all subdirectories.
- Subdirectories may contain more specific `AGENTS.md` files, which take precedence over this file.
- Explicit user instructions have the highest priority.

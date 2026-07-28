# WisdomPilot Project Agent Rules

> AI agents participating in coding, review, planning, or maintenance for this project must follow these rules in addition to global agent instructions.
> Priority: explicit user instructions > this file > global AGENTS.md > platform default prompts.

This project is primarily maintained through Codex and CodeGraph. Do not assume tool-specific local configuration from other agents is available.

---

## I. Workflow And Tooling

### Rule 1: Prefer CodeGraph For Code Understanding (when available)

If `.codegraph/` exists at the repository root **and** the `codegraph` executable is available in the current environment, prefer it over grep/find/manual file reading for code exploration, symbol lookup, call-chain analysis, or impact checks. If the executable is not available (e.g. `npx codegraph` cannot run), fall back to Grep/Glob/Read directly — do not block on it.

- Start-of-task check: run `npx codegraph init` only if the repository is not already initialized.
- Exploration examples:
  - `npx codegraph explore "<task or flow>"`
  - `npx codegraph impact <symbol>`
  - `npx codegraph query <symbol>`
- After code movement or module extraction, run `npx codegraph sync` or `npx codegraph index`.
- Grep/search is allowed as a supplement for exact text, comments, generated files, or cases CodeGraph cannot answer.

### Rule 2: Worktree Safety

This project may contain active git worktrees under local tool directories. Treat them as real work products.

- Do not delete `.claude/worktrees/`, `.codex/`, or other worktree directories unless the user explicitly asks to remove those worktrees.
- Before cleaning local tool configuration, distinguish disposable config from worktree source code.
- Do not revert, reset, or delete unrelated user/agent changes.

---

## II. Project Wrap-Up Maintenance

### Rule 5: Task Wrap-Up Maintenance

After completing every task, **you MUST perform the following maintenance actions**:

1. **Maintain AGENTS.md only when needed**: if the task produced durable project behavior rules, update this file; if it produced cross-project behavior rules, ask before changing global `~/.Codex/AGENTS.md`.
2. **Maintain CodeGraph** (when the executable is available): after code movement or meaningful source changes, run `npx codegraph sync` or `npx codegraph index`; skip silently if not installed.
3. **Maintain the database**: if the task involves database schema changes or data migration, ensure migration scripts have been executed, rollback scripts are prepared, and the database state matches the code.
4. **Code quality gate check** (see Rule 10): before committing, complete self-checks for DRY, naming, modularity, magic numbers, etc.

---

## III. Project Validation and Quality Gates

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

原则：重复 3 次的相似逻辑抽成共享函数；渲染期不稳定的值（如每次 render 都变的 search param）用 `useRef` 在挂载时读一次，不要直接塞进 `useCallback` 依赖。

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

## V. 训练舱架构（2026-07-26 重塑后生效）

产品已重塑为「AI 时代的编程实战训练舱」。设计依据：`docs/2026-07-26-产品评估与重塑方案.md`、
`docs/superpowers/specs/2026-07-26-deck-rebuild-design.md`。旧系统（课程/精进之路/错题复习/题解
广场/笔记/收藏/admin）已物理删除，相关规则不再适用。

### 页面与模块

- 路由：`/dashboard`（首页）+ 四模块 `/review-gym` `/arena` `/tutor` `/certification` +
  `/review`（复盘：错题/失败项聚合，与导师对话相互独立）+ `/abilities` `/profile`
  `/login` `/register` `/forgot-password`；`/` 重定向到 `/dashboard`。
- 费曼检验并入苏格拉底导师（「考考我」模式），不设独立模块。
- 后端已在 `backend/app/deck/` 落地，权威 schema 是 `frontend/lib/api/deck/types.ts`，
  接口规格在 `docs/backend-api/01-target-design.md`。
- 后端边界（2026-07-27 清理后）：只注册 auth + deck 两组路由，live 代码 = `app/deck/` +
  auth 链 + 基础设施（`services/ai.py`+`ai_provider/`、`services/judge0*`、限流 middleware、
  `core/`、`utils/`）。旧系统后端（课程/章节/练习/挑战/复习/统计/收藏/笔记/题解/旧演武场/
  旧经济/wrong_question/user_weak_point 等）已**物理删除**，对应数据表已 drop，
  `app.models` 只剩 `User`。新增功能一律进 `app/deck/`，不要复活旧模块。
- 掌握度模型（2026-07-26 起）：事件源 HLR 记忆模型 + 四级状态机（初识/熟悉/熟练/精通），
  纯函数在 `backend/app/deck/mastery.py`，事实源是 `deck_mastery_events` 事件表，
  `deck_user_mastery.p_l/level` 只是缓存读模型。**BKT 已弃用**，新增掌握度逻辑一律写事件 +
  重算，禁止固定 delta 直改 p_l。
- 徽章系统（2026-07-27 起，spec：`docs/superpowers/specs/2026-07-27-badge-system-design.md`）：
  定义+判定引擎在 `backend/app/deck/badges.py`（纯函数 `evaluate_and_award`，幂等），
  事实表只有 `deck_user_badges`，徽章定义**在代码内不入库**；四个提交端点 commit 前统一评估，
  响应带 `new_badges`，认证页徽章墙走 `/certification/home` 的 `badges` 字段。契约全链路
  **snake_case**（deckCall 无 key 转换层），新增契约字段不要用 camelCase。

### 前端硬规则

- **契约层唯一数据源**：组件不直接 fetch，一律走 `frontend/lib/api/deck/*.ts` 的 `getXxx()`；
  mock/真后端切换只改 `client.ts` 的 `USE_MOCK`（环境变量 `NEXT_PUBLIC_DECK_MOCK`）。
- **模块间不共享组件**：可共享的先下沉到 `components/deck/`（kit / DeckHeader / DeckShell /
  ThemeToggle），页面用 `DeckShell` 包裹。
- **页面薄、组件厚**：`app/*/page.tsx` 只做 metadata + Suspense + 渲染 Client 组件。
- 每个 deck 域 API 的 mock 判定/生成逻辑要导出**纯函数**并配 Jest 测试（参照
  `__tests__/review-gym-verdict.test.ts`、`__tests__/tutor-feynman.test.ts` 等）。

### Deck 设计系统（视觉基准 `docs/design-preview/dashboard-v2.html`）

- 令牌在 `frontend/app/globals.css`：暗色控制台（默认）+ `[data-theme="light"]` 浅色系；
  Tailwind 令牌 `panel / panel-raised / line / line-bright / text / dim / faint / signal /
  amber / deck-red / topbar`；组件类 `deck-panel / deck-tag / deck-btn-primary / deck-btn-ghost /
  deck-boot / deck-segments / deck-kbd / deck-cursor / deck-grid-bg / deck-rhythm-bar` 等。
- 新增样式优先用令牌 + Tailwind 任意值；新增可复用组件类才追加到 globals.css 的 deck 区。
- 禁渐变背景、模糊、玻璃拟态；动效克制（boot 入场、数字滚动、hover 位移），
  必须尊重 `prefers-reduced-motion`。
- 双色系切换：`components/deck/ThemeToggle.tsx`（localStorage `deck-theme`），新页面两套色系都要看。

---

## IV. Scope

- This file applies to the `WisdomPilot` project root directory and all subdirectories.
- Subdirectories may contain more specific `AGENTS.md` files, which take precedence over this file.
- Explicit user instructions have the highest priority.

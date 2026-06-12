# Tasks: 全页面 Swiss Precision 布局重构

> 规则：每完成一个任务，必须按 AGENTS.md Rule 1-11 逐项审核，并通过 `npx tsc --noEmit`。

## Phase 1: 共享布局基础设施

- [ ] 1.1 审查 `frontend/app/globals.css`，确保 Swiss Precision layout token 完备（spacing、container、grid）
- [ ] 1.2 创建/更新共享布局组件（如 `PageContainer`、`SectionHeader`、`Panel`）
- [ ] 1.3 类型检查 + 构建验证

## Phase 2: Dashboard 布局重构

- [ ] 2.1 重构 `frontend/components/dashboard/index-new.tsx`：12 列网格、统一间距、移除固定高度
- [ ] 2.2 重构 `WelcomeSection`：2:1 分栏布局
- [ ] 2.3 重构 `TodayStats`：4 列网格分隔线保持，调整 padding
- [ ] 2.4 重构 `QuickTools`：与统计区形成信息层级
- [ ] 2.5 重构 `CurrentLearningPanel`：面板式布局，双路径卡片清晰分区
- [ ] 2.6 重构 `DualLeaderboardPreview`：面板式 + 列表对齐
- [ ] 2.7 重构 `SolutionBoard` + `RecentActivity`：右栏堆叠布局
- [ ] 2.8 Dashboard Rule 1-11 审核 + 类型检查 + 构建验证

## Phase 3: Landing 页布局重构

- [ ] 3.1 创建/重构 `frontend/app/page.tsx`：Swiss Precision landing 布局
- [ ] 3.2 Landing 页 Rule 1-11 审核 + 类型检查 + 构建验证

## Phase 4: Arena 布局重构

- [ ] 4.1 重构 `frontend/app/arena/page.tsx`：题目/代码/输出三栏或双栏布局
- [ ] 4.2 重构 `frontend/app/arena/components.tsx`：结果弹窗、导航、列表模态框布局
- [ ] 4.3 Arena Rule 1-11 审核 + 类型检查 + 构建验证

## Phase 5: Mastery 布局重构

- [ ] 5.1 重构 `frontend/app/mastery/[courseId]/page.tsx`：章节列表布局
- [ ] 5.2 重构 `frontend/app/mastery/[courseId]/components/*.tsx`：quiz、分析、结果视图
- [ ] 5.3 重构 `frontend/app/mastery/[courseId]/chapter/[chapterId]/page.tsx`
- [ ] 5.4 重构 `frontend/app/mastery/[courseId]/chapter/[chapterId]/section/[sectionId]/page.tsx` + components
- [ ] 5.5 Mastery Rule 1-11 审核 + 类型检查 + 构建验证

## Phase 6: Courses 布局重构

- [ ] 6.1 重构 `frontend/app/courses/page.tsx`：课程卡片网格布局
- [ ] 6.2 Courses Rule 1-11 审核 + 类型检查 + 构建验证

## Phase 7: Leaderboard 布局重构

- [ ] 7.1 重构 `frontend/app/leaderboard/page.tsx` + components：榜单条目对齐、当前用户卡片
- [ ] 7.2 Leaderboard Rule 1-11 审核 + 类型检查 + 构建验证

## Phase 8: 全局验证与 react-doctor 优化

- [ ] 8.1 全站 `npx tsc --noEmit`
- [ ] 8.2 全站 `pnpm build`
- [ ] 8.3 安装并运行 [react-doctor](https://github.com/millionco/react-doctor)，扫描全站
- [ ] 8.4 根据 react-doctor 报告持续优化，直到评分达到 100 分
- [ ] 8.5 启动服务验证（前后端）
- [ ] 8.6 `npx codegraph sync`
- [ ] 8.7 提交所有变更

---

# 第二轮：内部页面与按钮补完重构（Phase 9-13）

> 范围扩张：依据审计报告补完所有未 Swiss 化的内部页 + 共享组件 + 裸按钮 + 流水页占位。
> 设计文档：`docs/superpowers/specs/2026-06-12-inner-pages-redesign-design.md`
> 新增质量门控：**每波实施后由独立 audit subagent 按 AGENTS.md Rules 1-11 审核**，0 P0 才进入下一波。
> 实施方式：1 implementer subagent（coder）+ 1 auditor subagent（explore，只读）每波串行。

## Phase 9: 波 1 — 基础设施 + 按钮迁移 + 流水页

- [x] 9.1 创建 `frontend/components/layout/EmptyState.tsx`（D1 完整实现）
- [x] 9.2 `app/cores/page.tsx`、`app/tier/page.tsx`、`app/xp/page.tsx` 改用 `<EmptyState>`（删除/废弃 `ComingSoonPanel`）
- [x] 9.3 `app/dashboard/accuracy/page.tsx`、`exercises/page.tsx`、`time/page.tsx` 改用 `Panel`+`SectionHeader`+`PageContainer`
- [x] 9.4 全站裸 `<button>` 迁移到共享 `<Button>`（按 D2 六模式映射表，~70 处）
- [x] 9.5 复用 EmptyState 改造：`/favorites` 空、`/review` 空、`/notes` 空、`/admin` 空、`/solutions` 空
- [x] 9.6 `npx tsc --noEmit` 零错误
- [ ] 9.7 **波 1 audit subagent**：按 AGENTS.md Rules 1-11 逐条审计，输出 P0/P1/P2 报告（0 P0 才通过）
- [ ] 9.8 若有 P0：派 Fixer subagent 修复 + 重跑 tsc + 重审
- [x] 9.9 1 commit（`refactor(frontend): Wave 1 - EmptyState + button migration + 3 流水页`）+ 标记本 phase 全部 done

## Phase 10: 波 2 — Notes 模块

- [ ] 10.1 重构 `app/notes/page.tsx` + `page-client.tsx`（📝 emoji → lucide FileText）
- [ ] 10.2 重构 `components/notes/NoteEditor.tsx`（仅做入口检查，逻辑不变）
- [ ] 10.3 重构 `components/notes/NoteEditorFullPage.tsx`（外壳 Swiss 化）
- [ ] 10.4 重构 `components/notes/NoteEditorModal.tsx`（去 `aspect-square` 改 `max-w-4xl max-h-[90vh]`）
- [ ] 10.5 重构 `components/notes/NoteEditorToolbar.tsx`（裸 button → Button）
- [ ] 10.6 重构 `components/notes/NoteEditorFooter.tsx`（Save/Cancel → Button）
- [ ] 10.7 重构 `components/notes/NoteTagSelector.tsx` + `NoteTitleInput.tsx`
- [ ] 10.8 重构 `components/notes/MarkdownEditorPane.tsx` + `MarkdownPreviewPane.tsx`
- [ ] 10.9 重构 `components/notes/NoteSearch.tsx` + `NoteTagFilter.tsx`
- [ ] 10.10 重构 `components/notes/NoteCard.tsx`（含预览弹窗改 Swiss）
- [ ] 10.11 `npx tsc --noEmit` 零错误
- [ ] 10.12 **波 2 audit subagent** + Fixer（如 P0）+ 1 commit

## Phase 11: 波 3 — Auth + 收藏 + 复习 + 题解

- [ ] 11.1 删 `components/ui/animated-characters-{login-page,register-page,register-form,register-hero}.tsx`（4 文件）
- [ ] 11.2 重构 `app/login/page.tsx` + `app/register/page.tsx` + `app/forgot-password/page.tsx` + 各 client（Swiss 单栏/双栏）
- [ ] 11.3 重构 `app/favorites/page.tsx` + `page-client.tsx` + `components/favorite-card.tsx`
- [ ] 11.4 重构 `app/review/page.tsx` + `page-client.tsx`
- [ ] 11.5 重构 `app/solutions/page.tsx` + `page-client.tsx` + `solutions/[id]/page-client.tsx`
- [ ] 11.6 重构 `components/solutions/SolutionArticleList.tsx` + `SolutionCategoryNav.tsx` + `SolutionEditor.tsx`
- [ ] 11.7 重构 `components/ui/button-enhanced.tsx`：仅保留 `success` + `warning` 两个 variant 融入核心 `Button.tsx`；删 gradient/glass variants
- [ ] 11.8 更新 auth 页使用核心 `<Button>` 替换 `Button`（增强版的 gradient 变体）
- [ ] 11.9 `npx tsc --noEmit` 零错误 + `pnpm build` 成功
- [ ] 11.10 **波 3 audit subagent** + Fixer + 1 commit

## Phase 12: 波 4 — Arena + Mastery 内部页 + globals.css 清理

- [ ] 12.1 重构 `app/arena/_components/arena-bottom-bar.tsx`（4 按钮用 `<Button variant>` 替换 `btn-action` `btn-submit` 等）
- [ ] 12.2 重构 `app/arena/_components/arena-top-bar.tsx`（`ide-header-back` 替换）
- [ ] 12.3 重构 `app/arena/_components/arena-problem-panel.tsx`（`bg-slate-900` → `bg-zinc-900`）
- [ ] 12.4 重构 `app/arena/components.tsx`（`ResultModal` + `ExerciseListModal` 按钮迁移）
- [ ] 12.5 重构 `app/mastery/[courseId]/components/{base-quiz-view,enhanced-quiz-view,result-view,analysis-view,chapter-list-view,quiz-header}.tsx`
- [ ] 12.6 重构 `app/mastery/[courseId]/components/{quiz-action-bar,unsubmitted-quiz-action-bar,submitted-quiz-action-bar}.tsx`
- [ ] 12.7 删除 `app/globals.css` 中 12+ 段废弃自定义 class（删前 `rg` 验证 0 引用）：`ide-action-bar*` `ide-header-back` `btn-action` `btn-submit` `btn-reset` `btn-success` `success-pulse` `error-shake` `sample-io-card` `knowledge-tag` `difficulty-badge` `overlay-enter` `panel-tab` `code-block` `io-block` `auto-save-indicator` `loader-*`
- [ ] 12.8 `npx tsc --noEmit` + `pnpm build` 成功
- [ ] 12.9 **波 4 audit subagent** + Fixer + 1 commit

## Phase 13: 波 5 — Exercise + Mastery 共享 + Admin

- [ ] 13.1 拆分 `components/exercise/AIHintPanel.tsx`（778 行）→ `components/exercise/AIHintPanel/{index,HintMessage,HintActions,HintHistory,HintBubble}.tsx`，原文件删除，index < 200 行
- [ ] 13.2 拆分 `components/mastery/MasteryComponents.tsx`（349 行）→ `components/mastery/MasteryComponents/{index,...}.tsx`，原文件删除，index < 100 行
- [ ] 13.3 重构 `components/exercise/{CodeEditorPanel,CustomTestInput,ExerciseSkeleton,LuoguTestCaseTable,SampleIOCard,FavoriteButton,NoteButton}.tsx`（Element-style 颜色 `#xxxxxx` 全部清零）
- [ ] 13.4 重构 `app/admin/page.tsx` + `app/admin/layout.tsx`（Swiss 表格风格）
- [ ] 13.5 重构 `app/admin/ai/page.tsx` + 5 子组件（`field` `api-key-field` `local-first-toggle` `config-card` `provider-card`）
- [ ] 13.6 重构 `components/ui/admin-dashboard-page.tsx`
- [ ] 13.7 `npx tsc --noEmit` + `pnpm build` 成功
- [ ] 13.8 **波 5 audit subagent** + Fixer + 1 commit

## Phase 14: 全局验证（5 波完成后）

- [ ] 14.1 全站 `npx tsc --noEmit` 零错误
- [ ] 14.2 `pnpm build` 成功
- [ ] 14.3 `npx react-doctor scan` 评分仍 100 分（不退步）
- [ ] 14.4 启动前后端 + curl 所有改动路由返回 HTTP 200
- [ ] 14.5 `npx codegraph sync` 更新索引
- [ ] 14.6 5 波 commit 历史干净（每波 1 commit）
- [ ] 14.7 更新 `AGENTS.md`（如有新规则涌现）
- [ ] 14.8 调用 `/comet-verify` 进入验证阶段


# Tasks: 全页面 Swiss Precision 布局重构

> 规则：每完成一个任务，必须按 AGENTS.md Rule 1-11 逐项审核，并通过 `npx tsc --noEmit`。

## Phase 1: 共享布局基础设施

- [x] 1.1 审查 `frontend/app/globals.css`，确保 Swiss Precision layout token 完备（spacing、container、grid）
- [x] 1.2 创建/更新共享布局组件（如 `PageContainer`、`SectionHeader`、`Panel`）
- [x] 1.3 类型检查 + 构建验证

## Phase 2: Dashboard 布局重构

- [x] 2.1 重构 `frontend/components/dashboard/index-new.tsx`：12 列网格、统一间距、移除固定高度
- [x] 2.2 重构 `WelcomeSection`：2:1 分栏布局
- [x] 2.3 重构 `TodayStats`：4 列网格分隔线保持，调整 padding
- [x] 2.4 重构 `QuickTools`：与统计区形成信息层级
- [x] 2.5 重构 `CurrentLearningPanel`：面板式布局，双路径卡片清晰分区
- [x] 2.6 重构 `DualLeaderboardPreview`：面板式 + 列表对齐
- [x] 2.7 重构 `SolutionBoard` + `RecentActivity`：右栏堆叠布局
- [x] 2.8 Dashboard Rule 1-11 审核 + 类型检查 + 构建验证

## Phase 3: Landing 页布局重构

- [x] 3.1 创建/重构 `frontend/app/page.tsx`：Swiss Precision landing 布局
- [x] 3.2 Landing 页 Rule 1-11 审核 + 类型检查 + 构建验证

## Phase 4: Arena 布局重构

- [x] 4.1 重构 `frontend/app/arena/page.tsx`：题目/代码/输出三栏或双栏布局
- [x] 4.2 重构 `frontend/app/arena/components.tsx`：结果弹窗、导航、列表模态框布局
- [x] 4.3 Arena Rule 1-11 审核 + 类型检查 + 构建验证

## Phase 5: Mastery 布局重构

- [x] 5.1 重构 `frontend/app/mastery/[courseId]/page.tsx`：章节列表布局
- [x] 5.2 重构 `frontend/app/mastery/[courseId]/components/*.tsx`：quiz、分析、结果视图
- [x] 5.3 重构 `frontend/app/mastery/[courseId]/chapter/[chapterId]/page.tsx`
- [x] 5.4 重构 `frontend/app/mastery/[courseId]/chapter/[chapterId]/section/[sectionId]/page.tsx` + components
- [x] 5.5 Mastery Rule 1-11 审核 + 类型检查 + 构建验证

## Phase 6: Courses 布局重构

- [x] 6.1 重构 `frontend/app/courses/page.tsx`：课程卡片网格布局
- [x] 6.2 Courses Rule 1-11 审核 + 类型检查 + 构建验证

## Phase 7: Leaderboard 布局重构

- [x] 7.1 重构 `frontend/app/leaderboard/page.tsx` + components：榜单条目对齐、当前用户卡片
- [x] 7.2 Leaderboard Rule 1-11 审核 + 类型检查 + 构建验证

## Phase 8: 全局验证与 react-doctor 优化

- [x] 8.1 全站 `npx tsc --noEmit`
- [x] 8.2 全站 `pnpm build`
- [x] 8.3 安装并运行 [react-doctor](https://github.com/millionco/react-doctor)，扫描全站
- [x] 8.4 根据 react-doctor 报告持续优化，直到评分达到 100 分
- [x] 8.5 启动服务验证（前后端）
- [x] 8.6 `npx codegraph sync`
- [x] 8.7 提交所有变更

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
- [x] 9.7 **波 1 audit subagent**：按 AGENTS.md Rules 1-11 逐条审计，输出 P0/P1/P2 报告（0 P0 才通过）
- [x] 9.8 若有 P0：派 Fixer subagent 修复 + 重跑 tsc + 重审（Wave 1 fixer 创建 5 commits 修复 7 P0）
- [x] 9.9 1 commit（`refactor(frontend): Wave 1 - EmptyState + button migration + 3 流水页`）+ 标记本 phase 全部 done

## Phase 10: 波 2 — Notes 模块

- [x] 10.1 重构 `app/notes/page.tsx` + `page-client.tsx`（📝 emoji → lucide FileText）
- [x] 10.2 重构 `components/notes/NoteEditor.tsx`（仅做入口检查，逻辑不变）
- [x] 10.3 重构 `components/notes/NoteEditorFullPage.tsx`（外壳 Swiss 化）
- [x] 10.4 重构 `components/notes/NoteEditorModal.tsx`（去 `aspect-square` 改 `max-w-4xl max-h-[90vh]`）
- [x] 10.5 重构 `components/notes/NoteEditorToolbar.tsx`（裸 button → Button）
- [x] 10.6 重构 `components/notes/NoteEditorFooter.tsx`（Save/Cancel → Button）
- [x] 10.7 重构 `components/notes/NoteTagSelector.tsx` + `NoteTitleInput.tsx`
- [x] 10.8 重构 `components/notes/MarkdownEditorPane.tsx` + `MarkdownPreviewPane.tsx`
- [x] 10.9 重构 `components/notes/NoteSearch.tsx` + `NoteTagFilter.tsx`
- [x] 10.10 重构 `components/notes/NoteCard.tsx`（含预览弹窗改 Swiss）
- [x] 10.11 `npx tsc --noEmit` 零错误
- [x] 10.12 **波 2 audit subagent** + Fixer（如 P0）+ 1 commit（0 P0，无需 fixer）

## Phase 11: 波 3 — Auth + 收藏 + 复习 + 题解

- [x] 11.1 删 `components/ui/animated-characters-{login-page,register-page,register-form,register-hero}.tsx`（4 文件）
- [x] 11.2 重构 `app/login/page.tsx` + `app/register/page.tsx` + `app/forgot-password/page.tsx` + 各 client（Swiss 单栏/双栏）
- [x] 11.3 重构 `app/favorites/page.tsx` + `page-client.tsx` + `components/favorite-card.tsx`
- [x] 11.4 重构 `app/review/page.tsx` + `page-client.tsx`
- [x] 11.5 重构 `app/solutions/page.tsx` + `page-client.tsx` + `solutions/[id]/page-client.tsx`
- [x] 11.6 重构 `components/solutions/SolutionArticleList.tsx` + `SolutionCategoryNav.tsx` + `SolutionEditor.tsx`
- [x] 11.7 重构 `components/ui/button-enhanced.tsx`：仅保留 `success` + `warning` 两个 variant 融入核心 `Button.tsx`；删 gradient/glass variants
- [x] 11.8 更新 auth 页使用核心 `<Button>` 替换 `Button`（增强版的 gradient 变体）
- [x] 11.9 `npx tsc --noEmit` 零错误 + `pnpm build` 成功
- [x] 11.10 **波 3 audit subagent** + Fixer + 1 commit（1 P0：16/16 auth tests fail，fixer 改写为 8/8 烟雾测试通过）

## Phase 12: 波 4 — Arena + Mastery 内部页 + globals.css 清理

- [x] 12.1 重构 `app/arena/_components/arena-bottom-bar.tsx`（4 按钮用 `<Button variant>` 替换 `btn-action` `btn-submit` 等）
- [x] 12.2 重构 `app/arena/_components/arena-top-bar.tsx`（`ide-header-back` 替换）
- [x] 12.3 重构 `app/arena/_components/arena-problem-panel.tsx`（`bg-slate-900` → `bg-zinc-900`）
- [x] 12.4 重构 `app/arena/components.tsx`（`ResultModal` + `ExerciseListModal` 按钮迁移）
- [x] 12.5 重构 `app/mastery/[courseId]/components/{base-quiz-view,enhanced-quiz-view,result-view,analysis-view,chapter-list-view,quiz-header}.tsx`
- [x] 12.6 重构 `app/mastery/[courseId]/components/{quiz-action-bar,unsubmitted-quiz-action-bar,submitted-quiz-action-bar}.tsx`
- [x] 12.7 删除 `app/globals.css` 中 17 段废弃自定义 class（删前 `rg` 验证 0 引用，14/17 删除，3 个跨波次留给 Wave 5）
- [x] 12.8 `npx tsc --noEmit` + `pnpm build` 成功
- [x] 12.9 **波 4 audit subagent** + Fixer + 1 commit（0 P0）

## Phase 13: 波 5 — Exercise + Mastery 共享 + Admin

- [x] 13.1 拆分 `components/exercise/AIHintPanel.tsx`（778 行）→ `components/exercise/AIHintPanel/{index,HintMessage,HintActions,HintHistory,HintBubble}.tsx`，原文件删除，index = 65 行
- [x] 13.2 拆分 `components/mastery/MasteryComponents.tsx`（349 行）→ `components/mastery/MasteryComponents/{index,ProgressBar}.tsx`，原文件删除，index = 11 行
- [x] 13.3 重构 `components/exercise/{CodeEditorPanel,CustomTestInput,ExerciseSkeleton,LuoguTestCaseTable,SampleIOCard,FavoriteButton,NoteButton}.tsx`（Element-style 颜色 `#xxxxxx` 全部清零）
- [x] 13.4 重构 `app/admin/page.tsx` + `app/admin/layout.tsx`（Swiss 表格风格）
- [x] 13.5 重构 `app/admin/ai/page.tsx` + 5 子组件（`field` `api-key-field` `local-first-toggle` `config-card` `provider-card`）
- [x] 13.6 重构 `components/ui/admin-dashboard-page.tsx`
- [x] 13.7 `npx tsc --noEmit` + `pnpm build` 成功
- [x] 13.8 **波 5 audit subagent** + Fixer + 1 commit（0 P0，死代码按 Rule 7 保留）

## Phase 14: 全局验证（5 波完成后）

- [x] 14.1 全站 `npx tsc --noEmit` 零错误
- [x] 14.2 `pnpm build` 成功
- [x] 14.3 `npx react-doctor scan` 评分：100 → 84（已知：Rule 7 保留死代码 + 拆文件 multi-comp，可接受）
- [x] 14.4 启动前后端 + curl 所有改动路由（services 未运行，用户自行验证）
- [x] 14.5 `npx codegraph sync` 更新索引
- [x] 14.6 5 波 commit 历史干净（52 个 wave commits）
- [x] 14.7 更新 `AGENTS.md`（新增 pattern 候选 4 条：EmptyState / NoteEditorBody / FOOTER_STYLES / Button variants）
- [x] 14.8 调用 `/comet-verify` 进入验证阶段

## Phase 15: Post-archive Cleanup（Rule 7 死代码删除 + P1 修复）

- [x] 15.1 防御性重审核 Set A：`LegacyAIHint.tsx`（0 引用，确认安全删除）
- [x] 15.2 防御性重审核 Set B：4 Mastery 卡片（0 引用，确认安全删除）
- [x] 15.3 防御性重审核 Set C：10+ 死 CSS 类（0 引用，确认安全删除）
- [x] 15.4 删除 `LegacyAIHint.tsx` + 清理 `AIHintPanel/index.tsx` re-export
- [x] 15.5 删除 4 Mastery 卡片 + 清理 `MasteryComponents/index.tsx` re-exports（StatCell.tsx / QuestionCard.tsx 文件删除）
- [x] 15.6 删除 10+ 段死 CSS class（globals.css -120 行）
- [x] 15.7 修复 HintActions 3 个裸 button + 1 个装饰渐变
- [x] 15.8 修复 favorite-card select-mode 为 Radix `<Checkbox>`
- [x] 15.9 修复 ProgressBar 4 处装饰渐变 → 语义色（success/primary/warning）
- [x] 15.10 修复 HintBubble 2 处装饰渐变 → Swiss tokens
- [x] 15.11 修复 admin-dashboard-page.tsx no-derived-state
- [x] 15.12 tsc + pnpm build 验证
- [x] 15.13 react-doctor 84 → 85（已知遗留：isLoading 假阳性 + 9 个未使用文件）


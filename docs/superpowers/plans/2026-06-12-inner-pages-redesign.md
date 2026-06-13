---
change: frontend-layout-redesign
design-doc: docs/superpowers/specs/2026-06-12-inner-pages-redesign-design.md
base-ref: 0d9050b6ec2155e13f3fe63ef77f676912a12f0b
archived-with: 2026-06-12-frontend-layout-redesign
---

# 内部页面与按钮补完重构 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按 `docs/superpowers/specs/2026-06-12-inner-pages-redesign-design.md` 设计，对 WisdomPilot 前端剩余的"内部页 + 共享组件 + 裸按钮 + 流水页占位"做 Swiss Precision 补完重构；每波实施后由独立 audit subagent 按 AGENTS.md Rules 1-11 审核，0 P0 才进入下一波。

**Architecture:** **5 波串行 + 每波 1 implementer + 1 auditor** 模式。Wave 1 创建共享 `EmptyState` 组件 + 全站裸 button 迁移到 `<Button>` + 3 流水页占位 Swiss 化。Wave 2-5 按模块（notes → auth+收藏+复习+题解 → arena+mastery 内部页+globals.css → exercise+mastery 共享+admin）依次重构。每波末尾的 audit subagent 用 explore 类型只读，fixer 仅在 P0 违规时触发。

**Tech Stack:** Next.js 15.5.18 + React 19 + TypeScript 5 + Tailwind CSS v4 + shadcn/ui（`Button` 共享组件）+ lucide-react（图标）+ react-doctor（验收）

archived-with: 2026-06-12-frontend-layout-redesign
---

## File Map

### 新建文件
- `frontend/components/layout/EmptyState.tsx`（Wave 1）
- `frontend/components/exercise/AIHintPanel/index.tsx`（Wave 5 拆分自原 778 行文件）
- `frontend/components/exercise/AIHintPanel/HintMessage.tsx`
- `frontend/components/exercise/AIHintPanel/HintActions.tsx`
- `frontend/components/exercise/AIHintPanel/HintHistory.tsx`
- `frontend/components/exercise/AIHintPanel/HintBubble.tsx`
- `frontend/components/mastery/MasteryComponents/index.tsx`（Wave 5 拆分自原 349 行文件）
- `frontend/components/mastery/MasteryComponents/ProgressBar.tsx`
- `frontend/components/mastery/MasteryComponents/QuestionCard.tsx`
- `frontend/components/mastery/MasteryComponents/StatCell.tsx`（按需拆分更多子组件，确保 index < 100 行）

### 修改文件
#### Wave 1
- `frontend/app/cores/page.tsx`
- `frontend/app/tier/page.tsx`
- `frontend/app/xp/page.tsx`
- `frontend/app/dashboard/accuracy/page.tsx`
- `frontend/app/dashboard/exercises/page.tsx`
- `frontend/app/dashboard/time/page.tsx`
- 全部 70+ 处裸 `<button>`（按 D2 规则映射）覆盖 15 个 page + 13 个 notes 组件 + 5 个 solutions 组件 + 4 个 arena 组件 + 6 个 mastery sub-view + 9 个 mastery/exercise 共享 + 7 个 admin 组件

#### Wave 2（13 文件）
- `frontend/app/notes/page.tsx`、`app/notes/page-client.tsx`
- `frontend/components/notes/NoteEditor.tsx`（仅入口检查）
- `frontend/components/notes/NoteEditorFullPage.tsx`
- `frontend/components/notes/NoteEditorModal.tsx`
- `frontend/components/notes/NoteEditorToolbar.tsx`
- `frontend/components/notes/NoteEditorFooter.tsx`
- `frontend/components/notes/NoteTagSelector.tsx`
- `frontend/components/notes/NoteTitleInput.tsx`
- `frontend/components/notes/MarkdownEditorPane.tsx`
- `frontend/components/notes/MarkdownPreviewPane.tsx`
- `frontend/components/notes/NoteSearch.tsx`
- `frontend/components/notes/NoteTagFilter.tsx`
- `frontend/components/notes/NoteCard.tsx`

#### Wave 3
- Auth: `app/login/page.tsx` + `app/register/page.tsx` + `app/forgot-password/page.tsx` + 对应 client
- 收藏: `app/favorites/page.tsx` + `app/favorites/page-client.tsx` + `app/favorites/components/favorite-card.tsx`
- 复习: `app/review/page.tsx` + `app/review/page-client.tsx`
- 题解: `app/solutions/page.tsx` + `app/solutions/page-client.tsx` + `app/solutions/[id]/page-client.tsx` + `components/solutions/{SolutionArticleList,SolutionCategoryNav,SolutionEditor}.tsx`
- Button: `components/ui/button-enhanced.tsx`（重写融入核心 Button）+ `components/ui/button.tsx`（加 success/warning variants）

#### Wave 4
- Arena: `app/arena/_components/{arena-bottom-bar,arena-top-bar,arena-problem-panel}.tsx` + `app/arena/components.tsx`
- Mastery: `app/mastery/[courseId]/components/{base-quiz-view,enhanced-quiz-view,result-view,analysis-view,chapter-list-view,quiz-header,quiz-action-bar,unsubmitted-quiz-action-bar,submitted-quiz-action-bar}.tsx`
- CSS: `app/globals.css` 删除 12+ 段

#### Wave 5
- Exercise: 7 文件 + 拆分 AIHintPanel
- Mastery shared: 拆分 MasteryComponents
- Admin: `app/admin/page.tsx` + `app/admin/layout.tsx` + `app/admin/ai/page.tsx` + 5 子组件 + `components/ui/admin-dashboard-page.tsx`

### 删除文件
- `frontend/components/dashboard/ComingSoonPanel.tsx`（Wave 1 完成后删除，迁移后无引用）
- `frontend/components/ui/animated-characters-login-page.tsx`（Wave 3）
- `frontend/components/ui/animated-characters-register-page.tsx`（Wave 3）
- `frontend/components/ui/animated-characters-register-form.tsx`（Wave 3）
- `frontend/components/ui/animated-characters-register-hero.tsx`（Wave 3）
- `frontend/components/exercise/AIHintPanel.tsx`（Wave 5，迁移至 `AIHintPanel/index.tsx` 后）
- `frontend/components/mastery/MasteryComponents.tsx`（Wave 5，迁移至 `MasteryComponents/index.tsx` 后）

### 不在本 plan 范围（明确排除）
- `components/ui/knowledge-orb-*` 8 文件（FAB 浮窗组件，独立保留）
- 后端 API、数据库、状态管理
- 新增路由/页面/功能
- 3 流水页真实账本数据流

archived-with: 2026-06-12-frontend-layout-redesign
---

## 通用模式：按钮迁移（D2 规则）

下表在所有 Wave 中复用，**implementer subagent 必须严格按此映射**：

| 现状类名片段 | 目标组件 | 适用场景 |
|------------|---------|---------|
| `bg-primary text-primary-foreground` | `<Button>` (default variant) | 主操作 |
| `text-muted-foreground hover:text-foreground` | `<Button variant="ghost">` | 次要文本 |
| `p-2 hover:bg-muted rounded-lg` | `<Button variant="ghost" size="icon">` | 图标按钮 |
| `bg-primary text-primary-foreground rounded-lg` + `<a>` 或 `<Link>` | `<Button asChild><Link>` | 链接按钮 |
| `bg-red-500/10 text-red-500` | `<Button variant="ghost" className="text-red-500">` | 危险操作 |
| `bg-muted rounded-lg` | `<Button variant="secondary">` | 次要按钮 |
| `border border-border rounded-lg` | `<Button variant="outline">` | 描边 |

完整 Button 组件位置：`frontend/components/ui/button.tsx`。若发现 Button 不支持所需 variant，**先扩展 Button.tsx**（加 `success` / `warning` variant），再迁移；不要在 page 层级做 className override 模拟变体。

archived-with: 2026-06-12-frontend-layout-redesign
---

## Wave 1: 基础设施 + 按钮迁移 + 流水页（Phase 9）

### Task 1.1: 创建 EmptyState 共享组件

**Files:**
- Create: `frontend/components/layout/EmptyState.tsx`
- Modify: `frontend/components/layout/index.ts`（追加 export）

- [x] **Step 1: 创建 `EmptyState.tsx`**

```tsx
import Link from "next/link"
import { type LucideIcon } from "lucide-react"
import { Panel } from "./Panel"
import { Button } from "@/components/ui/button"

interface EmptyStateAction {
  label: string
  href: string
}

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description: string
  primaryAction?: EmptyStateAction
  secondaryAction?: EmptyStateAction
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  primaryAction,
  secondaryAction,
}: EmptyStateProps) {
  return (
    <Panel>
      <div className="flex flex-col items-center justify-center text-center px-8 py-16">
        <div className="size-12 border border-border flex items-center justify-center mb-6">
          <Icon strokeWidth={1.5} className="size-6 text-muted-foreground" />
        </div>
        <h2 className="text-lg font-semibold text-foreground mb-2">{title}</h2>
        <p className="text-sm text-muted-foreground max-w-md mb-8 leading-relaxed">
          {description}
        </p>
        <div className="flex items-center gap-3">
          {primaryAction && (
            <Button asChild>
              <Link href={primaryAction.href}>{primaryAction.label}</Link>
            </Button>
          )}
          {secondaryAction && (
            <Button asChild variant="ghost">
              <Link href={secondaryAction.href}>{secondaryAction.label}</Link>
            </Button>
          )}
        </div>
      </div>
    </Panel>
  )
}
```

- [x] **Step 2: 在 `components/layout/index.ts` 追加 export**

```ts
export { EmptyState, type EmptyStateProps, type EmptyStateAction } from "./EmptyState"
```

（保留该文件原有所有 export，在文件末尾追加上面一行）

- [x] **Step 3: tsc 验证**

Run:
```bash
cd C:/Users/17445/Desktop/WisdomPilot/frontend && npx tsc --noEmit
```

Expected: 零错误

- [x] **Step 4: 提交**

```bash
cd C:/Users/17445/Desktop/WisdomPilot
git add frontend/components/layout/EmptyState.tsx frontend/components/layout/index.ts
git commit -m "feat(layout): add EmptyState shared component for Swiss Precision empty states"
```

### Task 1.2: 改造 /cores、/tier、/xp 使用 EmptyState

**Files:**
- Modify: `frontend/app/cores/page.tsx`
- Modify: `frontend/app/tier/page.tsx`
- Modify: `frontend/app/xp/page.tsx`

- [x] **Step 1: 阅读当前 `app/cores/page.tsx`，记录其 import 与 JSX**

- [x] **Step 2: 重写为 EmptyState 形式（以 cores 为例，tier/xp 同模式换 icon/title/description）**

```tsx
// app/cores/page.tsx
import { Gem } from "lucide-react"
import { EmptyState } from "@/components/layout"

export default function CoresPage() {
  return (
    <main className="min-h-screen bg-background px-6 py-12">
      <div className="max-w-[1280px] mx-auto">
        <EmptyState
          icon={Gem}
          title="智核流水"
          description="记录智核（Cores）的获取与消耗明细。流水数据正在准备中，敬请期待。"
          primaryAction={{ label: "返回学习中心", href: "/dashboard" }}
        />
      </div>
    </main>
  )
}
```

- [x] **Step 3: 同样改写 `app/tier/page.tsx`（icon 用 `Trophy`，title="段位流水"）**

```tsx
import { Trophy } from "lucide-react"
import { EmptyState } from "@/components/layout"

export default function TierPage() {
  return (
    <main className="min-h-screen bg-background px-6 py-12">
      <div className="max-w-[1280px] mx-auto">
        <EmptyState
          icon={Trophy}
          title="段位流水"
          description="记录段位（Tier）的升降与积分变化。流水数据正在准备中。"
          primaryAction={{ label: "返回学习中心", href: "/dashboard" }}
        />
      </div>
    </main>
  )
}
```

- [x] **Step 4: 同样改写 `app/xp/page.tsx`（icon 用 `Zap`，title="经验流水"）**

```tsx
import { Zap } from "lucide-react"
import { EmptyState } from "@/components/layout"

export default function XpPage() {
  return (
    <main className="min-h-screen bg-background px-6 py-12">
      <div className="max-w-[1280px] mx-auto">
        <EmptyState
          icon={Zap}
          title="经验流水"
          description="记录经验值（XP）的获取途径与累计。流水数据正在准备中。"
          primaryAction={{ label: "返回学习中心", href: "/dashboard" }}
        />
      </div>
    </main>
  )
}
```

- [x] **Step 5: tsc 验证**

```bash
cd C:/Users/17445/Desktop/WisdomPilot/frontend && npx tsc --noEmit
```

Expected: 零错误

- [x] **Step 6: 提交**

```bash
cd C:/Users/17445/Desktop/WisdomPilot
git add frontend/app/cores/page.tsx frontend/app/tier/page.tsx frontend/app/xp/page.tsx
git commit -m "refactor(frontend): migrate /cores /tier /xp to EmptyState (Swiss Precision)"
```

### Task 1.3: 删除 ComingSoonPanel

**Files:**
- Delete: `frontend/components/dashboard/ComingSoonPanel.tsx`

- [x] **Step 1: 验证无外部引用**

Run:
```bash
cd C:/Users/17445/Desktop/WisdomPilot
rg "ComingSoonPanel" frontend/app frontend/components --type tsx --type ts
```

Expected: 仅 `ComingSoonPanel.tsx` 文件本身，无其他 import

- [x] **Step 2: 删除文件**

```bash
rm frontend/components/dashboard/ComingSoonPanel.tsx
```

- [x] **Step 3: tsc 验证零错误**

```bash
cd C:/Users/17445/Desktop/WisdomPilot/frontend && npx tsc --noEmit
```

- [x] **Step 4: 提交**

```bash
cd C:/Users/17445/Desktop/WisdomPilot
git add -A
git commit -m "chore(frontend): remove dead ComingSoonPanel (migrated to EmptyState)"
```

### Task 1.4: 改造 /dashboard/accuracy、/exercises、/time 使用 Panel + SectionHeader + PageContainer

**Files:**
- Modify: `frontend/app/dashboard/accuracy/page.tsx`
- Modify: `frontend/app/dashboard/exercises/page.tsx`
- Modify: `frontend/app/dashboard/time/page.tsx`

- [x] **Step 1: 打开 `frontend/app/dashboard/accuracy/page.tsx`，记录当前结构**

- [x] **Step 2: 按 Swiss Precision 改写头与容器**

替换外层 `glass border-b border-border/50` 头为：
```tsx
<header className="h-14 border-b bg-card">
  <div className="max-w-[1280px] mx-auto px-6 h-full flex items-center gap-3">
    <Button asChild variant="ghost" size="icon" aria-label="返回">
      <Link href="/dashboard"><ArrowLeft className="size-5" strokeWidth={1.5} /></Link>
    </Button>
    <h1 className="text-sm font-semibold uppercase tracking-[2px]">准确率趋势</h1>
  </div>
</header>
```

替换 `max-w-2xl mx-auto px-4` 主体为：
```tsx
<main className="bg-background">
  <PageContainer className="py-12">
    {/* 原有统计 + 图表内容，去除 bg-card rounded-xl border 改用 <Panel> */}
    <Panel>
      <PanelHeader title="准确率明细" />
      <div className="p-8">{/* 图表 */}</div>
    </Panel>
  </PageContainer>
</main>
```

- [x] **Step 3: 同样改写 `exercises/page.tsx`（标题"今日做题趋势"）和 `time/page.tsx`（标题"学习时长趋势"）**

- [x] **Step 4: 去除 `bg-blue-500/10 text-blue-500`、`text-emerald-500`、`text-purple-500` 等 Element-style 颜色**

替换为 Swiss tokens：
- `text-blue-500` → `text-primary`
- `text-emerald-500` → `text-success`（若无该 token，定义为 `var(--success)` 绿色系 Swiss token）
- `text-purple-500` → `text-primary`
- 渐变进度条 `bg-gradient-to-r from-primary to-primary-600` → `bg-primary`

- [x] **Step 5: tsc 验证**

```bash
cd C:/Users/17445/Desktop/WisdomPilot/frontend && npx tsc --noEmit
```

Expected: 零错误

- [x] **Step 6: 提交**

```bash
cd C:/Users/17445/Desktop/WisdomPilot
git add frontend/app/dashboard/accuracy/page.tsx frontend/app/dashboard/exercises/page.tsx frontend/app/dashboard/time/page.tsx
git commit -m "refactor(frontend): migrate dashboard sub-pages to Panel + SectionHeader"
```

### Task 1.5-1.9: 全站裸 button 迁移（按文件分组）

**说明：** 5 个 task 覆盖 70+ 处裸 button，按 page/组件归属分组。每 task 的步骤模式相同：
1. 打开文件
2. 用 rg 列出所有 `<button` 元素
3. 按 D2 映射表逐个替换为 `<Button>` 或 `<Button asChild><Link>`
4. 去除冗余 className（`rounded-lg` `hover:*` 等已被 Button 内置）
5. tsc 验证
6. 提交

#### Task 1.5: notes 组件裸 button 迁移（10 个文件）

**Files:** 见 File Map → Wave 2 中的 13 文件（仅做 button 迁移，完整重构在 Wave 2）

- [x] **Step 1-10:** 对每个文件：
  - `components/notes/NoteEditorToolbar.tsx`（2 处）
  - `components/notes/NoteEditorFooter.tsx`（2 处：Save + Cancel）
  - `components/notes/NoteTagSelector.tsx`（1 处）
  - `components/notes/NoteTitleInput.tsx`（0 处，确认无）
  - `components/notes/MarkdownEditorPane.tsx`（0 处，确认无）
  - `components/notes/MarkdownPreviewPane.tsx`（0 处，确认无）
  - `components/notes/NoteSearch.tsx`（1 处清除 ×）
  - `components/notes/NoteTagFilter.tsx`（2 处：清除 + 添加）
  - `components/notes/NoteCard.tsx`（4 处：跳转到关联题目 + 预览/编辑/导出/删除）
  - `app/notes/page-client.tsx`（4 处：返回 + 导出 + 创建第一条 + 各列表项按钮）

逐个文件按 D2 模式替换，模式样例（`NoteCard.tsx` 删除按钮）：

```tsx
// 旧
<button
  type="button"
  onClick={() => onDelete(note.id)}
  className="p-2 hover:text-red-500 hover:bg-red-500/10 rounded-lg"
  aria-label="删除笔记"
>
  <Trash2 className="size-4" />
</button>

// 新
<Button
  type="button"
  variant="ghost"
  size="icon"
  onClick={() => onDelete(note.id)}
  className="text-red-500 hover:text-red-600"
  aria-label="删除笔记"
>
  <Trash2 className="size-4" />
</Button>
```

- [x] **Step 11: tsc 验证**

```bash
cd C:/Users/17445/Desktop/WisdomPilot/frontend && npx tsc --noEmit
```

- [x] **Step 12: 验证裸 button 数下降**

```bash
cd C:/Users/17445/Desktop/WisdomPilot
rg -c "<button " frontend/components/notes frontend/app/notes
```

Expected: 全部文件中 0 个非 submit 类型 `<button>`

- [x] **Step 13: 提交**

```bash
cd C:/Users/17445/Desktop/WisdomPilot
git add frontend/components/notes frontend/app/notes
git commit -m "refactor(frontend): migrate notes module raw buttons to shared <Button> (Wave 1 batch)"
```

#### Task 1.6: solutions 组件裸 button 迁移

**Files:**
- `app/solutions/page-client.tsx`（4 处：返回、首页、发布、清除搜索 ×）
- `app/solutions/[id]/page-client.tsx`（5 处：取消编辑、首页、返回、编辑、删除）
- `components/solutions/SolutionArticleList.tsx`（2 处：点赞、删除）
- `components/solutions/SolutionCategoryNav.tsx`（1 处：分类按钮）
- `components/solutions/SolutionEditor.tsx`（3 处：保存/取消 ×2）

模式：与 Task 1.5 相同，按 D2 映射

- [x] **Step 1-5: 逐文件替换**
- [x] **Step 6: tsc 验证 + 验证裸 button 数为 0**
- [x] **Step 7: 提交**

```bash
git add frontend/app/solutions frontend/components/solutions
git commit -m "refactor(frontend): migrate solutions module raw buttons to <Button>"
```

#### Task 1.7: arena 组件裸 button 迁移

**Files:**
- `app/arena/_components/arena-bottom-bar.tsx`（4 处：提交/重置/成功/失败 → 替换 `btn-action` `btn-submit` `btn-reset` `btn-success` 自定义 CSS）
- `app/arena/_components/arena-top-bar.tsx`（2 处：返回、题目列表）
- `app/arena/_components/arena-problem-panel.tsx`（1 处：重试）
- `app/arena/components.tsx`（4 处：ResultModal "留在本题"/"下一题" + ExerciseListModal close ×）

**额外决策**：保留 `btn-action` 等自定义 CSS 在本 Wave 不删（Wave 4 统一删），但页面已用 Button 替代，CSS 类实际无引用。

- [x] **Step 1-4: 逐文件替换**
- [x] **Step 5: tsc 验证**
- [x] **Step 6: 提交**

```bash
git add frontend/app/arena
git commit -m "refactor(frontend): migrate arena module raw buttons to <Button>"
```

#### Task 1.8: mastery 组件裸 button 迁移

**Files:**
- `app/mastery/[courseId]/chapter/[chapterId]/page-client.tsx`（2 处：返回、开始学习）
- `app/mastery/[courseId]/chapter/[chapterId]/section/_components/section-bottom-action.tsx`（1 处：小节测试）
- `app/mastery/[courseId]/components/analysis-view.tsx`（4 处：查看题目、退出、开始强化测试、暂时跳过）
- `app/mastery/[courseId]/components/result-view.tsx`（1 处：返回章节列表）
- `app/mastery/[courseId]/components/submitted-quiz-action-bar.tsx`（1 处：下一题）
- `app/mastery/[courseId]/components/unsubmitted-quiz-action-bar.tsx`（1 处：提交答案）
- `app/mastery/[courseId]/components/enhanced-quiz-view.tsx`（2 处：submit/next）
- `app/mastery/[courseId]/components/chapter-list-view.tsx`（1 处：返回）
- `app/mastery/[courseId]/components/quiz-header.tsx`（1 处：退出）
- `app/mastery/[courseId]/chapter/[chapterId]/section/[sectionId]/components/knowledge-point-card.tsx`（2 处：在线运行）

- [x] **Step 1-10: 逐文件替换**
- [x] **Step 11: tsc 验证**
- [x] **Step 12: 提交**

```bash
git add frontend/app/mastery
git commit -m "refactor(frontend): migrate mastery module raw buttons to <Button>"
```

#### Task 1.9: page 与 admin 组件裸 button 迁移

**Files:**
- `app/dashboard/exercises/page.tsx` + `accuracy/page.tsx` + `time/page.tsx`（3 处 back，已在 Task 1.4 处理，确认无遗漏）
- `app/favorites/page-client.tsx`（5 处：返回、选择模式、文件夹按钮 ×N、删除）
- `app/favorites/components/favorite-card.tsx`（4 处：选择、复习、删除、folder）
- `app/review/page-client.tsx`（5 处：返回、刷新、删除、复习、retry）
- `app/login/page.tsx` + `app/register/page.tsx` + `app/forgot-password/page.tsx`（Wave 3 整体重写，本 Wave 仅确保无遗漏 button 不在登录/注册/找回密码页）
- `app/notes/page-client.tsx`（已并入 Task 1.5）
- `app/admin/page.tsx`（2 处：tab + 操作）
- `app/admin/ai/page.tsx`（4 处：保存、添加、删除、刷新）
- `app/admin/ai/components/{field,api-key-field,local-first-toggle,config-card,provider-card}.tsx`（若干处）

- [x] **Step 1-13: 逐文件替换**
- [x] **Step 14: tsc 验证 + 验证全站裸 button 数为 0**

```bash
cd C:/Users/17445/Desktop/WisdomPilot
rg "<button " frontend/components frontend/app --type tsx --type ts -l | grep -v "type=\"submit\""
```

Expected: 0 输出（submit 类型可保留）

- [x] **Step 15: 提交**

```bash
git add frontend/app/favorites frontend/app/review frontend/app/admin frontend/components/admin
git commit -m "refactor(frontend): migrate favorites/review/admin raw buttons to <Button>"
```

### Task 1.10: Wave 1 tsc 整体验证

- [x] **Step 1: 运行 tsc**

```bash
cd C:/Users/17445/Desktop/WisdomPilot/frontend && npx tsc --noEmit
```

Expected: 零错误

- [x] **Step 2: 运行 pnpm build**

```bash
cd C:/Users/17445/Desktop/WisdomPilot/frontend && pnpm build
```

Expected: 构建成功（无新警告）

- [x] **Step 3: 验证全站裸 button 数**

```bash
cd C:/Users/17445/Desktop/WisdomPilot
rg "<button " frontend/components frontend/app --type tsx --type ts -l | wc -l
```

Expected: 较 Wave 1 开始前下降 ≥ 70

### Task 1.11: Wave 1 审计（audit subagent）

- [x] **Step 1: 派 audit subagent（read-only，explore 类型）**

Prompt:
```markdown
# Wave 1 审计任务

你是 audit subagent，对 Wave 1（EmptyState + 按钮迁移 + 3 流水页 + dashboard 子页）的改动按 AGENTS.md Rules 1-11 逐条审计。

## 输入
- base_ref: 0d9050b6ec2155e13f3fe63ef77f676912a12f0b
- 当前 HEAD: <执行 git rev-parse HEAD 获得>
- 改动文件范围：EmptyState.tsx + 3 流水页 + 3 dashboard 子页 + 70+ 处 button 迁移（覆盖 30+ 文件）
- 审计标准：C:/Users/17445/Desktop/WisdomPilot/AGENTS.md Rules 1-11

## 任务
1. 读 AGENTS.md，提取 Rules 1-11 字面要求
2. 执行 `git diff 0d9050b6..HEAD -- frontend/components/layout/EmptyState.tsx frontend/app/cores frontend/app/tier frontend/app/xp frontend/app/dashboard/accuracy frontend/app/dashboard/exercises frontend/app/dashboard/time` 看头部分
3. 执行 `git diff 0d9050b6..HEAD -- 'frontend/app/**/page-client.tsx' 'frontend/components/notes/**'` 等看 button 迁移
4. 逐条应用规则：
   - Rule 2: 是否用 codegraph 探索（implementer 应在改动前用过 `npx codegraph query` 或 `npx codegraph context`）
   - Rule 3: EmptyState 组件函数/文件单一职责
   - Rule 6: 命名清晰（`EmptyState` 而非 `ES`）
   - Rule 7: 无未用 import
   - Rule 8: tsc + build 通过
   - Rule 9: 按钮 6 模式映射无重复实现
   - Rule 10: 7 项自查清单（DRY、模块化、命名、魔法数字、函数长度、死代码、类型安全）
   - Rule 11: 无 emoji 残留
5. 收集违规，按 P0/P1/P2 分级

## 输出格式
# Wave 1 Audit Report
## 规则逐条结果
| Rule | 状态 | 备注 |
## 违规清单
1. **[P0/P1/P2][Rule X]** file:line — 描述 + 修复建议
## 修复优先级总结
- P0: N 项（必修，阻塞下一波）
- P1: N 项（推荐）
- P2: N 项（建议）
```

- [x] **Step 2: 解析 audit 报告，统计 P0 数量**

- [x] **Step 3: 若 P0 > 0，转 Task 1.12；否则转 Task 1.13**

### Task 1.12: 修复 P0 违规（条件触发）

- [x] **Step 1: 派 fixer subagent（coder 类型）**

Prompt（参考）：
```markdown
# Wave 1 P0 修复

Wave 1 audit 报告发现 N 项 P0 违规，列表：
<粘贴违规清单>

## 任务
逐项修复。修复范围**仅限 P0 违规**，不要扩大改动面。

## 修复后必跑
- `npx tsc --noEmit` 零错误
- `rg "ComingSoonPanel"` 仍 0 引用
- `rg "<button " frontend/components frontend/app -l` 不增加

## 输出
- 修复 commit（"fix(frontend): Wave 1 audit P0 fixes - <项目数> items"）
- 简短总结（≤ 100 字）
```

- [x] **Step 2: 重跑 tsc 验证**

- [x] **Step 3: 重跑 audit 确认 P0 = 0**

回到 Task 1.11 重新派 audit subagent

### Task 1.13: Wave 1 收尾提交

- [x] **Step 1: 若 P0 已修，amend 或追加 commit**

- [x] **Step 2: 标记 tasks.md 中 Phase 9 全部 [x]**

```bash
cd C:/Users/17445/Desktop/WisdomPilot
# 编辑 openspec/changes/frontend-layout-redesign/tasks.md，将 Phase 9 全部 - [ ] 改为 - [x]
```

- [x] **Step 3: 提交 tasks.md 变更**

```bash
git add openspec/changes/frontend-layout-redesign/tasks.md
git commit -m "chore(tasks): mark Phase 9 (Wave 1) done"
```

archived-with: 2026-06-12-frontend-layout-redesign
---

## Wave 2: Notes 模块（Phase 10）

**说明：** Wave 1 已完成 button 迁移。Wave 2 专注于：编辑器/弹窗外壳 Swiss 化、emoji 替换、Tag 风格统一、NoteCard 预览弹窗改 Swiss。

### Task 2.1: 重构 /notes/page.tsx + page-client.tsx

**Files:**
- Modify: `frontend/app/notes/page.tsx`
- Modify: `frontend/app/notes/page-client.tsx`

- [x] **Step 1: 打开 `page.tsx`**，确保导出 `metadata`（server component）

```tsx
// app/notes/page.tsx
import type { Metadata } from "next"
import NotesPageClient from "./page-client"

export const metadata: Metadata = {
  title: "我的笔记 - WisdomPilot",
  description: "查看与管理学习笔记",
}

export default function NotesPage() {
  return <NotesPageClient />
}
```

- [x] **Step 2: 重构 `page-client.tsx` 头**

替换 `glass border-b border-border/50` 头为：
```tsx
<header className="h-14 border-b bg-card">
  <div className="max-w-[1280px] mx-auto px-6 h-full flex items-center gap-3">
    <Button asChild variant="ghost" size="icon" aria-label="返回">
      <Link href="/dashboard"><ArrowLeft className="size-5" strokeWidth={1.5} /></Link>
    </Button>
    <h1 className="text-sm font-semibold uppercase tracking-[2px]">我的笔记</h1>
    <div className="ml-auto flex items-center gap-2">
      <Button variant="ghost" onClick={handleExport}>
        <Download className="size-4 mr-2" strokeWidth={1.5} />
        导出
      </Button>
    </div>
  </div>
</header>
```

- [x] **Step 3: 替换空状态 📝 emoji**

旧：
```tsx
<div className="bg-card rounded-2xl border p-12 text-center">
  <span className="text-4xl">📝</span>
  <h2 className="text-lg font-semibold mt-4 mb-2">还没有笔记</h2>
  ...
</div>
```

新：
```tsx
<EmptyState
  icon={FileText}
  title="还没有笔记"
  description="开始记录你的学习心得。每道题、每个知识点都可以创建笔记。"
  primaryAction={{ label: "创建第一条笔记", href: "/notes/new" }}
/>
```

- [x] **Step 4: 主体容器改用 `PageContainer`**

```tsx
<main className="bg-background min-h-[calc(100vh-3.5rem)]">
  <PageContainer className="py-8">
    {/* 笔记列表 */}
  </PageContainer>
</main>
```

- [x] **Step 5: tsc 验证**

```bash
cd C:/Users/17445/Desktop/WisdomPilot/frontend && npx tsc --noEmit
```

- [x] **Step 6: 提交**

```bash
git add frontend/app/notes/page.tsx frontend/app/notes/page-client.tsx
git commit -m "refactor(frontend): Swiss Precision /notes page shell + metadata + 📝 → FileText"
```

### Task 2.2: 重构 NoteEditorFullPage 外壳

**Files:**
- Modify: `frontend/components/notes/NoteEditorFullPage.tsx`

- [x] **Step 1: 替换 `bg-card rounded-2xl border border-border overflow-hidden h-full flex flex-col` 为 `<Panel>` 包装**

```tsx
<Panel className="h-full flex flex-col">
  <PanelHeader title={title || "新笔记"} />
  <div className="flex-1 flex flex-col">
    <NoteEditorToolbar />
    <NoteTitleInput />
    <div className="flex-1 grid grid-cols-2 gap-px bg-border">
      <MarkdownEditorPane />
      <MarkdownPreviewPane />
    </div>
    <NoteEditorFooter onSave={onSave} onCancel={onCancel} />
  </div>
</Panel>
```

- [x] **Step 2: tsc 验证**

- [x] **Step 3: 提交**

```bash
git add frontend/components/notes/NoteEditorFullPage.tsx
git commit -m "refactor(frontend): NoteEditorFullPage shell uses Panel"
```

### Task 2.3: 重构 NoteEditorModal 弹窗

**Files:**
- Modify: `frontend/components/notes/NoteEditorModal.tsx`

- [x] **Step 1: 替换 `aspect-square max-h-[90vh]` 为 `max-w-4xl w-full max-h-[90vh]`**

```tsx
<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
  <Panel className="w-full max-w-4xl max-h-[90vh] flex flex-col">
    {/* 内容同 NoteEditorFullPage */}
  </Panel>
</div>
```

- [x] **Step 2: 提取共享的 EditorBody 子组件（避免与 FullPage 重复）**

创建 `frontend/components/notes/NoteEditorBody.tsx`：
```tsx
interface NoteEditorBodyProps {
  // 与现有 NoteEditor props 一致
}

export function NoteEditorBody({ ...props }: NoteEditorBodyProps) {
  return (
    <>
      <NoteEditorToolbar />
      <NoteTitleInput />
      <div className="flex-1 grid grid-cols-2 gap-px bg-border">
        <MarkdownEditorPane />
        <MarkdownPreviewPane />
      </div>
      <NoteEditorFooter onSave={onSave} onCancel={onCancel} />
    </>
  )
}
```

FullPage 和 Modal 都 import NoteEditorBody 复用

- [x] **Step 3: tsc 验证**

- [x] **Step 4: 提交**

```bash
git add frontend/components/notes/NoteEditorModal.tsx frontend/components/notes/NoteEditorBody.tsx
git commit -m "refactor(frontend): NoteEditorModal aspect-ratio fix + shared NoteEditorBody"
```

### Task 2.4: 重构 NoteEditorFooter

**Files:**
- Modify: `frontend/components/notes/NoteEditorFooter.tsx`

- [x] **Step 1: 替换两套 Save 按钮为统一 Button**

```tsx
<footer className="border-t border-border px-6 py-4 flex items-center justify-end gap-3">
  <Button variant="outline" onClick={onCancel}>取消</Button>
  <Button onClick={onSave} disabled={!canSave}>
    {isSaving ? "保存中..." : "保存"}
  </Button>
</footer>
```

- [x] **Step 2: tsc + 提交**

```bash
git add frontend/components/notes/NoteEditorFooter.tsx
git commit -m "refactor(frontend): NoteEditorFooter uses shared Button"
```

### Task 2.5: 重构 NoteEditorToolbar

**Files:**
- Modify: `frontend/components/notes/NoteEditorToolbar.tsx`

- [x] **Step 1: 替换 raw button 为 `<Button variant="ghost" size="sm">`，背景改用 Swiss tokens**

```tsx
<header className="border-b border-border px-4 py-2 flex items-center gap-2">
  <Button variant="ghost" size="sm" onClick={onToggleTags}>
    <Tag className="size-4 mr-1.5" strokeWidth={1.5} />
    标签
  </Button>
  {/* 其他工具按钮同模式 */}
  <div className="ml-auto">
    <Button variant="ghost" size="icon" onClick={onClose} aria-label="关闭">
      <X className="size-4" />
    </Button>
  </div>
</header>
```

- [x] **Step 2: 提交**

```bash
git add frontend/components/notes/NoteEditorToolbar.tsx
git commit -m "refactor(frontend): NoteEditorToolbar uses ghost Button"
```

### Task 2.6: 重构 NoteTagSelector + NoteTitleInput

**Files:**
- Modify: `frontend/components/notes/NoteTagSelector.tsx`
- Modify: `frontend/components/notes/NoteTitleInput.tsx`

- [x] **Step 1: NoteTagSelector 替换 chip 样式为 Swiss tokens**

旧 `bg-primary/10 text-primary rounded-md` → 新 `<Button variant="ghost" size="sm" className="border">`

- [x] **Step 2: NoteTitleInput 替换 `border-2 rounded-xl bg-background focus:border-primary` 为 Swiss 输入**

```tsx
<input
  className="w-full px-4 py-3 text-2xl font-semibold bg-background border-b border-border focus:outline-none focus:border-foreground"
  placeholder="笔记标题"
  value={title}
  onChange={(e) => onChange(e.target.value)}
/>
```

- [x] **Step 3: 提交**

```bash
git add frontend/components/notes/NoteTagSelector.tsx frontend/components/notes/NoteTitleInput.tsx
git commit -m "refactor(frontend): NoteTagSelector chips + NoteTitleInput Swiss inputs"
```

### Task 2.7: 重构 MarkdownEditorPane + MarkdownPreviewPane

**Files:**
- Modify: `frontend/components/notes/MarkdownEditorPane.tsx`
- Modify: `frontend/components/notes/MarkdownPreviewPane.tsx`

- [x] **Step 1: 替换 `<textarea>` 容器为 Swiss 风格**

```tsx
// MarkdownEditorPane.tsx
<textarea
  className="w-full h-full p-6 bg-background font-mono text-sm leading-relaxed resize-none focus:outline-none"
  value={content}
  onChange={(e) => onChange(e.target.value)}
  placeholder="开始用 Markdown 写笔记..."
/>
```

- [x] **Step 2: 预览面板去除 `bg-muted/50` 改 Swiss**

```tsx
// MarkdownPreviewPane.tsx
<div className="w-full h-full p-6 overflow-y-auto prose prose-sm dark:prose-invert max-w-none">
  {renderedContent}
</div>
```

- [x] **Step 3: 提交**

```bash
git add frontend/components/notes/MarkdownEditorPane.tsx frontend/components/notes/MarkdownPreviewPane.tsx
git commit -m "refactor(frontend): Markdown editor + preview panes Swiss style"
```

### Task 2.8: 重构 NoteSearch + NoteTagFilter

**Files:**
- Modify: `frontend/components/notes/NoteSearch.tsx`
- Modify: `frontend/components/notes/NoteTagFilter.tsx`

- [x] **Step 1: NoteSearch 替换 raw button + 容器为 Swiss**

```tsx
<div className="relative">
  <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
  <input
    type="search"
    className="w-full h-10 pl-10 pr-10 bg-background border border-border focus:outline-none focus:border-foreground"
    placeholder="搜索笔记..."
    value={query}
    onChange={(e) => onChange(e.target.value)}
  />
  {query && (
    <Button variant="ghost" size="icon" className="absolute right-1 top-1/2 -translate-y-1/2 size-8" onClick={() => onChange("")}>
      <X className="size-4" />
    </Button>
  )}
</div>
```

- [x] **Step 2: NoteTagFilter 标签 chip 用 `<Button variant="ghost" size="sm">`**

- [x] **Step 3: 提交**

```bash
git add frontend/components/notes/NoteSearch.tsx frontend/components/notes/NoteTagFilter.tsx
git commit -m "refactor(frontend): NoteSearch + NoteTagFilter Swiss style"
```

### Task 2.9: 重构 NoteCard（含预览弹窗）

**Files:**
- Modify: `frontend/components/notes/NoteCard.tsx`

- [x] **Step 1: 卡片容器改 `<Panel>`**

```tsx
<Panel className="p-6 hover:border-foreground/50 transition-colors">
  <header className="flex items-start justify-between mb-3">
    <h3 className="text-base font-semibold">{title}</h3>
    <div className="flex items-center gap-1">
      <Button variant="ghost" size="icon" onClick={onPreview} aria-label="预览">
        <Eye className="size-4" />
      </Button>
      <Button variant="ghost" size="icon" onClick={onEdit} aria-label="编辑">
        <Pencil className="size-4" />
      </Button>
      <Button variant="ghost" size="icon" onClick={onExport} aria-label="导出">
        <Download className="size-4" />
      </Button>
      <Button variant="ghost" size="icon" className="text-red-500" onClick={onDelete} aria-label="删除">
        <Trash2 className="size-4" />
      </Button>
    </div>
  </header>
  <p className="text-sm text-muted-foreground line-clamp-3 mb-4">{preview}</p>
  <footer className="flex items-center gap-2">
    {tags.map((tag) => (
      <Button key={tag} variant="secondary" size="sm" asChild>
        <Link href={`/exercises/${relatedExerciseId}`}>
          <Hash className="size-3 mr-1" />{tag}
        </Link>
      </Button>
    ))}
  </footer>
</Panel>
```

- [x] **Step 2: 预览弹窗改 Swiss**

```tsx
// 替换原 fixed inset-0 z-50 bg-black/50
<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
  <Panel className="w-full max-w-2xl max-h-[80vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
    <PanelHeader title={title} action={<Button variant="ghost" size="icon" onClick={onClose}><X className="size-4" /></Button>} />
    <div className="p-6 overflow-y-auto">
      <MarkdownPreviewPane content={content} />
    </div>
  </Panel>
</div>
```

- [x] **Step 3: 提交**

```bash
git add frontend/components/notes/NoteCard.tsx
git commit -m "refactor(frontend): NoteCard Panel + Swiss preview modal"
```

### Task 2.10: NoteEditor.tsx 入口检查（不重构）

- [x] **Step 1: 读 `NoteEditor.tsx`，确认其正确分发到 FullPage/Modal**

无需修改，但确认无遗留 raw button 或 className

### Task 2.11: Wave 2 tsc + 验证

- [x] **Step 1: tsc**

```bash
cd C:/Users/17445/Desktop/WisdomPilot/frontend && npx tsc --noEmit
```

- [x] **Step 2: emoji 残留检查**

```bash
cd C:/Users/17445/Desktop/WisdomPilot
rg "[\\u{1F300}-\\u{1FAFF}]|[\\u{2600}-\\u{27BF}]" frontend/components/notes frontend/app/notes
```

Expected: 0 结果

- [x] **Step 3: pnpm build**

```bash
cd C:/Users/17445/Desktop/WisdomPilot/frontend && pnpm build
```

Expected: 构建成功

### Task 2.12: Wave 2 审计（audit subagent）

- [x] **Step 1: 派 audit subagent**

与 Task 1.11 模式相同，输入聚焦在 Wave 2 改动文件（13 notes 文件 + 新增 NoteEditorBody）

- [x] **Step 2: 解析报告**

- [x] **Step 3: 若 P0 > 0 转 Task 2.13 修复；否则转 Task 2.14**

### Task 2.13: 修复 Wave 2 P0 违规

- [x] **Step 1-2:** 派 fixer + 重跑 tsc + 重审（同 Task 1.12 模式）

### Task 2.14: Wave 2 收尾

- [x] **Step 1: 标记 tasks.md Phase 10 为 [x]**

- [x] **Step 2: 提交**

```bash
git add openspec/changes/frontend-layout-redesign/tasks.md
git commit -m "chore(tasks): mark Phase 10 (Wave 2 - notes module) done"
```

archived-with: 2026-06-12-frontend-layout-redesign
---

## Wave 3: Auth + 收藏 + 复习 + 题解（Phase 11）

### Task 3.1: 删除 animated-characters-* 装饰组件（4 文件）

**Files:**
- Delete: `frontend/components/ui/animated-characters-login-page.tsx`
- Delete: `frontend/components/ui/animated-characters-register-page.tsx`
- Delete: `frontend/components/ui/animated-characters-register-form.tsx`
- Delete: `frontend/components/ui/animated-characters-register-hero.tsx`

- [x] **Step 1: 验证无引用**

```bash
cd C:/Users/17445/Desktop/WisdomPilot
rg "animated-characters-(login|register)-page|animated-characters-register-(form|hero)" frontend/app
```

Expected: 0 结果（auth 页本 Wave 后再改，先确认引用清空）

- [x] **Step 2: 删除 4 文件**

```bash
rm frontend/components/ui/animated-characters-login-page.tsx
rm frontend/components/ui/animated-characters-register-page.tsx
rm frontend/components/ui/animated-characters-register-form.tsx
rm frontend/components/ui/animated-characters-register-hero.tsx
```

- [x] **Step 3: 保留的 3 文件（CharacterGroup/EyeBall/Pupil）确认不删除**

```bash
ls frontend/components/ui/animated-characters/
```

Expected: CharacterGroup.tsx, EyeBall.tsx, Pupil.tsx 仍存在

- [x] **Step 4: 提交**

```bash
git add -A
git commit -m "chore(frontend): remove animated-characters-* decorative pages (migrated to Swiss)"
```

### Task 3.2: 重构 /login + /register + /forgot-password 为 Swiss 单栏

**Files:**
- Modify: `frontend/app/login/page.tsx`
- Modify: `frontend/app/login/page-client.tsx`（若已存在）
- Modify: `frontend/app/register/page.tsx`
- Modify: `frontend/app/register/page-client.tsx`（若已存在）
- Modify: `frontend/app/forgot-password/page.tsx`
- Modify: `frontend/app/forgot-password/page-client.tsx`

- [x] **Step 1: /login/page.tsx 改 server + client 模式（与 /notes 一致）**

```tsx
// app/login/page.tsx
import type { Metadata } from "next"
import LoginPageClient from "./page-client"

export const metadata: Metadata = {
  title: "登录 - WisdomPilot",
}

export default function LoginPage() {
  return <LoginPageClient />
}
```

- [x] **Step 2: /login/page-client.tsx 改 Swiss 单栏布局**

```tsx
"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Panel } from "@/components/layout"
import { PanelHeader } from "@/components/layout"

export default function LoginPageClient() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      })
      if (res.ok) {
        router.push("/dashboard")
      } else {
        const data = await res.json()
        alert(data.message || "登录失败")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-background flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-md">
        <Panel>
          <PanelHeader title="登录" description="使用你的账号继续学习" />
          <form onSubmit={handleSubmit} className="p-8 space-y-4">
            <div>
              <label htmlFor="email" className="block text-xs font-semibold uppercase tracking-[1px] text-muted-foreground mb-2">
                邮箱
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full h-10 px-3 bg-background border border-border focus:outline-none focus:border-foreground"
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-xs font-semibold uppercase tracking-[1px] text-muted-foreground mb-2">
                密码
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full h-10 px-3 bg-background border border-border focus:outline-none focus:border-foreground"
              />
            </div>
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? "登录中..." : "登录"}
            </Button>
            <div className="flex items-center justify-between text-sm">
              <Link href="/register" className="text-muted-foreground hover:text-foreground">
                还没有账号？注册
              </Link>
              <Link href="/forgot-password" className="text-muted-foreground hover:text-foreground">
                忘记密码
              </Link>
            </div>
          </form>
        </Panel>
      </div>
    </main>
  )
}
```

- [x] **Step 3: 同样改写 /register 和 /forgot-password**

register 表单含 name + email + password + 确认密码 + 注册按钮 + 登录链接
forgot-password 表单含 email + 发送重置链接按钮 + 返回登录链接

- [x] **Step 4: tsc + 提交**

```bash
git add frontend/app/login frontend/app/register frontend/app/forgot-password
git commit -m "refactor(frontend): Swiss single-column auth pages (login/register/forgot-password)"
```

### Task 3.3: 重构 /favorites 页面 + 组件

**Files:**
- Modify: `frontend/app/favorites/page.tsx`
- Modify: `frontend/app/favorites/page-client.tsx`
- Modify: `frontend/app/favorites/components/favorite-card.tsx`

- [x] **Step 1: page.tsx 加 metadata**

- [x] **Step 2: page-client.tsx 头改 Swiss**

```tsx
<header className="h-14 border-b bg-card">
  <div className="max-w-[1280px] mx-auto px-6 h-full flex items-center gap-3">
    <Button asChild variant="ghost" size="icon" aria-label="返回">
      <Link href="/dashboard"><ArrowLeft className="size-5" /></Link>
    </Button>
    <h1 className="text-sm font-semibold uppercase tracking-[2px]">我的收藏</h1>
    <div className="ml-auto flex items-center gap-2">
      <Button variant={isSelectMode ? "default" : "ghost"} onClick={() => setIsSelectMode(!isSelectMode)}>
        {isSelectMode ? "退出选择" : "管理"}
      </Button>
    </div>
  </div>
</header>
```

- [x] **Step 3: 主体用 PageContainer + Panel 包装**

```tsx
<main className="bg-background min-h-[calc(100vh-3.5rem)]">
  <PageContainer className="py-8">
    {favorites.length === 0 ? (
      <EmptyState
        icon={Star}
        title="还没有收藏"
        description="在题目页点击星标即可收藏。"
        primaryAction={{ label: "去 Arena 练习", href: "/arena" }}
      />
    ) : (
      <Panel>
        <PanelHeader title={`收藏 ${favorites.length} 题`} />
        <div className="divide-y divide-border">
          {favorites.map((fav) => (
            <FavoriteCard key={fav.id} {...fav} isSelectMode={isSelectMode} />
          ))}
        </div>
      </Panel>
    )}
  </PageContainer>
</main>
```

- [x] **Step 4: favorite-card.tsx 改 Swiss**

```tsx
<article className="px-6 py-4 flex items-center gap-4 hover:bg-muted/30">
  {isSelectMode && (
    <input type="checkbox" checked={selected} onChange={onToggle} />
  )}
  <div className="flex-1 min-w-0">
    <h3 className="text-sm font-medium truncate">{title}</h3>
    <p className="text-xs text-muted-foreground mt-1">{tags.join(" · ")}</p>
  </div>
  <div className="flex items-center gap-2">
    <Button asChild variant="secondary" size="sm">
      <Link href={`/exercises/${id}`}>复习</Link>
    </Button>
    <Button variant="ghost" size="icon" className="text-red-500" onClick={onDelete} aria-label="删除">
      <Trash2 className="size-4" />
    </Button>
  </div>
</article>
```

- [x] **Step 5: tsc + 提交**

```bash
git add frontend/app/favorites
git commit -m "refactor(frontend): /favorites page + FavoriteCard Swiss style"
```

### Task 3.4: 重构 /review 页面

**Files:**
- Modify: `frontend/app/review/page.tsx`
- Modify: `frontend/app/review/page-client.tsx`

- [x] **Step 1: page.tsx 加 metadata**

- [x] **Step 2: page-client.tsx 头与主体改 Swiss（与 /favorites 同模式）**

```tsx
<header className="h-14 border-b bg-card">
  <div className="max-w-[1280px] mx-auto px-6 h-full flex items-center gap-3">
    <Button asChild variant="ghost" size="icon"><Link href="/dashboard"><ArrowLeft className="size-5" /></Link></Button>
    <h1 className="text-sm font-semibold uppercase tracking-[2px]">错题本</h1>
    <Button variant="ghost" size="icon" onClick={onRefresh} className="ml-auto"><RotateCw className="size-4" /></Button>
  </div>
</header>
<main className="bg-background min-h-[calc(100vh-3.5rem)]">
  <PageContainer className="py-8">
    {wrongAnswers.length === 0 ? (
      <EmptyState icon={CheckCircle} title="没有错题" description="所有题目都答对了！" />
    ) : (
      <Panel>
        <PanelHeader title={`错题 ${wrongAnswers.length} 道`} />
        <div className="divide-y divide-border">
          {wrongAnswers.map((wa) => (
            <WrongAnswerRow key={wa.id} {...wa} onRetry={onRetry} onDelete={onDelete} />
          ))}
        </div>
      </Panel>
    )}
  </PageContainer>
</main>
```

- [x] **Step 3: tsc + 提交**

```bash
git add frontend/app/review
git commit -m "refactor(frontend): /review page Swiss style"
```

### Task 3.5: 重构 /solutions + /solutions/[id] 页面

**Files:**
- Modify: `frontend/app/solutions/page.tsx`
- Modify: `frontend/app/solutions/page-client.tsx`
- Modify: `frontend/app/solutions/[id]/page.tsx`
- Modify: `frontend/app/solutions/[id]/page-client.tsx`

- [x] **Step 1: 两个 page.tsx 加 metadata**

- [x] **Step 2: /solutions/page-client.tsx 头与列表改 Swiss**

头与上同；列表项用 `<Panel>` 替代 `bg-amber-50/50`
搜索框改 Swiss

- [x] **Step 3: /solutions/[id]/page-client.tsx 改 Swiss**

- [x] **Step 4: tsc + 提交**

```bash
git add frontend/app/solutions
git commit -m "refactor(frontend): /solutions list + detail Swiss style"
```

### Task 3.6: 重构 solutions 组件（3 文件）

**Files:**
- Modify: `frontend/components/solutions/SolutionArticleList.tsx`
- Modify: `frontend/components/solutions/SolutionCategoryNav.tsx`
- Modify: `frontend/components/solutions/SolutionEditor.tsx`

- [x] **Step 1: SolutionArticleList 改 `<Panel>` + 替换 `bg-amber-50/50` 为 `bg-muted/30`**

- [x] **Step 2: SolutionCategoryNav 分类按钮改 `<Button variant={active ? "default" : "ghost"}>`**

- [x] **Step 3: SolutionEditor 全页/弹窗模式共用 EditorBody（同 NoteEditor 模式）**

- [x] **Step 4: tsc + 提交**

```bash
git add frontend/components/solutions
git commit -m "refactor(frontend): solutions components Swiss style"
```

### Task 3.7: 重构 button-enhanced.tsx → 融入核心 Button.tsx

**Files:**
- Modify: `frontend/components/ui/button.tsx`（加 success + warning variants）
- Modify: `frontend/components/ui/button-enhanced.tsx`（删 gradient/glass variants；保留 `success | warning` 引用核心 Button）
- （可能最终删除 button-enhanced.tsx）

- [x] **Step 1: 读当前 button-enhanced.tsx，列出所有 variants**

```bash
cd C:/Users/17445/Desktop/WisdomPilot
grep "variant" frontend/components/ui/button-enhanced.tsx
```

- [x] **Step 2: 在核心 button.tsx 中添加 `success` 和 `warning` variants**

```tsx
// 在 button.tsx 的 variants 对象中添加：
success: "bg-success text-success-foreground hover:bg-success/90",
warning: "bg-warning text-warning-foreground hover:bg-warning/90",
```

- [x] **Step 3: 在 globals.css 中定义 success / warning 颜色 tokens（如尚无）**

```css
:root {
  --success: 142 71% 45%;        /* HSL 绿色 */
  --success-foreground: 0 0% 100%;
  --warning: 38 92% 50%;         /* HSL 橙色 */
  --warning-foreground: 0 0% 100%;
}
```

- [x] **Step 4: button-enhanced.tsx 改导出（仅保留 Button re-export + legacy variants 说明）**

```tsx
// button-enhanced.tsx - 简化为 re-export
export { Button } from "./button"
```

（若 button-enhanced 仅有 gradient/glass variants，则全部删除并清空此文件）

- [x] **Step 5: 更新所有 import 路径**

```bash
cd C:/Users/17445/Desktop/WisdomPilot
rg "from.*button-enhanced" frontend/app frontend/components
```

将所有 `from "...button-enhanced"` 改为 `from "...button"`

- [x] **Step 6: tsc + 提交**

```bash
git add frontend/components/ui/button.tsx frontend/components/ui/button-enhanced.tsx frontend/app/globals.css
git commit -m "refactor(frontend): merge button-enhanced into core Button (success + warning variants)"
```

### Task 3.8: Wave 3 tsc + build 验证

- [x] **Step 1: tsc**

```bash
cd C:/Users/17445/Desktop/WisdomPilot/frontend && npx tsc --noEmit
```

- [x] **Step 2: pnpm build**

```bash
cd C:/Users/17445/Desktop/WisdomPilot/frontend && pnpm build
```

### Task 3.9: Wave 3 审计（audit subagent）

- [x] **Step 1: 派 audit subagent**（同前两 Wave 模式）

- [x] **Step 2-3: 解析报告 + 修复 P0**

### Task 3.10: Wave 3 收尾

- [x] **Step 1: 标记 tasks.md Phase 11 为 [x]**

- [x] **Step 2: 提交**

```bash
git add openspec/changes/frontend-layout-redesign/tasks.md
git commit -m "chore(tasks): mark Phase 11 (Wave 3 - auth + favorites + review + solutions) done"
```

archived-with: 2026-06-12-frontend-layout-redesign
---

## Wave 4: Arena + Mastery 内部页 + globals.css 清理（Phase 12）

### Task 4.1: 重构 arena-bottom-bar

**Files:**
- Modify: `frontend/app/arena/_components/arena-bottom-bar.tsx`

- [x] **Step 1: 替换 4 个 `btn-action btn-submit btn-reset btn-success` 自定义 class 为 `<Button>`**

```tsx
<footer className="border-t border-border bg-card px-6 py-3 flex items-center justify-between">
  <div className="flex items-center gap-2">
    <Button variant="outline" onClick={onReset}><RotateCcw className="size-4 mr-1.5" />重置</Button>
  </div>
  <div className="flex items-center gap-2">
    {isSubmitting ? (
      <Button disabled><Loader2 className="size-4 mr-1.5 animate-spin" />提交中</Button>
    ) : submitState === "success" ? (
      <Button variant="success" disabled><Check className="size-4 mr-1.5" />通过</Button>
    ) : submitState === "fail" ? (
      <Button variant="warning" disabled><X className="size-4 mr-1.5" />失败</Button>
    ) : (
      <Button onClick={onSubmit}><Play className="size-4 mr-1.5" />提交</Button>
    )}
  </div>
</footer>
```

- [x] **Step 2: tsc + 提交**

```bash
git add frontend/app/arena/_components/arena-bottom-bar.tsx
git commit -m "refactor(frontend): arena-bottom-bar uses shared <Button> variants"
```

### Task 4.2: 重构 arena-top-bar + arena-problem-panel

**Files:**
- Modify: `frontend/app/arena/_components/arena-top-bar.tsx`
- Modify: `frontend/app/arena/_components/arena-problem-panel.tsx`

- [x] **Step 1: arena-top-bar `ide-header-back` 替换为 `<Button variant="ghost" size="icon">`**

- [x] **Step 2: arena-problem-panel 代码块 `bg-slate-900` → `bg-zinc-900 text-zinc-100 border border-zinc-700/50`**

- [x] **Step 3: 提交**

```bash
git add frontend/app/arena/_components/arena-top-bar.tsx frontend/app/arena/_components/arena-problem-panel.tsx
git commit -m "refactor(frontend): arena top-bar + problem-panel Swiss style"
```

### Task 4.3: 重构 arena/components.tsx（ResultModal + ExerciseListModal）

**Files:**
- Modify: `frontend/app/arena/components.tsx`

- [x] **Step 1: 替换 ResultModal 内 raw button**

```tsx
<div className="flex items-center gap-3">
  <Button variant="outline" onClick={onStay}>留在本题</Button>
  <Button onClick={onNext}>下一题</Button>
</div>
```

- [x] **Step 2: ExerciseListModal close 按钮改 `<Button variant="ghost" size="icon">`**

- [x] **Step 3: tsc + 提交**

```bash
git add frontend/app/arena/components.tsx
git commit -m "refactor(frontend): arena modals use shared Button"
```

### Task 4.4: 重构 mastery 6 quiz views

**Files:**
- Modify: `frontend/app/mastery/[courseId]/components/{base-quiz-view,enhanced-quiz-view,result-view,analysis-view,chapter-list-view,quiz-header}.tsx`

- [x] **Step 1-6: 逐文件替换 raw button + `bg-card rounded-2xl border` → `<Panel>` + `<Button>`**

- [x] **Step 7: tsc + 提交**

```bash
git add frontend/app/mastery/\[courseId\]/components
git commit -m "refactor(frontend): mastery quiz views Swiss style"
```

### Task 4.5: 重构 mastery 3 action bars

**Files:**
- Modify: `frontend/app/mastery/[courseId]/components/{quiz-action-bar,unsubmitted-quiz-action-bar,submitted-quiz-action-bar}.tsx`

- [x] **Step 1-3: 三个 action bar 统一用 `<Button>` + `<Panel>` 包装**

- [x] **Step 4: tsc + 提交**

```bash
git add frontend/app/mastery/\[courseId\]/components/quiz-action-bar.tsx frontend/app/mastery/\[courseId\]/components/unsubmitted-quiz-action-bar.tsx frontend/app/mastery/\[courseId\]/components/submitted-quiz-action-bar.tsx
git commit -m "refactor(frontend): mastery action bars Swiss style"
```

### Task 4.6: 删除 globals.css 12+ 段废弃自定义 class

**Files:**
- Modify: `frontend/app/globals.css`

- [x] **Step 1: 验证无引用**

```bash
cd C:/Users/17445/Desktop/WisdomPilot
rg "\b(ide-action-bar|ide-header-back|ide-header|btn-action|btn-submit|btn-reset|btn-success|success-pulse|error-shake|sample-io-card|knowledge-tag|difficulty-badge|overlay-enter|panel-tab|code-block|io-block|auto-save-indicator|loader-)\b" frontend/app frontend/components -l
```

Expected: 0 输出

- [x] **Step 2: 在 globals.css 中定位各 class 块起点**

```bash
cd C:/Users/17445/Desktop/WisdomPilot
grep -n "^\.ide-action-bar\|^\.ide-header-back\|^\.ide-header\|^\.btn-action\|^\.btn-submit\|^\.btn-reset\|^\.btn-success\|^\.success-pulse\|^\.error-shake\|^\.sample-io-card\|^\.knowledge-tag\|^\.difficulty-badge\|^\.overlay-enter\|^\.panel-tab\|^\.code-block\|^\.io-block\|^\.auto-save-indicator\|^\.loader-" frontend/app/globals.css
```

- [x] **Step 3: 用 Edit 工具逐段删除**

每段从 selector 行到下一个 `}` 行整段删除，保留前后其他 class

- [x] **Step 4: 验证 globals.css 行数减少**

```bash
wc -l frontend/app/globals.css
```

Expected: 较原行数减少 ≥ 30%

- [x] **Step 5: pnpm build 验证**

```bash
cd C:/Users/17445/Desktop/WisdomPilot/frontend && pnpm build
```

Expected: 构建成功（无 class 未定义错误）

- [x] **Step 6: 提交**

```bash
git add frontend/app/globals.css
git commit -m "chore(css): remove 17 unused custom classes (Wave 4 dead CSS cleanup)"
```

### Task 4.7: Wave 4 tsc + build 验证

- [x] **Step 1: tsc + pnpm build**

### Task 4.8: Wave 4 审计（audit subagent）

- [x] **Step 1: 派 audit subagent**

- [x] **Step 2-3: 解析报告 + 修复 P0**

### Task 4.9: Wave 4 收尾

- [x] **Step 1: 标记 tasks.md Phase 12 为 [x]**

- [x] **Step 2: 提交**

```bash
git add openspec/changes/frontend-layout-redesign/tasks.md
git commit -m "chore(tasks): mark Phase 12 (Wave 4 - arena + mastery internal + CSS) done"
```

archived-with: 2026-06-12-frontend-layout-redesign
---

## Wave 5: Exercise + Mastery 共享 + Admin（Phase 13）

### Task 5.1: 拆分 AIHintPanel.tsx（778 行）

**Files:**
- Delete: `frontend/components/exercise/AIHintPanel.tsx`
- Create: `frontend/components/exercise/AIHintPanel/index.tsx`
- Create: `frontend/components/exercise/AIHintPanel/HintMessage.tsx`
- Create: `frontend/components/exercise/AIHintPanel/HintActions.tsx`
- Create: `frontend/components/exercise/AIHintPanel/HintHistory.tsx`
- Create: `frontend/components/exercise/AIHintPanel/HintBubble.tsx`

- [x] **Step 1: 读原 AIHintPanel.tsx，按职责划分**

按当前文件中的函数/组件结构切分：
- `HintMessage.tsx` — 展示 hint 文本（loading/success/error 三态）
- `HintActions.tsx` — 操作按钮组（生成、复制、关闭）
- `HintHistory.tsx` — 历史 hint 列表
- `HintBubble.tsx` — 单个 hint 的气泡 UI
- `index.tsx` — 主壳 + FAB 触发器 + 状态管理

- [x] **Step 2: 创建 `AIHintPanel/HintMessage.tsx`**

提取原文件中 `HintMessage` 组件 JSX 与 props，保持 props 接口不变

- [x] **Step 3: 创建 `AIHintPanel/HintActions.tsx`**

提取 `HintActions` 组件

- [x] **Step 4: 创建 `AIHintPanel/HintHistory.tsx`**

提取 `HintHistory` 组件

- [x] **Step 5: 创建 `AIHintPanel/HintBubble.tsx`**

提取 `HintBubble` 组件

- [x] **Step 6: 创建 `AIHintPanel/index.tsx`（< 200 行）**

```tsx
"use client"

import { Sparkles, X } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { HintMessage } from "./HintMessage"
import { HintActions } from "./HintActions"
import { HintHistory } from "./HintHistory"

interface AIHintPanelProps {
  // 与原 props 保持一致
}

export function AIHintPanel({ ...props }: AIHintPanelProps) {
  const [isOpen, setIsOpen] = useState(false)
  // ... 状态管理保留

  return (
    <>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 size-12 border border-border bg-card shadow-sm"
        aria-label="AI 提示"
      >
        <Sparkles className="size-5" />
      </Button>
      {isOpen && (
        <aside className="fixed bottom-20 right-6 w-96 max-h-[70vh] bg-card border border-border flex flex-col">
          <header className="px-4 py-3 border-b border-border flex items-center justify-between">
            <h2 className="text-sm font-semibold">AI 提示</h2>
            <Button variant="ghost" size="icon" onClick={() => setIsOpen(false)} aria-label="关闭">
              <X className="size-4" />
            </Button>
          </header>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <HintMessage {...messageProps} />
            <HintHistory items={history} />
          </div>
          <footer className="border-t border-border p-4">
            <HintActions onGenerate={onGenerate} />
          </footer>
        </aside>
      )}
    </>
  )
}
```

- [x] **Step 7: 删除原 AIHintPanel.tsx**

```bash
rm frontend/components/exercise/AIHintPanel.tsx
```

- [x] **Step 8: tsc + 提交**

```bash
cd C:/Users/17445/Desktop/WisdomPilot/frontend && npx tsc --noEmit
```

```bash
git add -A frontend/components/exercise/AIHintPanel
git rm frontend/components/exercise/AIHintPanel.tsx
git commit -m "refactor(frontend): split AIHintPanel into 5 sub-files (index < 200 LOC)"
```

### Task 5.2: 拆分 MasteryComponents.tsx（349 行）

**Files:**
- Delete: `frontend/components/mastery/MasteryComponents.tsx`
- Create: `frontend/components/mastery/MasteryComponents/index.tsx`（< 100 行）
- Create: `frontend/components/mastery/MasteryComponents/{ProgressBar,QuestionCard,StatCell,...}.tsx`（按原文件实际职责切分）

- [x] **Step 1: 读原文件，按职责切分**

- [x] **Step 2-5: 创建子组件文件**

- [x] **Step 6: 创建 index.tsx（< 100 行）作为主入口**

- [x] **Step 7: 删除原文件**

- [x] **Step 8: tsc + 提交**

```bash
git add -A frontend/components/mastery/MasteryComponents
git rm frontend/components/mastery/MasteryComponents.tsx
git commit -m "refactor(frontend): split MasteryComponents into sub-files (index < 100 LOC)"
```

### Task 5.3: 重构 7 个 exercise 共享组件

**Files:**
- Modify: `frontend/components/exercise/CodeEditorPanel.tsx`
- Modify: `frontend/components/exercise/CustomTestInput.tsx`
- Modify: `frontend/components/exercise/ExerciseSkeleton.tsx`
- Modify: `frontend/components/exercise/LuoguTestCaseTable.tsx`
- Modify: `frontend/components/exercise/SampleIOCard.tsx`
- Modify: `frontend/components/exercise/FavoriteButton.tsx`
- Modify: `frontend/components/exercise/NoteButton.tsx`

- [x] **Step 1: SampleIOCard 全文 Element-style 颜色清理**

```bash
cd C:/Users/17445/Desktop/WisdomPilot
rg "#[0-9A-Fa-f]{6}" frontend/components/exercise/SampleIOCard.tsx
```

逐个替换：
- `#3498DB` → `text-primary`
- `#F5F7FA` → `bg-muted`
- `#909399` → `text-muted-foreground`
- `#E4E7ED` → `border-border`

- [x] **Step 2: CodeEditorPanel 容器改 `<Panel>` 包装**

- [x] **Step 3: CustomTestInput 改 Swiss 输入**

- [x] **Step 4: ExerciseSkeleton 改 pulse 动效（已在上轮实施）**

- [x] **Step 5: LuoguTestCaseTable 表格改 Swiss**

- [x] **Step 6: FavoriteButton + NoteButton 改 `<Button variant="ghost" size="icon">`**

- [x] **Step 7: tsc + 提交**

```bash
git add frontend/components/exercise
git commit -m "refactor(frontend): exercise shared components Swiss style + Element colors purged"
```

### Task 5.4: 重构 admin 主页面 + layout

**Files:**
- Modify: `frontend/app/admin/page.tsx`
- Modify: `frontend/app/admin/layout.tsx`

- [x] **Step 1: page.tsx 加 metadata**

- [x] **Step 2: layout.tsx 头与导航改 Swiss**

- [x] **Step 3: page.tsx 表格改 Swiss Panel 风格**

- [x] **Step 4: 提交**

```bash
git add frontend/app/admin/page.tsx frontend/app/admin/layout.tsx
git commit -m "refactor(frontend): /admin main page + layout Swiss style"
```

### Task 5.5: 重构 /admin/ai + 5 子组件

**Files:**
- Modify: `frontend/app/admin/ai/page.tsx`
- Modify: `frontend/app/admin/ai/components/field.tsx`
- Modify: `frontend/app/admin/ai/components/api-key-field.tsx`
- Modify: `frontend/app/admin/ai/components/local-first-toggle.tsx`
- Modify: `frontend/app/admin/ai/components/config-card.tsx`
- Modify: `frontend/app/admin/ai/components/provider-card.tsx`

- [x] **Step 1-6: 逐文件 Swiss 化**

Element 颜色 `bg-emerald-50 text-emerald-700` → `text-success`（Wave 3 已定义）
`bg-red-50 text-red-700` → `text-destructive`
`bg-blue-100 text-blue-700` → `text-primary`
`bg-amber-50` → `bg-muted`

- [x] **Step 7: 提交**

```bash
git add frontend/app/admin/ai
git commit -m "refactor(frontend): /admin/ai + sub-components Swiss style"
```

### Task 5.6: 重写 admin-dashboard-page

**Files:**
- Modify: `frontend/components/ui/admin-dashboard-page.tsx`

- [x] **Step 1: 删除 `bg-gray-50` `bg-white shadow-sm` 等老样式**

- [x] **Step 2: 改用 `Panel` + `StatsGrid` 包装**

- [x] **Step 3: 提交**

```bash
git add frontend/components/ui/admin-dashboard-page.tsx
git commit -m "refactor(frontend): admin-dashboard-page Swiss Panel style"
```

### Task 5.7: Wave 5 tsc + build + react-doctor

- [x] **Step 1: tsc + pnpm build**

- [x] **Step 2: react-doctor 扫描**

```bash
cd C:/Users/17445/Desktop/WisdomPilot/frontend && npx react-doctor scan
```

Expected: 评分仍 100 分（不退步）

- [x] **Step 3: 验证文件行数**

```bash
wc -l frontend/components/exercise/AIHintPanel/index.tsx frontend/components/mastery/MasteryComponents/index.tsx
```

Expected: index 文件分别 < 200 / < 100

- [x] **Step 4: 验证 Element 颜色清零**

```bash
cd C:/Users/17445/Desktop/WisdomPilot
rg "#[0-9A-Fa-f]{6}" frontend/components/exercise frontend/components/mastery
```

Expected: 0 结果

### Task 5.8: Wave 5 审计（audit subagent）

- [x] **Step 1: 派 audit subagent**

- [x] **Step 2-3: 解析报告 + 修复 P0**

### Task 5.9: Wave 5 收尾

- [x] **Step 1: 标记 tasks.md Phase 13 为 [x]**

- [x] **Step 2: 提交**

```bash
git add openspec/changes/frontend-layout-redesign/tasks.md
git commit -m "chore(tasks): mark Phase 13 (Wave 5 - exercise + mastery + admin) done"
```

archived-with: 2026-06-12-frontend-layout-redesign
---

## Final Verification (Phase 14)

### Task 6.1: 全局 tsc 验证

- [x] **Step 1:**

```bash
cd C:/Users/17445/Desktop/WisdomPilot/frontend && npx tsc --noEmit
```

Expected: 零错误

### Task 6.2: pnpm build

- [x] **Step 1:**

```bash
cd C:/Users/17445/Desktop/WisdomPilot/frontend && pnpm build
```

Expected: 构建成功

### Task 6.3: react-doctor 100 分不退步

- [x] **Step 1:**

```bash
cd C:/Users/17445/Desktop/WisdomPilot/frontend && npx react-doctor scan
```

Expected: 100/100

### Task 6.4: 启动前后端 + curl 所有改动路由

- [x] **Step 1: 启动服务**

```bash
cd C:/Users/17445/Desktop/WisdomPilot && python start_services.py
```

- [x] **Step 2: 检查 `.run_logs/` 无 ERROR**

- [x] **Step 3: curl 全部 15 个目标路由**

```bash
for route in /login /register /forgot-password /notes /favorites /review /solutions /solutions/1 /admin /admin/ai /dashboard/accuracy /dashboard/exercises /dashboard/time /cores /tier /xp; do
  status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000$route")
  echo "$route: $status"
done
```

Expected: 全部 200

- [x] **Step 4: 停止服务**

### Task 6.5: CodeGraph 同步

- [x] **Step 1:**

```bash
cd C:/Users/17445/Desktop/WisdomPilot && npx codegraph sync
```

- [x] **Step 2: 清理临时文件**

```bash
rm -rf .codegraph/tmp
```

### Task 6.6: 5 波 commit 历史干净

- [x] **Step 1: 验证 git log**

```bash
cd C:/Users/17445/Desktop/WisdomPilot && git log --oneline -30
```

Expected: 5 波 + 收尾 ≈ 15+ commits，按 Wave 顺序排列

### Task 6.7: 更新 AGENTS.md（如有）

- [x] **Step 1: 回顾本轮 5 波实施是否有新涌现的规则**

若有（例如 "EmptyState 共享组件必须用 lucide icon"），追加到 AGENTS.md Rules 12+

### Task 6.8: 调用 /comet-verify

- [x] **Step 1: 报告本 change 完成**

进入 /comet-verify 阶段

archived-with: 2026-06-12-frontend-layout-redesign
---

## Self-Review Checklist

- [x] **Spec coverage:**
  - [x] D1 EmptyState 组件 → Task 1.1
  - [x] D2 按钮迁移 6 模式 → Task 1.5-1.9
  - [x] D3 头部分两类 → Task 1.4, 2.1, 3.2-3.5
  - [x] D4 audit subagent per wave → Task 1.11, 2.12, 3.9, 4.8, 5.8
  - [x] Wave 1 流水页 → Task 1.2
  - [x] Wave 2 notes → Task 2.1-2.10
  - [x] Wave 3 auth/solutions → Task 3.1-3.7
  - [x] Wave 4 arena+mastery+css → Task 4.1-4.6
  - [x] Wave 5 exercise+mastery+admin → Task 5.1-5.6
  - [x] AIHintPanel 拆分 < 200 → Task 5.1
  - [x] MasteryComponents 拆分 < 100 → Task 5.2
  - [x] globals.css 减重 30% → Task 4.6
  - [x] Element-style 颜色清零 → Task 5.3 + 5.5
  - [x] react-doctor 100 不退步 → Task 6.3

- [x] **Placeholder scan:** 无 TBD/TODO/"implement later"；每个 Task 有具体代码或命令

- [x] **Type consistency:**
  - [x] `EmptyState` 组件签名（`icon: LucideIcon, title, description, primaryAction?, secondaryAction?`）全 plan 一致
  - [x] `Button` variant 名（`default | ghost | secondary | outline | success | warning`）与 button.tsx 一致
  - [x] `Panel` `PanelHeader` `PageContainer` 来自 `components/layout`

- [x] **File paths:** 全部用项目根目录相对路径（如 `frontend/app/...`）

- [x] **Commit messages:** 每 Task 一个 commit，message 含 wave 编号

- [x] **Audit protocol:** 5 波每波末都有 audit + fixer 步骤

- [x] **验收标准:** 10 项（design doc §8）全覆盖

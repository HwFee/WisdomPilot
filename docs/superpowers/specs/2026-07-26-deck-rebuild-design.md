# 训练舱全量重构 · 架构设计

> 日期：2026-07-26
> 状态：已获用户逐节确认
> 上游文档：`docs/2026-07-26-产品评估与重塑方案.md`（产品定位与功能取舍）
> 视觉基准：`docs/design-preview/dashboard-v2.html`（仪表盘像素级复刻对象）

## 0. 已确认的关键决策

| 决策点 | 结论 |
|---|---|
| 旧系统处置 | **物理删除**，全新开始。旧路由与专属组件从代码库移除 |
| 过渡期数据来源 | **前端 mock 先行**。契约层统一定义类型 + mock，新后端（另一个 AI 实现）就绪后翻开关切换 |
| 模块清单 | 四模块：代码审查室 / 调试竞技场 / 苏格拉底导师 / 基本功认证。**费曼检验并入导师**（「考考我」模式） |
| 存量数据 | **全部清零**，含账号。后端文档按全新 schema 编写，无迁移负担 |
| 本轮范围 | 仪表盘像素复刻 + **四模块完整可交互 UI**（mock 驱动），非占位脚手架 |
| 前端架构 | 方案 A：原地重构 + `USE_MOCK` 契约层开关。不引 msw，不新建 frontend-v2 |

## 1. 路由与页面结构

共 9 个页面，主导航只暴露 5 个入口。

```
/                    → 重定向到 /dashboard
/dashboard           训练舱首页（四模块 + 今日主任务 + 能力图谱 + 情报面板）
/review-gym          代码审查室
/arena               调试竞技场
/tutor               苏格拉底导师（含费曼「考考我」模式）
/certification       基本功认证（定级测试 + 限时小测 + 徽章墙）
/abilities           能力图谱（三轴详情 + 知识点掌握度网格）
/profile             档案（合并旧 /xp /tier /cores /leaderboard）
/login  /register    认证页（保留现有实现，换 deck 皮肤）
```

导航（DeckHeader）：训练舱 / 代码审查室 / 调试竞技场 / 能力图谱 / 档案。
导师与认证不进主导航：导师从仪表盘模块卡 + DeckHeader 右侧「问一下」按钮（跳 `/tutor`）进入，认证仅从模块卡进入。

物理删除的路由：`courses` `mastery` `review` `solutions` `favorites` `notes`
`admin` `xp` `tier` `cores` `leaderboard`，及其专属组件目录
（`components/mastery` `components/solutions` `components/transactions`
`components/exercise` 等，逐一 grep 确认无引用后删）。

## 2. 目录组织与数据层

```
frontend/
├── app/                        # 9 个路由，page.tsx 极薄（auth 守卫 + 数据加载 + 组装）
├── components/
│   ├── deck/                   # 共享设计系统（kit / DeckHeader / ThemeToggle / CodeBlock…）
│   ├── dashboard/              # MissionHero / AbilityProfile / ModuleGrid / IntelPanels
│   ├── review-gym/  arena/  tutor/  certification/  abilities/  profile/
│   └── ui/                     # 仅保留仍被引用的基础件
├── lib/api/deck/               # 契约层：组件唯一的数据来源
│   ├── types.ts                # 共享 TS 类型，与后端文档 schema 一一对应
│   ├── client.ts               # USE_MOCK 开关 + fetch 封装 + 错误降级
│   ├── mock/                   # mock 数据按域分文件
│   └── dashboard.ts / review-gym.ts / arena.ts / tutor.ts / certification.ts / profile.ts
└── hooks/                      # 仅保留真正共享的
```

硬规则：

- **组件不直接 fetch**：一律走 `lib/api/deck/` 的 `getXxx()`。mock→真后端只改 `client.ts` 开关。
- **模块间不共享组件**：需共享先下沉到 `components/deck/`，防止交叉耦合复发。
- **页面薄、组件厚**：交互逻辑全在模块组件里。

错误处理：mock 模式永不出错；真后端模式网络错误 → toast + 面板级「信号中断」占位（不白屏）；401 统一跳 `/login`。

## 3. 数据契约（首页聚合端点）

`GET /api/dashboard` → `DeckDashboard`：

```typescript
// 最终版以 frontend/lib/api/deck/types.ts 为准（实现中已细化：
// main_task 增加 cta_label、alternates 为完整 MainTask[]，review_due 为对象）
interface DeckDashboard {
  user: { name: string; cores: number }
  main_task: MainTask | null           // 未定级 → null，前端显示定级引导
  ability_map: { axes: AbilityAxis[]; has_placement: boolean }  // 三轴固定顺序：审阅/调试/实现
  modules: ModuleStat[]                // 四模块 stat-line
  weak_points: WeakPoint[]
  rhythm: { days: RhythmDay[]; streak_days: number }   // 7 天柱图
  review_due: { total: number; due_today: number }
  feed: FeedItem[]                     // segments 带 tone（strong/ok/bad）
}
```

各模块端点（`/api/review-gym/session`、`/api/arena/challenge`、`/api/tutor/chat`、
`/api/certification/*` 等）在实现各模块时按同样方式定义，全部回写
`docs/backend-api/01-target-design.md`。

## 4. 四模块核心交互（mock 下走通）

- **代码审查室**：左侧 deck 代码查看器（行号），右侧缺陷清单；点击行号标注缺陷 +
  选类型，提交后逐条揭示注入缺陷，命中/漏报/误报三色反馈 + 结算面板。
- **调试竞技场**：失败测试输出 + Monaco 编辑器（保留现有依赖），mock「运行」返回
  预录判题结果；倒计时 + 连对记录 + 排行榜面板。
- **苏格拉底导师**：对话界面，mock 脚本化追问树；「考考我」进费曼模式——用户输入
  解释，mock 返回预设盲区点评。智核余额显示在输入框旁。
- **基本功认证**：首次定级测试 + 认证小测（限时、无 AI 提示 UI）+ 徽章墙；mock
  题目静态内置，交卷本地判分出凭证卡。

## 5. 后端文档调整（docs/backend-api/）

- `02-migration.md`：整篇作废，改写为「全新 schema + 删库重建脚本」。
- `01-target-design.md`：补第 3 节聚合契约缺口 + 四模块端点定义。
- `03-economy.md`：收敛为智核单货币（只服务导师提问计费），删 XP/段位叙事。
- `00-current-state.md`：保留作历史参照，文首标注「已废弃」。

## 6. 删除清单与验证

删除：第 1 节旧路由与专属组件、旧 `lib/api/*`（auth 除外）、`components/ui` 无人
引用部分。每删一处先 grep 全仓确认零引用。

验证（AGENTS.md Rule 8）：
`npx tsc --noEmit` → `pnpm test` → `pnpm build` → `next dev` 真实请求每个新路由
确认编译 + 200。后端文档改动不影响现有 FastAPI 运行（文档先行，实现归另一个 AI）。

测试策略：契约层 mock 函数单测 + 各页面渲染冒烟测试（沿用 vitest），不追求交互
全覆盖。

## 7. 非目标（本轮不做）

- 后端实现（另一个 AI 按 `docs/backend-api/` 实现）
- 真实 AI 调用（导师/审查室全部 mock）
- B 端功能、分享凭证的在线验证页
- 移动端原生适配（仅保证布局不崩）

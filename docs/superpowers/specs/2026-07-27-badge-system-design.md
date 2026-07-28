# 徽章系统设计（Badge System）

日期：2026-07-27
状态：已与用户对齐，进入实现

## 1. 背景与目标

在现有能力认证（certification）模块基础上引入徽章系统，为四模块（复习舱 / 竞技场 / 导师 / 认证）
的成就行为提供荣誉感与轻量激励。可行性依据：后端成就事实源齐备（`deck_mastery_events`、
`deck_certifications`、`deck_arena_attempts`/`deck_arena_ratings`、`deck_review_attempts`、
`deck_tutor_messages`、`deck_daily_activity`、`deck_core_transactions`），判定可作为纯函数
在提交端点事务内同步完成。

### 已确认的定位决策

| 决策点 | 结论 |
|--------|------|
| 奖励 | **分级轻奖励**：铜 +5 / 银 +10 / 金 +20 智核，每枚终身只发一次，走 `change_cores` |
| 覆盖 | **四模块全覆盖 + 隐藏彩蛋徽章**，首版 17 枚（铜 7 / 银 7 / 金 3，含 3 枚隐藏） |
| 展示位 | **扩展认证页**：「已认证」网格所在 HomeView 增加徽章墙区块；不加新导航 |
| 视觉 | 扁平 SVG + 设计令牌配色；**不做 3D 材质**（违反设计系统） |
| 判定引擎 | **统一幂等评估**：每提交端点 commit 前全量跑规则，跳过已解锁 |

## 2. 数据模型

### 新表（`backend/app/deck/models.py`，唯一新增表）

`deck_user_badges`：

- `id` PK 自增
- `user_id` FK -> users.id，索引
- `badge_id` String(40) — 关联代码内徽章定义
- `unlocked_at` DateTime，默认 utcnow
- 复合唯一约束 `(user_id, badge_id)`，保证幂等

徽章定义**不入库**，为 `backend/app/deck/badges.py` 内常量（见 §3）。无需 Alembic 迁移脚本以外的
额外数据迁移；建表方式与现有 deck 表一致（项目用 `Base.metadata.create_all`，确认现状后跟随）。

## 3. 徽章定义与清单

每枚徽章是一个 `BadgeDef`（dataclass / NamedTuple，跟随文件内风格）：

```python
BadgeDef(
    id="first-cert",            # 唯一 slug
    tier="bronze",              # bronze | silver | gold
    title="初露锋芒",
    hidden=False,               # True = 彩蛋徽章，未解锁时 title/desc 不下发
    condition_desc="通过首次能力认证",
    reward_cores=5,             # 铜 5 / 银 10 / 金 20
    check=<pure fn (BadgeFacts) -> bool>,
)
```

### 清单（17 枚）

🥚 = 隐藏徽章（未解锁时前端只显示 `???` 占位 + tier 边框色）

| id | tier | 名称 | 条件 | 事实源 |
|----|------|------|------|--------|
| `placement-done` | 铜 | 知己知彼 | 完成定级测试 | has_placement / placement 事件 |
| `first-cert` | 铜 | 初露锋芒 | 通过首次能力认证 | `deck_certifications` 计数 ≥1 |
| `review-first` | 铜 | 复盘首秀 | 首次完成复习舱判定 | `deck_review_attempts` 计数 ≥1 |
| `arena-first-win` | 铜 | 首胜 | 竞技场首次全题通过 | `deck_arena_attempts` solved 数 ≥1 |
| `feynman-first` | 铜 | 以教为学 | 首次费曼检验合格 | `deck_tutor_messages` mode=feynman 且 grade 合格 |
| `streak-3` | 铜 | 三日不断 | 连续学习 3 天 | `streak_days` ≥3 |
| 🥚 `night-owl` | 铜 | 夜猫子 | 00:00–05:00 间完成一次有效提交 | mastery 事件 `created_at.hour` |
| `cert-adept` | 银 | 游刃有余 | 首个「熟练」级认证 | `deck_certifications.level` |
| `cert-multi-topic` | 银 | 博览 | 认证覆盖 2 个不同主题 | `deck_certifications` distinct topic ≥2 |
| `review-perfect` | 银 | 弹无虚发 | 复习舱单次判定全命中 | `deck_review_attempts.verdict` accuracy=100% |
| `arena-streak-3` | 银 | 连战连捷 | 竞技场三连胜 | `deck_arena_ratings.win_streak` ≥3（含历史峰值，若只存当前值则用当前值≥3 触发） |
| `feynman-star` | 银 | 讲明白了 | 费曼检验拿到最高评级 | feynman grade = 最高档 |
| `streak-7` | 银 | 七日之约 | 连续学习 7 天 | `streak_days` ≥7 |
| 🥚 `perfect-score` | 银 | 满分答卷 | 认证考试得分 100 | `deck_certifications.score`=100 |
| `cert-master` | 金 | 登峰造极 | 首个「精通」级认证 | `deck_certifications.level` |
| `topic-ascend` | 金 | 一域通天 | 单主题全部知识点达「精通」 | 掌握度读模型 `deck_user_mastery.level` |
| 🥚 `comeback` | 金 | 起死回生 | 同一知识点先答错、后在复习舱答对 | `deck_mastery_events` 序列（correct 0→1，source=review_gym） |

实现时注意：`win_streak` 只存当前值时，三连胜判定只能在连胜发生的提交响应里触发——
因此 `collect_facts` 额外接收本次提交的上下文（`pending_context`，如本次 arena 是否达成三连胜、
本次考试分数），规则可声明只读 facts 或同时读 context。保持规则签名统一：
`check(facts, ctx) -> bool`，`ctx` 可为 None（回填时）。

### 奖励上限

全部解锁共 165 智核（7×5 + 7×10 + 3×20），相对认证单次 +20 的存量经济无膨胀风险。

## 4. 判定引擎（`backend/app/deck/badges.py`）

纯函数风格参照 `mastery.py`：

- `collect_facts(db, user_id) -> BadgeFacts`：集中聚合各事实表计数/极值（认证数、最高认证 level、
  distinct topic 数、review 提交数、是否有全命中、arena 胜场/当前连胜、feynman 合格数/最高 grade、
  streak_days、夜间事件数、各主题精通知识点覆盖、comeback 序列判定）。规则不各自查库。
- `evaluate_and_award(db, user_id, ctx=None) -> list[BadgeUnlock]`：
  1. `facts = collect_facts(...)`
  2. 查 `deck_user_badges` 已解锁集合
  3. 逐条跑 `check(facts, ctx)`，新达成的：写 `deck_user_badges` →
     `change_cores(db, user_id, reward, reason=f"解锁徽章 · {title}")` →
     `add_feed(db, user_id, kind="badge", payload=...)` → 收集进返回列表
  4. 返回 `BadgeUnlock`（badge_id/tier/title/reward_cores，供前端播解锁动画）

**接入点**（均在同一事务 commit 前调用，响应体追加 `new_badges` 字段）：

- review-gym submit（`router.py` 复习提交端点）
- arena submit
- tutor feynman 提交
- certification submit（含 placement 分支）

**回填**：提供 `backend/scripts/backfill_badges.py`，对全部用户各跑一次
`evaluate_and_award(db, uid)`（ctx=None，仅依赖历史事实的规则会补发）。幂等，可重复执行。

## 5. API 契约（`frontend/lib/api/deck/types.ts` 为权威）

> 实现修正：本仓库 deck 契约为全链路 **snake_case**（后端返回原始 snake_case 字典，
> `deckCall` 无 key 转换层），徽章字段跟随该约定。

```ts
export type BadgeTier = "bronze" | "silver" | "gold";

export interface BadgeInfo {
  id: string;
  tier: BadgeTier;
  title: string;            // 隐藏未解锁时为 "???"
  condition_desc: string;   // 隐藏未解锁时为 "???"
  hidden: boolean;
  unlocked: boolean;
  reward_cores: number;
  unlocked_at: string | null;
}

export interface BadgeUnlock {   // 提交响应里的新解锁项
  id: string;
  tier: BadgeTier;
  title: string;
  reward_cores: number;
}
```

- `GET /deck/certification/home` 响应 `CertificationHome` 增加 `badges: BadgeInfo[]`
  （全量 17 枚，含未解锁；hidden 未解锁做脱敏）。
- 四个提交端点响应各增加 `new_badges: BadgeUnlock[]`（无新解锁为空数组）。
- 前端封装进 `frontend/lib/api/deck/certification.ts`（或新 `badges.ts`，跟随现有组织方式），
  mock 判定逻辑导出纯函数并配 Jest 测试（项目硬规则）。

## 6. 前端 UI

### 6.1 徽章墙（认证页 HomeView 扩展，`components/certification/CertificationClient.tsx`）

- 「已认证 / Certified」凭证卡区块保留原样；其下新增「徽章墙 / Badges」区块。
- 按 tier 分组陈列（铜 / 银 / 金三行或三栏），每枚为 `BadgeIcon` + 名称 + 条件小字；
  未解锁：60% 透明度 + 虚线边框（`border-dashed border-line`）；隐藏未解锁：`???` 名称与描述。
- 统计行：`已解锁 N / 17`。
- 页面仍薄：`app/certification/page.tsx` 不动，改动集中在 Client 组件。

### 6.2 徽章图标（`components/deck/BadgeIcon.tsx`，跨模块共享故下沉 deck）

- 扁平 SVG：六边形轮廓 + 中心图形（lucide-react 图标，`strokeWidth=1.5`）。
- tier 配色映射设计令牌：铜 → `amber`，银 → `line-bright`，金 → `signal`。
- 禁渐变/模糊/玻璃；尺寸 props 化。

### 6.3 解锁仪式（`components/deck/BadgeUnlockCelebration.tsx` + `useBadgeCelebration` hook）

参照 PlayStation 奖杯（tier 仪式感）、Apple Watch 奖章（全屏聚焦入场）、Duolingo 结算
（奖励数字滚动），在 Deck 设计系统红线内实现：

1. 提交响应含非空 `new_badges` 时，在结果视图上方弹全屏遮罩（`bg-topbar/90`，**无** backdrop-blur）。
2. 徽章 SVG stroke 描绘入场（`stroke-dashoffset` 动画 ~600ms）→ tier 色边框脉冲一次 +
   `scale 1→1.06→1`。
3. `BADGE UNLOCKED` 文字用现有 boot 打字机效果逐行亮起；徽章名 + 条件跟随。
4. `+N 智核` 用现有 CountUp 数字滚动。
5. 克制粒子：8–12 个 tier 色 2px 方块自徽章边缘散开淡出（终端像素风，非彩色 confetti）。
6. 隐藏徽章：先显示 `???` 轮廓，~400ms 后"解码"翻出真名。
7. 单枚总时长 ~2.2s；点击跳过；多枚队列依次播放。
8. `prefers-reduced-motion`：直接呈现静态卡片，零动画。

四个模块的 Client（certification / review-gym / arena / tutor）各自消费响应里的 `new_badges`，
通过共享 hook 驱动同一个 Celebration 组件。

### 6.4 持久反馈

- `add_feed` kind=`badge`：dashboard / profile 动态流展示解锁事件。
- 徽章墙新解锁项首次进入视图时边框亮一次（一次性 pulse）。

### 6.5 顺手清理

`frontend/types/api.ts:219-277` 旧成就系统类型（`AchievementBase` 等）为死代码，删除；
删除前全仓 grep 确认无引用。

## 7. 测试方案

- **后端**（pytest，`backend/tests/`）：
  - 规则单测：构造 `BadgeFacts` 直接测每条 `check`（纯函数，不碰 DB）。
  - 引擎集成测试：内存库跑 `evaluate_and_award`，验证幂等（二次调用不重复发奖/发智核）、
    智核账本流水、feed 事件写入。
  - 端点测试：cert submit 通过后响应含 `new_badges`。
- **前端**（Jest）：mock 徽章判定纯函数测试（参照 `__tests__/review-gym-verdict.test.ts`）。
- **验证门禁**（AGENTS.md Rule 8/10/11）：
  - `npx tsc --noEmit` 零错误；后端服务启动无错误；
  - `next dev` 实跑并请求 `/certification`（看 `Compiled` + `GET 200`）；
  - 组件审计：令牌配色、lucide 图标、无渐变模糊、功能完整、响应式。

## 8. 边界（YAGNI）

- 不做徽章排行榜 / 分享 / 个人主页展示自定义。
- 不做 3D 徽章资源；不引入新依赖（粒子用 CSS 动画手写）。
- 徽章定义不入库、不做管理后台；改徽章 = 改代码发版。
- arena 不写 mastery 事件的现状不改；徽章直接读 arena 自己的表。

# 训练舱 · 目标接口设计（全新后端蓝图）

> 日期：2026-07-26
> 状态：目标设计，待实现（前端已用 mock 按此契约渲染）
> **权威 schema**：`frontend/lib/api/deck/types.ts` —— 本文所有响应结构与之逐字段对应，冲突时以 types.ts 为准
> 上游：`docs/2026-07-26-产品评估与重塑方案.md`、`docs/superpowers/specs/2026-07-26-deck-rebuild-design.md`

## 0. 与旧系统的关系

旧 API 全部废弃（见 `00-current-state.md`）。本设计从零开始：

- **无课程、无章节、无 XP/段位多货币**。成长体系 = 三根能力轴（审阅/调试/实现）+ 智核单货币。
- **存量数据全部清零**（含账号），无迁移负担，见 `02-migration.md`。
- 四个训练模块：代码审查室 / 调试竞技场 / 苏格拉底导师（含费曼检验）/ 基本功认证。

## 1. 端点总览

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| POST | /api/auth/register | 注册（email + password + username） | 公开 |
| POST | /api/auth/login | 登录，返回 JWT | 公开 |
| GET | /api/dashboard | 训练舱首页聚合 | ✓ |
| GET | /api/review-gym/session | 取一关审查会话（不含注入缺陷答案） | ✓ |
| POST | /api/review-gym/submit | 提交标注，返回判定（未全中可复盘重做，见 §3） | ✓ |
| GET | /api/review/queue | 复盘队列（错题/失败项聚合） | ✓ |
| GET | /api/arena/home | 竞技场首页（状态+今日挑战+排行） | ✓ |
| POST | /api/arena/run | 提交代码判题 | ✓ |
| GET | /api/tutor/state | 导师状态（余额+欢迎消息+建议主题） | ✓ |
| POST | /api/tutor/message | 发送消息，返回追问（扣智核） | ✓ |
| POST | /api/tutor/feynman | 开启费曼检验 | ✓ |
| POST | /api/tutor/feynman/check | 提交解释，返回点评（扣智核） | ✓ |
| GET | /api/certification/home | 徽章墙 + 可考列表 | ✓ |
| GET | /api/certification/exam | 取试卷（`id=placement` 为定级测试） | ✓ |
| POST | /api/certification/submit | 交卷判分 | ✓ |
| GET | /api/ability-map | 三轴 + 全量知识点掌握度 | ✓ |
| GET | /api/profile | 档案聚合 | ✓ |

## 2. 训练舱聚合

### GET /api/dashboard

首页一屏全部数据，对应 `DeckDashboard`：

```json
{
  "user": { "name": "清源", "cores": 86 },
  "main_task": {
    "id": "REVIEW-0247", "module": "review-gym", "module_label": "代码审查室",
    "stage_label": "第 12 关",
    "title": "这段快速排序里有 2 处缺陷……", "highlight": "2 处缺陷",
    "desc": "……", "difficulty": 3, "eta_minutes": 8,
    "related_weakness": "边界条件处理",
    "reason": "你的「审阅」轴是三轴最低（LV.2），这一关专攻「边界条件处理」。",
    "target_url": "/review-gym?session=REVIEW-0247",
    "cta_label": "开始审查 →",
    "alternates": [ { "...": "结构同主任务（alternates 为空数组）" } ]
  },
  "ability_map": {
    "has_placement": true,
    "axes": [
      { "key": "review", "label": "审阅", "level": 4, "xp_current": 1240, "xp_next": 1600, "weakest_focus": "并发代码审阅" }
    ]
  },
  "modules": [
    { "key": "review-gym", "stats": [ { "label": "今日完成", "value": "3" }, { "label": "连续 5 天", "trend": "up" } ] }
  ],
  "weak_points": [ { "name": "边界条件处理", "category": "数据结构 · 排序", "p_l": 0.42, "source": "3天前 · 审查漏报" } ],
  "rhythm": { "streak_days": 7, "days": [ { "label": "一", "minutes": 25, "is_today": false } ] },
  "review_due": { "total": 5, "due_today": 2 },
  "feed": [ { "time": "09:41", "segments": [ { "t": "审查 ", "tone": "plain" }, { "t": "REVIEW-0246", "tone": "strong" } ] } ]
}
```

- `main_task` 为 `null` 表示用户未定级，前端显示定级引导。
- `axes` 固定三根、固定顺序 review → debug → implement。
- `feed[].segments[].tone` ∈ `plain | strong | ok | bad`。
- 个性化字段（§3.5 P-01/P-04）：`main_task.reason` 说明「为什么推荐这个给你」（引用
  能力轴等级 + 弱点知识点，仅主任务与备用任务卡片带）；`weak_points[].source` 标注
  弱点来源（取 `deck_mastery_events` 最近一条事件，如「3天前 · 审查漏报」）。

### 主任务分发规则（service 层实现）

1. 用户未完成定级测试（`has_placement=false`）→ `main_task = null`。
2. 实现轴等级 < LV.3 → 从「基本功认证 / 苏格拉底导师」分发（审查/调试模块不锁，但不作为主任务）。
3. 否则 → 取三轴中等级最低者，分发其对应模块（review→审查室、debug→竞技场、implement→导师/认证轮换）。
4. **界面不出现任何「新手/老手」标签**；分发只决定任务内容。
5. `alternates` 给 2 个其他模块的候选任务（「换一个任务」用）。

## 3. 代码审查室

### GET /api/review-gym/session?id=REVIEW-0247

返回 `ReviewSession`（**绝不能包含 injected_defects**，答案只在服务端）：

```json
{ "id": "REVIEW-0247", "title": "快速排序实现", "language": "python",
  "code": "def quicksort(arr):...", "defect_count": 2,
  "difficulty": 3, "eta_minutes": 8, "related_weakness": "边界条件处理" }
```

`id` 省略时返回该用户进度上下一关：优先选 `related_weakness` 匹配用户 p_l 最低
知识点的未完成关卡（§3.5 P-05），无匹配时回退顺序取第一个未完成关卡。

### POST /api/review-gym/submit

请求：`{ "session_id": "REVIEW-0247", "marks": [ { "line": 6, "type": "boundary" } ] }`
`type` ∈ `logic | boundary | performance | style | security`。

判定规则（服务端确定性校验，参考实现 `frontend/lib/api/deck/mock/review-gym.ts` 的 `judgeMarks`）：

- 标注行与某注入缺陷行相差 ≤1 且类型一致 → 命中（一个标注只能命中一个缺陷）。
- 未被命中的注入缺陷 → 漏报；其余标注 → 误报。
- `score = round(命中/总缺陷 × 70 + (1 − 误报/标注数) × 30)`；零标注时无误报底分 30。

响应 `ReviewVerdict`：`{ hits, missed, false_alarms, score, accuracy }`，其中 hits/missed 元素含 `{ line, type, explanation }`。

**副作用**：按命中数更新 `review` 轴经验；每个命中/漏报的注入缺陷为其关联知识点写一条
`deck_mastery_events` 事件（`source=review_gym`，命中 `correct=true`、漏报 `correct=false`），
并重算该知识点缓存的 `p_l`/`level`（HLR 回忆概率，模型见 §8）；写 `feed_events`。
**重做语义（2026-07-26 起，替代原纯幂等）**：已全中的关重复提交返回旧判定不再结算；
未全中的关允许重做（复盘入口），重新判定后覆盖 attempt，经验与掌握度事件只按「新增命中数」
结算，全中 +5 智核奖励每关至多发放一次（attempt 全中后幂等锁死）。

### GET /api/review/queue（复盘 · 错题复习）

错题/失败项聚合队列，与导师对话是相互独立的功能。响应 `ReviewQueue`：

```json
{ "items": [ { "id": "rg-REVIEW-0248", "kind": "review-gym", "title": "重审 REVIEW-0248 · 链表反转",
    "detail": "漏报 2 处", "target_url": "/review-gym?session=REVIEW-0248",
    "cta_label": "重新审查 →", "last_at": "昨天" } ], "total": 1 }
```

`kind` ∈ `review-gym`（判定有漏报/误报的关，重做全中后出队）| `arena`（尝试过但从未
攻克的挑战）| `knowledge`（`p_l < 0.6` 的弱知识点，入口为费曼检验 `/tutor?topic=`）。
`GET /api/dashboard` 的 `review_due.total` 与本队列同源。

## 4. 调试竞技场

### GET /api/arena/home

`ArenaHome`：`{ profile: { tier, rating, week_rank, rank_delta, win_streak }, challenge, leaderboard }`。

- `challenge`：`{ id, title, language, code, failing_output, time_limit_sec, difficulty }`。
- `leaderboard`：TOP 10 + 当前用户行（`is_self: true`），按 rating 降序。
- 段位只服务竞技场，规则见 `03-economy.md`。

### POST /api/arena/run

请求：`{ "challenge_id": "DEBUG-0091", "code": "..." }`。
响应 `ArenaRunResult`：`{ passed, total, output, solved, score_delta }`。

- 判题走 Judge0（或降级本地 runner），限时 `time_limit_sec` 内有效；超时提交 `solved=false`。
- `solved=true` 时 `score_delta > 0`（按用时与难度折算），更新 rating/排行榜/`debug` 轴；写 `feed_events`。

## 5. 苏格拉底导师

### GET /api/tutor/state

`TutorState`：`{ cores_balance, today_used, cost_per_question, messages, suggested_topics }`。
`suggested_topics` 取该用户最弱的 3 个知识点（与 dashboard.weak_points 同源）。

### POST /api/tutor/message

请求：`{ "text": "...", "mode": "socratic" }`。
响应 `TutorReply`：`{ message: { id, role, text, mode }, cores_balance }`。

- **追问式系统提示词**：禁止直接给答案/写代码，只能提问引导。每次调用扣 `cost_per_question`（默认 2）智核；**余额不足返回 200 + 提示消息**（`TutorReply` 结构，不扣费——前端契约要求响应恒为 `TutorReply`，见 README 全局约定的例外条款）。
- 对话持久化到 `tutor_messages`，`GET /api/tutor/state` 的 `messages` 返回最近会话。

### POST /api/tutor/feynman 与 /api/tutor/feynman/check

- `feynman`：请求 `{ "topic": "递归出口设计" }`，服务端创建费曼会话时即绑定知识点（kp 绑定发生在服务端，不做前端子串匹配），返回开场追问（`mode: "feynman"`）与 `feynman_session_id`。
- `feynman/check`：请求 `{ "session_id": "<feynman_session_id>", "text": "<用户的解释>" }`（kp 从会话解析）。LLM 按评分量规（rubric）评估：每个知识点在种子数据中带 3–5 个 `key_points`（label + 同义词，见 §8），按覆盖率定 `grade` ∈ `优秀 | 良好 | 待加强`（优秀 = 覆盖 ≥80% 且具备因果/示例结构；良好 = 覆盖 ≥50%，或 ≥1/3 且有结构；否则待加强），点评反馈中点名遗漏的关键点。响应在 `TutorReply` 基础上加 `grade` 与 `mastery_update: { kp_name, p_l_before, p_l_after, level }`。**副作用**：写一条 `deck_mastery_events` 事件（`source=feynman`，`grade` 原样记录，优秀/良好记 `correct=true`、待加强记 `correct=false`），重算缓存 `p_l` 与 `level`；扣智核。

## 6. 基本功认证

### GET /api/certification/home

`CertificationHome`：`{ has_placement, certified: CertRecord[], available_exams, next_available_days }`。

- `CertRecord`：`{ topic, level, date, score, verify_code }`。
- `next_available_days`：冷却期（同一用户两次认证间隔，默认 3 天）；`null` 表示随时可考。

### GET /api/certification/exam?id=cert-pointer（或 id=placement）

`CertExam`：`{ info: { id, topic, question_count, time_limit_min, pass_score }, questions }`。
`questions[]`：`{ id, kind: "mcq" | "code", prompt, options?, starter_code? }` —— **不含答案**。

### POST /api/certification/submit

请求：`{ "exam_id": "cert-pointer", "answers": [ { "question_id": "q1", "answer": "10" } ] }`。
响应 `CertResult`：`{ score, passed, certificate, per_question }`。

- mcq 比对答案表；code 题过 Judge0 运行测试用例判分（mock 期前端为关键字匹配，后端必须换真判分）。
- `passed = score ≥ pass_score`；通过发 `CertRecord`（`verify_code` 唯一、可公开查验），更新 `implement` 轴，发智核奖励（见 03）。
- 定级测试（`exam_id=placement`）：永不返回 `passed=true`，但按答案分布写入三轴初始等级（`has_placement` 置 true）。等级映射：`LV = 1 + floor(score / 25)`，上限 LV.5。掌握度侧不再写统一初始 `p_l`，而是按每题作答为涉及知识点写 `deck_mastery_events` 事件（`source=placement`），初始 `p_l`/`level` 由事件流重算得出。

## 7. 能力图谱与档案

### GET /api/ability-map

`AbilityMapDetail`：`{ axes, has_placement, placement, knowledge_points }`。
`knowledge_points[]`：`{ name, category, axis, p_l, level, trend }`，`level` ∈ `初识 | 熟悉 | 熟练 | 精通`（判定规则见 §8 掌握度模型）；`trend` 由事件流分别重算 7 天前与当前的 `p_l`，差值 ±0.02 以内为 flat（此前为硬编码 "flat"，现为真实计算）。

`placement`（§3.5 P-10 能力演化对比的「定级时」基线，未定级为 `null`）：
`{ score, date, levels: { review, debug, implement }, fingerprint }`。
数据源为定级 feed 事件（新格式 `payload.placement.score` 结构化字段，旧格式从
segments 文案解析分数），初始三轴等级按 §8 规则复算（review/implement = `1+min(4,score//25)`，
debug 恒低一档最低 LV.1）。

### GET /api/profile

`ProfileData`：`{ user: { name, joined_days }, cores: { balance, transactions }, arena, certifications, leaderboard, recent, timeline }`。
`transactions` 按时间倒序取最近 50 条。

`timeline`（§3.5 P-09 训练档案路径时间线，按时间升序）：
由既有事实表重放构建（不新增表）——定级 feed 事件（`placement`：`{ score, date, levels, fingerprint }`）、
模块事实表经验增量重放（`axis_upgrade`：`{ axis, label, from_level, to_level }`，review=20×命中、
debug=23/攻克、implement=40/认证通过，跨 400 边界即升级）、掌握度事件流重放
（`mastery`：`{ kp_name, level }`，首次达到熟练/精通）、认证记录（`cert`：`{ topic, level, score }`）。
未定级用户为 `[]`。

## 8. 数据模型（全新表）

> **实现偏差（已落地）**：所有新表统一加 `deck_` 前缀（如 `deck_knowledge_points`、
> `deck_user_mastery`、`deck_arena_ratings`），避免与 legacy 表（`users` 除外，直接复用）冲突。
> 权威定义见 `backend/app/deck/models.py`。

| 表 | 关键字段 | 说明 |
|---|---|---|
| users | id, email, username, password_hash, cores, is_admin, created_at | 全新账号体系 |
| deck_ability_axes | user_id, axis(review/debug/implement), xp | 三轴经验；等级由 xp 推导 |
| deck_knowledge_points | id, name, category, axis, key_points(json) | 种子内置（13 个）；key_points 为 3–5 个关键点（label + 同义词），费曼评分量规的数据基础 |
| deck_mastery_events | id, user_id, kp_id, created_at, source, correct, grade, hints_used, latency_ms | 掌握度事件流，唯一事实源；source ∈ review_gym/arena/feynman/certification/placement；hints_used 仅记录、暂不进公式 |
| deck_user_mastery | user_id, kp_id, p_l, level, updated_at | 缓存读模型：p_l = HLR 当前回忆概率、level = 掌握等级，由事件流重算；三轴与弱点的数据源 |
| deck_review_sessions | id, title, language, code, difficulty, eta_minutes | 种子内容 |
| deck_injected_defects | session_id, line, type, explanation | 服务端秘密，不下发 |
| deck_review_attempts | id, user_id, session_id, marks, verdict, created_at | 幂等键 (user_id, session_id) |
| deck_arena_challenges | id, title, language, code, failing_output, time_limit_sec, difficulty | 种子内容（每日轮换） |
| deck_arena_attempts | id, user_id, challenge_id, solved, passed, total, created_at | 判题记录（实现偏差：不存代码原文） |
| deck_arena_ratings | user_id, rating, win_streak, updated_at | 段位由 rating 推导 |
| deck_tutor_messages | id, user_id, role, mode, text, grade, created_at | 导师对话 |
| deck_core_transactions | id, user_id, delta, reason, balance_after, created_at | 智核一本账 |
| deck_cert_exams / deck_cert_questions | exam: id, topic, pass_score, time_limit_min；question 含答案（不下发） | 种子内容 |
| deck_certifications | id, user_id, topic, level, score, verify_code(unique), created_at | 能力凭证 |
| deck_daily_activity | user_id, day, minutes, exercises, correct | 节奏柱图与今日统计 |
| deck_feed_events | id, user_id, kind, payload(json), created_at | 动态流 |

### 能力轴计算

- **经验制（已实现）**：`axis_level = 1 + xp // 400`，`xp_next = level × 400`；训练行为按模块归属给对应轴加 xp（审查命中 +20/处、调试修复 +23/场、认证通过 +40/场）。
- 定级测试按分数写初始 xp：base = 1 + min(4, score // 25)，debug 轴低一档（最低 LV.1），`xp = (level-1) × 400 + 200`。
- `weakest_focus` = 该轴 `p_l` 最低的知识点名称。

### 掌握度模型（事件源 HLR + 等级状态机）

- **事件为唯一事实源**：审查、竞技场、费曼、认证、定级各模块只写 `deck_mastery_events`；`deck_user_mastery.p_l`/`level` 是由事件流重算的缓存读模型，可随时重建。
- **回忆概率（HLR）**：`p = 2^(−Δ/h)`，半衰期 `h` 单位为天、初始 1.0；correct 事件后 `h = min(h×1.8, 180)`，错误事件后 `h = max(h×0.5, 0.2)`；`Δ` = 距最近一次 correct 事件的天数（尚无 correct 时 = 距首事件天数 + 1）。
- **掌握等级**（每 kp）：`初识`（无事件或 p<0.3）/ `熟悉`（p≥0.3）/ `熟练`（p≥0.6 且累计 ≥3 次 correct）/ `精通`（p≥0.8 且 ≥4 次 correct，且存在一对间隔 ≥3 天的 correct 事件，且 ≥1 次 correct 来自实战源 review_gym/arena/certification）。**仅费曼信号永远无法达到精通**——「能讲出来」只是佐证信号，需实战正确作答 corroborate。
- **trend**：用同一公式分别重算 7 天前时点与当前的 `p_l`，差值 ±0.02 以内为 flat。
- `hints_used` 已入表但暂不进入公式，预留给「提示依赖」负向信号。

### 掌握度模型设计依据

旧设计名义上叫 BKT，实为固定步长加减，既无遗忘建模也无意拟合数据。2026-07-26 的文献与市场调研表明：小数据规模下经典 BKT 被带特征的 logistic 模型压制（Gervet et al., JEDM 2020）；Duolingo 生产环境用半衰期回归（HLR）建模遗忘（Settles & Meeder, ACL 2016）；Khan Academy 用透明的掌握等级状态机对外沟通进度；Anki 生态的 FSRS 同样以记忆半衰期为核心。因此新模型取「事件源 HLR 回忆概率 + 掌握等级状态机」：HLR 参数少、可由事件流确定性重算，等级状态机对用户可解释、对前端可渲染。费曼检验不作为精通的充分条件——LLM 评判本身存在可靠性偏差（Zheng et al.），「能讲解」仅作佐证信号；`hints_used` 预留为负向信号，因为无护栏的 AI 帮助会显著损害独立作答表现（Bastani et al., PNAS 2025：未辅助考试 −17%）。

来源：

- Gervet et al., *Knowledge Tracing Machines...*, JEDM 2020 — https://jedm.educationaldatamining.org/index.php/JEDM/article/view/451
- Settles & Meeder, Duolingo Half-Life Regression, ACL 2016 — https://research.duolingo.com/papers/settles.acl16.pdf
- Khan Academy, Course Mastery levels — https://support.khanacademy.org/hc/en-us/articles/5548760867853
- Bastani et al., *Generative AI can harm learning*, PNAS 2025 — https://doi.org/10.1073/pnas.2422633122
- Zheng et al., *Judging LLM-as-a-Judge*, 2023 — https://arxiv.org/abs/2306.05685

## 9. 非目标

- 不做旧系统的任何兼容层；不做课程/章节/题解/笔记/收藏。
- 管理后台本期不重建，种子数据用脚本直接入库。

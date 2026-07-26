# 00 · 当前 API 与数据模型现状快照

> **⚠️ 已废弃 · 仅历史参照**
> 本文描述的旧 API 已随「训练舱」重塑全部废弃：前端旧封装已物理删除，后端将按
> `01-target-design.md` 全新实现，存量数据全部清零（`02-migration.md`）。
> 保留本文只为理解历史决策，不要据此写任何新代码。

> 日期：2026-07-26
> 来源：逐个核对 `backend/app/routers/`、`backend/app/models/`、`backend/app/core/routes.py` 与 `frontend/lib/api/` 得出，以代码为准。
> 状态标注：**保留** / **改造**（端点保留但语义或实现要改）/ **合并**（并入其他端点）/ **废弃**（目标设计中删除）。

## 路由注册总览

`backend/app/core/routes.py` 按域分组注册（均无前缀嵌套，各 router 自带 prefix）：

- CORE：`auth`、`users`、`admin`、`stats`、`code`、`courses`
- AI：`ai.py` 内 6 个 router（choice / review / config / chat / analysis / hint）
- LEARNING：`challenges`、`achievements`、`exercises`、`chapters`、`review`（间隔重复）、`favorites`、`notes`、`note_tags`、`learning_path`
- ECONOMY：`tier`、`core`（智核）、`xp`
- COMMUNITY：`solutions`
- WebSocket：`/ws/exercises?token=`；健康检查：`GET /`、`GET /health`

---

## 1. auth.py — `prefix=/api/auth`，tags `auth`

| 状态 | 方法 | 路径 | 用途 |
|---|---|---|---|
| 保留 | POST | `/api/auth/register` | 注册，返回 `Token`（201） |
| 保留 | POST | `/api/auth/login` | 登录（body 含 `remember_me`），返回 `Token` |
| 保留 | POST | `/api/auth/forgot-password` | 请求重置密码，恒 200 防枚举 |
| 保留 | GET | `/api/auth/me` | 当前用户信息 |

## 2. users.py — `prefix=/api/users`，tags `users`（全部需认证）

| 状态 | 方法 | 路径 | 用途 |
|---|---|---|---|
| 保留 | GET/PUT | `/api/users/me/profile` | 读/改我的资料 |
| 合并 | GET/PUT | `/api/users/profile` | 上一条的**别名路由**，前端 `profile.ts` 实际用的是它；重写时只留一组 |
| 保留 | GET | `/api/users/me/activities` | 我的最近活动（`limit` 1-100） |
| 保留 | POST | `/api/users/checkin` | 签到（按北京时间判重） |
| 保留 | GET | `/api/users/checkin/status` | 今日签到状态 |
| 保留 | GET | `/api/users/checkin/details` | 按月/日查签到明细（含农历） |
| 保留 | GET | `/api/users/checkin/stats` | 签到统计 |
| 废弃 | POST | `/api/users/me/xp` + 别名 `/api/users/xp` | 手动加 XP 的测试后门（query `xp_amount` 1-10000）；返回 `mastery_xp/mastery_level`，与前端声明类型不一致 |
| 保留 | GET | `/api/users/{user_id}` | 查任意用户公开信息 |

## 3. admin.py — `prefix=/api/admin`，tags `admin`（全部需管理员）

| 状态 | 方法 | 路径 | 用途 |
|---|---|---|---|
| 保留 | GET | `/api/admin/users` | 用户列表（**内存分页**，重写时改 SQL 分页） |
| 保留 | DELETE | `/api/admin/users/{user_id}` | 删除用户 |
| 保留 | GET | `/api/admin/users/online` | 在线用户（基于 `login_sessions`） |
| 保留 | GET/PUT | `/api/admin/users/{user_id}/quota` | 查/设用户配额 |
| 保留 | POST | `/api/admin/users/{user_id}/quota/reset` | 重置配额（默认 100） |

## 4. stats.py — `prefix=/api/stats`，tags `stats`

| 状态 | 方法 | 路径 | 用途 |
|---|---|---|---|
| 废弃 | GET/PUT | `/api/stats/progress[/{chapter_id}]` | 旧章节进度体系（`chapter_progress` 表，JSON 存子节状态），产品方案要求迁移到 BKT 后删表 |
| 保留 | POST | `/api/stats/sessions/start` / `end` | 学习时长会话开始/结束（`end` 支持 keepalive） |
| 保留 | GET | `/api/stats/sessions/active` | 当前活跃会话 |
| 保留 | POST | `/api/stats/sessions/subsection` | 更新会话内小节位置 |
| 保留 | GET | `/api/stats/sessions` | 会话历史 |
| 合并 | GET | `/api/stats/statistics` | 学习统计聚合（并入仪表盘聚合端点） |
| 合并 | GET | `/api/stats/activities` | 活动流（并入统一成长时间线） |
| 保留 | GET | `/api/stats/exercises/answers/{chapter_id}` | 章节选择题答案（前端判分用） |
| 合并 | GET | `/api/stats/user/me` | 我的统计（并入仪表盘） |
| 保留 | GET | `/api/stats/courses/{course_id}` | 课程统计（公开） |
| 废弃 | GET | `/api/stats/leaderboard` | 按 `users.xp` 的排行榜（公开）；产品方案只保留调试竞技场一个榜 |
| 合并 | GET | `/api/stats/activity/me` | 我最近活动（并入成长时间线） |
| 合并 | GET | `/api/stats/trends/exercises|accuracy|time` | 三个趋势端点（并入仪表盘） |
| 合并 | GET | `/api/stats/today` | 今日练习统计（并入仪表盘） |

## 5. code.py — `prefix=/api/code`，tags `code`（全部需认证）

| 状态 | 方法 | 路径 | 用途 |
|---|---|---|---|
| 保留 | POST | `/api/code/execute` | Judge0 单代码执行 |
| 保留 | POST | `/api/code/execute-batch` | 批量执行（≤50 用例） |
| 保留 | GET | `/api/code/languages` | 支持语言列表（Py/JS/TS/C/C++） |

> 新模块（代码审查室、调试竞技场、基本功认证）的判题复用此基础设施。

## 6. courses.py — `prefix=/api/courses`，tags `courses`

| 状态 | 方法 | 路径 | 用途 |
|---|---|---|---|
| 保留 | GET | `/api/courses` | 课程列表（公开） |
| 保留 | GET | `/api/courses/{course_id}` / `/code/{code}` | 课程详情（公开/可选认证） |
| 合并 | GET | `/api/courses/chapters/{chapter_id}` 和 `/{course_id}/chapters/{chapter_id}` | 章节详情，两条重复路径且前端都不用（前端走 `/api/chapters/{id}`）；重写只留一条 |
| 保留 | POST | `/api/courses/{course_id}/enroll` | 选课 |
| 保留 | GET | `/api/courses/users/me/course-progress` | 我的课程进度 |
| 保留 | POST | `/api/courses/init` | 初始化课程（管理员） |
| 保留 | GET | `/api/courses/chapters/{chapter_id}/sections` | 小节列表（含 BKT 掌握度） |
| 保留 | GET | `/api/courses/sections/{section_id}` | 小节详情（含知识点） |
| 保留 | POST | `/api/courses/sections/{section_id}/progress` | 保存小节进度（`section_progress` 新体系） |
| 保留 | GET | `/api/courses/{course_id}/current-position` | 当前学习位置 |
| 废弃 | GET | `/api/courses/{course_id}/hybrid-recommendations` 等 6 个 | 混合推荐 / user-profile / recalculate / extract-tags / generate-embedding / batch-update-embeddings / recommendation-debug——旧推荐系统，目标设计中被「今日主任务自适应分发」取代 |

## 7. chapters.py — `prefix=/api/chapters`，tags `chapters`

| 状态 | 方法 | 路径 | 用途 |
|---|---|---|---|
| 合并 | GET | `/api/chapters/{chapter_id}` | 章节详情（内嵌习题），与 courses.py 的两条路径三处重复，重写合并为一处 |

## 8. exercises.py — `prefix=/api/exercises`，tags `exercises`

| 状态 | 方法 | 路径 | 用途 |
|---|---|---|---|
| 保留 | GET | `/api/exercises/chapter/{chapter_id}` | 章节已验证习题（公开，`difficulty/limit` 过滤；`subsection` 参数未实现） |
| 保留 | GET | `/api/exercises/detail/{exercise_id}` | 单题详情（公开） |
| 合并 | GET | `/api/exercises/{chapter_id}` | 旧版兼容路由，同上，合并 |
| 改造 | POST | `/api/exercises/generate` | AI 生成习题（管理员）；产品方案：转为「按需生成针对弱点的变式题，必须过 Judge0 验证才能入库」 |
| 改造 | POST | `/api/exercises/{exercise_id}/verify` | 审核习题（管理员）；改为「Judge0 自动验证 + 抽样人工评审」流程的一环 |
| 保留 | POST | `/api/exercises/{exercise_id}/submit` | 提交答案并反馈 |
| 改造 | POST | `/api/exercises/recommend` | 个性化推荐（KT+ZPD）；并入主任务分发逻辑 |

## 9. ai.py — 6 个 router

**choice_router / review_router / analysis_router / chat_router — `prefix=/api/ai`（需认证）**

| 状态 | 方法 | 路径 | 用途 |
|---|---|---|---|
| 改造 | POST | `/api/ai/choice-explanation` | 选择题讲解 → 改造为苏格拉底式追问 |
| 改造 | POST | `/api/ai/code-review` | AI 审查学生代码 → 苏格拉底导师能力之一 |
| 改造 | POST | `/api/ai/choice-analysis` | 选择题错因分析 → 同上 |
| 改造 | POST | `/api/ai/chat` + `/chat/stream`（SSE） | 通用 AI 对话 → 统一进苏格拉底导师端点 |

**hint_router — `prefix=/api/ai`（需认证）**

| 状态 | 方法 | 路径 | 用途 |
|---|---|---|---|
| 保留 | GET | `/api/ai/exercise-hint/cache/{exercise_id}/{hint_level}` | 已购提示缓存查询（前端未封装此函数） |
| 保留 | POST | `/api/ai/exercise-hint/stream` | 流式提示，扣智核（独立短事务、失败退款、结果缓存、命中回放）；苏格拉底化后保留扣费与缓存机制 |

**config_router — `prefix=/api/admin/ai`（管理员）**：GET/PUT `/config`、GET `/status`、POST `/test-connection` —— 全部**保留**。

## 10. challenges.py — `prefix=/api/challenges`，tags `challenges`

**任务挑战系统**（非演武场）。与 `stats_service`、成就、`user_challenges` 表耦合。

| 状态 | 方法 | 路径 | 用途 |
|---|---|---|---|
| 废弃 | GET | `/api/challenges` / `/{id}` | 挑战定义列表/详情（公开） |
| 废弃 | GET | `/api/challenges/user/me` | 我的挑战进度 |
| 废弃 | POST | `/api/challenges/{id}/start` / `/progress` | 开始/推进挑战 |

> 产品方案：`/api/challenges`（任务挑战）与演武场 challenge **二选一，建议删任务挑战**。删除前需先解除 `stats_service`（挑战完成统计）与成就系统的耦合，详见 02 文档。

## 11. achievements.py — `prefix=/api/achievements`，tags `achievements`

| 状态 | 方法 | 路径 | 用途 |
|---|---|---|---|
| 合并 | GET | `/api/achievements` / `/me` / `/earned` / `/{id}` | 成就系统保留但收敛：成就奖励统一进单 XP 体系，前端零调用的 `getAchievements*` 封装已确认可清理 |
| 废弃 | GET | `/api/achievements/leaderboard` | XP 排行榜（三套榜之一，只留调试竞技场榜） |
| 废弃 | GET | `/api/achievements/rank` | 我的 XP 名次 |

## 12. review.py — `prefix=/api/review`，tags `review`（全部需认证）

间隔重复 + 错题本 + 弱点系统，整体**保留**：

| 状态 | 方法 | 路径 | 用途 |
|---|---|---|---|
| 保留 | GET | `/api/review/queue` | 到期复习队列（SM 调度） |
| 保留 | POST | `/api/review/complete/{exercise_id}` | 完成一次复习 |
| 保留 | GET | `/api/review/weak-points` + POST `/weak-points/target` | 薄弱点列表 / 定向练习 |
| 保留 | GET | `/api/review/stats` | 复习统计 |
| 保留 | GET/POST/DELETE | `/api/review/wrong-questions[...]` | 错题本 CRUD + collect + resolve（7 个端点） |
| 保留 | GET | `/api/review/analysis/weak-points` | 薄弱点分析 |
| 保留 | POST | `/api/review/practice/enhanced` | 强化定向练习（quick/deep） |
| 保留 | GET | `/api/review/reminders` | 艾宾浩斯复习提醒 |

## 13. learning_path.py — `prefix=/api/learning-path`（26 个端点，全部需认证）

**精进之路（mastery）**

| 状态 | 方法 | 路径 | 用途 |
|---|---|---|---|
| 保留 | GET | `/mastery/{course_id}/overview` | 课程掌握度总览 → 能力图谱的数据基础 |
| 保留 | GET | `/mastery/{course_id}/chapter/{chapter_id}` | 章节掌握度详情 |
| 改造 | POST | `/mastery/{course_id}/chapter/{chapter_id}/recommend` | 章节定向推荐（注意：前端用 GET 调，方法不匹配会 405） |
| 保留 | GET | `/mastery/section/{section_id}`、`/mastery/course/{course_id}` | 小节/课程 BKT 掌握度（四层聚合） |
| 废弃 | GET | `/mastery/{course_id}/chapter/{chapter_id}/knowledge` | AI 生成章节讲解——产品方案明确「砍掉 AI 生成讲义页面」 |
| 改造 | POST | `/mastery/{course_id}/generate-quiz` / `submit-quiz` | AI 生成个性化测试；生成内容须过验证 |
| 保留 | GET | `/mastery/section/{id}/knowledge-points` / `/base-questions` | 小节知识点 / 基础测试题（前端未消费前者） |
| 保留 | POST | `/mastery/{cid}/chapter/{chid}/submit-base` | 提交基础测试（10 XP/题） |
| 保留 | POST | `/mastery/{cid}/generate-enhanced` + 两个轮询端点 + `submit-enhanced` + `persist-enhanced-question` | 强化题生成（WS 推送）与提交（15 XP/题） |
| 保留 | POST/GET | `/mastery/progress/*`（5 个） | 单题进度保存、章节进度、完成 quiz、按 key 查进度 |

**挑战之路（arena）——重做为调试竞技场**

| 状态 | 方法 | 路径 | 用途 |
|---|---|---|---|
| 改造 | POST | `/challenge/infinite/start` | 开始挑战（伪 session） |
| 改造 | GET | `/challenge/progress`、`/challenge/exercise/{id}`、`/challenge/recent` | 进度（lite 模式）/按需加载单题/最近挑战 |
| 改造 | POST | `/challenge/submit` | 提交判题（含段位星星结算，判题不可用 503） |
| 改造 | POST | `/challenge/save-code` / `/switch` / `/append` / `/exit` | 草稿/切题/追加/退出（`/exit` 前端未消费） |

**排行榜**

| 状态 | 方法 | 路径 | 用途 |
|---|---|---|---|
| 废弃 | GET | `/leaderboard/{course_id}/mastery` | 精进榜（三套榜之一） |
| 保留 | GET | `/leaderboard/{course_id}/arena` | 竞技榜 → 迁移为调试竞技场排行榜 |

## 14. core.py — `prefix=/api/cores`，tags `cores`（全部需认证）

| 状态 | 方法 | 路径 | 用途 |
|---|---|---|---|
| 保留 | GET | `/api/cores/balance` | 余额/累计获得/累计消耗 |
| 保留 | POST | `/api/cores/spend` | 消耗（合法类别仅 `ai_hint_light/medium/deep`） |
| 废弃 | POST | `/api/cores/earn` | 手动发放后门；发放改为后端内部 service 调用，不暴露 HTTP |
| 保留 | GET | `/api/cores/transactions` | 智核流水 |
| 合并 | GET | `/api/cores/daily-summary` | 今日统计+待领奖励（「待领奖励」无自动发放逻辑，重写时或实现或删除展示） |

## 15. tier.py — `prefix=/api/tier`，tags `tier`

| 状态 | 方法 | 路径 | 用途 |
|---|---|---|---|
| 保留 | GET | `/api/tier/config` | 段位配置（公开） |
| 保留 | GET | `/api/tier/profile` | 全局段位（无则自动创建青铜 IV 0 星） |
| 合并 | GET | `/api/tier/profile/{course_id}` | 「按课程」查段位，实际仍读全局 profile，course_id 只校验存在——假参数，重写删除 |
| 改造 | POST | `/api/tier/profile/{course_id}/stars` | 手动改星（±10）；星数变更改为调试竞技场结算内部触发，不暴露给客户端直调 |
| 保留 | GET | `/api/tier/transactions` | 段位流水 |

> 段位实现已是**星数制**（7 大段，`app/core/tier_config.py`）；但 `user_arena.py` 里的分数阈值制常量 `TIER_THRESHOLDS = {bronze:0, silver:1000, ...}` **并非死代码**——`services/leaderboard_service.py:38 get_tier_for_score()` 仍在用它把 `total_score` 映射为 5 段 tier 供竞技榜展示，这就是「两套算法写同一概念」的活证据。前端 `learning-path.ts` 另有一份不一致的 `TIER_THRESHOLDS/TIER_NAMES`。产品方案要求只留星数制。

## 16. xp.py — `prefix=/api/xp`，tags `xp`（全部需认证）

| 状态 | 方法 | 路径 | 用途 |
|---|---|---|---|
| 合并 | GET | `/api/xp/balance` | mastery_xp 余额与等级 → XP 合一后并入成长端点 |
| 废弃 | POST | `/api/xp/earn` | 手动发放 mastery XP 后门（1-100） |
| 合并 | GET | `/api/xp/transactions` | mastery XP 流水 → 并入统一成长时间线 |

## 17. favorites.py / notes.py / note_tags.py / solutions.py

整体**保留**（收藏夹 9 端点、笔记 10 端点含导出、标签 4 端点、题解广场 8 端点）。备注：

- `solutions.py` tags 为中文 `题解广场`，重写时统一英文 tag。
- `notes.py` 中 `GET /export/{note_id}` 声明在 `/{note_id}` 之后，依赖 FastAPI 声明顺序匹配才可用——重写时调整路由顺序。
- `achievements/leaderboard`、`stats/leaderboard`、`learning-path/leaderboard/*/mastery` 三个榜废弃后，「题解广场」是唯一的社区内容出口。

## 18. WebSocket `/ws/exercises`

**保留**。用途：精进之路 AI 强化题生成实时推送。认证 `?token=`（失败 `4001`）；消息类型 `exercise_generated / generation_completed / generation_failed / subscribed`；客户端 `ping`/`pong` 心跳，30s 无消息服务端发 ping，5s 无 pong 断开。重写时泛化为「AI 生成任务推送通道」供新模块复用。

---

## 数据模型清单（34 个模型文件）

### 用户与认证

| 表 | 关键字段 | 说明 |
|---|---|---|
| `users` | `id`(UUID PK)、`email`/`username`(unique)、`hashed_password`、`is_active`/`is_admin`/`is_test_account`；成长字段：`xp`、`mastery_xp`、`mastery_level`、`streak_days`、`total_checkin_days`、`last_activity_date`、`weak_points`(JSON)、`cores`/`cores_total_earned`/`cores_total_spent`(默认 100/100/0)、`total_exercises`/`correct_exercises`/`accuracy_rate` | ✅ 已确认 `total_xp`、`current_streak` 死字段**已删除**，无残留 |
| `login_sessions` | `user_id` FK、`token`(unique)、`is_active`、`expires_at` | 登录会话/在线监控 |

### 学习统计（stats.py 同文件三表）

| 表 | 关键字段 | 说明 |
|---|---|---|
| `chapter_progress` | `user_id` FK、`chapter_id`(无 FK)、`status`、`progress_percent`、`completed_subsections`(JSON)、`exercise_results`(JSON) | ⚠️ 旧进度体系，待数据迁移后**删表** |
| `learning_sessions` | `user_id` FK、`chapter_id`、`subsection_index`、`started_at`/`ended_at`/`duration_seconds`/`is_active` | 学习时长 |
| `activity_logs` | `user_id` FK、`activity_type`、`description`、`extra_data`(JSON) | 活动流 |

### 课程结构

| 表 | 关键字段 | 说明 |
|---|---|---|
| `courses` | `id`(Int PK)、`code`(unique: C/CPP/Python)、`difficulty_level`、`is_active` | |
| `chapters` / `sections` | 层级 FK、`order_index`、`content`、`learning_objectives`(JSON) | |
| `section_knowledge_points` | `section_id` FK、`name`、`content`(Markdown)、代码三件套、`difficulty`/`importance` | 人工精编知识卡的内容载体 |
| `exercises` | `id`(Int PK)、`chapter_id` FK、`source`(manual/tk/ai_generated)、`z_id`(unique)、`type`(choice/programming/fill_blank)、`difficulty`(1-8)、`knowledge_points`/`test_cases`/`hints`(JSON)、`embedding`/`tag_embedding`、`is_verified` | 题库 |
| `section_base_questions` | `section_id` FK、`user_id`(NULL=共享基础题)、`question_source`(base/enhanced)、`options`/`correct_answer`、`test_cases`(JSON) | 精进之路测试题 |
| `exercise_generation_sessions` | `user_id` FK、`session_type`、`status`(generating/completed/failed)、`generated_exercises`(JSON)、`expires_at` | AI 出题会话 |

### 掌握度体系（BKT 四层聚合：知识点→小节→章节→课程）

| 表 | 关键字段 | 说明 |
|---|---|---|
| `knowledge_point_mastery` | BKT 四参数 `p_l0/p_t/p_g/p_s`(默认 0.15/0.1/0.2/0.05)、当前 `p_l`、`total_attempts`/`correct_attempts`、`mastered_at`；唯一约束 `(user_id, knowledge_point)` | 掌握阈值 P(L)≥0.80；能力图谱三轴的数据源 |
| `section_mastery` | `bkt_aggregated_p_l`、`mastery_score`(0-100)、`mastered_points_count` | ⚠️ 「已掌握」计数用 ≥0.95，与知识点层 0.80 阈值不一致 |
| `chapter_mastery` | `mastery_score`、`mastery_level`、四个旧分量分 + BKT 聚合字段（两套并存）；唯一约束 `(user_id, chapter_id)` | |
| `course_mastery` | `bkt_aggregated_p_l`、`mastery_score`；唯一约束 `(user_id, course_id)` | 顶层聚合 |

### 挑战之路 / 精进之路进度

| 表 | 关键字段 | 说明 |
|---|---|---|
| `user_arena_profiles` | `tier`(默认 bronze)、`sub_tier`(默认 4)、`stars`、`protection_remaining`、`highest_tier`；`current_streak`/`best_streak`（连对数，≠ 打卡 streak）；⚠️ 模块内残留分数阈值制常量 `TIER_THRESHOLDS` | 每用户一条；段位双算法问题所在 |
| `challenge_sessions` | `user_id`/`course_id` FK、`exercise_ids`(JSON)、`status`、`session_type`(challenge/infinite)、分数与加成 | 挑战会话 |
| `arena_exercise_progress` | 唯一约束 `(user_id, exercise_id)`、`stars_awarded`/`stars_deducted`、`saved_codes`(JSON)、`correct_at` | 每题进度（无会话概念，持久化） |
| `mastery_exercise_progress` | 唯一约束五元组、`exercise_key`、答案快照 | 精进之路每题进度 |
| `answer_history` | `question_source`(mastery/challenge/exercise)、`p_l_before`/`p_l_after`、`counted_for_mastery`/`not_counted_reason`（防刷分） | 作答明细 |

### 货币与流水（三本 append-only 账本，结构同构：用户+方向+数量+变化后快照+来源引用+时间）

| 表 | 关键字段 | 说明 |
|---|---|---|
| `core_transactions` | `type`(earn/spend)、`category`、`amount`+`balance_after`、`reference_type`/`reference_id` | 智核 |
| `tier_transactions` | `stars_change`、前后态段位/星快照、`promoted`/`demoted`/`used_protection`、`source` | 段位 |
| `mastery_xp_transactions` | `type`、`category`、`amount`+`balance_after`、`level_before`/`level_after`/`level_up` | 精进 XP（待与 users.xp 合一） |
| `ai_hint_cache` | 唯一约束 `(user_id, exercise_id, hint_level)`、`cost` | 已购提示缓存，复看不收费 |

### 复习与错题

| 表 | 关键字段 | 说明 |
|---|---|---|
| `spaced_repetitions` | `next_review_at`、`review_interval`、`ease_factor`(SM-2 默认 2.5)、`stage_id`(已弃用) | 间隔 1/3/7/14/30 天 |
| `wrong_questions` | `exercise_key`、`exercise_content` 快照、`error_count`、`is_resolved`、`stage_id`(弃用) | 错题本 |
| `user_weak_points` | `knowledge_point`、`error_count`、`mastery_level`(1-5) | 与 `users.weak_points` JSON 列重复（产品方案：留表删列） |

### 任务 / 成就 / 社区 / 收藏 / 笔记

| 表 | 说明 |
|---|---|
| `challenges` + `user_challenges` | 任务挑战系统（待删，见 02） |
| `achievements` + `user_achievements` | 成就（奖励含 `xp_reward`/`quota_reward`，并入单 XP） |
| `solutions` + `solution_likes` | 题解广场 |
| `favorites` | 收藏夹（结构对齐错题本） |
| `notes` + `note_tags` | 笔记与标签 |
| `section_progress` | 小节进度（新体系，保留） |

### 主键与 FK 的已知不一致（重写时注意）

- 主键风格两派：多数表 String(36) UUID；`courses/chapters/sections/exercises/challenges/achievements/solutions/section_*` 为 Integer 自增。
- 大量「软外键」：`chapter_progress.chapter_id`、`notes.*`、`favorites.*`、`user_arena_profiles.course_id`、`tier_transactions.course_id` 等无 FK 约束。
- `models/__init__.py` 中 `Section` 在 `__all__` 重复两次；`ChapterBaseQuestion` 只是 `SectionBaseQuestion` 别名。

## 前端消费侧已知错位（实现目标设计时一并修）

1. `profile.ts addXp` 声明响应 `{xp, level, xp_for_next_level}`，后端实际返回 `{xp, mastery_xp, mastery_level}`。
2. `learning-path.ts getMasteryExerciseRecommendations` 用 GET 调后端 POST 端点，必然 405。
3. 前端 hint 成本（light=1/medium=3/deep=5）为硬编码推算，未读后端 `ai_policy`。
4. `index.ts` 未再导出 `xp.ts`、`solutions.ts`；多个 API 文件里有定义但未 `export` 的死函数。

# 后端代码库结构文档

> 本文档面向初次接触本项目的开发者，逐目录、逐文件地说明后端代码库的结构与职责。
>
> 技术栈：Python 3.10+ / FastAPI / SQLAlchemy 2.0 (async) / SQLite (aiosqlite) / Pydantic v2
>
> 产品定位：「AI 时代的编程实战训练舱」——四模块训练 + 掌握度追踪 + 徽章系统 + 智核经济。

---

## 1. 顶层目录总览

```
backend/
├── app/                 # 应用主代码（所有业务逻辑）
│   ├── main.py          # FastAPI 应用入口，组装 app
│   ├── config.py        # 全局配置（Pydantic Settings，读 .env）
│   ├── database.py      # 异步数据库引擎、会话工厂、建表逻辑
│   ├── __init__.py      # 包标记
│   ├── ai/              # AI 基础设施（provider 抽象 + HTTP 客户端）
│   ├── auth/            # 认证域（用户模型、JWT、注册/登录路由）
│   ├── core/            # 应用骨架（路由注册、中间件、生命周期、异常处理）
│   ├── services/        # 外部服务集成（Judge0 代码执行）
│   ├── training/        # 训练舱核心业务域（模型、服务、路由、掌握度、徽章、种子数据）
│   └── utils/           # 纯工具函数
├── scripts/             # 运维脚本（徽章回填、列迁移）
├── tests/               # 测试套件
├── data.db              # SQLite 数据库文件（运行时生成）
├── test.db              # 测试用数据库
├── Dockerfile           # 容器构建
├── requirements.txt     # 依赖声明
├── pytest.ini           # pytest 配置
├── pyrightconfig.json   # 类型检查配置
└── .env                 # 环境变量（不入库）
```

---

## 2. 应用入口层 (`app/`)

### `app/main.py` — FastAPI 应用工厂

创建并配置 FastAPI 应用实例。采用工厂函数 `create_app()` 模式，依次完成：

1. 读取 `Settings`
2. 设置 `lifespan`（启动时建表 + 灌种子 + 配置 AI）
3. 注册中间件（CORS + 限流）
4. 注册路由（auth + training 两组）
5. 注册健康检查端点（`/` 和 `//health`）
6. 注册全局异常处理器

模块级变量 `app = create_app()` 供 uvicorn 直接引用：`uvicorn app.main:app`。

### `app/config.py` — 全局配置

使用 `pydantic-settings` 的 `BaseSettings`，从 `.env` 文件和环境变量加载配置：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接串 | `sqlite+aiosqlite:///./data/data.db` |
| `SECRET_KEY` | JWT 签名密钥（≥32 字符，必填） | — |
| `ALGORITHM` | JWT 算法 | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 有效期（分钟） | `1440`（1 天） |
| `ACCESS_TOKEN_EXPIRE_MINUTES_REMEMBER` | 记住我时的 Token 有效期 | `10080`（7 天） |
| `AI_PROVIDER` | AI 供应商 | `deepseek` |
| `AI_API_KEY` | AI API 密钥 | — |
| `AI_MODEL` | AI 模型名 | `deepseek-v4-flash` |
| `AI_BASE_URL` | AI API 地址 | `https://api.deepseek.com` |
| `AUTH_RATE_PER_MINUTE` | 认证接口限流（次/分钟） | `10` |

`get_settings()` 用 `@lru_cache` 缓存，全局单例。包含两个 `field_validator`：`SECRET_KEY` 必须非空且 ≥32 字符，`DATABASE_URL` 必须非空。

### `app/database.py` — 数据库引擎与会话

**核心职责**：

- 创建全局异步引擎 `engine`（`create_async_engine`），连接 SQLite。
- 在 SQLite 连接时设置 PRAGMA：`foreign_keys=ON`（外键约束）、`journal_mode=WAL`（并发读写）、`busy_timeout=30000`（写竞争超时 30s）。
- 创建会话工厂 `AsyncSessionLocal`（`async_sessionmaker`），`expire_on_commit=False`。
- 定义 `Base`（`DeclarativeBase`），所有 ORM 模型的基类。
- 提供 `get_db()` 异步生成器依赖：自动 commit / rollback / close。
- 提供 `init_db()`：`create_all` 幂等建表 + Alembic 版本戳记。

### `app/__init__.py`

仅一行注释标记，无逻辑。

---

## 3. 核心骨架层 (`app/core/`)

### `app/core/__init__.py`

包标记，含一行 docstring。

### `app/core/routes.py` — 路由注册

注册两组业务路由：

- `auth_router`（前缀 `/api/auth`）
- `training_router`（前缀 `/api`）

以及两个健康端点：

- `GET /` — 返回 `{"status": "ok", "message": "智码领航 API is running"}`
- `GET /health` — 返回 `{"status": "healthy"}`

### `app/core/lifespan.py` — 应用生命周期

`create_lifespan(settings)` 返回一个 `@asynccontextmanager`，在 FastAPI 启动时依次执行：

1. `configure_logging()` — 配置全局日志格式
2. `await init_db()` — 建表
3. 灌入种子数据 `await seed_deck(db)` — 知识点、审查关卡、竞技场挑战、认证考试
4. `configure_ai_service(settings)` — 从配置初始化 AI 服务

关闭时 `await ai_service.aclose()` 释放 HTTP 连接。

**关键细节**：通过 side-effect import 注册 ORM 模型到 `Base.metadata`（`app.auth.models` 和 `app.training.models`），确保 `init_db()` 的 `create_all` 能发现所有表。

### `app/core/middleware.py` — 中间件

包含两部分：

**限流 (`RateLimiter` + `RateLimitMiddleware`)**：

- 滑动窗口算法，内存字典存储，按 key（IP）追踪时间戳。
- `/api/auth/*` 端点按 IP 限流，超限返回 `429`。
- 健康端点等 `EXEMPT_PATHS` 豁免。
- `reset_rate_limiters()` 供测试间重置状态。

**CORS**：

- 默认允许 `localhost:3000` 和 `127.0.0.1:3000`。
- 支持通过环境变量 `CORS_ORIGINS` 追加生产域名。
- 允许正则匹配本地地址。

### `app/core/exceptions.py` — 异常处理

注册两个全局异常处理器：

1. **`RequestValidationError` → 422**：将 Pydantic 校验错误转为前端友好的中文消息（如「密码长度至少需要 8 个字符」）。
2. **`Exception` → 500**：记录完整 traceback 到日志，返回 `{"detail": "Internal server error"}` 不暴露内部信息。

---

## 4. 认证域 (`app/auth/`)

### `app/auth/__init__.py` — 包导出

统一导出认证域的全部公共接口：`User` 模型、Schema 类、`AuthService`、安全工具函数、依赖注入函数、路由、错误类。

### `app/auth/models.py` — 用户模型

`User` 表（`users`）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `String(36)` PK | UUID |
| `email` | `String(255)` unique | 邮箱 |
| `username` | `String(100)` unique | 用户名 |
| `hashed_password` | `String(255)` | bcrypt 哈希 |
| `is_active` | `Boolean` | 账户是否激活 |
| `is_admin` | `Boolean` | 是否管理员 |
| `cores` | `Integer` | 智核余额（平台货币，默认 100） |
| `created_at` / `updated_at` | `DateTime` | 时间戳 |

**设计原则**：训练舱重构后，领域数据（掌握度、训练记录、智核流水）全部落在 `app.training.models` 的事件/账本表中，不在 User 上冗余。`cores` 字段是余额缓存，事实源是 `DeckCoreTransaction` 账本表。

### `app/auth/schemas.py` — Pydantic 模型

| Schema | 用途 |
|--------|------|
| `UserBase` | 基类，含 `email` + `username`（带校验：用户名 2-100 字符，只允许字母/数字/下划线/中文） |
| `UserCreate` | 注册请求，继承 `UserBase` + `password`（校验：≥8 字符、含字母、含数字） |
| `UserLogin` | 登录请求，支持用户名或邮箱登录、记住我 |
| `UserResponse` | 用户公开信息响应（含 `id`, `is_active`, `is_admin`, 时间戳） |
| `Token` | JWT 响应（`access_token` + `token_type` + `user`） |
| `TokenData` | 解码后的 token 数据 |
| `ForgotPasswordRequest` | 忘记密码请求（仅 `email`） |

### `app/auth/security.py` — 安全工具

- `verify_password(plain, hashed)` — bcrypt 验证（截断至 72 字节）
- `get_password_hash(password)` — bcrypt 哈希（rounds=12）
- `create_access_token(data, expires_delta)` — 生成 JWT
- `decode_token(token)` — 解码并验证 JWT

### `app/auth/dependencies.py` — FastAPI 依赖注入

- `get_current_user` — 从 Bearer token 解码出 `user_id`，查库返回 `User`，无效则 401，未激活则 403。
- `get_current_active_user` — `get_current_user` 的别名（额外确保激活），供路由直接 `Depends`。

### `app/auth/service.py` — 认证业务逻辑

`AuthService` 类（持有 `db: AsyncSession`）：

- `register(user_data)` — 检查邮箱/用户名唯一性，创建用户，生成 token。
- `login(login_data)` — 按邮箱或用户名查找用户，验证密码，生成 token（记住我用更长有效期）。
- `get_user_by_id(user_id)` — 按 ID 查用户。
- `forgot_password(email)` — 查找用户但不暴露是否存在（防枚举），实际发送逻辑未实现。

### `app/auth/errors.py` — 认证错误类

自定义异常层次：

```
AuthError (基类)
├── EmailAlreadyRegisteredError    — "该邮箱已被注册"
├── UsernameAlreadyRegisteredError — "该用户名已被使用"
├── InvalidCredentialsError        — "用户名或密码错误"
└── InactiveAccountError           — "Account is inactive"
```

### `app/auth/router.py` — 认证路由

前缀 `/api/auth`，4 个端点：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册，返回 201 + Token |
| POST | `/api/auth/login` | 登录，返回 Token |
| POST | `/api/auth/forgot-password` | 忘记密码，始终返回 200（防枚举） |
| GET | `/api/auth/me` | 获取当前用户信息（需认证） |

---

## 5. 训练舱核心域 (`app/training/`)

这是整个后端最核心、代码量最大的模块。

### `app/training/__init__.py`

包标记，含 docstring。

### `app/training/models.py` — 数据模型（16 张表）

所有表名统一 `deck_` 前缀。按功能分组：

#### 知识点与掌握度

| 表名 | 模型类 | 说明 |
|------|--------|------|
| `deck_knowledge_points` | `DeckKnowledgePoint` | 知识点定义（种子内置），按三轴（review/debug/implement）分组，含费曼检验评分要点 `key_points` |
| `deck_user_mastery` | `DeckUserMastery` | 用户知识点掌握度**缓存**：`p_l`（回忆概率）、`level`（掌握等级）。复合主键 (user_id, kp_id) |
| `deck_mastery_events` | `DeckMasteryEvent` | 掌握度**事件流（事实源）**：每次答题/检验一条记录，`p_l` 与 `level` 由它重放推导 |

#### 能力与发展

| 表名 | 模型类 | 说明 |
|------|--------|------|
| `deck_ability_axes` | `DeckAbilityAxis` | 三轴经验值（审阅/调试/实现），等级 = 1 + xp//400 |
| `deck_daily_activity` | `DeckDailyActivity` | 每日活动统计（分钟数、练习数、正确数），用于节奏柱图和连续天数 |
| `deck_feed_events` | `DeckFeedEvent` | 动态流事件，`payload.segments` 与前端 FeedItem 同构 |
| `deck_core_transactions` | `DeckCoreTransaction` | 智核账本（唯一变动途径），记录 delta、reason、balance_after |
| `deck_user_badges` | `DeckUserBadge` | 已解锁徽章事实表，复合唯一约束 (user_id, badge_id) 保证幂等 |

#### 代码审查室

| 表名 | 模型类 | 说明 |
|------|--------|------|
| `deck_review_sessions` | `DeckReviewSession` | 审查关卡（种子内容）：代码、缺陷数、难度、ETA |
| `deck_injected_defects` | `DeckInjectedDefect` | 注入缺陷（**服务端秘密，绝不下发**）：行号、类型、解释 |
| `deck_review_attempts` | `DeckReviewAttempt` | 审查提交记录：用户标记 `marks` + 判定结果 `verdict` |

#### 调试竞技场

| 表名 | 模型类 | 说明 |
|------|--------|------|
| `deck_arena_challenges` | `DeckArenaChallenge` | 竞技场挑战（种子内容，按日轮换）：代码、失败输出、时间限制 |
| `deck_arena_attempts` | `DeckArenaAttempt` | 竞技场提交记录：是否解决、通过数/总数 |
| `deck_arena_ratings` | `DeckArenaRating` | 竞技场段位积分：rating（默认 1200）、win_streak |

#### 苏格拉底导师

| 表名 | 模型类 | 说明 |
|------|--------|------|
| `deck_tutor_messages` | `DeckTutorMessage` | 导师对话消息：role（user/tutor）、mode（socratic/feynman）、grade（费曼评级） |

#### 基本功认证

| 表名 | 模型类 | 说明 |
|------|--------|------|
| `deck_cert_exams` | `DeckCertExam` | 认证考试定义（种子内容），`id=placement` 为定级测试 |
| `deck_cert_questions` | `DeckCertQuestion` | 认证题目（**答案不下发**）：MCQ 答案 / code 关键片段 |
| `deck_certifications` | `DeckCertification` | 用户获得的认证凭证：主题、等级、分数、验证码 |

### `app/training/mastery.py` — 掌握度纯函数引擎

**不碰数据库**——输入是事件记录序列，输出是回忆概率、掌握等级、趋势、费曼评级。

核心算法：

- **HLR（半衰期回归）记忆模型**：
  - 首次接触后初始半衰期 1 天
  - 答对一次半衰期 ×1.8（封顶 180 天）
  - 答错一次半衰期 ×0.5（保底 0.2 天）
  - 回忆概率 `p = 2^(-Δ/h)`，Δ = 距最近答对的天数

- **Khan 式四级掌握等级**（初识/熟悉/熟练/精通）：
  - 熟悉：p ≥ 0.3
  - 熟练：p ≥ 0.6 且答对 ≥ 3 次
  - 精通：p ≥ 0.8 且答对 ≥ 4 次 **且** 存在间隔 ≥ 3 天的答对对 **且** 至少一次实战来源（review_gym/arena/certification）——纯费曼永远到不了精通

- **趋势**：当前 p 与 7 天前的 p 之差（up/down/flat）

- **费曼评分**：要点覆盖率 + 结构分（因果词「因为/所以」+ 举例词「比如/例如」）

导出函数：`half_life_days()`、`recall_probability()`、`mastery_level()`、`compute_trend()`、`feynman_grade()`。

### `app/training/badges.py` — 徽章系统

**设计模式**：定义清单（常量，不入库）+ 事实聚合 + 幂等评估引擎。

- **17 枚徽章**，分铜（+5 智核）/银（+10）/金（+20）三档，其中 3 枚为隐藏徽章（未解锁时脱敏为 `???`）。
- **`BadgeFacts`** dataclass：一次评估所需的全部事实（由 `collect_facts()` 一次性聚合，规则只读它，不各自查库）。
- **`BadgeDef`** dataclass：每枚徽章的定义，含 `check(facts, ctx) -> bool` 纯函数规则。
- **`evaluate_and_award(db, user_id, ctx)`**：全量跑规则，新达成的写表 + 发智核 + 写动态，幂等（已解锁的跳过）。在四个提交端点（审查/竞技场/费曼/认证）commit 前统一调用。
- **`list_badges(db, user_id)`**：徽章墙——全量 17 枚 + 解锁状态。
- **`collect_facts(db, user_id)`**：集中聚合各事实表（认证数/级别、审查数/全中、竞技场胜场/连胜、费曼合格数/最佳评级、连续天数、夜间事件、comeback 等）。

`ctx` 是本次提交的瞬时上下文（dict），支持 `arena_win_streak` 和 `cert_score` 两个键，用于回填时（ctx=None）与实时判定时保持一致。

### `app/training/service.py` — 领域服务

训练舱的核心业务逻辑层（454 行），包含：

**能力轴**：
- `get_axes(db, user_id)` — 三轴经验 + 每轴短板知识点
- `add_axis_xp(db, user_id, axis, amount)` — 增加经验
- `axis_level(xp)` — 等级 = 1 + xp // 400

**掌握度**（桥接 DB 与纯函数引擎）：
- `record_mastery_event(...)` — 写事件 + 重算 p_l/level 缓存
- `mastery_trends(db, user_id)` — 各知识点 7 天趋势
- `has_placement(db, user_id)` — 是否已定级

**智核经济**（唯一变动途径）：
- `change_cores(db, user, delta, reason)` — 增减智核 + 记账，余额不会变负
- `today_cores_used(db, user_id)` — 今日消耗

**活动与动态**：
- `touch_activity(db, user_id, ...)` — 更新今日活动
- `add_feed(db, user_id, kind, segments)` — 写动态流
- `feed_time_label(created_at)` — 时间格式化（刚刚/昨天/N天前）

**段位**：
- `tier_of(rating)` — 积分→段位名（青铜→王者）
- `get_or_create_rating(db, user_id)` — 获取或创建段位记录
- `week_rank(db, rating)` — 全站排名

**判定逻辑**（对齐前端 mock）：
- `judge_marks(defects, marks)` — 审查判定：行号±1 容差 + 类型匹配，算命中率/准确率/得分
- `judge_arena_code(code, failing_output)` — 竞技场判定：正则匹配关键代码模式（当前是规则判定，后续换 Judge0）
- `judge_cert_answer(kind, answer, correct, includes)` — 认证判分：MCQ 精确匹配 / code 关键片段包含

**导师脚本**（当前是规则回复，后续换 LLM）：
- `socratic_reply(text, history_len)` — 关键词匹配的苏格拉底式追问
- `feynman_opening(topic)` — 费曼开场白
- `feynman_feedback(grade, covered, missed)` — 按评分生成点评

**连续训练**：
- `streak_days(db, user_id)` — 从今天往前连续有活动的天数
- `next_cert_available_days(db, user_id)` — 认证冷却剩余天数
- `attempts_today(db, user_id)` — 今日审查完成数与平均准确率

### `app/training/router.py` — 训练舱 API 路由

前缀 `/api`，是后端最大的文件（1221 行），覆盖所有训练舱端点：

#### Dashboard

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/dashboard` | 首页数据：主任务分发、四模块 stat-line、弱点、7 天节奏、复盘待清、动态 |

#### 能力图谱与档案

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/ability-map` | 能力图谱：三轴 + 全部知识点的 p_l/level/trend |
| GET | `/api/profile` | 个人档案：智核流水、段位、认证列表、全站排行榜、动态 |

#### 代码审查室

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/review-gym/session` | 获取审查关卡（不含注入缺陷） |
| POST | `/api/review-gym/submit` | 提交审查判定（幂等：已全中直接返回旧结果；重做只按新增命中结算） |

#### 复盘

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/review/queue` | 错题/失败项聚合：审查漏报、竞技场未攻克、弱知识点 |

#### 调试竞技场

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/arena/home` | 竞技场首页：段位、今日挑战、全站排行榜 |
| POST | `/api/arena/run` | 提交代码判定：胜则加分+连胜+智核奖励，败则连胜清零 |

#### 苏格拉底导师

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tutor/state` | 导师状态：对话历史、智核余额、推荐主题 |
| POST | `/api/tutor/message` | 发送消息（苏格拉底模式，扣智核） |
| POST | `/api/tutor/feynman` | 开始费曼检验（创建内存态会话） |
| POST | `/api/tutor/feynman/check` | 提交费曼讲述评分（写掌握度事件 + 扣智核 + 评徽章） |

#### 基本功认证

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/certification/home` | 认证首页：已获认证、可考列表、徽章墙 |
| GET | `/api/certification/exam` | 获取试卷（绝不下发答案字段） |
| POST | `/api/certification/submit` | 提交认证：判分→写凭证→发智核→评徽章。`placement` 特殊处理：写全部知识点定级事件 + 三轴初始经验 |

**主任务分发逻辑**（`build_main_task`）：
- 未定级 → 返回 `null`（前端引导去定级）
- 实现轴 < LV.3 → 走认证或导师
- 否则 → 最低轴对应的模块

### `app/training/seed.py` — 种子数据

幂等灌入（`knowledge_points` 非空则跳过）：

- **12 个知识点**：按三轴分组（review 4 个 / debug 4 个 / implement 4 个），每个含 5 个费曼评分要点。
- **2 个审查关卡**：快速排序实现（2 处缺陷）、链表反转（3 处缺陷）。
- **1 个竞技场挑战**：中位数统计（死循环 bug）。
- **2 套认证考试**：指针认证（6 题）、定级测试（5 题）。

---

## 6. AI 基础设施 (`app/ai/`)

### `app/ai/__init__.py` — 包导出

统一导出 AI 配置、服务单例、Provider 抽象和错误类。

### `app/ai/config.py` — AI 配置

`AIProviderConfig` (Pydantic BaseModel)：provider、api_key、model、temperature、base_url、local_base_url、is_local_first。

### `app/ai/service.py` — AI 服务层

`AIService` 类（全局单例 `ai_service`）：

- `configure(config)` — 初始化 OpenAI 兼容客户端 + provider
- `is_configured()` — 检查是否已配置
- `aclose()` — 关闭 HTTP 连接
- `get_provider_status()` — 返回当前 provider 状态

**业务方法**（当前训练舱路由未直接使用，保留给旧系统兼容或后续接入）：
- `generate_chat(message)` — 生成 AI 问答
- `stream_chat(message, context)` — 流式生成
- `generate_choice_explanation(...)` — 选择题解答
- `generate_code_review(code, language)` — 代码审查
- `generate_exercises(...)` — AI 生成练习题
- `generate_personalized_quiz(...)` — 个性化测试题
- `stream_exercise_hint(...)` — 流式编程题提示

### `app/ai/provider/` — Provider 子包

#### `base.py` — 抽象接口

- `AIMessage` = `dict[str, str]`（role + content）
- `AICompletionClient` (Protocol)：`complete(messages) -> str` + `stream(messages) -> AsyncGenerator`
- `AIProvider` (ABC)：`generate_explanation(prompt)` + `review_code(code, language)` + `stream_generate(messages)`

#### `client.py` — OpenAI 兼容 HTTP 客户端

`OpenAICompatibleClient` 类：

- 直接用 `httpx.AsyncClient` 调用 `/chat/completions` 端点。
- **重试机制**：最多 3 次，5xx 和网络错误可重试，指数退避。
- **流式解析**：逐行读取 `data: ` 前缀的 SSE，解析 JSON delta，遇到 `[DONE]` 结束。
- **安全**：错误响应中会脱敏 API key。
- **连接管理**：自动创建/复用 HTTP 客户端，支持注入外部客户端（测试用）。

#### `openai.py` — Provider 实现

`OpenAICompatibleProvider` 实现 `AIProvider` 接口：

- `generate_explanation(prompt)` — system prompt（编程老师）+ user prompt
- `review_code(code, language)` — system prompt（代码审查专家）
- `stream_generate(messages)` — 透传流式

#### `errors.py` — 错误类

```
AIProviderError (基类)
├── AIProviderConfigurationError — 配置缺失或不支持
├── AIProviderNetworkError       — 网络请求失败（含重试次数）
├── AIProviderHTTPError          — HTTP 错误（含状态码和响应摘要）
├── AIProviderProtocolError      — 协议错误（含 content_started 标记）
└── AIProviderStreamError        — 流式中断/未完成
```

---

## 7. 外部服务集成 (`app/services/`)

### `app/services/__init__.py`

包标记，说明领域服务在各域包内（`app.auth.service` / `app.ai.service`），本包只放外部集成。

### `app/services/judge0.py` — Judge0 代码执行服务

`Judge0Service` 类：

- 封装 Judge0 API（在线代码执行平台），当前训练舱竞技场尚未接入（用的是规则判定），保留给后续真实判分。
- `execute_code(code, language_id, stdin)` — 单次执行
- `execute_batch(code, language_id, test_cases)` — 批量执行（多测试用例）
- 包含语言 ID 映射（Python=71, C=50, Java=62 等）和状态码消息（中文）。
- `_build_case_result()` / `_build_batch_response()` — 构建判定结果。
- `format_output(result)` — 格式化执行结果（含中文消息）。

### `app/services/judge0_client.py` — Judge0 HTTP 客户端

`Judge0Client` 类：

- 使用 Base64 编码提交代码（Judge0 API 要求）。
- `submit(code, language_id, stdin, expected_output)` — 单次提交（`wait=true` 同步等待）
- `submit_batch(code, language_id, test_cases)` — 批量提交 + 轮询结果
- `_poll_submission(token)` — 轮询单个提交结果（最多 20 次，间隔 0.3s）
- `_poll_tokens(tokens)` — 并发轮询多个 token（`asyncio.wait` + 异常传播）
- 自动解码 stdout/stderr/compile_output 的 Base64。

---

## 8. 工具层 (`app/utils/`)

### `app/utils/__init__.py`

包标记。

### `app/utils/time.py` — 时间工具

仅一个函数 `utc_now()` — 返回带时区的 UTC 时间（`datetime.now(timezone.utc)`）。供所有模型的时间戳默认值使用。

---

## 9. 运维脚本 (`scripts/`)

### `scripts/backfill_badges.py` — 徽章回填

对全部用户各跑一次 `evaluate_and_award(ctx=None)`。仅依赖历史事实的规则会补发；依赖瞬时上下文的规则（如竞技场三连胜历史峰值）不回填。幂等，可重复执行。

用法：`cd backend && python -m scripts.backfill_badges`

### `scripts/migrate_missing_columns.py` — 列迁移

开发辅助脚本：自动检查 SQLAlchemy 模型中有但 SQLite 数据库中缺失的列，执行 `ALTER TABLE ADD COLUMN`。仅处理新增列，不处理类型变更/约束变更/数据迁移。

用法：`cd backend && python -m scripts.migrate_missing_columns`

---

## 10. 测试 (`tests/`)

### `tests/conftest.py` — 测试配置

- 使用 `:memory:` SQLite + `StaticPool`（共享内存数据库）。
- 在导入 `app.main` 之前替换 `app.database.engine` 和 `AsyncSessionLocal` 为测试引擎。
- 禁用 lifespan（避免 `init_db` 干扰）。
- 覆盖 `get_db` 依赖，注入测试会话。
- 提供 fixtures：`setup_database`（建表+清表）、`db_session`、`client`（httpx AsyncClient）、`auth_user`/`test_user`/`admin_user`、`auth_headers`（JWT）、`test_user_token`/`admin_token`。
- `autouse` fixture：每个测试间重置限流器状态。

### 测试文件列表

| 文件 | 测试内容 |
|------|----------|
| `test_app_structure.py` | 应用结构完整性（路由注册、中间件等） |
| `test_auth.py` | 认证端点端到端测试 |
| `test_auth_service.py` | AuthService 业务逻辑 |
| `test_auth_dependencies.py` | 认证依赖注入 |
| `test_config.py` | 配置加载与校验 |
| `test_database.py` | 数据库引擎与会话 |
| `test_rate_limit.py` | 限流中间件 |
| `test_start_services_env.py` | 启动环境检查 |
| `test_validation_errors.py` | 校验错误处理 |
| `test_ai_provider_client.py` | AI Provider HTTP 客户端 |
| `test_ai_lifespan.py` | AI 服务生命周期 |
| `test_training_mastery.py` | 掌握度纯函数引擎 |
| `test_training_badges.py` | 徽章评估引擎 |

### 测试 fixtures

- `tests/fixtures/minimal.xml` — 最小 XML fixture
- `tests/fixtures/sample_problems.xml` — 示例题目 XML

---

## 11. 配置文件

| 文件 | 说明 |
|------|------|
| `Dockerfile` | 基于 `python:3.11-slim`，安装依赖、复制代码、创建非 root 用户、暴露 8000 端口、`uvicorn app.main:app` 启动 |
| `requirements.txt` | 依赖声明：FastAPI、uvicorn、SQLAlchemy、Pydantic、python-jose、passlib、bcrypt、alembic、aiosqlite、httpx 等 |
| `pytest.ini` | pytest 配置：testpaths=tests、asyncio_mode=auto |
| `pyrightconfig.json` | 类型检查：Python 3.10、basic 模式、仅检查 app/ |
| `.env` | 环境变量（不入库） |
| `.dockerignore` | Docker 构建忽略文件 |

---

## 12. 架构设计要点

### 分层结构

```
Router（路由层）  →  Service（领域服务）  →  Models（ORM 模型）
                          ↓
                    mastery.py / badges.py（纯函数引擎）
                          ↓
                    database.py（基础设施）
```

- **路由层**（`router.py`）：接收请求、调用 service、组装响应。不直接写业务逻辑。
- **领域服务**（`service.py`）：业务逻辑编排，桥接数据库与纯函数引擎。
- **纯函数引擎**（`mastery.py`、`badges.py`）：无副作用的核心算法，输入→输出，可独立测试。
- **模型层**（`models.py`）：ORM 定义，只管数据结构。
- **基础设施**（`database.py`、`ai/`、`services/`）：技术关注点。

### 事件溯源模式

掌握度系统采用事件溯源：

- **事实源**是 `deck_mastery_events` 事件表（每次答题一条记录）。
- `deck_user_mastery` 的 `p_l` / `level` 是**重放推导的缓存读模型**。
- `record_mastery_event()` 写事件后立即重算缓存。
- `mastery.py` 是纯函数引擎，不碰数据库，输入事件序列输出计算结果。

### 智核经济

- 智核（Cores）是平台货币，用户初始 100。
- **唯一变动途径**是 `service.change_cores()`，每次变动都写 `deck_core_transactions` 账本（delta + reason + balance_after）。
- 余额不会变负（`max(0, ...)`）。

### 幂等设计

- 审查提交：已全中的关卡重做直接返回旧结果；重做只按新增命中结算经验。
- 徽章评估：`deck_user_badges` 复合唯一约束兜底，已解锁的跳过。
- 种子数据：`knowledge_points` 非空则跳过。
- 建表：`create_all` 幂等，只创建缺失的表。

### 契约一致性

- 后端响应结构（snake_case）与 `frontend/lib/api/deck/types.ts` 逐字段对应。
- 判定规则与 `frontend/lib/api/deck/mock/` 下的纯函数一一对应（mock 是后端的参考实现）。
- 所有 API 契约全链路使用 **snake_case**，无 key 转换层。

---

## 13. 数据流速览

### 用户注册到首次训练

```
POST /api/auth/register
  → AuthService.register()
    → 检查唯一性 → 创建 User（cores=100）→ 生成 JWT
  → 返回 Token

GET /api/dashboard
  → has_placement() = false → main_task = null
  → 前端引导去定级测试

POST /api/certification/submit (exam_id=placement)
  → 判分 → 全部知识点写定级事件 → 三轴初始经验 → 动态
  → 返回 score + main_task 有了值
```

### 一次代码审查提交

```
POST /api/review-gym/submit
  → 查 session + defects（服务端秘密）
  → judge_marks(defects, marks) — 纯函数判定
  → 写 DeckReviewAttempt
  → add_axis_xp(review, 20×hits) — 经验
  → record_mastery_event(review_gym, correct) — 掌握度事件 + 重算
  → touch_activity() — 活动统计
  → add_feed() — 动态
  → change_cores(+5) if 全中 — 智核
  → badges.evaluate_and_award() — 评徽章
  → commit → 返回 verdict + new_badges
```

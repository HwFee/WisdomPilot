# 通用挑战状态与奖励治理设计

## 目标

将通用挑战 API 的状态转换、进度更新、奖励发放、事务所有权和响应组装整理为可阅读、可测试的完整用例，同时保持现有成功响应、挑战定义和奖励数值兼容。

本设计是后端学习型治理第 3 批的第一个子批次，只覆盖 `/api/challenges` 调用链。Arena challenge path 和 Mastery progress 使用不同模型与奖励算法，分别进入后续 3B、3C 子批次。

## 当前问题

当前 `ChallengeService` 存在以下边界和行为问题：

1. 服务内部调用 `commit()`，与请求级 `get_db` 的提交和回滚职责重复，无法证明进度、完成状态和奖励账本属于同一事务。
2. 完成奖励直接增加 `user.cores`，没有同步 `cores_total_earned`，也没有创建 `CoreTransaction`，因此余额、累计收入和账本不一致。
3. `progress_delta` 没有正数约束，客户端可以通过负数倒退进度。
4. 目标值只读取 `target` 或 `exercise_count`，然后默认成 10；默认的连续学习挑战实际定义为 `days: 7`，章节完成挑战则应是一次性目标。
5. 服务使用裸 `ValueError` 同时表达不存在、未开始和已完成，Router 只能笼统映射。
6. 用户挑战列表、启动结果和进度结果由 Router 手工拼装，稳定响应字段没有独立的纯映射边界。
7. 默认挑战初始化只要发现任意挑战就整体跳过，部分初始化状态无法补齐缺失定义。
8. 现有测试证明基本成功路径，但没有证明重复开始、重复完成、奖励账本一致性、回滚原子性或目标解析。

## 范围

本批次覆盖：

- `GET /api/challenges`、`GET /api/challenges/{id}`、`GET /api/challenges/user/me`。
- `POST /api/challenges/{id}/start` 和 `POST /api/challenges/{id}/progress`。
- 通用 `ChallengeService` 的查询、启动、进度、完成和默认数据初始化。
- `UserChallenge` 已存在记录上的状态转换和重试幂等。
- 完成挑战时的智核余额、累计收入和 `CoreTransaction` 账本一致性。
- 纯响应映射和明确的 Pydantic 进度响应模型。

本批次不覆盖：

- `/api/learning-path/challenge/*` 的 Arena exercise selection、Judge0、星级、段位和错题逻辑。
- Mastery quiz、章节掌握度、BKT 或 mastery XP。
- ChallengeSession 计分服务。
- 挑战奖励数值、默认挑战文案、JWT、前端或数据库模式变更。
- 同一用户并发发送两个“首次启动”请求时的数据库级唯一性。严格保证这一场景需要 `(user_id, challenge_id)` 唯一约束和迁移，应放入独立模式批次。

## 方案比较

### 方案一：治理通用 Challenge 状态机（采用）

沿现有 API 和模型边界建立类型化错误、目标解析、行锁进度更新、账本奖励、请求级事务和纯响应映射。该方案覆盖一条完整调用链，能以集成测试证明原子性和顺序重试幂等，不影响 Arena 与 Mastery 算法。

### 方案二：统一三套挑战系统

把通用 Challenge、Arena challenge path 和 Mastery progress 合并为一个状态机。三者的持久化模型、提交语义、奖励和前端契约不同，统一会导致大规模迁移和兼容层，无法作为可独立回退的单批次。

### 方案三：先增加唯一约束

先为 `UserChallenge(user_id, challenge_id)` 增加数据库唯一约束，再同时重写启动和奖励逻辑。它能解决并发首次启动，但把模式迁移和业务行为改造放入同一批，违反治理设计的风险控制。本批记录该限制，不采用此方案。

## 架构

### 领域错误

新增 `backend/app/services/challenge_errors.py`：

- `ChallengeError`：通用挑战预期失败基类。
- `ChallengeNotFoundError(challenge_id)`：挑战定义不存在。
- `ChallengeNotStartedError`：用户尚未启动该挑战。
- `ChallengeAlreadyCompletedError`：已完成挑战不能重新启动。
- `InvalidProgressDeltaError`：服务调用收到零或负进度。
- `InvalidChallengeDefinitionError`：挑战要求无法解析为正数目标；该错误表示服务器数据问题，不映射为客户端 400。

异常不导入 FastAPI。Router 只捕获可归因于请求状态的不存在、未开始、已完成和无效进度错误；未知数据库错误、奖励错误和无效挑战定义继续进入全局 500/回滚路径。

### 目标解析

`ChallengeService` 使用一个纯函数解析目标值：

1. 若 `requirements.target` 是正整数，优先使用。
2. `exercise_count` 类型读取 `exercise_count`。
3. `streak` 类型读取 `days`。
4. `time_spent` 类型读取 `minutes`。
5. `accuracy` 类型读取 `accuracy`。
6. `chapter_complete` 和 `course_complete` 是一次性目标，固定为 1。
7. 缺失、布尔值、非整数或小于 1 的值抛出 `InvalidChallengeDefinitionError`。

默认挑战因此得到目标值 5、1、7，不再依靠魔法默认值 10。

### 状态转换

启动状态规则：

- 挑战不存在：抛出 `ChallengeNotFoundError`。
- 已有 `in_progress` 记录：原样返回，同一顺序重试不会增加 attempts 或创建新记录。
- 已有 `completed` 记录：抛出 `ChallengeAlreadyCompletedError`，保持现有公开行为。
- 没有记录：创建 `in_progress`，进度为 0，attempts 为 1，并使用解析后的目标值。

进度状态规则：

- `progress_delta <= 0`：抛出 `InvalidProgressDeltaError`，不修改状态。
- 记录不存在：抛出 `ChallengeNotStartedError`。
- 已完成：原样返回，不再次发奖励。
- 进行中：在行锁下增加进度；达到目标时一次性设置 `completed` 和 `completed_at`，随后发放奖励。

进度保留实际累计值，不在完成时强制截断为 target，以保持现有超额进度行为。

### 奖励与账本

完成奖励通过 `CoreService(db).earn_cores(...)` 发放，不再直接修改用户字段：

```text
category       = "bonus"
reference_type = "challenge"
reference_id   = UserChallenge.id
description    = "Challenge completed: <challenge.code>"
```

奖励数值继续读取 `challenge.rewards.quota_bonus`。零奖励不创建交易。`CoreService` 同步更新 `cores`、`cores_total_earned` 和 `CoreTransaction`，并执行行锁与 flush。

`UserChallenge` 状态检查发生在奖励前。已提交完成记录的顺序重试会在 completed 分支提前返回，因此同一个 `UserChallenge.id` 只产生一次奖励交易。本批不声称数据库层能阻止两个并发首次启动请求创建两条记录。

### 事务所有权

`ChallengeService` 不再调用 `commit()`：

- 启动、进度和默认初始化使用 `flush()` 让主键和同会话查询可见。
- FastAPI 请求由 `get_db` 在 Router 成功返回后统一提交，异常时统一回滚。
- 服务级调用者显式决定提交或回滚。
- 进度完成、用户余额、累计收入和账本行处于同一数据库事务；奖励失败时全部回滚。

读取待更新的 `UserChallenge` 使用 `SELECT ... FOR UPDATE`。这在支持行锁的数据库上串行化已存在记录的并发进度更新；SQLite 测试环境用于验证事务结构和顺序幂等，不用于证明生产级并发隔离。

### 默认挑战初始化

默认挑战定义保留在 `backend/app/services/challenge.py`，但提取为 `DEFAULT_CHALLENGE_DEFINITIONS` 命名常量。初始化按 code 查询已存在集合，只插入缺失项并 flush。重复调用不新增记录，部分初始化数据库可以补齐缺失定义；现有同 code 数据不被覆盖。

### 响应边界

在 `backend/app/schemas/challenge.py` 增加 `ChallengeProgressResponse`，固定字段：

- `challenge_id`
- `current_progress`
- `target_value`
- `is_completed`
- `status`

新增 `backend/app/services/challenge_responses.py`，提供三个无 I/O 映射函数：

- `build_user_challenges_response(records) -> UserChallengesResponse`
- `build_user_challenge_response(record) -> UserChallengeResponse`
- `build_challenge_progress_response(record) -> ChallengeProgressResponse`

Router 负责认证、Query 参数约束、调用服务、映射已知错误并返回映射结果，不再遍历 ORM 关系或拼装字典。

## HTTP 契约

成功状态和字段保持不变。错误契约如下：

| 场景 | 状态 | detail |
|---|---:|---|
| GET 不存在挑战 | 404 | `Challenge <id> not found` |
| 启动不存在挑战 | 400 | `Challenge <id> not found` |
| 重启已完成挑战 | 400 | `Challenge already completed` |
| 未启动时更新进度 | 400 | `Challenge not started` |
| API progress 为零或负数 | 422 | FastAPI Query validation |

Router 捕获精确异常，不捕获裸 `ValueError`。无效挑战定义和奖励/数据库异常不得伪装成客户端 400。

## 测试设计

### 目标与状态测试

- 默认挑战分别解析为 5、1、7。
- 重复启动进行中挑战返回同一 ID、attempts 仍为 1。
- 已完成挑战重新启动产生专属错误。
- 服务直接收到零或负进度时拒绝且状态不变。
- API 零或负 progress 返回 422。

### 奖励和幂等测试

- 首次完成后响应、用户余额、`cores_total_earned` 和一条 `CoreTransaction` 的 amount/balance/reference 一致。
- 完成后再次更新不改变余额、累计收入、completed_at 或交易数量。
- 进度未达到目标时不创建奖励交易。

### 事务测试

- 监听或 mock session，证明启动、进度和默认初始化不调用 commit。
- 在 CoreService 已写入余额与交易后制造异常，执行 rollback 后证明进度、状态、余额、累计收入和交易行都恢复。

### 响应与 Router 测试

- 纯映射函数保持当前列表、启动和进度字段。
- Router 只映射已知领域错误；未知 `ValueError` 继续传播到 500 路径。
- 现有挑战列表、详情、认证和成功路径测试继续通过。

## 验证

完成前必须取得以下新鲜证据：

1. 领域错误、目标解析、状态转换、响应映射、账本和回滚的针对性测试通过。
2. 通用挑战、智核、统计和认证相关回归测试通过。
3. 完整后端测试通过且零跳过。
4. Pyright 为 `0 errors, 0 warnings, 0 informations`。
5. FastAPI 与 Next.js 启动无编译错误；挑战列表、认证启动、进度和用户挑战列表实际请求符合契约。
6. CodeGraph 同步后，通用 ChallengeService 调用者仍局限于 challenge Router/测试；Arena 与 Mastery 模块未被修改。
7. `git diff --check` 和项目 DRY、模块化、命名、魔法值、函数长度、死代码、类型安全自检通过。

## 成功标准

- 状态转换可以从类型化错误和测试直接理解。
- 请求级事务统一拥有提交，完成状态与奖励账本可一起回滚。
- 完成奖励在余额、累计收入和账本之间一致，顺序重试不重复发放。
- 默认挑战目标与各自 requirement 字段一致。
- Router 只处理 HTTP 契约，响应组装位于纯映射模块。
- Arena、Mastery、前端、数据库模式和奖励数值保持不变。

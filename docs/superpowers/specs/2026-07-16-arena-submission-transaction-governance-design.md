# Arena 权威提交事务治理设计

## 目标

将 `/api/learning-path/challenge/submit` 的权威判题、进度更新、下一题解锁、活动记录、错题与复习计划、星级段位、智核与流水、Arena 用户画像整理为一个请求拥有的原子用例，同时保持现有成功响应字段、奖励数值、Judge0 判定和前端调用兼容。

这是后端学习型治理第 3 批 B 的第一个子批次（3B-1）。Arena 初始化、追加、导航、保存代码和查询边界进入 3B-2；Mastery 进度进入 3C。

## 当前问题

当前提交链为 Router -> `ChallengeSubmissionService` -> `ChallengePathService._submit_exercise_impl` -> `ChallengeRewardService`，存在以下问题：

1. `ChallengeSubmissionService` 依赖 legacy service 的私有方法，权威判题与持久化用例没有稳定边界。
2. 服务层直接导入并抛出 FastAPI `HTTPException`，领域失败与 HTTP 映射耦合。
3. `_submit_exercise_impl` 内部 `commit()`，随后才更新用户画像；画像因此不属于提交事务。
4. 智核发放与段位流水分别用宽泛 `except Exception` 吞掉失败，可能提交进度、星级或余额中的一部分。
5. 进度和 Arena profile 更新没有行锁；同一题或不同题并发提交可能重复奖励或丢失段位更新。
6. `ChallengeRewardService._update_profile_stats` 和 `UserProfileService._update_statistics` 重复写相同统计，首次正确会把 `current_streak` 计算一次后再加一次。
7. Router 只捕获裸 `ValueError`，未知编程错误也会伪装成客户端 400。
8. 提交响应已有 `cores_earned`，但后端 `SubmitExerciseResponse` 未包含该字段且端点未声明响应模型。
9. 现有测试证明客户端伪造结果不能获奖，但没有证明奖励失败整体回滚、服务不提交、顺序重试不重复写账本或画像只统计一次。

## 方案比较

### 方案一：只加锁并删除 legacy commit

在 `_submit_exercise_impl` 中加锁、把 `commit()` 改为 `flush()`，并停止吞奖励异常。改动较小，但权威提交服务仍依赖 legacy 私有方法，画像重复统计和 FastAPI 服务耦合仍然存在。

### 方案二：收口权威提交用例（采用）

让 `ChallengeSubmissionService` 成为提交用例入口，新增小型状态服务处理锁定进度、状态写入、活动和解锁；奖励服务只处理奖励；用户画像服务统一行为向量和统计。Router 只映射专属错误和响应模型。该方案覆盖一条完整事务链，又不扩大到选择与导航。

### 方案三：一次重写整个 Arena

同时治理 start、progress、save、switch、append、exit、submit 和所有响应。最终边界更统一，但会把选择算法、导航契约与高风险奖励事务放入同一回滚面，不适合作为可独立验证的子批次。

## 范围

本批次覆盖：

- `POST /api/learning-path/challenge/submit`。
- 后端权威判题结果到 Arena 持久化状态的编排。
- `ArenaExerciseProgress`、下一题解锁和 `ActivityLog`。
- 错题、薄弱点与复习计划的现有写入。
- Arena 星级、段位、智核、`CoreTransaction` 和 `TierTransaction`。
- `UserArenaProfile` 的行为向量与统计。
- 提交错误映射和稳定响应模型。

本批次不覆盖：

- `/challenge/infinite/start`、`progress`、`save-code`、`switch`、`append`、`exit`、`exercise/{id}` 或 `recent`。
- 选题、推荐、难度推断或追加算法。
- Judge0 HTTP 协议、轮询、语言 ID 或输出判定规则。
- 星级公式、段位阈值、保护规则、智核数值或错题去重规则。
- Mastery、ChallengeSession、前端或数据库 schema/migration。
- SQLite 对生产数据库行锁隔离级别的证明。

## 架构

### 类型化错误

新增 `backend/app/services/challenge_path/errors.py`：

- `ChallengeSubmissionError`：Arena 提交预期失败基类。
- `ChallengeExerciseNotFoundError(exercise_id)`：题目不存在。
- `ChallengeProgressNotFoundError(exercise_id)`：用户没有对应 Arena 进度。
- `UnsupportedChallengeLanguageError(language)`：Judge0 不支持该语言。
- `MissingChallengeTestCasesError(exercise_id)`：编程题没有后端测试用例。
- `JudgeUnavailableError`：判题服务不可用。

错误模块不导入 FastAPI。`submission.py` 为已有测试兼容继续重新导出 `JudgeUnavailableError`。

Router 精确保持现有状态码：

| 错误 | HTTP |
|---|---:|
| 题目不存在 | 400 |
| 进度不存在 | 400 |
| 不支持的语言 | 400 |
| 缺少后端测试用例 | 400 |
| Judge0 不可用 | 503 |

未知 `ValueError`、数据库异常、奖励异常和画像异常不映射为 400，而是进入请求级 500/回滚路径。

### 权威判题与用例编排

`ChallengeSubmissionService(db)` 不再接收 legacy service。它按以下顺序执行：

1. 查询题目；不存在时抛出专属错误。
2. 对编程题使用后端 `test_cases` 调用 `run_authoritative_judge`；客户端 `test_results` 仅为兼容输入。
3. 用严格通过规则计算本次 `is_correct`。
4. 调用状态服务锁定并更新 Arena 进度、保存代码、写活动、解锁下一题。
5. 调用奖励服务写错题/复习、星级段位、智核和两类流水。
6. 调用用户画像服务更新行为向量与完整 Arena 统计。
7. `flush()` 后返回现有字段，不提交事务。

非编程题继续使用客户端结果，以保持当前兼容行为；Arena 当前选择流程仍以编程题为主。

### 提交状态服务

新增 `backend/app/services/challenge_path/submission_state.py`：

- `ChallengeSubmissionState` dataclass：包含锁定后的 `progress` 和 `next_unlocked`。
- `ChallengeSubmissionStateService.apply_attempt(...)`：使用 `SELECT ... FOR UPDATE` 读取用户题目进度并写入本次尝试状态。

该服务保留现有持久化语义：`is_completed`/`is_correct` 表示本次权威结果，`attempt_count` 每次增加，首次与最近尝试时间、首次正确时间、语言、代码、时间与 hint 字段按现有规则更新。正确时只解锁紧邻的下一题。它不处理奖励、不提交事务。

严格通过解析从 legacy `ChallengePathService` 移到提交模块的纯函数，现有测试改为直接验证新边界。仓库中没有调用者的 `ChallengePathService.submit_exercise` 与 `_submit_exercise_impl` 一并删除；`ChallengePathService` 及其 `ArenaInfiniteService` 别名继续保留选择、进度和统计兼容委托。

### 原子奖励

`ChallengeRewardService` 保持现有奖励顺序和数值，但不再吞异常：

1. 错误答案写错题、薄弱点和复习计划。
2. 锁定或创建 `UserArenaProfile`，计算并写星级/段位。
3. 首次获得正星时通过 `CoreService.earn_cores` 发放 3 智核并写 `CoreTransaction`。
4. 星级变化时通过 `TierTransactionService.record_transaction` 写段位流水。

智核或段位流水失败会向上抛出，使进度、活动、错题、复习、星级、余额和所有流水一起回滚。业务常量使用命名常量；成功响应仍返回实际 `cores_earned`。

`ChallengeTierRewardCalculator` 查询已存在 Arena profile 时使用 `FOR UPDATE`。同一题由进度锁串行化；不同题对同一用户的星级更新由 profile 锁串行化。SQLite 测试只证明查询结构和顺序幂等，不声称生产级并发隔离。

### 顺序重试幂等

保留 `progress.stars_awarded > 0` 的既有奖励门禁：已经正确并获得星级后再次正确提交，仍记录尝试和本次权威结果，但 `stars_earned=0`、`cores_earned=0`，不新增智核或段位流水，不重复解锁。

错误尝试的重复扣星规则保持不变；改变该规则需要单独的产品语义设计。

### 用户画像单一所有权

`UserProfileService.update_after_exercise` 成为 Arena 行为向量与统计的单一更新入口：

- 保留行为 embedding 更新。
- 从 Arena 进度与题目一次重算 `total_challenges`、wins/losses、best/current streak、highest difficulty、total submissions、accuracy 和平均用时。
- 删除奖励服务中的重复 `_update_profile_stats`。
- 使用 `flush()`，不 `commit()`。

这修复首次正确后 `current_streak` 从 1 被重复加到 2 的问题，并使画像失败参与整个请求回滚。

### HTTP 响应边界

`SubmitExerciseResponse` 增加当前已返回但未建模的 `cores_earned: int`，提交端点声明 `response_model=SubmitExerciseResponse`。返回字段保持：

- `is_correct`
- `test_results`
- `stars_earned`
- `cores_earned`
- `next_unlocked`
- `added_to_wrong_book`
- `tier_changed`
- `new_tier`、`new_sub_tier`、`new_stars`
- `promoted`、`demoted`
- `first_time_correct`、`first_time_wrong`

## 事务所有权

`ChallengeSubmissionService`、状态服务、奖励服务、tier calculator、`CoreService`、`TierTransactionService`、错题服务和 `UserProfileService.update_after_exercise` 都只 add/flush。FastAPI `get_db` 在响应成功后提交，任何异常时统一回滚。服务级测试显式调用 commit/rollback。

本批不修改 `ChallengeProgressService` 与 `ChallengeSelectionService` 中其他端点使用的 commit；它们进入 3B-2。

## 测试设计

### 错误与 Router

- 题目不存在、进度不存在、不支持语言、缺少测试用例和 Judge0 不可用产生专属错误。
- Router 精确映射 400/503。
- 未知 `ValueError` 不再被提交端点转换为 400。
- 服务模块不导入 FastAPI。

### 状态与事务

- 状态查询包含 `FOR UPDATE`，提交服务不调用 `commit()`。
- 正确提交更新进度、活动和下一题解锁；错误提交保留现有结果语义。
- 智核或段位流水在写入后制造异常，rollback 后进度、下一题、活动、错题、复习、profile、余额和流水全部恢复。

### 奖励与重试

- 首次正确写一次星级变化、3 智核、一条 `CoreTransaction` 和一条需要时的 `TierTransaction`。
- 顺序重复正确返回零新增奖励，不改变余额或交易数量。
- 奖励异常不返回伪成功或零奖励成功。

### 用户画像

- `update_after_exercise` 不提交。
- 首次正确后的 `current_streak` 为 1，不是 2。
- 完整统计与行为 embedding 在同一事务更新；异常回滚。

### 回归

- 现有 authoritative submission、learning path challenge、Arena result、tier、core、wrong question、user profile 和前端成功字段契约继续通过。

## 验证

完成前必须取得：

1. 每项生产行为先红后绿的聚焦测试证据。
2. Arena 提交、Judge0、智核、段位、画像、错题与学习路径邻接测试通过。
3. 完整后端测试零跳过，Pyright 零错误。
4. FastAPI 与 Next.js 实际启动，前端 `/` 编译并返回 200。
5. 注册用户后，提交错误场景的 400/503 契约和挑战查询路由实际请求通过。
6. 工作树 CodeGraph 同步后，提交调用链为 Router -> Submission -> State/Reward/Profile；legacy 私有提交边消失。
7. `git diff --check` 与 DRY、模块化、命名、魔法值、函数长度、死代码和类型安全检查通过。

## 成功标准

- 一次 Arena 提交只有一个明确的事务所有者。
- 任一奖励、流水或画像写入失败时，不留下部分持久化状态。
- 服务错误与 FastAPI 解耦，Router 只映射已知失败。
- 顺序重复正确提交不重复发星、智核或流水。
- Arena 画像统计只计算一次且行为向量不脱离主事务。
- 成功响应、奖励数值、Judge0 权威性、前端和数据库模式保持兼容。

## 残余风险与后续批次

- SQLite 不提供与 PostgreSQL 等价的 `FOR UPDATE` 证明；生产并发隔离需在目标数据库验证。
- Arena profile 并发首次创建依赖现有 `user_id` 唯一约束；本批不增加迁移。
- 选择、导航和保存代码服务仍有内部 commit 与裸 `ValueError`，由 3B-2 治理。
- Mastery 的进度、奖励与画像边界由 3C 治理。

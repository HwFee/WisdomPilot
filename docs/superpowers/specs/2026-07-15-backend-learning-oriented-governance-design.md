# 后端学习型治理设计

## 目标

将 FastAPI 后端逐步整理为可阅读、可测试、可演进的学习范例，同时修复有明确证据的工程缺陷。治理过程不进行全库重写，不改变已验证的业务规则或数据库语义。

本设计优先保证：

1. 每个模块的职责和依赖方向可以从目录、类型和测试中直接识别。
2. HTTP 层、业务编排、外部 I/O 和持久化逻辑不相互混杂。
3. 已公开 API 的成功响应保持兼容；必要的错误行为修复通过测试和文档明确说明。
4. 每个批次均可独立验证和回退。

## 范围

本次覆盖 `backend/app` 下的路由、服务、核心配置、依赖工具和相关测试。

本次不覆盖：

1. 前端代码或前后端视觉设计。
2. 无关的功能扩展、表结构重设计或大规模数据迁移。
3. 没有行为证据的主观风格改动。

## 分层约定

### Router

Router 只负责请求模型、认证和数据库依赖注入、调用应用服务、响应模型构造，以及将已知领域异常映射为 HTTP 状态码。Router 不负责 SQL 查询、外部 HTTP 请求、重试轮询或跨实体业务流程。

### Service

Service 负责一个可命名的业务用例，例如“提交代码执行”或“开始挑战”。它协调模型、仓储式查询和外部客户端，并用明确的领域异常或类型化结果表达失败。

Service 不依赖 FastAPI 的 `Request`、`HTTPException` 或路由对象。数据库会话的提交和回滚遵循现有请求级事务约定；只有存在明确独立事务需求时才新增提交点。

### External Client

外部服务集成封装在专用客户端中，负责 HTTP 请求、序列化、超时、重试或轮询、响应解码和连接关闭。外部协议细节不得泄漏到业务服务。

### Model And Schema

SQLAlchemy 模型表示持久化状态，Pydantic schema 表示 API 契约。禁止使用无约束的 `dict` 在层之间表达稳定的业务数据；动态外部响应可先在客户端边界转换为命名类型。

## 缺陷修复准则

允许修复下列明确缺陷：

1. 未验证或错误验证的外部输入。
2. 外部 HTTP 客户端、文件或异步资源未关闭。
3. 错误状态、异常映射或响应模型与实际行为不一致。
4. 事务原子性、授权边界、超时或重试导致的可证明错误。
5. 现有测试可复现的错误，或能先以回归测试精确复现的错误。

每项修复必须先增加或调整测试以描述预期行为。若修复会改变公开 API 的错误状态码、响应字段或持久化结果，必须在对应模块文档中记录旧行为、修复理由和新契约。

## 批次与顺序

### 1. 代码执行与 Judge0 集成

拆分外部 Judge0 协议客户端、执行编排和结果判定。目前该区域混合了 base64 编解码、轮询、状态转换、结果格式化与业务判断，是建立清晰边界和资源生命周期范例的最佳起点。

### 2. 认证与权限

统一认证服务的失败语义、管理员依赖和路由异常映射，避免裸 `ValueError` 或重复的权限判断扩散。

### 3. 挑战与学习进度

将挑战状态转换、进度更新、奖励和响应组装分别放入合适边界，保证事务一致性和幂等性可由测试理解。

### 4. AI、配额与缓存

明确 AI 提供者调用、配额消耗、缓存命中和失败回退的职责，隔离配置与外部依赖。

### 5. 常规业务模块

依次治理课程、章节、练习、笔记、收藏、统计、排行榜和成就模块，推广已经验证的模式，不人为制造新的抽象层。

### 6. 共用基础设施收口

最后只提取已经在多个批次中稳定重复的依赖、异常、常量和数据库工具，避免过早泛化。

## 每批次工作流

1. 用 CodeGraph 确认调用者、被调用者、影响范围和覆盖测试。
2. 阅读完整调用链，列出职责混杂、重复逻辑、隐式契约和可复现缺陷。
3. 先添加失败测试或强化现有契约测试。
4. 做最小重构，保持依赖单向：Router 到 Service，Service 到 Model、Client 或基础设施。
5. 为复杂决策补充简短注释和模块级说明，解释原因而非复述语句。
6. 运行针对性测试、完整后端测试、Pyright、FastAPI 启动和受影响路由请求。
7. 在批次记录中说明重构前问题、最终边界、修复的缺陷和验证证据。

## 质量门槛

每次代码修改必须满足：

1. 没有未使用导入、死代码、循环依赖或重复的业务编排。
2. 标识符表达业务意图；避免含义不明的缩写和魔法业务值。
3. 单个函数原则上不超过约 40 个有效代码行；若业务流程天然较长，应按明确步骤拆分，而非机械拆函数。
4. 新增或调整的 API、异常和事务路径有相应测试。
5. `pytest`、`pyright`、服务启动和受影响 HTTP 路由验证均通过。

## 风险控制

不在同一批次同时改变数据库模式和业务逻辑。外部服务调用的超时、重试、轮询和失败映射采用契约测试与模拟 HTTP 响应验证，避免依赖线上服务。每次只迁移一条完整调用链，确认无回归后再推广模式。

## 成功标准

完成后，学习者可以从路由入口沿着类型化调用链定位业务用例，理解外部依赖和数据库副作用的边界，并通过测试看到错误行为与正确行为的工程证据。所有已覆盖行为保持通过，已修复缺陷具有回归测试。

## Judge0 首批实施记录

- 重构前：`Judge0Service` 同时处理 HTTP 协议、base64 编解码、轮询、结果判定和 API 格式化；路由创建的实例没有请求结束清理保证。
- 重构后：`Judge0Client` 负责外部协议和资源生命周期，`Judge0Service` 负责执行语义和结果聚合，Router 只处理 HTTP 契约。
- 修复：异步生成器依赖在每次代码执行请求结束时调用 `Judge0Service.close()`；注入的测试 HTTP 客户端不会被客户端关闭。
- 证明：客户端模拟 HTTP 测试、服务聚合测试、路由契约测试、挑战权威判题回归测试、完整后端测试、Pyright 和服务启动检查均通过。

## Judge0 审查修复记录

- 空批量 token 响应现在返回空结果，由服务层统一转换为 Judge0 不可用错误，不再因 `asyncio.wait([])` 泄漏为 HTTP 500。
- 批量请求不向 Judge0 发送 `expected_output`，继续由服务层执行去除首尾空白后的兼容比较。
- 全后端 Pyright 基线和 Judge0 第一批重构拆分提交，后续模块仍按治理设计中的批次顺序推进。

## 认证与权限第二批实施记录

- 重构前：认证服务用裸 `ValueError` 表达四种失败；忘记密码依靠 Router 吞异常防枚举；必需与可选认证重复解析令牌和查询用户；管理员端点存在三种门禁写法。
- 重构后：认证专属异常表达服务失败，Router 只映射已知 HTTP 契约；共享解析器统一用户加载，活跃用户兼容依赖不再重复检查；端点级管理员权限统一进入 `get_current_admin_user`。
- 保留：注册、登录、忘记密码、JWT、数据库以及管理员业务成功行为不变；题解的作者或管理员规则继续留在对象级业务授权中。
- 证明：认证服务、Router、依赖、管理员消费者回归测试、609 项完整后端测试、Pyright、FastAPI 与 Next.js 启动、真实路由请求和 CodeGraph 影响检查均通过。

## 通用挑战状态与奖励第三批 A 实施记录

- 重构前：通用 `ChallengeService` 内部提交事务、用裸 `ValueError` 表达状态失败、直接修改智核余额且不写账本，Router 手工拼装响应。
- 重构后：类型化错误描述状态机，目标按 `ChallengeType` 解析，行锁更新已存在进度，请求依赖统一提交，`CoreService` 在同一事务写余额、累计收入和账本，纯映射模块构造响应。
- 幂等边界：重复开始进行中挑战返回同一记录；完成后的顺序重试不改变完成时间或重复发奖励。并发首次启动唯一性明确留给独立数据库迁移批次。
- 证明：目标、状态、回滚、账本、映射和 API 契约测试通过；636 项完整后端测试零跳过，Pyright 零错误，FastAPI 与 Next.js 启动、真实路由和工作树 CodeGraph 影响检查均通过。

## Arena 提交事务治理第三批 B-1 实施记录

- 重构前：Arena 提交同时存在新旧两条状态修改路径；Service 泄漏 HTTP 语义，奖励账本异常可被吞掉，状态、奖励和画像内部提交点会破坏请求级回滚，奖励与画像还重复统计同一份进度。
- 重构后：Router 只校验响应并映射五种类型化提交错误；`ChallengeSubmissionService` 依次协调后端权威判题、加锁状态更新、原子奖励和画像重算；状态、奖励、账本和画像只 `flush`，由请求数据库依赖统一提交或回滚。旧 `_submit_exercise_impl` 与旧提交代理已经移除。
- 原子性与幂等边界：当前及下一进度行和 Arena 画像按需加锁；智核、星级、段位账本失败向上传播；顺序重复答对不重复写奖励账本。画像统计只有一个所有者；除 `total_submissions` 汇总所有行的 `attempt_count` 外，挑战数、胜负、准确率、平均用时、最高难度与连续答题都只按 `attempt_count > 0` 的有序记录计算，因此未来未作答行不稀释统计或截断连续答对，已作答错误行仍计为失败并截断连续答对。
- 契约与范围：提交成功响应由 `SubmitExerciseResponse` 强制校验并包含 `cores_earned`；缺题精确返回 `400` 和 `Exercise 99999 not found`。Judge0 传输边界保留一处既有 `except Exception`，只用于转换为 `JudgeUnavailableError`。未修改前端、数据库模式、迁移、Mastery、ChallengeSession、选择、进度或导航行为。
- 证明：各任务先红后绿，聚焦门槛为 152 项通过；Task 6 预审完整后端为 649 项通过，最终审查修正画像混合统计总体并补充错误单次尝试、未来未作答行和画像失败后的完整回滚证明后，最终完整后端为 651 项通过且零跳过，Pyright 零诊断。最终提交上的 FastAPI、Next.js 编译和五个真实 HTTP 契约再次通过；CodeGraph 证明 Router -> Submission -> State/Reward/Profile 单向链路并确认旧实现无结果，最终复审无剩余发现并判定可合并。
- 剩余风险：SQLite 能证明编排、账本数量和回滚结果，但不能模拟生产数据库的 `SELECT ... FOR UPDATE` 竞争；应在生产方言集成门槛中补充并发验证。3B-2 应继续治理非提交挑战路径及其宽泛异常映射，不应顺带重开本批次已稳定的提交事务边界。

## Arena 生命周期与事务治理第三批 B-2 实施记录

- 重构前：非提交 Arena 路由分别调用选择或进度服务；追加和保存代码在 Service 内部提交，开始和按需附题由请求事务持有并分配或 `flush`，但这些写路径缺少共享的 User 所有者锁串行化边界；宽泛 `ValueError` 映射会掩盖未知错误，旧 `arena_infinite.py` facade 还保留一条重复入口。
- 重构后：类型化领域错误保持 Service 与 FastAPI 解耦；`ChallengePathLifecycleService` 统一开始、追加、保存、退出和按需附题的锁与写入编排，只 `flush`，由请求数据库依赖提交或回滚；选择服务只做纯选择，进度服务负责读取和导航，八个非提交路由声明显式响应模型，旧 facade 已删除。
- 原子性与兼容边界：开始和追加先锁用户结构所有者，保存代码锁目标进度行，按需附题采用所有者锁下的二次检查；顺序重复开始复用同一路径，追加索引与首题解锁规则、推荐顺序、三级 fallback、候选规模和抽样行为保持不变。`GET /challenge/exercise/{id}` 为兼容现有客户端仍可能附加进度行，是待后续改成显式命令的 mutating-GET 债务。
- 范围与必要偏差：未修改提交、画像、前端、数据库模式、迁移、Mastery 或 `ChallengeSession`。`rewards.py` 只把进度读取从私有名改为公开名，没有改变奖励行为或公式；共享测试数据库依赖改为与生产一致的成功提交、异常回滚并重新抛出，使 flush 后响应失败的回滚证明真实生效。Tasks 2-4 对兼容 facade 的最小更新在 Task 5 删除 facade 后不再存在。
- Task 6 历史检查点：Tasks 1-5 均有先红后绿证据；当时完整后端为 `674 passed in 104.28s` 且 `-rs` 没有 skipped 段，Pyright 为 `0 errors, 0 warnings, 0 informations`。空 SQLite 上八个响应模型路由、FastAPI 健康检查、注册、Next.js `/` 与 `/arena` 编译请求均通过；CodeGraph 证明 Router -> Lifecycle -> Selection/Progress 单向写链路、读取路由直达 Progress，旧 facade 查询无结果。
- 最终审查修正后的最新门槛：`test: close arena lifecycle review coverage` 提交增加 4 个聚焦测试、其中 1 个参数化为两种边界，共 5 个确定性 characterization cases，覆盖推荐 ID 输出顺序、推断查询 `LIMIT 100`、三级 fallback 与 `count * 2` 候选上限，以及 `random.sample` 分别受剩余请求数和候选池规模约束的两侧边界。最新完整后端为 `679 passed in 103.67s` 且 `-rs` 没有 skipped 段，Pyright 仍为 `0 errors, 0 warnings, 0 informations`。
- 实时契约明细：`GET /health` -> 200 `{"status":"healthy"}`；注册 -> 201 且 bearer token 存在；start -> 400 `{"detail":"Not enough verified exercises available (found 0, need 1)"}`；save-code 与 exit -> 404 `{"detail":"Progress record for exercise 99999 not found"}`；switch -> 400 `{"detail":"Invalid exercise index"}`；detail/99999 -> 404 `{"detail":"Exercise not found in challenge path"}`；progress -> 200 `{"total_exercises":0,"exercises":[],"correct_count":0,"completed_count":0,"total_stars_earned":0,"current_index":0}`；recent -> 200 `[]`；append -> 200 `{"new_exercise_ids":[],"count":0}`。Next.js `/` 在 3.5 秒编译 1592 modules 后返回 200/13597 bytes，`/arena` 在 4.3 秒编译 2791 modules 后返回 200/47920 bytes，frontend stderr 为空，后端没有 `ResponseValidationError`。
- CodeGraph 明细：Task 6 历史检查点中，`init` 报告已初始化，`sync` 同步 1 个仅空白字符变化的 Router 文件、67 nodes，impact 为 Lifecycle 25、Selection 20、Progress 39。最终审查修正后，`sync` 索引 1 个变更测试文件、42 nodes，Selection impact 更新为 24，并包含全部 4 个新增测试函数。start/save/append/exit 与 mutating detail GET 进入 Lifecycle，Lifecycle 再调用 Selection/Progress；progress/recent 与只读 switch POST 直达 Progress，没有写路由绕过 Lifecycle；`ChallengePathService` 与 `get_arena_infinite_service` 均为 `No results found`。
- Rule 10 明细：共享进度行创建、响应映射和 append 推荐/fallback 各有单一所有者；依赖保持 Router -> Lifecycle -> Selection/Progress 单向且 Service 不依赖 FastAPI；新增命名明确，append 窗口、候选倍数、难度边界和 100 行样本使用命名常量；新增 lifecycle/append helper 保持单一职责，较长的既有初始选择树未扩张并委托聚焦 helper；CodeGraph 与精确搜索确认 facade 和陈旧调用不存在；全量类型与运行门槛通过。
- Task 6 与类型偏差：第一次 `git diff --check dd50e05..HEAD` 暴露六个 CRLF 空行，单独的 `33a3db6`（`style: clean arena router whitespace`）只替换行尾且 `--ignore-space-at-eol` 无语义差异，修复后范围 diff check 为 0。Python 3.10 每次订阅 `list[RecentArenaExercise]` 都产生新的 `GenericAlias`，因此 Task 5 对 recent 路由模型使用相等性而非同一性断言，具体 Pydantic 模型仍使用同一性。
- 进程与产物清理：检查命令行后只停止已验证的 FastAPI PID 34640/42424 与 Next PID 39404/38056/32432 进程树，端口 18176/13176 最终 listener 均为 0；已证明位于工作树内的 `.tmp-task6-live` SQLite/WAL/SHM 与日志目录已移除。预先存在的 `frontend/.next` 保留，`frontend/node_modules` 仍是指向主检出 `C:\Users\17445\Desktop\WisdomPilot\frontend\node_modules` 的 Junction。
- 审查与剩余风险：Tasks 1、2、4、5 审查无发现；Task 3 当时获批但保留的推荐顺序、fallback 升级和 100 行抽样规模覆盖 Minor，已经由 `test: close arena lifecycle review coverage` 提交的 5 个确定性 characterization cases 关闭，不再是未决项。Task 6 提交文档前的全批次只读复审没有该历史 Minor 之外的新发现。仍未解决的风险只有既有兼容与集成边界：detail 路由继续是 mutating GET；SQLite 能证明锁语句结构、编排和回滚结果，但不能模拟生产数据库 `SELECT ... FOR UPDATE` 的真实竞争，仍需生产方言并发集成测试。

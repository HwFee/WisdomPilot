# 认证与权限治理设计

## 目标

在不改变认证成功响应、令牌格式、数据库结构或管理员业务逻辑的前提下，建立一条可阅读、可测试的认证与授权边界：认证服务使用专属异常表达失败，FastAPI Router 负责 HTTP 映射，认证依赖统一负责令牌解析、用户加载、账户状态和管理员权限。

本批次是后端学习型治理的第二批，承接 Judge0 批次已经验证的分层原则。

## 当前问题

当前实现存在四类边界问题：

1. `AuthService` 使用裸 `ValueError` 同时表达邮箱冲突、用户名冲突、无效凭据和停用账户。Router 只能根据调用位置笼统映射 HTTP 状态，异常类型没有记录失败语义。
2. `forgot_password` 的注释声称不存在的邮箱不会抛错，实际却抛出 `ValueError`，Router 再静默吞掉。防用户枚举的安全语义没有在服务接口本身成立。
3. `get_current_user` 和 `get_optional_user` 重复令牌解码与用户查询；`get_current_user` 已拒绝停用账户，`get_current_active_user` 又做一次不可到达的重复检查。
4. `routers/admin.py` 自定义 `require_admin`，`POST /api/courses/init` 在端点体内直接检查 `is_admin`，其他 AI、课程、练习和题解管理员入口使用 `get_current_admin_user`。三种写法让端点级管理员门禁没有唯一边界。

## 范围

本批次覆盖：

- 注册、登录、忘记密码和 `/api/auth/me` 的认证失败语义。
- 必需用户、可选用户、活跃用户兼容依赖和管理员依赖。
- `routers/admin.py` 中六个端点向统一管理员依赖迁移。
- `POST /api/courses/init` 从端点体内权限判断迁移到统一管理员依赖。
- 已经使用统一管理员依赖的 AI、课程、练习和题解入口的回归验证。

本批次不覆盖：

- JWT 算法、令牌载荷、过期时间或密码哈希策略变更。
- 真正发送密码重置邮件、增加重置令牌或新增 API。
- 管理员用户 CRUD、配额、AI 配置或课程业务逻辑重构。
- 数据库模式、迁移、前端代码和公开成功响应变更。
- 全局领域异常框架或全局 FastAPI 异常中间件。

## 方案比较

### 方案一：认证专属异常与统一依赖链（采用）

为认证用例定义小型、专属异常类型，由 `AuthService` 抛出，认证 Router 显式映射。认证依赖共享一个内部令牌解析与用户查找函数，保留现有公开依赖名作为兼容入口；所有管理员端点使用唯一的 `get_current_admin_user`。

该方案直接修复当前证据指向的问题，改动范围可由认证和管理员契约测试完整覆盖，不要求其他业务模块采用新框架。

### 方案二：类型化结果对象

让注册和登录返回成功或失败的联合结果，Router 根据结果类型映射 HTTP。该方案避免异常控制流，但会改变现有服务签名，在 Python 调用方中引入较多分支和样板代码，对只有一个调用方的认证服务收益有限。

### 方案三：全局领域异常与中间件

建立跨模块异常层并由全局 FastAPI handler 统一映射。长期可能减少 Router 重复，但当前只有认证批次证明了这类需求；提前推广会扩大影响面，并把模块专属错误与全局基础设施耦合。本批次不采用。

## 架构

### 认证异常

新增 `backend/app/services/auth_errors.py`，只包含以下认证专属异常：

- `AuthError`：认证服务异常基类，不直接由业务代码抛出。
- `EmailAlreadyRegisteredError`：邮箱已存在。
- `UsernameAlreadyRegisteredError`：用户名已存在。
- `InvalidCredentialsError`：用户不存在或密码错误，二者继续使用相同公开文案。
- `InactiveAccountError`：凭据正确但账户已停用。

异常类携带稳定的默认消息。它们不导入 FastAPI，也不包含 HTTP 状态码。异常类型表达领域语义，Router 决定传输层映射。

### 认证服务

`AuthService.register` 和 `AuthService.login` 的参数及成功返回值保持不变：

```python
async def register(self, user_data: UserCreate) -> tuple[User, Token]
async def login(self, login_data: UserLogin) -> tuple[User, Token]
```

注册分别抛出邮箱和用户名冲突异常。登录分别抛出无效凭据和停用账户异常。服务不捕获这些异常，也不构造 `HTTPException`。

`AuthService.forgot_password(email) -> None` 对存在和不存在的邮箱都正常返回。当前批次没有邮件提供者，因此存在用户时也只保留查询这一占位行为；不存在用户不再依靠 Router 吞异常实现防枚举。

移除注册时记录密码长度和 UTF-8 字节长度的调试日志。认证模块不记录密码派生信息，即使该信息不是密码明文。

### 认证 Router

Router 显式捕获它能够映射的认证异常：

| 服务失败 | HTTP 状态 | `detail` |
|---|---:|---|
| 邮箱已注册 | 400 | `该邮箱已被注册` |
| 用户名已使用 | 400 | `该用户名已被使用` |
| 用户名或密码错误 | 401 | `用户名或密码错误` |
| 登录账户停用 | 401 | `Account is inactive` |

这张表保留当前注册和登录公开失败契约。Router 不再捕获裸 `ValueError`。忘记密码 Router 无需 `try/except`，无论邮箱是否存在都返回现有统一 200 消息。

### 用户依赖链

`backend/app/utils/deps.py` 保持 FastAPI 传输层职责，并引入一个私有异步查询函数：它接收可选 bearer credentials 和数据库会话，解码令牌、读取 `sub`、查询用户，返回 `User | None`。必需和可选认证依赖共享该函数，消除协议解析与查询重复。

公开依赖行为如下：

- `get_current_user`：无效令牌、缺少 `sub` 或用户不存在时返回现有 `401` 和 `WWW-Authenticate: Bearer`；停用账户返回现有 `403 / User account is inactive`。
- `get_optional_user`：没有凭据、无效凭据、用户不存在或账户停用时返回 `None`。
- `get_current_active_user`：保留为广泛使用的兼容依赖，直接返回已由 `get_current_user` 验证的用户，不再重复不可到达的活跃检查。
- `get_current_admin_user`：依赖活跃用户兼容入口，非管理员统一返回 `403 / Admin access required`。
- `get_quota_user`：保持现有签名与行为，本批次不改变配额语义。

命名常量保存凭据无效、账户停用和管理员权限不足的公开文本，避免同一权限规则再次产生不同魔法字符串。

### 管理员入口

删除 `backend/app/routers/admin.py` 的本地 `require_admin`。该文件中的用户列表、删除、在线用户和三个配额端点统一依赖 `get_current_admin_user`。管理员业务服务、查询、分页、异常映射和响应保持不变。

`POST /api/courses/init` 改用管理员依赖并删除函数体内的重复检查。其他 AI、课程调试、练习和题解置顶管理员入口已经依赖 `get_current_admin_user`，不做机械重写，只通过影响检查和相关测试确认统一依赖没有破坏其契约。

题解创建时的“只有管理员可发布公告”和题解修改时的“作者或管理员”属于对象级业务授权，而不是整个端点的管理员门禁。本批次保留这些 `is_admin` 判断，避免把普通作者合法路径错误收紧为管理员专用。

## 数据流

注册或登录请求按以下方向流动：

```text
HTTP request -> auth Router -> AuthService -> User / security utilities
                    |              |
                    |              +-> typed auth error
                    +-> HTTP status and response detail
```

受保护请求按以下方向流动：

```text
Bearer credentials -> shared resolver -> active user -> optional admin check -> endpoint
```

Service 不依赖 FastAPI；权限依赖不进入认证服务；Router 不查询用户或验证密码。

## 错误处理与安全约束

1. 用户不存在和密码错误继续产生完全相同的登录响应，避免通过登录接口枚举账号。
2. 忘记密码对存在和不存在邮箱产生相同状态码和响应体，且服务调用本身不再通过异常暴露存在性。
3. 无效 JWT、缺少 `sub` 和已删除用户使用相同凭据无效响应。
4. 停用账户不能通过必需、活跃、管理员或可选认证依赖进入端点。
5. 管理员拒绝文本统一为 `Admin access required`。这是唯一主动收口的公开错误文本变化；状态码保持 403，现有测试和前端没有依赖旧文本。
6. 未预期的数据库、JWT 工具或密码哈希错误不伪装成认证失败，由现有应用错误处理记录和返回。

## 测试设计

### 服务级测试

新增 `backend/tests/test_auth_service.py`，直接证明：

- 重复邮箱和重复用户名产生各自的专属异常。
- 不存在用户和错误密码都产生 `InvalidCredentialsError`。
- 停用账户产生 `InactiveAccountError`。
- 忘记密码对不存在邮箱正常返回。

### API 契约测试

扩充 `backend/tests/test_auth.py`，保留已有成功、冲突、无效凭据和防枚举测试，并增加：

- 停用账户登录仍返回 401 和现有文本。
- 停用用户令牌访问 `/api/auth/me` 返回 403 和稳定文本。
- 必需认证错误继续包含 bearer challenge header。

扩充 `backend/tests/test_admin.py`，证明本地管理员依赖移除后：

- 普通用户访问代表性管理员端点返回统一的 403 文本。
- 管理员仍能访问用户管理端点。
- 停用管理员不能进入管理员端点。

扩充 `backend/tests/test_courses.py`，证明普通用户调用 `/api/courses/init` 得到统一 403 文本，管理员仍可执行初始化。

### 影响回归

运行认证、管理员、AI、配额、课程、练习和题解相关测试，覆盖所有 `get_current_admin_user` 调用模块；随后运行完整后端测试与 Pyright。

## 验证

本批次完成前必须取得以下新鲜证据：

1. 认证服务、认证 API、管理员及所有管理员依赖消费者的针对性测试通过。
2. 完整后端测试通过且零跳过。
3. Pyright 为 `0 errors, 0 warnings, 0 informations`。
4. FastAPI 启动无错误；`/health` 返回 200；未认证 `/api/auth/me` 和 `/api/admin/users` 返回 401。
5. 使用真实测试用户令牌请求 `/api/auth/me` 返回 200，普通用户请求 `/api/admin/users` 返回统一 403 文本。
6. CodeGraph 同步完成；影响检查显示管理员入口只使用统一依赖，认证服务异常没有泄漏到非认证 Router。
7. `git diff --check` 和项目代码质量自检通过。

## 成功标准

- 从认证 Router 可以沿类型化调用链理解每一种已知失败，不再依靠裸 `ValueError` 猜测语义。
- 防用户枚举是 `forgot_password` 服务接口的直接契约，而不是 Router 的异常吞噬技巧。
- 令牌解析和用户查询只有一份实现，活跃检查没有重复不可达分支。
- 所有管理员端点使用一个权限依赖和一个拒绝契约。
- 认证成功响应、JWT、数据库、前端和管理员业务行为均保持兼容。

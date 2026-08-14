# WisdomPilot 安全与性能审计报告

> 审计日期：2026-08-13
> 审计方法：Cloudflare security-audit skill（六阶段流程）+ addyosmani web-performance-audit skill（静态源码分析）
> 审计范围：`backend/`（FastAPI + SQLAlchemy 2.0 async + SQLite WAL）、`frontend/`（Next.js 15.5 + React 19）
> 分支：`audit/security-performance-review`

---

## 一、审计结论摘要

本次审计由 3 个安全狩猎 agent（注入类 / 访问控制与认证 / 业务逻辑与 AI 滥用）+ 2 个性能审查 agent（前端 / 后端）并行执行，随后由主会话对全部发现逐一验证（Phase 3 对抗验证）。

### 修复清单（全部已修复并验证）

| # | 严重度 | 类别 | 问题 | 修复 |
|---|--------|------|------|------|
| S1 | **CRITICAL** | 认证 | 弱 `SECRET_KEY`（`a1b2c3...` 可猜测模式）→ 攻击者可伪造任意用户 JWT | 已轮换为随机密钥；`config.py` 启动校验拒绝已知弱密钥；`start_services.py` 自动检测并轮换弱密钥 |
| S3 | **HIGH** | 业务逻辑 | 竞技场同一挑战可无限重放刷积分/经验；三连胜奖励 `>= 3` 导致每胜触发 | 已攻克不重复发奖；连胜奖励改为 3 的倍数时发放一次；partial unique index（user_id+challenge_id WHERE solved=1）数据库层兜底并发 TOCTOU |
| S2 | **HIGH** | 业务逻辑 | 认证考试可无限重考刷智核/经验/证书（冷却期仅展示不校验） | `submit_certification` 强制 3 天冷却（429）+ 定级测试每用户仅一次 + 判分后二次复检收窄并发窗口 |
| S4 | **MEDIUM** | 经济/资源 | `/api/tutor/feynman/check` 无余额校验 → 0 余额仍触发 LLM 调用并写掌握度事件 | 余额不足直接 402，不调 LLM、不写事件 |
| S5 | **MEDIUM** | 认证 | 登录时序侧信道：邮箱不存在时跳过 bcrypt（~390ms vs 几 ms）→ 可枚举注册邮箱 | 用户不存在时执行 dummy bcrypt 验证抹平时序 |
| S6 | **MEDIUM** | 认证 | 邮箱本地部分大小写敏感 → 可注册 `Boss@x.com` 与 `boss@x.com` 双账户造成身份混淆 | 注册/登录统一本地部分小写规范化 |
| S7 | **LOW** | 认证 | bcrypt 72 字节静默截断（多字节字符被切断、长密码虚假安全感） | 注册时拒绝超 72 字节密码 |
| P1 | **HIGH** | 性能 | `DeckHeader` 在每个页面拉取重量级 `/api/dashboard` 聚合（仅用 2 个字段）；dashboard 页重复请求 | 头部改走轻量 `/api/auth/me`（响应新增 `cores` 字段） |
| P2 | **HIGH** | 性能 | deck API 客户端无超时、无 in-flight 去重；POST 去重键不含 body 有张冠李戴风险 | `apiFetch` 增加超时（默认 30s，导师 LLM 端点 300s）+ 仅 GET 去重；mock 延迟仅 dev 模式 |
| P3 | **CRITICAL** | 性能 | 高频查询缺复合索引 → 事件表随数据增长全表扫描+临时排序 | 7 个复合索引（mastery/attempts/transactions/feed/rating），`migrate_add_indexes.py` 已应用 |
| P4 | **MEDIUM** | 性能 | TutorClient `setTimeout` 无清理 + 请求失败无 catch → 卸载后 setState、失败卡死 | timer 存 ref 卸载清理；失败恢复输入并提示 |

### 已知残留风险（未修复，记录在案）

- **认证冷却存在毫秒级 TOCTOU 残留**：判分后发奖前已二次复检，但两检查之间仍有毫秒级窗口（无可用唯一约束兜底——DeckCertification 允许同主题重复认证）。彻底堵死需引入认证尝试表，见后续建议。竞技场侧已用 partial unique index 从数据库层根治。
- **JWT 存 localStorage**（无 httpOnly Cookie）：任何 XSS 可窃取令牌。审计未发现可利用 XSS（全部 UGC 走 React 文本节点），属防御纵深缺口。
- **限流仅覆盖 `/api/auth/*`**：训练端点无速率限制，内存限流器单实例有效。
- **费曼会话内存存储**：进程内字典，无 TTL，多 worker 部署失效（代码注释已声明生产应换 Redis）。
- **Judge0 禁用时的关键字匹配判题可被构造答案绕过**：属降级模式的设计权衡（Judge0 未配置时无真实执行），接入 Judge0 后自然消除。
- **历史数据迁移注意**：邮箱规范化（S6）生效前注册的混合大小写邮箱账户将无法登录（登录查库用小写值）。本项目尚未上线、无真实用户，可接受；若曾上线需在迁移时先统一存量邮箱小写。

---

## 二、安全审计详情（Phase 3 已验证发现）

### S1 CRITICAL — 弱 SECRET_KEY 导致 JWT 伪造

**文件**：`backend/.env:7`、`backend/app/config.py`

部署中的 `SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0` 是可猜测的顺次模式。HS256 对称签名下，猜测该密钥即可伪造任意用户（`sub`=UUID）的令牌，完全接管账户。`config.py` 仅校验长度 ≥32，`start_services.py` 仅当长度不足才重新生成——弱密钥永不轮换。

**修复**：
1. 轮换为 `secrets.token_hex(32)` 随机值（已执行）
2. `config.py` 校验器拒绝已知弱密钥/占位模式，启动即失败
3. `start_services.py` 检测到弱密钥时**原地替换** SECRET_KEY 行（保留其他配置）

### S2 HIGH — 认证考试无限重考

**文件**：`backend/app/training/router.py:1800-1932`

3 天冷却期只在 `dashboard`/`certification/home` 响应中**展示**，`submit_certification` 端点不校验。同一场考试可无限重放：每次 +20 智核、+40 implement 经验、生成新证书。定级测试同理可重放：每次向全部 13 个知识点写 `placement` 事件并覆盖三轴经验。

**修复**：提交前强制校验——普通试卷冷却期内返回 429；`placement` 每用户仅一次（400）。

### S3 HIGH — 竞技场重放刷分

**文件**：`backend/app/training/router.py:1394-1465`

`solved` 无幂等检查：同一挑战反复提交每次 +23 积分、+23 debug 经验；`win_streak >= 3` 导致 3 连胜后**每次**获胜都 +10 智核。

**修复**：查询该挑战是否已被本用户攻克（`solved=1` 存在即跳过奖励，仅记录尝试）；连胜奖励改为 `win_streak % 3 == 0` 时发放。

### S4 MEDIUM — 费曼检验零余额免费 LLM

**文件**：`backend/app/training/router.py:1590-1647`

`check_feynman` 先调 LLM 评分、写掌握度事件，后扣 2 智核；`change_cores` 把余额 clamp 到 0，余额不足时 LLM 调用和事件写入照常完成——AI 费用白嫖 + 免费掌握度事件刷写。

**修复**：`user.cores < TUTOR_COST` 时直接 402，不调 LLM、不写事件。

### S5 MEDIUM — 登录时序侧信道

**文件**：`backend/app/auth/service.py:139-147`

邮箱不存在时跳过 bcrypt（数毫秒返回），存在时 bcrypt 12 rounds（~390ms），时序差异可枚举注册邮箱，绕过统一错误响应的设计。

**修复**：用户不存在时对 dummy hash 执行一次同成本 `verify_password` 后返回相同异常。

### S6 MEDIUM — 邮箱大小写混淆

**文件**：`backend/app/auth/schemas.py`

`EmailStr` 只小写域名、保留本地部分大小写。`Boss@x.com` 与 `boss@x.com` 是两个账户，但多数邮件服务商本地部分大小写不敏感——身份混淆。

**修复**：注册与登录 schema 统一本地部分小写规范化。

### S7 LOW — bcrypt 72 字节截断

**文件**：`backend/app/auth/security.py:44,64`

截断多字节字符会切断 UTF-8 序列（`errors='ignore'` 静默丢弃），且用户以为 100+ 字符口令生效。

**修复**：注册时拒绝 UTF-8 编码超 72 字节的密码。

### 已核查无漏洞项（对抗验证通过）

- **SQL 注入**：全部请求路径使用 SQLAlchemy ORM 参数化查询；raw SQL 仅在离线迁移脚本（表名硬编码）。
- **命令注入**：`backend/app` 无 subprocess/eval/exec；Judge0 代码拼接发生在外部沙箱。
- **XSS**：全部 UGC（消息/输出/代码/动态）渲染为 React 文本节点；唯一 `dangerouslySetInnerHTML` 是静态主题脚本。
- **IDOR**：所有训练端点按 `user.id` 过滤；费曼会话 `uuid4` + 属主校验。
- **JWT 算法混淆**：`algorithms=["HS256"]` 显式白名单，none/HS384/过期/畸形令牌均拒绝（实测）。
- **评审答案泄漏**：三个内容端点的响应 schema 均正确剔除服务端秘密（缺陷/答案/测试用例）。

---

## 三、性能审计详情

### 后端（静态分析，未跑基准）

**C1 CRITICAL — `/profile` 每次请求全量重放时间线**：`build_timeline` 读全部 attempts/certifications/mastery events 并按事件重跑 HLR。**未修复**——需要引入快照表或增量状态，属架构级改动，超出本次修复范围（见「后续建议」）。

**P3 已修复 — 缺复合索引**（7 个索引 + 迁移脚本，见修复清单）。

**H1 徽章评估全表扫描**、**H2 排行榜无 rating 索引**（已修复 rating 索引）、**H3 rank_delta_7d 全局扫描**、**H4 tutor 端点串行 LLM 调用无截止时间**——**部分未修复**，详见「后续建议」。

**已确认良好实践**：WAL + busy_timeout 配置正确；异步 IO 贯穿；批量查询（leaderboard 单次分组查询）；徽章事实聚合一次；多处 LIMIT。

### 前端（静态分析，LCP/INP/CLS 未测量）

**已修复**：P1（DeckHeader 轻量化 + 去重）、P2（超时+去重）、P4（timer 清理+错误恢复）。

**未修复（低危/待办）**：
- CodeViewer 每行 `marks.find` O(n×m)（可 useMemo 优化）
- 认证页/竞技场倒计时 timer 依赖不稳定（键盘输入重建 timer）
- 无 route-level `error.tsx`/`loading.tsx`，多数 fetch 无 `.catch`

**已确认良好实践**：Monaco 动态导入正确隔离；路由级代码拆分完整；`next/font` + `display: swap`；主题预绘制脚本防 FOUC；`prefers-reduced-motion` 尊重；kit 组件 timer/RAF 清理正确；auth client 已有超时+abort。

---

## 四、后续建议（按优先级）

1. **接入 Judge0 或增强关键字判题**：S2/S3 修复堵住了重放，但关键字匹配仍可被构造答案绕过（设计权衡，接入真实判题后消除）。
2. **训练端点限流**：将 `/api/tutor/*`、`/api/arena/run`、`/api/certification/submit` 纳入限流（或独立窗口），防 AI 费用/资源滥用。
3. **费曼会话迁移 Redis/DB**：加 TTL 驱逐。
4. **JWT 迁移 httpOnly Cookie**：配合 CSRF token，消除 localStorage 暴露面。
5. **时间线/徽章评估增量化**：事件写入时维护快照（读模型已有 `DeckUserMastery` 先例），避免每次请求全量重放。
6. **tutor LLM 调用并发化 + 截止时间**：`asyncio.gather` + `asyncio.timeout`。
7. **修复前端 22 个 jest 基线失败**：已通过 jest.config.js 强制 `NODE_ENV=test` 修复（系统环境变量 `NODE_ENV=production` 曾让 react-dom 加载无 `act` 的 production 构建），138 测试全绿。
8. **复合索引已在 ORM 声明**：新库 `create_all` 自动获得；已有库跑 `python -m scripts.migrate_add_indexes`（幂等，已执行）。

---

## 五、验证证据

| 检查 | 命令 | 结果 |
|------|------|------|
| 后端测试 | `cd backend && .venv/Scripts/python -m pytest tests/ -q` | **288 passed** |
| 前端类型 | `cd frontend && npx tsc --noEmit` | **0 errors** |
| 前端构建 | `cd frontend && pnpm build` | **成功**（First Load JS 102 kB 共享） |
| 前端测试 | `cd frontend && npx jest` | **138 passed / 19 suites**（jest.config 强制 NODE_ENV=test 后） |
| 索引迁移 | `python -m scripts.migrate_add_indexes` | 7 indexes created（幂等） |
| 密钥轮换 | `ensure_backend_env` | SECRET_KEY 已替换为随机值 |
| 启动冒烟 | uvicorn :8000 + next dev :3000 | `/health` 200、`/login` 200 |
| 安全修复冒烟 | 真实 HTTP 请求 | 邮箱大小写规范化生效；认证重考 429；竞技场重放 rating 只加一次（profile=1223）；费曼余额不足 402；不存在邮箱登录 371ms ≈ 存在邮箱 350ms（时序抹平） |
| 并发竞态冒烟 | 双请求 asyncio.gather | 竞技场并发重放 delta=0（partial unique index 兜底）；认证并发重放双双 429；余额不变 |
| 重放语义冒烟 | 真实 HTTP + 单测 | 重放以 solved=0 落记录且 score_delta=0；recent_arena_win_rate 排除重放行（练习不拉低难度推荐），新增单测覆盖 |

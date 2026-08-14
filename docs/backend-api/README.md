# WisdomPilot 后端接口设计文档

> 日期：2026-07-26
> 受众：负责实现/重写后端的工程师（人类或 AI）
> 依据：`docs/2026-07-26-产品评估与重塑方案.md` + `docs/superpowers/specs/2026-07-26-deck-rebuild-design.md`

本目录是**全新后端**的完整规格说明。产品已重塑为「训练舱」（代码审查室 / 调试竞技场 /
苏格拉底导师 / 基本功认证），旧 API 与旧数据全部废弃，后端从零实现。

**权威 schema 是 `frontend/lib/api/deck/types.ts`**：前端已按它用 mock 数据完整渲染，
`01-target-design.md` 的每个响应结构与之逐字段对应。实现时让 `/api/*` 的响应严格匹配
types.ts，前端把 `NEXT_PUBLIC_DECK_MOCK` 置 `0` 即可无缝切换。

## 实现状态（2026-07-26 更新）

首版后端**已实现并通过端到端验证**，代码在 `backend/app/deck/`：

| 文件 | 职责 |
|---|---|
| `models.py` | 16 张 `deck_` 前缀新表（复用 legacy `users` 表） |
| `seed.py` | 幂等种子：13 知识点、2 审查关卡 + 5 注入缺陷、1 竞技场挑战、2 套试卷 11 题 |
| `service.py` | 判定逻辑（审查/竞技场/费曼/认证）、能力轴、智核经济、主任务分发 |
| `router.py` | 15 个 `/api/*` 端点（dashboard、ability-map、profile、review-gym×2、review/queue、arena×2、tutor×4、certification×3） |

装配：`app/core/routes.py` 只注册 auth + deck 路由（旧 router 文件保留但不再挂载）；
`app/core/lifespan.py` 在 `init_db()` 后执行 `seed_deck()`。

> **已有数据库升级注意**：`seed_deck` 幂等（知识点表非空即跳过），已有库不会自动获得
> 新增/修订的种子内容（新关卡、新挑战、题目修订）。升级代码后请执行：
>
> ```bash
> cd backend && python -m scripts.migrate_missing_columns        # 补缺失列（start_services 已自动跑）
> cd backend && python -m scripts.migrate_backfill_deck_content  # 同步内容（upsert，幂等）
> ```
>
> 启动时 lifespan 会检测内容表行数是否落后于 seed 并打印上述提示（WARNING 日志）。

当前判定为**关键字/答案表规则**（与前端 mock 逐字对齐）；竞技场 Judge0 真判题与
导师 LLM 追问是已标注的后续替换点（见 service.py 注释）。

## 阅读顺序

| 顺序 | 文件 | 内容 | 什么时候读 |
|---|---|---|---|
| 1 | `01-target-design.md` | 目标接口设计：端点清单、字段级 schema、数据模型、主任务分发规则 | 实现时对照施工 |
| 2 | `02-migration.md` | 删库重建步骤与种子数据清单（**无数据迁移，全部清零**） | 建库前必读 |
| 3 | `03-economy.md` | 智核单货币的获取/消耗/防刷规则 | 实现任何涉及智核的逻辑时必读 |
| 参照 | `00-current-state.md` | 旧 API 全貌快照（**已废弃，仅历史参照**） | 理解历史决策时 |

## 全局约定

以下约定适用于**目标设计**（01 文档）中的所有新端点。现状端点存在大量不一致（见 00 文档各节备注），重写时统一到此约定。

### 认证

- 方式：JWT Bearer Token。请求头 `Authorization: Bearer <token>`。
- 获取：`POST /api/auth/register` 或 `POST /api/auth/login`，响应 `{"access_token": "...", "token_type": "bearer"}`。
- Token 载荷 `sub` 为用户 ID（String(36) UUID）。
- 除明确标注「公开」的端点外，一律要求认证；管理端点要求 `is_admin=true`。
- WebSocket 认证：查询参数 `?token=<jwt>`，鉴权失败以 `4001` 关闭。

### 错误格式

统一使用 FastAPI 风格错误体：

```json
{ "detail": "错误描述（人类可读）" }
```

- 参数校验失败：HTTP 422，body 为 `{"detail": [{"loc": ["body", "field"], "msg": "...", "type": "..."}]}`。
- 业务错误使用语义化 HTTP 状态码：400（参数/状态非法）、401（未认证）、403（无权限/余额不足之外的禁止操作）、404（资源不存在）、409（状态冲突，如重复提交）、429（触发频率限制）、503（外部依赖不可用，如判题服务）。
- 智核余额不足统一返回 **402** `{"detail": "智核余额不足", "required": 3, "balance": 1}`（在 402 场景允许附带额外字段）。
- **例外（已实现偏差）**：导师对话类端点（`POST /api/tutor/message`、`POST /api/tutor/feynman/check`）余额不足时返回 **200** + 一条提示性质的导师消息（`TutorReply` 结构，不扣费），因为前端契约要求响应恒为 `TutorReply`。费曼检验当前直接按 `change_cores` 地板规则扣到 0 为止，不拦截。

### 分页

- 请求：`limit`（默认 20，最大 100）+ `offset`（默认 0）。
- 响应统一包一层：

```json
{ "items": [], "total": 137, "limit": 20, "offset": 0 }
```

- 现状中「直接返回数组」「内存分页」等做法在重写时一律收敛到此格式。

### 时间戳

- 一律 ISO 8601 UTC、带 `Z` 后缀，例如 `"2026-07-26T06:52:11Z"`。
- 与「自然日」相关的逻辑（签到、每日统计、每日上限）按**北京时间（UTC+8）** 判定，存储仍为 UTC。
- 前端展示时自行转本地时区，后端不输出不带时区的时间。

### 字段命名

- JSON 字段一律 `snake_case`。
- 布尔字段用 `is_` / `has_` / `can_` 前缀（如 `is_correct`、`has_active_session`）。
- 金额/数量字段用名词（`amount`、`balance`、`stars`），变化量用 `*_change`（如 `stars_change`）。
- ID：新表主键一律 String(36) UUID；存量 Integer 自增主键（courses/chapters/sections/exercises 等）保留不动，但新端点路径参数中称为 `*_id` 并在 schema 中标注类型。

### 幂等与事务

- 所有「提交答案 / 结算奖励」类端点必须幂等：同一资源重复提交返回首次结果，不重复发放 XP/智核/星星。
- 奖励发放与流水记录在同一事务内；service 层只 `flush`，由调用方控制 `commit`（沿用现有 `core_service` 的事务边界约定）。
- 用户余额类字段更新使用 `SELECT ... FOR UPDATE` 行锁防并发。

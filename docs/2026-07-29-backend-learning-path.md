# 后端代码库学习路线

> 面向初次接触本项目的开发者，给出一条从外到内、从骨架到核心的阅读顺序。
>
> 配套参考：`docs/2026-07-28-backend-codebase-guide.md`（逐文件结构说明）
>
> 技术栈：Python 3.10+ / FastAPI / SQLAlchemy 2.0 (async) / SQLite (aiosqlite) / Pydantic v2

---

## 总览路线

```
main.py → config.py → database.py → core/* → auth/* → training/models.py
  → training/mastery.py → training/badges.py → training/service.py → training/router.py
  → ai/* → services/* → tests/*
```

核心思路：**先看怎么启动，再看请求怎么流转，然后从数据模型到纯算法到业务编排到路由，最后是周边基础设施。**

`training/mastery.py` 和 `training/service.py` 是整个系统最有价值的两个文件，前者是算法核心，后者是业务中枢。

---

## 第一阶段：应用入口与基础设施

> 目标：理解"程序怎么跑起来的"

| 顺序 | 文件 | 为什么先读它 |
|------|------|-------------|
| 1 | `app/main.py` | FastAPI 工厂函数 `create_app()`，全局组装顺序一览无余——看这一个文件就知道整个应用由哪些部分拼成 |
| 2 | `app/config.py` | 全局配置项（数据库、JWT、AI、限流），读完就知道系统依赖哪些外部参数 |
| 3 | `app/database.py` | 异步引擎 + 会话工厂 + `Base` + `get_db()` 依赖，后续所有 ORM 和 service 都建立在这上面 |

---

## 第二阶段：核心骨架

> 目标：理解"请求怎么进来、怎么出去"

| 顺序 | 文件 | 重点 |
|------|------|------|
| 4 | `app/core/routes.py` | 路由注册——只有 `auth` + `training` 两组，是整个系统的入口地图 |
| 5 | `app/core/lifespan.py` | 启动生命周期：建表 → 灌种子 → 配置 AI，理解初始化时序 |
| 6 | `app/core/middleware.py` | 限流（滑动窗口）+ CORS，理解请求拦截层 |
| 7 | `app/core/exceptions.py` | 全局异常处理，理解错误响应格式 |

---

## 第三阶段：认证域

> 目标：通过一个自包含的小模块，熟悉本项目的分层模式（schemas → models → security → service → dependencies → router）

| 顺序 | 文件 | 重点 |
|------|------|------|
| 8 | `app/auth/schemas.py` | Pydantic 请求/响应模型，理解输入校验规则 |
| 9 | `app/auth/models.py` | `User` 表结构（唯一非训练域的表） |
| 10 | `app/auth/security.py` | bcrypt 哈希 + JWT 签发/解码 |
| 11 | `app/auth/service.py` | `AuthService`：注册/登录/忘记密码的业务编排 |
| 12 | `app/auth/dependencies.py` | `get_current_user` 依赖注入——所有需认证端点的入口 |
| 13 | `app/auth/router.py` | 4 个端点，把前面的串起来 |

---

## 第四阶段：训练舱核心域

> 目标：理解系统最重要的业务模块。建议先模型、再纯函数引擎、再服务、最后路由。

| 顺序 | 文件 | 为什么这个顺序 |
|------|------|---------------|
| 14 | `app/training/models.py` | 16 张表定义，先建立数据全景认知。注意事件溯源模式：`deck_mastery_events` 是事实源，`deck_user_mastery` 是缓存 |
| 15 | `app/training/mastery.py` | **纯函数引擎**，不碰数据库。HLR 记忆模型 + 四级状态机 + 费曼评分。先读这个能理解核心算法逻辑，不被 DB 代码干扰 |
| 16 | `app/training/badges.py` | 徽章评估引擎，同样是纯函数驱动（`BadgeFacts` + `BadgeDef` + `evaluate_and_award`） |
| 17 | `app/training/service.py` | **领域服务**（~454 行），桥接 DB 与纯函数引擎。这里是所有业务编排的中枢：掌握度事件、智核经济、活动动态、判定逻辑、段位 |
| 18 | `app/training/router.py` | **最大文件**（~1221 行），所有 API 端点。按模块分块读：Dashboard → 能力图谱 → 审查室 → 竞技场 → 导师 → 认证 |
| 19 | `app/training/seed.py` | 种子数据，读完后能理解演示环境的数据长什么样 |

### 第四阶段阅读建议

- `router.py` 很长，不要线性从头读到尾。先扫一遍所有端点的路径和方法，再按业务模块逐块读。
- `service.py` 中的 `judge_marks()`、`record_mastery_event()`、`change_cores()` 三个函数是理解全流程的关键。
- 读 `mastery.py` 时可以同时打开 `tests/test_training_mastery.py`，用测试用例反推算法语义。

---

## 第五阶段：AI 基础设施与外部服务

> 目标：按需阅读，理解扩展点

| 顺序 | 文件 | 说明 |
|------|------|------|
| 20 | `app/ai/config.py` → `provider/base.py` → `provider/client.py` → `provider/openai.py` → `service.py` | Provider 抽象 + OpenAI 兼容客户端 + 重试/流式。当前训练舱路由尚未直接使用，但骨架已搭好 |
| 21 | `app/services/judge0_client.py` → `judge0.py` | Judge0 代码执行服务，竞技场后续真实判分会接入 |
| 22 | `app/utils/time.py` | 一个函数 `utc_now()`，顺手看完 |

---

## 第六阶段：测试

> 目标：通过测试用例验证对实现的理解

| 顺序 | 文件 | 说明 |
|------|------|------|
| 23 | `tests/conftest.py` | 测试基础设施：内存 SQLite + 依赖覆盖 |
| 24 | `tests/test_training_mastery.py` | 掌握度纯函数的测试——读测试用例是理解算法最快的方式 |
| 25 | `tests/test_training_badges.py` | 徽章评估的测试 |
| 26 | 其余 `test_*.py` | 按兴趣选读 |

---

## 架构分层速查

```
Router（路由层）  →  Service（领域服务）  →  Models（ORM 模型）
                          ↓
                    mastery.py / badges.py（纯函数引擎）
                          ↓
                    database.py（基础设施）
```

- **路由层**（`router.py`）：接收请求、调用 service、组装响应，不直接写业务逻辑。
- **领域服务**（`service.py`）：业务逻辑编排，桥接数据库与纯函数引擎。
- **纯函数引擎**（`mastery.py`、`badges.py`）：无副作用的核心算法，输入→输出，可独立测试。
- **模型层**（`models.py`）：ORM 定义，只管数据结构。
- **基础设施**（`database.py`、`ai/`、`services/`）：技术关注点。

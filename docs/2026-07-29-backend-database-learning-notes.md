# 后端数据库基础设施学习与代码修复归档

> 日期：2026-07-29
> 涉及文件：`backend/app/main.py`、`backend/app/config.py`、`backend/app/database.py`
> 主题：SQLAlchemy 异步数据库层知识点梳理 + 代码修复记录

---

## 一、代码修改记录

### 1. main.py — 局部变量遮蔽警告修复

**问题**：模块级 `app = create_app()` 与 `create_app()` 内部的局部变量 `app` 同名，IDE 报 "shadows name from outer scope"。

**改动**：函数内局部变量 `app` 改名为 `application`，模块级 `app = create_app()` 不变。

```python
def create_app() -> FastAPI:
    application = FastAPI(...)          # 原来叫 app
    configure_middleware(application)
    include_routers(application, settings)
    register_health_routes(application)
    register_exception_handlers(application)
    return application

app = create_app()  # 模块级不变，uvicorn 仍引用 app.main:app
```

### 2. database.py — WAL 模式缺失修复

**问题**：注释和 docstring 多处声称开启 WAL 模式，但代码中只有 `foreign_keys` 和 `busy_timeout` 两条 PRAGMA，缺失 `journal_mode=WAL` 的实际执行语句。

**改动**：补上 `cursor.execute("PRAGMA journal_mode=WAL")`，使三条 PRAGMA 齐全：

```python
cursor.execute("PRAGMA foreign_keys=ON")
cursor.execute("PRAGMA journal_mode=WAL")       # 补充
cursor.execute("PRAGMA busy_timeout=30000")
```

### 3. database.py — run_sync 类型检查报错修复

**问题**：`conn.run_sync(Base.metadata.create_all)` 触发 Pyright 类型不匹配警告——`create_all` 的第一个参数是 `Engine | Connection | MockConnection` 联合类型，而 `run_sync` 期望纯 `Connection`。

**改动**：改为显式函数定义（与同文件 `_check_alembic`、`_stamp_head` 风格一致）：

```python
def _create_tables(sync_conn: Connection):
    Base.metadata.create_all(sync_conn)

await conn.run_sync(_create_tables)
```

### 4. database.py — get_table_names() 警告修复

**问题**：`_check_alembic(sync_conn)` 的参数没有类型标注，`inspect()` 是重载函数，PyCharm 无法推断返回类型，导致 `inspector.get_table_names()` 报"找不到方法"。

**改动**：三个局部函数的 `sync_conn` 都加上 `Connection` 类型标注，并导入：

```python
from sqlalchemy.engine import Connection

def _create_tables(sync_conn: Connection): ...
def _check_alembic(sync_conn: Connection): ...
def _stamp_head(sync_conn: Connection): ...
```

### 5. database.py — connection_record 加下划线前缀

**问题**：`_set_sqlite_pragma` 的第二个参数 `connection_record` 未使用，但未按 Python 惯例加下划线前缀。

**改动**：

```python
def _set_sqlite_pragma(dbapi_connection, _connection_record):
```

docstring 同步更新。

### 6. 三个文件 — 英文注释清理为中文

**涉及文件**：`main.py`、`config.py`、`database.py`

**改动**：删除所有重复的英文 docstring 和英文行内注释，保留已有的中文注释。日志消息字符串（`logger.info(...)` 中的英文）保留不动，因为那是运行时输出不是注释。

---

## 二、知识点梳理

### 1. `@lru_cache()` 装饰器

- `functools.lru_cache` 给函数加缓存，避免重复计算
- LRU = Least Recently Used，缓存满时淘汰最久未使用的
- `@lru_cache()` 空白不填 = 默认 `maxsize=128, typed=False`
- 无参函数（如 `get_settings()`）只有一种参数组合，`maxsize` 多少都无所谓
- 带括号 `@lru_cache()` vs 不带括号 `@lru_cache`：3.8+ 都可用，效果相同

### 2. `cursor = dbapi_connection.cursor()`

- 游标（cursor）是执行 SQL 和遍历结果的"把手"
- 连接（connection）是通道，游标是真正执行操作的地方
- `execute()` 执行 SQL，`fetchone()/fetchall()` 获取结果
- 一个连接可以创建多个游标，彼此独立

### 3. `@event.listens_for` 事件监听器

- SQLAlchemy 提供的事件钩子：当某事件发生时自动调用函数
- `@event.listens_for(engine.sync_engine, "connect")` = 每当新建 DBAPI 连接时自动调用
- 用于在每条新连接上设置连接级 PRAGMA（foreign_keys、WAL、busy_timeout）

### 4. `PRAGMA foreign_keys=ON`

- SQLite 默认关闭外键约束，必须手动开启
- 开启后：插入时阻止指向不存在的父记录、删除时阻止删除被引用的记录、支持级联删除
- 外键开关是**连接级**的，每条新连接默认关闭，所以需要事件监听器每次建连时重新开

### 5. WAL 模式

- Write-Ahead Logging，写入先记到 `-wal` 文件再 checkpoint 回主库
- 允许读不阻塞写、写不阻塞读
- 数据库级设置（持久化到文件），但放在 connect 事件里重复执行无害（幂等）

### 6. `alembic_version` 表

- Alembic 迁移系统的"书签"，只存一行：当前数据库版本号
- 每次迁移执行后更新版本号
- 检查此表是否存在 = 判断数据库是否被 Alembic 管理过
- 存在 -> 接着当前版本走；不存在 -> 全新数据库，写入初始版本号

### 7. `inspect()` 函数

- SQLAlchemy 的 `inspect`（不是 Python 标准库的），用于查看数据库**结构**元信息
- `inspect(connection)` 返回 `Inspector` 对象
- `inspector.get_table_names()` 查所有表名、`get_columns()` 查列结构等
- 是重载函数：传 `Engine`/`Connection` 返回 `Inspector`，传 ORM 实例返回 `InstanceState`

### 8. `engine.begin()` 返回什么

- 返回带事务的异步连接 `AsyncConnection`
- `async with` 进入时开事务，退出时自动提交/回滚
- 用于 DDL 操作（建表），需要事务保证
- `begin()` vs `connect()`：前者自动开事务，后者不自动开

### 9. `async_sessionmaker` 第一个参数 `engine`

- 告诉会话工厂"连哪个数据库、怎么管连接池"
- 工厂靠引擎才知道从哪个连接池借连接

### 10. 下划线前缀命名约定

| 前缀 | 含义 |
|------|------|
| `_name` | 内部使用，不建议外部调用 |
| `__name` | 更强私有（触发名称改写） |
| `name` | 公开 API |

- 只是约定，Python 不强制阻止访问
- `from module import *` 默认不导入下划线开头的名字
- 未使用的参数加 `_` 前缀表示"故意忽略"

### 11. `connection_record` 参数

- SQLAlchemy `"connect"` 事件回调的第二个参数
- 是连接池里的记录对象，包含连接创建时间、检出/归还状态、所属池等元信息
- 设 PRAGMA 只需要底层 DBAPI 连接，不需要连接池层面信息，所以加 `_` 前缀忽略

---

## 三、四层连接/会话结构

```
┌─────────────────────────────────────────────────────┐
│  ④  Session（会话）   AsyncSession                    │  ← 业务层
│      ORM 映射、身份映射、增删改查                       │
│      生产者：AsyncSessionLocal()                      │
├─────────────────────────────────────────────────────┤
│  ③  Connection（连接）  AsyncConnection               │  ← 事务层
│      事务管理、执行 SQL、DDL 建表                       │
│      生产者：engine.begin() / engine.connect()        │
├─────────────────────────────────────────────────────┤
│  ②  Engine（引擎）                                     │  ← 池管理层
│      连接池管理、创建/回收连接                           │
│      全局唯一：engine = create_async_engine(...)       │
├─────────────────────────────────────────────────────┤
│  ①  DBAPI 连接（底层连接）                             │  ← 最底层
│      aiosqlite / sqlite3 的原始连接对象                 │
│      真正能跑 SQL 的那个东西                            │
└─────────────────────────────────────────────────────┘
```

| 层级 | 代码位置 | 做什么 |
|------|---------|--------|
| ① DBAPI 连接 | `_set_sqlite_pragma(dbapi_connection, ...)` | 设 PRAGMA |
| ② Engine | `engine = create_async_engine(...)` | 管连接池 |
| ③ Connection | `async with engine.begin() as conn` | 建表（DDL） |
| ④ Session | `async with AsyncSessionLocal() as session` | 增删改查（ORM） |

Session 内部包着 Connection，Connection 内部包着 DBAPI 连接：

```
Session（会话）— 加了 ORM
 └── Connection（连接）— 加了事务管理
      └── DBAPI 连接 — 能跑 SQL，仅此而已
```

建表用 Connection（DDL 不需要 ORM），业务增删改查用 Session（需要操作 ORM 对象）。

---

## 四、涉及的数据库表结构

迁移后数据库共有 18 张表（17 张业务表 + 1 张 alembic_version）：

| 表名 | 用途 | 来源文件 |
|------|------|---------|
| `users` | 用户认证与账户信息 | `auth/models.py` |
| `alembic_version` | Alembic 迁移版本标记 | 迁移系统自动创建 |
| `deck_knowledge_points` | 知识点定义（种子内置） | `training/models.py` |
| `deck_user_mastery` | 用户掌握度缓存（读模型） | 同上 |
| `deck_mastery_events` | 掌握度事件流（事实源） | 同上 |
| `deck_ability_axes` | 三轴经验值 | 同上 |
| `deck_review_sessions` | 代码审查室关卡 | 同上 |
| `deck_injected_defects` | 注入缺陷（服务端秘密） | 同上 |
| `deck_review_attempts` | 审查提交记录 | 同上 |
| `deck_arena_challenges` | 竞技场挑战 | 同上 |
| `deck_arena_attempts` | 竞技场提交记录 | 同上 |
| `deck_arena_ratings` | ELO 评分 | 同上 |
| `deck_tutor_messages` | 导师对话消息 | 同上 |
| `deck_core_transactions` | 智核流水账 | 同上 |
| `deck_cert_exams` | 认证考试定义 | 同上 |
| `deck_cert_questions` | 考试题目 | 同上 |
| `deck_certifications` | 用户认证凭证 | 同上 |
| `deck_daily_activity` | 每日活动统计 | 同上 |
| `deck_feed_events` | 动态流事件 | 同上 |
| `deck_user_badges` | 已解锁徽章记录 | 同上 |

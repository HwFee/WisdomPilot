"""
异步数据库引擎与会话管理模块。

本模块是整个后端的数据访问基础设施，基于 SQLAlchemy 2.0 异步模式构建：
    - 使用 ``aiosqlite`` 作为 SQLite 的异步驱动
    - 使用 ``AsyncSession`` 进行异步数据库操作
    - 使用 ``DeclarativeBase`` 作为所有 ORM 模型的基类

核心组件：
    - ``engine``: 全局异步数据库引擎（连接池管理）
    - ``AsyncSessionLocal``: 异步会话工厂（用于创建数据库会话）
    - ``Base``: 所有 ORM 模型的声明式基类
    - ``get_db``: FastAPI 依赖注入函数，为每个请求提供数据库会话
    - ``init_db``: 数据库初始化函数（建表 + Alembic 版本标记）

SQLite 优化：
    - 开启外键约束（SQLite 默认关闭）
    - 使用 WAL 模式提升并发读写性能
    - 设置 30 秒忙超时，避免写冲突时立即报错
"""

import logging
from typing import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

# 模块级日志记录器，用于记录数据库操作中的异常信息
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 创建全局异步数据库引擎
# ---------------------------------------------------------------------------
# echo=False: 不在控制台输出 SQL 语句（生产环境应关闭）
# future=True: 使用 SQLAlchemy 2.0 风格 API
# pool_pre_ping=True: 每次从连接池取连接前先发 ping，避免使用已断开的连接
# pool_recycle=3600: 连接在连接池中存活 3600 秒（1 小时）后自动回收重建
engine = create_async_engine(
    get_settings().DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
)

#  @event.listens_for(target, event_name) 是 SQLAlchemy 提供的事件监听装饰器，作用是：当 target 上发生
#  event_name 这种事件时，自动调用下面的函数
@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _connection_record):
    """在每次建立新的 SQLite 连接时设置 PRAGMA 参数。

    SQLAlchemy 的事件监听器机制：每当底层的 DBAPI 建立新连接时，
    本函数会被自动调用，用于配置 SQLite 的运行时参数。

    为什么需要这样做：
        - SQLite 默认不开启外键约束，需要手动 ``PRAGMA foreign_keys=ON``
        - SQLite 默认使用 DELETE 日志模式，WAL 模式可以大幅提升并发读写性能
        - 忙超时防止写冲突时立即报错，给其他事务释放锁的时间

    Args:
        dbapi_connection: 底层 aiosqlite/sqlite3 的原始连接对象
        _connection_record: SQLAlchemy 内部的连接记录对象（回调签名要求，未使用）
    """
    cursor = dbapi_connection.cursor()
    # 开启外键约束：SQLite 默认关闭外键，需要手动开启才能让 CASCADE 删除等约束生效
    cursor.execute("PRAGMA foreign_keys=ON")
    # WAL (Write-Ahead Logging) 模式：允许读写并发（普通模式下写操作会阻塞读）
    cursor.execute("PRAGMA journal_mode=WAL")
    # 设置忙超时为 30 秒：当遇到数据库被锁定时，最多等待 30 秒再报错
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.close()


def get_engine_url() -> str:
    """获取当前配置的数据库连接 URL。

    Returns:
        str: 数据库连接字符串，如 ``sqlite+aiosqlite:///./data/data.db``
    """
    return get_settings().DATABASE_URL


def is_debug_enabled() -> bool:
    """检查是否启用了调试模式。

    调试模式下可以输出更详细的 SQL 日志等信息。

    Returns:
        bool: True 表示调试模式已开启
    """
    return get_settings().DEBUG

# ---------------------------------------------------------------------------
# 异步会话工厂
# ---------------------------------------------------------------------------
# 使用 async_sessionmaker 创建会话工厂，每次调用会生成一个新的 AsyncSession
# expire_on_commit=False: commit 后不自动过期对象（避免 commit 后访问属性触发额外查询）
# autocommit=False: 不自动提交，需要手动调用 session.commit()
# autoflush=False: 不自动刷新（不在查询前自动将挂起的修改发送到数据库）
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """所有 ORM 模型的声明式基类。

    所有数据库模型（如 User、DeckMasteryEvent 等）都继承自此类。
    SQLAlchemy 通过 ``Base.metadata`` 收集所有模型的表定义信息，
    ``init_db()`` 中的 ``Base.metadata.create_all`` 会根据这些信息创建数据库表。
    """
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入：为每个请求提供异步数据库会话。

    本函数是一个异步生成器，在路由函数中通过 ``Depends(get_db)`` 注入。
    它会在请求开始时创建一个数据库会话，请求结束后自动提交或回滚并关闭会话。

    生命周期：
        1. 创建会话 -> 2. yield 会话给路由使用 -> 3. 路由执行完毕
        4. 如果没有异常则 commit，有异常则 rollback -> 5. 关闭会话

    异常处理策略：
        如果请求处理过程中抛出任何异常，会自动回滚事务并记录日志，
        防止部分写入的数据导致数据不一致。

    Yields:
        AsyncSession: 异步数据库会话实例

    用法示例:
        ``python
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
        ``
    """
    async with AsyncSessionLocal() as session:
        try:
            # 将会话交给路由函数使用
            yield session
            # 路由执行完毕且无异常，提交事务
            await session.commit()
        except Exception:
            # 发生异常，回滚所有未提交的修改，防止脏数据
            logger.exception("Database transaction failed, rolling back")
            await session.rollback()
            # 重新抛出异常，让上层异常处理器处理
            raise
        finally:
            # 无论成功还是失败，都关闭会话释放连接
            await session.close()


async def init_db():
    """初始化数据库 - 创建表或应用迁移。

    初始化策略：
        1. **始终执行 create_all**：这是幂等操作，只会创建缺失的表，不会删除已有表。
           这确保了即使有 Alembic 迁移记录，新增的模型表也会被自动创建。
        2. **检查 Alembic 版本表**：如果存在 ``alembic_version`` 表，说明数据库
          已经被 Alembic 迁移系统管理，无需额外处理。
        3. **如果没有 Alembic 记录**：直接插入版本标记 ``001_initial``，
           避免后续 Alembic 尝试重复执行初始迁移。

    为什么不直接用 Alembic 的 ``command.stamp()``：
        因为 ``command.stamp()`` 会加载 ``env.py``，其中可能包含 ``asyncio.run()``
        调用，而当前已经在异步上下文中，会导致 "event loop already running" 错误。
        所以直接用 SQL INSERT 写入版本号。

    对于正式的 schema 迁移，应运行: ``alembic upgrade head``
    """
    from sqlalchemy import text, inspect
    from sqlalchemy.engine import Connection

    async with engine.begin() as conn:
        # 始终创建缺失的表（幂等操作 - 不会删除已存在的表）
        # create_all 会检查 Base.metadata 中收集的所有模型表定义，只创建不存在的表
        def _create_tables(sync_conn: Connection):
            Base.metadata.create_all(sync_conn)

        await conn.run_sync(_create_tables)

        # 检查 alembic_version 表是否存在（Alembic 迁移系统的版本跟踪表）
        def _check_alembic(sync_conn: Connection):
            inspector = inspect(sync_conn)
            return 'alembic_version' in inspector.get_table_names()

        has_alembic = await conn.run_sync(_check_alembic)

        if has_alembic:
            # 已有 Alembic 记录，说明数据库已被迁移系统管理，只需确保新表已创建
            logger.info("Database tables ensured (new tables created if needed). Alembic tracked.")
        else:
            # 没有 Alembic 记录 - 直接写入版本行来标记当前数据库版本
            # 这样避免了调用 command.stamp()（它会加载 env.py -> asyncio.run() 产生冲突）
            # 使用 INSERT OR IGNORE 处理并发启动时的竞态条件
            def _stamp_head(sync_conn: Connection):
                # 创建 alembic_version 表（如果不存在）
                sync_conn.execute(
                    text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL, CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))")
                )
                # 插入初始版本号 "001_initial"，INSERT OR IGNORE 防止重复插入
                sync_conn.execute(
                    text("INSERT OR IGNORE INTO alembic_version (version_num) VALUES (:ver)"),
                    {"ver": "001_initial"},
                )

            await conn.run_sync(_stamp_head)
            logger.info("Database initialized and stamped with Alembic revision 001_initial.")

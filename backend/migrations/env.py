"""
Alembic 异步环境配置

- 从 app.config 动态读取 DATABASE_URL
- 使用 Base.metadata 进行自动生成迁移
- 支持异步引擎 + SQLite
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Alembic Config 对象
config = context.config

# 设置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 导入 Base 和所有模型（确保 metadata 包含所有表定义）
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base
from app.config import get_settings

# 动态设置数据库 URL
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式：生成 SQL 脚本，不连接数据库"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """执行迁移（同步回调）"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """在线模式：连接数据库并执行迁移"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在线模式入口"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

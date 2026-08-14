"""
自动迁移脚本：为 SQLAlchemy 模型中定义、但本地 SQLite 数据库中缺失的列
自动执行 ALTER TABLE ADD COLUMN。

这是一个开发辅助工具，用于解决以下场景：
    在开发过程中，开发者修改了 SQLAlchemy 模型（如新增字段），但本地
    SQLite 数据库文件已经存在，create_all 不会为已有表添加新列。
    本脚本通过比较模型定义与数据库实际结构，自动补齐缺失的列。

局限性（重要）：
    - 仅处理「新增列」，不处理列类型变更、约束变更或数据迁移
    - 新增的 NOT NULL 列必须提供默认值（SQLite 的限制）
    - 不适用于生产环境的数据库迁移，生产环境应使用 Alembic

使用方式：
    cd backend && python -m scripts.migrate_missing_columns
"""

import asyncio
import sqlite3
from pathlib import Path

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.dialects.sqlite import dialect as sqlite_dialect

from app.database import engine
from app.config import get_settings
# noqa: F401,F403 - 通配导入确保所有模型类被加载，从而注册到 Base.metadata
# 只有注册到 metadata 的表才会参与迁移检查
from app.auth.models import *  # noqa: F401,F403 - register all models with Base
from app.training.models import *  # noqa: F401,F403 - register training models
from app.database import Base


async def migrate_missing_columns() -> None:
    """
    执行列迁移：比较 ORM 模型定义与数据库实际结构，补齐缺失的列。

    执行流程：
        1. 读取数据库配置，仅对 SQLite 数据库执行迁移
        2. 通过 SQLAlchemy inspector 获取数据库中已有的表列表
        3. 用 sqlite3 直接连接数据库文件（绕过 ORM，直接执行 DDL）
        4. 遍历每个模型表，逐列检查是否缺失
        5. 对缺失的列构建 ALTER TABLE ADD COLUMN 语句并执行
        6. 提交事务
    """
    settings = get_settings()
    db_url = settings.DATABASE_URL

    # 仅支持 SQLite 数据库；其他数据库（如 PostgreSQL）应使用 Alembic
    if not db_url.startswith("sqlite"):
        print("[migrate] Non-SQLite database; skipping.")
        return

    # 从连接 URL 中提取数据库文件路径
    # 例如 "sqlite:///./data.db" -> "data.db"
    db_path = db_url.split(":///", 1)[-1]
    if db_path.startswith("./"):
        db_path = db_path[2:]

    # 以脚本文件位置为基准，拼接到 backend/ 目录下的数据库文件路径
    db_file = Path(__file__).resolve().parent.parent / db_path

    if not db_file.exists():
        print(f"[migrate] Database file not found at {db_file}; skipping.")
        return

    # 第一步：通过 SQLAlchemy 的 inspector 获取数据库中已存在的表名列表
    # 使用 run_sync 是因为 inspector 的 API 是同步的，需要包装到异步调用中
    async with engine.connect() as conn:
        tables = await conn.run_sync(lambda sync_conn: sa_inspect(sync_conn).get_table_names())

    # 第二步：用 sqlite3 模块直接操作数据库文件
    # 这里不使用 SQLAlchemy ORM，因为 ALTER TABLE 是 DDL 语句，
    # 直接用 sqlite3 执行更直接、可控
    conn = sqlite3.connect(str(db_file))
    try:
        cursor = conn.cursor()
        added_any = False  # 跟踪是否有任何列被添加

        # 遍历 Base.metadata 中注册的所有表（即 ORM 模型定义的表）
        for table_name, table in Base.metadata.tables.items():
            if table_name not in tables:
                # 表本身不存在，跳过--create_all 会负责创建新表
                continue

            # PRAGMA table_info 返回表的列信息，row[1] 是列名
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = {row[1] for row in cursor.fetchall()}

            # 逐列检查模型定义中是否有数据库缺失的列
            for column in table.columns:
                if column.name in existing_columns:
                    continue  # 列已存在，跳过

                # 构建 ALTER TABLE ADD COLUMN 语句
                # 将 SQLAlchemy 列类型编译为 SQLite 方言的 SQL 类型
                col_type = column.type.compile(dialect=sqlite_dialect())
                nullable = "NULL" if column.nullable else "NOT NULL"
                default_clause = ""

                # 处理默认值
                if column.default is not None and hasattr(column.default, "arg"):
                    # 模型中显式定义了默认值（如 default=False）
                    default_val = column.default.arg
                    if isinstance(default_val, str):
                        default_clause = f" DEFAULT '{default_val}'"
                    else:
                        default_clause = f" DEFAULT {default_val}"
                elif not column.nullable:
                    # SQLite 要求：为已有表添加 NOT NULL 列时必须提供默认值
                    # 根据列类型推断合适的默认值
                    if "INT" in col_type.upper() or "BOOL" in col_type.upper():
                        default_clause = " DEFAULT 0"
                    elif "FLOAT" in col_type.upper() or "DOUBLE" in col_type.upper():
                        default_clause = " DEFAULT 0.0"
                    elif "JSON" in col_type.upper():
                        default_clause = " DEFAULT '[]'"
                    else:
                        default_clause = " DEFAULT ''"

                # 拼接完整的 ALTER TABLE 语句
                sql = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type} {nullable}{default_clause}"
                try:
                    cursor.execute(sql)
                    print(f"[migrate] {table_name}.{column.name}: added")
                    added_any = True
                except sqlite3.OperationalError as exc:
                    # 某些列可能因约束冲突无法添加（如 UNIQUE），记录并跳过
                    print(f"[migrate] {table_name}.{column.name}: skipped ({exc})")

        # 只有添加了列才需要提交
        if added_any:
            conn.commit()
            print("[migrate] Migration complete.")
        else:
            print("[migrate] No missing columns found.")
    finally:
        # 无论成功与否都要关闭数据库连接
        conn.close()


if __name__ == "__main__":
    # asyncio.run 创建事件循环并运行异步迁移函数
    asyncio.run(migrate_missing_columns())

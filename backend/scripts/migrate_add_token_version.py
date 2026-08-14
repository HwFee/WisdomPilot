"""
迁移脚本：为 users 表新增 token_version 列（JWT 吊销版本号）。

背景：token_version 用于 logout / 改密码时使该用户所有旧 JWT 立即失效。
SQLite 的 create_all 不会为已有表添加新列，故需要本脚本补齐。

使用方式：
    cd backend && python -m scripts.migrate_add_token_version
"""

import asyncio
import sqlite3
from pathlib import Path

from sqlalchemy import inspect as sa_inspect

from app.database import engine
from app.config import get_settings


async def migrate() -> None:
    """为 users 表新增 token_version 列（如缺失）。"""
    settings = get_settings()
    db_url = settings.DATABASE_URL

    if not db_url.startswith("sqlite"):
        print("[migrate] Non-SQLite database; skipping.")
        return

    db_path = db_url.split(":///", 1)[-1]
    if db_path.startswith("./"):
        db_path = db_path[2:]
    db_file = Path(__file__).resolve().parent.parent / db_path

    if not db_file.exists():
        print(f"[migrate] Database file not found at {db_file}; skipping.")
        return

    async with engine.connect() as conn:
        tables = await conn.run_sync(lambda sync_conn: sa_inspect(sync_conn).get_table_names())

    if "users" not in tables:
        print("[migrate] users table not found; create_all will handle it.")
        return

    conn = sqlite3.connect(str(db_file))
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        existing = {row[1] for row in cursor.fetchall()}
        if "token_version" in existing:
            print("[migrate] users.token_version already exists; nothing to do.")
            return
        cursor.execute("ALTER TABLE users ADD COLUMN token_version INTEGER NOT NULL DEFAULT 0")
        conn.commit()
        print("[migrate] users.token_version: added (INTEGER NOT NULL DEFAULT 0).")
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())

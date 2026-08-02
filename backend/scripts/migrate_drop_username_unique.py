"""
迁移脚本：移除 users.username 的唯一索引（用户名可重复）。

背景：
    2026-08 起登录统一以邮箱为唯一登录标识，用户名不再参与登录、
    允许重复，因此删除数据库上的 UNIQUE 索引 ix_users_username，
    并重建为普通（非唯一）索引，与 ORM 模型（index=True）保持一致。

使用方式：
    cd backend && python -m scripts.migrate_drop_username_unique

回滚（恢复用户名唯一）：
    DROP INDEX ix_users_username;
    CREATE UNIQUE INDEX ix_users_username ON users (username);
"""

import sqlite3
from pathlib import Path

from app.config import get_settings


def main() -> None:
    settings = get_settings()
    db_url = settings.DATABASE_URL

    # 仅支持 SQLite；其他数据库（如 PostgreSQL）应使用 Alembic
    if not db_url.startswith("sqlite"):
        print("[migrate] Non-SQLite database; skipping.")
        return

    # 从连接 URL 中提取数据库文件路径，例如 "sqlite:///./data.db" -> "data.db"
    db_path = db_url.split(":///", 1)[-1]
    if db_path.startswith("./"):
        db_path = db_path[2:]

    # 以脚本文件位置为基准，拼接到 backend/ 目录下的数据库文件路径
    db_file = Path(__file__).resolve().parent.parent / db_path

    if not db_file.exists():
        print(f"[migrate] Database file not found at {db_file}; skipping.")
        return

    conn = sqlite3.connect(str(db_file))
    try:
        cursor = conn.cursor()
        # 删除旧的唯一索引，重建为普通索引（与模型 index=True 对齐）
        cursor.execute("DROP INDEX IF EXISTS ix_users_username")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ix_users_username ON users (username)"
        )
        conn.commit()
        print("[migrate] ix_users_username: UNIQUE -> non-unique (username may repeat).")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

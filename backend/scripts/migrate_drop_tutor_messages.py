"""
一次性迁移脚本：物理删除 deck_tutor_messages 表。

背景：
    导师会话已改为完全不持久化（对话历史由前端随请求携带注入 LLM 上下文），
    deck_tutor_messages 表不再被任何代码读写，成为死物。本脚本按项目
    「旧系统表物理删除」先例（AGENTS.md）将其 DROP。

幂等性：
    DROP TABLE IF EXISTS 可重复执行；表已不存在时无操作。

回滚说明：
    如需恢复，重新创建空表即可（结构与原模型一致）：

    CREATE TABLE deck_tutor_messages (
        id VARCHAR(36) NOT NULL PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL REFERENCES users (id),
        role VARCHAR(10) NOT NULL,
        mode VARCHAR(10) NOT NULL,
        text TEXT NOT NULL,
        grade VARCHAR(10),
        created_at DATETIME,
        FOREIGN KEY(user_id) REFERENCES users (id)
    );
    CREATE INDEX ix_deck_tutor_messages_user_id
        ON deck_tutor_messages (user_id);

用法：
    cd backend && python -m scripts.migrate_drop_tutor_messages
"""

import asyncio
import sqlite3
from pathlib import Path

from app.config import get_settings


def _db_file() -> Path:
    """从 DATABASE_URL 解析 SQLite 数据库文件路径（backend/ 目录下）。"""
    settings = get_settings()
    db_url = settings.DATABASE_URL
    if not db_url.startswith("sqlite"):
        raise SystemExit(f"[migrate] 非 SQLite 数据库（{db_url}），请改用 Alembic。")
    db_path = db_url.split(":///", 1)[-1]
    if db_path.startswith("./"):
        db_path = db_path[2:]
    return Path(__file__).resolve().parent.parent / db_path


async def migrate_drop_tutor_messages() -> None:
    """执行迁移：DROP TABLE IF EXISTS deck_tutor_messages，打印执行结果。"""
    db_file = _db_file()
    if not db_file.exists():
        print(f"[migrate] 数据库文件不存在：{db_file}；跳过。")
        return

    conn = sqlite3.connect(str(db_file))
    try:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS deck_tutor_messages")
        dropped = cursor.rowcount
        conn.commit()
        print(f"[migrate] done: dropped_table=deck_tutor_messages, rows_affected={dropped}")
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(migrate_drop_tutor_messages())

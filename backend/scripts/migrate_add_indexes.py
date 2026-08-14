"""
迁移脚本：为高频查询表添加复合索引（安全/性能审计修复）。

背景：
    2026-08 安全与性能审计发现以下表缺少复合索引，导致"最近 N 条"、
    HLR 重放、排行榜等查询随数据增长退化为全表扫描 + 临时排序：
      - deck_mastery_events:    (user_id, kp_id, created_at) / (user_id, created_at)
      - deck_review_attempts:   (user_id, created_at)
      - deck_arena_attempts:    (user_id, created_at)
      - deck_core_transactions: (user_id, created_at)
      - deck_feed_events:       (user_id, created_at)
      - deck_arena_ratings:     (rating)

    ORM 模型的 __table_args__ 已声明这些索引，create_all 只会为新库建索引；
    已有 data.db 需要本脚本补建。

幂等性：
    每个索引先查 sqlite_master 是否存在，存在即跳过；重复执行无副作用。

回滚：
    DROP INDEX 对应索引名即可，纯性能优化无数据影响。

用法：
    cd backend && python -m scripts.migrate_add_indexes
"""

import asyncio
import sqlite3
from pathlib import Path

from app.config import get_settings

# 待建索引：(表名, 索引名, 列定义 SQL, 可选 WHERE 子句, 是否 UNIQUE)
# 安全审计修复：uq_deck_arena_attempts_solved_once 为 partial unique index
# （WHERE solved=1），数据库层保证同一 (用户, 挑战) 至多一条已攻克记录，
# 兜底并发双击 TOCTOU 竞态。其余为普通性能索引——必须保持非 UNIQUE，
# 否则 (user_id, created_at) 等列组合会拒绝同一时间戳的多条事件
# （Windows 时钟粒度 ~15.6ms，定级测试循环写 13 条事件极易撞同值）。
INDEXES = [
    ("deck_mastery_events", "ix_deck_mastery_events_user_kp_created",
     "(user_id, kp_id, created_at)", None, False),
    ("deck_mastery_events", "ix_deck_mastery_events_user_created",
     "(user_id, created_at)", None, False),
    ("deck_review_attempts", "ix_deck_review_attempts_user_created",
     "(user_id, created_at)", None, False),
    ("deck_arena_attempts", "ix_deck_arena_attempts_user_created",
     "(user_id, created_at)", None, False),
    ("deck_core_transactions", "ix_deck_core_transactions_user_created",
     "(user_id, created_at)", None, False),
    ("deck_feed_events", "ix_deck_feed_events_user_created",
     "(user_id, created_at)", None, False),
    ("deck_arena_ratings", "ix_deck_arena_ratings_rating", "(rating)", None, False),
    ("deck_arena_attempts", "uq_deck_arena_attempts_solved_once",
     "(user_id, challenge_id)", "solved = 1", True),
]


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


async def migrate_add_indexes() -> None:
    """为已有数据库补建复合索引（幂等）。"""
    db_file = _db_file()
    if not db_file.exists():
        print(f"[migrate] 数据库文件不存在：{db_file}；跳过。")
        return

    conn = sqlite3.connect(str(db_file))
    try:
        cursor = conn.cursor()
        created = 0
        for table, index_name, columns, where, unique in INDEXES:
            # 检查表与索引是否存在（幂等）
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if cursor.fetchone() is None:
                print(f"[migrate] 表 {table} 不存在，跳过索引 {index_name}。")
                continue
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name=?", (index_name,))
            if cursor.fetchone() is not None:
                continue
            keyword = "CREATE UNIQUE INDEX" if unique else "CREATE INDEX"
            sql = f"{keyword} {index_name} ON {table} {columns}"
            if where:
                sql += f" WHERE {where}"
            cursor.execute(sql)
            created += 1
            print(f"[migrate] {table}.{index_name}: created")
        conn.commit()
        print(f"[migrate] done: indexes_created={created}")
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(migrate_add_indexes())

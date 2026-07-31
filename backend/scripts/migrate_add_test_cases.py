"""
迁移脚本：为 deck_arena_challenges / deck_cert_questions 增加 test_cases 列，
并按种子数据回填全部挑战/题目的测试用例（Judge0 判题用）。

背景：
    竞技场与认证 code 题此前用关键字匹配判题，数据库没有测试用例数据。
    接入 Judge0 真判题后每道题需要一份 [{"input", "expected_output"}]，
    但 seed_deck 幂等（知识点表非空即跳过），已有数据库不会自动获得新列
    和新数据，因此需要本脚本一次性补齐。

回滚说明：
    - 新增列：test_cases 为纯增量列（JSON，可空），不影响既有数据与查询；
      旧版 SQLite 不支持 DROP COLUMN，如确需移除请备份后重建表。
    - 回填数据：UPDATE 只覆盖 test_cases 列，不触碰其他列；按
      challenge id / (exam_id, qid) 匹配，重复执行结果一致（幂等）。

用法：
    cd backend && python -m scripts.migrate_add_test_cases
"""

import asyncio
import json
import sqlite3
from pathlib import Path

from app.config import get_settings
from app.training.seed import ARENA_CHALLENGES, CERT_QUESTIONS


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


def _add_column_if_missing(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    """检查列是否存在，缺失则 ALTER TABLE ADD COLUMN（JSON，可空）。

    Returns:
        True 表示本次新增了列。
    """
    cursor.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cursor.fetchall()}
    if column in existing:
        return False
    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} JSON NULL")
    print(f"[migrate] {table}.{column}: added")
    return True


async def migrate_add_test_cases() -> None:
    """执行迁移：加列 + 回填测试用例。

    执行流程：
        1. 定位 SQLite 数据库文件（仅支持 SQLite，其他库请用 Alembic）
        2. 为两张表补充 test_cases 列（缺失时）
        3. 按种子数据回填：竞技场按 challenge id、认证题按 (exam_id, qid)
        4. 提交事务并打印统计
    """
    db_file = _db_file()
    if not db_file.exists():
        print(f"[migrate] 数据库文件不存在：{db_file}；跳过。")
        return

    conn = sqlite3.connect(str(db_file))
    try:
        cursor = conn.cursor()
        added_columns = 0

        # ── 步骤 1：补列 ──
        if _add_column_if_missing(cursor, "deck_arena_challenges", "test_cases"):
            added_columns += 1
        if _add_column_if_missing(cursor, "deck_cert_questions", "test_cases"):
            added_columns += 1

        # ── 步骤 2：回填竞技场挑战测试用例（按 challenge id 匹配）──
        arena_updated = 0
        for c in ARENA_CHALLENGES:
            test_cases = c.get("test_cases") or []
            cursor.execute(
                "UPDATE deck_arena_challenges SET test_cases = ? WHERE id = ?",
                (json.dumps(test_cases, ensure_ascii=False), c["id"]),
            )
            arena_updated += cursor.rowcount

        # ── 步骤 3：回填认证 code 题测试用例（按 exam_id + qid 匹配）──
        cert_updated = 0
        for row in CERT_QUESTIONS:
            test_cases = row[8]  # 第 10 个字段：test_cases（mcq 为 None）
            if not test_cases:
                continue
            cursor.execute(
                "UPDATE deck_cert_questions SET test_cases = ? WHERE exam_id = ? AND qid = ?",
                (json.dumps(test_cases, ensure_ascii=False), row[0], row[1]),
            )
            cert_updated += cursor.rowcount

        conn.commit()
        print(
            f"[migrate] done: columns_added={added_columns}, "
            f"arena_test_cases_backfilled={arena_updated}, "
            f"cert_test_cases_backfilled={cert_updated}"
        )
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(migrate_add_test_cases())

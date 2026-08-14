"""
迁移脚本：将 seed.py 中的训练舱内容（审查关卡/竞技场挑战/认证考试与题目）
幂等同步进已有数据库。

背景：
    seed_deck 幂等（知识点表非空即跳过），已有数据库不会自动获得新增的种子内容，
    也不会获得对既有题目的修订（缺陷修正、答案订正、文案勘误等）。

同步语义（upsert，重复执行结果一致）：
    - 按主键（审查关卡 id、竞技场 id、考试 id、(exam_id, qid)）缺失的行：INSERT
    - 已存在的行：以 seed.py 为准 UPDATE 内容字段（含审查关卡的缺陷子表重建）
    - 不触碰任何用户数据（尝试记录、掌握度事件、证书等）

注意：
    本脚本不建新列。若模型新增过列（如 deck_arena_challenges.related_weakness），
    先跑 `python -m scripts.migrate_missing_columns`（start_services 启动时会自动跑），
    本脚本检测到列缺失时会跳过该列并打印提示。

用法：
    cd backend && python -m scripts.migrate_backfill_deck_content
"""

import json
import sqlite3
import uuid
from pathlib import Path

from app.config import get_settings
from app.training.seed import (
    ARENA_CHALLENGES,
    CERT_EXAMS,
    CERT_QUESTIONS,
    REVIEW_SESSIONS,
)


def _db_file() -> Path:
    """从 DATABASE_URL 解析 SQLite 数据库文件路径（backend/ 目录下）。"""
    settings = get_settings()
    db_url = settings.DATABASE_URL
    if not db_url.startswith("sqlite"):
        raise SystemExit(f"[backfill] 非 SQLite 数据库（{db_url}），请改用 Alembic。")
    db_path = db_url.split(":///", 1)[-1]
    if db_path.startswith("./"):
        db_path = db_path[2:]
    return Path(__file__).resolve().parent.parent / db_path


def _existing_ids(cursor: sqlite3.Cursor, table: str, id_col: str) -> set:
    cursor.execute(f"SELECT {id_col} FROM {table}")
    return {row[0] for row in cursor.fetchall()}


def _table_columns(cursor: sqlite3.Cursor, table: str) -> set[str]:
    """读取表的实际列名（用于对缺失的新列降级跳过）。"""
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def sync_review_sessions(cursor: sqlite3.Cursor) -> tuple[int, int]:
    """同步审查关卡 + 注入缺陷（先父后子，处理外键）。

    既有关卡的缺陷子表按 seed 重建（DELETE + INSERT）：缺陷行没有
    用户数据外键引用（尝试记录的 marks/verdict 是 JSON 快照），重建安全。
    """
    columns = _table_columns(cursor, "deck_review_sessions")
    has_weakness = "related_weakness" in columns
    if not has_weakness:
        print("[backfill] deck_review_sessions 缺 related_weakness 列，"
              "请先跑 python -m scripts.migrate_missing_columns；本次跳过该列")
    existing = _existing_ids(cursor, "deck_review_sessions", "id")
    inserted = updated = 0
    for s in REVIEW_SESSIONS:
        if s["id"] in existing:
            if has_weakness:
                cursor.execute(
                    "UPDATE deck_review_sessions SET title=?, language=?, code=?, "
                    "defect_count=?, difficulty=?, eta_minutes=?, related_weakness=? "
                    "WHERE id=?",
                    (s["title"], s["language"], s["code"], s["defect_count"],
                     s["difficulty"], s["eta_minutes"], s["related_weakness"], s["id"]),
                )
            else:
                cursor.execute(
                    "UPDATE deck_review_sessions SET title=?, language=?, code=?, "
                    "defect_count=?, difficulty=?, eta_minutes=? WHERE id=?",
                    (s["title"], s["language"], s["code"], s["defect_count"],
                     s["difficulty"], s["eta_minutes"], s["id"]),
                )
            cursor.execute(
                "DELETE FROM deck_injected_defects WHERE session_id=?", (s["id"],)
            )
            updated += 1
        else:
            if has_weakness:
                cursor.execute(
                    "INSERT INTO deck_review_sessions (id, title, language, code, "
                    "defect_count, difficulty, eta_minutes, related_weakness) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (s["id"], s["title"], s["language"], s["code"], s["defect_count"],
                     s["difficulty"], s["eta_minutes"], s["related_weakness"]),
                )
            else:
                cursor.execute(
                    "INSERT INTO deck_review_sessions (id, title, language, code, "
                    "defect_count, difficulty, eta_minutes) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (s["id"], s["title"], s["language"], s["code"], s["defect_count"],
                     s["difficulty"], s["eta_minutes"]),
                )
            inserted += 1
        for line, dtype, explanation in s["defects"]:
            cursor.execute(
                "INSERT INTO deck_injected_defects (id, session_id, line, type, explanation) "
                "VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), s["id"], line, dtype, explanation),
            )
    return inserted, updated


def sync_arena(cursor: sqlite3.Cursor) -> tuple[int, int]:
    """同步竞技场挑战（含 related_weakness 知识点映射）。"""
    columns = _table_columns(cursor, "deck_arena_challenges")
    has_weakness = "related_weakness" in columns
    if not has_weakness:
        print("[backfill] deck_arena_challenges 缺 related_weakness 列，"
              "请先跑 python -m scripts.migrate_missing_columns；本次跳过该列")
    existing = _existing_ids(cursor, "deck_arena_challenges", "id")
    inserted = updated = 0
    for c in ARENA_CHALLENGES:
        test_cases_json = json.dumps(c.get("test_cases") or [], ensure_ascii=False)
        if c["id"] in existing:
            if has_weakness:
                cursor.execute(
                    "UPDATE deck_arena_challenges SET title=?, language=?, code=?, "
                    "failing_output=?, test_cases=?, time_limit_sec=?, difficulty=?, "
                    "related_weakness=? WHERE id=?",
                    (c["title"], c["language"], c["code"], c["failing_output"],
                     test_cases_json, c["time_limit_sec"], c["difficulty"],
                     c.get("related_weakness"), c["id"]),
                )
            else:
                cursor.execute(
                    "UPDATE deck_arena_challenges SET title=?, language=?, code=?, "
                    "failing_output=?, test_cases=?, time_limit_sec=?, difficulty=? "
                    "WHERE id=?",
                    (c["title"], c["language"], c["code"], c["failing_output"],
                     test_cases_json, c["time_limit_sec"], c["difficulty"], c["id"]),
                )
            updated += 1
        else:
            if has_weakness:
                cursor.execute(
                    "INSERT INTO deck_arena_challenges (id, title, language, code, "
                    "failing_output, test_cases, time_limit_sec, difficulty, "
                    "related_weakness) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (c["id"], c["title"], c["language"], c["code"], c["failing_output"],
                     test_cases_json, c["time_limit_sec"], c["difficulty"],
                     c.get("related_weakness")),
                )
            else:
                cursor.execute(
                    "INSERT INTO deck_arena_challenges (id, title, language, code, "
                    "failing_output, test_cases, time_limit_sec, difficulty) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (c["id"], c["title"], c["language"], c["code"], c["failing_output"],
                     test_cases_json, c["time_limit_sec"], c["difficulty"]),
                )
            inserted += 1
    return inserted, updated


def sync_cert(cursor: sqlite3.Cursor) -> tuple[int, int, int, int]:
    """同步认证考试 + 题目（先 exam 后 question）。"""
    exam_existing = _existing_ids(cursor, "deck_cert_exams", "id")
    exams_inserted = exams_updated = 0
    for exam_id, topic, limit_min, pass_score in CERT_EXAMS:
        if exam_id in exam_existing:
            cursor.execute(
                "UPDATE deck_cert_exams SET topic=?, time_limit_min=?, pass_score=? "
                "WHERE id=?",
                (topic, limit_min, pass_score, exam_id),
            )
            exams_updated += 1
        else:
            cursor.execute(
                "INSERT INTO deck_cert_exams (id, topic, time_limit_min, pass_score) "
                "VALUES (?, ?, ?, ?)",
                (exam_id, topic, limit_min, pass_score),
            )
            exams_inserted += 1

    # 已有题目键：查询所有 (exam_id, qid)
    cursor.execute("SELECT exam_id, qid FROM deck_cert_questions")
    existing_q = {(r[0], r[1]) for r in cursor.fetchall()}
    questions_inserted = questions_updated = 0
    for row in CERT_QUESTIONS:
        exam_id, qid, kind, prompt, options, starter, ans_correct, ans_inc, tc, sort_order = row
        options_json = json.dumps(options, ensure_ascii=False) if options else None
        includes_json = json.dumps(ans_inc, ensure_ascii=False) if ans_inc else None
        cases_json = json.dumps(tc, ensure_ascii=False) if tc else None
        if (exam_id, qid) in existing_q:
            cursor.execute(
                "UPDATE deck_cert_questions SET kind=?, prompt=?, options=?, "
                "starter_code=?, answer_correct=?, answer_includes=?, test_cases=?, "
                "sort_order=? WHERE exam_id=? AND qid=?",
                (kind, prompt, options_json, starter, ans_correct, includes_json,
                 cases_json, sort_order, exam_id, qid),
            )
            questions_updated += 1
        else:
            cursor.execute(
                "INSERT INTO deck_cert_questions (id, exam_id, qid, kind, prompt, options, "
                "starter_code, answer_correct, answer_includes, test_cases, sort_order) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), exam_id, qid, kind, prompt, options_json, starter,
                 ans_correct, includes_json, cases_json, sort_order),
            )
            questions_inserted += 1
    return exams_inserted, exams_updated, questions_inserted, questions_updated


def main() -> None:
    db_file = _db_file()
    if not db_file.exists():
        print(f"[backfill] 数据库文件不存在：{db_file}；跳过。")
        return

    conn = sqlite3.connect(str(db_file))
    try:
        cursor = conn.cursor()
        review_ins, review_upd = sync_review_sessions(cursor)
        arena_ins, arena_upd = sync_arena(cursor)
        exams_ins, exams_upd, q_ins, q_upd = sync_cert(cursor)
        conn.commit()
        print(
            f"[backfill] done: "
            f"review_sessions +{review_ins} ~{review_upd}, "
            f"arena_challenges +{arena_ins} ~{arena_upd}, "
            f"cert_exams +{exams_ins} ~{exams_upd}, "
            f"cert_questions +{q_ins} ~{q_upd}  （+新增 ~更新）"
        )
    finally:
        conn.close()


if __name__ == "__main__":
    main()

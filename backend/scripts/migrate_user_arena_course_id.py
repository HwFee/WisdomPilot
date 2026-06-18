"""
One-off migration: add course_id column to user_arena_profiles if missing.

The column was added to the UserArenaProfile model but existing SQLite databases
may not have it. This script safely adds the column when missing.
"""

import asyncio
import sqlite3
from pathlib import Path

from app.config import get_settings


async def add_course_id_column() -> None:
    settings = get_settings()
    db_url = settings.DATABASE_URL

    if not db_url.startswith("sqlite"):
        print("[migrate] Non-SQLite database; skipping manual migration.")
        return

    # Extract file path from sqlite+aiosqlite:///./data/data.db or sqlite:///./data/data.db
    db_path = db_url.split(":///", 1)[-1]
    if db_path.startswith("./"):
        db_path = db_path[2:]
    db_file = Path(__file__).resolve().parent.parent / db_path

    if not db_file.exists():
        print(f"[migrate] Database file not found at {db_file}; skipping.")
        return

    conn = sqlite3.connect(str(db_file))
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(user_arena_profiles)")
        columns = {row[1] for row in cursor.fetchall()}

        if "course_id" in columns:
            print("[migrate] course_id column already exists.")
            return

        cursor.execute("ALTER TABLE user_arena_profiles ADD COLUMN course_id INTEGER")
        conn.commit()
        print("[migrate] Added course_id column to user_arena_profiles.")
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(add_course_id_column())

"""
迁移脚本：更新 favorites 表结构
添加新字段以支持完整信息存储（类似错题本）
"""

import asyncio
import sqlite3

def migrate():
    """执行迁移"""
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    # 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='favorites'")
    if not cursor.fetchone():
        print("favorites 表不存在，将创建新表")
        cursor.execute('''
            CREATE TABLE favorites (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                exercise_key TEXT,
                exercise_id INTEGER,
                course_id INTEGER,
                chapter_id INTEGER,
                source_type TEXT,
                exercise_content TEXT,
                exercise_type TEXT,
                exercise_difficulty INTEGER,
                knowledge_points TEXT,
                folder TEXT,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        print("迁移完成：创建新表")
        return

    # 获取现有列
    cursor.execute("PRAGMA table_info(favorites)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    print(f"现有列: {existing_columns}")

    # 需要添加的新列
    new_columns = [
        ("exercise_key", "TEXT"),
        ("course_id", "INTEGER"),
        ("source_type", "TEXT"),
        ("exercise_content", "TEXT"),
        ("exercise_type", "TEXT"),
        ("exercise_difficulty", "INTEGER"),
        ("knowledge_points", "TEXT"),
    ]

    for col_name, col_type in new_columns:
        if col_name not in existing_columns:
            print(f"添加列: {col_name}")
            cursor.execute(f"ALTER TABLE favorites ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()
    print("迁移完成")

if __name__ == "__main__":
    migrate()

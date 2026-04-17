"""
数据库迁移脚本：更新 favorites 表结构，使其与 wrong_questions 完全一致

运行方式：
cd backend
python migrate_favorites_v2.py
"""

import asyncio
import sqlite3
from pathlib import Path


def migrate():
    """同步迁移 favorites 表"""
    db_path = Path(__file__).parent / "data.db"

    if not db_path.exists():
        print("数据库文件不存在，跳过迁移")
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 检查 favorites 表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='favorites'")
    if not cursor.fetchone():
        print("favorites 表不存在，跳过迁移")
        conn.close()
        return

    # 获取现有列
    cursor.execute("PRAGMA table_info(favorites)")
    existing_columns = {row[1]: row[2] for row in cursor.fetchall()}

    print(f"现有列: {list(existing_columns.keys())}")

    # 需要添加的列（如果不存在）
    columns_to_add = []

    # 确保关键字段存在
    if 'knowledge_points' not in existing_columns:
        columns_to_add.append("ALTER TABLE favorites ADD COLUMN knowledge_points JSON DEFAULT '[]'")
    if 'exercise_type' not in existing_columns:
        columns_to_add.append("ALTER TABLE favorites ADD COLUMN exercise_type VARCHAR(20) DEFAULT 'choice'")
    if 'exercise_difficulty' not in existing_columns:
        columns_to_add.append("ALTER TABLE favorites ADD COLUMN exercise_difficulty INTEGER DEFAULT 1")

    # 删除不再需要的列（source_type - 现在通过 exercise_key 推断）
    # SQLite 不支持 DROP COLUMN，但我们不再使用 source_type

    for sql in columns_to_add:
        try:
            cursor.execute(sql)
            print(f"执行: {sql}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                print(f"警告: {e}")

    conn.commit()
    conn.close()
    print("迁移完成！")


if __name__ == "__main__":
    migrate()

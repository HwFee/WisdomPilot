"""
Migration: Add columns to notes table

This migration:
1. Adds tags column (JSON array)
2. Adds knowledge_points column (JSON array)
3. Adds source column (text, default 'manual')
4. Creates note_tags table
"""

import sqlite3
import os


def migrate(db_path: str):
    """Run the migration"""
    print(f"Migrating database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if migration is needed
    cursor.execute("PRAGMA table_info(notes)")
    columns = {col[1]: col[2] for col in cursor.fetchall()}

    print(f"Current notes columns: {list(columns.keys())}")

    if 'tags' in columns and 'knowledge_points' in columns and 'source' in columns:
        print("Migration already applied (all new columns exist)")
        conn.close()
        return

    # Add missing columns to notes table
    if 'tags' not in columns:
        print("Adding 'tags' column...")
        cursor.execute("ALTER TABLE notes ADD COLUMN tags TEXT DEFAULT '[]'")

    if 'knowledge_points' not in columns:
        print("Adding 'knowledge_points' column...")
        cursor.execute("ALTER TABLE notes ADD COLUMN knowledge_points TEXT DEFAULT '[]'")

    if 'source' not in columns:
        print("Adding 'source' column...")
        cursor.execute("ALTER TABLE notes ADD COLUMN source TEXT DEFAULT 'manual'")

    # Create note_tags table
    print("Creating note_tags table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS note_tags (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            color TEXT DEFAULT '#6366f1',
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Create index
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_note_tags_user ON note_tags(user_id)")

    conn.commit()
    conn.close()

    print("Migration completed successfully!")


if __name__ == "__main__":
    # Default database path
    db_path = os.path.join(os.path.dirname(__file__), "data.db")

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        print("Please specify the correct path to data.db")
        exit(1)

    migrate(db_path)

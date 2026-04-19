"""
Migration script: Add cores columns, remove ai_quota columns

Run this script to migrate the database schema:
    python scripts/migrate_cores.py
"""

import sqlite3
import os
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def migrate_database(db_path: str = "data.db"):
    """Migrate the database to add cores columns and remove ai_quota columns."""

    if not os.path.exists(db_path):
        print(f"[ERROR] Database file not found: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check current columns
        cursor.execute("PRAGMA table_info(users)")
        columns = {row[1]: row for row in cursor.fetchall()}
        print(f"[INFO] Current columns: {list(columns.keys())}")

        changes = []

        # Add cores column if not exists
        if "cores" not in columns:
            print("[ADD] Adding 'cores' column...")
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN cores INTEGER DEFAULT 100")
                changes.append("Added 'cores' column")
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e).lower():
                    raise
                print("[SKIP] 'cores' column already exists")

        # Add cores_total_earned column if not exists
        if "cores_total_earned" not in columns:
            print("[ADD] Adding 'cores_total_earned' column...")
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN cores_total_earned INTEGER DEFAULT 100")
                changes.append("Added 'cores_total_earned' column")
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e).lower():
                    raise
                print("[SKIP] 'cores_total_earned' column already exists")

        # Add cores_total_spent column if not exists
        if "cores_total_spent" not in columns:
            print("[ADD] Adding 'cores_total_spent' column...")
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN cores_total_spent INTEGER DEFAULT 0")
                changes.append("Added 'cores_total_spent' column")
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e).lower():
                    raise
                print("[SKIP] 'cores_total_spent' column already exists")

        # Migrate data: copy ai_quota to cores if ai_quota exists
        if "ai_quota" in columns:
            print("[MIGRATE] Copying ai_quota values to cores...")
            cursor.execute("UPDATE users SET cores = COALESCE(ai_quota, 100) WHERE cores IS NULL")
            cursor.execute("UPDATE users SET cores = COALESCE(ai_quota, 100)")
            cursor.execute("UPDATE users SET cores_total_earned = cores")
            changes.append("Migrated ai_quota values to cores")

        conn.commit()

        # Verify the migration
        cursor.execute("PRAGMA table_info(users)")
        new_columns = {row[1]: row for row in cursor.fetchall()}
        print(f"\n[OK] Migration complete!")
        print(f"[INFO] Columns: {list(new_columns.keys())}")

        for change in changes:
            print(f"  - {change}")

        return True

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()


def verify_migration(db_path: str = "data.db"):
    """Verify that the migration was successful."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(users)")
        columns = {row[1]: row for row in cursor.fetchall()}

        required = ["cores", "cores_total_earned", "cores_total_spent"]
        missing = [col for col in required if col not in columns]

        if missing:
            print(f"[ERROR] Missing columns: {missing}")
            return False

        # Check data
        cursor.execute("SELECT id, username, cores, cores_total_earned, cores_total_spent FROM users LIMIT 3")
        users = cursor.fetchall()

        print("\n[DATA] Sample user data after migration:")
        for user in users:
            print(f"  - {user[1]}: cores={user[2]}, earned={user[3]}, spent={user[4]}")

        return True

    finally:
        conn.close()


if __name__ == "__main__":
    # Get database path
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data.db"

    print(f"[MIGRATE] Database: {db_path}\n")

    if migrate_database(db_path):
        verify_migration(db_path)

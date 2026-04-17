"""
Migration: Remove session_id from ArenaExerciseProgress

This migration:
1. Removes the session_id column (no longer needed - no session concept)
2. Adds unique constraint on (user_id, course_id, exercise_id)
3. Cleans up duplicate records (keep the most recent one per exercise)
"""

import sqlite3
import os

def migrate(db_path: str):
    """Run the migration"""
    print(f"Migrating database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if migration is needed
    cursor.execute("PRAGMA table_info(arena_exercise_progress)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'session_id' not in columns:
        print("Migration already applied (no session_id column found)")
        conn.close()
        return

    print("Step 1: Deduplicating records...")

    # Find duplicates (same user, course, exercise)
    cursor.execute("""
        SELECT user_id, course_id, exercise_id, COUNT(*) as cnt
        FROM arena_exercise_progress
        GROUP BY user_id, course_id, exercise_id
        HAVING cnt > 1
    """)
    duplicates = cursor.fetchall()

    for user_id, course_id, exercise_id, count in duplicates:
        # Keep the most recent record (highest updated_at)
        cursor.execute("""
            DELETE FROM arena_exercise_progress
            WHERE user_id = ? AND course_id = ? AND exercise_id = ?
            AND id NOT IN (
                SELECT id FROM arena_exercise_progress
                WHERE user_id = ? AND course_id = ? AND exercise_id = ?
                ORDER BY updated_at DESC
                LIMIT 1
            )
        """, (user_id, course_id, exercise_id, user_id, course_id, exercise_id))
        print(f"  Removed {cursor.rowcount} duplicate(s) for exercise {exercise_id}")

    print("Step 2: Creating new table without session_id...")

    # Create new table with desired structure
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS arena_exercise_progress_new (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            exercise_id INTEGER NOT NULL,
            exercise_index INTEGER NOT NULL,
            is_completed INTEGER DEFAULT 0,
            is_correct INTEGER DEFAULT 0,
            is_unlocked INTEGER DEFAULT 0,
            saved_codes TEXT DEFAULT '{}',
            current_language TEXT DEFAULT 'python',
            first_attempt_at TEXT,
            last_attempt_at TEXT,
            correct_at TEXT,
            attempt_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (course_id) REFERENCES courses(id),
            FOREIGN KEY (exercise_id) REFERENCES exercises(id)
        )
    """)

    # Copy data (excluding session_id)
    cursor.execute("""
        INSERT INTO arena_exercise_progress_new
        (id, user_id, course_id, exercise_id, exercise_index,
         is_completed, is_correct, is_unlocked, saved_codes, current_language,
         first_attempt_at, last_attempt_at, correct_at, attempt_count,
         created_at, updated_at)
        SELECT id, user_id, course_id, exercise_id, exercise_index,
               is_completed, is_correct, is_unlocked, saved_codes, current_language,
               first_attempt_at, last_attempt_at, correct_at, attempt_count,
               created_at, updated_at
        FROM arena_exercise_progress
    """)

    print(f"  Copied {cursor.rowcount} records")

    # Drop old table and rename new one
    cursor.execute("DROP TABLE arena_exercise_progress")
    cursor.execute("ALTER TABLE arena_exercise_progress_new RENAME TO arena_exercise_progress")

    print("Step 3: Creating indexes and constraints...")

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_arena_user ON arena_exercise_progress(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_arena_course ON arena_exercise_progress(course_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_arena_exercise ON arena_exercise_progress(exercise_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_arena_user_course ON arena_exercise_progress(user_id, course_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_arena_user_course_index ON arena_exercise_progress(user_id, course_id, exercise_index)")

    # Create unique constraint (SQLite uses UNIQUE index for this)
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_arena_user_course_exercise
        ON arena_exercise_progress(user_id, course_id, exercise_id)
    """)

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

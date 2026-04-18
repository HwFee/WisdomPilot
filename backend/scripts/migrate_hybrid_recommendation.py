"""
Migration script to add hybrid recommendation fields.

Run: python scripts/migrate_hybrid_recommendation.py

Note: SQLite doesn't support COMMENT syntax, so we use simpler ALTER TABLE statements.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine, Base
from app.models import *  # Import all models


async def migrate():
    """Add new columns for hybrid recommendation system."""
    print("Starting hybrid recommendation migration...")

    async with engine.begin() as conn:
        # Exercise model: add extracted_tags and tag_embedding
        print("Adding extracted_tags and tag_embedding to exercises table...")
        try:
            await conn.execute(
                text("ALTER TABLE exercises ADD COLUMN extracted_tags JSON NULL")
            )
            print("  - Added extracted_tags column")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("  - extracted_tags column already exists, skipping")
            else:
                print(f"  - Error adding extracted_tags: {e}")

        try:
            await conn.execute(
                text("ALTER TABLE exercises ADD COLUMN tag_embedding TEXT NULL")
            )
            print("  - Added tag_embedding column")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("  - tag_embedding column already exists, skipping")
            else:
                print(f"  - Error adding tag_embedding: {e}")

        # ArenaExerciseProgress: add time_spent, hint_used, first_attempt_correct
        print("Adding behavior tracking columns to arena_exercise_progress table...")
        try:
            await conn.execute(
                text("ALTER TABLE arena_exercise_progress ADD COLUMN time_spent INTEGER NULL")
            )
            print("  - Added time_spent column")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("  - time_spent column already exists, skipping")
            else:
                print(f"  - Error adding time_spent: {e}")

        try:
            await conn.execute(
                text("ALTER TABLE arena_exercise_progress ADD COLUMN hint_used BOOLEAN DEFAULT 0")
            )
            print("  - Added hint_used column")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("  - hint_used column already exists, skipping")
            else:
                print(f"  - Error adding hint_used: {e}")

        try:
            await conn.execute(
                text("ALTER TABLE arena_exercise_progress ADD COLUMN first_attempt_correct BOOLEAN NULL")
            )
            print("  - Added first_attempt_correct column")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("  - first_attempt_correct column already exists, skipping")
            else:
                print(f"  - Error adding first_attempt_correct: {e}")

        # UserArenaProfile: add behavior_embedding, avg_time_spent, total_submissions
        print("Adding profile embedding columns to user_arena_profiles table...")
        try:
            await conn.execute(
                text("ALTER TABLE user_arena_profiles ADD COLUMN behavior_embedding TEXT NULL")
            )
            print("  - Added behavior_embedding column")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("  - behavior_embedding column already exists, skipping")
            else:
                print(f"  - Error adding behavior_embedding: {e}")

        try:
            await conn.execute(
                text("ALTER TABLE user_arena_profiles ADD COLUMN avg_time_spent FLOAT DEFAULT 0.0")
            )
            print("  - Added avg_time_spent column")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("  - avg_time_spent column already exists, skipping")
            else:
                print(f"  - Error adding avg_time_spent: {e}")

        try:
            await conn.execute(
                text("ALTER TABLE user_arena_profiles ADD COLUMN total_submissions INTEGER DEFAULT 0")
            )
            print("  - Added total_submissions column")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("  - total_submissions column already exists, skipping")
            else:
                print(f"  - Error adding total_submissions: {e}")

    print("\nMigration completed successfully!")
    print("New columns added:")
    print("  - exercises.extracted_tags")
    print("  - exercises.tag_embedding")
    print("  - arena_exercise_progress.time_spent")
    print("  - arena_exercise_progress.hint_used")
    print("  - arena_exercise_progress.first_attempt_correct")
    print("  - user_arena_profiles.behavior_embedding")
    print("  - user_arena_profiles.avg_time_spent")
    print("  - user_arena_profiles.total_submissions")


if __name__ == "__main__":
    asyncio.run(migrate())

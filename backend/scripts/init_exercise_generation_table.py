"""Initialize exercise_generation_sessions table

Run this script to create the exercise_generation_sessions table
for streaming exercise generation feature.
"""

import asyncio
from sqlalchemy import text
from app.database import engine


async def init_exercise_generation_table():
    """Create the exercise_generation_sessions table"""

    async with engine.begin() as conn:
        # Check if table exists
        result = await conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='exercise_generation_sessions'"
        ))
        table_exists = result.scalar_one_or_none()

        if table_exists:
            print("Table 'exercise_generation_sessions' already exists, skipping creation.")
            return

        # Create the table
        create_table_sql = """
        CREATE TABLE exercise_generation_sessions (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL REFERENCES users(id),
            session_type VARCHAR(20) NOT NULL,
            section_id INTEGER,
            chapter_id INTEGER,
            course_id INTEGER,
            request_data JSON DEFAULT '{}',
            total_count INTEGER DEFAULT 0,
            generated_count INTEGER DEFAULT 0,
            generated_exercises JSON DEFAULT '[]',
            status VARCHAR(20) DEFAULT 'generating',
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP DEFAULT (DATETIME('now', '+24 hours'))
        );

        CREATE INDEX idx_generation_sessions_user_id ON exercise_generation_sessions(user_id);
        CREATE INDEX idx_generation_sessions_status ON exercise_generation_sessions(status);
        CREATE INDEX idx_generation_sessions_expires ON exercise_generation_sessions(expires_at);
        """

        await conn.execute(text(create_table_sql))
        print("Table 'exercise_generation_sessions' created successfully.")


if __name__ == "__main__":
    asyncio.run(init_exercise_generation_table())

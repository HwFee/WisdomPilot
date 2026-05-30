"""Tests for database configuration (C7) and foreign key enforcement"""

import pytest
from sqlalchemy import text


class TestSQLiteForeignKeyEnforcement:
    """Test that SQLite foreign key constraints are enforced (C7)"""

    @pytest.mark.asyncio
    async def test_pragma_foreign_keys_is_on_default_engine(self):
        """PRAGMA foreign_keys must be ON for the main engine connections (C7)."""
        from app.database import engine

        async with engine.connect() as conn:
            result = await conn.execute(text("PRAGMA foreign_keys"))
            value = result.scalar()
            assert value == 1, f"PRAGMA foreign_keys = {value}, expected 1"


class TestForeignKeyConstraintWithORM:
    """Test FK enforcement through actual ORM models using the test fixture."""

    @pytest.mark.asyncio
    async def test_chapter_progress_requires_valid_user(self, db_session):
        """ChapterProgress with invalid user_id should fail with IntegrityError."""
        from sqlalchemy.exc import IntegrityError
        from app.models.stats import ChapterProgress

        orphan = ChapterProgress(
            user_id="nonexistent-user-id-00000",
            chapter_id=1,
            status="not_started",
        )
        db_session.add(orphan)

        with pytest.raises(IntegrityError):
            await db_session.flush()
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_login_session_requires_valid_user(self, db_session):
        """LoginSession with invalid user_id should fail with IntegrityError."""
        from sqlalchemy.exc import IntegrityError
        from app.models.session import LoginSession

        orphan = LoginSession(
            user_id="nonexistent-user-id-00000",
            token="test-token-unique-12345",
            is_active=True,
        )
        db_session.add(orphan)

        with pytest.raises(IntegrityError):
            await db_session.flush()
            await db_session.commit()


class TestForeignKeyViaRawQuery:
    """Test FK enforcement via raw SQL."""

    @pytest.mark.asyncio
    async def test_orphaned_login_session_rejected(self, db_session):
        """Inserting a login_session with nonexistent user_id should fail."""
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            await db_session.execute(text(
                "INSERT INTO login_sessions (id, user_id, token, is_active, created_at) "
                "VALUES ('test-id-raw-001', 'nonexistent-user', 'tok-raw-123', 1, '2024-01-01 00:00:00')"
            ))
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_orphaned_activity_log_rejected(self, db_session):
        """Inserting an activity_log with nonexistent user_id should fail."""
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            await db_session.execute(text(
                "INSERT INTO activity_logs (id, user_id, activity_type, description, extra_data, created_at) "
                "VALUES ('test-id-raw-002', 'nonexistent-user', 'test', 'testing', '{}', '2024-01-01 00:00:00')"
            ))
            await db_session.commit()

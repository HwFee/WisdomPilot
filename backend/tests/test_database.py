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
    """Test FK enforcement through a live ORM model (deck_mastery_events -> users)."""

    @pytest.mark.asyncio
    async def test_mastery_event_requires_valid_user(self, db_session):
        """DeckMasteryEvent with invalid user_id should fail with IntegrityError."""
        from sqlalchemy.exc import IntegrityError
        from app.training.models import DeckMasteryEvent

        orphan = DeckMasteryEvent(
            user_id="nonexistent-user-id-00000",
            kp_id="nonexistent-kp-id-00000",
            source="feynman",
            correct=True,
        )
        db_session.add(orphan)

        with pytest.raises(IntegrityError):
            await db_session.flush()
            await db_session.commit()


class TestForeignKeyViaRawQuery:
    """Test FK enforcement via raw SQL on a live table."""

    @pytest.mark.asyncio
    async def test_orphaned_mastery_event_rejected(self, db_session):
        """Inserting a deck_mastery_events row with nonexistent user_id should fail."""
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            await db_session.execute(text(
                "INSERT INTO deck_mastery_events (id, user_id, kp_id, created_at, source, correct, hints_used) "
                "VALUES ('test-id-raw-001', 'nonexistent-user', 'nonexistent-kp', "
                "'2024-01-01 00:00:00', 'feynman', 1, 0)"
            ))
            await db_session.commit()

"""Admin service for user management"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.models import User, LoginSession
from app.utils.time import utc_now

logger = logging.getLogger(__name__)

# Tables with user_id column that need cascade deletion
# Ordered to handle foreign key dependencies (child tables first)
USER_RELATED_TABLES = [
    "login_sessions",
    "activity_logs",
    "learning_sessions",
    "chapter_progress",
    "user_weak_points",
    "spaced_repetition",
    "user_achievements",
    "user_challenges",
    "favorites",
    "notes",
    "chapter_mastery",
    "challenge_sessions",
    "wrong_questions",
    "section_base_questions",
    "user_arena_profiles",
    "arena_exercise_progress",
    "mastery_exercise_progress",
    "section_progress",
    "core_transactions",
    "ai_hint_cache",
    "knowledge_point_mastery",
    "answer_history",
    "section_mastery",
    "course_mastery",
    "tier_transactions",
    "mastery_xp_transactions",
    "solution_likes",
    "solutions",
]


class AdminService:
    """Admin service for user management"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_users(self) -> list[User]:
        """Get all users with pagination."""
        result = await self.db.execute(select(User).order_by(User.created_at.desc()))
        return list(result.scalars().all())

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user and all associated data (cascade delete)."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return False

        try:
            # Delete from all related tables using raw SQL (idempotent, skips missing tables)
            for table in USER_RELATED_TABLES:
                try:
                    await self.db.execute(
                        text(f"DELETE FROM {table} WHERE user_id = :user_id"),
                        {"user_id": user_id}
                    )
                except SQLAlchemyError:
                    # Table may not exist or not have user_id — skip silently
                    pass

            # Finally delete the user
            await self.db.execute(delete(User).where(User.id == user_id))
            await self.db.commit()
            logger.info("Deleted user %s and all associated data", user_id)
            return True
        except IntegrityError as exc:
            logger.error("Integrity error deleting user %s: %s", user_id, exc)
            await self.db.rollback()
            raise
        except SQLAlchemyError as exc:
            logger.error("Database error deleting user %s: %s", user_id, exc)
            await self.db.rollback()
            raise

    async def get_online_users(self) -> list[User]:
        """Get users with active login sessions"""
        result = await self.db.execute(
            select(LoginSession).where(LoginSession.is_active.is_(True))
        )
        sessions = result.scalars().all()

        user_ids = [s.user_id for s in sessions]
        if not user_ids:
            return []

        result = await self.db.execute(
            select(User).where(User.id.in_(user_ids))
        )
        return list(result.scalars().all())

    async def create_login_session(self, user_id: str, token: str) -> LoginSession:
        """Create a new login session"""
        session = LoginSession(
            user_id=user_id,
            token=token,
            is_active=True,
            created_at=utc_now()
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def deactivate_session(self, token: str) -> bool:
        """Deactivate a login session (logout)"""
        result = await self.db.execute(
            select(LoginSession).where(LoginSession.token == token)
        )
        session = result.scalar_one_or_none()
        if session:
            session.is_active = False
            await self.db.commit()
            return True
        return False

"""AI Quota Service - Manages user AI quota tracking and deduction"""

from datetime import datetime, timedelta
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.time import utc_now


class QuotaService:
    """Service for managing AI quota"""

    DEFAULT_QUOTA = 100
    QUOTA_RESET_INTERVAL_HOURS = 24

    async def get_quota(self, user: User, db: AsyncSession) -> dict:
        """Get current quota status for a user"""
        await self._check_and_reset_quota(user, db)

        return {
            "quota_remaining": user.ai_quota,
            "quota_reset_at": user.quota_reset_at,
            "is_admin": user.is_admin,
        }

    async def check_quota(self, user: User, db: AsyncSession, cost: int = 1) -> bool:
        """Check if user has enough quota, resets if needed"""
        if user.is_admin:
            return True

        if cost < 0:
            cost = 1

        await self._check_and_reset_quota(user, db)
        return user.ai_quota >= cost

    async def deduct_quota(self, user: User, db: AsyncSession, cost: int = 1) -> bool:
        """Deduct quota from user atomically. Returns True if successful, False if insufficient."""
        if user.is_admin:
            return True

        if cost < 0:
            cost = 1

        # Check reset first
        await self._check_and_reset_quota(user, db)

        # Atomic deduct: UPDATE ... WHERE ai_quota >= cost
        result = await db.execute(
            update(User)
            .where(User.id == user.id, User.ai_quota >= cost)
            .values(ai_quota=User.ai_quota - cost)
        )
        await db.commit()

        # If no rows updated, insufficient quota
        if result.rowcount == 0:
            return False

        # Refresh user to get updated value
        await db.refresh(user)
        return True

    async def reset_quota(self, user: User, db: AsyncSession, amount: int = DEFAULT_QUOTA) -> None:
        """Reset quota for a user to specified amount"""
        if amount < 0:
            amount = 0

        user.ai_quota = amount
        user.quota_reset_at = utc_now().replace(tzinfo=None) + timedelta(hours=self.QUOTA_RESET_INTERVAL_HOURS)
        db.add(user)
        await db.commit()

    async def set_quota(self, user: User, db: AsyncSession, amount: int) -> None:
        """Set quota to a specific amount"""
        if amount < 0:
            amount = 0

        user.ai_quota = amount
        db.add(user)
        await db.commit()

    async def _check_and_reset_quota(self, user: User, db: AsyncSession) -> None:
        """Check if quota has expired and reset if needed"""
        now = utc_now().replace(tzinfo=None)
        reset_at = user.quota_reset_at
        if reset_at.tzinfo is not None:
            reset_at = reset_at.replace(tzinfo=None)

        if now >= reset_at:
            user.ai_quota = self.DEFAULT_QUOTA
            user.quota_reset_at = now + timedelta(hours=self.QUOTA_RESET_INTERVAL_HOURS)
            db.add(user)
            await db.commit()

    async def get_or_create_user_quota(self, user_id: str, db: AsyncSession) -> User | None:
        """Get user by ID for quota operations"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


quota_service = QuotaService()

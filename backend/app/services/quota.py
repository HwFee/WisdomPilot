"""
Core (智核) Service - Manages user core currency tracking and deduction

This replaces the old QuotaService. The new Core system:
- Uses 'cores' field instead of 'ai_quota'
- No automatic daily reset (cores persist)
- Earn cores through learning activities
- Spend cores on AI hints
"""

import logging
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.core_transaction import CoreTransaction
from app.utils.time import utc_now

logger = logging.getLogger(__name__)


class QuotaService:
    """Service for managing core (智核) currency - backwards compatible with old quota API"""

    DEFAULT_QUOTA = 100  # Initial cores for new users

    async def get_quota(self, user: User, db: AsyncSession) -> dict:
        """Get current core balance for a user (backwards compatible)"""
        return {
            "quota_remaining": user.cores,
            "quota_reset_at": None,  # No longer used - cores don't reset
            "is_admin": user.is_admin,
        }

    async def check_quota(self, user: User, db: AsyncSession, cost: int = 1) -> bool:
        """Check if user has enough cores"""
        if user.is_admin:
            return True

        if cost < 0:
            cost = 1

        return user.cores >= cost

    async def deduct_quota(self, user: User, db: AsyncSession, cost: int = 1) -> bool:
        """Deduct cores from user atomically. Returns True if successful, False if insufficient."""
        if user.is_admin:
            return True

        if cost < 0:
            cost = 1

        # Atomic deduct: UPDATE ... WHERE cores >= cost
        result = await db.execute(
            update(User)
            .where(User.id == user.id, User.cores >= cost)
            .values(cores=User.cores - cost)
        )
        await db.commit()

        # If no rows updated, insufficient cores
        if result.rowcount == 0:
            return False

        # Refresh user to get updated value
        await db.refresh(user)
        logger.info(f"[Core] Deducted {cost} cores from user {user.id[:8]}... Balance: {user.cores}")
        return True

    async def reset_quota(self, user: User, db: AsyncSession, amount: int = DEFAULT_QUOTA) -> None:
        """Reset user's cores to specified amount (admin operation)"""
        if amount < 0:
            amount = 0

        user.cores = amount
        db.add(user)
        await db.commit()

    async def set_quota(self, user: User, db: AsyncSession, amount: int) -> None:
        """Set cores to a specific amount (admin operation)"""
        if amount < 0:
            amount = 0

        user.cores = amount
        db.add(user)
        await db.commit()

    async def get_or_create_user_quota(self, user_id: str, db: AsyncSession) -> User | None:
        """Get user by ID for quota operations"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


quota_service = QuotaService()

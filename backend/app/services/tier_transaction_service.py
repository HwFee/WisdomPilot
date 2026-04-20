"""
Tier Transaction Service - 段位变化记录服务
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.tier_transaction import TierTransaction

logger = logging.getLogger(__name__)


class TierTransactionService:
    """Service for managing tier transaction records"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_transaction(
        self,
        user_id: str,
        course_id: int,
        tier_before: str,
        sub_tier_before: int,
        stars_before: int,
        tier_after: str,
        sub_tier_after: int,
        stars_after: int,
        stars_change: int,
        promoted: bool = False,
        demoted: bool = False,
        used_protection: bool = False,
        protection_remaining: int = 0,
        source: str = "arena_challenge",
        reference_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> TierTransaction:
        """Record a tier transaction"""
        tx = TierTransaction(
            user_id=user_id,
            course_id=course_id,
            tier_before=tier_before,
            sub_tier_before=sub_tier_before,
            stars_before=stars_before,
            tier_after=tier_after,
            sub_tier_after=sub_tier_after,
            stars_after=stars_after,
            stars_change=stars_change,
            promoted=promoted,
            demoted=demoted,
            used_protection=used_protection,
            protection_remaining=protection_remaining,
            source=source,
            reference_id=reference_id,
            description=description,
        )
        self.db.add(tx)
        await self.db.flush()  # Get ID without committing
        await self.db.refresh(tx)
        logger.info(f"[TierTx] User {user_id[:8]}... {tier_before} {sub_tier_before} {stars_before}⭐ → {tier_after} {sub_tier_after} {stars_after}⭐ ({stars_change:+d})")
        return tx

    async def get_transactions(
        self,
        user_id: str,
        course_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """Get user's tier transaction history"""
        # Build query
        query = select(TierTransaction).where(TierTransaction.user_id == user_id)
        count_query = select(func.count()).select_from(TierTransaction).where(TierTransaction.user_id == user_id)

        if course_id:
            query = query.where(TierTransaction.course_id == course_id)
            count_query = count_query.where(TierTransaction.course_id == course_id)

        # Get total count
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # Get transactions
        result = await self.db.execute(
            query.order_by(TierTransaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        transactions = result.scalars().all()

        return {
            "transactions": [
                {
                    "id": tx.id,
                    "course_id": tx.course_id,
                    "tier_before": tx.tier_before,
                    "sub_tier_before": tx.sub_tier_before,
                    "stars_before": tx.stars_before,
                    "tier_after": tx.tier_after,
                    "sub_tier_after": tx.sub_tier_after,
                    "stars_after": tx.stars_after,
                    "stars_change": tx.stars_change,
                    "promoted": tx.promoted,
                    "demoted": tx.demoted,
                    "used_protection": tx.used_protection,
                    "protection_remaining": tx.protection_remaining,
                    "source": tx.source,
                    "description": tx.description,
                    "created_at": tx.created_at,
                }
                for tx in transactions
            ],
            "total": total,
        }


def get_tier_transaction_service(db: AsyncSession = None) -> TierTransactionService:
    """Get TierTransactionService instance"""
    return TierTransactionService(db)

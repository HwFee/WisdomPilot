"""
Mastery XP Transaction Service - 精进之路经验变化记录服务
"""

import logging
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.mastery_xp_transaction import MasteryXpTransaction

logger = logging.getLogger(__name__)


# Mastery level thresholds (mastery_xp: level_name)
MASTERY_LEVELS = [
    (0, "入门"),
    (100, "学习"),
    (300, "练习"),
    (600, "熟练"),
    (1000, "精通"),
]


def get_mastery_level(mastery_xp: int) -> str:
    """Get mastery level name based on XP"""
    for threshold, level_name in reversed(MASTERY_LEVELS):
        if mastery_xp >= threshold:
            return level_name
    return "入门"


class MasteryXpTransactionService:
    """Service for managing mastery XP transaction records"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_transaction(
        self,
        user_id: str,
        type: str,
        category: str,
        amount: int,
        balance_after: int,
        level_before: str,
        level_after: str,
        level_up: bool = False,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> MasteryXpTransaction:
        """Record a mastery XP transaction"""
        tx = MasteryXpTransaction(
            user_id=user_id,
            type=type,
            category=category,
            amount=amount,
            balance_after=balance_after,
            level_before=level_before,
            level_after=level_after,
            level_up=level_up,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
        )
        self.db.add(tx)
        await self.db.flush()  # Get ID without committing
        await self.db.refresh(tx)
        logger.info(f"[MasteryXpTx] User {user_id[:8]}... {type} {amount} XP -> {balance_after} ({level_before} -> {level_after})")
        return tx

    async def earn_xp(
        self,
        user_id: str,
        amount: int,
        category: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        description: Optional[str] = None,
        auto_commit: bool = True,
    ) -> dict:
        """Earn mastery XP and record transaction

        Args:
            auto_commit: If True, commit the transaction. If False, leave it to the caller.
        """
        # Get user
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Record before state
        level_before = get_mastery_level(user.mastery_xp)

        # Update user
        user.mastery_xp += amount
        level_after = get_mastery_level(user.mastery_xp)
        level_up = level_after != level_before and level_after != "入门"

        user.mastery_level = level_after
        self.db.add(user)

        # Record transaction
        tx = await self.record_transaction(
            user_id=user_id,
            type="earn",
            category=category,
            amount=amount,
            balance_after=user.mastery_xp,
            level_before=level_before,
            level_after=level_after,
            level_up=level_up,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
        )

        if auto_commit:
            await self.db.commit()
            await self.db.refresh(user)

        return {
            "id": tx.id,
            "type": "earn",
            "category": category,
            "amount": amount,
            "balance_after": user.mastery_xp,
            "level_before": level_before,
            "level_after": level_after,
            "level_up": level_up,
            "description": description,
            "created_at": tx.created_at,
        }

    async def get_transactions(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """Get user's mastery XP transaction history"""
        # Build query
        query = select(MasteryXpTransaction).where(MasteryXpTransaction.user_id == user_id)
        count_query = select(func.count()).select_from(MasteryXpTransaction).where(MasteryXpTransaction.user_id == user_id)

        # Get total count
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # Get transactions
        result = await self.db.execute(
            query.order_by(MasteryXpTransaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        transactions = result.scalars().all()

        return {
            "transactions": [
                {
                    "id": tx.id,
                    "type": tx.type,
                    "category": tx.category,
                    "amount": tx.amount,
                    "balance_after": tx.balance_after,
                    "level_before": tx.level_before,
                    "level_after": tx.level_after,
                    "level_up": tx.level_up,
                    "reference_type": tx.reference_type,
                    "reference_id": tx.reference_id,
                    "description": tx.description,
                    "created_at": tx.created_at,
                }
                for tx in transactions
            ],
            "total": total,
        }

    async def get_balance(self, user_id: str) -> dict:
        """Get user's current mastery XP balance"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not found")

        return {
            "balance": user.mastery_xp,
            "level": user.mastery_level,
        }


def get_mastery_xp_transaction_service(db: AsyncSession = None) -> MasteryXpTransactionService:
    """Get MasteryXpTransactionService instance"""
    return MasteryXpTransactionService(db)

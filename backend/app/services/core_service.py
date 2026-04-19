"""
Core (智核) Service - Business logic for core currency management
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.core_transaction import CoreTransaction
from app.schemas.core import CoreEarnRequest
from app.database import get_db

logger = logging.getLogger(__name__)

# Valid categories for spending and earning
VALID_SPEND_CATEGORIES = {"ai_hint_light", "ai_hint_medium", "ai_hint_deep"}
VALID_EARN_CATEGORIES = {
    "mastery", "arena", "checkin", "study_time",
    "daily_exercises", "daily_accuracy", "bonus"
}


class CoreService:
    """Service for managing core (智核) currency"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_balance(self, user_id: str) -> dict:
        """Get user's current core balance"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        return {
            "balance": user.cores,
            "total_earned": user.cores_total_earned,
            "total_spent": user.cores_total_spent,
        }

    async def spend_cores(
        self,
        user_id: str,
        amount: int,
        category: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> dict:
        """Spend cores for a user

        Args:
            user_id: User ID
            amount: Amount to spend (must be positive)
            category: Spending category (ai_hint_light, ai_hint_medium, ai_hint_deep)
            reference_type: Optional reference type
            reference_id: Optional reference ID
            description: Optional description

        Returns:
            dict with success, balance_after, transaction_id

        Raises:
            ValueError: If insufficient cores or invalid category
        """
        # Validate category
        if category not in VALID_SPEND_CATEGORIES:
            raise ValueError(f"Invalid spend category: {category}. Valid: {VALID_SPEND_CATEGORIES}")

        # Get user with row lock to prevent race conditions
        result = await self.db.execute(
            select(User).where(User.id == user_id).with_for_update()
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        # Check balance
        if user.cores < amount:
            raise ValueError(f"Insufficient cores. Have {user.cores}, need {amount}")

        try:
            # Create transaction
            tx = CoreTransaction(
                user_id=user_id,
                type="spend",
                category=category,
                amount=amount,
                balance_after=user.cores - amount,
                reference_type=reference_type,
                reference_id=reference_id,
                description=description,
            )
            self.db.add(tx)

            # Update user
            user.cores -= amount
            user.cores_total_spent += amount

            await self.db.commit()
            await self.db.refresh(tx)

            logger.info(f"[Core] User {user_id[:8]}... spent {amount} cores on {category}. Balance: {user.cores}")

            return {
                "success": True,
                "balance_after": user.cores,
                "transaction_id": tx.id,
            }
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[Core] Transaction failed for user {user_id[:8]}...: {e}")
            raise

    async def earn_cores(
        self,
        user_id: str,
        amount: int,
        category: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> dict:
        """Earn cores for a user

        Args:
            user_id: User ID
            amount: Amount to earn (must be positive)
            category: Earning category (mastery, arena, checkin, study_time, etc.)
            reference_type: Optional reference type
            reference_id: Optional reference ID
            description: Optional description

        Returns:
            dict with success, balance_after, transaction_id
        """
        import traceback
        call_stack = ''.join(traceback.format_stack()[-5:-1])  # 获取调用栈
        logger.info(f"[Core] earn_cores 被调用: user={user_id[:8]}..., amount={amount}, category={category}, ref_type={reference_type}, ref_id={reference_id}")
        logger.info(f"[Core] 调用栈:\n{call_stack}")

        # Validate category
        if category not in VALID_EARN_CATEGORIES:
            raise ValueError(f"Invalid earn category: {category}. Valid: {VALID_EARN_CATEGORIES}")

        # Get user with row lock
        result = await self.db.execute(
            select(User).where(User.id == user_id).with_for_update()
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        try:
            # Create transaction
            tx = CoreTransaction(
                user_id=user_id,
                type="earn",
                category=category,
                amount=amount,
                balance_after=user.cores + amount,
                reference_type=reference_type,
                reference_id=reference_id,
                description=description,
            )
            self.db.add(tx)

            # Update user
            user.cores += amount
            user.cores_total_earned += amount

            await self.db.commit()
            await self.db.refresh(tx)

            logger.info(f"[Core] User {user_id[:8]}... earned {amount} cores from {category}. Balance: {user.cores}")

            return {
                "success": True,
                "balance_after": user.cores,
                "transaction_id": tx.id,
            }
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[Core] Transaction failed for user {user_id[:8]}...: {e}")
            raise

    async def get_transactions(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """Get user's transaction history"""
        # Get total count
        count_result = await self.db.execute(
            select(func.count()).select_from(CoreTransaction).where(
                CoreTransaction.user_id == user_id
            )
        )
        total = count_result.scalar() or 0

        # Get transactions
        result = await self.db.execute(
            select(CoreTransaction)
            .where(CoreTransaction.user_id == user_id)
            .order_by(CoreTransaction.created_at.desc())
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
                    "reference_type": tx.reference_type,
                    "reference_id": tx.reference_id,
                    "description": tx.description,
                    "created_at": tx.created_at,
                }
                for tx in transactions
            ],
            "total": total,
        }

    async def get_daily_summary(self, user_id: str) -> dict:
        """Get user's daily core statistics"""
        # Get today's date range (UTC)
        utc_now = datetime.now(timezone.utc)
        today_start = utc_now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Get today's transactions
        result = await self.db.execute(
            select(CoreTransaction).where(
                CoreTransaction.user_id == user_id,
                CoreTransaction.created_at >= today_start,
            )
        )
        today_transactions = result.scalars().all()

        # Calculate earned and spent today
        earned_today = sum(tx.amount for tx in today_transactions if tx.type == "earn")
        spent_today = sum(tx.amount for tx in today_transactions if tx.type == "spend")

        # Get daily exercises and accuracy from ActivityLog
        from app.models.stats import ActivityLog

        activities_result = await self.db.execute(
            select(ActivityLog).where(
                ActivityLog.user_id == user_id,
                ActivityLog.created_at >= today_start,
                ActivityLog.activity_type == "exercise_complete",
            )
        )
        today_activities = activities_result.scalars().all()

        # Only count challenge-path exercises
        challenge_activities = [
            a for a in today_activities
            if (a.extra_data or {}).get("learning_path") != "mastery"
        ]

        daily_exercises = len(challenge_activities)
        correct_count = sum(
            1 for a in challenge_activities
            if (a.extra_data or {}).get("is_correct", False)
        )
        daily_accuracy = round((correct_count / daily_exercises) * 100, 1) if daily_exercises > 0 else 0.0

        # Calculate pending rewards
        pending_rewards = {}

        # Exercise count rewards
        if daily_exercises >= 5:
            pending_rewards["exercise_count_5"] = 3
        if daily_exercises >= 10:
            pending_rewards["exercise_count_10"] = 8
        if daily_exercises >= 20:
            pending_rewards["exercise_count_20"] = 15

        # Accuracy rewards
        if daily_accuracy >= 60:
            pending_rewards["accuracy_60"] = 5
        if daily_accuracy >= 80:
            pending_rewards["accuracy_80"] = 10
        if daily_accuracy >= 95:
            pending_rewards["accuracy_95"] = 20

        return {
            "earned_today": earned_today,
            "spent_today": spent_today,
            "daily_exercises": daily_exercises,
            "daily_accuracy": daily_accuracy,
            "pending_rewards": pending_rewards,
        }


def get_core_service(db: AsyncSession = Depends(get_db)) -> CoreService:
    """Get CoreService instance - FastAPI dependency"""
    return CoreService(db)

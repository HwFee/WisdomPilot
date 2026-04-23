"""Challenge Service - Manages challenges and user progress"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.challenge import Challenge, ChallengeType
from app.models.user_challenge import UserChallenge, UserChallengeStatus
import logging


class ChallengeService:
    """Service for managing challenges and user challenge progress"""

    async def get_active_challenges(self, db: AsyncSession) -> list[Challenge]:
        """Get all active challenges"""
        result = await db.execute(
            select(Challenge)
            .where(Challenge.is_active)
            .order_by(Challenge.difficulty, Challenge.code)
        )
        return list(result.scalars().all())

    async def get_challenge_by_id(self, db: AsyncSession, challenge_id: int) -> Challenge | None:
        """Get challenge by ID"""
        result = await db.execute(
            select(Challenge).where(Challenge.id == challenge_id)
        )
        return result.scalar_one_or_none()

    async def get_user_challenges(
        self, db: AsyncSession, user_id: str
    ) -> list[UserChallenge]:
        """Get all challenge progress for a user"""
        result = await db.execute(
            select(UserChallenge)
            .where(UserChallenge.user_id == user_id)
            .options(selectinload(UserChallenge.challenge))
        )
        return list(result.scalars().all())

    async def get_user_challenge(
        self, db: AsyncSession, user_id: str, challenge_id: int
    ) -> UserChallenge | None:
        """Get user's progress on a specific challenge"""
        result = await db.execute(
            select(UserChallenge)
            .where(
                UserChallenge.user_id == user_id,
                UserChallenge.challenge_id == challenge_id
            )
        )
        return result.scalar_one_or_none()

    async def start_challenge(
        self, db: AsyncSession, user: User, challenge_id: int
    ) -> UserChallenge:
        """Start a challenge for a user"""
        challenge = await self.get_challenge_by_id(db, challenge_id)
        if not challenge:
            raise ValueError(f"Challenge {challenge_id} not found")

        # Check if already started
        existing = await self.get_user_challenge(db, user.id, challenge_id)
        if existing:
            if existing.status == UserChallengeStatus.COMPLETED:
                raise ValueError("Challenge already completed")
            if existing.status == UserChallengeStatus.IN_PROGRESS:
                return existing

        # Get target from requirements
        requirements = challenge.requirements or {}
        target_value = requirements.get("target", requirements.get("exercise_count", 10))

        user_challenge = UserChallenge(
            id=str(uuid.uuid4()),
            user_id=user.id,
            challenge_id=challenge_id,
            status=UserChallengeStatus.IN_PROGRESS,
            current_progress=0,
            target_value=target_value,
            attempts=1,
            started_at=datetime.now(timezone.utc),
        )
        db.add(user_challenge)
        await db.commit()
        await db.refresh(user_challenge)
        return user_challenge

    async def update_progress(
        self,
        db: AsyncSession,
        user: User,
        challenge_id: int,
        progress_delta: int = 1,
    ) -> UserChallenge:
        """Update user's progress on a challenge"""
        user_challenge = await self.get_user_challenge(db, user.id, challenge_id)
        if not user_challenge:
            raise ValueError("Challenge not started")

        if user_challenge.status == UserChallengeStatus.COMPLETED:
            return user_challenge

        user_challenge.current_progress += progress_delta

        # Check if completed
        if user_challenge.current_progress >= user_challenge.target_value:
            user_challenge.status = UserChallengeStatus.COMPLETED
            user_challenge.completed_at = datetime.now(timezone.utc)

            # Apply rewards
            await self._apply_rewards(db, user, challenge_id)

        db.add(user_challenge)
        await db.commit()
        await db.refresh(user_challenge)
        return user_challenge

    async def _apply_rewards(
        self, db: AsyncSession, user: User, challenge_id: int
    ) -> None:
        """Apply challenge rewards to user"""
        challenge = await self.get_challenge_by_id(db, challenge_id)
        if not challenge:
            return

        rewards = challenge.rewards or {}
        quota_bonus = rewards.get("quota_bonus", 0)

        if quota_bonus > 0:
            user.cores += quota_bonus
            db.add(user)

    async def check_challenge_completion(
        self, db: AsyncSession, user_id: str, challenge_id: int
    ) -> bool:
        """Check if user has completed a specific challenge"""
        user_challenge = await self.get_user_challenge(db, user_id, challenge_id)
        if not user_challenge:
            return False
        return user_challenge.status == UserChallengeStatus.COMPLETED

    async def create_default_challenges(self, db: AsyncSession) -> None:
        """Create default challenges if they don't exist"""
        existing = await db.execute(select(Challenge).limit(1))
        if existing.scalar_one_or_none():
            return  # Already has challenges

        default_challenges = [
            {
                "code": "FIRST_STEPS",
                "title": "First Steps",
                "description": "Complete your first 5 exercises",
                "type": ChallengeType.EXERCISE_COUNT.value,
                "difficulty": 1,
                "requirements": {"exercise_count": 5},
                "rewards": {"quota_bonus": 10},
            },
            {
                "code": "CHAPTER_MASTER",
                "title": "Chapter Master",
                "description": "Complete a chapter",
                "type": ChallengeType.CHAPTER_COMPLETE.value,
                "difficulty": 2,
                "requirements": {"chapter_id": 1},
                "rewards": {"quota_bonus": 20},
            },
            {
                "code": "STREAK_7",
                "title": "7 Day Streak",
                "description": "Maintain a 7-day learning streak",
                "type": ChallengeType.STREAK.value,
                "difficulty": 3,
                "requirements": {"days": 7},
                "rewards": {"quota_bonus": 50},
            },
        ]

        for ch_data in default_challenges:
            challenge = Challenge(**ch_data)
            db.add(challenge)

        await db.commit()


challenge_service = ChallengeService()


logger = logging.getLogger(__name__)
"""Challenge Service - Manages challenges and user progress"""

import uuid
from datetime import datetime, timezone
from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.challenge import Challenge, ChallengeType
from app.models.user_challenge import UserChallenge, UserChallengeStatus
from app.services.challenge_errors import (
    ChallengeAlreadyCompletedError,
    ChallengeNotFoundError,
    ChallengeNotStartedError,
    InvalidChallengeDefinitionError,
    InvalidProgressDeltaError,
)
from app.services.core_service import CoreService


class ChallengeDefinition(TypedDict):
    code: str
    title: str
    description: str
    type: str
    difficulty: int
    requirements: dict[str, int]
    rewards: dict[str, int]


CHALLENGE_TARGET_KEYS = {
    ChallengeType.EXERCISE_COUNT.value: "exercise_count",
    ChallengeType.STREAK.value: "days",
    ChallengeType.TIME_SPENT.value: "minutes",
    ChallengeType.ACCURACY.value: "accuracy",
}
BINARY_CHALLENGE_TYPES = frozenset(
    {
        ChallengeType.CHAPTER_COMPLETE.value,
        ChallengeType.COURSE_COMPLETE.value,
    }
)
QUOTA_BONUS_REWARD_KEY = "quota_bonus"
CHALLENGE_REWARD_CATEGORY = "bonus"
CHALLENGE_REWARD_REFERENCE_TYPE = "challenge"
DEFAULT_CHALLENGE_DEFINITIONS: tuple[ChallengeDefinition, ...] = (
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
)


def _positive_integer(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return None
    return value


def resolve_challenge_target(challenge: Challenge) -> int:
    requirements = challenge.requirements or {}
    if "target" in requirements:
        explicit_target = _positive_integer(requirements["target"])
        if explicit_target is None:
            raise InvalidChallengeDefinitionError(str(challenge.type), "target")
        return explicit_target

    challenge_type = str(challenge.type)
    if challenge_type in BINARY_CHALLENGE_TYPES:
        return 1

    requirement_key = CHALLENGE_TARGET_KEYS.get(challenge_type)
    if requirement_key is None:
        raise InvalidChallengeDefinitionError(challenge_type, "target")

    target = _positive_integer(requirements.get(requirement_key))
    if target is None:
        raise InvalidChallengeDefinitionError(challenge_type, requirement_key)
    return target


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

    async def get_user_challenge_for_update(
        self, db: AsyncSession, user_id: str, challenge_id: int
    ) -> UserChallenge | None:
        """Lock and return a user's progress on a specific challenge."""
        result = await db.execute(
            select(UserChallenge)
            .where(
                UserChallenge.user_id == user_id,
                UserChallenge.challenge_id == challenge_id,
            )
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def start_challenge(
        self, db: AsyncSession, user: User, challenge_id: int
    ) -> UserChallenge:
        """Start a challenge for a user"""
        challenge = await self.get_challenge_by_id(db, challenge_id)
        if not challenge:
            raise ChallengeNotFoundError(challenge_id)

        # Check if already started
        existing = await self.get_user_challenge(db, user.id, challenge_id)
        if existing:
            if existing.status == UserChallengeStatus.COMPLETED:
                raise ChallengeAlreadyCompletedError()
            if existing.status == UserChallengeStatus.IN_PROGRESS:
                return existing

        target_value = resolve_challenge_target(challenge)

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
        await db.flush()
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
        if progress_delta <= 0:
            raise InvalidProgressDeltaError()

        user_challenge = await self.get_user_challenge_for_update(
            db, user.id, challenge_id
        )
        if not user_challenge:
            raise ChallengeNotStartedError()

        if user_challenge.status == UserChallengeStatus.COMPLETED:
            return user_challenge

        user_challenge.current_progress += progress_delta

        # Check if completed
        if user_challenge.current_progress >= user_challenge.target_value:
            user_challenge.status = UserChallengeStatus.COMPLETED
            user_challenge.completed_at = datetime.now(timezone.utc)

            await self._apply_rewards(db, user_challenge)

        db.add(user_challenge)
        await db.flush()
        await db.refresh(user_challenge)
        return user_challenge

    async def _apply_rewards(
        self,
        db: AsyncSession,
        user_challenge: UserChallenge,
    ) -> None:
        """Apply challenge rewards to user"""
        challenge = await self.get_challenge_by_id(db, user_challenge.challenge_id)
        if challenge is None:
            raise ChallengeNotFoundError(user_challenge.challenge_id)

        quota_bonus = (challenge.rewards or {}).get(QUOTA_BONUS_REWARD_KEY, 0)
        if not isinstance(quota_bonus, int) or isinstance(quota_bonus, bool):
            raise InvalidChallengeDefinitionError(
                challenge.type, QUOTA_BONUS_REWARD_KEY
            )
        if quota_bonus <= 0:
            return

        await CoreService(db).earn_cores(
            user_id=user_challenge.user_id,
            amount=quota_bonus,
            category=CHALLENGE_REWARD_CATEGORY,
            reference_type=CHALLENGE_REWARD_REFERENCE_TYPE,
            reference_id=user_challenge.id,
            description=f"Challenge completed: {challenge.code}",
        )

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
        codes = tuple(item["code"] for item in DEFAULT_CHALLENGE_DEFINITIONS)
        result = await db.execute(
            select(Challenge.code).where(Challenge.code.in_(codes))
        )
        existing_codes = set(result.scalars().all())

        for definition in DEFAULT_CHALLENGE_DEFINITIONS:
            if definition["code"] not in existing_codes:
                db.add(Challenge(**definition))

        await db.flush()


challenge_service = ChallengeService()

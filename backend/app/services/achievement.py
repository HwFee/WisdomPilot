"""Achievement Service - Manages achievements and user progress"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.achievement import Achievement, UserAchievement, AchievementType


class AchievementService:
    """Service for managing achievements"""

    async def get_active_achievements(self, db: AsyncSession) -> list[Achievement]:
        """Get all active achievements"""
        result = await db.execute(
            select(Achievement)
            .where(Achievement.is_active == True)
            .order_by(Achievement.display_order, Achievement.difficulty)
        )
        return list(result.scalars().all())

    async def get_achievement_by_id(
        self, db: AsyncSession, achievement_id: int
    ) -> Achievement | None:
        """Get achievement by ID"""
        result = await db.execute(
            select(Achievement).where(Achievement.id == achievement_id)
        )
        return result.scalar_one_or_none()

    async def get_achievement_by_code(
        self, db: AsyncSession, code: str
    ) -> Achievement | None:
        """Get achievement by code"""
        result = await db.execute(
            select(Achievement).where(Achievement.code == code)
        )
        return result.scalar_one_or_none()

    async def get_user_achievements(
        self, db: AsyncSession, user_id: str
    ) -> list[UserAchievement]:
        """Get all achievements for a user"""
        result = await db.execute(
            select(UserAchievement)
            .where(UserAchievement.user_id == user_id)
            .options(selectinload(UserAchievement.achievement))
        )
        return list(result.scalars().all())

    async def get_earned_achievements(
        self, db: AsyncSession, user_id: str
    ) -> list[UserAchievement]:
        """Get earned achievements for a user"""
        result = await db.execute(
            select(UserAchievement)
            .where(UserAchievement.user_id == user_id)
            .options(selectinload(UserAchievement.achievement))
            .order_by(UserAchievement.earned_at.desc())
        )
        return list(result.scalars().all())

    async def earn_achievement(
        self, db: AsyncSession, user: User, achievement_id: int
    ) -> UserAchievement:
        """Award an achievement to a user"""
        # Check if already earned
        existing = await db.execute(
            select(UserAchievement).where(
                UserAchievement.user_id == user.id,
                UserAchievement.achievement_id == achievement_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Achievement already earned")

        achievement = await self.get_achievement_by_id(db, achievement_id)
        if not achievement:
            raise ValueError("Achievement not found")

        user_achievement = UserAchievement(
            id=str(uuid.uuid4()),
            user_id=user.id,
            achievement_id=achievement_id,
            earned_at=datetime.now(timezone.utc),
            progress=achievement.requirements.get("threshold", 1),
            is_notified=False,
        )
        db.add(user_achievement)

        # Apply rewards
        if achievement.xp_reward > 0:
            user.xp += achievement.xp_reward
            db.add(user)
        if achievement.quota_reward > 0:
            user.ai_quota += achievement.quota_reward
            db.add(user)

        await db.commit()
        await db.refresh(user_achievement)
        return user_achievement

    async def get_user_rank(
        self, db: AsyncSession, user_id: str
    ) -> Optional[dict]:
        """Get user's rank on the leaderboard"""
        # Get user's XP
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return None

        # Count users with higher XP
        rank_result = await db.execute(
            select(func.count(User.id)).where(User.xp > user.xp)
        )
        higher_count = rank_result.scalar() or 0

        # Count total users
        total_result = await db.execute(select(func.count(User.id)))
        total_users = total_result.scalar() or 0

        return {
            "rank": higher_count + 1,
            "user_id": user.id,
            "username": user.username,
            "level": user.level,
            "xp": user.xp,
            "streak_days": user.streak_days,
            "accuracy_rate": user.accuracy_rate,
            "total_users": total_users,
        }

    async def create_default_achievements(self, db: AsyncSession) -> None:
        """Create default achievements if they don't exist"""
        existing = await db.execute(select(Achievement).limit(1))
        if existing.scalar_one_or_none():
            return  # Already has achievements

        default_achievements = [
            {
                "code": "FIRST_LESSON",
                "title": "First Step",
                "description": "Complete your first lesson",
                "icon": "🎯",
                "type": AchievementType.LESSON_COMPLETE.value,
                "category": "learning",
                "xp_reward": 10,
                "quota_reward": 0,
                "requirements": {"threshold": 1, "type": "lesson"},
                "is_secret": False,
                "difficulty": 1,
                "display_order": 1,
            },
            {
                "code": "FIVE_LESSONS",
                "title": "Getting Started",
                "description": "Complete 5 lessons",
                "icon": "📚",
                "type": AchievementType.LESSON_COMPLETE.value,
                "category": "learning",
                "xp_reward": 25,
                "quota_reward": 5,
                "requirements": {"threshold": 5, "type": "lesson"},
                "is_secret": False,
                "difficulty": 2,
                "display_order": 2,
            },
            {
                "code": "STREAK_3",
                "title": "On a Roll",
                "description": "Maintain a 3-day learning streak",
                "icon": "🔥",
                "type": AchievementType.STREAK.value,
                "category": "streak",
                "xp_reward": 15,
                "quota_reward": 0,
                "requirements": {"threshold": 3, "type": "streak"},
                "is_secret": False,
                "difficulty": 1,
                "display_order": 10,
            },
            {
                "code": "STREAK_7",
                "title": "Week Warrior",
                "description": "Maintain a 7-day learning streak",
                "icon": "⭐",
                "type": AchievementType.STREAK.value,
                "category": "streak",
                "xp_reward": 50,
                "quota_reward": 10,
                "requirements": {"threshold": 7, "type": "streak"},
                "is_secret": False,
                "difficulty": 3,
                "display_order": 11,
            },
            {
                "code": "PERFECT_SCORE",
                "title": "Perfectionist",
                "description": "Complete an exercise with 100% accuracy",
                "icon": "💯",
                "type": AchievementType.ACCURACY.value,
                "category": "learning",
                "xp_reward": 20,
                "quota_reward": 5,
                "requirements": {"threshold": 100, "type": "accuracy"},
                "is_secret": False,
                "difficulty": 2,
                "display_order": 20,
            },
            {
                "code": "EXPLORER",
                "title": "Explorer",
                "description": "Try 3 different programming languages",
                "icon": "🗺️",
                "type": AchievementType.EXPLORER.value,
                "category": "exploration",
                "xp_reward": 30,
                "quota_reward": 10,
                "requirements": {"threshold": 3, "type": "language"},
                "is_secret": False,
                "difficulty": 3,
                "display_order": 30,
            },
        ]

        for ach_data in default_achievements:
            achievement = Achievement(**ach_data)
            db.add(achievement)

        await db.commit()


achievement_service = AchievementService()

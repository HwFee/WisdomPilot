"""Learning Profile Service - Manages user learning statistics and XP"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.time import utc_now
from app.services.achievement import achievement_service
from app.services.core_service import CoreService


class ProfileService:
    """Service for managing user learning profile and statistics"""

    # Check-in XP rewards
    CHECKIN_BASE_XP = 10
    CHECKIN_STREAK_BONUS_MULTIPLIER = 2  # Bonus XP per 7-day streak

    # Streak multiplier tiers (streak_days range: multiplier)
    STREAK_TIERS = [
        ((1, 6), 1.0),      # 1-6 days: 1x XP
        ((7, 13), 1.2),     # 7-13 days: 1.2x XP
        ((14, 29), 1.5),    # 14-29 days: 1.5x XP
        ((30, float('inf')), 2.0),  # 30+ days: 2x XP
    ]

    # Check-in Core (智核) rewards by streak
    CHECKIN_CORE_REWARDS = {
        1: 5,    # Day 1: 5 cores
        3: 10,   # 3+ day streak: 10 cores
        7: 20,   # 7+ day streak: 20 cores
        14: 35,  # 14+ day streak: 35 cores
        30: 55,  # 30+ day streak: 55 cores
    }

    # Mastery level thresholds (mastery_xp: level_name)
    MASTERY_LEVELS = [
        (0, "入门"),
        (100, "学习"),
        (300, "练习"),
        (600, "熟练"),
        (1000, "精通"),
    ]

    def _get_streak_multiplier(self, streak_days: int) -> float:
        """Get XP multiplier for current streak"""
        for (min_days, max_days), multiplier in self.STREAK_TIERS:
            if min_days <= streak_days <= max_days:
                return multiplier
        return 1.0

    def _get_checkin_cores(self, streak_days: int) -> int:
        """Get core reward for check-in based on streak"""
        # Return the highest applicable tier
        for threshold in sorted(self.CHECKIN_CORE_REWARDS.keys(), reverse=True):
            if streak_days >= threshold:
                return self.CHECKIN_CORE_REWARDS[threshold]
        return self.CHECKIN_CORE_REWARDS[1]  # Default to day 1 reward

    async def get_profile(self, db: AsyncSession, user_id: str) -> User | None:
        """Get user profile"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def add_xp(self, db: AsyncSession, user: User, xp_amount: int) -> User:
        """Add XP to user (for check-in, etc.)"""
        user.xp += xp_amount
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    def get_mastery_level(self, mastery_xp: int) -> str:
        """Get mastery level name based on XP"""
        for threshold, level_name in reversed(self.MASTERY_LEVELS):
            if mastery_xp >= threshold:
                return level_name
        return "入门"

    async def add_mastery_xp(self, db: AsyncSession, user: User, xp_amount: int) -> User:
        """Add mastery XP to user and update mastery level"""
        user.mastery_xp += xp_amount
        user.mastery_level = self.get_mastery_level(user.mastery_xp)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def update_exercise_result(
        self, db: AsyncSession, user: User, is_correct: bool
    ) -> User:
        """Update exercise statistics"""
        user.total_exercises += 1
        if is_correct:
            user.correct_exercises += 1

        # Update accuracy rate
        if user.total_exercises > 0:
            user.accuracy_rate = round(
                user.correct_exercises / user.total_exercises * 100, 1
            )

        await self._update_streak(db, user)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def update_streak(self, db: AsyncSession, user: User) -> User:
        """Update user's learning streak"""
        await self._update_streak(db, user)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def _update_streak(self, db: AsyncSession, user: User) -> None:
        """Internal: update streak based on last activity

        Uses Beijing timezone (UTC+8) for date calculations.
        """
        # 使用北京时区计算日期
        beijing_tz = timezone(timedelta(hours=8))
        beijing_now = datetime.now(beijing_tz)
        beijing_today_start = beijing_now.replace(hour=0, minute=0, second=0, microsecond=0)
        # 转换为 naive datetime 用于比较（数据库存储的是 naive UTC）
        today_start_naive = beijing_today_start.replace(tzinfo=None)

        if user.last_activity_date:
            last_date = user.last_activity_date
            if hasattr(last_date, 'tzinfo') and last_date.tzinfo:
                last_date = last_date.replace(tzinfo=None)
            last_date = last_date.replace(hour=0, minute=0, second=0, microsecond=0)

            # If last activity was yesterday, increment streak
            if today_start_naive - last_date == timedelta(days=1):
                user.streak_days += 1
            # If last activity was today, don't change streak
            elif today_start_naive == last_date:
                pass
            # If more than 1 day gap, reset streak
            else:
                user.streak_days = 1
        else:
            user.streak_days = 1

        # 更新 last_activity_date 为当前 UTC 时间
        user.last_activity_date = utc_now().replace(tzinfo=None)

    # Supported programming languages
    SUPPORTED_LANGUAGES = [
        "C", "C++", "Python", "Java", "JavaScript", "TypeScript",
        "Rust", "Go", "Ruby", "Swift", "Kotlin", "C#", "PHP", "Scala",
        "R", "MATLAB", "Julia", "Perl", "Haskell", "Lua", "Shell"
    ]

    async def set_preferred_languages(
        self, db: AsyncSession, user: User, languages: list[str]
    ) -> User:
        """Set user's preferred programming languages"""
        # Validate languages
        invalid = [lang for lang in languages if lang not in self.SUPPORTED_LANGUAGES]
        if invalid:
            raise ValueError(f"Unsupported languages: {invalid}")
        user.preferred_languages = languages
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    def calculate_accuracy(self, user: User) -> float:
        """Calculate accuracy percentage"""
        if user.total_exercises == 0:
            return 0.0
        return round(user.correct_exercises / user.total_exercises * 100, 1)

    def is_checked_in_today(self, user: User) -> bool:
        """Check if user has already checked in today

        Uses Beijing timezone (UTC+8) for date calculations.
        """
        # Never checked in before - can't be checked in today
        if user.total_checkin_days == 0:
            return False

        # Streak days must be at least 1 if total_checkin_days > 0
        # If streak_days > total_checkin_days, data is inconsistent - trust total_checkin_days
        if user.streak_days == 0 or user.streak_days > user.total_checkin_days:
            return False

        if not user.last_activity_date:
            return False

        # 使用北京时区计算日期
        beijing_tz = timezone(timedelta(hours=8))
        beijing_now = datetime.now(beijing_tz)
        beijing_today_start = beijing_now.replace(hour=0, minute=0, second=0, microsecond=0)
        # 转换为 naive datetime 用于比较
        today_start_naive = beijing_today_start.replace(tzinfo=None)

        last_date = user.last_activity_date
        if hasattr(last_date, 'tzinfo') and last_date.tzinfo:
            last_date = last_date.replace(tzinfo=None)
        last_date = last_date.replace(hour=0, minute=0, second=0, microsecond=0)

        return today_start_naive == last_date

    async def checkin(self, db: AsyncSession, user: User) -> dict:
        """Process daily check-in

        Uses Beijing timezone (UTC+8) for date calculations.

        Returns:
            dict with streak_days, checked_in_today, xp_earned, last_checkin_date,
                   total_checkin_days, streak_multiplier, cores_earned
        """
        # 使用北京时区计算日期
        beijing_tz = timezone(timedelta(hours=8))
        beijing_now = datetime.now(beijing_tz)
        beijing_today_start = beijing_now.replace(hour=0, minute=0, second=0, microsecond=0)
        # 转换为 naive datetime 用于比较
        today_start_naive = beijing_today_start.replace(tzinfo=None)

        # Check if already checked in today
        if self.is_checked_in_today(user):
            return {
                "streak_days": user.streak_days,
                "checked_in_today": True,
                "xp_earned": 0,
                "last_checkin_date": user.last_activity_date,
                "total_checkin_days": user.total_checkin_days,
                "streak_multiplier": self._get_streak_multiplier(user.streak_days),
                "cores_earned": 0,
            }

        # Calculate streak
        if user.last_activity_date:
            last_date = user.last_activity_date
            if hasattr(last_date, 'tzinfo') and last_date.tzinfo:
                last_date = last_date.replace(tzinfo=None)
            last_date = last_date.replace(hour=0, minute=0, second=0, microsecond=0)

            # If last activity was yesterday, increment streak
            if today_start_naive - last_date == timedelta(days=1):
                user.streak_days += 1
            # If more than 1 day gap, reset streak
            else:
                user.streak_days = 1
        else:
            # First check-in ever
            user.streak_days = 1

        # Calculate XP earned with streak multiplier
        streak_multiplier = self._get_streak_multiplier(user.streak_days)
        base_xp = self.CHECKIN_BASE_XP
        xp_earned = int(base_xp * streak_multiplier)

        # Add streak bonus (every 7 days gives extra XP)
        if user.streak_days >= 7:
            streak_bonus = (user.streak_days // 7) * self.CHECKIN_STREAK_BONUS_MULTIPLIER
            xp_earned += streak_bonus

        # Calculate core reward
        cores_earned = self._get_checkin_cores(user.streak_days)

        # Update user - 使用 UTC 时间存储
        user.last_activity_date = utc_now().replace(tzinfo=None)
        user.xp += xp_earned
        user.total_checkin_days += 1

        db.add(user)

        # Award cores using CoreService
        core_service = CoreService(db)
        await core_service.earn_cores(
            user_id=user.id,
            amount=cores_earned,
            category="checkin",
            description=f"每日签到奖励 (连续{user.streak_days}天)",
        )

        await db.refresh(user)

        # Check and award streak achievements
        new_achievements = await self._check_and_award_streak_achievements(db, user)

        return {
            "streak_days": user.streak_days,
            "checked_in_today": True,
            "xp_earned": xp_earned,
            "last_checkin_date": user.last_activity_date,
            "total_checkin_days": user.total_checkin_days,
            "streak_multiplier": streak_multiplier,
            "cores_earned": cores_earned,
            "new_achievements": new_achievements,
        }

    async def _check_and_award_streak_achievements(
        self, db: AsyncSession, user: User
    ) -> list[str]:
        """Check and award streak-based achievements

        Returns:
            list of newly earned achievement codes
        """
        earned_codes = []

        # Map streak thresholds to achievement codes
        streak_achievements = [
            (3, "STREAK_3"),
            (7, "STREAK_7"),
            (14, "STREAK_14"),
            (30, "STREAK_30"),
            (100, "STREAK_100"),
        ]

        for threshold, code in streak_achievements:
            if user.streak_days >= threshold:
                try:
                    achievement = await achievement_service.get_achievement_by_code(db, code)
                    if achievement:
                        await achievement_service.earn_achievement(db, user, achievement.id)
                        earned_codes.append(code)
                except ValueError:
                    # Already earned, skip
                    pass

        return earned_codes


profile_service = ProfileService()

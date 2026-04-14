"""Learning Profile Service - Manages user learning statistics and XP"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.time import utc_now


class ProfileService:
    """Service for managing user learning profile and statistics"""

    # XP thresholds per level (level 1 = 0, level 2 = 100, etc.)
    XP_PER_LEVEL = 100

    # Check-in XP rewards
    CHECKIN_BASE_XP = 10
    CHECKIN_STREAK_BONUS_MULTIPLIER = 2  # Bonus XP per 7-day streak

    async def get_profile(self, db: AsyncSession, user_id: str) -> User | None:
        """Get user profile"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def add_xp(self, db: AsyncSession, user: User, xp_amount: int) -> User:
        """Add XP to user and handle level up"""
        user.xp += xp_amount

        # Check for level up
        new_level = (user.xp // self.XP_PER_LEVEL) + 1
        if new_level > user.level:
            user.level = new_level

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
        """Internal: update streak based on last activity"""
        now = utc_now()
        now_naive = now.replace(tzinfo=None)
        today_start = now_naive.replace(hour=0, minute=0, second=0, microsecond=0)

        if user.last_activity_date:
            last_date = user.last_activity_date
            if hasattr(last_date, 'tzinfo') and last_date.tzinfo:
                last_date = last_date.replace(tzinfo=None)
            last_date = last_date.replace(hour=0, minute=0, second=0, microsecond=0)

            # If last activity was yesterday, increment streak
            if today_start - last_date == timedelta(days=1):
                user.streak_days += 1
            # If last activity was today, don't change streak
            elif today_start == last_date:
                pass
            # If more than 1 day gap, reset streak
            else:
                user.streak_days = 1
        else:
            user.streak_days = 1

        user.last_activity_date = now_naive

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

    def get_xp_for_next_level(self, user: User) -> int:
        """Get XP needed for next level"""
        next_level_xp = user.level * self.XP_PER_LEVEL
        return next_level_xp - user.xp

    def is_checked_in_today(self, user: User) -> bool:
        """Check if user has already checked in today"""
        if not user.last_activity_date:
            return False

        now = utc_now()
        now_naive = now.replace(tzinfo=None)
        today_start = now_naive.replace(hour=0, minute=0, second=0, microsecond=0)

        last_date = user.last_activity_date
        if hasattr(last_date, 'tzinfo') and last_date.tzinfo:
            last_date = last_date.replace(tzinfo=None)
        last_date = last_date.replace(hour=0, minute=0, second=0, microsecond=0)

        return today_start == last_date

    async def checkin(self, db: AsyncSession, user: User) -> dict:
        """Process daily check-in

        Returns:
            dict with streak_days, checked_in_today, xp_earned, last_checkin_date
        """
        now = utc_now()
        now_naive = now.replace(tzinfo=None)
        today_start = now_naive.replace(hour=0, minute=0, second=0, microsecond=0)

        # Check if already checked in today
        if self.is_checked_in_today(user):
            return {
                "streak_days": user.streak_days,
                "checked_in_today": True,
                "xp_earned": 0,
                "last_checkin_date": user.last_activity_date,
            }

        # Calculate streak
        if user.last_activity_date:
            last_date = user.last_activity_date
            if hasattr(last_date, 'tzinfo') and last_date.tzinfo:
                last_date = last_date.replace(tzinfo=None)
            last_date = last_date.replace(hour=0, minute=0, second=0, microsecond=0)

            # If last activity was yesterday, increment streak
            if today_start - last_date == timedelta(days=1):
                user.streak_days += 1
            # If more than 1 day gap, reset streak
            else:
                user.streak_days = 1
        else:
            # First check-in ever
            user.streak_days = 1

        # Calculate XP earned
        xp_earned = self.CHECKIN_BASE_XP
        # Add streak bonus (every 7 days gives extra XP)
        if user.streak_days >= 7:
            streak_bonus = (user.streak_days // 7) * self.CHECKIN_STREAK_BONUS_MULTIPLIER
            xp_earned += streak_bonus

        # Update user
        user.last_activity_date = now_naive
        user.xp += xp_earned

        # Check for level up
        new_level = (user.xp // self.XP_PER_LEVEL) + 1
        if new_level > user.level:
            user.level = new_level

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return {
            "streak_days": user.streak_days,
            "checked_in_today": True,
            "xp_earned": xp_earned,
            "last_checkin_date": user.last_activity_date,
        }


profile_service = ProfileService()

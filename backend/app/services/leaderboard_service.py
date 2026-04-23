"""
Leaderboard Service

Implements leaderboard calculations for both:
1. Mastery Leaderboard (精进榜) - Based on chapter mastery progress
2. Arena Leaderboard (竞技榜) - Based on challenge scores
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.user_arena import UserArenaProfile, TIER_THRESHOLDS
from app.models.chapter_mastery import ChapterMastery
import logging


class ArenaLeaderboardService:
    """
    Service for managing the Arena (竞技) leaderboard.
    """

    def __init__(self, db: Optional[AsyncSession]):
        self.db = db

    def get_tier_for_score(self, score: float) -> str:
        """
        Get tier based on total score.

        Args:
            score: Total accumulated score

        Returns:
            Tier name: bronze, silver, gold, platinum, diamond
        """
        # Check from highest to lowest
        for tier in ["diamond", "platinum", "gold", "silver", "bronze"]:
            if score >= TIER_THRESHOLDS[tier]:
                return tier
        return "bronze"

    def rank_profiles(self, profiles: list[dict]) -> list[dict]:
        """
        Rank profiles by stars (descending).

        Args:
            profiles: List of profile dicts with user_id and stars

        Returns:
            Sorted list with ranks
        """
        sorted_profiles = sorted(
            profiles,
            key=lambda x: x.get("stars", 0),
            reverse=True
        )

        # Add rank
        for i, profile in enumerate(sorted_profiles):
            profile["rank"] = i + 1

        return sorted_profiles

    async def get_leaderboard(
        self,
        course_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> list[dict]:
        """
        Get arena leaderboard for a course.

        Ranking order:
        1. Tier (diamond > platinum > gold > silver > bronze)
        2. Sub-tier (I > II > III > IV > V, i.e., lower number = higher rank)
        3. Stars (more stars = higher rank)

        Args:
            course_id: Course ID
            limit: Max number of results
            offset: Pagination offset

        Returns:
            List of leaderboard entries with rank, user info, tier and stars
        """
        if not self.db:
            return []

        from app.models.user import User
        from sqlalchemy import case

        # Define tier order (higher tier = higher rank)
        tier_order = case(
            (UserArenaProfile.tier == "king", 7),
            (UserArenaProfile.tier == "master", 6),
            (UserArenaProfile.tier == "diamond", 5),
            (UserArenaProfile.tier == "platinum", 4),
            (UserArenaProfile.tier == "gold", 3),
            (UserArenaProfile.tier == "silver", 2),
            (UserArenaProfile.tier == "bronze", 1),
            else_=0
        )

        # Query profiles with user info, ordered by tier (desc), sub_tier (asc), stars (desc)
        query = (
            select(UserArenaProfile, User)
            .join(User, UserArenaProfile.user_id == User.id)
            
            .order_by(
                tier_order.desc(),        # Higher tier first
                UserArenaProfile.sub_tier.asc(),  # Lower sub-tier first (I > II > III > IV > V)
                UserArenaProfile.stars.desc()     # More stars first
            )
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        rows = result.all()

        # If no arena profiles, return empty list
        if not rows:
            return []

        leaderboard = []
        for i, (profile, user) in enumerate(rows):
            leaderboard.append({
                "rank": offset + i + 1,
                "user_id": user.id,
                "username": user.username,
                "total_score": profile.total_score,  # Keep for backward compatibility
                "stars": profile.stars,
                "tier": profile.tier,
                "sub_tier": profile.sub_tier,
                "total_challenges": profile.total_challenges,
                "wins": profile.wins,
                "highest_difficulty": profile.highest_difficulty,
            })

        return leaderboard

    async def update_user_tier(self, user_id: str, course_id: int) -> str:
        """
        Update user's tier based on their total score.

        Args:
            user_id: User ID
            course_id: Course ID

        Returns:
            New tier
        """
        if not self.db:
            return "bronze"

        result = await self.db.execute(
            select(UserArenaProfile).where(
                UserArenaProfile.user_id == user_id,
            )
        )
        profile = result.scalar_one_or_none()

        if not profile:
            return "bronze"

        new_tier = self.get_tier_for_score(profile.total_score)
        profile.tier = new_tier
        await self.db.commit()

        return new_tier


class MasteryLeaderboardService:
    """
    Service for managing the Mastery (精进) leaderboard.

    Rankings are based on mastery_xp (精进之路经验值).
    """

    def __init__(self, db: Optional[AsyncSession]):
        self.db = db

    async def get_leaderboard(
        self,
        course_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> list[dict]:
        """
        Get mastery leaderboard for a course.

        Rankings are based on mastery_xp.

        Args:
            course_id: Course ID
            limit: Max number of results
            offset: Pagination offset

        Returns:
            List of leaderboard entries
        """
        if not self.db:
            return []

        from app.models.user import User
        from app.models.chapter import Chapter

        # Get total chapters for the course
        chapter_count_query = select(func.count()).select_from(Chapter).where(
            Chapter.course_id == course_id
        )
        chapter_count_result = await self.db.execute(chapter_count_query)
        total_chapters = chapter_count_result.scalar() or 1

        # Query users with mastery_xp > 0, ordered by mastery_xp descending
        # Also join with ChapterMastery to get chapter statistics
        query = (
            select(User)
            .where(User.mastery_xp > 0)
            .order_by(User.mastery_xp.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        users = result.scalars().all()

        if not users:
            return []

        # Get chapter mastery stats for each user
        user_ids = [u.id for u in users]
        mastery_query = (
            select(
                ChapterMastery.user_id,
                func.sum(ChapterMastery.mastery_score).label("total_mastery"),
                func.avg(ChapterMastery.mastery_score).label("avg_mastery"),
                func.count(ChapterMastery.id).label("chapters_practiced"),
                func.sum(
                    func.iif(ChapterMastery.mastery_score >= 85, 1, 0)
                ).label("mastered_chapters")
            )
            .where(
                
                ChapterMastery.user_id.in_(user_ids)
            )
            .group_by(ChapterMastery.user_id)
        )

        mastery_result = await self.db.execute(mastery_query)
        mastery_stats = {row.user_id: row for row in mastery_result.all()}

        leaderboard = []
        for i, user in enumerate(users):
            stats = mastery_stats.get(user.id)
            leaderboard.append({
                "rank": offset + i + 1,
                "user_id": user.id,
                "username": user.username,
                "mastery_xp": user.mastery_xp,
                "mastery_level": user.mastery_level,
                "total_mastery": round(stats.total_mastery, 2) if stats else 0,
                "avg_mastery": round(stats.avg_mastery, 2) if stats else 0,
                "chapters_practiced": stats.chapters_practiced if stats else 0,
                "mastered_chapters": stats.mastered_chapters if stats else 0,
                "total_chapters": total_chapters,
                "progress_pct": round((stats.chapters_practiced / total_chapters) * 100, 1) if stats else 0,
            })

        return leaderboard

    async def get_user_rank(self, user_id: str, course_id: int) -> Optional[int]:
        """
        Get user's rank in mastery leaderboard.

        Args:
            user_id: User ID
            course_id: Course ID (unused, kept for API compatibility)

        Returns:
            Rank or None if not ranked
        """
        if not self.db:
            return None

        from app.models.user import User

        # Query all users with mastery_xp > 0, ordered by mastery_xp
        query = (
            select(User.id)
            .where(User.mastery_xp > 0)
            .order_by(User.mastery_xp.desc())
        )

        result = await self.db.execute(query)
        user_ids = [row[0] for row in result.all()]

        if not user_ids:
            return None

        try:
            return user_ids.index(user_id) + 1
        except ValueError:
            return None


def get_arena_leaderboard_service(db: AsyncSession) -> ArenaLeaderboardService:
    """Factory function for the arena leaderboard service."""
    return ArenaLeaderboardService(db)


def get_mastery_leaderboard_service(db: AsyncSession) -> MasteryLeaderboardService:
    """Factory function for the mastery leaderboard service."""
    return MasteryLeaderboardService(db)


logger = logging.getLogger(__name__)
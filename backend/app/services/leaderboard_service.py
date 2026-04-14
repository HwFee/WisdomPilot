"""
Leaderboard Service

Implements leaderboard calculations for both:
1. Mastery Leaderboard (精进榜) - Based on chapter mastery progress
2. Arena Leaderboard (竞技榜) - Based on challenge scores
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.user_arena import UserArenaProfile, TIER_THRESHOLDS
from app.models.chapter_mastery import ChapterMastery


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
        Rank profiles by score (descending).

        Args:
            profiles: List of profile dicts with user_id and total_score

        Returns:
            Sorted list with ranks
        """
        sorted_profiles = sorted(
            profiles,
            key=lambda x: x.get("total_score", 0),
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

        Args:
            course_id: Course ID
            limit: Max number of results
            offset: Pagination offset

        Returns:
            List of leaderboard entries with rank, user info, and score
        """
        if not self.db:
            return []

        # Query profiles with user info
        from app.models.user import User

        query = (
            select(UserArenaProfile, User)
            .join(User, UserArenaProfile.user_id == User.id)
            .where(UserArenaProfile.course_id == course_id)
            .order_by(UserArenaProfile.total_score.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        rows = result.all()

        # If no arena profiles, return users with stage progress
        if not rows:
            from app.models.user_stage import UserStageProgress
            from app.models.stage import Stage

            stage_query = (
                select(UserStageProgress.user_id, func.count().label('stages_started'))
                .join(Stage, UserStageProgress.stage_id == Stage.id)
                .where(Stage.course_id == course_id)
                .group_by(UserStageProgress.user_id)
                .order_by(func.count().desc())
                .limit(limit)
            )
            stage_result = await self.db.execute(stage_query)
            stage_rows = stage_result.all()

            if stage_rows:
                user_ids = [row.user_id for row in stage_rows]
                user_query = select(User).where(User.id.in_(user_ids))
                user_result = await self.db.execute(user_query)
                users = {u.id: u for u in user_result.scalars().all()}

                leaderboard = []
                for i, row in enumerate(stage_rows):
                    user = users.get(row.user_id)
                    if user:
                        leaderboard.append({
                            "rank": offset + i + 1,
                            "user_id": user.id,
                            "username": user.username,
                            "total_score": 0,
                            "tier": "bronze",
                            "total_challenges": 0,
                            "wins": 0,
                            "highest_difficulty": 0,
                        })
                return leaderboard

            return []

        leaderboard = []
        for i, (profile, user) in enumerate(rows):
            leaderboard.append({
                "rank": offset + i + 1,
                "user_id": user.id,
                "username": user.username,
                "total_score": profile.total_score,
                "tier": profile.tier,
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
                UserArenaProfile.course_id == course_id
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

        Rankings are based on:
        1. Total mastery points (sum of mastery scores)
        2. Number of mastered chapters (score >= 85)
        3. Average mastery score

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

        # Aggregate mastery scores per user
        query = (
            select(
                ChapterMastery.user_id,
                func.sum(ChapterMastery.mastery_score).label("total_mastery"),
                func.avg(ChapterMastery.mastery_score).label("avg_mastery"),
                func.count(ChapterMastery.id).label("chapters_practiced"),
                func.sum(
                    func.iif(ChapterMastery.mastery_score >= 85, 1, 0)
                ).label("mastered_chapters")
            )
            .where(ChapterMastery.course_id == course_id)
            .group_by(ChapterMastery.user_id)
            .order_by(func.sum(ChapterMastery.mastery_score).desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        rows = result.all()

        # Get user info
        user_ids = [row.user_id for row in rows]

        # If no mastery records yet, return users who have stages in progress for this course
        if not user_ids:
            # Get users with stage progress in this course
            from app.models.user_stage import UserStageProgress
            from app.models.stage import Stage

            stage_query = (
                select(UserStageProgress.user_id, func.count().label('stages_started'))
                .join(Stage, UserStageProgress.stage_id == Stage.id)
                .where(Stage.course_id == course_id)
                .group_by(UserStageProgress.user_id)
                .order_by(func.count().desc())
                .limit(limit)
            )
            stage_result = await self.db.execute(stage_query)
            stage_rows = stage_result.all()

            if stage_rows:
                user_ids = [row.user_id for row in stage_rows]
                user_query = select(User).where(User.id.in_(user_ids))
                user_result = await self.db.execute(user_query)
                users = {u.id: u for u in user_result.scalars().all()}

                leaderboard = []
                for i, row in enumerate(stage_rows):
                    user = users.get(row.user_id)
                    if user:
                        leaderboard.append({
                            "rank": offset + i + 1,
                            "user_id": user.id,
                            "username": user.username,
                            "total_mastery": 0,
                            "avg_mastery": 0,
                            "chapters_practiced": 0,
                            "mastered_chapters": 0,
                            "total_chapters": total_chapters,
                            "progress_pct": 0,
                            "stages_started": row.stages_started,
                        })
                return leaderboard

            return []

        user_query = select(User).where(User.id.in_(user_ids))
        user_result = await self.db.execute(user_query)
        users = {u.id: u for u in user_result.scalars().all()}

        leaderboard = []
        for i, row in enumerate(rows):
            user = users.get(row.user_id)
            if user:
                leaderboard.append({
                    "rank": offset + i + 1,
                    "user_id": user.id,
                    "username": user.username,
                    "total_mastery": round(row.total_mastery or 0, 2),
                    "avg_mastery": round(row.avg_mastery or 0, 2),
                    "chapters_practiced": row.chapters_practiced,
                    "mastered_chapters": row.mastered_chapters or 0,
                    "total_chapters": total_chapters,
                    "progress_pct": round((row.chapters_practiced / total_chapters) * 100, 1),
                })

        return leaderboard

    async def get_user_rank(self, user_id: str, course_id: int) -> Optional[int]:
        """
        Get user's rank in mastery leaderboard.

        Args:
            user_id: User ID
            course_id: Course ID

        Returns:
            Rank or None if not ranked
        """
        if not self.db:
            return None

        # First try ChapterMastery-based ranking
        query = (
            select(ChapterMastery.user_id)
            .where(ChapterMastery.course_id == course_id)
            .group_by(ChapterMastery.user_id)
            .order_by(func.sum(ChapterMastery.mastery_score).desc())
        )

        result = await self.db.execute(query)
        user_ids = [row[0] for row in result.all()]

        # If no mastery records, use stage progress
        if not user_ids:
            from app.models.user_stage import UserStageProgress
            from app.models.stage import Stage

            stage_query = (
                select(UserStageProgress.user_id)
                .join(Stage, UserStageProgress.stage_id == Stage.id)
                .where(Stage.course_id == course_id)
                .group_by(UserStageProgress.user_id)
                .order_by(func.count().desc())
            )
            result = await self.db.execute(stage_query)
            user_ids = [row[0] for row in result.all()]

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

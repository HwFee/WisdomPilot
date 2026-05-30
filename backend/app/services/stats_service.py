"""Statistics Service - Aggregates learning analytics"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.stats import ChapterProgress, LearningSession, ActivityLog
from app.models.course import Course
from app.models.user_challenge import UserChallenge
import logging


class StatsService:
    """Service for aggregating and computing learning statistics"""

    async def get_user_stats(self, db: AsyncSession, user_id: str) -> dict:
        """Get comprehensive stats for a user"""
        # User info
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return {}

        # Chapter progress stats
        progress_result = await db.execute(
            select(ChapterProgress).where(ChapterProgress.user_id == user_id)
        )
        chapter_progress = list(progress_result.scalars().all())

        completed_chapters = [p for p in chapter_progress if p.status == "completed"]
        total_chapters = len(chapter_progress)

        # Learning sessions stats
        sessions_result = await db.execute(
            select(LearningSession).where(LearningSession.user_id == user_id)
        )
        sessions = list(sessions_result.scalars().all())
        total_time = sum(s.duration_seconds for s in sessions)

        # Activity stats
        activity_result = await db.execute(
            select(ActivityLog).where(ActivityLog.user_id == user_id)
        )
        list(activity_result.scalars().all())

        # Challenge stats
        challenge_result = await db.execute(
            select(UserChallenge).where(UserChallenge.user_id == user_id)
        )
        user_challenges = list(challenge_result.scalars().all())
        completed_challenges = [
            uc for uc in user_challenges if uc.status == "completed"
        ]

        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "level": user.mastery_level,
                "xp": user.xp,
                "streak_days": user.streak_days,
                "preferred_languages": user.preferred_languages,
            },
            "chapter_progress": {
                "total": total_chapters,
                "completed": len(completed_chapters),
                "in_progress": total_chapters - len(completed_chapters),
                "completion_rate": round(len(completed_chapters) / max(total_chapters, 1) * 100, 1),
            },
            "exercises": {
                "total": user.total_exercises,
                "correct": user.correct_exercises,
                "accuracy_rate": user.accuracy_rate,
            },
            "learning_time": {
                "total_seconds": total_time,
                "total_minutes": round(total_time / 60, 1),
                "total_hours": round(total_time / 3600, 1),
                "session_count": len(sessions),
            },
            "challenges": {
                "total": len(user_challenges),
                "completed": len(completed_challenges),
            },
            "xp_summary": {
                "total_xp": user.xp,
                "level": user.mastery_level,
                "xp_to_next_level": user.mastery_xp - user.xp,
            },
        }

    async def get_course_stats(self, db: AsyncSession, course_id: int) -> dict:
        """Get stats for a specific course"""
        course_result = await db.execute(
            select(Course).where(Course.id == course_id)
        )
        course = course_result.scalar_one_or_none()
        if not course:
            return {}

        from app.models.chapter import Chapter

        chapters_result = await db.execute(
            select(Chapter).where(Chapter.course_id == course_id)
        )
        chapters = list(chapters_result.scalars().all())

        # Count users who started this course
        chapter_ids = [ch.id for ch in chapters]
        if chapter_ids:
            progress_result = await db.execute(
                select(func.count(func.distinct(ChapterProgress.user_id)))
                .where(ChapterProgress.chapter_id.in_(chapter_ids))
            )
            enrolled_users = progress_result.scalar() or 0

            completed_result = await db.execute(
                select(func.count(func.distinct(ChapterProgress.user_id)))
                .where(
                    ChapterProgress.chapter_id.in_(chapter_ids),
                    ChapterProgress.status == "completed"
                )
            )
            completed_users = completed_result.scalar() or 0
        else:
            enrolled_users = 0
            completed_users = 0

        return {
            "course_id": course_id,
            "code": course.code,
            "name": course.name,
            "chapter_count": len(chapters),
            "enrolled_users": enrolled_users,
            "completed_users": completed_users,
            "completion_rate": round(completed_users / max(enrolled_users, 1) * 100, 1),
        }

    async def get_leaderboard(
        self, db: AsyncSession, limit: int = 10, offset: int = 0
    ) -> list[dict]:
        """Get XP-based leaderboard"""
        result = await db.execute(
            select(User)
            .order_by(User.xp.desc())
            .limit(limit)
            .offset(offset)
        )
        users = list(result.scalars().all())

        leaderboard = []
        for rank, user in enumerate(users, start=offset + 1):
            leaderboard.append({
                "rank": rank,
                "user_id": user.id,
                "username": user.username,
                "level": user.mastery_level,
                "xp": user.xp,
                "streak_days": user.streak_days,
                "accuracy_rate": user.accuracy_rate,
            })

        return leaderboard

    async def get_recent_activity(
        self, db: AsyncSession, user_id: str, limit: int = 10
    ) -> list[dict]:
        """Get recent activity for a user"""
        result = await db.execute(
            select(ActivityLog)
            .where(ActivityLog.user_id == user_id)
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
        )
        activities = list(result.scalars().all())

        return [
            {
                "id": a.id,
                "activity_type": a.activity_type,
                "description": a.description,
                "chapter_id": a.chapter_id,
                # 添加 UTC 时区标识，确保前端正确解析
                "created_at": a.created_at.isoformat() + "Z" if a.created_at else None,
                "details": a.extra_data,
            }
            for a in activities
        ]


stats_service = StatsService()


logger = logging.getLogger(__name__)
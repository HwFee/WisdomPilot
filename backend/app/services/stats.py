"""Service for learning statistics operations"""

from datetime import datetime, timedelta, date
from app.utils.time import utc_now
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
import logging

from app.models.stats import ChapterProgress, LearningSession, ActivityLog, ProgressStatus, ActivityType
from app.models.exercise import Exercise
from app.models.chapter import Chapter
from app.schemas.stats import (
    UpdateProgressRequest,
    StartSessionRequest,
    EndSessionRequest,
    LearningStatistics,
)
from app.services.wrong_question import wrong_question_service

logger = logging.getLogger(__name__)


class StatsService:
    """Service for managing learning statistics"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_progress(self, user_id: str) -> list[ChapterProgress]:
        """Get all chapter progress records for a user"""
        result = await self.db.execute(
            select(ChapterProgress)
            .where(ChapterProgress.user_id == user_id)
            .order_by(ChapterProgress.chapter_id)
        )
        return list(result.scalars().all())

    async def get_chapter_progress(
        self, user_id: str, chapter_id: int
    ) -> Optional[ChapterProgress]:
        """Get progress for a specific chapter"""
        result = await self.db.execute(
            select(ChapterProgress).where(
                ChapterProgress.user_id == user_id,
                ChapterProgress.chapter_id == chapter_id
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create_progress(
        self, user_id: str, chapter_id: int
    ) -> ChapterProgress:
        """Get existing progress or create new one"""
        progress = await self.get_chapter_progress(user_id, chapter_id)
        if progress is None:
            progress = ChapterProgress(
                user_id=user_id,
                chapter_id=chapter_id,
                status=ProgressStatus.NOT_STARTED.value,
                progress_percent=0,
                completed_subsections=[],
                completed_exercise_count=0,
                completed_exercises_by_subsection={},
                exercise_results={},
            )
            self.db.add(progress)
            await self.db.commit()
            await self.db.refresh(progress)
        return progress

    async def update_chapter_progress(
        self, user_id: str, chapter_id: int, data: UpdateProgressRequest
    ) -> ChapterProgress:
        """Update chapter progress and collect wrong questions."""
        progress = await self.get_or_create_progress(user_id, chapter_id)

        # Track wrong exercises before applying new results
        old_results = progress.exercise_results or {}

        self._apply_status(progress, data)
        self._apply_progress_percent(progress, data)
        self._apply_completed_subsections(progress, data)
        self._apply_completed_exercises_by_subsection(progress, data)
        await self._apply_exercise_results_with_wrong_collection(
            progress, data, user_id, chapter_id, old_results
        )
        await self.db.commit()
        await self.db.refresh(progress)
        return progress

    def _apply_status(self, progress: ChapterProgress, data: UpdateProgressRequest) -> None:
        """Handle status changes and timestamps."""
        if data.status is None:
            return
        progress.status = data.status
        if data.status == ProgressStatus.IN_PROGRESS.value and progress.started_at is None:
            progress.started_at = utc_now()
        elif data.status == ProgressStatus.COMPLETED.value:
            progress.completed_at = utc_now()

    def _apply_progress_percent(self, progress: ChapterProgress, data: UpdateProgressRequest) -> None:
        """Handle percentage and auto-status."""
        if data.progress_percent is None:
            return
        progress.progress_percent = min(100, max(0, data.progress_percent))
        if progress.progress_percent == 100 and progress.status != ProgressStatus.COMPLETED.value:
            progress.status = ProgressStatus.COMPLETED.value
            progress.completed_at = utc_now()
        elif 0 < progress.progress_percent < 100 and progress.status == ProgressStatus.NOT_STARTED.value:
            progress.status = ProgressStatus.IN_PROGRESS.value
            progress.started_at = progress.started_at or utc_now()

    def _apply_completed_subsections(self, progress: ChapterProgress, data: UpdateProgressRequest) -> None:
        """Handle subsection tracking and derived progress."""
        if data.completed_exercise_count is not None:
            progress.completed_exercise_count = data.completed_exercise_count
            total_exercises = data.total_exercises if data.total_exercises else 14
            progress.progress_percent = min(100, int(data.completed_exercise_count / total_exercises * 100))
            if progress.progress_percent > 0 and progress.status == ProgressStatus.NOT_STARTED.value:
                progress.status = ProgressStatus.IN_PROGRESS.value
                progress.started_at = progress.started_at or utc_now()
            if progress.progress_percent == 100:
                progress.status = ProgressStatus.COMPLETED.value
                progress.completed_at = progress.completed_at or utc_now()
            elif progress.progress_percent < 100 and progress.status == ProgressStatus.COMPLETED.value:
                # 进度从100%降下来了，状态也要改
                progress.status = ProgressStatus.IN_PROGRESS.value
                progress.completed_at = None
            # 从 completed_exercises_by_subsection 推导已完成的小节
            if data.completed_exercises_by_subsection is not None:
                # 小节索引：凡是在 dict 中有记录的，说明该小节有练习被做过
                completed_subsections_from_exercises = sorted([
                    int(sidx) for sidx, exercises in data.completed_exercises_by_subsection.items()
                    if exercises and len(exercises) > 0
                ])
                if completed_subsections_from_exercises:
                    progress.completed_subsections = completed_subsections_from_exercises
        elif data.completed_subsections is not None:
            total_subsections = 14
            progress.completed_subsections = data.completed_subsections
            progress.progress_percent = min(100, int(len(data.completed_subsections) / total_subsections * 100))
            if progress.progress_percent == 100:
                if progress.status != ProgressStatus.COMPLETED.value:
                    progress.status = ProgressStatus.COMPLETED.value
                    progress.completed_at = progress.completed_at or utc_now()
            elif progress.progress_percent > 0:
                if progress.status == ProgressStatus.NOT_STARTED.value:
                    progress.status = ProgressStatus.IN_PROGRESS.value
                    progress.started_at = progress.started_at or utc_now()
                elif progress.status == ProgressStatus.COMPLETED.value:
                    # 进度从100%降下来了
                    progress.status = ProgressStatus.IN_PROGRESS.value
                    progress.completed_at = None

    def _apply_completed_exercises_by_subsection(self, progress: ChapterProgress, data: UpdateProgressRequest) -> None:
        """Handle exercise dict."""
        if data.completed_exercises_by_subsection is not None:
            progress.completed_exercises_by_subsection = data.completed_exercises_by_subsection

    async def _apply_exercise_results_with_wrong_collection(
        self,
        progress: ChapterProgress,
        data: UpdateProgressRequest,
        user_id: str,
        chapter_id: int,
        old_results: dict,
    ) -> None:
        """Handle exercise results and collect wrong questions.

        Exercise key format: chapterId-subsectionIndex-exerciseId
        Result values: "correct" or "wrong"
        """
        if data.exercise_results is None:
            return

        # 如果是空字典，显式清除所有结果
        if data.exercise_results == {}:
            progress.exercise_results = {}
            return

        # Merge with existing results
        existing = progress.exercise_results or {}
        merged = {**existing, **data.exercise_results}
        progress.exercise_results = merged

        # Get chapter to find course_id (once for all exercises)
        ch_result = await self.db.execute(
            select(Chapter).where(Chapter.id == chapter_id)
        )
        chapter = ch_result.scalar_one_or_none()
        course_id = chapter.course_id if chapter else 0

        # Find newly wrong exercises and collect them
        for exercise_key, result in data.exercise_results.items():
            # Only process new wrong answers
            if result != 'wrong':
                continue
            if old_results.get(exercise_key) == 'wrong':
                continue  # Already recorded as wrong

            # Parse exercise key: chapterId-subsectionIndex-exerciseId
            try:
                parts = exercise_key.split('-')
                if len(parts) >= 3:
                    ex_chapter_id = int(parts[0])
                    subsection_index = int(parts[1])
                    exercise_id = int(parts[2])

                    logger.info(f"[错题收集] 处理错题: key={exercise_key}, chapter_id={ex_chapter_id}, exercise_id={exercise_id}")

                    # Try to find real Exercise in database
                    ex_result = await self.db.execute(
                        select(Exercise).where(Exercise.id == exercise_id)
                    )
                    exercise = ex_result.scalar_one_or_none()

                    if exercise:
                        # Found real Exercise - use standard collection
                        logger.info(f"[错题收集] 找到真实 Exercise: id={exercise.id}, type={exercise.type}")
                        await wrong_question_service.collect_wrong_question(
                            db=self.db,
                            user_id=user_id,
                            exercise=exercise,
                            user_answer=None,
                            course_id=course_id,
                            chapter_id=ex_chapter_id,
                        )
                        logger.info(f"[错题收集] 已收集到错题本 (真实 Exercise)")
                    else:
                        # No real Exercise - use exercise_key based collection
                        # This handles frontend hardcoded exercises
                        logger.info(f"[错题收集] 未找到真实 Exercise，使用 exercise_key 方式收集")
                        await wrong_question_service.collect_wrong_question_by_key(
                            db=self.db,
                            user_id=user_id,
                            exercise_key=exercise_key,
                            user_answer=None,
                            course_id=course_id,
                            chapter_id=ex_chapter_id,
                            exercise_type="choice",  # Default to choice
                            knowledge_points=[],
                        )
                        logger.info(f"[错题收集] 已收集到错题本 (exercise_key)")
            except (ValueError, IndexError) as e:
                # Skip invalid exercise keys
                logger.warning(f"[错题收集] 跳过无效的 exercise_key: {exercise_key}, error={e}")
                continue

    def _apply_exercise_results(self, progress: ChapterProgress, data: UpdateProgressRequest) -> None:
        """Handle exercise results (correct/wrong per exercise)."""
        if data.exercise_results is not None:
            # 如果是空字典，显式清除所有结果
            if data.exercise_results == {}:
                progress.exercise_results = {}
            else:
                # Merge with existing results (don't overwrite, just update)
                existing = progress.exercise_results or {}
                merged = {**existing, **data.exercise_results}
                progress.exercise_results = merged

    async def start_session(
        self, user_id: str, data: StartSessionRequest
    ) -> LearningSession:
        """Start a new learning session, ending any existing active one"""
        # End any existing active sessions
        await self.end_all_active_sessions(user_id)

        session = LearningSession(
            user_id=user_id,
            chapter_id=data.chapter_id,
            subsection_index=data.subsection_index,
            is_active=True,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def end_session(
        self, user_id: str, session_id: str, data: EndSessionRequest
    ) -> Optional[LearningSession]:
        """End a learning session"""
        # Expire any cached session data to force fresh read
        self.db.expire_all()

        result = await self.db.execute(
            select(LearningSession).where(
                LearningSession.id == session_id,
                LearningSession.user_id == user_id
            )
        )
        session = result.scalar_one_or_none()

        if session:
            session.is_active = False
            session.ended_at = utc_now()
            session.duration_seconds = data.duration_seconds
            await self.db.commit()
            await self.db.refresh(session)

        return session

    async def end_all_active_sessions(self, user_id: str) -> None:
        """End all active sessions for a user"""
        # Expire any cached session data to force fresh read
        self.db.expire_all()

        result = await self.db.execute(
            select(LearningSession).where(
                LearningSession.user_id == user_id,
                LearningSession.is_active.is_(True)
            )
        )
        sessions = result.scalars().all()
        for session in sessions:
            session.is_active = False
            session.ended_at = utc_now()
        await self.db.commit()
    async def get_active_session(self, user_id: str) -> Optional[LearningSession]:
        """Get current active session for a user"""
        result = await self.db.execute(
            select(LearningSession).where(
                LearningSession.user_id == user_id,
                LearningSession.is_active.is_(True)
            )
        )
        session = result.scalar_one_or_none()
        return session

    async def update_session_subsection(
        self, user_id: str, session_id: str, new_subsection_index: int
    ) -> Optional[LearningSession]:
        """Update the subsection index for an active session"""
        result = await self.db.execute(
            select(LearningSession).where(
                LearningSession.id == session_id,
                LearningSession.user_id == user_id,
                LearningSession.is_active.is_(True)
            )
        )
        session = result.scalar_one_or_none()
        if session:
            session.subsection_index = new_subsection_index
            await self.db.commit()
            await self.db.refresh(session)
        return session

    async def get_user_sessions(
        self, user_id: str, limit: int = 50
    ) -> list[LearningSession]:
        """Get user learning sessions"""
        result = await self.db.execute(
            select(LearningSession)
            .where(LearningSession.user_id == user_id)
            .order_by(desc(LearningSession.started_at))
            .limit(limit)
        )
        return list(result.scalars().all())
    async def get_statistics(self, user_id: str) -> LearningStatistics:
        """Get aggregated learning statistics"""
        # Get all progress records
        progress_list = await self.get_user_progress(user_id)

        # Count completed and in progress
        completed = sum(1 for p in progress_list if p.status == ProgressStatus.COMPLETED.value)
        in_progress = sum(1 for p in progress_list if p.status == ProgressStatus.IN_PROGRESS.value)

        # Count total completed subsections
        total_subsections = sum(len(p.completed_subsections or []) for p in progress_list)

        # Get session stats
        result = await self.db.execute(
            select(
                func.count(LearningSession.id).label("total_sessions"),
                func.sum(LearningSession.duration_seconds).label("total_time")
            )
            .where(
                LearningSession.user_id == user_id,
                LearningSession.is_active.is_(False)
            )
        )
        session_stats = result.one()

        total_time = session_stats.total_time or 0
        total_sessions = session_stats.total_sessions or 0

        # Calculate streak
        current_streak, longest_streak = await self._calculate_streaks(user_id)

        return LearningStatistics(
            total_learning_time_seconds=int(total_time),
            total_sessions=total_sessions,
            completed_chapters=completed,
            in_progress_chapters=in_progress,
            total_subsections_completed=total_subsections,
            current_streak=current_streak,
            longest_streak=longest_streak,
        )
    async def _calculate_streaks(self, user_id: str) -> tuple[int, int]:
        """Calculate current and longest learning streaks."""
        result = await self.db.execute(
            select(func.date(ActivityLog.created_at))
            .where(ActivityLog.user_id == user_id)
            .distinct()
            .order_by(desc(func.date(ActivityLog.created_at)))
            .limit(60)
        )
        raw_dates = [row[0] for row in result.all()]

        if not raw_dates:
            return 0, 0

        today = date.today()

        # Normalize all dates to date objects
        dates = set()
        for d in raw_dates:
            if isinstance(d, str):
                d = datetime.fromisoformat(d).date()
            dates.add(d)

        sorted_dates = sorted(dates, reverse=True)

        longest_streak = self._longest_consecutive_streak(sorted_dates)

        # Calculate current streak: must start from today
        # If no activity today, current streak is 0
        current_streak = 0
        if today in dates:
            current_streak = self._count_consecutive_from(today, dates)

        return current_streak, longest_streak

    @staticmethod
    def _count_consecutive_from(start_date: date, date_set: set) -> int:
        """Count consecutive days backward from start_date."""
        streak = 0
        current = start_date
        while current in date_set:
            streak += 1
            current -= timedelta(days=1)
        return streak

    @staticmethod
    def _longest_consecutive_streak(sorted_dates: list) -> int:
        """Find the longest run of consecutive days."""
        if not sorted_dates:
            return 0
        longest = 1
        current = 1
        for i in range(1, len(sorted_dates)):
            if sorted_dates[i - 1] - sorted_dates[i] == timedelta(days=1):
                current += 1
            else:
                longest = max(longest, current)
                current = 1
        return max(longest, current)
    async def log_activity(
        self,
        user_id: str,
        activity_type: str,
        description: str,
        chapter_id: Optional[int] = None,
        subsection_index: Optional[int] = None,
        extra_data: Optional[dict] = None,
    ) -> ActivityLog:
        """Log a learning activity"""
        activity = ActivityLog(
            user_id=user_id,
            activity_type=activity_type,
            chapter_id=chapter_id,
            subsection_index=subsection_index,
            description=description,
            extra_data=extra_data or {},
        )
        self.db.add(activity)
        await self.db.commit()
        await self.db.refresh(activity)
        return activity

    async def get_activities(
        self, user_id: str, limit: int = 20
    ) -> list[ActivityLog]:
        """Get user recent activities"""
        result = await self.db.execute(
            select(ActivityLog)
            .where(ActivityLog.user_id == user_id)
            .order_by(desc(ActivityLog.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    # ============ Exercise Answers (Mock Data) ============
    # TODO: 后续可以从数据库题库表读取，当前用内存数据演示

    MOCK_EXERCISE_ANSWERS = {
        1: {
            0: {
                2: 2,  # 第2题正确答案是索引2
                3: 0,  # 第3题正确答案是索引0
            }
        }
    }

    async def get_chapter_exercise_answers(self, chapter_id: int) -> list[dict]:
        """Get exercise answers for a chapter (from mock data or database)"""
        answers = []
        chapter_answers = self.MOCK_EXERCISE_ANSWERS.get(chapter_id, {})
        for subsection_index, exercises in chapter_answers.items():
            for exercise_id, correct_answer_index in exercises.items():
                answers.append({
                    "subsection_index": subsection_index,
                    "exercise_id": exercise_id,
                    "correct_answer_index": correct_answer_index,
                })
        return answers

    # ============ Daily Trends ============

    async def get_daily_exercises_trend(self, user_id: str, days: int = 7) -> list[dict]:
        """Get daily exercises count for the past N days"""
        now = utc_now()
        trends = []

        for i in range(days):
            day_start = (now - timedelta(days=i)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_end = day_start + timedelta(days=1)

            # Count exercises completed on this day
            result = await self.db.execute(
                select(func.count(ActivityLog.id))
                .where(
                    ActivityLog.user_id == user_id,
                    ActivityLog.activity_type == "exercise_complete",
                    ActivityLog.created_at >= day_start,
                    ActivityLog.created_at < day_end,
                )
            )
            count = result.scalar() or 0

            trends.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "count": count,
            })

        return trends  # Most recent first

    async def get_daily_accuracy_trend(self, user_id: str, days: int = 7) -> list[dict]:
        """Get daily accuracy rate for the past N days"""
        now = utc_now()
        trends = []

        for i in range(days):
            day_start = (now - timedelta(days=i)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_end = day_start + timedelta(days=1)

            # Get all exercise results for this day from activity logs
            result = await self.db.execute(
                select(ActivityLog)
                .where(
                    ActivityLog.user_id == user_id,
                    ActivityLog.activity_type == "exercise_complete",
                    ActivityLog.created_at >= day_start,
                    ActivityLog.created_at < day_end,
                )
            )
            activities = result.scalars().all()

            total = len(activities)
            correct = sum(1 for a in activities if a.extra_data.get("is_correct", False))
            accuracy = round(correct / total * 100, 1) if total > 0 else 0.0

            trends.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "accuracy": accuracy,
                "total": total,
                "correct": correct,
            })

        return trends  # Most recent first

    async def get_daily_time_trend(self, user_id: str, days: int = 7) -> list[dict]:
        """Get daily learning time for the past N days"""
        now = utc_now()
        trends = []

        for i in range(days):
            day_start = (now - timedelta(days=i)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_end = day_start + timedelta(days=1)

            # Sum duration of sessions that ended on this day
            result = await self.db.execute(
                select(func.sum(LearningSession.duration_seconds))
                .where(
                    LearningSession.user_id == user_id,
                    LearningSession.ended_at >= day_start,
                    LearningSession.ended_at < day_end,
                )
            )
            total_seconds = result.scalar() or 0
            minutes = round(total_seconds / 60)

            trends.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "minutes": minutes,
            })

        return trends  # Most recent first
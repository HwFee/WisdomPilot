from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.exercise import Exercise
from app.models.stats import ActivityLog
from app.services.challenge_path.errors import ChallengeProgressNotFoundError


@dataclass(frozen=True)
class ChallengeSubmissionState:
    progress: ArenaExerciseProgress
    next_unlocked: bool


class ChallengeSubmissionStateService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def apply_attempt(
        self,
        *,
        user_id: str,
        exercise: Exercise,
        code: str,
        language: str,
        is_correct: bool,
        time_spent: int | None,
        hint_used: bool,
    ) -> ChallengeSubmissionState:
        result = await self.db.execute(
            select(ArenaExerciseProgress)
            .where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.exercise_id == exercise.id,
            )
            .with_for_update()
        )
        progress = result.scalar_one_or_none()
        if progress is None:
            raise ChallengeProgressNotFoundError(exercise.id)

        now = datetime.utcnow()
        progress.is_completed = is_correct
        progress.is_correct = is_correct
        progress.last_attempt_at = now
        progress.attempt_count += 1
        progress.current_language = language
        progress.saved_codes = {**(progress.saved_codes or {}), language: code}
        if progress.first_attempt_at is None:
            progress.first_attempt_at = now
        if is_correct and progress.correct_at is None:
            progress.correct_at = now
        if time_spent is not None:
            progress.time_spent = time_spent
        if hint_used:
            progress.hint_used = True
        if progress.attempt_count == 1:
            progress.first_attempt_correct = is_correct

        self.db.add(self._build_activity(user_id, exercise, progress, is_correct))
        next_unlocked = await self._unlock_next(user_id, progress, is_correct)
        await self.db.flush()
        return ChallengeSubmissionState(progress, next_unlocked)

    @staticmethod
    def _build_activity(
        user_id: str,
        exercise: Exercise,
        progress: ArenaExerciseProgress,
        is_correct: bool,
    ) -> ActivityLog:
        content = exercise.content or {}
        exercise_title = (
            content.get("title")
            or content.get("text")
            or f"挑战题目 {progress.exercise_index + 1}"
        )
        return ActivityLog(
            user_id=user_id,
            activity_type="exercise_complete",
            chapter_id=exercise.chapter_id,
            description=f"挑战之路完成练习：{exercise_title}",
            extra_data={
                "learning_path": "challenge",
                "learning_path_label": "挑战之路",
                "exercise_id": exercise.id,
                "exercise_index": progress.exercise_index,
                "exercise_title": exercise_title,
                "is_correct": is_correct,
                "difficulty": exercise.difficulty,
            },
        )

    async def _unlock_next(
        self,
        user_id: str,
        progress: ArenaExerciseProgress,
        is_correct: bool,
    ) -> bool:
        if not is_correct:
            return False
        result = await self.db.execute(
            select(ArenaExerciseProgress)
            .where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.exercise_index > progress.exercise_index,
            )
            .order_by(ArenaExerciseProgress.exercise_index)
            .limit(1)
            .with_for_update()
        )
        next_progress = result.scalar_one_or_none()
        if next_progress is None or next_progress.is_unlocked:
            return False
        next_progress.is_unlocked = True
        return True

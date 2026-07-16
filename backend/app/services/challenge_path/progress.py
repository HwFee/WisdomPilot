"""Challenge progress service - tracking and retrieving exercise progress."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.exercise import Exercise
from app.services.challenge_path.errors import (
    ChallengeExerciseDetailNotFoundError,
    ChallengeExerciseLockedError,
    ChallengeProgressIndexNotFoundError,
    InvalidChallengeExerciseIndexError,
)

DEFAULT_EXERCISE_TIME_LIMIT = 1000
DEFAULT_EXERCISE_MEMORY_LIMIT = 256
PROGRAMMING_EXERCISE_TYPE = "programming"


class ChallengeProgressService:
    """Service for challenge path progress operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_user_progress(
        self, user_id: str
    ) -> list[ArenaExerciseProgress]:
        """Get all progress records for user's challenge path."""
        result = await self.db.execute(
            select(ArenaExerciseProgress)
            .where(ArenaExerciseProgress.user_id == user_id)
            .order_by(ArenaExerciseProgress.exercise_index)
        )
        return list(result.scalars().all())

    async def get_exercise_count(self, user_id: str) -> int:
        """Get total exercise count for user's challenge path."""
        result = await self.db.execute(
            select(func.count())
            .select_from(ArenaExerciseProgress)
            .where(ArenaExerciseProgress.user_id == user_id)
        )
        return result.scalar() or 0

    async def get_exercises_for_progress(
        self,
        progress_records: list[ArenaExerciseProgress],
    ) -> list[Exercise]:
        """Fetch Exercise objects from progress records."""
        exercise_ids = [p.exercise_id for p in progress_records]
        if not exercise_ids:
            return []

        result = await self.db.execute(
            select(Exercise).where(Exercise.id.in_(exercise_ids))
        )
        exercises_map = {ex.id: ex for ex in result.scalars().all()}

        return [
            exercises_map[p.exercise_id]
            for p in progress_records
            if p.exercise_id in exercises_map
        ]

    @staticmethod
    def _current_exercise_index(
        progress_records: list[ArenaExerciseProgress],
    ) -> int:
        current_index = 0
        for index, progress in enumerate(progress_records):
            if not progress.is_completed:
                return index
            current_index = index + 1
        return min(current_index, len(progress_records) - 1)

    @staticmethod
    def _build_full_content(exercise: Exercise) -> dict:
        content = exercise.content or {}
        return {
            "text": content.get("text", ""),
            "title": content.get("title", ""),
            "description": content.get("description", ""),
            "options": content.get("options", []),
            "code_template": content.get("code_template", ""),
            "input_format": content.get("input_format", ""),
            "output_format": content.get("output_format", ""),
            "sample_input": content.get("sample_input", ""),
            "sample_output": content.get("sample_output", ""),
            "samples": content.get("samples", []),
            "time_limit": content.get(
                "time_limit", DEFAULT_EXERCISE_TIME_LIMIT
            ),
            "memory_limit": content.get(
                "memory_limit", DEFAULT_EXERCISE_MEMORY_LIMIT
            ),
        }

    def _build_progress_item(
        self,
        *,
        progress: ArenaExerciseProgress,
        exercise: Exercise | None,
        lite: bool,
    ) -> dict | None:
        if exercise is None:
            return None
        item = {
            "exercise_id": progress.exercise_id,
            "exercise_index": progress.exercise_index,
            "is_completed": progress.is_completed,
            "is_correct": progress.is_correct,
            "is_unlocked": progress.is_unlocked,
            "saved_code": (progress.saved_codes or {}).get(
                progress.current_language, ""
            ),
            "current_language": progress.current_language,
            "title": (exercise.content or {}).get(
                "title", f"题目 {progress.exercise_index + 1}"
            ),
            "difficulty": exercise.difficulty,
            "type": exercise.type,
            "z_id": exercise.z_id,
        }
        if not lite:
            item["content"] = self._build_full_content(exercise)
            item["knowledge_points"] = exercise.knowledge_points or []
            item["test_cases"] = (
                exercise.test_cases
                if exercise.type == PROGRAMMING_EXERCISE_TYPE
                else None
            )
        return item

    async def get_progress(self, user_id: str, lite: bool = True) -> dict:
        """Get current progress for challenge path.

        Args:
            lite: If True, only return metadata (title, difficulty, progress state).
        """
        progress_records = await self.list_user_progress(user_id)

        if not progress_records:
            return {
                "total_exercises": 0,
                "exercises": [],
                "correct_count": 0,
                "completed_count": 0,
                "total_stars_earned": 0,
                "current_index": 0,
            }

        exercise_ids = [progress.exercise_id for progress in progress_records]
        exercises_result = await self.db.execute(
            select(Exercise).where(Exercise.id.in_(exercise_ids))
        )
        exercises = {
            exercise.id: exercise
            for exercise in exercises_result.scalars().all()
        }
        progress_list = [
            item
            for progress in progress_records
            if (
                item := self._build_progress_item(
                    progress=progress,
                    exercise=exercises.get(progress.exercise_id),
                    lite=lite,
                )
            ) is not None
        ]

        return {
            "total_exercises": len(progress_records),
            "exercises": progress_list,
            "correct_count": sum(
                1 for progress in progress_records if progress.is_correct
            ),
            "completed_count": sum(
                1 for progress in progress_records if progress.is_completed
            ),
            "total_stars_earned": sum(
                progress.stars_awarded for progress in progress_records
            ),
            "current_index": self._current_exercise_index(progress_records),
        }

    async def get_existing_exercise_detail(
        self,
        *,
        user_id: str,
        exercise_id: int,
    ) -> dict | None:
        """Get an existing exercise and progress detail without mutation."""
        result = await self.db.execute(
            select(ArenaExerciseProgress, Exercise)
            .join(
                Exercise,
                ArenaExerciseProgress.exercise_id == Exercise.id,
            )
            .where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.exercise_id == exercise_id,
            )
        )
        row = result.one_or_none()
        if row is None:
            return None
        progress, exercise = row
        return self.build_exercise_detail(
            progress=progress,
            exercise=exercise,
        )

    def build_exercise_detail(
        self,
        *,
        progress: ArenaExerciseProgress,
        exercise: Exercise,
    ) -> dict:
        return {
            "exercise_id": progress.exercise_id,
            "exercise_index": progress.exercise_index,
            "is_completed": progress.is_completed,
            "is_correct": progress.is_correct,
            "is_unlocked": progress.is_unlocked,
            "saved_code": (progress.saved_codes or {}).get(
                progress.current_language, ""
            ),
            "current_language": progress.current_language,
            "title": (exercise.content or {}).get(
                "title", f"题目 {progress.exercise_index + 1}"
            ),
            "difficulty": exercise.difficulty,
            "exercise": exercise,
        }

    async def get_exercise_by_index(
        self, user_id: str, exercise_index: int
    ) -> dict | None:
        """Get exercise by its index in the challenge path."""
        result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.exercise_index == exercise_index,
            )
        )
        progress = result.scalar_one_or_none()
        if not progress:
            return None

        return await self.get_existing_exercise_detail(
            user_id=user_id,
            exercise_id=progress.exercise_id,
        )

    async def _get_switch_progress(
        self,
        *,
        user_id: str,
        target_index: int,
    ) -> ArenaExerciseProgress:
        total = await self.get_exercise_count(user_id)
        if target_index < 0 or target_index >= total:
            raise InvalidChallengeExerciseIndexError()

        result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.exercise_index == target_index,
            )
        )
        progress = result.scalar_one_or_none()
        if progress is None:
            raise ChallengeProgressIndexNotFoundError()
        if not progress.is_unlocked:
            raise ChallengeExerciseLockedError()
        return progress

    async def switch_exercise(self, user_id: str, target_index: int) -> dict:
        """Switch to a different exercise by index."""
        progress = await self._get_switch_progress(
            user_id=user_id,
            target_index=target_index,
        )

        ex_result = await self.db.execute(
            select(Exercise).where(Exercise.id == progress.exercise_id)
        )
        exercise = ex_result.scalar_one_or_none()
        if exercise is None:
            raise ChallengeExerciseDetailNotFoundError()

        return {
            "exercise_id": progress.exercise_id,
            "saved_code": (progress.saved_codes or {}).get(
                progress.current_language, ""
            ),
            "current_language": progress.current_language,
            "is_completed": progress.is_completed,
            "is_correct": progress.is_correct,
            "exercise": exercise,
        }

    async def get_recent_exercises(
        self, user_id: str, limit: int = 3
    ) -> list[dict]:
        result = await self.db.execute(
            select(ArenaExerciseProgress, Exercise)
            .join(Exercise, ArenaExerciseProgress.exercise_id == Exercise.id)
            .where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.is_completed,
            )
            .order_by(ArenaExerciseProgress.last_attempt_at.desc())
            .limit(limit)
        )
        rows = result.all()

        recent = []
        for progress, exercise in rows:
            content = exercise.content or {}
            title = (
                content.get("title", "")
                or content.get("text", "")[:30]
                or f"题目 {exercise.id}"
            )
            recent.append({
                "exercise_id": exercise.id,
                "title": title,
                "is_correct": progress.is_correct,
                "difficulty": exercise.difficulty,
            })
        return recent

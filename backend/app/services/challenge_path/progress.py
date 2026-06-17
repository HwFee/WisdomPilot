"""Challenge progress service - tracking and retrieving exercise progress."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.exercise import Exercise

DEFAULT_CHALLENGE_LANGUAGE = "python"


class ChallengeProgressService:
    """Service for challenge path progress operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_user_progress(self, user_id: str) -> list[ArenaExerciseProgress]:
        """Get all progress records for user's challenge path."""
        result = await self.db.execute(
            select(ArenaExerciseProgress)
            .where(ArenaExerciseProgress.user_id == user_id)
            .order_by(ArenaExerciseProgress.exercise_index)
        )
        return list(result.scalars().all())

    async def _get_exercise_count(self, user_id: str) -> int:
        """Get total exercise count for user's challenge path."""
        result = await self.db.execute(
            select(func.count())
            .select_from(ArenaExerciseProgress)
            .where(ArenaExerciseProgress.user_id == user_id)
        )
        return result.scalar() or 0

    async def _get_exercises_from_progress(
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

    async def get_progress(self, user_id: str, lite: bool = True) -> dict:
        """Get current progress for challenge path.

        Args:
            lite: If True, only return metadata (title, difficulty, progress state).
        """
        progress_records = await self._get_user_progress(user_id)

        if not progress_records:
            return {
                "total_exercises": 0,
                "exercises": [],
                "correct_count": 0,
                "completed_count": 0,
                "total_stars_earned": 0,
                "current_index": 0,
            }

        exercise_ids = [p.exercise_id for p in progress_records]
        exercises_result = await self.db.execute(
            select(Exercise).where(Exercise.id.in_(exercise_ids))
        )
        exercises = {ex.id: ex for ex in exercises_result.scalars().all()}

        current_index = 0
        for i, p in enumerate(progress_records):
            if not p.is_completed:
                current_index = i
                break
            current_index = i + 1
        if current_index >= len(progress_records):
            current_index = len(progress_records) - 1

        progress_list = []
        for p in progress_records:
            ex = exercises.get(p.exercise_id)
            if ex:
                item = {
                    "exercise_id": p.exercise_id,
                    "exercise_index": p.exercise_index,
                    "is_completed": p.is_completed,
                    "is_correct": p.is_correct,
                    "is_unlocked": p.is_unlocked,
                    "saved_code": (p.saved_codes or {}).get(p.current_language, ""),
                    "current_language": p.current_language,
                    "title": (ex.content or {}).get(
                        "title", f"题目 {p.exercise_index + 1}"
                    ),
                    "difficulty": ex.difficulty,
                    "type": ex.type,
                    "z_id": ex.z_id,
                }

                if not lite:
                    item["content"] = {
                        "text": (ex.content or {}).get("text", ""),
                        "title": (ex.content or {}).get("title", ""),
                        "description": (ex.content or {}).get("description", ""),
                        "options": (ex.content or {}).get("options", []),
                        "code_template": (ex.content or {}).get("code_template", ""),
                        "input_format": (ex.content or {}).get("input_format", ""),
                        "output_format": (ex.content or {}).get("output_format", ""),
                        "sample_input": (ex.content or {}).get("sample_input", ""),
                        "sample_output": (ex.content or {}).get("sample_output", ""),
                        "samples": (ex.content or {}).get("samples", []),
                        "time_limit": (ex.content or {}).get("time_limit", 1000),
                        "memory_limit": (ex.content or {}).get("memory_limit", 256),
                    }
                    item["knowledge_points"] = ex.knowledge_points or []
                    item["test_cases"] = ex.test_cases if ex.type == "programming" else None

                progress_list.append(item)

        correct_count = sum(1 for p in progress_records if p.is_correct)
        completed_count = sum(1 for p in progress_records if p.is_completed)
        total_stars_earned = sum(p.stars_awarded for p in progress_records)

        return {
            "total_exercises": len(progress_records),
            "exercises": progress_list,
            "correct_count": correct_count,
            "completed_count": completed_count,
            "total_stars_earned": total_stars_earned,
            "current_index": current_index,
        }

    async def get_exercise_by_id(
        self, user_id: str, exercise_id: int
    ) -> dict | None:
        """Get specific exercise progress by exercise_id."""
        result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.exercise_id == exercise_id,
            )
        )
        progress = result.scalar_one_or_none()
        if not progress:
            exercise_result = await self.db.execute(
                select(Exercise).where(
                    Exercise.id == exercise_id,
                    Exercise.is_verified,
                )
            )
            exercise = exercise_result.scalar_one_or_none()
            if not exercise:
                return None

            exercise_index = await self._get_exercise_count(user_id)
            from app.services.challenge_path.selection import ChallengeSelectionService

            selection_service = ChallengeSelectionService(self.db)
            await selection_service._create_progress_for_selected_exercises(
                user_id, [exercise], start_index=exercise_index
            )
            await self.db.flush()

            return {
                "exercise_id": exercise.id,
                "exercise_index": exercise_index,
                "is_completed": False,
                "is_correct": False,
                "is_unlocked": exercise_index == 0,
                "saved_code": "",
                "current_language": DEFAULT_CHALLENGE_LANGUAGE,
                "title": (exercise.content or {}).get(
                    "title", f"题目 {exercise_index + 1}"
                ),
                "difficulty": exercise.difficulty,
                "exercise": exercise,
            }

        ex_result = await self.db.execute(
            select(Exercise).where(Exercise.id == exercise_id)
        )
        exercise = ex_result.scalar_one_or_none()
        if not exercise:
            return None

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

        return await self.get_exercise_by_id(user_id, progress.exercise_id)

    async def save_code(
        self, user_id: str, exercise_id: int, code: str, language: str
    ) -> bool:
        """Save code for a specific language."""
        result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.exercise_id == exercise_id,
            )
        )
        progress = result.scalar_one_or_none()
        if not progress:
            return False

        saved_codes = progress.saved_codes or {}
        saved_codes[language] = code
        progress.saved_codes = saved_codes
        progress.current_language = language

        await self.db.commit()
        return True

    async def switch_exercise(self, user_id: str, target_index: int) -> dict:
        """Switch to a different exercise by index."""
        count_result = await self.db.execute(
            select(func.count())
            .select_from(ArenaExerciseProgress)
            .where(ArenaExerciseProgress.user_id == user_id)
        )
        total = count_result.scalar() or 0

        if target_index < 0 or target_index >= total:
            raise ValueError("Invalid exercise index")

        result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.exercise_index == target_index,
            )
        )
        progress = result.scalar_one_or_none()
        if not progress:
            raise ValueError("Progress not found")

        if not progress.is_unlocked:
            raise ValueError("Exercise is locked")

        ex_result = await self.db.execute(
            select(Exercise).where(Exercise.id == progress.exercise_id)
        )
        exercise = ex_result.scalar_one_or_none()

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

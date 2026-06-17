"""Challenge Path Service (挑战之路服务)

Service for managing Challenge Path:
- No session concept - direct course-based management
- Persistent exercise records per user per course
- New exercises are appended to existing list
- exercise_id is stable for wrong question book / favorites integration

Design:
- Each course has ONE challenge path per user
- Old exercises have fixed index, new exercises are appended
- exercise_id is used for cross-references (wrong book, favorites, notes)
- Uses AdaptiveRecommendationService for intelligent exercise matching based on user profile
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.exercise import Exercise
from app.models.stats import ActivityLog

# Import focused services
from app.services.challenge_path.selection import ChallengeSelectionService
from app.services.challenge_path.progress import ChallengeProgressService
from app.services.challenge_path.rewards import ChallengeRewardService

logger = logging.getLogger(__name__)

DEFAULT_CHALLENGE_LANGUAGE = "python"


class ChallengePathService:
    """Service for Challenge Path operations - delegates to focused services."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.selection = ChallengeSelectionService(db)
        self.progress = ChallengeProgressService(db)
        self.rewards = ChallengeRewardService(db)

    @staticmethod
    def _is_strict_passed(value: object) -> bool:
        """Accept only explicit pass-like values.

        This avoids Python truthiness pitfalls like bool("false") == True.
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value == 1
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "pass", "passed", "ok"}
        return False

    @classmethod
    def _all_test_cases_passed(cls, test_results: list[dict]) -> bool:
        """Return True only when every test case is explicitly passed."""
        if not test_results:
            return False

        return all(cls._is_strict_passed(result.get("passed")) for result in test_results)

    # ========================================
    # Compatibility delegates - Selection
    # ========================================

    async def get_or_create_challenge_path(
        self,
        user_id: str,
        difficulty_level: int = 3,
        initial_count: int = 3,
    ) -> tuple[list[Exercise], bool]:
        """Get existing exercises or create initial set."""
        return await self.selection.get_or_create_challenge_path(
            user_id=user_id,
            difficulty_level=difficulty_level,
            initial_count=initial_count,
        )

    async def append_exercises(
        self,
        user_id: str,
        difficulty_level: Optional[int] = None,
        count: int = 5,
    ) -> list[int]:
        """Append more exercises to the challenge path."""
        return await self.selection.append_exercises(
            user_id=user_id,
            difficulty_level=difficulty_level,
            count=count,
        )

    # ========================================
    # Compatibility delegates - Progress
    # ========================================

    async def get_progress(self, user_id: str, lite: bool = True) -> dict:
        """Get current progress for challenge path."""
        return await self.progress.get_progress(user_id=user_id, lite=lite)

    async def get_exercise_by_id(
        self, user_id: str, exercise_id: int
    ) -> Optional[dict]:
        """Get specific exercise progress by exercise_id."""
        return await self.progress.get_exercise_by_id(
            user_id=user_id, exercise_id=exercise_id
        )

    async def get_exercise_by_index(
        self, user_id: str, exercise_index: int
    ) -> Optional[dict]:
        """Get exercise by its index in the challenge path."""
        return await self.progress.get_exercise_by_index(
            user_id=user_id, exercise_index=exercise_index
        )

    async def save_code(
        self, user_id: str, exercise_id: int, code: str, language: str
    ) -> bool:
        """Save code for a specific language."""
        return await self.progress.save_code(
            user_id=user_id,
            exercise_id=exercise_id,
            code=code,
            language=language,
        )

    async def switch_exercise(
        self, user_id: str, target_index: int
    ) -> dict:
        """Switch to a different exercise by index."""
        return await self.progress.switch_exercise(
            user_id=user_id, target_index=target_index
        )

    # ========================================
    # Compatibility delegates - Submission
    # ========================================

    async def submit_exercise(
        self,
        user_id: str,
        exercise_id: int,
        code: str,
        language: str,
        test_results: list[dict],
        time_spent: Optional[int] = None,
        hint_used: bool = False,
    ) -> dict:
        """Submit exercise answer and update progress.

        NOTE: This is the original implementation kept for backward compatibility.
        For authoritative judging, use ChallengeSubmissionService directly.
        """
        return await self._submit_exercise_impl(
            user_id=user_id,
            exercise_id=exercise_id,
            code=code,
            language=language,
            test_results=test_results,
            time_spent=time_spent,
            hint_used=hint_used,
        )

    # ========================================
    # Internal implementation (used by submission service)
    # ========================================

    async def _submit_exercise_impl(
        self,
        user_id: str,
        exercise_id: int,
        code: str,
        language: str,
        test_results: list[dict],
        time_spent: Optional[int] = None,
        hint_used: bool = False,
    ) -> dict:
        """Core submission logic - mutates progress, delegates rewards."""
        result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.exercise_id == exercise_id,
            )
        )
        progress = result.scalar_one_or_none()
        if not progress:
            raise ValueError("Progress record not found")

        all_passed = self._all_test_cases_passed(test_results)
        now = datetime.utcnow()

        progress.is_completed = all_passed
        progress.is_correct = all_passed
        progress.last_attempt_at = now
        progress.attempt_count += 1
        progress.current_language = language

        saved_codes = progress.saved_codes or {}
        saved_codes[language] = code
        progress.saved_codes = saved_codes

        if not progress.first_attempt_at:
            progress.first_attempt_at = now

        if all_passed and not progress.correct_at:
            progress.correct_at = now

        if time_spent is not None:
            progress.time_spent = time_spent
        if hint_used:
            progress.hint_used = True
        if progress.attempt_count == 1:
            progress.first_attempt_correct = all_passed

        exercise_result = await self.db.execute(
            select(Exercise).where(Exercise.id == exercise_id)
        )
        exercise = exercise_result.scalar_one_or_none()

        if exercise:
            exercise_title = (
                (exercise.content or {}).get("title")
                or (exercise.content or {}).get("text")
                or f"挑战题目 {progress.exercise_index + 1}"
            )
            activity = ActivityLog(
                user_id=user_id,
                activity_type="exercise_complete",
                chapter_id=exercise.chapter_id,
                description=f"挑战之路完成练习：{exercise_title}",
                extra_data={
                    "learning_path": "challenge",
                    "learning_path_label": "挑战之路",
                    "exercise_id": exercise_id,
                    "exercise_index": progress.exercise_index,
                    "exercise_title": exercise_title,
                    "is_correct": all_passed,
                    "difficulty": exercise.difficulty,
                },
            )
            self.db.add(activity)

        next_unlocked = False
        next_result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.exercise_index > progress.exercise_index,
            ).order_by(ArenaExerciseProgress.exercise_index).limit(1)
        )
        next_progress = next_result.scalar_one_or_none()
        if all_passed and next_progress and not next_progress.is_unlocked:
            next_progress.is_unlocked = True
            next_unlocked = True

        # Delegate all reward logic to ChallengeRewardService
        reward_service = ChallengeRewardService(self.db)
        reward_fields = await reward_service.apply_submission_rewards(
            user_id=user_id,
            exercise=exercise,
            progress=progress,
            is_correct=all_passed,
            code=code,
        )

        await self.db.commit()
        logger.info("[STARS] After commit - submission committed")

        try:
            from app.services.user_profile import UserProfileService
            profile_service = UserProfileService(self.db)
            await profile_service.update_after_exercise(
                user_id=user_id,
                exercise_id=exercise_id,
                is_correct=all_passed,
                course_id=None,
                time_spent=time_spent,
                hint_used=hint_used,
                first_attempt_correct=(progress.attempt_count == 1 and all_passed),
            )
        except Exception as e:
            logger.warning("Failed to update user profile: %s", e)

        logger.info("[STARS] === Returning result ===")
        logger.info("[STARS] stars_earned: %s, tier_changed: %s", reward_fields["stars_earned"], reward_fields["tier_changed"])
        logger.info(
            "[STARS] new_tier: %s, new_sub_tier: %s, new_stars: %s",
            reward_fields["new_tier"], reward_fields["new_sub_tier"], reward_fields["new_stars"]
        )

        return {
            "is_correct": all_passed,
            "test_results": test_results,
            "next_unlocked": next_unlocked,
            **reward_fields,
        }

    async def get_stats(self, user_id: str) -> dict:
        """Get challenge path statistics."""
        return await self.rewards.get_stats(user_id=user_id)


def get_challenge_path_service(db: AsyncSession) -> ChallengePathService:
    """Get ChallengePathService instance."""
    return ChallengePathService(db)


# Backward compatibility alias
ArenaInfiniteService = ChallengePathService
get_arena_infinite_service = get_challenge_path_service

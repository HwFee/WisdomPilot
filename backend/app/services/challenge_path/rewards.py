"""Challenge reward service - handles stars, tiers, and cores."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.exercise import Exercise
from app.services.challenge_path.tier_rewards import ChallengeTierRewardCalculator
from app.services.core_service import CoreService
from app.services.tier_transaction_service import TierTransactionService
from app.services.wrong_question import wrong_question_service
from app.core.tier_config import TierRank

CORE_REWARD_CHALLENGE_CORRECT = 3
CORE_REWARD_CATEGORY = "arena"
CORE_REWARD_REFERENCE_TYPE = "exercise"
TIER_TRANSACTION_SOURCE = "arena_challenge"


class ChallengeRewardService:
    """Service for challenge path rewards."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats(self, user_id: str) -> dict:
        """Get challenge path statistics."""
        from app.services.challenge_path.progress import ChallengeProgressService

        progress_service = ChallengeProgressService(self.db)
        progress_records = await progress_service._get_user_progress(user_id)

        if not progress_records:
            return {
                "total_exercises": 0,
                "completed_count": 0,
                "correct_count": 0,
                "total_xp": 0,
            }

        completed = sum(1 for p in progress_records if p.is_completed)
        correct = sum(1 for p in progress_records if p.is_correct)

        return {
            "total_exercises": len(progress_records),
            "completed_count": completed,
            "correct_count": correct,
            "total_xp": correct * 10,
        }

    async def apply_submission_rewards(
        self,
        *,
        user_id: str,
        exercise: Exercise,
        progress: ArenaExerciseProgress,
        is_correct: bool,
        code: str,
    ) -> dict:
        """Apply all reward-related side effects for a challenge submission.

        Handles: wrong-book collection, star/tier updates, core rewards,
        and tier transaction recording.

        Returns a dict with all reward fields used by the API response.
        """
        added_to_wrong_book = await self._collect_wrong_question(
            user_id=user_id,
            exercise=exercise,
            progress=progress,
            is_correct=is_correct,
            code=code,
        )

        reward_result = await self._apply_stars_and_tier(
            user_id=user_id,
            exercise=exercise,
            progress=progress,
            is_correct=is_correct,
        )

        cores_earned = await self._award_cores(
            user_id=user_id,
            exercise=exercise,
            is_correct=is_correct,
            stars_earned=reward_result["stars_earned"],
        )

        await self._record_tier_transaction(
            user_id=user_id,
            exercise=exercise,
            progress=progress,
            is_correct=is_correct,
            reward_result=reward_result,
        )

        first_time_correct = is_correct and progress.attempt_count == 1
        first_time_wrong = not is_correct and progress.attempt_count == 1

        return {
            "stars_earned": reward_result["stars_earned"],
            "cores_earned": cores_earned,
            "added_to_wrong_book": added_to_wrong_book,
            "tier_changed": reward_result["tier_changed"],
            "new_tier": reward_result["new_tier"],
            "new_sub_tier": reward_result["new_sub_tier"],
            "new_stars": reward_result["new_stars"],
            "promoted": reward_result["promoted"],
            "demoted": reward_result["demoted"],
            "first_time_correct": first_time_correct,
            "first_time_wrong": first_time_wrong,
        }

    async def _collect_wrong_question(
        self,
        *,
        user_id: str,
        exercise: Optional[Exercise],
        progress: ArenaExerciseProgress,
        is_correct: bool,
        code: str,
    ) -> bool:
        """Add exercise to wrong question book if answer was incorrect."""
        if is_correct or not exercise:
            return False

        exercise_key = f"arena-global-{progress.exercise_id}"
        await wrong_question_service.collect_wrong_question_by_key(
            db=self.db,
            user_id=user_id,
            exercise_key=exercise_key,
            user_answer=code,
            exercise_id=progress.exercise_id,
            exercise_content=exercise.content,
            exercise_type=exercise.type,
            knowledge_points=exercise.knowledge_points,
        )
        return True

    async def _apply_stars_and_tier(
        self,
        *,
        user_id: str,
        exercise: Optional[Exercise],
        progress: ArenaExerciseProgress,
        is_correct: bool,
    ) -> dict:
        """Calculate and apply star/tier changes."""
        return await ChallengeTierRewardCalculator(self.db).apply(
            user_id=user_id,
            exercise=exercise,
            progress=progress,
            is_correct=is_correct,
        )

    async def _award_cores(
        self,
        *,
        user_id: str,
        exercise: Exercise,
        is_correct: bool,
        stars_earned: int,
    ) -> int:
        if not is_correct or stars_earned <= 0:
            return 0
        await CoreService(self.db).earn_cores(
            user_id=user_id,
            amount=CORE_REWARD_CHALLENGE_CORRECT,
            category=CORE_REWARD_CATEGORY,
            reference_type=CORE_REWARD_REFERENCE_TYPE,
            reference_id=str(exercise.id),
            description="挑战之路答对题目",
        )
        return CORE_REWARD_CHALLENGE_CORRECT

    async def _record_tier_transaction(
        self,
        *,
        user_id: str,
        exercise: Exercise,
        progress: ArenaExerciseProgress,
        is_correct: bool,
        reward_result: dict,
    ) -> None:
        stars_earned = reward_result["stars_earned"]
        promoted = reward_result["promoted"]
        demoted = reward_result["demoted"]
        if stars_earned == 0 and not promoted and not demoted:
            return

        tier_result = reward_result.get("tier_result")
        current_tier = reward_result.get("current_tier")
        profile = reward_result.get("profile")
        used_protection = bool(
            tier_result
            and stars_earned < 0
            and getattr(tier_result, "used_protection", False)
        )
        await TierTransactionService(self.db).record_transaction(
            user_id=user_id,
            course_id=None,
            tier_before=(
                current_tier.value if current_tier else TierRank.BRONZE.value
            ),
            sub_tier_before=int(reward_result.get("current_sub_tier") or 0),
            stars_before=int(reward_result.get("current_stars") or 0),
            tier_after=(reward_result.get("new_tier") or TierRank.BRONZE.value),
            sub_tier_after=int(reward_result.get("new_sub_tier") or 0),
            stars_after=int(reward_result.get("new_stars") or 0),
            stars_change=stars_earned,
            promoted=promoted,
            demoted=demoted,
            used_protection=used_protection,
            protection_remaining=(
                int(profile.protection_remaining or 0) if profile else 0
            ),
            source=TIER_TRANSACTION_SOURCE,
            reference_id=str(exercise.id),
            description=f"挑战之路答题 - {'答对' if is_correct else '答错'}",
        )

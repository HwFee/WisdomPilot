"""Challenge reward service - handles stars, tiers, cores, and profile stats."""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.exercise import Exercise
from app.models.user_arena import UserArenaProfile
from app.services.core_service import CoreService
from app.services.tier_service import tier_service
from app.services.wrong_question import wrong_question_service
from app.core.tier_config import TierRank, tier_from_string

logger = logging.getLogger(__name__)

CORE_REWARD_CHALLENGE_CORRECT = 3


class ChallengeRewardService:
    """Service for challenge path rewards and statistics."""

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
        exercise: Optional[Exercise],
        progress: ArenaExerciseProgress,
        is_correct: bool,
        code: str,
    ) -> dict:
        """Apply all reward-related side effects for a challenge submission.

        Handles: wrong-book collection, star/tier updates, core rewards,
        tier transaction recording, and arena profile stats updates.

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

        await self._update_profile_stats(user_id=user_id)

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
        profile_result = await self.db.execute(
            select(UserArenaProfile).where(UserArenaProfile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()

        if not profile:
            profile = UserArenaProfile(user_id=user_id)
            self.db.add(profile)
            await self.db.flush()
            logger.info("[STARS] Created new profile for user %s... ", user_id[:8])

        current_tier = tier_from_string(profile.tier) if profile.tier else TierRank.BRONZE
        current_sub_tier = profile.sub_tier if profile.sub_tier else 4
        current_stars = profile.stars if profile.stars else 0

        stars_earned = 0
        tier_changed = False
        new_tier = None
        new_sub_tier = None
        new_stars = 0
        promoted = False
        demoted = False
        tier_result = None

        stars_deducted = getattr(progress, "stars_deducted", None)
        if stars_deducted is None:
            stars_deducted = abs(min(0, progress.stars_awarded)) if progress.stars_awarded < 0 else 0

        logger.info("[STARS] === Reward Application ===")
        logger.info("[STARS] User: %s...,  Exercise: %s", user_id[:8], progress.exercise_id)
        logger.info(
            "[STARS] is_correct: %s, attempt_count: %s, difficulty: %s",
            is_correct, progress.attempt_count, exercise.difficulty if exercise else "?"
        )
        logger.info("[STARS] stars_awarded: %s, stars_deducted: %s", progress.stars_awarded, stars_deducted)
        logger.info(
            "[STARS] Current profile - tier: %s, sub_tier: %s, stars: %s",
            current_tier.value, current_sub_tier, current_stars
        )

        already_correct = progress.stars_awarded > 0

        if already_correct:
            new_tier = current_tier
            new_sub_tier = current_sub_tier
            new_stars = current_stars
            logger.info(
                "[STARS] Already correct before (stars_awarded=%s), no change",
                progress.stars_awarded
            )
        else:
            if is_correct:
                base_reward = tier_service.get_base_reward(exercise.difficulty) if exercise else 1
                stars_earned = base_reward
                logger.info("[STARS] CORRECT! base_reward=%s, total=+%s", base_reward, stars_earned)
            else:
                stars_earned = tier_service.calculate_stars_earned(
                    accuracy=0.0,
                    difficulty=exercise.difficulty if exercise else 1,
                    attempt_count=progress.attempt_count,
                    total_deducted=stars_deducted,
                )
                logger.info(
                    "[STARS] WRONG. attempt_count=%s, stars_deducted=%s, result=%s",
                    progress.attempt_count, stars_deducted, stars_earned
                )

            progress.stars_awarded = stars_earned

            if stars_earned < 0 and hasattr(progress, "stars_deducted"):
                progress.stars_deducted = stars_deducted + abs(stars_earned)
                logger.info("[STARS] Updated stars_deducted to %s", progress.stars_deducted)

            if stars_earned > 0:
                tier_result = tier_service.add_stars(
                    tier=current_tier,
                    sub_tier=current_sub_tier,
                    current_stars=current_stars,
                    stars_earned=stars_earned,
                )
                new_tier = tier_result.tier
                new_sub_tier = tier_result.sub_tier
                new_stars = tier_result.stars
                promoted = tier_result.promoted
                logger.info(
                    "[STARS] Add stars result - new_tier: %s, new_sub_tier: %s, new_stars: %s, promoted: %s",
                    new_tier.value, new_sub_tier, new_stars, promoted
                )
            elif stars_earned < 0:
                tier_result = tier_service.remove_stars(
                    tier=current_tier,
                    sub_tier=current_sub_tier,
                    current_stars=current_stars,
                    stars_lost=abs(stars_earned),
                    protection_remaining=profile.protection_remaining or 0,
                )
                new_tier = tier_result.tier
                new_sub_tier = tier_result.sub_tier
                new_stars = tier_result.stars
                demoted = tier_result.demoted
                logger.info(
                    "[STARS] Remove stars result - new_tier: %s, new_sub_tier: %s, new_stars: %s, demoted: %s",
                    new_tier.value, new_sub_tier, new_stars, demoted
                )
                profile.protection_remaining = tier_result.protection_remaining
            else:
                new_tier = current_tier
                new_sub_tier = current_sub_tier
                new_stars = current_stars
                logger.info("[STARS] No stars change (stars_earned == 0)")

            profile.tier = new_tier.value
            profile.sub_tier = new_sub_tier
            profile.stars = new_stars
            logger.info(
                "[STARS] Updated profile - tier: %s, sub_tier: %s, stars: %s",
                profile.tier, profile.sub_tier, profile.stars
            )

            if promoted:
                highest_tier, highest_sub = tier_service.update_highest_tier(
                    profile.highest_tier,
                    profile.highest_sub_tier,
                    new_tier,
                    new_sub_tier,
                )
                profile.highest_tier = highest_tier.value if isinstance(highest_tier, TierRank) else highest_tier
                profile.highest_sub_tier = highest_sub

            tier_changed = (new_tier != current_tier or new_sub_tier != current_sub_tier)
            new_tier = tier_from_string(profile.tier) if profile.tier else TierRank.BRONZE
            new_sub_tier = profile.sub_tier if profile.sub_tier else 4
            new_stars = profile.stars if profile.stars else 0

        return {
            "stars_earned": stars_earned,
            "tier_changed": tier_changed,
            "new_tier": new_tier.value if new_tier else None,
            "new_sub_tier": new_sub_tier,
            "new_stars": new_stars,
            "promoted": promoted,
            "demoted": demoted,
            "tier_result": tier_result,
            "current_tier": current_tier,
            "current_sub_tier": current_sub_tier,
            "current_stars": current_stars,
            "profile": profile,
        }

    async def _award_cores(
        self,
        *,
        user_id: str,
        exercise: Optional[Exercise],
        is_correct: bool,
        stars_earned: int,
    ) -> int:
        """Award cores for correct answers."""
        if not is_correct or stars_earned <= 0:
            return 0

        try:
            core_service = CoreService(self.db)
            cores_earned = CORE_REWARD_CHALLENGE_CORRECT
            await core_service.earn_cores(
                user_id=user_id,
                amount=cores_earned,
                category="arena",
                reference_type="exercise",
                reference_id=str(exercise.id) if exercise else "0",
                description="挑战之路答对题目",
            )
            logger.info(
                "[CORE] Awarded %s cores to user %s... for correct challenge exercise",
                cores_earned, user_id[:8]
            )
            return cores_earned
        except Exception as e:
            logger.warning("Failed to award cores: %s", e)
            return 0

    async def _record_tier_transaction(
        self,
        *,
        user_id: str,
        exercise: Optional[Exercise],
        progress: ArenaExerciseProgress,
        is_correct: bool,
        reward_result: dict,
    ) -> None:
        """Record tier transaction if stars changed or tier promoted/demoted."""
        stars_earned = reward_result["stars_earned"]
        promoted = reward_result["promoted"]
        demoted = reward_result["demoted"]
        tier_result = reward_result.get("tier_result")
        current_tier = reward_result.get("current_tier")
        current_sub_tier = reward_result.get("current_sub_tier")
        current_stars = reward_result.get("current_stars")
        profile = reward_result.get("profile")
        new_tier_value = reward_result.get("new_tier")
        new_sub_tier = reward_result.get("new_sub_tier")
        new_stars = reward_result.get("new_stars")

        if stars_earned == 0 and not promoted and not demoted:
            return

        try:
            from app.services.tier_transaction_service import TierTransactionService
            tier_tx_service = TierTransactionService(self.db)
            used_protection = (
                getattr(tier_result, "used_protection", False)
                if tier_result and stars_earned < 0 else False
            )
            await tier_tx_service.record_transaction(
                user_id=user_id,
                course_id=None,
                tier_before=current_tier.value if current_tier else TierRank.BRONZE.value,
                sub_tier_before=current_sub_tier,
                stars_before=current_stars,
                tier_after=new_tier_value if new_tier_value else TierRank.BRONZE.value,
                sub_tier_after=new_sub_tier,
                stars_after=new_stars,
                stars_change=stars_earned,
                promoted=promoted,
                demoted=demoted,
                used_protection=used_protection,
                protection_remaining=profile.protection_remaining or 0 if profile else 0,
                source="arena_challenge",
                reference_id=str(exercise.id) if exercise else "0",
                description=f"挑战之路答题 - {'答对' if is_correct else '答错'}",
            )
            logger.info(
                "[TierTx] Recorded tier transaction for user %s... stars_change=%s",
                user_id[:8], stars_earned
            )
        except Exception as e:
            logger.warning("Failed to record tier transaction: %s", e)

    async def _update_profile_stats(self, user_id: str) -> None:
        """Update arena profile statistics from progress records."""
        result = await self.db.execute(
            select(ArenaExerciseProgress, Exercise)
            .join(Exercise, ArenaExerciseProgress.exercise_id == Exercise.id)
            .where(ArenaExerciseProgress.user_id == user_id)
            .order_by(ArenaExerciseProgress.exercise_index)
        )
        rows = list(result.all())
        if not rows:
            return

        progresses = [p for p, _ in rows]
        exercises_map = {p.exercise_id: ex for p, ex in rows}

        total = len(progresses)
        completed = [p for p in progresses if p.is_completed]
        correct = [p for p in progresses if p.is_correct]
        total_attempts = sum(p.attempt_count for p in progresses)
        times_spent = [p.time_spent for p in progresses if p.time_spent]

        best_streak = 0
        current_run = 0
        for p in progresses:
            if p.is_correct:
                current_run += 1
                best_streak = max(best_streak, current_run)
            else:
                current_run = 0

        current_streak = 0
        for p in reversed(progresses):
            if p.is_correct:
                current_streak += 1
            else:
                break

        highest_difficulty = 0
        for p in completed:
            ex = exercises_map.get(p.exercise_id)
            if ex and ex.difficulty > highest_difficulty:
                highest_difficulty = ex.difficulty

        profile_result = await self.db.execute(
            select(UserArenaProfile).where(UserArenaProfile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()
        if not profile:
            return

        profile.total_challenges = len(completed)
        profile.wins = len(correct)
        profile.losses = len(completed) - len(correct)
        profile.best_streak = best_streak
        profile.current_streak = current_streak
        profile.highest_difficulty = highest_difficulty
        profile.total_submissions = total_attempts
        profile.avg_accuracy = len(correct) / total if total > 0 else 0.0
        profile.avg_time_spent = sum(times_spent) / len(times_spent) if times_spent else 0.0

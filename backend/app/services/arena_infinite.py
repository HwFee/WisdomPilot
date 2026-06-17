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
from app.models.user import User
from app.models.user_arena import UserArenaProfile
from app.services.wrong_question import wrong_question_service
from app.services.tier_service import tier_service
from app.services.core_service import CoreService
from app.core.tier_config import TierRank, tier_from_string

# Import focused services
from app.services.challenge_path.selection import ChallengeSelectionService
from app.services.challenge_path.progress import ChallengeProgressService
from app.services.challenge_path.rewards import ChallengeRewardService

logger = logging.getLogger(__name__)

# Core rewards for challenge path
CORE_REWARD_CHALLENGE_CORRECT = 3
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
        """Core submission logic - mutates progress, awards stars, tiers, cores."""
        result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,
                ArenaExerciseProgress.exercise_id == exercise_id,
            )
        )
        progress = result.scalar_one_or_none()
        if not progress:
            raise ValueError("Progress record not found")

        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        is_test_account = user.is_test_account if user else False
        is_first_three = progress.exercise_index < 3

        if is_test_account and is_first_three:
            all_passed = True
            logger.info(
                f"[TEST_ACCOUNT] User {user_id[:8]}... is test account, "
                f"exercise_index={progress.exercise_index}, auto-passing"
            )
        else:
            all_passed = self._all_test_cases_passed(test_results)
        now = datetime.utcnow()

        progress.is_completed = True
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

        added_to_wrong_book = False
        if not all_passed and exercise:
            exercise_key = f"arena-global-{exercise_id}"
            await wrong_question_service.collect_wrong_question_by_key(
                db=self.db,
                user_id=user_id,
                exercise_key=exercise_key,
                user_answer=code,
                exercise_id=exercise_id,
                exercise_content=exercise.content,
                exercise_type=exercise.type,
                knowledge_points=exercise.knowledge_points,
            )
            added_to_wrong_book = True

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
        if next_progress and not next_progress.is_unlocked:
            next_progress.is_unlocked = True
            next_unlocked = True

        stars_earned = 0
        tier_changed = False
        new_tier = None
        new_sub_tier = None
        new_stars = 0
        promoted = False
        demoted = False

        profile_result = await self.db.execute(
            select(UserArenaProfile).where(
                UserArenaProfile.user_id == user_id,
            )
        )
        profile = profile_result.scalar_one_or_none()

        if not profile:
            profile = UserArenaProfile(user_id=user_id)
            self.db.add(profile)
            await self.db.flush()
            logger.info(f"[STARS] Created new profile for user {user_id[:8]}... ")

        current_tier = tier_from_string(profile.tier) if profile.tier else TierRank.BRONZE
        current_sub_tier = profile.sub_tier if profile.sub_tier else 4
        current_stars = profile.stars if profile.stars else 0

        tier_result = None

        stars_deducted = getattr(progress, "stars_deducted", None)
        if stars_deducted is None:
            stars_deducted = abs(min(0, progress.stars_awarded)) if progress.stars_awarded < 0 else 0

        logger.info("[STARS] === Submit Exercise ===")
        logger.info(f"[STARS] User: {user_id[:8]}...,  Exercise: {exercise_id}")
        logger.info(
            f"[STARS] is_correct: {all_passed}, attempt_count: {progress.attempt_count}, "
            f"difficulty: {exercise.difficulty if exercise else '?'}")
        logger.info(f"[STARS] stars_awarded: {progress.stars_awarded}, stars_deducted: {stars_deducted}")
        logger.info(
            f"[STARS] Current profile - tier: {current_tier.value}, "
            f"sub_tier: {current_sub_tier}, stars: {current_stars}")

        already_correct = progress.stars_awarded > 0

        if already_correct:
            new_tier = current_tier
            new_sub_tier = current_sub_tier
            new_stars = current_stars
            logger.info(
                f"[STARS] Already correct before (stars_awarded={progress.stars_awarded}), no change"
            )
        else:
            if all_passed:
                base_reward = tier_service.get_base_reward(exercise.difficulty) if exercise else 1
                stars_earned = base_reward
                logger.info(f"[STARS] CORRECT! base_reward={base_reward}, total=+{stars_earned}")
            else:
                stars_earned = tier_service.calculate_stars_earned(
                    accuracy=0.0,
                    difficulty=exercise.difficulty if exercise else 1,
                    attempt_count=progress.attempt_count,
                    total_deducted=stars_deducted,
                )
                logger.info(
                    f"[STARS] WRONG. attempt_count={progress.attempt_count}, "
                    f"stars_deducted={stars_deducted}, result={stars_earned}"
                )

            progress.stars_awarded = stars_earned

            if stars_earned < 0 and hasattr(progress, "stars_deducted"):
                progress.stars_deducted = stars_deducted + abs(stars_earned)
                logger.info(f"[STARS] Updated stars_deducted to {progress.stars_deducted}")

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
                    f"[STARS] Add stars result - new_tier: {new_tier.value}, "
                    f"new_sub_tier: {new_sub_tier}, new_stars: {new_stars}, promoted: {promoted}"
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
                    f"[STARS] Remove stars result - new_tier: {new_tier.value}, "
                    f"new_sub_tier: {new_sub_tier}, new_stars: {new_stars}, demoted: {demoted}"
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
                f"[STARS] Updated profile - tier: {profile.tier}, "
                f"sub_tier: {profile.sub_tier}, stars: {profile.stars}"
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

        try:
            await self._update_arena_profile_stats(profile, user_id)
        except Exception as e:
            logger.warning(f"Failed to update arena profile stats: {e}")

        cores_earned = 0
        if all_passed and stars_earned > 0:
            try:
                core_service = CoreService(self.db)
                cores_earned = CORE_REWARD_CHALLENGE_CORRECT
                await core_service.earn_cores(
                    user_id=user_id,
                    amount=cores_earned,
                    category="arena",
                    reference_type="exercise",
                    reference_id=str(exercise_id),
                    description="挑战之路答对题目",
                )
                logger.info(
                    f"[CORE] Awarded {cores_earned} cores to user {user_id[:8]}... "
                    f"for correct challenge exercise"
                )
            except Exception as e:
                logger.warning(f"Failed to award cores: {e}")
                cores_earned = 0

        if stars_earned != 0 or promoted or demoted:
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
                    tier_after=new_tier.value if new_tier else TierRank.BRONZE.value,
                    sub_tier_after=new_sub_tier,
                    stars_after=new_stars,
                    stars_change=stars_earned,
                    promoted=promoted,
                    demoted=demoted,
                    used_protection=used_protection,
                    protection_remaining=profile.protection_remaining or 0,
                    source="arena_challenge",
                    reference_id=str(exercise_id),
                    description=f"挑战之路答题 - {'答对' if all_passed else '答错'}",
                )
                logger.info(
                    f"[TierTx] Recorded tier transaction for user {user_id[:8]}... "
                    f"stars_change={stars_earned}"
                )
            except Exception as e:
                logger.warning(f"Failed to record tier transaction: {e}")

        await self.db.commit()
        logger.info(f"[STARS] After commit - profile.stars: {profile.stars}")

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
            logger.warning(f"Failed to update user profile: {e}")

        logger.info("[STARS] === Returning result ===")
        logger.info(f"[STARS] stars_earned: {stars_earned}, tier_changed: {tier_changed}")
        logger.info(
            f"[STARS] new_tier: {new_tier.value if new_tier else None}, "
            f"new_sub_tier: {new_sub_tier}, new_stars: {new_stars}"
        )

        first_time_correct = all_passed and progress.attempt_count == 1
        first_time_wrong = not all_passed and progress.attempt_count == 1

        return {
            "is_correct": all_passed,
            "test_results": test_results,
            "stars_earned": stars_earned,
            "cores_earned": cores_earned,
            "next_unlocked": next_unlocked,
            "added_to_wrong_book": added_to_wrong_book,
            "tier_changed": tier_changed,
            "new_tier": new_tier.value if new_tier else None,
            "new_sub_tier": new_sub_tier,
            "new_stars": new_stars,
            "promoted": promoted,
            "demoted": demoted,
            "first_time_correct": first_time_correct,
            "first_time_wrong": first_time_wrong,
        }

    async def _update_arena_profile_stats(
        self, profile: UserArenaProfile, user_id: str
    ) -> None:
        """Update UserArenaProfile statistics from ArenaExerciseProgress records."""
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

        profile.total_challenges = len(completed)
        profile.wins = len(correct)
        profile.losses = len(completed) - len(correct)
        profile.best_streak = best_streak
        profile.current_streak = current_streak
        profile.highest_difficulty = highest_difficulty
        profile.total_submissions = total_attempts
        profile.avg_accuracy = len(correct) / total if total > 0 else 0.0
        profile.avg_time_spent = sum(times_spent) / len(times_spent) if times_spent else 0.0

    async def get_stats(self, user_id: str) -> dict:
        """Get challenge path statistics."""
        return await self.rewards.get_stats(user_id=user_id)


def get_challenge_path_service(db: AsyncSession) -> ChallengePathService:
    """Get ChallengePathService instance."""
    return ChallengePathService(db)


# Backward compatibility alias
ArenaInfiniteService = ChallengePathService
get_arena_infinite_service = get_challenge_path_service

"""Tier and star reward helpers for challenge submissions."""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tier_config import TierRank, tier_from_string
from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.exercise import Exercise
from app.models.user_arena import UserArenaProfile
from app.services.tier_service import tier_service

logger = logging.getLogger(__name__)


class ChallengeTierRewardCalculator:
    """Applies star and tier state transitions for challenge rewards."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def apply(
        self,
        *,
        user_id: str,
        exercise: Optional[Exercise],
        progress: ArenaExerciseProgress,
        is_correct: bool,
    ) -> dict:
        profile = await self._get_or_create_profile(user_id)
        current_tier, current_sub_tier, current_stars = self._get_profile_tier_state(profile)
        stars_deducted = self._get_stars_deducted(progress)

        self._log_reward_start(
            user_id=user_id,
            exercise=exercise,
            progress=progress,
            is_correct=is_correct,
            stars_deducted=stars_deducted,
            current_tier=current_tier,
            current_sub_tier=current_sub_tier,
            current_stars=current_stars,
        )

        if progress.stars_awarded > 0:
            logger.info(
                "[STARS] Already correct before (stars_awarded=%s), no change",
                progress.stars_awarded,
            )
            return self._build_reward_result(
                stars_earned=0,
                tier_changed=False,
                new_tier=current_tier,
                new_sub_tier=current_sub_tier,
                new_stars=current_stars,
                promoted=False,
                demoted=False,
                tier_result=None,
                current_tier=current_tier,
                current_sub_tier=current_sub_tier,
                current_stars=current_stars,
                profile=profile,
            )

        stars_earned = self._calculate_stars_earned(
            exercise=exercise,
            progress=progress,
            is_correct=is_correct,
            stars_deducted=stars_deducted,
        )
        progress.stars_awarded = stars_earned
        self._record_star_deduction(progress, stars_earned, stars_deducted)

        tier_change = self._apply_profile_tier_change(
            profile=profile,
            current_tier=current_tier,
            current_sub_tier=current_sub_tier,
            current_stars=current_stars,
            stars_earned=stars_earned,
        )

        return self._build_reward_result(
            stars_earned=stars_earned,
            tier_changed=tier_change["tier_changed"],
            new_tier=tier_change["new_tier"],
            new_sub_tier=tier_change["new_sub_tier"],
            new_stars=tier_change["new_stars"],
            promoted=tier_change["promoted"],
            demoted=tier_change["demoted"],
            tier_result=tier_change["tier_result"],
            current_tier=current_tier,
            current_sub_tier=current_sub_tier,
            current_stars=current_stars,
            profile=profile,
        )

    async def _get_or_create_profile(self, user_id: str) -> UserArenaProfile:
        profile_result = await self.db.execute(
            select(UserArenaProfile).where(UserArenaProfile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()

        if not profile:
            profile = UserArenaProfile(user_id=user_id)
            self.db.add(profile)
            await self.db.flush()
            logger.info("[STARS] Created new profile for user %s... ", user_id[:8])

        return profile

    def _get_profile_tier_state(self, profile: UserArenaProfile):
        current_tier = tier_from_string(profile.tier) if profile.tier else TierRank.BRONZE
        current_sub_tier = profile.sub_tier if profile.sub_tier else 4
        current_stars = profile.stars if profile.stars else 0
        return current_tier, current_sub_tier, current_stars

    def _get_stars_deducted(self, progress: ArenaExerciseProgress) -> int:
        stars_deducted = getattr(progress, "stars_deducted", None)
        if stars_deducted is None:
            stars_deducted = abs(min(0, progress.stars_awarded)) if progress.stars_awarded < 0 else 0
        return stars_deducted

    def _log_reward_start(
        self,
        *,
        user_id: str,
        exercise: Optional[Exercise],
        progress: ArenaExerciseProgress,
        is_correct: bool,
        stars_deducted: int,
        current_tier: TierRank,
        current_sub_tier: int,
        current_stars: int,
    ) -> None:
        logger.info("[STARS] === Reward Application ===")
        logger.info("[STARS] User: %s...,  Exercise: %s", user_id[:8], progress.exercise_id)
        logger.info(
            "[STARS] is_correct: %s, attempt_count: %s, difficulty: %s",
            is_correct,
            progress.attempt_count,
            exercise.difficulty if exercise else "?",
        )
        logger.info(
            "[STARS] stars_awarded: %s, stars_deducted: %s",
            progress.stars_awarded,
            stars_deducted,
        )
        logger.info(
            "[STARS] Current profile - tier: %s, sub_tier: %s, stars: %s",
            current_tier.value,
            current_sub_tier,
            current_stars,
        )

    def _calculate_stars_earned(
        self,
        *,
        exercise: Optional[Exercise],
        progress: ArenaExerciseProgress,
        is_correct: bool,
        stars_deducted: int,
    ) -> int:
        if is_correct:
            base_reward = tier_service.get_base_reward(exercise.difficulty) if exercise else 1
            logger.info("[STARS] CORRECT! base_reward=%s, total=+%s", base_reward, base_reward)
            return base_reward

        stars_earned = tier_service.calculate_stars_earned(
            accuracy=0.0,
            difficulty=exercise.difficulty if exercise else 1,
            attempt_count=progress.attempt_count,
            total_deducted=stars_deducted,
        )
        logger.info(
            "[STARS] WRONG. attempt_count=%s, stars_deducted=%s, result=%s",
            progress.attempt_count,
            stars_deducted,
            stars_earned,
        )
        return stars_earned

    def _record_star_deduction(
        self,
        progress: ArenaExerciseProgress,
        stars_earned: int,
        stars_deducted: int,
    ) -> None:
        if stars_earned < 0 and hasattr(progress, "stars_deducted"):
            progress.stars_deducted = stars_deducted + abs(stars_earned)
            logger.info("[STARS] Updated stars_deducted to %s", progress.stars_deducted)

    def _apply_profile_tier_change(
        self,
        *,
        profile: UserArenaProfile,
        current_tier: TierRank,
        current_sub_tier: int,
        current_stars: int,
        stars_earned: int,
    ) -> dict:
        if stars_earned > 0:
            tier_result = self._apply_positive_stars(
                current_tier=current_tier,
                current_sub_tier=current_sub_tier,
                current_stars=current_stars,
                stars_earned=stars_earned,
            )
            new_tier = tier_result.tier
            new_sub_tier = tier_result.sub_tier
            new_stars = tier_result.stars
            promoted = tier_result.promoted
            demoted = False
        elif stars_earned < 0:
            tier_result = self._apply_negative_stars(
                profile=profile,
                current_tier=current_tier,
                current_sub_tier=current_sub_tier,
                current_stars=current_stars,
                stars_earned=stars_earned,
            )
            new_tier = tier_result.tier
            new_sub_tier = tier_result.sub_tier
            new_stars = tier_result.stars
            promoted = False
            demoted = tier_result.demoted
        else:
            tier_result = None
            new_tier = current_tier
            new_sub_tier = current_sub_tier
            new_stars = current_stars
            promoted = False
            demoted = False
            logger.info("[STARS] No stars change (stars_earned == 0)")

        self._persist_profile_tier(
            profile=profile,
            new_tier=new_tier,
            new_sub_tier=new_sub_tier,
            new_stars=new_stars,
            promoted=promoted,
        )
        persisted_tier, persisted_sub_tier, persisted_stars = self._get_profile_tier_state(profile)

        return {
            "tier_changed": new_tier != current_tier or new_sub_tier != current_sub_tier,
            "new_tier": persisted_tier,
            "new_sub_tier": persisted_sub_tier,
            "new_stars": persisted_stars,
            "promoted": promoted,
            "demoted": demoted,
            "tier_result": tier_result,
        }

    def _apply_positive_stars(
        self,
        *,
        current_tier: TierRank,
        current_sub_tier: int,
        current_stars: int,
        stars_earned: int,
    ):
        tier_result = tier_service.add_stars(
            tier=current_tier,
            sub_tier=current_sub_tier,
            current_stars=current_stars,
            stars_earned=stars_earned,
        )
        logger.info(
            "[STARS] Add stars result - new_tier: %s, new_sub_tier: %s, new_stars: %s, promoted: %s",
            tier_result.tier.value,
            tier_result.sub_tier,
            tier_result.stars,
            tier_result.promoted,
        )
        return tier_result

    def _apply_negative_stars(
        self,
        *,
        profile: UserArenaProfile,
        current_tier: TierRank,
        current_sub_tier: int,
        current_stars: int,
        stars_earned: int,
    ):
        tier_result = tier_service.remove_stars(
            tier=current_tier,
            sub_tier=current_sub_tier,
            current_stars=current_stars,
            stars_lost=abs(stars_earned),
            protection_remaining=profile.protection_remaining or 0,
        )
        profile.protection_remaining = tier_result.protection_remaining
        logger.info(
            "[STARS] Remove stars result - new_tier: %s, new_sub_tier: %s, new_stars: %s, demoted: %s",
            tier_result.tier.value,
            tier_result.sub_tier,
            tier_result.stars,
            tier_result.demoted,
        )
        return tier_result

    def _persist_profile_tier(
        self,
        *,
        profile: UserArenaProfile,
        new_tier: TierRank,
        new_sub_tier: int,
        new_stars: int,
        promoted: bool,
    ) -> None:
        profile.tier = new_tier.value
        profile.sub_tier = new_sub_tier
        profile.stars = new_stars
        logger.info(
            "[STARS] Updated profile - tier: %s, sub_tier: %s, stars: %s",
            profile.tier,
            profile.sub_tier,
            profile.stars,
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

    def _build_reward_result(
        self,
        *,
        stars_earned: int,
        tier_changed: bool,
        new_tier: TierRank,
        new_sub_tier: int,
        new_stars: int,
        promoted: bool,
        demoted: bool,
        tier_result,
        current_tier: TierRank,
        current_sub_tier: int,
        current_stars: int,
        profile: UserArenaProfile,
    ) -> dict:
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

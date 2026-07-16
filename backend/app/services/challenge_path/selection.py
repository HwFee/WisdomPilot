"""Challenge selection service - exercise selection and path creation."""

import logging
import random
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.arena_exercise_progress import ArenaExerciseProgress
from app.models.exercise import Exercise
from app.models.stats import ActivityLog
from app.models.user import User
from app.models.user_arena import UserArenaProfile
from app.services.adaptive_recommendation import AdaptiveRecommendationService
from app.services.challenge_path.errors import InsufficientChallengeExercisesError
from app.services.hybrid_recommendation import HybridRecommendationService

logger = logging.getLogger(__name__)

MIN_CHALLENGE_DIFFICULTY = 1
MAX_CHALLENGE_DIFFICULTY = 8
CHALLENGE_CANDIDATE_MULTIPLIER = 3
APPEND_DIFFICULTY_WINDOW = 2
APPEND_CANDIDATE_MULTIPLIER = 2
MAX_EXISTING_DIFFICULTY_SAMPLE = 100
# Fixed first two exercises
HELLO_WORLD_EXERCISE_ID = 211
A_PLUS_B_EXERCISE_ID = 207


class ChallengeSelectionService:
    """Service for selecting and creating challenge path exercises."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _has_behavior_data(self, user_id: str) -> bool:
        """Check if user has behavior data useful for recommendation."""
        profile_result = await self.db.execute(
            select(UserArenaProfile).where(UserArenaProfile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()
        if profile and getattr(profile, "behavior_embedding", None):
            return True

        progress_count = await self._get_exercise_count(user_id)
        if progress_count > 0:
            return True

        activity_result = await self.db.execute(
            select(ActivityLog)
            .where(
                ActivityLog.user_id == user_id,
                ActivityLog.activity_type == "exercise_complete",
            )
            .limit(1)
        )
        if activity_result.scalar_one_or_none():
            return True

        return False

    async def _get_exercise_count(self, user_id: str) -> int:
        """Get total exercise count for user's challenge path."""
        result = await self.db.execute(
            select(func.count())
            .select_from(ArenaExerciseProgress)
            .where(ArenaExerciseProgress.user_id == user_id)
        )
        return result.scalar() or 0

    async def _select_verified_exercises_by_difficulty(
        self,
        difficulty_level: int,
        count: int,
    ) -> list[Exercise]:
        """Select verified exercises near the requested difficulty."""
        exercises_result = await self.db.execute(
            select(Exercise)
            .where(
                Exercise.is_verified,
                Exercise.difficulty == difficulty_level,
            )
            .limit(count * CHALLENGE_CANDIDATE_MULTIPLIER)
        )
        all_exercises = list(exercises_result.scalars().all())

        if len(all_exercises) < count:
            exercises_result = await self.db.execute(
                select(Exercise)
                .where(
                    Exercise.is_verified,
                    Exercise.difficulty >= max(
                        MIN_CHALLENGE_DIFFICULTY,
                        difficulty_level - 1,
                    ),
                    Exercise.difficulty <= min(
                        MAX_CHALLENGE_DIFFICULTY,
                        difficulty_level + 1,
                    ),
                )
                .limit(count * CHALLENGE_CANDIDATE_MULTIPLIER)
            )
            all_exercises = list(exercises_result.scalars().all())

        return all_exercises

    async def _find_fixed_exercise(self, exercise_id: int) -> Optional[Exercise]:
        """Get fixed exercise by ID."""
        result = await self.db.execute(
            select(Exercise).where(
                Exercise.id == exercise_id,
                Exercise.is_verified,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _ensure_fixed_first_two(
        selected: list[Exercise],
        hello_world_ex: Optional[Exercise],
        a_plus_b_ex: Optional[Exercise],
        count: int,
    ) -> list[Exercise]:
        """Force first two exercises to be Hello World and A+B."""
        if not selected:
            return selected[:count]

        fixed = []
        if hello_world_ex:
            fixed.append(hello_world_ex)
        if a_plus_b_ex:
            fixed.append(a_plus_b_ex)

        if not fixed:
            return selected[:count]

        fixed_ids = {ex.id for ex in fixed}
        filtered = [ex for ex in selected if ex.id not in fixed_ids]

        result = fixed + filtered
        return result[:count]

    async def select_initial_exercises(
        self,
        user_id: str,
        difficulty_level: int,
        count: int,
    ) -> list[Exercise]:
        """Create initial exercise set for a new challenge path."""
        hello_world_ex = await self._find_fixed_exercise(HELLO_WORLD_EXERCISE_ID)
        a_plus_b_ex = await self._find_fixed_exercise(A_PLUS_B_EXERCISE_ID)
        if hello_world_ex:
            logger.info(f"Fixed exercise[0]: Hello World id={hello_world_ex.id}")
        if a_plus_b_ex:
            logger.info(f"Fixed exercise[1]: A+B id={a_plus_b_ex.id}")

        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        has_behavior = await self._has_behavior_data(user_id) if user else False

        if user and has_behavior:
            logger.info(f"User {user_id[:8]}... has behavior data, using recommendation services")

            hybrid_service = HybridRecommendationService(self.db)
            recommendations = await hybrid_service.get_recommendations(
                user_id=user_id,
                course_id=None,
                limit=count,
                min_difficulty=max(MIN_CHALLENGE_DIFFICULTY, difficulty_level - 1),
                max_difficulty=min(MAX_CHALLENGE_DIFFICULTY, difficulty_level + 1),
            )

            if recommendations:
                recommended_ids = [rec["exercise_id"] for rec in recommendations]

                result = await self.db.execute(
                    select(Exercise).where(Exercise.id.in_(recommended_ids))
                )
                exercises_map = {ex.id: ex for ex in result.scalars().all()}
                selected = [
                    exercises_map[eid]
                    for eid in recommended_ids
                    if eid in exercises_map
                ]

                if len(selected) >= count:
                    return self._ensure_fixed_first_two(
                        selected, hello_world_ex, a_plus_b_ex, count
                    )

            adaptive_service = AdaptiveRecommendationService(self.db)
            recommendation = await adaptive_service.get_recommendations(
                user=user,
                limit=count,
                min_difficulty=max(MIN_CHALLENGE_DIFFICULTY, difficulty_level - 1),
                max_difficulty=min(MAX_CHALLENGE_DIFFICULTY, difficulty_level + 1),
                learning_path="challenge",
            )

            recommended_ids = [
                rec["exercise_id"] for rec in recommendation.get("recommendations", [])
            ]

            if recommended_ids:
                result = await self.db.execute(
                    select(Exercise).where(Exercise.id.in_(recommended_ids))
                )
                exercises_map = {ex.id: ex for ex in result.scalars().all()}
                selected = [
                    exercises_map[eid]
                    for eid in recommended_ids
                    if eid in exercises_map
                ]

                if len(selected) >= count:
                    return self._ensure_fixed_first_two(
                        selected, hello_world_ex, a_plus_b_ex, count
                    )

        effective_difficulty = (
            MIN_CHALLENGE_DIFFICULTY if not has_behavior else difficulty_level
        )
        logger.info(
            f"Challenge path (fast path): user={user_id[:8]}... "
            f"has_behavior={has_behavior}, selecting {count} exercises "
            f"by difficulty={effective_difficulty}"
        )
        logger.info(
            f"Challenge path: selecting {count} exercises from all verified exercises "
            f"(difficulty_level={effective_difficulty})"
        )

        all_exercises = await self._select_verified_exercises_by_difficulty(
            effective_difficulty,
            count,
        )

        if len(all_exercises) < count and effective_difficulty != difficulty_level:
            all_exercises = await self._select_verified_exercises_by_difficulty(
                difficulty_level,
                count,
            )

        if len(all_exercises) < count:
            exercises_result = await self.db.execute(
                select(Exercise)
                .where(
                    Exercise.is_verified,
                    Exercise.difficulty >= MIN_CHALLENGE_DIFFICULTY,
                    Exercise.difficulty <= min(
                        MAX_CHALLENGE_DIFFICULTY,
                        effective_difficulty + 1,
                    ),
                )
                .limit(count * CHALLENGE_CANDIDATE_MULTIPLIER)
            )
            all_exercises = list(exercises_result.scalars().all())

        if len(all_exercises) < count:
            raise InsufficientChallengeExercisesError(
                found=len(all_exercises),
                required=count,
            )

        exercise_pool = list(all_exercises)
        selected = random.sample(exercise_pool, min(count, len(exercise_pool)))
        return self._ensure_fixed_first_two(
            selected,
            hello_world_ex,
            a_plus_b_ex,
            count,
        )

    async def _infer_append_difficulty(
        self,
        existing_ids: list[int],
        requested_difficulty: int | None,
    ) -> int:
        if requested_difficulty is not None:
            return requested_difficulty
        if not existing_ids:
            return MIN_CHALLENGE_DIFFICULTY
        result = await self.db.execute(
            select(Exercise)
            .where(Exercise.id.in_(existing_ids))
            .limit(MAX_EXISTING_DIFFICULTY_SAMPLE)
        )
        sampled = list(result.scalars().all())
        if not sampled:
            return MIN_CHALLENGE_DIFFICULTY
        average = sum(exercise.difficulty for exercise in sampled) / len(sampled)
        return max(
            MIN_CHALLENGE_DIFFICULTY,
            min(MAX_CHALLENGE_DIFFICULTY, round(average)),
        )

    async def _recommended_append_exercises(
        self,
        *,
        user_id: str,
        difficulty_level: int,
        count: int,
        existing_ids: list[int],
    ) -> list[Exercise]:
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if user is None:
            return []
        recommendation = await AdaptiveRecommendationService(
            self.db
        ).get_recommendations(
            user=user,
            limit=count,
            min_difficulty=max(
                MIN_CHALLENGE_DIFFICULTY,
                difficulty_level - APPEND_DIFFICULTY_WINDOW,
            ),
            max_difficulty=min(
                MAX_CHALLENGE_DIFFICULTY,
                difficulty_level + APPEND_DIFFICULTY_WINDOW,
            ),
            learning_path="challenge",
            exclude_ids=existing_ids,
        )
        recommended_ids = [
            item["exercise_id"]
            for item in recommendation.get("recommendations", [])
        ]
        if not recommended_ids:
            return []
        result = await self.db.execute(
            select(Exercise).where(Exercise.id.in_(recommended_ids))
        )
        exercises_by_id = {
            exercise.id: exercise for exercise in result.scalars().all()
        }
        return [
            exercises_by_id[exercise_id]
            for exercise_id in recommended_ids
            if exercise_id in exercises_by_id
        ]

    async def _fallback_append_exercises(
        self,
        *,
        difficulty_level: int,
        remaining_count: int,
        requested_count: int,
        excluded_ids: list[int],
    ) -> list[Exercise]:
        candidate_limit = requested_count * APPEND_CANDIDATE_MULTIPLIER
        statements = (
            select(Exercise)
            .where(
                Exercise.is_verified,
                Exercise.difficulty == difficulty_level,
                ~Exercise.id.in_(excluded_ids),
            )
            .limit(candidate_limit),
            select(Exercise)
            .where(
                Exercise.is_verified,
                Exercise.difficulty
                >= max(
                    MIN_CHALLENGE_DIFFICULTY,
                    difficulty_level - APPEND_DIFFICULTY_WINDOW,
                ),
                Exercise.difficulty
                <= min(
                    MAX_CHALLENGE_DIFFICULTY,
                    difficulty_level + APPEND_DIFFICULTY_WINDOW,
                ),
                ~Exercise.id.in_(excluded_ids),
            )
            .limit(candidate_limit),
            select(Exercise)
            .where(
                Exercise.is_verified,
                Exercise.difficulty >= MIN_CHALLENGE_DIFFICULTY,
                Exercise.difficulty
                <= min(
                    MAX_CHALLENGE_DIFFICULTY,
                    difficulty_level + APPEND_DIFFICULTY_WINDOW,
                ),
                ~Exercise.id.in_(excluded_ids),
            )
            .limit(candidate_limit),
        )
        candidates: list[Exercise] = []
        for statement in statements:
            result = await self.db.execute(statement)
            candidates = list(result.scalars().all())
            if len(candidates) >= remaining_count:
                break
        if not candidates:
            return []
        return random.sample(
            candidates,
            min(remaining_count, len(candidates)),
        )

    async def select_append_exercises(
        self,
        *,
        user_id: str,
        existing_ids: list[int],
        difficulty_level: int | None,
        count: int,
    ) -> list[Exercise]:
        effective_difficulty = await self._infer_append_difficulty(
            existing_ids,
            difficulty_level,
        )
        selected = await self._recommended_append_exercises(
            user_id=user_id,
            difficulty_level=effective_difficulty,
            count=count,
            existing_ids=existing_ids,
        )
        if len(selected) >= count:
            return selected[:count]
        fallback = await self._fallback_append_exercises(
            difficulty_level=effective_difficulty,
            remaining_count=count - len(selected),
            requested_count=count,
            excluded_ids=existing_ids + [exercise.id for exercise in selected],
        )
        return selected + fallback

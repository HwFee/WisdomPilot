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

DEFAULT_DIFFICULTY_LEVEL = 3
DEFAULT_INITIAL_COUNT = 3
DEFAULT_APPEND_COUNT = 5
MIN_CHALLENGE_DIFFICULTY = 1
MAX_CHALLENGE_DIFFICULTY = 8
CHALLENGE_CANDIDATE_MULTIPLIER = 3
DEFAULT_CHALLENGE_LANGUAGE = "python"

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

    async def _create_progress_for_selected_exercises(
        self,
        user_id: str,
        exercises: list[Exercise],
        start_index: int = 0,
    ) -> None:
        """Create challenge progress records for selected exercises."""
        for index_offset, exercise in enumerate(exercises):
            exercise_index = start_index + index_offset
            progress = ArenaExerciseProgress(
                user_id=user_id,
                exercise_id=exercise.id,
                exercise_index=exercise_index,
                is_unlocked=(exercise_index == 0),
            )
            self.db.add(progress)

    async def _create_initial_exercises(
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
                    selected = self._ensure_fixed_first_two(
                        selected, hello_world_ex, a_plus_b_ex, count
                    )
                    await self._create_progress_for_selected_exercises(
                        user_id, selected, start_index=0
                    )

                    await self.db.flush()
                    return selected

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
                    selected = self._ensure_fixed_first_two(
                        selected, hello_world_ex, a_plus_b_ex, count
                    )
                    await self._create_progress_for_selected_exercises(
                        user_id, selected, start_index=0
                    )

                    await self.db.flush()
                    return selected

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
        selected = self._ensure_fixed_first_two(selected, hello_world_ex, a_plus_b_ex, count)

        await self._create_progress_for_selected_exercises(user_id, selected)
        await self.db.flush()
        return selected

    async def get_or_create_challenge_path(
        self,
        user_id: str,
        difficulty_level: int = DEFAULT_DIFFICULTY_LEVEL,
        initial_count: int = DEFAULT_INITIAL_COUNT,
    ) -> tuple[list[Exercise], bool]:
        """Get existing exercises or create initial set.

        Returns:
            tuple: (exercises, is_new)
        """
        from app.services.challenge_path.progress import ChallengeProgressService

        progress_service = ChallengeProgressService(self.db)
        existing_progress = await progress_service._get_user_progress(user_id)

        if existing_progress:
            exercises = await progress_service._get_exercises_from_progress(existing_progress)
            return exercises, False

        exercises = await self._create_initial_exercises(
            user_id, difficulty_level, initial_count
        )
        return exercises, True

    async def append_exercises(
        self,
        user_id: str,
        difficulty_level: Optional[int] = None,
        count: int = DEFAULT_APPEND_COUNT,
    ) -> list[int]:
        """Append more exercises to the challenge path."""
        max_index_result = await self.db.execute(
            select(func.max(ArenaExerciseProgress.exercise_index)).where(
                ArenaExerciseProgress.user_id == user_id,
            )
        )
        max_index = max_index_result.scalar() or -1

        existing_result = await self.db.execute(
            select(ArenaExerciseProgress.exercise_id).where(
                ArenaExerciseProgress.user_id == user_id,
            )
        )
        existing_ids = list(set(row[0] for row in existing_result.fetchall()))

        if difficulty_level is None:
            existing_exercises_result = await self.db.execute(
                select(Exercise)
                .where(Exercise.id.in_(existing_ids))
                .limit(100)
            )
            existing_exercises = list(existing_exercises_result.scalars().all())
            if existing_exercises:
                avg_difficulty = sum(ex.difficulty for ex in existing_exercises) / len(existing_exercises)
                difficulty_level = max(1, min(8, round(avg_difficulty)))
            else:
                difficulty_level = 1

        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        selected = []

        if user:
            adaptive_service = AdaptiveRecommendationService(self.db)
            recommendation = await adaptive_service.get_recommendations(
                user=user,
                limit=count,
                min_difficulty=max(1, difficulty_level - 2),
                max_difficulty=min(8, difficulty_level + 2),
                learning_path="challenge",
                exclude_ids=existing_ids,
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

        if len(selected) < count:
            all_exclude = existing_ids + [ex.id for ex in selected]

            exercises_result = await self.db.execute(
                select(Exercise)
                .where(
                    Exercise.is_verified,
                    Exercise.difficulty == difficulty_level,
                    ~Exercise.id.in_(all_exclude),
                )
                .limit(count * 2)
            )
            all_exercises = exercises_result.scalars().all()

            if len(all_exercises) < count - len(selected):
                exercises_result = await self.db.execute(
                    select(Exercise)
                    .where(
                        Exercise.is_verified,
                        Exercise.difficulty >= max(1, difficulty_level - 2),
                        Exercise.difficulty <= min(8, difficulty_level + 2),
                        ~Exercise.id.in_(all_exclude),
                    )
                    .limit(count * 2)
                )
                all_exercises = exercises_result.scalars().all()

            if len(all_exercises) < count - len(selected):
                exercises_result = await self.db.execute(
                    select(Exercise)
                    .where(
                        Exercise.is_verified,
                        Exercise.difficulty >= 1,
                        Exercise.difficulty <= min(8, difficulty_level + 2),
                        ~Exercise.id.in_(all_exclude),
                    )
                    .limit(count * 2)
                )
                all_exercises = exercises_result.scalars().all()

            remaining = (
                random.sample(
                    list(all_exercises), min(count - len(selected), len(all_exercises))
                )
                if all_exercises
                else []
            )
            selected.extend(remaining)

        if not selected:
            return []

        last_exercise_completed = False
        if max_index >= 0:
            last_result = await self.db.execute(
                select(ArenaExerciseProgress).where(
                    ArenaExerciseProgress.user_id == user_id,
                    ArenaExerciseProgress.exercise_index == max_index,
                )
            )
            last_progress = last_result.scalar_one_or_none()
            last_exercise_completed = (
                last_progress.is_completed if last_progress else False
            )

        new_ids = []
        for i, ex in enumerate(selected):
            progress = ArenaExerciseProgress(
                user_id=user_id,
                exercise_id=ex.id,
                exercise_index=max_index + 1 + i,
                is_unlocked=(i == 0 and (max_index < 0 or last_exercise_completed)),
            )
            self.db.add(progress)
            new_ids.append(ex.id)

        await self.db.commit()
        return new_ids

"""
User Profile Service for Hybrid Recommendation

Updates user profile embeddings and statistics based on exercise behavior.

User embedding formula:
    user_vector = correct_exercise_embeddings_weighted_avg × 0.6
                - incorrect_exercise_embeddings_weighted_avg × 0.4

Behavior categories:
    - Fast correct (< 5 min): High weight for strength
    - Slow correct (> 2 attempts): Practice needed
    - Incorrect: Weakness direction
"""

import json
import logging
import math
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.exercise import Exercise
from app.models.user_arena import UserArenaProfile
from app.models.arena_exercise_progress import ArenaExerciseProgress


logger = logging.getLogger(__name__)


# Time thresholds (in seconds)
FAST_SOLVER_THRESHOLD = 300  # 5 minutes
SLOW_SOLVER_THRESHOLD = 600  # 10 minutes


class UserProfileService:
    """
    Service for updating user profile embeddings and statistics.

    Usage:
        service = UserProfileService(db)
        await service.update_after_exercise(
            user_id="user123",
            course_id=1,
            exercise_id=1,
            is_correct=True,
            time_spent=180,
        )
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_profile(
        self,
        user_id: str,
        course_id: Optional[int] = None,
    ) -> UserArenaProfile:
        """Get or create user arena profile (global, not per-course)."""
        result = await self.db.execute(
            select(UserArenaProfile).where(
                UserArenaProfile.user_id == user_id,
            )
        )
        profile = result.scalar_one_or_none()

        if not profile:
            profile = UserArenaProfile(
                user_id=user_id,
            )
            self.db.add(profile)
            await self.db.flush()

        return profile

    async def get_or_create_profile_for_update(
        self, user_id: str
    ) -> UserArenaProfile:
        result = await self.db.execute(
            select(UserArenaProfile)
            .where(UserArenaProfile.user_id == user_id)
            .with_for_update()
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            profile = UserArenaProfile(user_id=user_id)
            self.db.add(profile)
            await self.db.flush()
        return profile

    async def update_after_exercise(
        self,
        user_id: str,
        exercise_id: int,
        is_correct: bool,
        course_id: Optional[int] = None,
        time_spent: Optional[int] = None,
        hint_used: bool = False,
        first_attempt_correct: Optional[bool] = None,
    ) -> dict:
        profile = await self.get_or_create_profile_for_update(user_id)
        exercise_result = await self.db.execute(
            select(Exercise).where(Exercise.id == exercise_id)
        )
        exercise = exercise_result.scalar_one_or_none()
        exercise_embedding = None
        if exercise and exercise.embedding:
            try:
                exercise_embedding = json.loads(exercise.embedding)
            except json.JSONDecodeError:
                logger.warning(
                    "Failed to parse exercise embedding for %s", exercise_id
                )
        if exercise_embedding:
            await self._update_behavior_embedding(
                profile, exercise_embedding, is_correct, time_spent
            )
        await self._update_statistics(profile)
        await self.db.flush()
        return {
            "avg_accuracy": profile.avg_accuracy,
            "avg_time_spent": profile.avg_time_spent,
            "total_submissions": profile.total_submissions,
            "has_behavior_embedding": profile.behavior_embedding is not None,
        }

    async def _update_behavior_embedding(
        self,
        profile: UserArenaProfile,
        exercise_embedding: list[float],
        is_correct: bool,
        time_spent: Optional[int],
    ) -> None:
        """
        Update user behavior embedding based on exercise result.

        Formula:
            - Fast correct (time < 5min): weight = 1.0
            - Slow correct (time >= 5min): weight = 0.5
            - Incorrect: weight = -0.8
        """
        # Determine weight based on performance
        if is_correct:
            if time_spent and time_spent < FAST_SOLVER_THRESHOLD:
                weight = 1.0  # Fast correct - strong indicator of strength
            elif time_spent and time_spent > SLOW_SOLVER_THRESHOLD:
                weight = 0.4  # Slow correct - weaker indicator
            else:
                weight = 0.7  # Normal correct
        else:
            weight = -0.8  # Incorrect - negative indicator

        # Get current embedding or initialize
        current_embedding = None
        if profile.behavior_embedding:
            try:
                current_embedding = json.loads(profile.behavior_embedding)
            except json.JSONDecodeError:
                logger.warning("Failed to parse behavior embedding, reinitializing")

        if current_embedding is None:
            # Initialize new embedding
            if weight > 0:
                new_embedding = [v * weight for v in exercise_embedding]
            else:
                # For negative weight, initialize with small positive direction
                # then subtract the exercise embedding direction
                new_embedding = [v * 0.3 for v in exercise_embedding]
        else:
            # Weighted average with current embedding
            # More weight to recent performance
            alpha = 0.3  # Learning rate
            new_embedding = []
            for i in range(len(exercise_embedding)):
                current_val = current_embedding[i] if i < len(current_embedding) else 0.0
                new_val = current_val * (1 - alpha) + exercise_embedding[i] * weight * alpha
                new_embedding.append(new_val)

        # Normalize embedding
        magnitude = math.sqrt(sum(v * v for v in new_embedding))
        if magnitude > 0:
            new_embedding = [v / magnitude for v in new_embedding]

        profile.behavior_embedding = json.dumps(new_embedding)

    async def _update_statistics(
        self,
        profile: UserArenaProfile,
    ) -> None:
        """Recompute arena statistics from ordered progress records."""
        rows = list(
            (
                await self.db.execute(
                    select(ArenaExerciseProgress, Exercise)
                    .join(
                        Exercise,
                        ArenaExerciseProgress.exercise_id == Exercise.id,
                    )
                    .where(ArenaExerciseProgress.user_id == profile.user_id)
                    .order_by(ArenaExerciseProgress.exercise_index)
                )
            ).all()
        )
        progresses = [progress for progress, _ in rows]
        exercise_by_id = {
            progress.exercise_id: exercise for progress, exercise in rows
        }

        # Aggregate every persisted Arena statistic from the same ordered snapshot.
        completed = [progress for progress in progresses if progress.is_completed]
        correct = [progress for progress in progresses if progress.is_correct]
        profile.total_challenges = len(completed)
        profile.wins = len(correct)
        profile.losses = len(completed) - len(correct)
        profile.total_submissions = sum(
            progress.attempt_count for progress in progresses
        )
        profile.avg_accuracy = len(correct) / len(progresses) if progresses else 0.0
        times = [progress.time_spent for progress in progresses if progress.time_spent]
        profile.avg_time_spent = sum(times) / len(times) if times else 0.0
        profile.highest_difficulty = max(
            (
                exercise_by_id[progress.exercise_id].difficulty
                for progress in completed
                if progress.exercise_id in exercise_by_id
            ),
            default=0,
        )

        # Future unlocked exercises have no attempts and must not break a streak.
        attempted_progresses = [
            progress for progress in progresses if progress.attempt_count > 0
        ]
        best_streak = 0
        current_run = 0
        for progress in attempted_progresses:
            if progress.is_correct:
                current_run += 1
                best_streak = max(best_streak, current_run)
            else:
                current_run = 0
        profile.best_streak = best_streak

        current_streak = 0
        for progress in reversed(attempted_progresses):
            if not progress.is_correct:
                break
            current_streak += 1
        profile.current_streak = current_streak

    async def recalculate_full_embedding(
        self,
        user_id: str,
        course_id: int,
    ) -> dict:
        """
        Recalculate user embedding from all exercise history.

        This is useful for initial setup or periodic recalculation.
        """
        profile = await self.get_or_create_profile(user_id, course_id)

        # Get all progress with exercise embeddings
        result = await self.db.execute(
            select(ArenaExerciseProgress, Exercise)
            .join(Exercise, ArenaExerciseProgress.exercise_id == Exercise.id)
            .where(
                ArenaExerciseProgress.user_id == user_id,
                
                Exercise.embedding.isnot(None),
            )
        )
        rows = result.all()

        if not rows:
            return {"status": "no_data", "exercises_processed": 0}

        # Separate correct and incorrect exercises
        correct_embeddings = []
        incorrect_embeddings = []

        for progress, exercise in rows:
            try:
                embedding = json.loads(exercise.embedding)

                # Apply time-based weight
                if progress.is_correct:
                    time_spent = progress.time_spent or 300
                    if time_spent < FAST_SOLVER_THRESHOLD:
                        weight = 1.0
                    elif time_spent > SLOW_SOLVER_THRESHOLD:
                        weight = 0.4
                    else:
                        weight = 0.7
                    correct_embeddings.append((embedding, weight))
                else:
                    incorrect_embeddings.append(embedding)
            except Exception:
                continue

        # Calculate weighted average for correct
        if correct_embeddings:
            total_weight = sum(w for _, w in correct_embeddings)
            correct_avg = [
                sum(e[i] * w for e, w in correct_embeddings) / total_weight
                for i in range(len(correct_embeddings[0][0]))
            ]
        else:
            correct_avg = None

        # Calculate average for incorrect
        if incorrect_embeddings:
            incorrect_avg = [
                sum(e[i] for e in incorrect_embeddings) / len(incorrect_embeddings)
                for i in range(len(incorrect_embeddings[0]))
            ]
        else:
            incorrect_avg = None

        # Combine: correct × 0.6 - incorrect × 0.4
        if correct_avg and incorrect_avg:
            user_embedding = [
                correct_avg[i] * 0.6 - incorrect_avg[i] * 0.4
                for i in range(len(correct_avg))
            ]
        elif correct_avg:
            user_embedding = [v * 0.6 for v in correct_avg]
        elif incorrect_avg:
            user_embedding = [v * -0.4 for v in incorrect_avg]
        else:
            return {"status": "no_valid_embeddings", "exercises_processed": len(rows)}

        # Normalize
        magnitude = math.sqrt(sum(v * v for v in user_embedding))
        if magnitude > 0:
            user_embedding = [v / magnitude for v in user_embedding]

        profile.behavior_embedding = json.dumps(user_embedding)
        await self.db.commit()

        return {
            "status": "success",
            "exercises_processed": len(rows),
            "correct_count": len(correct_embeddings),
            "incorrect_count": len(incorrect_embeddings),
        }

    async def get_user_stats(
        self,
        user_id: str,
        course_id: int,
    ) -> dict:
        """Get user statistics for recommendation."""
        profile = await self.get_or_create_profile(user_id, course_id)

        # Get exercise progress stats
        result = await self.db.execute(
            select(ArenaExerciseProgress).where(
                ArenaExerciseProgress.user_id == user_id,
                
            )
        )
        progresses = list(result.scalars().all())

        total = len(progresses)
        completed = [p for p in progresses if p.is_completed]
        completed_count = len(completed)
        correct = sum(1 for p in completed if p.is_correct)
        total_attempts = sum(p.attempt_count for p in progresses)

        # Calculate average attempts per completed exercise
        avg_attempts = total_attempts / completed_count if completed_count > 0 else 0

        # Parse behavior embedding
        behavior_embedding = None
        if hasattr(profile, 'behavior_embedding') and profile.behavior_embedding:
            try:
                behavior_embedding = json.loads(profile.behavior_embedding)
            except json.JSONDecodeError:
                logger.warning("Failed to parse behavior embedding for user %s", user_id)

        # Calculate accuracy based on completed exercises only
        accuracy = correct / completed_count if completed_count > 0 else 0.0

        # User level based on tier (段位)
        from app.core.tier_config import tier_from_string, TierRank
        tier = tier_from_string(profile.tier) if profile.tier else TierRank.BRONZE
        # Map tier to level 1-8: bronze=1-2, silver=3-4, gold=5-6, platinum/diamond/master/king=7-8
        tier_level_map = {
            TierRank.BRONZE: 1,
            TierRank.SILVER: 3,
            TierRank.GOLD: 5,
            TierRank.PLATINUM: 7,
            TierRank.DIAMOND: 7,
            TierRank.MASTER: 8,
            TierRank.KING: 8,
        }
        base_level = tier_level_map.get(tier, 1)
        # Add sub_tier contribution (sub_tier 1=I is highest, 5=V is lowest)
        sub_tier = profile.sub_tier if profile.sub_tier else 4
        user_level = min(8, max(1, base_level + (5 - sub_tier) * 0.2))

        return {
            "accuracy": accuracy,
            "avg_attempts": avg_attempts,
            "total_submissions": total_attempts,
            "current_streak": profile.current_streak or 0,
            "best_streak": profile.best_streak or 0,
            "behavior_embedding": behavior_embedding,
            "user_level": user_level,
            "total_exercises": total,
            "completed_exercises": completed_count,
            # 段位信息
            "tier": profile.tier or "bronze",
            "sub_tier": sub_tier,
            "stars": profile.stars or 0,
        }


def get_user_profile_service(db: AsyncSession) -> UserProfileService:
    """Factory function to create service instance."""
    return UserProfileService(db)

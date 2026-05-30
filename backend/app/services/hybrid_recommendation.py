"""
Hybrid Recommendation Service

Implements a fusion recommendation algorithm combining:
1. Behavior-based scoring (40%) - User behavior patterns
2. Embedding similarity (35%) - Semantic matching
3. Difficulty matching (25%) - ZPD-based difficulty alignment

Formula:
    final_score = 0.40 × behavior_score
                + 0.35 × embedding_similarity
                + 0.25 × difficulty_match
"""

import json
import logging
import math
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.exercise import Exercise
from app.models.user_arena import UserArenaProfile
from app.models.arena_exercise_progress import ArenaExerciseProgress


logger = logging.getLogger(__name__)



# Fusion weights (must sum to 1.0)
FUSION_WEIGHTS = {
    "behavior": 0.40,
    "embedding": 0.35,
    "difficulty": 0.25,
}


def calculate_cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity (-1.0 to 1.0), or 0.0 for invalid inputs
    """
    if not vec1 or not vec2:
        return 0.0

    if len(vec1) != len(vec2):
        return 0.0

    # Calculate dot product and magnitudes
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


class BehaviorScorer:
    """
    Scores exercises based on user behavior patterns.

    Strategy:
    - High accuracy (>80%) → Bonus for challenging problems
    - Low accuracy (<50%) → Bonus for foundational problems
    - Low attempts (<2) → Quick learner, bonus for depth
    - High attempts (>3) → Need practice, bonus for foundation
    - Many submissions (>50) → Experienced, bonus for challenges
    """

    def calculate(
        self,
        user_stats: dict,
        exercise_difficulty: int,
    ) -> float:
        """
        Calculate behavior-based score for an exercise.

        Args:
            user_stats: Dict with accuracy, avg_attempts, total_submissions
            exercise_difficulty: Exercise difficulty level (1-8)

        Returns:
            Score between 0.0 and 1.0
        """
        accuracy = user_stats.get("accuracy", 0.5)
        avg_attempts = user_stats.get("avg_attempts", 1.0)
        total_submissions = user_stats.get("total_submissions", 0)

        score = 0.5  # Base score

        # High accuracy user → favor challenging problems
        if accuracy > 0.8:
            if exercise_difficulty >= 4:
                score += 0.25  # Bonus for hard problems
        # Low accuracy user → favor foundational problems
        elif accuracy < 0.5:
            if exercise_difficulty <= 3:
                score += 0.20  # Bonus for foundation

        # Low attempts (<2) → quick learner, bonus for depth
        if avg_attempts < 2:
            if exercise_difficulty >= 4:
                score += 0.15  # Bonus for depth
        # High attempts (>3) → need practice, bonus for foundation
        elif avg_attempts > 3:
            if exercise_difficulty <= 3:
                score += 0.15  # Bonus for foundation

        # Experienced user → bonus for challenges
        if total_submissions > 50:
            if exercise_difficulty >= 5:
                score += 0.10

        # Cap at 1.0
        return min(1.0, max(0.0, score))


class EmbeddingScorer:
    """
    Scores exercises based on embedding similarity.

    Higher similarity indicates the exercise matches the user's
    learning profile (strengths and weaknesses).
    """

    def calculate(
        self,
        user_embedding: Optional[list[float]],
        exercise_embedding: Optional[list[float]],
    ) -> float:
        """
        Calculate embedding-based score.

        Args:
            user_embedding: User's profile embedding vector
            exercise_embedding: Exercise's tag embedding vector

        Returns:
            Score between 0.0 and 1.0 (normalized from cosine similarity)
        """
        if user_embedding is None or exercise_embedding is None:
            return 0.5  # Neutral default when embeddings unavailable

        similarity = calculate_cosine_similarity(user_embedding, exercise_embedding)

        # Normalize from [-1, 1] to [0, 1]
        return (similarity + 1.0) / 2.0


class DifficultyScorer:
    """
    Scores exercises based on ZPD (Zone of Proximal Development).

    Target difficulty = user_level + 0.5 (slightly above current level)
    Closer to target → higher score
    """

    def calculate(
        self,
        user_level: float,
        exercise_difficulty: int,
    ) -> float:
        """
        Calculate ZPD-based difficulty score.

        Args:
            user_level: Estimated user level (1-8)
            exercise_difficulty: Exercise difficulty level (1-8)

        Returns:
            Score between 0.0 and 1.0
        """
        # Target difficulty: slightly above user level
        target_difficulty = user_level + 0.5

        # Calculate distance from target
        distance = abs(exercise_difficulty - target_difficulty)

        # Score decreases with distance
        if distance == 0:
            return 1.0  # Perfect match
        elif distance <= 0.5:
            return 0.9
        elif distance <= 1.0:
            return 0.75
        elif distance <= 2.0:
            return 0.5
        elif distance <= 3.0:
            return 0.25
        else:
            return 0.1  # Too far from ZPD


class HybridRecommendationService:
    """
    Hybrid recommendation service combining behavior, embedding, and difficulty scores.

    Usage:
        service = HybridRecommendationService(db)
        recommendations = await service.get_recommendations(
            user_id="user123",
            course_id=1,
            limit=10,
        )
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.behavior_scorer = BehaviorScorer()
        self.embedding_scorer = EmbeddingScorer()
        self.difficulty_scorer = DifficultyScorer()

    def get_fusion_weights(self) -> dict[str, float]:
        """Return fusion weights (sum to 1.0)"""
        return FUSION_WEIGHTS.copy()

    def calculate_final_score(
        self,
        behavior_score: float,
        embedding_score: float,
        difficulty_score: float,
    ) -> float:
        """Calculate weighted final score"""
        return (
            FUSION_WEIGHTS["behavior"] * behavior_score +
            FUSION_WEIGHTS["embedding"] * embedding_score +
            FUSION_WEIGHTS["difficulty"] * difficulty_score
        )

    async def get_user_stats(self, user_id: str, course_id: Optional[int]) -> dict:
        """
        Get user statistics for behavior scoring.

        Args:
            user_id: User ID
            course_id: Course ID. If None, aggregates stats across all courses (for challenge path).

        Returns:
            Dict with accuracy, avg_attempts, total_submissions, behavior_embedding
        """
        # Get user arena profile
        if course_id is not None:
            result = await self.db.execute(
                select(UserArenaProfile).where(
                    UserArenaProfile.user_id == user_id,
                    
                )
            )
            profile = result.scalar_one_or_none()

            # Get exercise progress stats for specific course
            progress_result = await self.db.execute(
                select(ArenaExerciseProgress).where(
                    ArenaExerciseProgress.user_id == user_id,
                    
                )
            )
        else:
            # Challenge path: aggregate across all courses
            result = await self.db.execute(
                select(UserArenaProfile).where(
                    UserArenaProfile.user_id == user_id,
                )
            )
            profiles = list(result.scalars().all())
            profile = profiles[0] if profiles else None

            # Get exercise progress stats across all courses
            progress_result = await self.db.execute(
                select(ArenaExerciseProgress).where(
                    ArenaExerciseProgress.user_id == user_id,
                )
            )

        progresses = list(progress_result.scalars().all())

        total = len(progresses)
        correct = sum(1 for p in progresses if p.is_correct)
        total_attempts = sum(p.attempt_count for p in progresses)

        # Calculate average attempts per exercise
        avg_attempts = total_attempts / total if total > 0 else 1.0

        # Parse behavior embedding
        behavior_embedding = None
        if profile and hasattr(profile, 'behavior_embedding') and profile.behavior_embedding:
            try:
                behavior_embedding = json.loads(profile.behavior_embedding)
            except json.JSONDecodeError:
                logger.warning("Failed to parse behavior embedding for user %s", user_id)

        # Estimate user level from accuracy (scale 1-8)
        accuracy = correct / total if total > 0 else 0.5
        user_level = min(8, max(1, accuracy * 7 + 1))  # Map to 1-8 scale

        return {
            "accuracy": accuracy,
            "avg_attempts": avg_attempts,
            "total_submissions": total_attempts,
            "behavior_embedding": behavior_embedding,
            "user_level": user_level,
            "total_exercises": total,
        }

    async def get_candidate_exercises(
        self,
        course_id: Optional[int],
        exclude_ids: Optional[list[int]] = None,
        limit: int = 100,
        min_difficulty: int = 1,
        max_difficulty: int = 8,
    ) -> list[Exercise]:
        """Get candidate exercises for recommendation.

        Args:
            course_id: Course ID to filter by. If None, selects from all verified exercises
                       (used for challenge path which is independent of courses).
            exclude_ids: Exercise IDs to exclude from results.
            limit: Maximum number of exercises to return.
        """
        # Note: distinct() is unnecessary since Exercise.id is a primary key.
        query = select(Exercise).where(
            Exercise.is_verified,
            Exercise.difficulty >= min_difficulty,
            Exercise.difficulty <= max_difficulty,
        )

        # Challenge path (course_id=None) is independent of courses
        # Only filter by course if course_id is provided
        if course_id is not None:
            from app.models.chapter import Chapter
            query = query.join(Chapter, Exercise.chapter_id == Chapter.id)
            query = query.where(Chapter.course_id == course_id)

        if exclude_ids:
            query = query.where(~Exercise.id.in_(exclude_ids))

        # Random ordering for variety; limit kept small since we only need
        # enough candidates to produce the final recommendation list.
        query = query.order_by(func.random()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    def parse_embedding(self, exercise: Exercise) -> Optional[list[float]]:
        """Parse exercise embedding from JSON string.

        Prefers tag_embedding (semantic) over content embedding.
        """
        # Try tag_embedding first (more relevant for hybrid recommendation)
        if hasattr(exercise, 'tag_embedding') and exercise.tag_embedding:
            try:
                return json.loads(exercise.tag_embedding)
            except json.JSONDecodeError:
                logger.warning("Failed to parse tag_embedding for exercise %s", exercise.id)

        # Fallback to content embedding
        if exercise.embedding:
            try:
                return json.loads(exercise.embedding)
            except json.JSONDecodeError:
                logger.warning("Failed to parse embedding for exercise %s", exercise.id)

        return None

    def generate_recommendation_reasons(
        self,
        scores: dict,
        knowledge_points: list[str],
    ) -> list[str]:
        """
        Generate human-readable recommendation reasons.

        Args:
            scores: Dict with behavior_score, embedding_score, difficulty_score
            knowledge_points: List of knowledge point strings

        Returns:
            List of reason strings
        """
        reasons = []

        if scores.get("behavior_score", 0) > 0.7:
            reasons.append("根据你的做题习惯推荐")

        if scores.get("embedding_score", 0) > 0.7:
            reasons.append("与你擅长的题型相似")

        if scores.get("difficulty_score", 0) > 0.7:
            reasons.append("难度适中，符合你当前水平")

        if knowledge_points:
            reasons.append(f"知识点：{'、'.join(knowledge_points[:3])}")

        return reasons if reasons else ["系统推荐"]

    async def get_recommendations(
        self,
        user_id: str,
        course_id: Optional[int],
        limit: int = 10,
        exclude_ids: Optional[list[int]] = None,
        min_difficulty: int = 1,
        max_difficulty: int = 8,
    ) -> list[dict]:
        """
        Get personalized exercise recommendations.

        Args:
            user_id: User ID
            course_id: Course ID. If None, selects from all verified exercises
                       (used for challenge path which is independent of courses).
            limit: Maximum recommendations to return
            exclude_ids: Exercise IDs to exclude
            min_difficulty: Minimum difficulty filter
            max_difficulty: Maximum difficulty filter

        Returns:
            List of recommendation dicts with exercise_id, final_score, score_breakdown, reasons
        """
        # 1. Get user stats
        user_stats = await self.get_user_stats(user_id, course_id)

        # 2. Get candidate exercises (with difficulty filter at DB level)
        exercises = await self.get_candidate_exercises(
            course_id,
            exclude_ids,
            limit=100,
            min_difficulty=min_difficulty,
            max_difficulty=max_difficulty,
        )

        # 3. Score each exercise
        scored_exercises = []

        for ex in exercises:
            # Skip if outside difficulty range
            if ex.difficulty < min_difficulty or ex.difficulty > max_difficulty:
                continue

            # Calculate component scores
            behavior_score = self.behavior_scorer.calculate(
                user_stats, ex.difficulty
            )

            exercise_embedding = self.parse_embedding(ex)
            embedding_score = self.embedding_scorer.calculate(
                user_stats.get("behavior_embedding"),
                exercise_embedding,
            )

            difficulty_score = self.difficulty_scorer.calculate(
                user_stats.get("user_level", 2.0),
                ex.difficulty,
            )

            # Calculate final score
            final_score = self.calculate_final_score(
                behavior_score, embedding_score, difficulty_score
            )

            # Parse knowledge points
            kp_list = ex.knowledge_points or []
            if isinstance(kp_list, str):
                try:
                    kp_list = json.loads(kp_list)
                except Exception:
                    kp_list = []

            # Generate reasons
            scores = {
                "behavior_score": behavior_score,
                "embedding_score": embedding_score,
                "difficulty_score": difficulty_score,
            }
            reasons = self.generate_recommendation_reasons(scores, kp_list)

            scored_exercises.append({
                "exercise_id": ex.id,
                "difficulty": ex.difficulty,
                "knowledge_points": kp_list,
                "final_score": final_score,
                "score_breakdown": {
                    "behavior": behavior_score,
                    "embedding": embedding_score,
                    "difficulty": difficulty_score,
                },
                "reasons": reasons,
                "title": ex.content.get("title", "") if ex.content else "",
            })

        # 4. Sort by final score
        scored_exercises.sort(key=lambda x: x["final_score"], reverse=True)

        # 5. Deduplicate by title (keep higher scoring one)
        seen_titles = set()
        unique_recommendations = []
        for rec in scored_exercises:
            title = rec.get("title", "")
            if title and title in seen_titles:
                continue
            seen_titles.add(title)
            unique_recommendations.append(rec)

        # 6. Return top recommendations
        return unique_recommendations[:limit]


def get_hybrid_recommendation_service(db: AsyncSession) -> HybridRecommendationService:
    """Factory function to create service instance."""
    return HybridRecommendationService(db)

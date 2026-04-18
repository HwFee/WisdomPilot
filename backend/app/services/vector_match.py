"""
Vector Matching Service for Exercise Recommendation

Provides:
1. Cosine similarity calculation
2. User profile vector generation (based on weak points and learning history)
3. Exercise recommendation by vector similarity
"""

import json
import numpy as np
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.models.exercise import Exercise
from app.models.user import User
from app.models.user_weak_point import UserWeakPoint
from app.config import get_settings


def _get_embedding_config():
    """Get embedding configuration from settings."""
    settings = get_settings()
    return {
        "api_key": settings.EMBEDDING_API_KEY,
        "base_url": settings.EMBEDDING_BASE_URL,
        "model": settings.EMBEDDING_MODEL,
        "dimensions": settings.EMBEDDING_DIMENSIONS,
    }


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Returns a value between -1 and 1:
    - 1: identical direction
    - 0: orthogonal (unrelated)
    - -1: opposite direction

    For zero vectors, returns 0.0 (undefined case).
    """
    arr1 = np.array(vec1, dtype=np.float64)
    arr2 = np.array(vec2, dtype=np.float64)

    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(np.dot(arr1, arr2) / (norm1 * norm2))


async def generate_user_vector(
    user: User,
    weak_points: list[UserWeakPoint],
    db: Optional[AsyncSession] = None,
    preferred_difficulty: int = 2,  # Default to "简单" for new users
) -> list[float]:
    """
    Generate user profile vector based on their weak points and learning history.

    Strategy:
    1. If user has weak points, create text description and generate embedding
    2. If no weak points, generate embedding from user's preferred topics/languages
    3. If no data at all, return a default vector that favors easier exercises

    Args:
        user: User object with weak_points list
        weak_points: List of UserWeakPoint objects
        db: Database session for fetching additional data
        preferred_difficulty: Default difficulty preference for new users (1-5)

    Returns:
        A 1024-dimensional vector (same as exercise embeddings)
    """
    text_parts = []

    # Add weak points (most important)
    if weak_points:
        weak_point_texts = []
        for wp in weak_points:
            weight = wp.error_count / max(wp.mastery_level, 1)  # Higher weight for more errors
            weak_point_texts.append(f"{wp.knowledge_point} (掌握度:{wp.mastery_level}/5, 错误:{wp.error_count}次)")
        text_parts.append(f"薄弱知识点: {', '.join(weak_point_texts)}")

    # Add preferred difficulty
    if hasattr(user, 'preferred_difficulty') and user.preferred_difficulty:
        diff_labels = {1: "入门", 2: "简单", 3: "中等", 4: "困难", 5: "极难"}
        text_parts.append(f"偏好难度: {diff_labels.get(user.preferred_difficulty, '中等')}")
    else:
        # For new users, indicate preference for easier exercises
        diff_labels = {1: "入门", 2: "简单", 3: "中等", 4: "困难", 5: "极难"}
        text_parts.append(f"偏好难度: {diff_labels.get(preferred_difficulty, '简单')}")

    # Add preferred languages
    if hasattr(user, 'preferred_languages') and user.preferred_languages:
        text_parts.append(f"编程语言: {', '.join(user.preferred_languages)}")

    # If we have some user data, generate embedding
    if text_parts:
        text = "\n".join(text_parts)
        return await _get_embedding_from_api(text)

    # Default: return a neutral vector (will match all exercises moderately)
    # Use a small random component to avoid all users having same vector
    config = _get_embedding_config()
    np.random.seed(hash(user.id) % (2**32))
    default_vec = np.random.randn(config["dimensions"]) * 0.1
    default_vec = default_vec / np.linalg.norm(default_vec)  # Normalize
    return default_vec.tolist()


async def _get_embedding_from_api(text: str) -> list[float]:
    """
    Get embedding vector from configured embedding API.

    Args:
        text: Text to embed

    Returns:
        Embedding vector (dimension depends on model)
    """
    import httpx

    if not text.strip():
        config = _get_embedding_config()
        return [0.0] * config["dimensions"]

    config = _get_embedding_config()

    if not config["api_key"]:
        print("Embedding API key not configured")
        return [0.0] * config["dimensions"]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f'{config["base_url"]}/embeddings',
                headers={
                    'Authorization': f'Bearer {config["api_key"]}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': config["model"],
                    'input': text[:8000]  # Limit text length
                }
            )
            if response.status_code == 200:
                return response.json()['data'][0]['embedding']
            else:
                print(f"Embedding API error: {response.status_code}")
                return [0.0] * config["dimensions"]
    except Exception as e:
        print(f"Embedding generation error: {e}")
        return [0.0] * config["dimensions"]


async def recommend_exercises(
    db: AsyncSession,
    user_vector: list[float],
    limit: int = 10,
    exclude_ids: Optional[list[int]] = None,
    min_difficulty: int = 1,
    max_difficulty: int = 5,
    course_id: Optional[int] = None,
    source: str = "loj",
) -> list[dict]:
    """
    Recommend exercises based on vector similarity.

    Args:
        db: Database session
        user_vector: User's profile vector (1024 dimensions)
        limit: Maximum number of recommendations
        exclude_ids: Exercise IDs to exclude (already completed)
        min_difficulty: Minimum difficulty filter
        max_difficulty: Maximum difficulty filter
        course_id: Optional course filter
        source: Exercise source filter (default: loj)

    Returns:
        List of recommendations with exercise_id, similarity, and metadata
    """
    exclude_ids = exclude_ids or []

    # Build query for exercises
    query = select(Exercise).where(
        Exercise.source == source,
        Exercise.is_verified == True,
        Exercise.embedding != None,
        Exercise.embedding != '',
        Exercise.difficulty >= min_difficulty,
        Exercise.difficulty <= max_difficulty,
    )

    # Exclude already completed
    if exclude_ids:
        query = query.where(~Exercise.id.in_(exclude_ids))

    # Filter by course if specified (through chapter relationship)
    # This would require a join with chapters table

    result = await db.execute(query.limit(500))  # Limit to avoid processing too many
    exercises = list(result.scalars().all())

    if not exercises:
        return []

    # Calculate similarity for each exercise
    recommendations = []
    for ex in exercises:
        if not ex.embedding:
            continue

        try:
            exercise_vector = json.loads(ex.embedding)
            similarity = cosine_similarity(user_vector, exercise_vector)

            recommendations.append({
                "exercise_id": ex.id,
                "source_id": ex.source_id,
                "similarity": round(similarity, 4),
                "difficulty": ex.difficulty,
                "type": ex.type,
                "knowledge_points": ex.knowledge_points or [],
                "title": ex.content.get("title", "") if ex.content else "",
            })
        except (json.JSONDecodeError, TypeError):
            continue

    # Sort by a combined score: similarity + difficulty preference
    # For new users (lower difficulty exercises), we boost their scores
    # This ensures entry-level exercises appear at the top for beginners
    def calculate_score(rec: dict, prefer_easy: bool = True) -> float:
        similarity = rec["similarity"]
        difficulty = rec["difficulty"]

        # Base score is similarity
        score = similarity

        # Difficulty adjustment
        # For new users: boost easier exercises, penalize hard ones
        if prefer_easy:
            # Lower difficulty = higher boost
            difficulty_bonus = (6 - difficulty) * 0.1  # +0.5 for diff 1, +0.1 for diff 5
            score += difficulty_bonus

        return score

    # Determine if this is a new user (should prefer easy exercises)
    # This is passed from the service level
    recommendations.sort(key=lambda x: calculate_score(x, prefer_easy=True), reverse=True)

    # Return top N
    return recommendations[:limit]


async def get_user_weak_points(db: AsyncSession, user_id: str) -> list[UserWeakPoint]:
    """
    Get user's weak points from database.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        List of UserWeakPoint objects
    """
    result = await db.execute(
        select(UserWeakPoint)
        .where(UserWeakPoint.user_id == user_id)
        .order_by(UserWeakPoint.error_count.desc())
        .limit(10)
    )
    return list(result.scalars().all())


class VectorMatchService:
    """Service class for vector-based exercise recommendation"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recommendations(
        self,
        user: User,
        limit: int = 10,
        exclude_ids: Optional[list[int]] = None,
        min_difficulty: int = 1,
        max_difficulty: int = 5,
    ) -> dict:
        """
        Get personalized exercise recommendations for a user.

        Returns a dict with:
        - user_vector_generated: bool
        - weak_points: list of weak point names
        - recommendations: list of recommended exercises
        """
        # Get user's weak points
        weak_points = await get_user_weak_points(self.db, user.id)

        # Determine if user is new (no learning history)
        is_new_user = len(weak_points) == 0 and (
            not hasattr(user, 'weak_points') or
            user.weak_points is None or
            len(user.weak_points) == 0
        )

        # For new users, default to easier exercises (difficulty 1-3)
        # But if no easier exercises exist in the database, use the full range
        if is_new_user:
            # Check if there are exercises with difficulty < 4
            from sqlalchemy import func
            result = await self.db.execute(
                select(func.count()).select_from(Exercise).where(
                    Exercise.source == "loj",
                    Exercise.difficulty < 4,
                    Exercise.embedding != None,
                    Exercise.embedding != '',
                )
            )
            easier_count = result.scalar() or 0

            if easier_count > 0:
                # Override difficulty range for new users
                actual_max_difficulty = min(max_difficulty, 3)  # Cap at "中等"
            else:
                # No easier exercises, use full range
                actual_max_difficulty = max_difficulty
            preferred_difficulty = 2  # 简单
        else:
            actual_max_difficulty = max_difficulty
            preferred_difficulty = user.preferred_difficulty if hasattr(user, 'preferred_difficulty') and user.preferred_difficulty else 3

        # Generate user vector with preferred difficulty
        user_vector = await generate_user_vector(
            user, weak_points, self.db, preferred_difficulty
        )

        # Get recommendations
        recommendations = await recommend_exercises(
            self.db,
            user_vector,
            limit=limit,
            exclude_ids=exclude_ids,
            min_difficulty=min_difficulty,
            max_difficulty=actual_max_difficulty,
        )

        # Check if user vector was generated from actual data
        has_weak_points = len(weak_points) > 0
        has_user_weak_points_attr = (
            hasattr(user, 'weak_points') and
            user.weak_points is not None and
            len(user.weak_points) > 0
        )
        user_vector_generated = has_weak_points or has_user_weak_points_attr

        return {
            "user_vector_generated": user_vector_generated,
            "weak_points": [wp.knowledge_point for wp in weak_points],
            "user_weak_point_count": len(weak_points),
            "recommendations": recommendations,
            "total_candidates": len(recommendations),
        }


# Singleton instance for convenience
def get_vector_match_service(db: AsyncSession) -> VectorMatchService:
    return VectorMatchService(db)

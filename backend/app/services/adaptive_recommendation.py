"""
Adaptive Exercise Recommendation Service

Implements a hybrid recommendation algorithm combining:
1. Knowledge Tracing - Track student knowledge state
2. Difficulty Matching - Zone of Proximal Development (ZPD)
3. Diversity - Ensure variety in recommendations
4. Spaced Repetition - Reinforce learning over time
5. Course Context - Align with current learning path

Based on research:
- Deep Knowledge Tracing (DKT)
- BKT-sequence algorithm
- RL-based exercise recommendation
- ExRec framework
"""

import json
import time
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.exercise import Exercise
from app.models.user import User
from app.models.user_weak_point import UserWeakPoint
from app.models.stats import ActivityLog
import logging


# Difficulty labels for display - 8级洛谷体系
# 1入门 2普及- 3普及/提高- 4普及+/提高 5提高+/省选- 6省选/NOI- 7NOI 8NOI+/CTSC
DIFFICULTY_LABELS = {
    1: "入门",
    2: "普及-",
    3: "普及/提高-",
    4: "普及+/提高",
    5: "提高+/省选-",
    6: "省选/NOI-",
    7: "NOI",
    8: "NOI+/CTSC",
}

# Scoring weights
WEIGHTS = {
    "difficulty_match": 0.35,      # ZPD difficulty alignment
    "weak_point_alignment": 0.25,  # Matches user's weak points
    "diversity": 0.20,             # New knowledge points
    "coverage": 0.10,              # Knowledge point richness
    "recency_penalty": 0.10,       # Penalize recently practiced
}


class AdaptiveRecommendationService:
    """
    Adaptive exercise recommendation service.

    Key principles:
    1. Zone of Proximal Development (ZPD) - recommend exercises slightly above current level
    2. Knowledge Tracing - estimate mastery level for each knowledge point
    3. Diversity - avoid recommending similar exercises
    4. Spaced Repetition - revisit concepts at optimal intervals
    5. Course Context - align with user's current course
    """

    # Simple in-memory TTL cache for knowledge state to avoid repeated DB queries
    # Key: "{user_id}:{chapter_id or 'none'}", Value: (knowledge_state_dict, timestamp)
    _knowledge_state_cache: dict[str, tuple[dict, float]] = {}
    _KNOWLEDGE_CACHE_TTL = 300  # 5 minutes

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recommendations(
        self,
        user: User,
        limit: int = 10,
        min_difficulty: int = 1,
        max_difficulty: int = 5,
        course_id: Optional[int] = None,
        chapter_id: Optional[int] = None,
        learning_path: str = "mastery",  # "mastery" or "challenge"
        exclude_ids: Optional[list[int]] = None,
    ) -> dict:
        """
        Get personalized exercise recommendations.

        Args:
            user: User object
            limit: Max recommendations to return
            min_difficulty: Minimum difficulty filter
            max_difficulty: Maximum difficulty filter
            course_id: Optional course context
            chapter_id: Optional chapter context for mastery path
            learning_path: "mastery" for chapter-based, "challenge" for difficulty-based
            exclude_ids: Exercise IDs to exclude

        Returns:
            dict with user stats and recommendations
        """
        # 1. Get user's knowledge state (with short-term caching)
        cache_key = f"{user.id}:{chapter_id or 'none'}"
        cached = self._knowledge_state_cache.get(cache_key)
        if cached and (time.time() - cached[1]) < self._KNOWLEDGE_CACHE_TTL:
            knowledge_state = cached[0]
        else:
            knowledge_state = await self._get_knowledge_state(user.id, chapter_id)
            self._knowledge_state_cache[cache_key] = (knowledge_state, time.time())

        # 2. Determine target difficulty (ZPD)
        target_difficulty = self._calculate_target_difficulty(knowledge_state, learning_path)

        # 3. Adjust difficulty range based on learning path
        if learning_path == "mastery":
            # 精进之路：渐进式难度，根据用户水平调整
            # 初学者限制在低难度，有经验后逐步放宽
            if knowledge_state["total_attempts"] < 5:
                # 新用户：严格限制在入门难度
                actual_min = max(min_difficulty, 1)
                actual_max = min(max_difficulty, 2)
            elif knowledge_state["total_attempts"] < 15:
                # 初学者：难度 1-2
                actual_min = max(min_difficulty, 1)
                actual_max = min(max_difficulty, 2)
            else:
                # 有基础：使用关卡难度范围
                actual_min = min_difficulty
                actual_max = max_difficulty
        else:
            # 挑战之路：根据用户经验限制难度范围
            if knowledge_state["total_attempts"] < 5:
                # 新用户：严格限制在入门难度
                actual_min = max(min_difficulty, 1)
                actual_max = min(max_difficulty, 1)
            elif knowledge_state["total_attempts"] < 15:
                # 初学者：难度 1-2
                actual_min = max(min_difficulty, 1)
                actual_max = min(max_difficulty, 2)
            else:
                # 有经验：使用传入的难度范围
                actual_min = min_difficulty
                actual_max = max_difficulty

        # 4. Get recently practiced exercises
        recently_practiced = await self._get_recently_practiced(user.id, days=7)

        # 5. Get candidate exercises
        candidates = await self._get_candidate_exercises(
            target_difficulty=target_difficulty,
            min_difficulty=actual_min,
            max_difficulty=actual_max,
            knowledge_state=knowledge_state,
            exclude_ids=exclude_ids or [],
            recently_practiced=recently_practiced,
            chapter_id=chapter_id,
            learning_path=learning_path,
        )

        # 5. Score and rank candidates
        scored_candidates = self._score_candidates(
            candidates=candidates,
            knowledge_state=knowledge_state,
            target_difficulty=target_difficulty,
            recently_practiced=recently_practiced,
        )

        # 6. Apply diversity filter
        diverse_recommendations = self._apply_diversity_filter(
            scored_candidates,
            limit=limit,
        )

        # 7. Generate recommendation reasons
        recommendations_with_reasons = self._add_recommendation_reasons(
            diverse_recommendations,
            knowledge_state,
            target_difficulty,
        )

        # 8. Format response
        return {
            "user_vector_generated": knowledge_state["has_history"],
            "weak_points": knowledge_state["weak_points"],
            "user_weak_point_count": len(knowledge_state["weak_points"]),
            "recommendations": recommendations_with_reasons,
            "total_candidates": len(candidates),
            "knowledge_state": {
                "estimated_level": round(knowledge_state["estimated_level"], 2),
                "target_difficulty": target_difficulty,
                "target_difficulty_label": DIFFICULTY_LABELS.get(target_difficulty, "未知"),
                "total_attempts": knowledge_state["total_attempts"],
                "accuracy": round(knowledge_state["accuracy"] * 100, 1),
            }
        }

    async def _get_knowledge_state(self, user_id: str, chapter_id: Optional[int] = None) -> dict:
        """
        Estimate user's current knowledge state.

        Uses:
        - Weak points from error history
        - Recent activity performance
        - Time since last practice
        """
        # Get weak points
        result = await self.db.execute(
            select(UserWeakPoint)
            .where(UserWeakPoint.user_id == user_id)
            .order_by(UserWeakPoint.error_count.desc())
            .limit(20)
        )
        weak_points = list(result.scalars().all())

        # Get recent exercise performance
        result = await self.db.execute(
            select(ActivityLog)
            .where(
                ActivityLog.user_id == user_id,
                ActivityLog.activity_type == "exercise_complete",
            )
            .order_by(ActivityLog.created_at.desc())
            .limit(100)
        )
        recent_activities = list(result.scalars().all())

        # Calculate mastery metrics
        total_attempts = len(recent_activities)
        correct_count = sum(
            1 for a in recent_activities
            if a.extra_data and a.extra_data.get("is_correct", False)
        )
        accuracy = correct_count / total_attempts if total_attempts > 0 else 0.5

        # Estimate user level (1-5 scale)
        if total_attempts < 3:
            # New users start at beginner level
            estimated_level = 1.5
        elif total_attempts < 10:
            # Still learning - use accuracy-weighted level
            estimated_level = 1.5 + accuracy * 1.0
        else:
            # Experienced - combine accuracy and difficulty history
            total_with_data = sum(1 for a in recent_activities[:50] if a.extra_data)
            if total_with_data > 0:
                avg_difficulty = sum(
                    a.extra_data.get("difficulty", 3)
                    for a in recent_activities[:50]
                    if a.extra_data
                ) / total_with_data
                # Ensure minimum difficulty of 1
                avg_difficulty = max(1, avg_difficulty)
            else:
                avg_difficulty = 2.5  # Default to mid-range

            # Weighted combination
            estimated_level = avg_difficulty * accuracy * 0.7 + 1.5 * 0.3
            # Cap at 8 for 8-level system, with floor of 1
            estimated_level = min(8, max(1, estimated_level))

        # Build weak point knowledge map
        weak_point_map = {}
        for wp in weak_points:
            weak_point_map[wp.knowledge_point] = {
                "error_count": wp.error_count,
                "mastery_level": wp.mastery_level,
                "priority": wp.error_count / max(wp.mastery_level, 1),
            }

        return {
            "weak_points": [wp.knowledge_point for wp in weak_points],
            "weak_point_objects": weak_points,
            "weak_point_map": weak_point_map,
            "total_attempts": total_attempts,
            "accuracy": accuracy,
            "estimated_level": estimated_level,
            "has_history": total_attempts > 0 or len(weak_points) > 0,
        }

    async def _get_recently_practiced(self, user_id: str, days: int = 7) -> dict:
        """Get recently practiced exercise IDs with timestamps."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(ActivityLog)
            .where(
                ActivityLog.user_id == user_id,
                ActivityLog.activity_type == "exercise_completed",
                ActivityLog.created_at >= cutoff,
            )
            .order_by(ActivityLog.created_at.desc())
        )
        activities = list(result.scalars().all())

        practiced = {}
        for a in activities:
            if a.extra_data and "exercise_id" in a.extra_data:
                eid = a.extra_data["exercise_id"]
                if eid not in practiced:
                    practiced[eid] = a.created_at

        return practiced

    def _calculate_target_difficulty(self, knowledge_state: dict, learning_path: str = "mastery") -> int:
        """
        Calculate target difficulty using Zone of Proximal Development.

        ZPD: Recommend exercises slightly above current ability
        - Too easy = boring, no learning
        - Too hard = frustrating, no learning
        - Just right = optimal learning

        Different strategies for different learning paths:
        - Mastery: Progressive difficulty within stage range (1-4 for beginners)
        - Challenge: Aggressive difficulty, push limits (up to 8)
        """
        estimated_level = knowledge_state["estimated_level"]
        accuracy = knowledge_state["accuracy"]

        if learning_path == "mastery":
            # 精进之路：渐进式难度策略
            # 新用户从入门开始，有基础后逐步提升
            if knowledge_state["total_attempts"] < 5:
                # 新用户：从最简单开始
                target = 1
            elif knowledge_state["total_attempts"] < 15:
                # 初学者：难度 1-2
                zpd_offset = 0.5 + accuracy * 0.5
                target = estimated_level + zpd_offset
                target = min(2, max(1, round(target)))
            elif knowledge_state["total_attempts"] < 30:
                # 有基础：难度 2-3
                zpd_offset = 0.5 + accuracy * 0.5
                target = estimated_level + zpd_offset
                target = min(3, max(1, round(target)))
            else:
                # 经验丰富：可达难度 4
                zpd_offset = 0.5 + accuracy * 0.5
                target = estimated_level + zpd_offset
                target = min(4, max(1, round(target)))
        else:
            # 挑战之路：根据用户经验调整策略
            if knowledge_state["total_attempts"] < 5:
                # 新用户：从最简单的题开始，建立信心
                target = 1
            elif knowledge_state["total_attempts"] < 15:
                # 初学者：难度 1-2
                zpd_offset = 0.3 + accuracy * 0.3
                target = estimated_level + zpd_offset
                target = min(2, max(1, round(target)))
            else:
                # 有经验后：激进策略，难度可以到 8
                zpd_offset = 0.5 + accuracy * 0.8
                target = estimated_level + zpd_offset + 0.5
                target = min(8, max(1, round(target)))

        return target

    async def _get_candidate_exercises(
        self,
        target_difficulty: int,
        min_difficulty: int,
        max_difficulty: int,
        knowledge_state: dict,
        exclude_ids: list[int],
        recently_practiced: dict,
        chapter_id: Optional[int] = None,
        learning_path: str = "mastery",
    ) -> list[dict]:
        """
        Get candidate exercises for recommendation.

        Args:
            target_difficulty: Target difficulty level
            min_difficulty: Minimum difficulty
            max_difficulty: Maximum difficulty
            knowledge_state: User's knowledge state
            exclude_ids: IDs to exclude
            recently_practiced: Recently practiced exercise IDs
            chapter_id: Optional chapter filter for mastery path
            learning_path: "mastery" or "challenge"
        """
        weak_point_objects = knowledge_state.get("weak_point_objects", [])
        weak_point_kps = [wp.knowledge_point for wp in weak_point_objects]

        # Build base query with random ordering for variety
        query = select(Exercise).where(
            Exercise.is_verified,
            Exercise.difficulty >= min_difficulty,
            Exercise.difficulty <= max_difficulty,
        )

        # Chapter filter for mastery path
        if chapter_id:
            query = query.where(Exercise.chapter_id == chapter_id)

        # Exclude specific IDs
        if exclude_ids:
            query = query.where(~Exercise.id.in_(exclude_ids))

        # Random ordering + limit: we only need a small pool for scoring.
        # 100 candidates is plenty when we only return ~5-10 recommendations.
        query = query.order_by(func.random()).limit(100)
        result = await self.db.execute(query)
        exercises = list(result.scalars().all())

        candidates = []
        for ex in exercises:
            # Parse knowledge points
            kp_list = ex.knowledge_points or []
            if isinstance(kp_list, str):
                try:
                    kp_list = json.loads(kp_list)
                except Exception:
                    kp_list = []

            # Check if matches weak points
            matches_weak_point = any(
                any(wp.lower() in kp.lower() for kp in kp_list)
                for wp in weak_point_kps
            ) if weak_point_kps else False

            # Check if recently practiced
            last_practiced = recently_practiced.get(ex.id)
            days_since_practice = None
            if last_practiced:
                days_since_practice = (datetime.utcnow() - last_practiced).days

            candidates.append({
                "exercise_id": ex.id,
                "source_id": ex.source_id,
                "difficulty": ex.difficulty,
                "type": ex.type,
                "knowledge_points": kp_list,
                "title": ex.content.get("title", "") if ex.content else "",
                # NOTE: embedding is not used by _score_candidates, so we skip
                # the json.loads overhead here. Add it back if scoring uses it.
                "matches_weak_point": matches_weak_point,
                "matched_weak_points": [
                    wp for wp in weak_point_kps
                    if any(wp.lower() in kp.lower() for kp in kp_list)
                ] if weak_point_kps else [],
                "last_practiced_days": days_since_practice,
            })

        return candidates

    def _score_candidates(
        self,
        candidates: list[dict],
        knowledge_state: dict,
        target_difficulty: int,
        recently_practiced: dict,
    ) -> list[dict]:
        """
        Score each candidate exercise using weighted factors.
        """
        scored = []
        seen_kps = set()
        seen_source_ids = set()

        for candidate in candidates:
            # Skip duplicate source_ids (same problem)
            source_id = candidate["source_id"]
            if source_id in seen_source_ids:
                continue

            scores = {}

            # 1. Difficulty match (ZPD scoring)
            diff = candidate["difficulty"]
            diff_distance = abs(diff - target_difficulty)

            if diff_distance == 0:
                scores["difficulty"] = 1.0
            elif diff_distance == 1:
                scores["difficulty"] = 0.75
            elif diff_distance == 2:
                scores["difficulty"] = 0.5
            else:
                scores["difficulty"] = max(0.1, 0.3 - diff_distance * 0.05)

            # 2. Weak point alignment
            if candidate["matches_weak_point"]:
                # Bonus for matching weak points
                matched_count = len(candidate["matched_weak_points"])
                scores["weak_point"] = min(1.0, 0.5 + matched_count * 0.25)
            else:
                scores["weak_point"] = 0.3

            # 3. Diversity bonus (new knowledge points)
            new_kps = set(candidate["knowledge_points"]) - seen_kps
            total_kps = len(candidate["knowledge_points"])
            scores["diversity"] = len(new_kps) / max(total_kps, 1) if total_kps > 0 else 0.5

            # 4. Knowledge point coverage
            scores["coverage"] = min(total_kps / 5, 1.0)

            # 5. Recency penalty (avoid recently practiced)
            days_since = candidate.get("last_practiced_days")
            if days_since is not None:
                if days_since < 3:
                    scores["recency"] = 0.1  # Very recent - strong penalty
                elif days_since < 7:
                    scores["recency"] = 0.4  # Recent - moderate penalty
                else:
                    scores["recency"] = 0.8  # Old - slight penalty
            else:
                scores["recency"] = 1.0  # Never practiced - bonus

            # Calculate weighted total score
            total_score = sum(
                scores.get(key, 0) * weight
                for key, weight in WEIGHTS.items()
            )

            candidate["score"] = round(total_score, 4)
            candidate["similarity"] = round(total_score, 4)
            candidate["score_breakdown"] = scores

            scored.append(candidate)
            seen_source_ids.add(source_id)
            seen_kps.update(candidate["knowledge_points"])

        # Sort by score descending
        scored.sort(key=lambda x: x["score"], reverse=True)

        return scored

    def _apply_diversity_filter(
        self,
        candidates: list[dict],
        limit: int,
    ) -> list[dict]:
        """
        Ensure diversity in final recommendations.
        """
        if len(candidates) <= limit:
            return candidates[:limit]

        selected = []
        difficulty_counts = {i: 0 for i in range(1, 9)}  # 8 级难度
        type_counts = {}

        # Max 40% from any difficulty level
        max_per_difficulty = max(1, int(limit * 0.4))
        # Max 70% from any type
        max_per_type = max(1, int(limit * 0.7))

        for candidate in candidates:
            if len(selected) >= limit:
                break

            diff = candidate["difficulty"]
            ex_type = candidate["type"]

            # Check difficulty limit
            if difficulty_counts.get(diff, 0) >= max_per_difficulty:
                continue

            # Check type limit
            if type_counts.get(ex_type, 0) >= max_per_type:
                continue

            # Add to selected
            selected.append({
                "exercise_id": candidate["exercise_id"],
                "source_id": candidate["source_id"],
                "similarity": candidate["similarity"],
                "difficulty": candidate["difficulty"],
                "type": candidate["type"],
                "knowledge_points": candidate["knowledge_points"],
                "title": candidate["title"],
                "matched_weak_points": candidate.get("matched_weak_points", []),
                "score_breakdown": candidate.get("score_breakdown", {}),
            })

            # Update counts
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
            type_counts[ex_type] = type_counts.get(ex_type, 0) + 1

        return selected

    def _add_recommendation_reasons(
        self,
        recommendations: list[dict],
        knowledge_state: dict,
        target_difficulty: int,
    ) -> list[dict]:
        """
        Add human-readable reasons for each recommendation.
        """
        DIFFICULTY_LABELS.get(target_difficulty, "中等")

        for rec in recommendations:
            reasons = []

            # Difficulty reason
            diff = rec["difficulty"]
            diff_label = DIFFICULTY_LABELS.get(diff, "未知")
            if diff == target_difficulty:
                reasons.append(f"难度适中（{diff_label}），符合你当前水平")
            elif diff < target_difficulty:
                reasons.append(f"基础巩固（{diff_label}），打牢基本功")
            else:
                reasons.append(f"挑战提升（{diff_label}），突破舒适区")

            # Weak point reason
            if rec.get("matched_weak_points"):
                kps = rec["matched_weak_points"][:2]
                reasons.append(f"针对薄弱点：{', '.join(kps)}")

            # Knowledge point reason
            if rec.get("knowledge_points"):
                kps = rec["knowledge_points"][:3]
                reasons.append(f"知识点：{', '.join(kps)}")

            rec["reason"] = "；".join(reasons[:3])

            # Add difficulty label
            rec["difficulty_label"] = DIFFICULTY_LABELS.get(rec["difficulty"], "未知")

        return recommendations


def get_adaptive_recommendation_service(db: AsyncSession) -> AdaptiveRecommendationService:
    """Factory function to create service instance."""
    return AdaptiveRecommendationService(db)


logger = logging.getLogger(__name__)
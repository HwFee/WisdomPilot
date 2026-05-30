"""
Chapter Mastery Service

Implements mastery level calculation based on:
1. Weighted Accuracy - correct rate weighted by difficulty
2. Consistency - stable performance across attempts
3. Depth - learning objective coverage
4. Recency - recent practice reinforcement

Based on research:
- Khan Academy mastery model
- N-CCR (N-Consecutive Correct in a Row)
- Deep Knowledge Tracing concepts
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

import logging


# Mastery level thresholds
MASTERY_LEVELS = {
    "入门": (0, 30),
    "学习": (31, 50),
    "练习": (51, 70),
    "熟练": (71, 85),
    "精通": (86, 100),
}

# Threshold to advance to next chapter
ADVANCE_THRESHOLD = 75.0


class ChapterMasteryService:
    """
    Service for calculating and managing chapter mastery.
    """

    def __init__(self, db: Optional[AsyncSession]):
        self.db = db

    def get_mastery_level(self, score: float) -> str:
        """
        Convert mastery score to level name.

        Args:
            score: 0-100 mastery score

        Returns:
            Level name: 入门, 学习, 练习, 熟练, 精通
        """
        for level, (low, high) in MASTERY_LEVELS.items():
            if low <= score <= high:
                return level
        return "入门"

    def can_advance(self, score: float) -> bool:
        """
        Check if user can advance to next chapter.

        Args:
            score: Mastery score

        Returns:
            True if score >= advance threshold
        """
        return score >= ADVANCE_THRESHOLD

    def calculate_weighted_accuracy(self, exercises: list[dict]) -> float:
        """
        Calculate accuracy weighted by difficulty.

        Higher difficulty exercises count more towards the score.
        This follows IRT (Item Response Theory) principles.

        Args:
            exercises: List of {"difficulty": int, "is_correct": bool}

        Returns:
            Weighted accuracy score (0-100)
        """
        if not exercises:
            return 0.0

        weighted_correct = sum(
            ex.get("difficulty", 1) * (1 if ex.get("is_correct", False) else 0)
            for ex in exercises
        )
        weighted_total = sum(ex.get("difficulty", 1) for ex in exercises)

        if weighted_total == 0:
            return 0.0

        return (weighted_correct / weighted_total) * 100

    def calculate_consistency(self, exercises: list[dict]) -> float:
        """
        Calculate consistency score based on rolling window variance.

        Low variance = high consistency.

        Args:
            exercises: List of {"is_correct": bool}

        Returns:
            Consistency score (0-100)
        """
        if len(exercises) < 3:
            return 50.0  # Not enough data, return middle

        window_size = min(5, len(exercises))
        accuracies = []

        for i in range(len(exercises) - window_size + 1):
            window = exercises[i:i + window_size]
            correct = sum(1 for ex in window if ex.get("is_correct", False))
            accuracies.append(correct / window_size)

        if not accuracies:
            return 50.0

        # Calculate variance
        mean_acc = sum(accuracies) / len(accuracies)
        variance = sum((a - mean_acc) ** 2 for a in accuracies) / len(accuracies)

        # Low variance = high consistency
        # Variance 0 = 100 score, Variance 0.25 = 0 score
        consistency = max(0, min(100, (1 - variance * 4) * 100))

        return consistency

    def calculate_depth_score(
        self,
        objectives: list[str],
        covered_objectives: set[str]
    ) -> float:
        """
        Calculate depth score based on learning objective coverage.

        Args:
            objectives: List of all learning objectives
            covered_objectives: Set of covered objectives

        Returns:
            Coverage score (0-100)
        """
        if not objectives:
            return 100.0  # No objectives defined = full coverage

        coverage = len(covered_objectives) / len(objectives)
        return coverage * 100

    def calculate_recency_score(
        self,
        last_practiced_at: Optional[datetime]
    ) -> float:
        """
        Calculate recency score based on time since last practice.

        More recent = higher score.

        Args:
            last_practiced_at: When user last practiced this chapter

        Returns:
            Recency score (0-100)
        """
        if last_practiced_at is None:
            return 50.0  # Never practiced

        days_since = (datetime.utcnow() - last_practiced_at).days

        # 0 days = 100, 7 days = 50, 14+ days = 0
        if days_since <= 0:
            return 100.0
        elif days_since >= 14:
            return 0.0
        else:
            return max(0, 100 - days_since * 7)

    def calculate_mastery_score(
        self,
        exercises: list[dict],
        objectives: list[str] = None,
        covered_objectives: set[str] = None,
        last_practiced_at: Optional[datetime] = None,
    ) -> dict:
        """
        Calculate overall mastery score with component breakdown.

        Formula:
        mastery_score = 0.35 * accuracy + 0.25 * consistency +
                        0.20 * depth + 0.15 * recency

        Args:
            exercises: List of exercise records
            objectives: Learning objectives for the chapter
            covered_objectives: Objectives covered by exercises
            last_practiced_at: Last practice timestamp

        Returns:
            Dict with total score and component scores
        """
        # Calculate components
        accuracy = self.calculate_weighted_accuracy(exercises)
        consistency = self.calculate_consistency(exercises)
        depth = self.calculate_depth_score(
            objectives or [],
            covered_objectives or set()
        )
        recency = self.calculate_recency_score(last_practiced_at)

        # Weighted total
        total = (
            0.35 * accuracy +
            0.25 * consistency +
            0.20 * depth +
            0.20 * recency
        )

        return {
            "total": round(total, 2),
            "accuracy": round(accuracy, 2),
            "consistency": round(consistency, 2),
            "depth": round(depth, 2),
            "recency": round(recency, 2),
            "level": self.get_mastery_level(total),
            "can_advance": self.can_advance(total),
        }

    def check_n_ccr(self, exercises: list[dict], n: int = 3) -> bool:
        """
        Check N-Consecutive Correct in a Row.

        If user got N exercises correct in a row, they likely mastered it.
        This is used by ASSISTments and similar systems.

        Args:
            exercises: List sorted by time (newest first)
            n: Number of consecutive correct required

        Returns:
            True if N consecutive correct found
        """
        if len(exercises) < n:
            return False

        recent = exercises[:n]
        return all(ex.get("is_correct", False) for ex in recent)


def get_chapter_mastery_service(db: AsyncSession) -> ChapterMasteryService:
    """Factory function for the service."""
    return ChapterMasteryService(db)


logger = logging.getLogger(__name__)
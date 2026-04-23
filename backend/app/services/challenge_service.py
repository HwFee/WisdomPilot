"""
Challenge Service

Implements challenge session management and scoring for the Challenge Path (竞技之路).
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.challenge_session import ChallengeSession
import logging


# Score multipliers by difficulty
DIFFICULTY_MULTIPLIERS = {
    1: 1.0,
    2: 1.2,
    3: 1.5,
    4: 2.0,
    5: 3.0,
}

# Time limits per question (in seconds)
TIME_PER_QUESTION = {
    1: 60,
    2: 90,
    3: 120,
    4: 180,
    5: 300,
}


class ChallengeService:
    """
    Service for managing challenge sessions and scoring.
    """

    def __init__(self, db: Optional[AsyncSession]):
        self.db = db

    def calculate_base_score(self, correct: int, total: int, difficulty: int) -> float:
        """
        Calculate base score from correct answers.

        Formula: (correct/total * 100) * (1 + difficulty_bonus)
        Where difficulty_bonus = (difficulty - 1) * 0.1

        Args:
            correct: Number of correct answers
            total: Total number of questions
            difficulty: Difficulty level (1-5)

        Returns:
            Base score
        """
        if total == 0:
            return 0.0

        accuracy = correct / total
        difficulty_bonus = (difficulty - 1) * 0.1
        base = accuracy * 100

        return round(base * (1 + difficulty_bonus), 2)

    def calculate_time_bonus(self, time_spent: int, time_limit: int) -> float:
        """
        Calculate time bonus for fast completion.

        Faster completion = higher bonus.
        Max bonus: 10% of base score

        Args:
            time_spent: Actual time spent in seconds
            time_limit: Total time allowed in seconds

        Returns:
            Bonus percentage (0-10)
        """
        if time_limit == 0:
            return 0.0

        # Percentage of time used
        time_ratio = time_spent / time_limit

        # Bonus: inverse relationship with time used
        # time_ratio 0.0 = 10% bonus, time_ratio 1.0 = 0% bonus
        bonus = max(0, (1 - time_ratio) * 10)

        return round(bonus, 2)

    def calculate_streak_bonus(self, streak: int) -> float:
        """
        Calculate streak bonus for consecutive correct answers.

        Each consecutive correct adds 1% bonus.
        Max bonus: 5% (for 5+ streak)

        Args:
            streak: Number of consecutive correct answers

        Returns:
            Bonus percentage (0-5)
        """
        return min(streak, 5)

    def get_score_multiplier(self, difficulty: int) -> float:
        """
        Get score multiplier for difficulty level.

        Args:
            difficulty: Difficulty level (1-5)

        Returns:
            Multiplier value
        """
        return DIFFICULTY_MULTIPLIERS.get(difficulty, 1.0)

    def get_time_limit(self, difficulty: int, question_count: int) -> int:
        """
        Calculate time limit based on difficulty and question count.

        Args:
            difficulty: Difficulty level (1-5)
            question_count: Number of questions

        Returns:
            Time limit in seconds
        """
        time_per_question = TIME_PER_QUESTION.get(difficulty, 120)
        return time_per_question * question_count

    async def create_session(
        self,
        user_id: str,
        course_id: int,
        difficulty: int,
        exercise_ids: list[str],
    ) -> ChallengeSession:
        """
        Create a new challenge session.

        Args:
            user_id: User ID
            course_id: Course ID
            difficulty: Difficulty level (1-5)
            exercise_ids: List of exercise IDs for this challenge

        Returns:
            Created ChallengeSession
        """
        session = ChallengeSession(
            user_id=user_id,
            course_id=course_id,
            difficulty_level=difficulty,
            exercise_ids=exercise_ids,
            time_limit=self.get_time_limit(difficulty, len(exercise_ids)),
            score_multiplier=self.get_score_multiplier(difficulty),
            total_questions=len(exercise_ids),
        )

        if self.db:
            self.db.add(session)
            await self.db.commit()
            await self.db.refresh(session)

        return session

    async def complete_session(
        self,
        session_id: str,
        correct_answers: int,
        time_spent: int,
        max_streak: int,
    ) -> ChallengeSession:
        """
        Complete a challenge session and calculate final score.

        Args:
            session_id: Session ID
            correct_answers: Number of correct answers
            time_spent: Time spent in seconds
            max_streak: Maximum consecutive correct answers

        Returns:
            Updated ChallengeSession
        """
        if not self.db:
            raise ValueError("Database session required")

        result = await self.db.execute(
            select(ChallengeSession).where(ChallengeSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Calculate scores
        base_score = self.calculate_base_score(
            correct_answers,
            session.total_questions,
            session.difficulty_level
        )
        time_bonus = self.calculate_time_bonus(time_spent, session.time_limit)
        streak_bonus = self.calculate_streak_bonus(max_streak)

        # Total before multiplier
        pre_multiplier = base_score * (1 + (time_bonus + streak_bonus) / 100)

        # Apply multiplier
        final_score = pre_multiplier * session.score_multiplier

        # Update session
        session.correct_answers = correct_answers
        session.time_spent = time_spent
        session.max_streak = max_streak
        session.base_score = round(base_score, 2)
        session.time_bonus = round(time_bonus, 2)
        session.streak_bonus = round(streak_bonus, 2)
        session.final_score = round(final_score, 2)
        session.status = "completed"
        session.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(session)

        return session


def get_challenge_service(db: AsyncSession) -> ChallengeService:
    """Factory function for the service."""
    return ChallengeService(db)


logger = logging.getLogger(__name__)
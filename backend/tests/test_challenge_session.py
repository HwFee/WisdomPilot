"""
Tests for Challenge Session model and service

Following TDD: Write tests first, then implement
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.challenge_session import ChallengeSession
from app.models.user import User
from app.models.course import Course


class TestChallengeSessionModel:
    """Test ChallengeSession model CRUD operations"""

    @pytest.mark.asyncio
    async def test_create_challenge_session(self, db_session: AsyncSession, test_user: User, test_course: Course):
        """Test creating a new challenge session"""
        session = ChallengeSession(
            user_id=test_user.id,
            course_id=test_course.id,
            difficulty_level=3,
            exercise_ids=["ex1", "ex2", "ex3"],
            time_limit=300,
            score_multiplier=1.5,
        )
        db_session.add(session)
        await db_session.commit()

        # Verify it was saved
        result = await db_session.execute(
            select(ChallengeSession).where(
                ChallengeSession.user_id == test_user.id,
                ChallengeSession.course_id == test_course.id,
            )
        )
        saved = result.scalar_one_or_none()

        assert saved is not None
        assert saved.difficulty_level == 3
        assert len(saved.exercise_ids) == 3
        assert saved.status == "pending"
        assert saved.score_multiplier == 1.5

    @pytest.mark.asyncio
    async def test_challenge_session_lifecycle(self, db_session: AsyncSession, test_user: User, test_course: Course):
        """Test challenge session status transitions"""
        session = ChallengeSession(
            user_id=test_user.id,
            course_id=test_course.id,
            difficulty_level=2,
            exercise_ids=["ex1", "ex2"],
            time_limit=180,
        )
        db_session.add(session)
        await db_session.commit()

        # Start the session
        session.status = "in_progress"
        session.started_at = datetime.utcnow()
        await db_session.commit()

        # Complete the session
        session.status = "completed"
        session.correct_answers = 2
        session.total_questions = 2
        session.base_score = 100.0
        session.final_score = 120.0  # with multiplier
        session.completed_at = datetime.utcnow()
        await db_session.commit()

        # Verify
        result = await db_session.execute(
            select(ChallengeSession).where(ChallengeSession.id == session.id)
        )
        updated = result.scalar_one()

        assert updated.status == "completed"
        assert updated.correct_answers == 2
        assert updated.final_score == 120.0


class TestChallengeScoring:
    """Test challenge score calculation"""

    def test_base_score_calculation(self):
        """Test base score from correct answers"""
        from app.services.challenge_service import ChallengeService

        service = ChallengeService(None)

        # 8 correct out of 10, difficulty 3
        score = service.calculate_base_score(correct=8, total=10, difficulty=3)
        # Base: 80% * 100 = 80, difficulty bonus: (3-1) * 0.1 = 0.2
        # Total: 80 * (1 + 0.2) = 96
        assert score == 96.0

    def test_time_bonus_calculation(self):
        """Test time bonus for fast completion"""
        from app.services.challenge_service import ChallengeService

        service = ChallengeService(None)

        # Completed in half the time
        bonus = service.calculate_time_bonus(time_spent=150, time_limit=300)
        # Used 50% of time, so bonus is (1 - 0.5) * 10 = 5
        assert bonus == 5.0

        # Completed very fast
        bonus = service.calculate_time_bonus(time_spent=60, time_limit=300)
        # Used 20% of time, bonus is (1 - 0.2) * 10 = 8
        assert bonus == 8.0

        # No time left - no bonus
        bonus = service.calculate_time_bonus(time_spent=300, time_limit=300)
        assert bonus == 0.0

    def test_streak_bonus(self):
        """Test streak bonus for consecutive correct"""
        from app.services.challenge_service import ChallengeService

        service = ChallengeService(None)

        # No streak
        bonus = service.calculate_streak_bonus(streak=0)
        assert bonus == 0.0

        # 3 streak
        bonus = service.calculate_streak_bonus(streak=3)
        assert bonus == 3.0

        # 5 streak (max bonus)
        bonus = service.calculate_streak_bonus(streak=5)
        assert bonus == 5.0


# Additional fixtures for this test module
@pytest.fixture
async def test_course(db_session: AsyncSession):
    """Create test course"""
    course = Course(
        code="TEST_CHALLENGE_C",
        name="Test C Course for Challenge",
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course

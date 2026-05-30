"""
Tests for Chapter Mastery model and service

Following TDD: Write tests first, then implement
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chapter_mastery import ChapterMastery
from app.models.user import User
from app.models.chapter import Chapter
from app.models.course import Course


class TestChapterMasteryModel:
    """Test ChapterMastery model CRUD operations"""

    @pytest.mark.asyncio
    async def test_create_chapter_mastery(self, db_session: AsyncSession, test_user: User, test_course: Course, test_chapter: Chapter):
        """Test creating a new chapter mastery record"""
        mastery = ChapterMastery(
            user_id=test_user.id,
            chapter_id=test_chapter.id,
            course_id=test_chapter.course_id,
            mastery_score=45.5,
            mastery_level="学习",
        )
        db_session.add(mastery)
        await db_session.commit()

        # Verify it was saved
        result = await db_session.execute(
            select(ChapterMastery).where(
                ChapterMastery.user_id == test_user.id,
                ChapterMastery.chapter_id == test_chapter.id,
            )
        )
        saved = result.scalar_one_or_none()

        assert saved is not None
        assert saved.mastery_score == 45.5
        assert saved.mastery_level == "学习"
        assert saved.id is not None

    @pytest.mark.asyncio
    async def test_unique_user_chapter_constraint(self, db_session: AsyncSession, test_user: User, test_course: Course, test_chapter: Chapter):
        """Test that user can only have one mastery record per chapter"""
        mastery1 = ChapterMastery(
            user_id=test_user.id,
            chapter_id=test_chapter.id,
            course_id=test_chapter.course_id,
        )
        db_session.add(mastery1)
        await db_session.commit()

        # Try to create duplicate - should fail
        mastery2 = ChapterMastery(
            user_id=test_user.id,
            chapter_id=test_chapter.id,
            course_id=test_chapter.course_id,
        )
        db_session.add(mastery2)

        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_update_mastery_score(self, db_session: AsyncSession, test_user: User, test_course: Course, test_chapter: Chapter):
        """Test updating mastery score"""
        mastery = ChapterMastery(
            user_id=test_user.id,
            chapter_id=test_chapter.id,
            course_id=test_chapter.course_id,
            mastery_score=30.0,
        )
        db_session.add(mastery)
        await db_session.commit()

        # Update score
        mastery.mastery_score = 75.0
        mastery.mastery_level = "熟练"
        await db_session.commit()

        # Verify update
        result = await db_session.execute(
            select(ChapterMastery).where(ChapterMastery.id == mastery.id)
        )
        updated = result.scalar_one()

        assert updated.mastery_score == 75.0
        assert updated.mastery_level == "熟练"


class TestChapterMasteryLevel:
    """Test mastery level calculation"""

    def test_get_mastery_level_for_score(self):
        """Test converting score to mastery level"""
        from app.services.chapter_mastery import ChapterMasteryService

        service = ChapterMasteryService(None)

        assert service.get_mastery_level(0) == "入门"
        assert service.get_mastery_level(25) == "入门"
        assert service.get_mastery_level(35) == "学习"
        assert service.get_mastery_level(50) == "学习"
        assert service.get_mastery_level(60) == "练习"
        assert service.get_mastery_level(75) == "熟练"
        assert service.get_mastery_level(90) == "精通"
        assert service.get_mastery_level(100) == "精通"

    def test_can_advance_to_next_chapter(self):
        """Test threshold for advancing to next chapter"""
        from app.services.chapter_mastery import ChapterMasteryService

        service = ChapterMasteryService(None)

        # Need 75% to advance
        assert service.can_advance(74.9) is False
        assert service.can_advance(75.0) is True
        assert service.can_advance(85.0) is True


class TestChapterMasteryScoring:
    """Test mastery score calculation"""

    def test_weighted_accuracy_calculation(self):
        """Test weighted accuracy with difficulty"""
        from app.services.chapter_mastery import ChapterMasteryService

        service = ChapterMasteryService(None)

        # Simple case: all difficulty 1, all correct
        exercises = [
            {"difficulty": 1, "is_correct": True},
            {"difficulty": 1, "is_correct": True},
            {"difficulty": 1, "is_correct": True},
        ]
        score = service.calculate_weighted_accuracy(exercises)
        assert score == 100.0

        # Mixed difficulty, partial correct
        exercises = [
            {"difficulty": 1, "is_correct": True},   # 1 correct
            {"difficulty": 2, "is_correct": False},  # 2 incorrect
            {"difficulty": 3, "is_correct": True},   # 3 correct
        ]
        score = service.calculate_weighted_accuracy(exercises)
        # Weighted correct: 1 + 3 = 4
        # Weighted total: 1 + 2 + 3 = 6
        # Score: 4/6 * 100 = 66.67
        assert abs(score - 66.67) < 0.1

    def test_consistency_score_calculation(self):
        """Test consistency based on rolling variance"""
        from app.services.chapter_mastery import ChapterMasteryService

        service = ChapterMasteryService(None)

        # Perfect consistency - all correct (need more than window_size to calculate variance)
        exercises = [
            {"is_correct": True},
            {"is_correct": True},
            {"is_correct": True},
            {"is_correct": True},
            {"is_correct": True},
            {"is_correct": True},
            {"is_correct": True},
        ]
        score = service.calculate_consistency(exercises)
        assert score == 100.0  # Perfect consistency

        # Inconsistent - alternating
        exercises = [
            {"is_correct": True},
            {"is_correct": False},
            {"is_correct": True},
            {"is_correct": False},
            {"is_correct": True},
            {"is_correct": False},
            {"is_correct": True},
        ]
        score = service.calculate_consistency(exercises)
        assert score < 100  # Lower consistency

    def test_empty_exercises_returns_zero(self):
        """Test edge case: no exercises"""
        from app.services.chapter_mastery import ChapterMasteryService

        service = ChapterMasteryService(None)

        assert service.calculate_weighted_accuracy([]) == 0.0
        assert service.calculate_consistency([]) == 50.0  # Default middle


# Additional fixtures for this test module
@pytest.fixture
async def test_course(db_session: AsyncSession):
    """Create test course"""
    course = Course(
        code="TEST_MASTERY_C",
        name="Test C Course for Mastery",
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


@pytest.fixture
async def test_chapter(db_session: AsyncSession, test_course: Course):
    """Create test chapter"""
    chapter = Chapter(
        course_id=test_course.id,
        order_index=1,
        title="Test Chapter for Mastery",
        learning_objectives=["objective1", "objective2"],
    )
    db_session.add(chapter)
    await db_session.commit()
    await db_session.refresh(chapter)
    return chapter

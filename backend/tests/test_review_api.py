"""Tests for Review API endpoints"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.models import User, Course, Exercise, Chapter, UserWeakPoint, SpacedRepetition
from app.utils.time import utc_now


@pytest.fixture
async def test_chapter(db_session: AsyncSession) -> Chapter:
    """Create a test chapter"""
    course = Course(code="REVIEW_TEST", name="复习测试课程", is_active=True)
    db_session.add(course)
    await db_session.flush()

    chapter = Chapter(
        course_id=course.id,
        title="测试章节",
        order_index=1,
        is_active=True
    )
    db_session.add(chapter)
    await db_session.flush()
    return chapter


@pytest.fixture
async def test_exercises(db_session: AsyncSession, test_chapter: Chapter) -> list[Exercise]:
    """Create test exercises"""
    exercises = []
    for i in range(5):
        exercise = Exercise(
            chapter_id=test_chapter.id,
            type="choice",
            difficulty=i + 1,
            content={"text": f"题目 {i+1}", "options": ["A", "B", "C", "D"]},
            knowledge_points=[f"知识点{i+1}", "通用"],
            source="manual"
        )
        db_session.add(exercise)
        exercises.append(exercise)
    await db_session.flush()
    return exercises


@pytest.fixture
async def test_repetitions(
    db_session: AsyncSession, test_user: User, test_exercises: list[Exercise]
) -> list[SpacedRepetition]:
    """Create test spaced repetition records"""
    repetitions = []
    now = utc_now()

    # Create some due and some future repetitions
    for i, ex in enumerate(test_exercises):
        # First 3 are due, last 2 are scheduled for future
        next_review = now - timedelta(days=i) if i < 3 else now + timedelta(days=i)
        rep = SpacedRepetition(
            user_id=test_user.id,
            exercise_id=ex.id,
            next_review_at=next_review,
            review_interval=1,
            ease_factor=2.5,
            review_count=i
        )
        db_session.add(rep)
        repetitions.append(rep)
    await db_session.flush()
    return repetitions


@pytest.fixture
async def test_weak_points(
    db_session: AsyncSession, test_user: User, test_chapter: Chapter
) -> list[UserWeakPoint]:
    """Create test weak points"""
    weak_points = []
    knowledge_points = ["数组", "链表", "递归"]

    for i, kp in enumerate(knowledge_points):
        wp = UserWeakPoint(
            user_id=test_user.id,
            course_id=test_chapter.course_id,
            knowledge_point=kp,
            error_count=5 - i,
            mastery_level=i + 1
        )
        db_session.add(wp)
        weak_points.append(wp)
    await db_session.flush()
    return weak_points


class TestReviewQueue:
    """Tests for GET /api/review/queue"""

    @pytest.mark.asyncio
    async def test_get_review_queue(
        self, client: AsyncClient, auth_headers: dict, test_repetitions: list[SpacedRepetition]
    ):
        """Test getting review queue"""
        response = await client.get(
            "/api/review/queue",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total_due" in data
        assert "total_scheduled" in data

    @pytest.mark.asyncio
    async def test_review_queue_limit(
        self, client: AsyncClient, auth_headers: dict, test_repetitions: list[SpacedRepetition]
    ):
        """Test review queue limit parameter"""
        response = await client.get(
            "/api/review/queue?limit=2",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2


class TestCompleteReview:
    """Tests for POST /api/review/complete/{exercise_id}"""

    @pytest.mark.asyncio
    async def test_complete_review_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test completing review for non-existent exercise"""
        response = await client.post(
            "/api/review/complete/99999",
            headers=auth_headers,
            json={"exercise_id": 99999, "quality": 4, "success": True}
        )
        assert response.status_code == 404


class TestWeakPoints:
    """Tests for GET /api/review/weak-points"""

    @pytest.mark.asyncio
    async def test_get_weak_points_empty(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting weak points list for user with no weak points"""
        response = await client.get(
            "/api/review/weak-points",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "weak_points" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_weak_points_sorted_by_mastery(
        self, client: AsyncClient, auth_headers: dict, test_weak_points: list[UserWeakPoint]
    ):
        """Test that weak points are sorted by mastery level"""
        response = await client.get(
            "/api/review/weak-points",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        weak_points = data["weak_points"]

        # Should be sorted by mastery level (ascending)
        if len(weak_points) > 1:
            for i in range(len(weak_points) - 1):
                assert weak_points[i]["mastery_level"] <= weak_points[i + 1]["mastery_level"]


class TestTargetPractice:
    """Tests for POST /api/review/weak-points/target"""

    @pytest.mark.asyncio
    async def test_target_practice(
        self, client: AsyncClient, auth_headers: dict, test_weak_points: list[UserWeakPoint], test_exercises: list[Exercise]
    ):
        """Test getting targeted practice exercises"""
        response = await client.post(
            "/api/review/weak-points/target",
            headers=auth_headers,
            json={"limit": 3}
        )
        assert response.status_code == 200
        data = response.json()
        assert "exercises" in data
        assert "weak_points" in data

    @pytest.mark.asyncio
    async def test_target_practice_with_course_filter(
        self, client: AsyncClient, auth_headers: dict, test_weak_points: list[UserWeakPoint]
    ):
        """Test targeted practice with course filter"""
        course_id = test_weak_points[0].course_id

        response = await client.post(
            "/api/review/weak-points/target",
            headers=auth_headers,
            json={"course_id": course_id, "limit": 5}
        )
        assert response.status_code == 200


class TestReviewStats:
    """Tests for GET /api/review/stats"""

    @pytest.mark.asyncio
    async def test_get_review_stats(
        self, client: AsyncClient, auth_headers: dict, test_repetitions: list[SpacedRepetition]
    ):
        """Test getting review statistics"""
        response = await client.get(
            "/api/review/stats",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_due" in data
        assert "total_scheduled" in data
        assert "reviewed_today" in data
        assert "streak_days" in data
        assert "weak_points_count" in data
        assert "mastery_distribution" in data

    @pytest.mark.asyncio
    async def test_review_stats_empty_user(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test review stats for user with no data"""
        # This test needs an empty user - use fresh auth_headers
        response = await client.get(
            "/api/review/stats",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # These should be 0 for a new user without repetitions
        assert data["total_due"] == 0
        assert data["total_scheduled"] == 0

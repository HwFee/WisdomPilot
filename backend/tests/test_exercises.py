"""Tests for Exercise API endpoints - Question Bank"""

import pytest
import uuid
from datetime import datetime, timezone


@pytest.mark.asyncio
class TestExerciseList:
    """Test GET /api/exercises/{chapter_id} endpoint"""

    async def test_get_exercises_empty(self, client, db_session):
        """Should return empty list when no exercises"""
        response = await client.get("/api/exercises/1")
        assert response.status_code == 200
        data = response.json()
        assert data["exercises"] == []
        assert data["total"] == 0

    async def test_get_exercises_returns_list(self, client, db_session):
        """Should return exercises for chapter"""
        from app.models.exercise import Exercise
        from app.models.course import Course

        # Create course first
        course = Course(
            code="TEST101",
            name="Test Course",
            description="Test",
            difficulty_level=1,
        )
        db_session.add(course)
        await db_session.commit()
        await db_session.refresh(course)

        # Create chapter
        from app.models.chapter import Chapter
        chapter = Chapter(
            course_id=course.id,
            title="Test Chapter",
            description="Test",
            order_index=1,
        )
        db_session.add(chapter)
        await db_session.commit()
        await db_session.refresh(chapter)

        # Create exercise
        exercise = Exercise(
            chapter_id=chapter.id,
            source="manual",
            type="choice",
            difficulty=2,
            content={
                "text": "What is 2+2?",
                "options": ["3", "4", "5", "6"],
                "correct_index": 1,
            },
            solution={"answer": 1, "explanation": "2+2=4"},
            hints=["Think mathematically"],
            is_verified=True,
        )
        db_session.add(exercise)
        await db_session.commit()

        response = await client.get(f"/api/exercises/{chapter.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 1
        assert len(data["exercises"]) == 1

    async def test_get_exercises_filters_unverified(self, client, db_session):
        """Should not return unverified exercises"""
        from app.models.exercise import Exercise
        from app.models.course import Course
        from app.models.chapter import Chapter

        course = Course(code="TEST101", name="Test Course", description="Test", difficulty_level=1)
        db_session.add(course)
        await db_session.commit()
        await db_session.refresh(course)

        chapter = Chapter(
            course_id=course.id,
            title="Test Chapter",
            description="Test",
            order_index=1,
        )
        db_session.add(chapter)
        await db_session.commit()
        await db_session.refresh(chapter)

        # Create unverified exercise
        exercise = Exercise(
            chapter_id=chapter.id,
            source="ai_generated",
            type="choice",
            difficulty=2,
            content={"text": "Test?"},
            is_verified=False,  # Not verified
        )
        db_session.add(exercise)
        await db_session.commit()

        response = await client.get(f"/api/exercises/{chapter.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0  # Unverified not returned

    async def test_get_exercises_filters_by_difficulty(self, client, db_session):
        """Should filter exercises by difficulty"""
        from app.models.exercise import Exercise
        from app.models.course import Course
        from app.models.chapter import Chapter

        course = Course(code="TEST101", name="Test Course", description="Test", difficulty_level=1)
        db_session.add(course)
        await db_session.commit()
        await db_session.refresh(course)

        chapter = Chapter(
            course_id=course.id,
            title="Test Chapter",
            description="Test",
            order_index=1,
        )
        db_session.add(chapter)
        await db_session.commit()
        await db_session.refresh(chapter)

        # Create exercises with different difficulties
        for diff in [1, 2, 3]:
            exercise = Exercise(
                chapter_id=chapter.id,
                source="manual",
                type="choice",
                difficulty=diff,
                content={"text": f"Question difficulty {diff}"},
                is_verified=True,
            )
            db_session.add(exercise)
        await db_session.commit()

        # Filter by difficulty 2
        response = await client.get(f"/api/exercises/{chapter.id}?difficulty=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


@pytest.mark.asyncio
class TestExerciseSubmit:
    """Test POST /api/exercises/{id}/submit endpoint"""

    async def test_submit_requires_auth(self, client):
        """Should require authentication"""
        response = await client.post("/api/exercises/1/submit", json={"answer": "test"})
        assert response.status_code == 401

    async def test_submit_correct_answer(self, client, auth_headers, db_session):
        """Should return is_correct=true for correct answer"""
        from app.models.exercise import Exercise
        from app.models.course import Course
        from app.models.chapter import Chapter

        course = Course(code="TEST101", name="Test Course", description="Test", difficulty_level=1)
        db_session.add(course)
        await db_session.commit()
        await db_session.refresh(course)

        chapter = Chapter(
            course_id=course.id,
            title="Test Chapter",
            description="Test",
            order_index=1,
        )
        db_session.add(chapter)
        await db_session.commit()
        await db_session.refresh(chapter)

        exercise = Exercise(
            chapter_id=chapter.id,
            source="manual",
            type="choice",
            difficulty=2,
            content={
                "text": "What is 2+2?",
                "options": ["3", "4", "5", "6"],
                "correct_index": 1,
            },
            solution={"answer": 1, "explanation": "2+2=4"},
            is_verified=True,
        )
        db_session.add(exercise)
        await db_session.commit()
        await db_session.refresh(exercise)

        response = await client.post(
            f"/api/exercises/{exercise.id}/submit",
            json={"answer": 1},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] is True
        assert data["xp_earned"] > 0
        assert data["correct_answer"] == 1

    async def test_submit_wrong_answer(self, client, auth_headers, db_session):
        """Should return is_correct=false for wrong answer"""
        from app.models.exercise import Exercise
        from app.models.course import Course
        from app.models.chapter import Chapter

        course = Course(code="TEST101", name="Test Course", description="Test", difficulty_level=1)
        db_session.add(course)
        await db_session.commit()
        await db_session.refresh(course)

        chapter = Chapter(
            course_id=course.id,
            title="Test Chapter",
            description="Test",
            order_index=1,
        )
        db_session.add(chapter)
        await db_session.commit()
        await db_session.refresh(chapter)

        exercise = Exercise(
            chapter_id=chapter.id,
            source="manual",
            type="choice",
            difficulty=2,
            content={
                "text": "What is 2+2?",
                "options": ["3", "4", "5", "6"],
                "correct_index": 1,
            },
            solution={"answer": 1, "explanation": "2+2=4"},
            is_verified=True,
        )
        db_session.add(exercise)
        await db_session.commit()
        await db_session.refresh(exercise)

        response = await client.post(
            f"/api/exercises/{exercise.id}/submit",
            json={"answer": 0},  # Wrong answer
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] is False
        assert data["xp_earned"] == 0

    async def test_submit_nonexistent_exercise(self, client, auth_headers):
        """Should return 404 for nonexistent exercise"""
        response = await client.post(
            "/api/exercises/99999/submit",
            json={"answer": 1},
            headers=auth_headers,
        )
        assert response.status_code == 404


@pytest.mark.asyncio
class TestExerciseGenerate:
    """Test POST /api/exercises/generate endpoint"""

    async def test_generate_requires_admin(self, client, auth_headers):
        """Should require admin authentication"""
        response = await client.post(
            "/api/exercises/generate",
            json={"chapter_id": 1, "count": 3},
            headers=auth_headers,
        )
        # auth_headers is for regular user, not admin
        assert response.status_code in [401, 403]

    async def test_generate_requires_auth(self, client):
        """Should require authentication"""
        response = await client.post(
            "/api/exercises/generate",
            json={"chapter_id": 1, "count": 3},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestExerciseService:
    """Test exercise service logic"""

    async def test_check_answer_updates_usage_count(self, db_session, auth_user):
        """Should increment usage_count when answer submitted"""
        from app.models.exercise import Exercise
        from app.models.course import Course
        from app.models.chapter import Chapter
        from app.services.exercise import exercise_service

        course = Course(code="TEST101", name="Test Course", description="Test", difficulty_level=1)
        db_session.add(course)
        await db_session.commit()
        await db_session.refresh(course)

        chapter = Chapter(
            course_id=course.id,
            title="Test Chapter",
            description="Test",
            order_index=1,
        )
        db_session.add(chapter)
        await db_session.commit()
        await db_session.refresh(chapter)

        exercise = Exercise(
            chapter_id=chapter.id,
            source="manual",
            type="choice",
            difficulty=1,
            content={
                "text": "What is 2+2?",
                "options": ["3", "4", "5", "6"],
                "correct_index": 1,
            },
            solution={"answer": 1},
            is_verified=True,
            usage_count=0,
        )
        db_session.add(exercise)
        await db_session.commit()
        await db_session.refresh(exercise)

        initial_count = exercise.usage_count

        await exercise_service.check_answer(
            db=db_session,
            user=auth_user,
            exercise=exercise,
            user_answer=1,
        )

        await db_session.refresh(exercise)
        assert exercise.usage_count == initial_count + 1

    async def test_check_answer_updates_user_xp(self, db_session, auth_user):
        """Should update user XP when answer is correct"""
        from app.models.exercise import Exercise
        from app.models.course import Course
        from app.models.chapter import Chapter
        from app.services.exercise import exercise_service

        course = Course(code="TEST101", name="Test Course", description="Test", difficulty_level=1)
        db_session.add(course)
        await db_session.commit()
        await db_session.refresh(course)

        chapter = Chapter(
            course_id=course.id,
            title="Test Chapter",
            description="Test",
            order_index=1,
        )
        db_session.add(chapter)
        await db_session.commit()
        await db_session.refresh(chapter)

        exercise = Exercise(
            chapter_id=chapter.id,
            source="manual",
            type="choice",
            difficulty=2,
            content={
                "text": "What is 2+2?",
                "options": ["3", "4", "5", "6"],
                "correct_index": 1,
            },
            solution={"answer": 1},
            is_verified=True,
        )
        db_session.add(exercise)
        await db_session.commit()
        await db_session.refresh(exercise)

        initial_xp = auth_user.xp

        await exercise_service.check_answer(
            db=db_session,
            user=auth_user,
            exercise=exercise,
            user_answer=1,
        )

        await db_session.refresh(auth_user)
        # Difficulty 2 gives 10 XP base
        assert auth_user.xp > initial_xp

    async def test_verify_exercise(self, db_session):
        """Should mark exercise as verified"""
        from app.models.exercise import Exercise
        from app.models.course import Course
        from app.models.chapter import Chapter
        from app.services.exercise import exercise_service

        course = Course(code="TEST101", name="Test Course", description="Test", difficulty_level=1)
        db_session.add(course)
        await db_session.commit()
        await db_session.refresh(course)

        chapter = Chapter(
            course_id=course.id,
            title="Test Chapter",
            description="Test",
            order_index=1,
        )
        db_session.add(chapter)
        await db_session.commit()
        await db_session.refresh(chapter)

        exercise = Exercise(
            chapter_id=chapter.id,
            source="ai_generated",
            type="choice",
            difficulty=1,
            content={"text": "Test"},
            is_verified=False,
        )
        db_session.add(exercise)
        await db_session.commit()
        await db_session.refresh(exercise)

        verified = await exercise_service.verify_exercise(db_session, exercise.id, True)

        assert verified.is_verified is True

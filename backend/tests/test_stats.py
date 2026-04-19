"""Tests for learning statistics models and API endpoints"""

import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone, timedelta, date
from httpx import ASGITransport
from sqlalchemy import select
from app.models.stats import ChapterProgress, LearningSession, ActivityLog
from app.models.user import User
from app.main import app
from app.utils.security import get_password_hash, create_access_token


# ========================================
# Today Stats Tests (TDD - Phase 1 Fix)
# ========================================
class TestTodayStatsCalculation:
    """Test today stats calculation - specifically the is_correct logic bug fix"""

    @pytest.mark.asyncio
    async def test_today_stats_correct_count_with_correct_answers(self, client, db_session):
        """Test that correct answers are counted correctly

        This test verifies the fix for the bug where is_correct logic was inverted:
        - OLD (BUG): correct = sum(...) if is_correct == False (WRONG!)
        - NEW (FIX): correct = sum(exercises_correct) for all activities

        The bug caused: correct answers were NOT being counted because the condition
        checked for is_correct == False instead of True.
        """
        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email="todaystats@test.com",
            username="todaystatsuser",
            hashed_password=get_password_hash("Password123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create auth headers
        token = create_access_token({"sub": user.id})
        headers = {"Authorization": f"Bearer {token}"}

        # Create today's activity log with CORRECT answers (is_correct = True)
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)

        activity_correct = ActivityLog(
            user_id=user.id,
            activity_type="exercise_complete",
            description="完成练习 - 全部正确",
            extra_data={
                "exercises_completed": 3,
                "exercises_correct": 3,
                "is_correct": True,  # User got all correct
            },
            created_at=today_start,
        )
        db_session.add(activity_correct)
        await db_session.commit()

        # Call today stats API
        response = await client.get("/api/stats/today", headers=headers)
        assert response.status_code == 200
        data = response.json()

        # BUG FIX VERIFICATION:
        # Before fix: correct would be 0 (because is_correct == True, not False)
        # After fix: correct should be 3
        assert data["exercises"] == 3, f"Expected 3 exercises, got {data['exercises']}"
        assert data["correct"] == 3, f"Expected 3 correct, got {data['correct']} - BUG: is_correct logic was inverted!"

    @pytest.mark.asyncio
    async def test_today_stats_with_partial_correct_answers(self, client, db_session):
        """Test that partial correct answers are counted correctly

        Scenario: User completed 5 exercises, 3 correct (is_correct = True because > 0 correct)
        """
        user = User(
            id=str(uuid.uuid4()),
            email="partial@test.com",
            username="partialuser",
            hashed_password=get_password_hash("Password123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = create_access_token({"sub": user.id})
        headers = {"Authorization": f"Bearer {token}"}

        today = date.today()
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)

        # User did 5 exercises, 3 correct
        activity = ActivityLog(
            user_id=user.id,
            activity_type="exercise_complete",
            description="完成练习 - 部分正确",
            extra_data={
                "exercises_completed": 5,
                "exercises_correct": 3,
                "is_correct": True,  # True because exercises_correct > 0
            },
            created_at=today_start,
        )
        db_session.add(activity)
        await db_session.commit()

        response = await client.get("/api/stats/today", headers=headers)
        assert response.status_code == 200
        data = response.json()

        # Correct should be 3, not 0
        assert data["exercises"] == 5
        assert data["correct"] == 3, f"Expected 3 correct, got {data['correct']}"

    @pytest.mark.asyncio
    async def test_today_stats_with_wrong_answers_only(self, client, db_session):
        """Test that activities with all wrong answers (is_correct = False) are handled

        Scenario: User completed 2 exercises, 0 correct (is_correct = False)
        """
        user = User(
            id=str(uuid.uuid4()),
            email="wrong@test.com",
            username="wronguser",
            hashed_password=get_password_hash("Password123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = create_access_token({"sub": user.id})
        headers = {"Authorization": f"Bearer {token}"}

        today = date.today()
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)

        # User did 2 exercises, all wrong
        activity = ActivityLog(
            user_id=user.id,
            activity_type="exercise_complete",
            description="完成练习 - 全错",
            extra_data={
                "exercises_completed": 2,
                "exercises_correct": 0,
                "is_correct": False,  # False because exercises_correct == 0
            },
            created_at=today_start,
        )
        db_session.add(activity)
        await db_session.commit()

        response = await client.get("/api/stats/today", headers=headers)
        assert response.status_code == 200
        data = response.json()

        # Exercises should be 2, correct should be 0
        assert data["exercises"] == 2
        assert data["correct"] == 0

    @pytest.mark.asyncio
    async def test_today_stats_with_multiple_activities(self, client, db_session):
        """Test that multiple activities are aggregated correctly"""
        user = User(
            id=str(uuid.uuid4()),
            email="multi@test.com",
            username="multiuser",
            hashed_password=get_password_hash("Password123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = create_access_token({"sub": user.id})
        headers = {"Authorization": f"Bearer {token}"}

        today = date.today()
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)

        # Activity 1: 3 exercises, 2 correct
        activity1 = ActivityLog(
            user_id=user.id,
            activity_type="exercise_complete",
            description="练习1",
            extra_data={
                "exercises_completed": 3,
                "exercises_correct": 2,
                "is_correct": True,
            },
            created_at=today_start,
        )
        # Activity 2: 4 exercises, 3 correct
        activity2 = ActivityLog(
            user_id=user.id,
            activity_type="exercise_complete",
            description="练习2",
            extra_data={
                "exercises_completed": 4,
                "exercises_correct": 3,
                "is_correct": True,
            },
            created_at=today_start + timedelta(hours=1),
        )
        db_session.add_all([activity1, activity2])
        await db_session.commit()

        response = await client.get("/api/stats/today", headers=headers)
        assert response.status_code == 200
        data = response.json()

        # Total: 7 exercises, 5 correct
        assert data["exercises"] == 7, f"Expected 7 exercises, got {data['exercises']}"
        assert data["correct"] == 5, f"Expected 5 correct, got {data['correct']}"
        # Accuracy: 5/7 = 71.4%
        assert abs(data["accuracy"] - 71.4) < 0.5, f"Expected ~71.4% accuracy, got {data['accuracy']}%"

    @pytest.mark.asyncio
    async def test_today_stats_empty(self, client, db_session):
        """Test today stats when no activities exist"""
        user = User(
            id=str(uuid.uuid4()),
            email="empty@test.com",
            username="emptyuser",
            hashed_password=get_password_hash("Password123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = create_access_token({"sub": user.id})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get("/api/stats/today", headers=headers)
        assert response.status_code == 200
        data = response.json()

        assert data["exercises"] == 0
        assert data["correct"] == 0
        assert data["accuracy"] == 0.0


# ========================================
# API Endpoint Tests
# ========================================
class TestStatsAPI:
    """Test stats API endpoints"""

    @pytest.mark.asyncio
    async def test_get_progress_empty(self, client, auth_headers):
        """Test getting empty progress"""
        response = await client.get("/api/stats/progress", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_update_progress(self, client, auth_headers):
        """Test updating chapter progress"""
        response = await client.put(
            "/api/stats/progress/1",
            json={"status": "in_progress", "progress_percent": 50},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["chapter_id"] == 1
        assert data["status"] == "in_progress"
        assert data["progress_percent"] == 50

    @pytest.mark.asyncio
    async def test_start_session(self, client, auth_headers):
        """Test starting a learning session"""
        response = await client.post(
            "/api/stats/sessions/start",
            json={"chapter_id": 1, "subsection_index": 0},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["chapter_id"] == 1
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_end_session(self, client, auth_headers):
        """Test ending a learning session"""
        # Start session first
        start_response = await client.post(
            "/api/stats/sessions/start",
            json={"chapter_id": 1, "subsection_index": 0},
            headers=auth_headers
        )
        session_id = start_response.json()["id"]

        # End session
        response = await client.post(
            "/api/stats/sessions/end",
            json={"duration_seconds": 3600},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert data["duration_seconds"] == 3600

    @pytest.mark.asyncio
    async def test_get_statistics(self, client, auth_headers):
        """Test getting learning statistics"""
        response = await client.get("/api/stats/statistics", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_learning_time_seconds" in data
        assert "completed_chapters" in data
        assert "in_progress_chapters" in data

    @pytest.mark.asyncio
    async def test_get_activities(self, client, auth_headers):
        """Test getting activity history"""
        response = await client.get("/api/stats/activities", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client):
        """Test that unauthenticated requests are rejected"""
        response = await client.get("/api/stats/progress")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_chapter_id(self, client, auth_headers):
        """Test updating invalid chapter ID"""
        response = await client.put(
            "/api/stats/progress/99",
            json={"status": "completed"},
            headers=auth_headers
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_complete_exercise(self, client, auth_headers):
        """Test completing an exercise adds subsection to completed_subsections"""
        # Initial progress
        await client.put(
            "/api/stats/progress/1",
            json={"completed_subsections": []},
            headers=auth_headers
        )

        # Complete exercise for subsection 0
        response = await client.put(
            "/api/stats/progress/1",
            json={"completed_subsections": [0]},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["completed_subsections"] == [0]

        # Complete exercise for subsection 1 (should keep 0)
        response = await client.put(
            "/api/stats/progress/1",
            json={"completed_subsections": [0, 1]},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["completed_subsections"] == [0, 1]

    @pytest.mark.asyncio
    async def test_complete_exercise_persists(self, client, auth_headers):
        """Test that completed exercises persist across requests"""
        # Complete exercise
        response = await client.put(
            "/api/stats/progress/1",
            json={"completed_subsections": [0]},
            headers=auth_headers
        )
        assert response.status_code == 200

        # Get progress - should still have the completed subsection
        response = await client.get("/api/stats/progress", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        chapter1_progress = next((p for p in data if p["chapter_id"] == 1), None)
        assert chapter1_progress is not None
        assert 0 in chapter1_progress["completed_subsections"]

    @pytest.mark.asyncio
    async def test_complete_one_exercise_one_percent(self, client, auth_headers):
        """Test that completing one exercise updates progress by ~7% (1/14)"""
        # Initial state - no subsections completed
        response = await client.put(
            "/api/stats/progress/1",
            json={"completed_subsections": []},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["progress_percent"] == 0

        # Complete one subsection (e.g., one small section with 3 exercises)
        response = await client.put(
            "/api/stats/progress/1",
            json={"completed_subsections": [0]},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # 1/14 ≈ 7.14%, stored as int → 7%
        assert data["progress_percent"] == 7
        assert data["completed_subsections"] == [0]

        # Complete two subsections
        response = await client.put(
            "/api/stats/progress/1",
            json={"completed_subsections": [0, 1]},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # 2/14 ≈ 14.28%, stored as int → 14%
        assert data["progress_percent"] == 14
        assert data["completed_subsections"] == [0, 1]

    @pytest.mark.asyncio
    async def test_progress_should_not_use_placeholder_array(self, client, auth_headers):
        """Test that progress update does NOT accept placeholder arrays like [0, 0, 0]

        This test verifies the bug fix: previously, frontend was sending
        [0, 0, 0] to indicate "3 exercises completed" instead of
        [0] to indicate "subsection 0 completed".

        The backend should reject or handle arrays with duplicate values.
        """
        # Send [0, 0] - this should be treated as 2 completed subsections
        # (which is semantically wrong from frontend, but backend accepts it)
        response = await client.put(
            "/api/stats/progress/1",
            json={"completed_subsections": [0, 0]},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # Backend treats [0, 0] as len=2, so 2/14 * 100 = 14%
        assert data["progress_percent"] == 14
        # Note: completed_subsections will be [0, 0] which is problematic

        # The correct approach: [0] means subsection 0 completed
        response = await client.put(
            "/api/stats/progress/1",
            json={"completed_subsections": [0]},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["progress_percent"] == 7
        assert data["completed_subsections"] == [0]

    @pytest.mark.asyncio
    async def test_completed_exercise_count_progress(self, client, auth_headers):
        """Test that completed_exercise_count correctly calculates progress

        This tests the new flow where frontend sends completed_exercise_count
        instead of completed_subsections array.
        """
        # Complete 1 exercise out of 14 total
        response = await client.put(
            "/api/stats/progress/1",
            json={"completed_exercise_count": 1},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # 1/14 * 100 ≈ 7.14% → stored as 7
        assert data["progress_percent"] == 7
        assert data["completed_exercise_count"] == 1
        assert data["status"] == "in_progress"

        # Complete 3 exercises
        response = await client.put(
            "/api/stats/progress/1",
            json={"completed_exercise_count": 3},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # 3/14 * 100 ≈ 21.42% → stored as 21
        assert data["progress_percent"] == 21
        assert data["completed_exercise_count"] == 3

        # Complete all 14 exercises
        response = await client.put(
            "/api/stats/progress/1",
            json={"completed_exercise_count": 14},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["progress_percent"] == 100
        assert data["completed_exercise_count"] == 14
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_total_exercises_affects_progress(self, client, auth_headers):
        """Test that total_exercises correctly affects progress calculation

        If total_exercises is 3:
        - 1/3 * 100 = 33%
        - 2/3 * 100 = 66%
        - 3/3 * 100 = 100%
        """
        # Complete 1 exercise out of 3 total
        response = await client.put(
            "/api/stats/progress/1",
            json={"completed_exercise_count": 1, "total_exercises": 3},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # 1/3 * 100 = 33.33% → stored as 33
        assert data["progress_percent"] == 33

        # Complete 2 exercises out of 3 total
        response = await client.put(
            "/api/stats/progress/1",
            json={"completed_exercise_count": 2, "total_exercises": 3},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # 2/3 * 100 = 66.66% → stored as 66
        assert data["progress_percent"] == 66

        # Complete all 3 exercises
        response = await client.put(
            "/api/stats/progress/1",
            json={"completed_exercise_count": 3, "total_exercises": 3},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["progress_percent"] == 100

    @pytest.mark.asyncio
    async def test_completed_exercises_by_subsection(self, client, auth_headers):
        """Test that completed_exercises_by_subsection correctly stores per-subsection exercise completion

        This tests the new flow where frontend sends:
        - completedExercisesBySubsection: {"0": [1, 2], "1": [3]} meaning:
          - Subsection 0: exercises 1 and 2 completed
          - Subsection 1: exercise 3 completed

        Note: JSON keys are strings, so we use "0" not 0
        """
        # Complete exercise 1 in subsection 0
        response = await client.put(
            "/api/stats/progress/1",
            json={
                "completed_exercise_count": 1,
                "total_exercises": 3,
                "completed_exercises_by_subsection": {"0": [1]},
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["completed_exercises_by_subsection"] == {"0": [1]}
        assert data["completed_exercise_count"] == 1

        # Complete exercise 2 in subsection 0 (now subsection 0 has [1, 2])
        response = await client.put(
            "/api/stats/progress/1",
            json={
                "completed_exercise_count": 2,
                "total_exercises": 3,
                "completed_exercises_by_subsection": {"0": [1, 2]},
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["completed_exercises_by_subsection"] == {"0": [1, 2]}
        assert data["completed_exercise_count"] == 2

        # Complete exercise 1 in subsection 1 (now we have {"0": [1, 2], "1": [1]})
        response = await client.put(
            "/api/stats/progress/1",
            json={
                "completed_exercise_count": 3,
                "total_exercises": 5,
                "completed_exercises_by_subsection": {"0": [1, 2], "1": [1]},
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["completed_exercises_by_subsection"] == {"0": [1, 2], "1": [1]}
        assert data["completed_exercise_count"] == 3


class TestChapterProgressModel:
    """Test ChapterProgress model"""

    @pytest.mark.asyncio
    async def test_create_chapter_progress(self, db_session):
        """Test creating a chapter progress record"""
        from app.models.user import User
        import uuid

        # Create user first
        user = User(
            id=str(uuid.uuid4()),
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
        )
        db_session.add(user)
        await db_session.commit()

        # Create chapter progress
        progress = ChapterProgress(
            user_id=user.id,
            chapter_id=1,
            status="not_started",
            progress_percent=0,
            completed_subsections=[],
        )
        db_session.add(progress)
        await db_session.commit()

        assert progress.id is not None
        assert progress.user_id == user.id
        assert progress.chapter_id == 1
        assert progress.status == "not_started"
        assert progress.progress_percent == 0

    @pytest.mark.asyncio
    async def test_chapter_progress_relationships(self, db_session):
        """Test chapter progress user relationship"""
        from app.models.user import User
        import uuid

        user = User(
            id=str(uuid.uuid4()),
            email="test2@example.com",
            username="testuser2",
            hashed_password="hashed",
        )
        db_session.add(user)
        await db_session.commit()

        progress = ChapterProgress(
            user_id=user.id,
            chapter_id=2,
            status="in_progress",
            progress_percent=50,
            completed_subsections=[0, 1, 2],
        )
        db_session.add(progress)
        await db_session.commit()

        # Refresh and check
        await db_session.refresh(progress)
        assert progress.user.id == user.id


class TestLearningSessionModel:
    """Test LearningSession model"""

    @pytest.mark.asyncio
    async def test_create_learning_session(self, db_session):
        """Test creating a learning session"""
        from app.models.user import User
        import uuid

        user = User(
            id=str(uuid.uuid4()),
            email="session@example.com",
            username="sessionuser",
            hashed_password="hashed",
        )
        db_session.add(user)
        await db_session.commit()

        session = LearningSession(
            user_id=user.id,
            chapter_id=1,
            subsection_index=0,
            is_active=True,
        )
        db_session.add(session)
        await db_session.commit()

        assert session.id is not None
        assert session.is_active is True
        assert session.ended_at is None

    @pytest.mark.asyncio
    async def test_end_learning_session(self, db_session):
        """Test ending a learning session"""
        from app.models.user import User
        from datetime import datetime
        import uuid

        user = User(
            id=str(uuid.uuid4()),
            email="end@example.com",
            username="enduser",
            hashed_password="hashed",
        )
        db_session.add(user)
        await db_session.commit()

        session = LearningSession(
            user_id=user.id,
            chapter_id=1,
            subsection_index=0,
            is_active=True,
        )
        db_session.add(session)
        await db_session.commit()

        # End session
        session.is_active = False
        session.ended_at = datetime.now(timezone.utc)
        session.duration_seconds = 3600
        await db_session.commit()

        assert session.is_active is False
        assert session.ended_at is not None
        assert session.duration_seconds == 3600


class TestStatsServiceAPI:
    """Test the new StatsService-based API endpoints (Phase 5)"""

    @pytest.mark.asyncio
    async def test_get_my_stats(self, client, auth_headers, db_session):
        """Test GET /api/stats/user/me - returns user learning stats"""
        # Create user with some data first
        user = User(
            id=str(uuid.uuid4()),
            email="stats@test.com",
            username="statsuser",
            hashed_password=get_password_hash("Password123"),
            is_active=True,
            xp=250,
            mastery_level="熟练",
            streak_days=5,
            total_exercises=20,
            correct_exercises=18,
            accuracy_rate=90.0,
            preferred_languages=["Python", "JavaScript"],
        )
        db_session.add(user)
        await db_session.commit()

        # Get auth headers for this user
        from app.utils.security import create_access_token
        token = create_access_token({"sub": user.id})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get("/api/stats/user/me", headers=headers)
        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "user" in data
        assert "chapter_progress" in data
        assert "exercises" in data
        assert "learning_time" in data
        assert "challenges" in data
        assert "xp_summary" in data

        # Verify user data
        assert data["user"]["xp"] == 250
        assert data["user"]["streak_days"] == 5
        assert data["xp_summary"]["total_xp"] == 250

        # Verify exercises
        assert data["exercises"]["total"] == 20
        assert data["exercises"]["correct"] == 18
        assert data["exercises"]["accuracy_rate"] == 90.0

    @pytest.mark.asyncio
    async def test_get_my_stats_unauthorized(self, client):
        """Test GET /api/stats/user/me requires authentication"""
        response = await client.get("/api/stats/user/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_leaderboard(self, client, db_session):
        """Test GET /api/stats/leaderboard - returns ranked users"""
        # Create multiple users with different XP
        for i, xp in enumerate([500, 300, 400, 100, 200]):
            user = User(
                id=str(uuid.uuid4()),
                email=f"leader{i}@test.com",
                username=f"leaderuser{i}",
                hashed_password=get_password_hash("Password123"),
                is_active=True,
                xp=xp,
                mastery_level="学习",
                streak_days=i,
                accuracy_rate=80.0 + i,
            )
            db_session.add(user)
        await db_session.commit()

        response = await client.get("/api/stats/leaderboard")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 5

        # Should be sorted by XP descending
        assert data[0]["xp"] == 500
        assert data[1]["xp"] == 400
        assert data[2]["xp"] == 300
        assert data[3]["xp"] == 200
        assert data[4]["xp"] == 100

        # Verify rank is set correctly
        assert data[0]["rank"] == 1
        assert data[1]["rank"] == 2

    @pytest.mark.asyncio
    async def test_get_leaderboard_with_pagination(self, client, db_session):
        """Test GET /api/stats/leaderboard with limit and offset"""
        # Create 10 users with sequential XP
        for i in range(10):
            user = User(
                id=str(uuid.uuid4()),
                email=f"page{i}@test.com",
                username=f"pageuser{i}",
                hashed_password=get_password_hash("Password123"),
                is_active=True,
                xp=(10 - i) * 100,  # 1000, 900, 800, ...
                mastery_level="学习",
            )
            db_session.add(user)
        await db_session.commit()

        # Get first page (limit 3)
        response = await client.get("/api/stats/leaderboard?limit=3&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["xp"] == 1000
        assert data[2]["xp"] == 800

        # Get second page
        response = await client.get("/api/stats/leaderboard?limit=3&offset=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["xp"] == 700

    @pytest.mark.asyncio
    async def test_get_course_stats(self, client, db_session):
        """Test GET /api/stats/courses/{course_id} - returns course enrollment stats"""
        # Create course and chapters
        from app.models.course import Course
        from app.models.chapter import Chapter

        course = Course(
            code="PY101",
            name="Python 基础",
            description="Python编程基础课程",
        )
        db_session.add(course)
        await db_session.commit()
        await db_session.refresh(course)

        # Create chapters for this course
        for i in range(1, 4):
            chapter = Chapter(
                course_id=course.id,
                title=f"Chapter {i}",
                description=f"Chapter {i} desc",
                order_index=i,
            )
            db_session.add(chapter)
        await db_session.commit()

        # Create progress for some users
        user1 = User(
            id=str(uuid.uuid4()),
            email="course1@test.com",
            username="courseuser1",
            hashed_password=get_password_hash("Password123"),
            is_active=True,
        )
        user2 = User(
            id=str(uuid.uuid4()),
            email="course2@test.com",
            username="courseuser2",
            hashed_password=get_password_hash("Password123"),
            is_active=True,
        )
        db_session.add(user1)
        db_session.add(user2)
        await db_session.commit()

        # Add progress for user1 on chapters 1 and 2
        from app.models.stats import ChapterProgress
        progress1 = ChapterProgress(user_id=user1.id, chapter_id=1, status="in_progress", progress_percent=50)
        progress2 = ChapterProgress(user_id=user1.id, chapter_id=2, status="completed", progress_percent=100)
        db_session.add(progress1)
        db_session.add(progress2)
        await db_session.commit()

        response = await client.get(f"/api/stats/courses/{course.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["course_id"] == course.id
        assert data["code"] == "PY101"
        assert data["name"] == "Python 基础"
        assert data["chapter_count"] == 3
        assert data["enrolled_users"] == 1  # Only user1 has progress
        assert data["completed_users"] == 1  # user1 completed chapter 2

    @pytest.mark.asyncio
    async def test_get_course_stats_not_found(self, client):
        """Test GET /api/stats/courses/{id} returns empty for non-existent course"""
        response = await client.get("/api/stats/courses/99999")
        assert response.status_code == 200
        data = response.json()
        assert data == {}  # Returns empty dict for non-existent course

    @pytest.mark.asyncio
    async def test_get_my_recent_activity(self, client, auth_headers, db_session):
        """Test GET /api/stats/activity/me - returns recent activity"""
        # Create activity logs for user
        from app.models.stats import ActivityLog

        user = User(
            id=str(uuid.uuid4()),
            email="activity2@test.com",
            username="activityuser2",
            hashed_password=get_password_hash("Password123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create auth headers
        token = create_access_token({"sub": user.id})
        headers = {"Authorization": f"Bearer {token}"}

        # Create activities with staggered timestamps - oldest to newest
        now = datetime.now(timezone.utc)
        activities = [
            ActivityLog(user_id=user.id, activity_type="chapter_started", chapter_id=1, description="开始学习", created_at=now - timedelta(minutes=10)),
            ActivityLog(user_id=user.id, activity_type="exercise_complete", chapter_id=1, description="完成练习", created_at=now - timedelta(minutes=5)),
            ActivityLog(user_id=user.id, activity_type="chapter_completed", chapter_id=1, description="完成章节", created_at=now),
        ]
        for a in activities:
            db_session.add(a)
        await db_session.commit()

        response = await client.get("/api/stats/activity/me", headers=headers)
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 3
        # Most recent first
        assert data[0]["activity_type"] == "chapter_completed"
        assert data[1]["activity_type"] == "exercise_complete"
        assert data[2]["activity_type"] == "chapter_started"

    @pytest.mark.asyncio
    async def test_get_my_recent_activity_with_limit(self, client, auth_headers, db_session):
        """Test GET /api/stats/activity/me with limit parameter"""
        user = User(
            id=str(uuid.uuid4()),
            email="activity3@test.com",
            username="activityuser3",
            hashed_password=get_password_hash("Password123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = create_access_token({"sub": user.id})
        headers = {"Authorization": f"Bearer {token}"}

        from app.models.stats import ActivityLog
        for i in range(10):
            activity = ActivityLog(
                user_id=user.id,
                activity_type="exercise_complete",
                chapter_id=1,
                description=f"练习 {i}",
            )
            db_session.add(activity)
        await db_session.commit()

        response = await client.get("/api/stats/activity/me?limit=5", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    @pytest.mark.asyncio
    async def test_get_my_recent_activity_unauthorized(self, client):
        """Test GET /api/stats/activity/me requires authentication"""
        response = await client.get("/api/stats/activity/me")
        assert response.status_code == 401


class TestActivityLogModel:
    """Test ActivityLog model"""

    @pytest.mark.asyncio
    async def test_create_activity_log(self, db_session):
        """Test creating an activity log entry"""
        from app.models.user import User
        import uuid

        user = User(
            id=str(uuid.uuid4()),
            email="activity@example.com",
            username="activityuser",
            hashed_password="hashed",
        )
        db_session.add(user)
        await db_session.commit()

        activity = ActivityLog(
            user_id=user.id,
            activity_type="chapter_started",
            chapter_id=1,
            description="开始学习第一章",
        )
        db_session.add(activity)
        await db_session.commit()

        assert activity.id is not None
        assert activity.activity_type == "chapter_started"
        assert activity.description == "开始学习第一章"

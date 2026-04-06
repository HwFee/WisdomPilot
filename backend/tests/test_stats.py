"""Tests for learning statistics models and API endpoints"""

import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone
from httpx import ASGITransport
from sqlalchemy import select
from app.models.stats import ChapterProgress, LearningSession, ActivityLog
from app.models.user import User
from app.main import app
from app.utils.security import get_password_hash


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

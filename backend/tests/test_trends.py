"""Tests for daily statistics trends API"""

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import select

from app.models.stats import ActivityLog


@pytest.mark.asyncio
class TestDailyStatsTrends:
    """Test daily statistics trends endpoints"""

    async def test_get_daily_exercises_trend(self, client, auth_headers, auth_user, db_session):
        """Should return daily exercises count for the past 7 days"""
        # Create some activity logs for the past few days
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Create exercise activities for today
        for i in range(3):
            activity = ActivityLog(
                user_id=auth_user.id,
                activity_type="exercise_complete",
                description=f"Completed exercise {i}",
                created_at=now
            )
            db_session.add(activity)

        # Create exercise activities for yesterday
        yesterday = now - timedelta(days=1)
        for i in range(5):
            activity = ActivityLog(
                user_id=auth_user.id,
                activity_type="exercise_complete",
                description=f"Completed exercise {i}",
                created_at=yesterday
            )
            db_session.add(activity)

        await db_session.commit()

        response = await client.get("/api/stats/trends/exercises", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "trends" in data
        assert len(data["trends"]) == 7  # 7 days of data

        # Check today's count
        today_data = data["trends"][0]
        assert today_data["count"] == 3

        # Check yesterday's count
        yesterday_data = data["trends"][1]
        assert yesterday_data["count"] == 5

    async def test_get_daily_accuracy_trend(self, client, auth_headers, auth_user, db_session):
        """Should return daily accuracy rate for the past 7 days"""
        response = await client.get("/api/stats/trends/accuracy", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "trends" in data
        assert len(data["trends"]) == 7

        # Each trend entry should have date and accuracy
        for trend in data["trends"]:
            assert "date" in trend
            assert "accuracy" in trend
            assert "total" in trend
            assert "correct" in trend

    async def test_get_daily_learning_time_trend(self, client, auth_headers, auth_user, db_session):
        """Should return daily learning time for the past 7 days"""
        from app.models.stats import LearningSession

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Create learning sessions for today
        for i in range(2):
            session = LearningSession(
                user_id=auth_user.id,
                chapter_id=1,
                subsection_index=i,
                started_at=now - timedelta(minutes=30),
                ended_at=now,
                duration_seconds=1800,  # 30 minutes
                is_active=False
            )
            db_session.add(session)

        await db_session.commit()

        response = await client.get("/api/stats/trends/time", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "trends" in data
        assert len(data["trends"]) == 7

        # Check today's learning time (60 minutes from 2 sessions)
        today_data = data["trends"][0]
        assert today_data["minutes"] == 60

    async def test_trends_require_auth(self, client):
        """Should require authentication for trends endpoints"""
        endpoints = [
            "/api/stats/trends/exercises",
            "/api/stats/trends/accuracy",
            "/api/stats/trends/time",
        ]

        for endpoint in endpoints:
            response = await client.get(endpoint)
            assert response.status_code == 401, f"{endpoint} should require auth"

    async def test_trends_with_no_data(self, client, auth_headers):
        """Should return zero values when no data exists"""
        response = await client.get("/api/stats/trends/exercises", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data["trends"]) == 7
        for trend in data["trends"]:
            assert trend["count"] == 0

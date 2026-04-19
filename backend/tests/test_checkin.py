"""Tests for Check-in (打卡) API"""

import pytest
from datetime import datetime, timezone, timedelta


@pytest.mark.asyncio
class TestCheckinEndpoints:
    """Test check-in endpoints"""

    async def test_checkin_requires_auth(self, client):
        """Should require authentication"""
        response = await client.post("/api/users/checkin")
        assert response.status_code == 401

    async def test_checkin_first_time(self, client, auth_headers, auth_user, db_session):
        """Should set streak to 1 on first check-in when user has no streak"""
        # Reset user's streak for clean test (last_activity_date was set by default)
        auth_user.streak_days = 0
        # Set last_activity_date to far in the past (simulating no previous check-in)
        from datetime import datetime, timezone
        auth_user.last_activity_date = datetime(2020, 1, 1)
        await db_session.commit()

        response = await client.post("/api/users/checkin", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["streak_days"] == 1
        assert data["checked_in_today"] is True
        assert "xp_earned" in data

    async def test_checkin_same_day(self, client, auth_headers, auth_user, db_session):
        """Should not increment streak if already checked in today"""
        # Reset for clean test - set last activity far in the past
        from datetime import datetime
        auth_user.streak_days = 0
        auth_user.last_activity_date = datetime(2020, 1, 1)
        await db_session.commit()

        # First check-in
        response1 = await client.post("/api/users/checkin", headers=auth_headers)
        assert response1.status_code == 200
        assert response1.json()["streak_days"] == 1

        # Second check-in same day
        response2 = await client.post("/api/users/checkin", headers=auth_headers)
        assert response2.status_code == 200

        data = response2.json()
        # Streak should still be 1
        assert data["streak_days"] == 1
        assert data["checked_in_today"] is True
        # No XP for duplicate check-in
        assert data["xp_earned"] == 0

    async def test_checkin_consecutive_days(self, client, auth_headers, auth_user, db_session):
        """Should increment streak on consecutive days"""
        from app.services.profile import profile_service

        # Simulate check-in yesterday
        yesterday = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
        auth_user.last_activity_date = yesterday
        auth_user.streak_days = 1
        await db_session.commit()
        await db_session.refresh(auth_user)

        # Check-in today
        response = await client.post("/api/users/checkin", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["streak_days"] == 2
        assert data["checked_in_today"] is True
        assert data["xp_earned"] > 0

    async def test_checkin_after_gap(self, client, auth_headers, auth_user, db_session):
        """Should reset streak to 1 after missing a day"""
        # Simulate check-in 2 days ago
        two_days_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=2)
        auth_user.last_activity_date = two_days_ago
        auth_user.streak_days = 5
        await db_session.commit()
        await db_session.refresh(auth_user)

        # Check-in today
        response = await client.post("/api/users/checkin", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        # Streak should be reset to 1
        assert data["streak_days"] == 1
        assert data["checked_in_today"] is True

    async def test_checkin_status_endpoint(self, client, auth_headers, auth_user):
        """Should return check-in status"""
        response = await client.get("/api/users/checkin/status", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "streak_days" in data
        assert "checked_in_today" in data
        assert "last_checkin_date" in data


@pytest.mark.asyncio
class TestCheckinService:
    """Test check-in service logic"""

    async def test_checkin_xp_reward(self, db_session, auth_user):
        """Should award XP for first check-in of the day"""
        from app.services.profile import profile_service
        from datetime import datetime

        # Reset for clean test - set last activity far in the past
        auth_user.streak_days = 0
        auth_user.last_activity_date = datetime(2020, 1, 1)
        auth_user.xp = 0
        await db_session.commit()

        initial_xp = auth_user.xp

        result = await profile_service.checkin(db_session, auth_user)
        await db_session.refresh(auth_user)

        assert auth_user.xp > initial_xp
        assert result["xp_earned"] > 0

    async def test_checkin_streak_bonus(self, db_session, auth_user):
        """Should award bonus XP for longer streaks"""
        from app.services.profile import profile_service

        # Set up a 7-day streak
        yesterday = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
        auth_user.last_activity_date = yesterday
        auth_user.streak_days = 7
        await db_session.commit()

        result = await profile_service.checkin(db_session, auth_user)

        # Streak bonus should be applied
        assert result["streak_days"] == 8
        # More XP for longer streak
        assert result["xp_earned"] >= 10  # Base XP

    async def test_is_checked_in_today(self, db_session, auth_user):
        """Should correctly determine if user checked in today"""
        from app.services.profile import profile_service
        from app.utils.time import utc_now

        # Set last activity far in the past (not checked in today)
        auth_user.last_activity_date = datetime(2020, 1, 1)
        auth_user.total_checkin_days = 1  # Need this for is_checked_in_today to work
        auth_user.streak_days = 1
        await db_session.commit()
        assert profile_service.is_checked_in_today(auth_user) is False

        # Just checked in - use utc_now() for consistency
        now = utc_now()
        auth_user.last_activity_date = now.replace(tzinfo=None)  # Store as naive UTC
        await db_session.commit()

        assert profile_service.is_checked_in_today(auth_user) is True

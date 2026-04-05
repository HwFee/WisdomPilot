"""Tests for streak calculation in StatsService"""

import uuid
import pytest
from datetime import date, timedelta

from app.models.stats import ActivityLog
from app.models.user import User
from app.services.stats import StatsService


class TestStreakCalculation:
    """Unit tests for _calculate_streaks method"""

    @pytest.fixture
    async def user(self, db_session):
        """Create a test user"""
        user = User(
            id=str(uuid.uuid4()),
            email="streak@test.com",
            username="streakuser",
            hashed_password="hashed",
        )
        db_session.add(user)
        await db_session.commit()
        return user

    async def _create_activity(self, db_session, user, days_ago=0):
        """Create an activity log entry at a specific date"""
        from datetime import datetime, time, timezone
        target_date = date.today() - timedelta(days=days_ago)
        created_at = datetime.combine(target_date, time(12, 0), tzinfo=timezone.utc)
        activity = ActivityLog(
            user_id=user.id,
            activity_type="chapter_started",
            chapter_id=1,
            description="Study activity",
            created_at=created_at,
        )
        db_session.add(activity)
        await db_session.commit()
        return activity

    @pytest.mark.asyncio
    async def test_streak_no_activity(self, db_session, user):
        """Test streak with no activity returns (0, 0)"""
        service = StatsService(db_session)
        current, longest = await service._calculate_streaks(user.id)
        assert current == 0
        assert longest == 0

    @pytest.mark.asyncio
    async def test_streak_today_only(self, db_session, user):
        """Test streak with only today's activity: (1, 1)"""
        await self._create_activity(db_session, user, days_ago=0)
        service = StatsService(db_session)
        current, longest = await service._calculate_streaks(user.id)
        assert current == 1
        assert longest == 1

    @pytest.mark.asyncio
    async def test_streak_three_consecutive_days(self, db_session, user):
        """Test streak with three consecutive days: (3, 3)"""
        await self._create_activity(db_session, user, days_ago=0)
        await self._create_activity(db_session, user, days_ago=1)
        await self._create_activity(db_session, user, days_ago=2)
        service = StatsService(db_session)
        current, longest = await service._calculate_streaks(user.id)
        assert current == 3
        assert longest == 3

    @pytest.mark.asyncio
    async def test_streak_yesterday_only_no_today(self, db_session, user):
        """Test streak with only yesterday: current=0, longest=1"""
        await self._create_activity(db_session, user, days_ago=1)
        service = StatsService(db_session)
        current, longest = await service._calculate_streaks(user.id)
        assert current == 0
        assert longest == 1

    @pytest.mark.asyncio
    async def test_streak_broken_by_gap(self, db_session, user):
        """Test streak broken by a gap day"""
        await self._create_activity(db_session, user, days_ago=0)
        await self._create_activity(db_session, user, days_ago=2)
        await self._create_activity(db_session, user, days_ago=3)
        service = StatsService(db_session)
        current, longest = await service._calculate_streaks(user.id)
        assert current == 1
        assert longest == 2

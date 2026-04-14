"""
Tests for User Arena Profile model and leaderboard service

Following TDD: Write tests first, then implement
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_arena import UserArenaProfile
from app.models.user import User
from app.models.course import Course


class TestUserArenaProfileModel:
    """Test UserArenaProfile model CRUD operations"""

    @pytest.mark.asyncio
    async def test_create_arena_profile(self, db_session: AsyncSession, test_user: User, test_course: Course):
        """Test creating a new arena profile"""
        profile = UserArenaProfile(
            user_id=test_user.id,
            course_id=test_course.id,
        )
        db_session.add(profile)
        await db_session.commit()

        # Verify it was saved
        result = await db_session.execute(
            select(UserArenaProfile).where(
                UserArenaProfile.user_id == test_user.id,
                UserArenaProfile.course_id == test_course.id,
            )
        )
        saved = result.scalar_one_or_none()

        assert saved is not None
        assert saved.tier == "bronze"
        assert saved.total_score == 0.0
        assert saved.total_challenges == 0

    @pytest.mark.asyncio
    async def test_unique_user_course_constraint(self, db_session: AsyncSession, test_user: User, test_course: Course):
        """Test that user can only have one profile per course"""
        profile1 = UserArenaProfile(
            user_id=test_user.id,
            course_id=test_course.id,
        )
        db_session.add(profile1)
        await db_session.commit()

        # Try to create duplicate - should fail
        profile2 = UserArenaProfile(
            user_id=test_user.id,
            course_id=test_course.id,
        )
        db_session.add(profile2)

        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_update_arena_stats(self, db_session: AsyncSession, test_user: User, test_course: Course):
        """Test updating arena stats after challenge"""
        profile = UserArenaProfile(
            user_id=test_user.id,
            course_id=test_course.id,
        )
        db_session.add(profile)
        await db_session.commit()

        # Update after winning a challenge
        profile.total_score = 500.0
        profile.total_challenges = 1
        profile.wins = 1
        profile.current_streak = 1
        profile.best_streak = 1
        profile.highest_difficulty = 3
        await db_session.commit()

        # Verify
        result = await db_session.execute(
            select(UserArenaProfile).where(UserArenaProfile.id == profile.id)
        )
        updated = result.scalar_one()

        assert updated.total_score == 500.0
        assert updated.wins == 1
        assert updated.current_streak == 1


class TestTierProgression:
    """Test tier calculation and progression"""

    def test_get_tier_for_score(self):
        """Test converting score to tier"""
        from app.services.leaderboard_service import ArenaLeaderboardService

        service = ArenaLeaderboardService(None)

        assert service.get_tier_for_score(0) == "bronze"
        assert service.get_tier_for_score(999) == "bronze"
        assert service.get_tier_for_score(1000) == "silver"
        assert service.get_tier_for_score(2500) == "gold"
        assert service.get_tier_for_score(5000) == "platinum"
        assert service.get_tier_for_score(10000) == "diamond"

    def test_tier_progression(self):
        """Test tier updates after score increase"""
        from app.services.leaderboard_service import ArenaLeaderboardService

        service = ArenaLeaderboardService(None)

        # Bronze to Silver
        assert service.get_tier_for_score(1500) == "silver"

        # Silver to Gold
        assert service.get_tier_for_score(3000) == "gold"

        # Gold to Platinum
        assert service.get_tier_for_score(7500) == "platinum"

        # Platinum to Diamond
        assert service.get_tier_for_score(15000) == "diamond"


class TestLeaderboardRanking:
    """Test leaderboard ranking calculations"""

    def test_rank_sorting(self):
        """Test that rankings are sorted by score descending"""
        from app.services.leaderboard_service import ArenaLeaderboardService

        service = ArenaLeaderboardService(None)

        profiles = [
            {"user_id": "user1", "total_score": 1000},
            {"user_id": "user2", "total_score": 3000},
            {"user_id": "user3", "total_score": 2000},
        ]

        ranked = service.rank_profiles(profiles)

        assert ranked[0]["user_id"] == "user2"  # 3000
        assert ranked[1]["user_id"] == "user3"  # 2000
        assert ranked[2]["user_id"] == "user1"  # 1000


# Additional fixtures for this test module
@pytest.fixture
async def test_course(db_session: AsyncSession):
    """Create test course"""
    course = Course(
        code="TEST_ARENA_C",
        name="Test C Course for Arena",
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course

"""Tests for Achievement API endpoints"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta


@pytest.mark.asyncio
class TestAchievementList:
    """Test GET /api/achievements endpoint"""

    async def test_get_achievements_returns_list(self, client, db_session):
        """Should return a list of achievements"""
        from app.services.achievement import achievement_service

        await achievement_service.create_default_achievements(db_session)

        response = await client.get("/api/achievements")
        assert response.status_code == 200

        data = response.json()
        assert "achievements" in data
        assert "total" in data
        assert isinstance(data["achievements"], list)

    async def test_get_achievements_empty_db(self, client):
        """Should return empty list when no achievements exist"""
        response = await client.get("/api/achievements")
        assert response.status_code == 200
        assert response.json()["achievements"] == []

    async def test_get_achievements_includes_earned_status(self, client, db_session):
        """Achievement list should include key fields"""
        from app.services.achievement import achievement_service

        await achievement_service.create_default_achievements(db_session)

        response = await client.get("/api/achievements")
        assert response.status_code == 200

        data = response.json()
        ach = data["achievements"][0]
        assert "code" in ach
        assert "title" in ach
        assert "icon" in ach
        assert "type" in ach
        assert "difficulty" in ach


@pytest.mark.asyncio
class TestAchievementMe:
    """Test GET /api/achievements/me endpoint"""

    async def test_get_my_achievements_requires_auth(self, client):
        """Should require authentication"""
        response = await client.get("/api/achievements/me")
        assert response.status_code == 401

    async def test_get_my_achievements_returns_all(self, client, auth_headers, db_session):
        """Should return all achievements with earned status"""
        from app.services.achievement import achievement_service

        await achievement_service.create_default_achievements(db_session)

        response = await client.get("/api/achievements/me", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "achievements" in data
        assert "total" in data
        assert "earned_count" in data
        # Should include non-secret achievements
        assert data["total"] >= 0

    async def test_get_my_achievements_shows_earned(self, client, auth_headers, auth_user, db_session):
        """Should show earned=true for completed achievements"""
        from app.services.achievement import achievement_service

        await achievement_service.create_default_achievements(db_session)
        achievements = await achievement_service.get_active_achievements(db_session)

        # Earn the first achievement
        await achievement_service.earn_achievement(
            db_session, auth_user, achievements[0].id
        )

        response = await client.get("/api/achievements/me", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        earned = [a for a in data["achievements"] if a.get("earned")]
        assert len(earned) == 1

    async def test_get_my_achievements_hides_secret_until_earned(
        self, client, auth_headers, db_session
    ):
        """Should hide secret achievements until earned"""
        from app.models.achievement import Achievement, AchievementType

        # Create a secret achievement
        secret = Achievement(
            code="SECRET_ACH",
            title="Secret",
            description="A secret achievement",
            icon="🔐",
            type=AchievementType.SPECIAL.value,
            category="special",
            is_secret=True,
            difficulty=5,
            display_order=100,
        )
        db_session.add(secret)
        await db_session.commit()

        response = await client.get("/api/achievements/me", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        # Secret achievement should not appear
        codes = [a["code"] for a in data["achievements"]]
        assert "SECRET_ACH" not in codes


@pytest.mark.asyncio
class TestEarnedAchievements:
    """Test GET /api/achievements/earned endpoint"""

    async def test_get_earned_requires_auth(self, client):
        """Should require authentication"""
        response = await client.get("/api/achievements/earned")
        assert response.status_code == 401

    async def test_get_earned_returns_only_earned(self, client, auth_headers, auth_user, db_session):
        """Should return only earned achievements"""
        from app.services.achievement import achievement_service

        await achievement_service.create_default_achievements(db_session)
        achievements = await achievement_service.get_active_achievements(db_session)

        # Earn first achievement
        await achievement_service.earn_achievement(
            db_session, auth_user, achievements[0].id
        )

        response = await client.get("/api/achievements/earned", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data["achievements"]) == 1
        assert data["earned_count"] == 1


@pytest.mark.asyncio
class TestUserRank:
    """Test GET /api/achievements/rank endpoint"""

    async def test_get_rank_requires_auth(self, client):
        """Should require authentication"""
        response = await client.get("/api/achievements/rank")
        assert response.status_code == 401

    async def test_get_rank_returns_user_position(self, client, auth_headers, db_session):
        """Should return user's rank on leaderboard"""
        response = await client.get("/api/achievements/rank", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "rank" in data
        assert "user_id" in data
        assert "username" in data
        assert "level" in data
        assert "xp" in data
        assert "total_users" in data

    async def test_get_rank_ordering(self, client, db_session):
        """Higher XP should have better rank"""
        from app.models.user import User
        from app.utils.security import create_access_token

        # Create multiple users with different XP - auth_user is in DB with XP=0
        # So we create additional users with specific XP values
        user1 = User(
            id=str(uuid.uuid4()),
            email=f"rank1@test.com",
            username=f"rankuser1",
            hashed_password="hashed",
            is_active=True,
            xp=100,
            mastery_level="学习",
        )
        user2 = User(
            id=str(uuid.uuid4()),
            email=f"rank2@test.com",
            username=f"rankuser2",
            hashed_password="hashed",
            is_active=True,
            xp=300,
            mastery_level="熟练",
        )
        user3 = User(
            id=str(uuid.uuid4()),
            email=f"rank3@test.com",
            username=f"rankuser3",
            hashed_password="hashed",
            is_active=True,
            xp=200,
            mastery_level="练习",
        )
        db_session.add(user1)
        db_session.add(user2)
        db_session.add(user3)
        await db_session.commit()

        # Get rank for user with 200 XP (user3) - should be 2nd
        # (only user2 with 300 XP is higher)
        token = create_access_token({"sub": user3.id})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get("/api/achievements/rank", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["rank"] == 2  # user2 (300 XP) is only one higher
        assert data["xp"] == 200


@pytest.mark.asyncio
class TestAchievementService:
    """Test achievement service logic"""

    async def test_create_default_achievements(self, db_session):
        """Should create default achievements"""
        from app.services.achievement import achievement_service

        await achievement_service.create_default_achievements(db_session)

        achievements = await achievement_service.get_active_achievements(db_session)
        assert len(achievements) == 9
        codes = [a.code for a in achievements]
        assert "FIRST_LESSON" in codes
        assert "FIVE_LESSONS" in codes
        assert "STREAK_3" in codes
        assert "PERFECT_SCORE" in codes

    async def test_earn_achievement_awards_xp(self, db_session, auth_user):
        """Should award XP when earning achievement"""
        from app.services.achievement import achievement_service

        await achievement_service.create_default_achievements(db_session)
        achievements = await achievement_service.get_active_achievements(db_session)
        first_lesson = next(a for a in achievements if a.code == "FIRST_LESSON")

        initial_xp = auth_user.xp
        await achievement_service.earn_achievement(db_session, auth_user, first_lesson.id)

        await db_session.refresh(auth_user)
        # FIRST_LESSON has xp_reward of 10
        assert auth_user.xp == initial_xp + 10

    async def test_earn_achievement_awards_quota(self, db_session, auth_user):
        """Should award quota when earning achievement"""
        from app.services.achievement import achievement_service

        await achievement_service.create_default_achievements(db_session)
        achievements = await achievement_service.get_active_achievements(db_session)
        five_lessons = next(a for a in achievements if a.code == "FIVE_LESSONS")

        initial_cores = auth_user.cores
        await achievement_service.earn_achievement(db_session, auth_user, five_lessons.id)

        await db_session.refresh(auth_user)
        # FIVE_LESSONS has quota_reward of 5
        assert auth_user.cores == initial_cores + 5

    async def test_cannot_earn_same_achievement_twice(self, db_session, auth_user):
        """Should raise error if achievement already earned"""
        from app.services.achievement import achievement_service

        await achievement_service.create_default_achievements(db_session)
        achievements = await achievement_service.get_active_achievements(db_session)
        first_lesson = next(a for a in achievements if a.code == "FIRST_LESSON")

        await achievement_service.earn_achievement(db_session, auth_user, first_lesson.id)

        with pytest.raises(ValueError, match="already earned"):
            await achievement_service.earn_achievement(db_session, auth_user, first_lesson.id)

    async def test_get_user_rank_nonexistent_user(self, db_session):
        """Should return None for nonexistent user"""
        from app.services.achievement import achievement_service

        rank = await achievement_service.get_user_rank(db_session, "nonexistent-id")
        assert rank is None

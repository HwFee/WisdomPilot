"""
Tests for Mastery XP functionality

Tests:
1. User model has mastery_xp and mastery_level fields
2. User model no longer has level field
3. ProfileService.add_mastery_xp works correctly
4. ProfileService.get_mastery_level returns correct level
"""

import pytest
from datetime import datetime

from app.services.profile import profile_service
from app.models.user import User


class TestMasteryXpModel:
    """Test User model mastery XP fields"""

    def test_user_has_mastery_xp_field(self):
        """User should have mastery_xp field"""
        user = User(
            id="test-id",
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            mastery_xp=0,  # Explicitly set since SQLAlchemy default may not apply to in-memory objects
        )
        assert hasattr(user, 'mastery_xp')
        assert user.mastery_xp == 0

    def test_user_has_mastery_level_field(self):
        """User should have mastery_level field"""
        user = User(
            id="test-id",
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            mastery_level="入门",  # Explicitly set
        )
        assert hasattr(user, 'mastery_level')
        assert user.mastery_level == "入门"

    def test_user_no_level_field(self):
        """User should NOT have level field"""
        user = User(
            id="test-id",
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
        )
        assert not hasattr(user, 'level')


class TestMasteryLevelCalculation:
    """Test mastery level calculation"""

    def test_get_mastery_level_entry(self):
        """0-99 XP should be 入门"""
        assert profile_service.get_mastery_level(0) == "入门"
        assert profile_service.get_mastery_level(50) == "入门"
        assert profile_service.get_mastery_level(99) == "入门"

    def test_get_mastery_level_learning(self):
        """100-299 XP should be 学习"""
        assert profile_service.get_mastery_level(100) == "学习"
        assert profile_service.get_mastery_level(200) == "学习"
        assert profile_service.get_mastery_level(299) == "学习"

    def test_get_mastery_level_practice(self):
        """300-599 XP should be 练习"""
        assert profile_service.get_mastery_level(300) == "练习"
        assert profile_service.get_mastery_level(400) == "练习"
        assert profile_service.get_mastery_level(599) == "练习"

    def test_get_mastery_level_skilled(self):
        """600-999 XP should be 熟练"""
        assert profile_service.get_mastery_level(600) == "熟练"
        assert profile_service.get_mastery_level(800) == "熟练"
        assert profile_service.get_mastery_level(999) == "熟练"

    def test_get_mastery_level_master(self):
        """1000+ XP should be 精通"""
        assert profile_service.get_mastery_level(1000) == "精通"
        assert profile_service.get_mastery_level(2000) == "精通"
        assert profile_service.get_mastery_level(10000) == "精通"


class TestAddMasteryXp:
    """Test add_mastery_xp service method"""

    @pytest.mark.asyncio
    async def test_add_mastery_xp_increments(self, db_session):
        """Adding mastery XP should increment mastery_xp"""
        user = User(
            id="test-mastery-xp-1",
            email="test1@example.com",
            username="testuser1",
            hashed_password="hashed",
            mastery_xp=0,
            mastery_level="入门",
        )
        db_session.add(user)
        await db_session.commit()

        result = await profile_service.add_mastery_xp(db_session, user, 50)
        assert result.mastery_xp == 50

    @pytest.mark.asyncio
    async def test_add_mastery_xp_updates_level(self, db_session):
        """Adding mastery XP should update mastery_level"""
        user = User(
            id="test-mastery-xp-2",
            email="test2@example.com",
            username="testuser2",
            hashed_password="hashed",
            mastery_xp=50,
            mastery_level="入门",
        )
        db_session.add(user)
        await db_session.commit()

        # Add 60 XP to reach 110 (学习 level)
        result = await profile_service.add_mastery_xp(db_session, user, 60)
        assert result.mastery_xp == 110
        assert result.mastery_level == "学习"

    @pytest.mark.asyncio
    async def test_add_mastery_xp_multiple_times(self, db_session):
        """Adding mastery XP multiple times should accumulate"""
        user = User(
            id="test-mastery-xp-3",
            email="test3@example.com",
            username="testuser3",
            hashed_password="hashed",
            mastery_xp=0,
            mastery_level="入门",
        )
        db_session.add(user)
        await db_session.commit()

        # Add XP multiple times
        await profile_service.add_mastery_xp(db_session, user, 100)  # 100 -> 学习
        assert user.mastery_xp == 100
        assert user.mastery_level == "学习"

        await profile_service.add_mastery_xp(db_session, user, 200)  # 300 -> 练习
        assert user.mastery_xp == 300
        assert user.mastery_level == "练习"

        await profile_service.add_mastery_xp(db_session, user, 300)  # 600 -> 熟练
        assert user.mastery_xp == 600
        assert user.mastery_level == "熟练"

        await profile_service.add_mastery_xp(db_session, user, 400)  # 1000 -> 精通
        assert user.mastery_xp == 1000
        assert user.mastery_level == "精通"


class TestMasteryXpNotAffectUserXp:
    """Test that mastery XP does not affect user XP"""

    @pytest.mark.asyncio
    async def test_add_mastery_xp_not_affect_user_xp(self, db_session):
        """Adding mastery XP should NOT affect user.xp"""
        user = User(
            id="test-mastery-xp-4",
            email="test4@example.com",
            username="testuser4",
            hashed_password="hashed",
            xp=100,
            mastery_xp=0,
            mastery_level="入门",
        )
        db_session.add(user)
        await db_session.commit()

        result = await profile_service.add_mastery_xp(db_session, user, 50)
        assert result.xp == 100  # User XP should remain unchanged
        assert result.mastery_xp == 50  # Mastery XP should increase

"""Tests for Learning Profile API"""

import pytest


@pytest.mark.asyncio
class TestProfileEndpoints:
    """Test profile endpoints"""

    async def test_get_my_profile_requires_auth(self, client):
        """Should require authentication"""
        response = await client.get("/api/users/me/profile")
        assert response.status_code == 401

    async def test_get_my_profile_returns_data(self, client, auth_headers):
        """Should return user profile data"""
        response = await client.get("/api/users/me/profile", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "xp" in data
        assert "mastery_xp" in data  # New field
        assert "mastery_level" in data  # New field
        assert "streak_days" in data
        assert "preferred_languages" in data
        assert "total_exercises" in data
        assert "accuracy_rate" in data

    async def test_update_profile(self, client, auth_headers):
        """Should update profile preferences"""
        response = await client.put(
            "/api/users/me/profile",
            headers=auth_headers,
            json={"preferred_languages": ["Python", "C++"]}
        )
        assert response.status_code == 200
        assert response.json()["preferred_languages"] == ["Python", "C++"]

    async def test_add_xp(self, client, auth_headers):
        """Should add XP"""
        initial = await client.get("/api/users/me/profile", headers=auth_headers)
        initial_xp = initial.json()["xp"]

        response = await client.post(
            "/api/users/me/xp?xp_amount=50",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["xp"] == initial_xp + 50
        assert "mastery_xp" in data
        assert "mastery_level" in data


@pytest.mark.asyncio
class TestProfileService:
    """Test profile service logic"""

    async def test_add_xp_increments_xp(self, db_session, auth_user):
        """Should increment XP"""
        from app.services.profile import profile_service

        auth_user.xp = 0
        await db_session.commit()

        await profile_service.add_xp(db_session, auth_user, 50)
        await db_session.refresh(auth_user)

        assert auth_user.xp == 50

    async def test_update_exercise_correct(self, db_session, auth_user):
        """Should update exercise statistics for correct answer"""
        from app.services.profile import profile_service

        auth_user.total_exercises = 0
        auth_user.correct_exercises = 0
        await db_session.commit()

        await profile_service.update_exercise_result(db_session, auth_user, True)
        await db_session.refresh(auth_user)

        assert auth_user.total_exercises == 1
        assert auth_user.correct_exercises == 1
        assert auth_user.accuracy_rate == 100.0

    async def test_update_exercise_incorrect(self, db_session, auth_user):
        """Should update exercise statistics for incorrect answer"""
        from app.services.profile import profile_service

        auth_user.total_exercises = 0
        auth_user.correct_exercises = 0
        await db_session.commit()

        await profile_service.update_exercise_result(db_session, auth_user, False)
        await db_session.refresh(auth_user)

        assert auth_user.total_exercises == 1
        assert auth_user.correct_exercises == 0
        assert auth_user.accuracy_rate == 0.0

    async def test_set_preferred_languages(self, db_session, auth_user):
        """Should set preferred languages"""
        from app.services.profile import profile_service

        await profile_service.set_preferred_languages(
            db_session, auth_user, ["Python", "JavaScript"]
        )
        await db_session.refresh(auth_user)

        assert auth_user.preferred_languages == ["Python", "JavaScript"]

    async def test_mastery_xp_separate_from_user_xp(self, db_session, auth_user):
        """Mastery XP should be separate from user XP"""
        from app.services.profile import profile_service

        auth_user.xp = 100
        auth_user.mastery_xp = 0
        await db_session.commit()

        # Add mastery XP
        await profile_service.add_mastery_xp(db_session, auth_user, 50)
        await db_session.refresh(auth_user)

        # User XP should remain unchanged
        assert auth_user.xp == 100
        # Mastery XP should increase
        assert auth_user.mastery_xp == 50

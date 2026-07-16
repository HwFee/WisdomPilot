"""Tests for Challenge API endpoints"""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
class TestChallengeList:
    """Test GET /api/challenges endpoint"""

    async def test_get_challenges_returns_list(self, client):
        """Should return a list of challenges (may be empty)"""
        response = await client.get("/api/challenges")
        assert response.status_code == 200

        data = response.json()
        assert "challenges" in data
        assert "total" in data
        assert isinstance(data["challenges"], list)

    async def test_get_challenges_empty_db(self, client):
        """Should return empty list when no challenges exist"""
        response = await client.get("/api/challenges")
        assert response.status_code == 200
        assert response.json()["challenges"] == []


@pytest.mark.asyncio
class TestChallengeDetail:
    """Test GET /api/challenges/{id} endpoint"""

    async def test_get_challenge_returns_404_for_empty_db(self, client):
        """Should return 404 when challenge not found"""
        response = await client.get("/api/challenges/99999")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestUserChallenges:
    """Test user challenge endpoints"""

    async def test_get_my_challenges_requires_auth(self, client):
        """Should require authentication"""
        response = await client.get("/api/challenges/user/me")
        assert response.status_code == 401

    async def test_get_my_challenges_returns_list(self, client, auth_headers):
        """Should return user's challenges"""
        response = await client.get("/api/challenges/user/me", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "challenges" in data
        assert "total" in data
        assert "completed_count" in data


@pytest.mark.asyncio
class TestChallengeStart:
    """Test POST /api/challenges/{id}/start endpoint"""

    async def test_start_challenge_requires_auth(self, client):
        """Should require authentication"""
        response = await client.post("/api/challenges/1/start")
        assert response.status_code == 401

    async def test_start_challenge_400_for_nonexistent(self, client, auth_headers):
        """Should return 400 for nonexistent challenge"""
        response = await client.post(
            "/api/challenges/99999/start",
            headers=auth_headers,
        )
        assert response.status_code == 400


@pytest.mark.asyncio
class TestChallengeProgress:
    """Test POST /api/challenges/{id}/progress endpoint"""

    async def test_update_progress_requires_auth(self, client):
        """Should require authentication"""
        response = await client.post("/api/challenges/1/progress")
        assert response.status_code == 401

    async def test_update_progress_400_if_not_started(self, client, auth_headers):
        """Should return 400 if challenge not started"""
        response = await client.post(
            "/api/challenges/1/progress",
            headers=auth_headers,
        )
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_progress_rejects_non_positive_query_values(client, auth_headers):
    for progress in (0, -1):
        response = await client.post(
            f"/api/challenges/99999/progress?progress={progress}",
            headers=auth_headers,
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_unexpected_start_value_error_is_not_mapped_to_bad_request(
    client, auth_headers
):
    with patch(
        "app.routers.challenges.challenge_service.start_challenge",
        new=AsyncMock(side_effect=ValueError("unexpected storage failure")),
    ):
        with pytest.raises(ValueError, match="unexpected storage failure"):
            await client.post("/api/challenges/1/start", headers=auth_headers)


@pytest.mark.asyncio
class TestChallengeService:
    """Test challenge service logic"""

    async def test_create_default_challenges(self, db_session):
        """Should create default challenges"""
        from app.services.challenge import challenge_service

        await challenge_service.create_default_challenges(db_session)

        challenges = await challenge_service.get_active_challenges(db_session)
        assert len(challenges) == 3
        codes = [c.code for c in challenges]
        assert "FIRST_STEPS" in codes
        assert "CHAPTER_MASTER" in codes
        assert "STREAK_7" in codes

    async def test_start_challenge_creates_user_challenge(self, db_session, auth_user):
        """Should create user challenge when started"""
        from app.services.challenge import challenge_service

        await challenge_service.create_default_challenges(db_session)
        challenges = await challenge_service.get_active_challenges(db_session)
        first_steps = next(c for c in challenges if c.code == "FIRST_STEPS")

        user_challenge = await challenge_service.start_challenge(
            db_session, auth_user, first_steps.id
        )

        assert user_challenge.challenge_id == first_steps.id
        assert user_challenge.user_id == auth_user.id
        assert user_challenge.status == "in_progress"
        assert user_challenge.current_progress == 0

    async def test_update_progress_increments(self, db_session, auth_user):
        """Should increment progress"""
        from app.services.challenge import challenge_service

        await challenge_service.create_default_challenges(db_session)
        challenges = await challenge_service.get_active_challenges(db_session)
        first_steps = next(c for c in challenges if c.code == "FIRST_STEPS")

        await challenge_service.start_challenge(db_session, auth_user, first_steps.id)

        user_challenge = await challenge_service.update_progress(
            db_session, auth_user, first_steps.id, 3
        )

        assert user_challenge.current_progress == 3
        assert user_challenge.status == "in_progress"

    async def test_complete_challenge_when_target_reached(self, db_session, auth_user):
        """Should mark as completed when target reached"""
        from app.services.challenge import challenge_service

        await challenge_service.create_default_challenges(db_session)
        challenges = await challenge_service.get_active_challenges(db_session)
        first_steps = next(c for c in challenges if c.code == "FIRST_STEPS")

        await challenge_service.start_challenge(db_session, auth_user, first_steps.id)
        user_challenge = await challenge_service.update_progress(
            db_session, auth_user, first_steps.id, 5
        )

        assert user_challenge.status == "completed"
        assert user_challenge.completed_at is not None

    async def test_complete_challenge_grants_quota_bonus(self, db_session, auth_user):
        """Should grant quota bonus when challenge completed"""
        from app.services.challenge import challenge_service

        initial_cores = auth_user.cores

        await challenge_service.create_default_challenges(db_session)
        challenges = await challenge_service.get_active_challenges(db_session)
        first_steps = next(c for c in challenges if c.code == "FIRST_STEPS")

        await challenge_service.start_challenge(db_session, auth_user, first_steps.id)
        await challenge_service.update_progress(db_session, auth_user, first_steps.id, 5)

        await db_session.refresh(auth_user)
        # FIRST_STEPS has quota_bonus of 10
        assert auth_user.cores == initial_cores + 10

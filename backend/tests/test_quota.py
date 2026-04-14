"""Tests for AI Quota System"""

import pytest
from datetime import datetime, timedelta


@pytest.mark.asyncio
class TestQuotaEndpoints:
    """Test admin quota management endpoints"""

    async def test_get_quota_returns_quota_info(self, client, admin_auth_headers, auth_user):
        """Admin should be able to get user quota info"""
        response = await client.get(
            f"/api/admin/users/{auth_user.id}/quota",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "quota_remaining" in data
        assert "quota_reset_at" in data
        assert "is_admin" in data
        assert data["is_admin"] is False

    async def test_get_quota_404_for_nonexistent_user(self, client, admin_auth_headers):
        """Should return 404 for nonexistent user"""
        response = await client.get(
            "/api/admin/users/nonexistent-id/quota",
            headers=admin_auth_headers,
        )
        assert response.status_code == 404

    async def test_set_quota_updates_amount(self, client, admin_auth_headers, auth_user):
        """Admin should be able to set user quota to specific amount"""
        response = await client.put(
            f"/api/admin/users/{auth_user.id}/quota?amount=50",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["quota"] == 50

        # Verify it persisted
        response = await client.get(
            f"/api/admin/users/{auth_user.id}/quota",
            headers=admin_auth_headers,
        )
        assert response.json()["quota_remaining"] == 50

    async def test_reset_quota_restores_default(self, client, admin_auth_headers, auth_user):
        """Admin should be able to reset user quota to default"""
        # First set a low quota
        await client.put(
            f"/api/admin/users/{auth_user.id}/quota?amount=5",
            headers=admin_auth_headers,
        )

        # Then reset
        response = await client.post(
            f"/api/admin/users/{auth_user.id}/quota/reset?amount=100",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["quota"] == 100

    async def test_quota_endpoints_require_admin(self, client, auth_headers, auth_user):
        """Quota endpoints should require admin privileges"""
        response = await client.get(
            f"/api/admin/users/{auth_user.id}/quota",
            headers=auth_headers,
        )
        assert response.status_code == 403


@pytest.mark.asyncio
class TestQuotaService:
    """Test quota service logic"""

    async def test_quota_deducts_correctly(self, db_session, auth_user):
        """Quota should be deducted when sufficient"""
        from app.services.quota import quota_service

        # Set quota to known value
        auth_user.ai_quota = 10
        await db_session.commit()

        result = await quota_service.deduct_quota(auth_user, db_session, cost=1)
        assert result is True
        await db_session.refresh(auth_user)
        assert auth_user.ai_quota == 9

    async def test_quota_fails_when_insufficient(self, db_session, auth_user):
        """Quota deduction should fail when insufficient"""
        from app.services.quota import quota_service

        auth_user.ai_quota = 0
        await db_session.commit()

        result = await quota_service.deduct_quota(auth_user, db_session, cost=1)
        assert result is False

    async def test_admin_bypasses_quota_check(self, db_session, admin_user):
        """Admin should never run out of quota"""
        from app.services.quota import quota_service

        admin_user.ai_quota = 0
        await db_session.commit()

        has_quota = await quota_service.check_quota(admin_user, db_session)
        assert has_quota is True

        result = await quota_service.deduct_quota(admin_user, db_session, cost=1)
        assert result is True

    async def test_get_quota_returns_correct_structure(self, db_session, auth_user):
        """get_quota should return proper structure"""
        from app.services.quota import quota_service

        result = await quota_service.get_quota(auth_user, db_session)
        assert "quota_remaining" in result
        assert "quota_reset_at" in result
        assert "is_admin" in result
        assert result["is_admin"] is False

"""Tests for rate limiting middleware (C5, C8)"""

import time
import pytest

from app.config import get_settings


class TestRateLimiter:
    """Unit tests for the in-memory rate limiter (sync, no app needed)"""

    def test_is_allowed_under_limit(self):
        """Requests under limit should be allowed"""
        from app.middleware import RateLimiter

        limiter = RateLimiter(max_requests=3, window_seconds=60)
        for i in range(3):
            assert limiter.is_allowed("test-ip") is True

    def test_is_allowed_over_limit(self):
        """Requests over limit should be denied"""
        from app.middleware import RateLimiter

        limiter = RateLimiter(max_requests=2, window_seconds=60)
        assert limiter.is_allowed("test-ip") is True
        assert limiter.is_allowed("test-ip") is True
        assert limiter.is_allowed("test-ip") is False

    def test_sliding_window_purges_old_entries(self):
        """Entries older than window should be purged"""
        from app.middleware import RateLimiter

        limiter = RateLimiter(max_requests=2, window_seconds=1)
        assert limiter.is_allowed("test-ip") is True
        assert limiter.is_allowed("test-ip") is True
        assert limiter.is_allowed("test-ip") is False

        # Wait for window to expire
        time.sleep(1.1)

        assert limiter.is_allowed("test-ip") is True

    def test_separate_ips_tracked_independently(self):
        """Different IPs should have independent limits"""
        from app.middleware import RateLimiter

        limiter = RateLimiter(max_requests=1, window_seconds=60)
        assert limiter.is_allowed("ip-a") is True
        assert limiter.is_allowed("ip-a") is False
        assert limiter.is_allowed("ip-b") is True


class TestAuthRateLimitIntegration:
    """Integration tests for auth endpoint rate limiting (C5)"""

    @pytest.fixture(autouse=True)
    def _reset_limiters(self, setup_database):
        """Reset limiter state between tests to avoid cross-test pollution."""
        import app.middleware as mw

        mw.reset_rate_limiters()
        yield

    @pytest.mark.asyncio
    async def test_auth_rate_limit_blocks_after_threshold(self):
        """Requests beyond AUTH_RATE_PER_MINUTE should return 429"""
        import importlib
        import app.middleware as mw
        import app.main as main

        # Ensure middleware is loaded with fresh limiters
        importlib.reload(mw)
        importlib.reload(main)

        from httpx import AsyncClient, ASGITransport

        transport = ASGITransport(app=main.app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            settings = get_settings()
            limit = settings.AUTH_RATE_PER_MINUTE
            for i in range(limit):
                response = await ac.post(
                    "/api/auth/login",
                    json={
                        "email": f"ratelimit{i}@example.com",
                        "password": "password123",
                    },
                )
                assert response.status_code != 429, (
                    f"Request {i + 1} should not be rate limited yet"
                )

            response = await ac.post(
                "/api/auth/login",
                json={
                    "email": "ratelimit-extra@example.com",
                    "password": "password123",
                },
            )
            assert response.status_code == 429
            assert "Rate limit exceeded" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_auth_rate_limit_applies_to_forgot_password(self):
        """Forgot password endpoint should also be rate limited"""
        import importlib
        import app.middleware as mw
        import app.main as main

        importlib.reload(mw)
        importlib.reload(main)

        from httpx import AsyncClient, ASGITransport

        transport = ASGITransport(app=main.app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            settings = get_settings()
            limit = settings.AUTH_RATE_PER_MINUTE
            for i in range(limit):
                response = await ac.post(
                    "/api/auth/forgot-password",
                    json={"email": f"reset{i}@example.com"},
                )
                assert response.status_code != 429

            response = await ac.post(
                "/api/auth/forgot-password",
                json={"email": "reset-extra@example.com"},
            )
            assert response.status_code == 429


class TestCodeExecRateLimitIntegration:
    """Integration tests for code execution rate limiting (C8)"""

    @pytest.fixture(autouse=True)
    def _reset_limiters(self):
        """Reset limiter state between tests."""
        import importlib
        import app.middleware as mw

        importlib.reload(mw)
        mw.reset_rate_limiters()
        yield

    @pytest.mark.asyncio
    async def test_code_exec_rate_limit_blocks_after_threshold(self):
        """Code exec requests beyond CODE_EXEC_RATE_PER_MINUTE should return 429.

        Rate limiting hits BEFORE auth, so even unauth'd requests count.
        """
        import importlib
        import app.middleware as mw
        import app.main as main

        importlib.reload(mw)
        importlib.reload(main)

        from httpx import AsyncClient, ASGITransport

        transport = ASGITransport(app=main.app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            settings = get_settings()
            limit = settings.CODE_EXEC_RATE_PER_MINUTE
            for i in range(limit):
                response = await ac.post(
                    "/api/code/execute",
                    json={"language_id": 71, "code": "print(1)"},
                )
                # Could be 401 (auth) or 500, but NOT 429
                assert response.status_code != 429, (
                    f"Request {i + 1} should not be rate limited yet"
                )

            response = await ac.post(
                "/api/code/execute",
                json={"language_id": 71, "code": "print(1)"},
            )
            assert response.status_code == 429
            assert "Rate limit exceeded" in response.json()["detail"]

"""Tests for validation error handling in auth endpoints.

TDD: Tests written FIRST to define expected behavior.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    """Create async test client"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


class TestRegistrationValidationErrors:
    """Test registration validation error messages are user-friendly."""

    @pytest.mark.asyncio
    async def test_password_too_short_returns_friendly_message(self, client: AsyncClient):
        """密码太短应返回友好的中文错误提示"""
        response = await client.post("/api/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "abc123"  # Only 6 characters
        })
        assert response.status_code == 422
        data = response.json()
        # 应该返回字符串
        assert "detail" in data
        detail = data["detail"]
        assert isinstance(detail, str), f"Expected string, got {type(detail)}: {detail}"
        assert "8" in detail or "字符" in detail

    @pytest.mark.asyncio
    async def test_password_missing_letter_returns_friendly_message(self, client: AsyncClient):
        """密码缺少字母应返回友好提示"""
        response = await client.post("/api/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "12345678"  # Only numbers, no letter
        })
        assert response.status_code == 422
        data = response.json()
        detail = data["detail"]
        assert isinstance(detail, str)
        assert "字母" in detail

    @pytest.mark.asyncio
    async def test_password_missing_digit_returns_friendly_message(self, client: AsyncClient):
        """密码缺少数字应返回友好提示"""
        response = await client.post("/api/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "abcdefgh"  # Only letters, no digit
        })
        assert response.status_code == 422
        data = response.json()
        detail = data["detail"]
        assert isinstance(detail, str)
        assert "数字" in detail

    @pytest.mark.asyncio
    async def test_invalid_email_returns_friendly_message(self, client: AsyncClient):
        """无效邮箱应返回友好提示"""
        response = await client.post("/api/auth/register", json={
            "email": "not-an-email",
            "username": "testuser",
            "password": "abc12345"
        })
        assert response.status_code == 422
        data = response.json()
        detail = data["detail"]
        assert isinstance(detail, str)
        assert "邮箱" in detail

    @pytest.mark.asyncio
    async def test_multiple_password_errors_combined(self, client: AsyncClient):
        """多个密码错误应该合并显示"""
        response = await client.post("/api/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "ab"  # Too short, missing digit
        })
        assert response.status_code == 422
        data = response.json()
        detail = data["detail"]
        assert isinstance(detail, str)
        # 应该包含至少一个错误
        assert "字符" in detail or "数字" in detail or "字母" in detail


class TestLoginValidationErrors:
    """Test login validation error messages."""

    @pytest.mark.asyncio
    async def test_invalid_email_format_returns_friendly_message(self, client: AsyncClient):
        """登录时无效邮箱应返回友好提示"""
        response = await client.post("/api/auth/login", json={
            "email": "not-an-email",
            "password": "somepassword"
        })
        assert response.status_code == 422
        data = response.json()
        detail = data["detail"]
        assert isinstance(detail, str)
        assert "邮箱" in detail


class TestErrorResponseFormat:
    """Test error response format is consistent."""

    @pytest.mark.asyncio
    async def test_error_detail_is_string_not_object(self, client: AsyncClient):
        """错误详情应该是字符串，不是对象"""
        response = await client.post("/api/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "12345678"  # Missing letter
        })
        assert response.status_code == 422
        data = response.json()
        # detail 应该是字符串，前端可以直接显示
        assert "detail" in data
        detail = data["detail"]
        assert isinstance(detail, str), f"Expected string, got {type(detail)}: {detail}"

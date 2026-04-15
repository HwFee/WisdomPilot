import pytest
from httpx import AsyncClient
from app.models import User


class TestAuthRegister:
    """Test user registration endpoint"""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration"""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "password123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["username"] == "testuser"
        assert "id" in data["user"]

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient):
        """Test registration with duplicate email fails"""
        # First registration
        await client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "username": "user1",
                "password": "password123",
            },
        )
        # Second registration with same email
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "username": "user2",
                "password": "password123",
            },
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient):
        """Test registration with duplicate username fails"""
        # First registration
        await client.post(
            "/api/auth/register",
            json={
                "email": "user1@example.com",
                "username": "duplicateuser",
                "password": "password123",
            },
        )
        # Second registration with same username
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "user2@example.com",
                "username": "duplicateuser",
                "password": "password123",
            },
        )
        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email format fails"""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "invalid-email",
                "username": "testuser",
                "password": "password123",
            },
        )
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: AsyncClient):
        """Test registration with short password fails"""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "short",
            },
        )
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_password_without_letter(self, client: AsyncClient):
        """Test registration with password without letter fails"""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "12345678",
            },
        )
        assert response.status_code == 422
        # Check for either English or Chinese error message
        response_str = str(response.json())
        assert "letter" in response_str.lower() or "字母" in response_str

    @pytest.mark.asyncio
    async def test_register_password_without_digit(self, client: AsyncClient):
        """Test registration with password without digit fails"""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "abcdefgh",
            },
        )
        assert response.status_code == 422
        # Check for either English or Chinese error message
        response_str = str(response.json())
        assert "digit" in response_str.lower() or "数字" in response_str


class TestAuthLogin:
    """Test user login endpoint"""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """Test successful login"""
        # Register first
        await client.post(
            "/api/auth/register",
            json={
                "email": "login@example.com",
                "username": "loginuser",
                "password": "password123",
            },
        )
        # Login
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "login@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "login@example.com"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        """Test login with wrong password fails"""
        # Register first
        await client.post(
            "/api/auth/register",
            json={
                "email": "wrong@example.com",
                "username": "wronguser",
                "password": "password123",
            },
        )
        # Login with wrong password
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "wrong@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user fails"""
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]


class TestAuthMe:
    """Test get current user endpoint"""

    @pytest.mark.asyncio
    async def test_get_me_authenticated(self, client: AsyncClient):
        """Test getting current user info when authenticated"""
        # Register
        register_response = await client.post(
            "/api/auth/register",
            json={
                "email": "me@example.com",
                "username": "meuser",
                "password": "password123",
            },
        )
        token = register_response.json()["access_token"]

        # Get current user
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["username"] == "meuser"

    @pytest.mark.asyncio
    async def test_get_me_unauthenticated(self, client: AsyncClient):
        """Test getting current user info without token fails"""
        response = await client.get("/api/auth/me")
        assert response.status_code == 401  # No credentials - HTTPBearer returns 401

    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self, client: AsyncClient):
        """Test getting current user info with invalid token fails"""
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401


class TestAuthForgotPassword:
    """Test forgot-password endpoint (C6 - user enumeration prevention)"""

    @pytest.mark.asyncio
    async def test_forgot_password_existing_user(self, client: AsyncClient):
        """Forgot password for existing user returns 200"""
        # Register first
        await client.post(
            "/api/auth/register",
            json={
                "email": "existing@example.com",
                "username": "existinguser",
                "password": "password123",
            },
        )
        response = await client.post(
            "/api/auth/forgot-password",
            json={"email": "existing@example.com"},
        )
        assert response.status_code == 200
        assert "If an account exists" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_forgot_password_nonexistent_user(self, client: AsyncClient):
        """Forgot password for non-existent user returns 200 (same as existing user).

        This prevents user enumeration -- an attacker cannot determine whether
        an email is registered by observing different responses.
        """
        response = await client.post(
            "/api/auth/forgot-password",
            json={"email": "nonexistent-user-xyz@example.com"},
        )
        assert response.status_code == 200
        assert "If an account exists" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_forgot_password_same_response(self, client: AsyncClient):
        """Both existing and non-existing emails return identical response text."""
        # Register a user
        await client.post(
            "/api/auth/register",
            json={
                "email": "sameresp@example.com",
                "username": "samerespuser",
                "password": "password123",
            },
        )
        resp_existing = await client.post(
            "/api/auth/forgot-password",
            json={"email": "sameresp@example.com"},
        )
        resp_nonexistent = await client.post(
            "/api/auth/forgot-password",
            json={"email": "does-not-exist@example.com"},
        )
        assert resp_existing.status_code == resp_nonexistent.status_code == 200
        assert resp_existing.json() == resp_nonexistent.json()

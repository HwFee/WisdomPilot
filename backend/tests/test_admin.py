import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models import User
from app.utils.security import get_password_hash


@pytest.fixture
async def regular_user(db_session: AsyncSession):
    """Create a regular test user"""
    user = User(
        email="user@test.com",
        username="testuser",
        hashed_password=get_password_hash("Password123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_user(db_session: AsyncSession):
    """Create an admin test user"""
    user = User(
        email="admin@test.com",
        username="adminuser",
        hashed_password=get_password_hash("AdminPass123"),
        is_active=True,
        is_admin=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def user_token(regular_user: User):
    """Get token for regular user"""
    from app.utils.security import create_access_token
    from datetime import timedelta
    from app.config import get_settings
    settings = get_settings()
    return create_access_token(
        data={"sub": regular_user.id, "email": regular_user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


@pytest.fixture
async def admin_token(admin_user: User):
    """Get token for admin user"""
    from app.utils.security import create_access_token
    from datetime import timedelta
    from app.config import get_settings
    settings = get_settings()
    return create_access_token(
        data={"sub": admin_user.id, "email": admin_user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


class TestAdminListUsers:
    """Tests for admin user listing"""

    @pytest.mark.asyncio
    async def test_admin_can_list_users(self, admin_user, admin_token):
        """Admin should be able to list all users"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/admin/users",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_regular_user_cannot_list_users(self, regular_user, user_token):
        """Regular user should not access admin endpoint"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/admin/users",
                headers={"Authorization": f"Bearer {user_token}"}
            )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_list_users(self):
        """Unauthenticated request should be rejected"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/admin/users")
        assert response.status_code == 401


class TestAdminDeleteUser:
    """Tests for admin user deletion"""

    @pytest.mark.asyncio
    async def test_admin_can_delete_user(self, admin_user, admin_token, regular_user):
        """Admin should be able to delete a user"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(
                f"/api/admin/users/{regular_user.id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_regular_user_cannot_delete_user(self, regular_user, user_token, db_session):
        """Regular user should not delete users"""
        # Create another user to delete
        other_user = User(
            email="other@test.com",
            username="otheruser",
            hashed_password=get_password_hash("Password123"),
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.commit()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(
                f"/api/admin/users/{other_user.id}",
                headers={"Authorization": f"Bearer {user_token}"}
            )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_nonexistent_user(self, admin_user, admin_token):
        """Deleting non-existent user returns 404"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(
                "/api/admin/users/nonexistent-id",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
        assert response.status_code == 404


class TestAdminOnlineUsers:
    """Tests for online user listing"""

    @pytest.mark.asyncio
    async def test_admin_can_list_online_users(self, admin_user, admin_token):
        """Admin should be able to see online users"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/admin/users/online",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_regular_user_cannot_list_online_users(self, regular_user, user_token):
        """Regular user should not see online users"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/admin/users/online",
                headers={"Authorization": f"Bearer {user_token}"}
            )
        assert response.status_code == 403

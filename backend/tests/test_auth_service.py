import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.schemas import UserCreate, UserLogin
from app.services.auth import AuthService
from app.services.auth_errors import (
    EmailAlreadyRegisteredError,
    InactiveAccountError,
    InvalidCredentialsError,
    UsernameAlreadyRegisteredError,
)


@pytest.mark.asyncio
async def test_register_duplicate_email_raises_typed_error(
    db_session: AsyncSession, auth_user: User
) -> None:
    service = AuthService(db_session)
    request = UserCreate(
        email=auth_user.email,
        username="differentuser",
        password="Password123",
    )

    with pytest.raises(EmailAlreadyRegisteredError, match="该邮箱已被注册"):
        await service.register(request)


@pytest.mark.asyncio
async def test_register_duplicate_username_raises_typed_error(
    db_session: AsyncSession, auth_user: User
) -> None:
    service = AuthService(db_session)
    request = UserCreate(
        email="different@example.com",
        username=auth_user.username,
        password="Password123",
    )

    with pytest.raises(UsernameAlreadyRegisteredError, match="该用户名已被使用"):
        await service.register(request)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("identifier", "password"),
    [("missing@example.com", "Password123"), ("auth@test.com", "WrongPass123")],
)
async def test_login_rejects_unknown_user_and_wrong_password_identically(
    db_session: AsyncSession,
    auth_user: User,
    identifier: str,
    password: str,
) -> None:
    service = AuthService(db_session)

    with pytest.raises(InvalidCredentialsError, match="用户名或密码错误"):
        await service.login(UserLogin(username=identifier, password=password))


@pytest.mark.asyncio
async def test_login_inactive_account_raises_typed_error(
    db_session: AsyncSession, auth_user: User
) -> None:
    auth_user.is_active = False
    await db_session.commit()
    service = AuthService(db_session)

    with pytest.raises(InactiveAccountError, match="Account is inactive"):
        await service.login(
            UserLogin(username=auth_user.email, password="Password123")
        )


@pytest.mark.asyncio
async def test_forgot_password_unknown_email_returns_normally(
    db_session: AsyncSession,
) -> None:
    service = AuthService(db_session)

    assert await service.forgot_password("missing@example.com") is None

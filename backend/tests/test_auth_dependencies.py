import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.dependencies import (
    _find_user_from_credentials,
    get_current_active_user,
    get_current_user,
)
from app.auth.security import create_access_token


def bearer_credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


@pytest.mark.asyncio
async def test_shared_resolver_returns_token_user(
    db_session: AsyncSession, auth_user: User
) -> None:
    credentials = bearer_credentials(create_access_token({"sub": auth_user.id}))

    resolved_user = await _find_user_from_credentials(credentials, db_session)

    assert resolved_user is auth_user


@pytest.mark.asyncio
async def test_required_user_rejects_invalid_token(db_session: AsyncSession) -> None:
    credentials = bearer_credentials("invalid-token")

    with pytest.raises(HTTPException) as exception_info:
        await get_current_user(credentials, db_session)

    assert exception_info.value.status_code == 401
    assert exception_info.value.detail == "Could not validate credentials"
    assert exception_info.value.headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "token",
    [create_access_token({}), create_access_token({"sub": "missing-user-id"})],
)
async def test_required_user_rejects_unresolvable_subject(
    db_session: AsyncSession, token: str
) -> None:
    with pytest.raises(HTTPException) as exception_info:
        await get_current_user(bearer_credentials(token), db_session)

    assert exception_info.value.status_code == 401
    assert exception_info.value.detail == "Could not validate credentials"
    assert exception_info.value.headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.asyncio
async def test_current_user_does_not_check_active_state(
    db_session: AsyncSession, auth_user: User
) -> None:
    """get_current_user 只解析身份，不检查激活状态（由上层依赖负责）。"""
    auth_user.is_active = False
    await db_session.commit()
    credentials = bearer_credentials(create_access_token({"sub": auth_user.id}))

    resolved_user = await get_current_user(credentials, db_session)

    assert resolved_user is auth_user
    assert resolved_user.is_active is False


@pytest.mark.asyncio
async def test_active_user_dependency_rejects_inactive_user(
    db_session: AsyncSession, auth_user: User
) -> None:
    """激活用户依赖：账户停用返回 403。"""
    auth_user.is_active = False
    await db_session.commit()
    credentials = bearer_credentials(create_access_token({"sub": auth_user.id}))

    with pytest.raises(HTTPException) as exception_info:
        await get_current_active_user(await get_current_user(credentials, db_session))

    assert exception_info.value.status_code == 403
    assert exception_info.value.detail == "User account is inactive"


@pytest.mark.asyncio
async def test_active_user_dependency_accepts_active_user(
    db_session: AsyncSession, auth_user: User
) -> None:
    """激活用户依赖：激活用户直接放行。"""
    credentials = bearer_credentials(create_access_token({"sub": auth_user.id}))

    current_user = await get_current_user(credentials, db_session)
    assert await get_current_active_user(current_user) is auth_user

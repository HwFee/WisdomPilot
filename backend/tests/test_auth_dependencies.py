from typing import cast

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


class UserWhoseActiveStateMustNotBeRead:
    @property
    def is_active(self) -> bool:
        raise AssertionError("active state was checked twice")


@pytest.mark.asyncio
async def test_active_compatibility_dependency_does_not_recheck_state() -> None:
    current_user = cast(User, UserWhoseActiveStateMustNotBeRead())

    assert await get_current_active_user(current_user) is current_user

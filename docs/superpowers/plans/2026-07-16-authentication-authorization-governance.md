# Authentication And Authorization Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace ambiguous authentication failures and duplicated authorization checks with typed authentication errors and one request dependency chain while preserving established API contracts.

**Architecture:** `AuthService` raises authentication-specific exceptions without importing FastAPI, and `routers/auth.py` maps those exceptions to the existing HTTP contract. `utils/deps.py` owns bearer-token resolution and active/admin checks through one shared resolver; endpoint-wide admin gates use `get_current_admin_user`, while object-level owner-or-admin rules remain in their business endpoints.

**Tech Stack:** Python 3.10, FastAPI, SQLAlchemy async ORM, python-jose, pytest, pytest-asyncio, HTTPX, Pyright.

## Global Constraints

- Preserve registration, login, forgot-password, and `/api/auth/me` successful response schemas.
- Preserve JWT algorithms, claims, expiry rules, and password hashing behavior.
- Preserve registration conflict and login failure status codes and response text.
- Normalize endpoint-wide administrator rejection to HTTP 403 with `Admin access required`.
- Do not modify frontend code, database schema, migrations, admin CRUD, quota algorithms, AI configuration, or course business behavior.
- Keep object-level "owner or admin" and "admin may announce" checks in `routers/solutions.py`; they are not endpoint-wide admin gates.
- Fix only behavior demonstrated by a failing regression test or an explicit contract test.
- Run focused tests, the complete backend suite with zero skips, Pyright, FastAPI startup, Next.js startup, affected live routes, CodeGraph synchronization, and the project quality checklist before completion.

---

## File Structure

- Create `backend/app/services/auth_errors.py`: FastAPI-independent authentication error types and stable messages.
- Modify `backend/app/services/auth.py`: raise typed errors, remove sensitive debug metadata, and make forgot-password enumeration-safe at the service boundary.
- Modify `backend/app/routers/auth.py`: map only known authentication errors to HTTP responses.
- Modify `backend/app/utils/deps.py`: share token/user resolution and define the single active/admin dependency chain.
- Modify `backend/app/routers/admin.py`: remove the local admin dependency.
- Modify `backend/app/routers/courses.py`: move `/api/courses/init` to the central admin dependency.
- Create `backend/tests/test_auth_service.py`: direct service error-contract tests.
- Create `backend/tests/test_auth_dependencies.py`: direct dependency and shared-resolver tests.
- Modify `backend/tests/test_auth.py`: public auth error and security contract tests.
- Modify `backend/tests/test_admin.py`: central admin rejection and inactive-admin tests.
- Modify `backend/tests/test_courses.py`: course initialization admin-boundary tests.
- Modify `docs/superpowers/specs/2026-07-15-backend-learning-oriented-governance-design.md`: completed second-batch learning record.
- Modify this plan: checked steps and completion evidence.

## Task 1: Type Authentication Service Failures

**Files:**
- Create: `backend/app/services/auth_errors.py`
- Create: `backend/tests/test_auth_service.py`
- Modify: `backend/app/services/auth.py:1-118`

**Interfaces:**
- Produces: `AuthError`, `EmailAlreadyRegisteredError`, `UsernameAlreadyRegisteredError`, `InvalidCredentialsError`, and `InactiveAccountError`.
- Preserves: `AuthService.register(UserCreate) -> tuple[User, Token]` and `AuthService.login(UserLogin) -> tuple[User, Token]`.
- Produces: `AuthService.forgot_password(email: str) -> None`, which returns normally for unknown email addresses.

- [ ] **Step 1: Add failing service contract tests**

Create `backend/tests/test_auth_service.py`:

```python
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
```

- [ ] **Step 2: Run the new module and confirm the error module is absent**

Run from `backend`:

```powershell
py -3 -m pytest tests/test_auth_service.py -q
```

Expected: collection fails with `ModuleNotFoundError: No module named 'app.services.auth_errors'`.

- [ ] **Step 3: Add the authentication-specific exception module**

Create `backend/app/services/auth_errors.py`:

```python
class AuthError(Exception):
    """Base class for expected authentication use-case failures."""


class EmailAlreadyRegisteredError(AuthError):
    def __init__(self) -> None:
        super().__init__("该邮箱已被注册")


class UsernameAlreadyRegisteredError(AuthError):
    def __init__(self) -> None:
        super().__init__("该用户名已被使用")


class InvalidCredentialsError(AuthError):
    def __init__(self) -> None:
        super().__init__("用户名或密码错误")


class InactiveAccountError(AuthError):
    def __init__(self) -> None:
        super().__init__("Account is inactive")
```

- [ ] **Step 4: Run the service tests and confirm the old `ValueError` behavior fails**

Run:

```powershell
py -3 -m pytest tests/test_auth_service.py -q
```

Expected: typed-error assertions fail because `AuthService` still raises `ValueError`; the forgot-password test also fails for the unknown address.

- [ ] **Step 5: Replace ambiguous service failures with typed errors**

Modify `backend/app/services/auth.py` as follows:

```python
from app.services.auth_errors import (
    EmailAlreadyRegisteredError,
    InactiveAccountError,
    InvalidCredentialsError,
    UsernameAlreadyRegisteredError,
)
```

Remove the password-length logging statement and replace the four `ValueError` branches:

```python
if existing_user:
    if existing_user.email == user_data.email:
        raise EmailAlreadyRegisteredError
    raise UsernameAlreadyRegisteredError

# In login:
if not user or not verify_password(login_data.password, user.hashed_password):
    raise InvalidCredentialsError

if not user.is_active:
    raise InactiveAccountError
```

Make the forgot-password branch return normally for both lookup outcomes while keeping the lookup private for the future mail-delivery integration:

```python
async def forgot_password(self, email: str) -> None:
    """Look up a reset recipient without revealing whether it exists."""
    result = await self.db.execute(select(User.id).where(User.email == email))
    if result.scalar_one_or_none() is None:
        return None

    # Password-reset delivery is not configured in this application yet.
    return None
```

Remove the now-unused `logging` import and module logger.

- [ ] **Step 6: Verify the service boundary**

Run:

```powershell
py -3 -m pytest tests/test_auth_service.py -q
pyright
```

Expected: all new service tests pass; Pyright reports `0 errors, 0 warnings, 0 informations`.

- [ ] **Step 7: Review and commit Task 1**

Run:

```powershell
git diff --check
git diff -- app/services/auth_errors.py app/services/auth.py tests/test_auth_service.py
git add app/services/auth_errors.py app/services/auth.py tests/test_auth_service.py
git commit -m "refactor: type authentication service failures"
```

Expected: only the three Task 1 files are committed.

## Task 2: Map Only Known Authentication Errors In The Router

**Files:**
- Modify: `backend/app/routers/auth.py:1-76`
- Modify: `backend/tests/test_auth.py:1-318`

**Interfaces:**
- Consumes: typed errors from Task 1.
- Preserves: registration 400 details, login 401 details, forgot-password uniform 200 response, and `/api/auth/me` response.
- Guarantees: unexpected `ValueError` is not mislabeled as a client authentication failure.

- [ ] **Step 1: Add failing Router contract tests**

Add imports to `backend/tests/test_auth.py`:

```python
from unittest.mock import AsyncMock, patch
```

Add the following tests:

```python
    @pytest.mark.asyncio
    async def test_unexpected_register_error_is_not_mapped_to_bad_request(
        self, client: AsyncClient
    ) -> None:
        with patch("app.routers.auth.AuthService") as service_class:
            service_class.return_value.register = AsyncMock(
                side_effect=ValueError("unexpected persistence failure")
            )
            with pytest.raises(ValueError, match="unexpected persistence failure"):
                await client.post(
                    "/api/auth/register",
                    json={
                        "email": "unexpected@example.com",
                        "username": "unexpecteduser",
                        "password": "Password123",
                    },
                )

    @pytest.mark.asyncio
    async def test_login_inactive_account_preserves_public_contract(
        self, client: AsyncClient, db_session
    ) -> None:
        user = User(
            email="inactive-login@example.com",
            username="inactivelogin",
            hashed_password=get_password_hash("Password123"),
            is_active=False,
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.post(
            "/api/auth/login",
            json={"username": user.email, "password": "Password123"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Account is inactive"
```

Also import `get_password_hash` from `app.utils.security`.

- [ ] **Step 2: Confirm the broad Router catch and typed service error break the tests**

Run:

```powershell
py -3 -m pytest tests/test_auth.py -q
```

Expected: the unexpected error is converted to 400 by the old broad catch, and typed authentication errors are not mapped by the Router.

- [ ] **Step 3: Map the exact typed errors and remove forgot-password exception swallowing**

Update imports in `backend/app/routers/auth.py`:

```python
from app.services.auth_errors import (
    EmailAlreadyRegisteredError,
    InactiveAccountError,
    InvalidCredentialsError,
    UsernameAlreadyRegisteredError,
)
```

Use these exact mappings:

```python
try:
    _, token = await service.register(user_data)
    return token
except (EmailAlreadyRegisteredError, UsernameAlreadyRegisteredError) as error:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(error),
    ) from error
```

```python
try:
    _, token = await service.login(login_data)
    return token
except (InvalidCredentialsError, InactiveAccountError) as error:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=str(error),
    ) from error
```

Replace the forgot-password `try/except` with:

```python
service = AuthService(db)
await service.forgot_password(request.email)
return {
    "message": (
        "If an account exists with that email, "
        "a password reset link has been sent."
    )
}
```

Remove unused logging code from the Router.

- [ ] **Step 4: Verify all authentication API contracts**

Run:

```powershell
py -3 -m pytest tests/test_auth.py tests/test_auth_service.py tests/test_rate_limit.py -q
pyright
```

Expected: all selected tests pass and Pyright remains clean.

- [ ] **Step 5: Review and commit Task 2**

Run:

```powershell
git diff --check
git diff -- app/routers/auth.py tests/test_auth.py
git add app/routers/auth.py tests/test_auth.py
git commit -m "refactor: map typed authentication errors"
```

## Task 3: Share Token Resolution And Remove The Duplicate Active Check

**Files:**
- Create: `backend/tests/test_auth_dependencies.py`
- Modify: `backend/app/utils/deps.py:1-104`

**Interfaces:**
- Produces: `_find_user_from_credentials(credentials, db) -> User | None`.
- Preserves: `get_current_user`, `get_current_active_user`, `get_current_admin_user`, `get_optional_user`, and `get_quota_user` dependency signatures.
- Produces constants: `INVALID_CREDENTIALS_DETAIL`, `INACTIVE_ACCOUNT_DETAIL`, and `ADMIN_ACCESS_REQUIRED_DETAIL`.

- [ ] **Step 1: Add failing dependency tests**

Create `backend/tests/test_auth_dependencies.py`:

```python
from typing import cast

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.utils.deps import (
    _find_user_from_credentials,
    get_current_active_user,
    get_current_user,
    get_optional_user,
)
from app.utils.security import create_access_token


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
async def test_optional_user_hides_inactive_account(
    db_session: AsyncSession, auth_user: User
) -> None:
    auth_user.is_active = False
    await db_session.commit()
    credentials = bearer_credentials(create_access_token({"sub": auth_user.id}))

    assert await get_optional_user(credentials, db_session) is None


class UserWhoseActiveStateMustNotBeRead:
    @property
    def is_active(self) -> bool:
        raise AssertionError("active state was checked twice")


@pytest.mark.asyncio
async def test_active_compatibility_dependency_does_not_recheck_state() -> None:
    current_user = cast(User, UserWhoseActiveStateMustNotBeRead())

    assert await get_current_active_user(current_user) is current_user
```

- [ ] **Step 2: Run the dependency module and confirm the shared resolver is absent**

Run:

```powershell
py -3 -m pytest tests/test_auth_dependencies.py -q
```

Expected: collection fails because `_find_user_from_credentials` does not exist.

- [ ] **Step 3: Replace duplicated dependency logic with the shared resolver**

Rewrite `backend/app/utils/deps.py` with these responsibilities:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.utils.security import decode_token

INVALID_CREDENTIALS_DETAIL = "Could not validate credentials"
INACTIVE_ACCOUNT_DETAIL = "User account is inactive"
ADMIN_ACCESS_REQUIRED_DETAIL = "Admin access required"

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


async def _find_user_from_credentials(
    credentials: HTTPAuthorizationCredentials | None,
    db: AsyncSession,
) -> User | None:
    if credentials is None:
        return None

    payload = decode_token(credentials.credentials)
    if payload is None:
        return None

    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


def _invalid_credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=INVALID_CREDENTIALS_DETAIL,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await _find_user_from_credentials(credentials, db)
    if user is None:
        raise _invalid_credentials_exception()
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=INACTIVE_ACCOUNT_DETAIL,
        )
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ADMIN_ACCESS_REQUIRED_DETAIL,
        )
    return current_user


async def get_quota_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    return current_user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_security),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    user = await _find_user_from_credentials(credentials, db)
    if user is None or not user.is_active:
        return None
    return user
```

- [ ] **Step 4: Verify dependency and broad authentication regressions**

Run:

```powershell
py -3 -m pytest tests/test_auth_dependencies.py tests/test_auth.py tests/test_ai.py tests/test_code_execution.py -q
pyright
```

Expected: all selected tests pass; Pyright reports no issues.

- [ ] **Step 5: Review and commit Task 3**

Run:

```powershell
git diff --check
git diff -- app/utils/deps.py tests/test_auth_dependencies.py
git add app/utils/deps.py tests/test_auth_dependencies.py
git commit -m "refactor: centralize authentication dependencies"
```

## Task 4: Route Endpoint-Wide Admin Gates Through One Dependency

**Files:**
- Modify: `backend/app/routers/admin.py:1-131`
- Modify: `backend/app/routers/courses.py:42-52,491-526`
- Modify: `backend/tests/test_admin.py:1-180`
- Modify: `backend/tests/test_courses.py:1-129`

**Interfaces:**
- Consumes: `get_current_admin_user` and `ADMIN_ACCESS_REQUIRED_DETAIL` from Task 3.
- Preserves: all admin CRUD, quota, and course initialization success behavior.
- Produces: one endpoint-wide admin gate for `/api/admin/*` and `POST /api/courses/init`.

- [ ] **Step 1: Add failing central-admin dependency tests**

In `backend/tests/test_admin.py`, strengthen the regular-user list assertion:

```python
assert response.status_code == 403
assert response.json()["detail"] == "Admin access required"
```

Add an inactive-admin test:

```python
    @pytest.mark.asyncio
    async def test_inactive_admin_cannot_list_users(
        self, admin_user, admin_token, db_session
    ) -> None:
        admin_user.is_active = False
        await db_session.commit()
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/admin/users",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 403
        assert response.json()["detail"] == "User account is inactive"
```

In `backend/tests/test_courses.py`, add imports:

```python
from app.main import app
from app.utils.deps import get_current_admin_user
```

Add these tests:

```python
@pytest.mark.asyncio
class TestCourseInitializationAuthorization:
    async def test_regular_user_cannot_initialize_courses(
        self, client, auth_headers
    ) -> None:
        response = await client.post("/api/courses/init", headers=auth_headers)

        assert response.status_code == 403
        assert response.json()["detail"] == "Admin access required"

    async def test_init_uses_central_admin_dependency(
        self, client, admin_user
    ) -> None:
        app.dependency_overrides[get_current_admin_user] = lambda: admin_user
        try:
            response = await client.post("/api/courses/init")
        finally:
            app.dependency_overrides.pop(get_current_admin_user, None)

        assert response.status_code == 200
        assert response.json()["message"] == "Created 8 new courses"
```

- [ ] **Step 2: Run the new contracts and confirm local gates remain**

Run:

```powershell
py -3 -m pytest tests/test_admin.py::TestAdminListUsers tests/test_courses.py::TestCourseInitializationAuthorization -q
```

Expected: admin detail is still `Admin privileges required`; the course dependency override does not bypass the inline `get_current_active_user` gate.

- [ ] **Step 3: Remove the local admin dependency from `routers/admin.py`**

Replace the dependency import with:

```python
from app.utils.deps import get_current_admin_user
```

Delete `require_admin`, then replace all six occurrences of:

```python
admin: User = Depends(require_admin)
```

with:

```python
admin: User = Depends(get_current_admin_user)
```

Do not alter endpoint bodies or their database error mappings. Remove the unused logger if it has no remaining references.

- [ ] **Step 4: Move course initialization to the central dependency**

Change only the endpoint signature and delete its inline `is_admin` block:

```python
@router.post("/init")
async def init_courses(
    db: db_dependency,
    user: User = Depends(get_current_admin_user),
):
    """Initialize the eight courses when invoked by an administrator."""
```

Keep the existing course existence checks, inserts, flush, and response unchanged.

- [ ] **Step 5: Verify all administrator dependency consumers**

Run:

```powershell
py -3 -m pytest tests/test_admin.py tests/test_quota.py tests/test_ai.py tests/test_courses.py tests/test_exercises.py -q
pyright
```

Expected: all existing selected tests pass and Pyright stays clean. The repository has no dedicated solutions Router test module, so its unchanged central-dependency use is covered by the complete suite, application startup, and CodeGraph impact check in Task 5.

- [ ] **Step 6: Confirm no duplicate endpoint-wide admin gate remains**

Run from the repository root:

```powershell
rg -n "require_admin|Admin privileges required" backend/app backend/tests
rg -n "if not .*is_admin" backend/app/routers
npx codegraph impact get_current_admin_user
```

Expected: the first search has no matches. The second search shows only object-level rules in `routers/solutions.py`; CodeGraph lists admin, AI, courses, exercises, and solutions consumers.

- [ ] **Step 7: Review and commit Task 4**

Run from `backend`:

```powershell
git diff --check
git diff -- app/routers/admin.py app/routers/courses.py tests/test_admin.py tests/test_courses.py
git add app/routers/admin.py app/routers/courses.py tests/test_admin.py tests/test_courses.py
git commit -m "refactor: unify administrator route gates"
```

## Task 5: Complete Validation, Learning Record, And Index Maintenance

**Files:**
- Modify: `docs/superpowers/specs/2026-07-15-backend-learning-oriented-governance-design.md`
- Modify: `docs/superpowers/plans/2026-07-16-authentication-authorization-governance.md`

**Interfaces:**
- Consumes: Tasks 1-4.
- Produces: fresh full-suite, type-check, startup, live-route, CodeGraph, and quality-gate evidence.

- [ ] **Step 1: Run the full backend quality gate**

Run from `backend`:

```powershell
py -3 -m pytest -q -rs
pyright
```

Expected: every backend test passes, no `SKIPPED` section appears, and Pyright reports `0 errors, 0 warnings, 0 informations`.

- [ ] **Step 2: Run code quality and dead-code searches**

Run from the repository root:

```powershell
rg -n "except ValueError|require_admin|Admin privileges required" backend/app/services/auth.py backend/app/routers/auth.py backend/app/routers/admin.py backend/app/utils/deps.py
rg -n "EmailAlreadyRegisteredError|UsernameAlreadyRegisteredError|InvalidCredentialsError|InactiveAccountError" backend/app backend/tests
git diff --check
```

Expected: no broad authentication `ValueError` catch or local admin dependency remains; every typed error has a service producer and Router/test consumers; the diff check is clean.

Inspect each changed function for the mandatory project checklist: no duplicated logic, no circular dependencies, descriptive names, no unexplained business literals, functions near or below 40 effective lines, no unused imports, and explicit types at module boundaries.

- [ ] **Step 3: Start both services and request affected routes**

From the repository root, start the launcher in a hidden background process:

```powershell
$launcher = Start-Process -FilePath "py" -ArgumentList "-3", "start_services.py" -WorkingDirectory (Get-Location) -WindowStyle Hidden -PassThru
```

Poll `http://127.0.0.1:8000/` and `http://127.0.0.1:3000/` until both respond, then run:

```powershell
$health = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8000/health"
$frontend = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:3000/"
$registration = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/auth/register" -ContentType "application/json" -Body (@{
    email = "auth-governance-smoke-$(Get-Date -Format 'yyyyMMddHHmmss')@example.com"
    username = "authsmoke$(Get-Date -Format 'HHmmss')"
    password = "Password123"
} | ConvertTo-Json)
$headers = @{ Authorization = "Bearer $($registration.access_token)" }
$me = Invoke-WebRequest -UseBasicParsing -Headers $headers "http://127.0.0.1:8000/api/auth/me"
try {
    Invoke-WebRequest -UseBasicParsing -Headers $headers "http://127.0.0.1:8000/api/admin/users"
    throw "regular user unexpectedly reached admin endpoint"
} catch {
    $adminResponse = $_.Exception.Response
    if ([int]$adminResponse.StatusCode -ne 403) { throw }
}
```

Expected: health, frontend, and `/api/auth/me` return 200; registration returns a bearer token; the regular user admin request returns 403. Inspect `.run_logs/backend.err.log` and `.run_logs/frontend.err.log` for startup or compile errors, then stop services:

```powershell
py -3 stop_services.py
```

- [ ] **Step 4: Synchronize CodeGraph and inspect impact**

Run:

```powershell
npx codegraph sync
npx codegraph impact AuthService
npx codegraph impact get_current_admin_user
```

Expected: synchronization succeeds; `AuthService` remains consumed only by the auth Router, and the admin dependency impact includes admin, AI, courses, exercises, and solutions routes.

- [ ] **Step 5: Record the completed authentication batch**

Append this section to `docs/superpowers/specs/2026-07-15-backend-learning-oriented-governance-design.md`, replacing the final proof values with the exact fresh counts from Steps 1-4:

```markdown
## 认证与权限第二批实施记录

- 重构前：认证服务用裸 `ValueError` 表达四种失败；忘记密码依靠 Router 吞异常防枚举；必需与可选认证重复解析令牌和查询用户；管理员端点存在三种门禁写法。
- 重构后：认证专属异常表达服务失败，Router 只映射已知 HTTP 契约；共享解析器统一用户加载，活跃用户兼容依赖不再重复检查；端点级管理员权限统一进入 `get_current_admin_user`。
- 保留：注册、登录、忘记密码、JWT、数据库以及管理员业务成功行为不变；题解的作者或管理员规则继续留在对象级业务授权中。
- 证明：认证服务、Router、依赖、管理员消费者回归测试、完整后端测试、Pyright、FastAPI 与 Next.js 启动、真实路由请求和 CodeGraph 影响检查均通过。
```

- [ ] **Step 6: Update plan evidence and perform final review**

Check every completed step in this plan and append a `## Completion Evidence` section containing exact test counts, Pyright output, live HTTP statuses, CodeGraph consumers, and the final commit list.

Run:

```powershell
git diff --check
git status --short --branch
git log --oneline --decorate -8
```

Review every changed file against the design specification and the project DRY, modularity, naming, magic-value, function-length, dead-code, and type-safety gates. Resolve every Critical or Important issue before committing the records.

- [ ] **Step 7: Commit completion records**

Run:

```powershell
git add docs/superpowers/specs/2026-07-15-backend-learning-oriented-governance-design.md docs/superpowers/plans/2026-07-16-authentication-authorization-governance.md
git commit -m "docs: record authentication governance batch"
```

Expected: the implementation branch is clean, all five tasks are committed, and no frontend or database files changed.

## Plan Self-Review

- Spec coverage: Tasks 1-4 cover typed service errors, Router mapping, forgot-password privacy, shared user resolution, active-state compatibility, central admin gates, course initialization, and object-level authorization preservation. Task 5 covers every validation and maintenance requirement.
- Scope: one authentication/authorization batch; admin business services, JWT configuration, password hashing, frontend, and schema changes remain excluded.
- Type consistency: all error names, dependency names, signatures, response messages, and file paths match the design document and current codebase.
- TDD ordering: each production change is preceded by a test that fails for the current implementation's specific missing boundary.
- Placeholder scan: no unfinished implementation instruction remains.

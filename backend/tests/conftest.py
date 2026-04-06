import uuid
import asyncio
from datetime import datetime
from typing import AsyncGenerator, List, TYPE_CHECKING

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import String, Boolean, DateTime, event
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.database import Base, get_db
from app.main import app
from app.utils.time import utc_now
from app.models import User
from app.utils.security import get_password_hash, create_access_token

if TYPE_CHECKING:
    from app.models.stats import ChapterProgress, LearningSession, ActivityLog


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)


@event.listens_for(test_engine.sync_engine, "connect")
def _set_test_sqlite_pragma(dbapi_connection, connection_record):  # type: ignore[no-untyped-def]
    """Enable SQLite foreign key enforcement in tests (mirrors C7 fix)."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override database dependency for tests"""
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def setup_database():
    """Setup and teardown database for each test"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(setup_database) -> AsyncSession:
    """Create a new database session for each test using the test database"""
    async with TestAsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(setup_database) -> AsyncGenerator[AsyncClient, None]:
    """Create test client"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_user(db_session) -> User:
    """Create authenticated user for testing"""
    user = User(
        id=str(uuid.uuid4()),
        email="auth@test.com",
        username="authuser",
        hashed_password=get_password_hash("Password123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def auth_headers(auth_user):
    """Get auth headers for the user"""
    token = create_access_token({"sub": auth_user.id})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_user(db_session) -> User:
    """Create admin user for testing"""
    user = User(
        id=str(uuid.uuid4()),
        email="admin@test.com",
        username="adminuser",
        hashed_password=get_password_hash("Password123"),
        is_active=True,
        is_admin=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_auth_headers(admin_user):
    """Get auth headers for the admin user"""
    token = create_access_token({"sub": admin_user.id})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def _reset_rate_limiters_between_tests():
    """Reset global rate limiter counters between tests so they don't
    accumulate across the entire test suite. (C5, C8 test isolation)"""
    import app.middleware as mw

    mw._auth_limiter._entries.clear()
    mw._code_limiter._entries.clear()
    yield

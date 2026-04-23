"""
Test configuration for 智码领航 backend.

This conftest.py sets up test fixtures with a shared test database.
"""

import os

# CRITICAL: Set test environment BEFORE any app imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-min-32-chars"

import uuid
import asyncio
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event

# Import Base and app.database BEFORE app.models or app.main
from app.database import Base, get_db
import app.database as app_database

# Create test engine
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)


@event.listens_for(test_engine.sync_engine, "connect")
def _set_test_sqlite_pragma(dbapi_connection, connection_record):
    """Enable SQLite foreign key enforcement."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Replace app.database.engine BEFORE importing app.main
app_database.engine = test_engine

# Import models
from app.models import User, LoginSession, ChapterProgress, LearningSession, ActivityLog
from app.models import Course, Chapter, Exercise, Challenge, UserChallenge, Achievement, UserAchievement
from app.models import UserWeakPoint, SpacedRepetition, CoreTransaction
from app.utils.security import get_password_hash, create_access_token

# Import app.main AFTER engine replacement
from app.main import app as _app

# Create test sessionmaker
TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Also replace AsyncSessionLocal so raw-SQL tests use test engine
app_database.AsyncSessionLocal = TestAsyncSessionLocal


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override database dependency for tests."""
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Disable lifespan (which would call init_db)
from contextlib import asynccontextmanager

@asynccontextmanager
async def null_lifespan(app):
    yield

_app.router.lifespan_context = null_lifespan

# Apply dependency override
_app.dependency_overrides[get_db] = override_get_db

# Export app
app = _app


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def setup_database():
    """Setup and teardown database for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(setup_database) -> AsyncSession:
    """Create a new database session for each test."""
    async with TestAsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession, setup_database) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with shared database session."""

    async def override_get_db_shared():
        yield db_session

    # Override get_db to use the same session
    app.dependency_overrides[get_db] = override_get_db_shared

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clean up override
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
async def auth_user(db_session) -> User:
    """Create authenticated user for testing."""
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
async def test_user(db_session) -> User:
    """Create a test user (alias for auth_user for clarity)."""
    user = User(
        id=str(uuid.uuid4()),
        email="test@test.com",
        username="testuser",
        hashed_password=get_password_hash("Password123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def auth_headers(auth_user):
    """Get auth headers for the user."""
    token = create_access_token({"sub": auth_user.id})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_user(db_session) -> User:
    """Create admin user for testing."""
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
    """Get auth headers for the admin user."""
    token = create_access_token({"sub": admin_user.id})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_user_token(test_user) -> str:
    """Get JWT token for test user."""
    return create_access_token({"sub": test_user.id})


@pytest.fixture
async def admin_token(admin_user) -> str:
    """Get JWT token for admin user."""
    return create_access_token({"sub": admin_user.id})


@pytest.fixture(autouse=True)
def _reset_rate_limiters_between_tests():
    """Reset global rate limiter counters between tests."""
    import app.middleware as mw
    auth = mw._get_auth_limiter()
    code = mw._get_code_limiter()
    auth._entries.clear()
    code._entries.clear()
    yield


@pytest.fixture
async def init_courses(db_session):
    """Initialize the 8 courses for testing."""
    courses_data = [
        {"code": "C", "name": "C语言程序设计", "difficulty_level": 1, "icon": "c"},
        {"code": "CPP", "name": "C++程序设计", "difficulty_level": 2, "icon": "cpp"},
        {"code": "Python", "name": "Python程序设计", "difficulty_level": 1, "icon": "python"},
        {"code": "Java", "name": "Java程序设计", "difficulty_level": 2, "icon": "java"},
        {"code": "Rust", "name": "Rust程序设计", "difficulty_level": 4, "icon": "rust"},
        {"code": "DSA", "name": "数据结构与算法", "difficulty_level": 3, "icon": "dsa"},
        {"code": "ADA", "name": "算法设计与分析", "difficulty_level": 4, "icon": "ada"},
        {"code": "DiscreteMath", "name": "离散数学", "difficulty_level": 3, "icon": "math"},
    ]

    for course_data in courses_data:
        course = Course(
            code=course_data["code"],
            name=course_data["name"],
            difficulty_level=course_data["difficulty_level"],
            icon=course_data["icon"],
            is_active=True
        )
        db_session.add(course)

    await db_session.commit()

import logging
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    get_settings().DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
)


@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):  # type: ignore[no-untyped-def
    """Enable SQLite foreign key enforcement and WAL mode for better concurrency."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    # WAL mode allows concurrent reads during writes - essential for production
    cursor.execute("PRAGMA journal_mode=WAL")
    # Increase busy timeout for write contention (30 seconds)
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.close()


def get_engine_url() -> str:
    """Get the database URL from current settings"""
    return get_settings().DATABASE_URL


def is_debug_enabled() -> bool:
    """Check if debug mode is enabled"""
    return get_settings().DEBUG

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """Dependency for getting async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            logger.exception("Database transaction failed, rolling back")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database - create tables or apply migrations

    Strategy:
    - Always run create_all (idempotent: only creates missing tables)
    - This ensures new model tables are created even when alembic_version exists
    - For actual schema migrations, run: alembic upgrade head
    """
    from sqlalchemy import text, inspect

    async with engine.begin() as conn:
        # Always create missing tables (idempotent - won't drop existing tables)
        await conn.run_sync(Base.metadata.create_all)

        # Check if alembic_version table exists
        def _check_alembic(sync_conn):
            inspector = inspect(sync_conn)
            return 'alembic_version' in inspector.get_table_names()

        has_alembic = await conn.run_sync(_check_alembic)

        if has_alembic:
            logger.info("Database tables ensured (new tables created if needed). Alembic tracked.")
        else:
            # No alembic tracking - stamp by directly writing alembic_version row
            # This avoids calling command.stamp() which loads env.py -> asyncio.run() conflict
            def _stamp_head(sync_conn):
                sync_conn.execute(
                    text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL, CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))")
                )
                sync_conn.execute(
                    text("INSERT INTO alembic_version (version_num) VALUES (:ver)"),
                    {"ver": "001_initial"},
                )

            await conn.run_sync(_stamp_head)
            logger.info("Database initialized and stamped with Alembic revision 001_initial.")

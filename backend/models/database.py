"""
Database configuration - supports PostgreSQL (production) and SQLite (local dev).
Production: PostgreSQL via DATABASE_URL env var (Render provides this).
Local dev: SQLite fallback for convenience.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

DATABASE_URL = os.getenv("DATABASE_URL", "")

# Normalize database URL
if DATABASE_URL:
    # Render may provide postgres:// (without async) - normalize to async format
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    # Local dev fallback to SQLite
    DATABASE_URL = "sqlite+aiosqlite:///./merchantflow.db"

# Determine if using PostgreSQL
IS_POSTGRES = "postgresql" in DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    **(
        # PostgreSQL connection pooling
        {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
        }
        if IS_POSTGRES
        else
        # SQLite settings
        {
            "connect_args": {"check_same_thread": False},
        }
    ),
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Create all tables. Safe to call multiple times (idempotent)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

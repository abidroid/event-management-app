"""Async database setup: engine, session factory, declarative Base and get_db()."""

from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


def to_asyncpg_url(raw_url: str) -> URL:
    """Convert a Neon connection string into one the asyncpg driver accepts.

    Neon hands out `postgresql://...?sslmode=require&channel_binding=require`.
    asyncpg rejects both query parameters, so they are removed here and SSL
    is requested through `connect_args` instead (see `create_db_engine`).

    Args:
        raw_url: Connection string exactly as copied from the Neon console.

    Returns:
        A SQLAlchemy URL using the `postgresql+asyncpg` driver.
    """
    url = make_url(raw_url).set(drivername="postgresql+asyncpg")
    return url.difference_update_query(["sslmode", "channel_binding"])


def create_db_engine(database_url: str, **engine_kwargs: Any) -> AsyncEngine:
    """Create an async engine configured for Neon serverless PostgreSQL.

    Args:
        database_url: Neon connection string (any `postgresql://` form).
        **engine_kwargs: Extra options for `create_async_engine`, for example
            `poolclass=NullPool` in the test suite.

    Returns:
        A configured `AsyncEngine`.
    """
    return create_async_engine(
        to_asyncpg_url(database_url),
        # Replaces the stripped `sslmode=require`: Neon only accepts TLS.
        connect_args={"ssl": "require"},
        # Neon suspends idle compute and closes its connections, so test each
        # pooled connection before use and never keep one longer than 5 minutes.
        pool_pre_ping=True,
        pool_recycle=300,
        **engine_kwargs,
    )


engine = create_db_engine(settings.database_url)

# expire_on_commit=False keeps attributes loaded after commit, so a service can
# return an object it just saved without triggering a lazy (sync) reload.
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all ORM models; its metadata holds every table."""


async def get_db() -> AsyncIterator[AsyncSession]:
    """Provide one database session per request as a FastAPI dependency.

    Yields:
        An `AsyncSession` that is closed automatically when the request ends.
    """
    async with SessionLocal() as session:
        yield session

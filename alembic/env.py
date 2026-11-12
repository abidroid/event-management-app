"""Alembic migration environment wired to the application's Settings and Base.

The database URL comes from `app.core.config.settings` (the `.env` file) and is
converted for asyncpg by `app.db`, so migrations connect exactly like the app.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection

import app.models  # noqa: F401  (imported so every model registers on Base.metadata)
from alembic import context
from app.core.config import settings
from app.db import Base, create_db_engine, to_asyncpg_url

# The Alembic Config object, which gives access to values in alembic.ini.
config = context.config

# Set up Python logging from the [loggers] sections of alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Autogenerate compares the database against this metadata.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode, emitting SQL instead of executing it.

    Only a URL is needed here, no live connection, so the converted URL is
    rendered as a string for Alembic.
    """
    url = to_asyncpg_url(settings.database_url).render_as_string(hide_password=False)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Configure the migration context on a connection and run migrations.

    Args:
        connection: A synchronous-facing connection supplied by `run_sync`.
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Open an async connection to the database and run migrations on it."""
    # Same Neon settings as the app (asyncpg URL, SSL), but NullPool because a
    # one-off CLI command has no use for a connection pool.
    connectable = create_db_engine(settings.database_url, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode against the live database."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

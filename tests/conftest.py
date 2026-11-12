"""Shared pytest fixtures: test database, HTTP client and sample data.

Tests run against the Neon `test` branch (TEST_DATABASE_URL), never the
development database, so PostgreSQL-specific behaviour is tested for real.
"""

from collections.abc import AsyncIterator
from datetime import date, timedelta
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app import models  # noqa: F401  (registers every table on Base.metadata)
from app.core.config import settings
from app.db import Base, create_db_engine, get_db
from app.main import app


@pytest.fixture(scope="session")
async def test_engine() -> AsyncIterator[AsyncEngine]:
    """Create the test engine and the tables once for the whole test session.

    NullPool opens a fresh connection each time instead of reusing pooled
    ones, which avoids asyncpg connections outliving the loop they were made on.

    Yields:
        An `AsyncEngine` connected to the Neon test branch.
    """
    engine = create_db_engine(settings.test_database_url, poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(autouse=True)
async def clean_tables(test_engine: AsyncEngine) -> None:
    """Empty every table before each test so tests never affect each other.

    TRUNCATE is one round trip to Neon, far faster than dropping and
    recreating tables per test. RESTART IDENTITY resets ids to 1.

    Args:
        test_engine: The session-wide test engine.
    """
    table_names = ", ".join(table.name for table in Base.metadata.sorted_tables)
    async with test_engine.begin() as connection:
        await connection.execute(
            text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE")
        )


@pytest.fixture
async def client(test_engine: AsyncEngine) -> AsyncIterator[AsyncClient]:
    """Provide an HTTP client that calls the app in-process with the test database.

    Args:
        test_engine: The session-wide test engine.

    Yields:
        An `AsyncClient` whose requests use sessions bound to the test engine.
    """
    test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        """Replace the app's get_db so routes use the test database.

        Yields:
            An `AsyncSession` bound to the test engine.
        """
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()


@pytest.fixture
def user_payload() -> dict[str, str]:
    """Return a valid sign-up body.

    Returns:
        A JSON-ready dict accepted by POST /auth/register.
    """
    return {
        "email": "ada.lovelace@acme.com",
        "full_name": "Ada Lovelace",
        "password": "correct-horse-battery",
    }


@pytest.fixture
async def auth_headers(
    client: AsyncClient, user_payload: dict[str, str]
) -> dict[str, str]:
    """Register and log in a user, returning headers that authenticate as them.

    Args:
        client: The test HTTP client.
        user_payload: A valid sign-up body.

    Returns:
        An `Authorization: Bearer <token>` header dict for requests.
    """
    response = await client.post("/auth/register", json=user_payload)
    assert response.status_code == 201
    # The login endpoint takes OAuth2 form fields, not JSON.
    response = await client.post(
        "/auth/login",
        data={
            "username": user_payload["email"],
            "password": user_payload["password"],
        },
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def event_payload() -> dict[str, Any]:
    """Return a valid event body dated 30 days ahead, so it never expires.

    Returns:
        A JSON-ready dict accepted by POST /events.
    """
    return {
        "title": "Quarterly Town Hall",
        "description": "Company-wide update from the leadership team.",
        "event_date": (date.today() + timedelta(days=30)).isoformat(),
        "location": "Main Auditorium",
        "max_capacity": 100,
    }


@pytest.fixture
async def event(client: AsyncClient, event_payload: dict[str, Any]) -> dict[str, Any]:
    """Create one event through the API.

    Args:
        client: The test HTTP client.
        event_payload: A valid event body.

    Returns:
        The created event as returned by the API.
    """
    response = await client.post("/events", json=event_payload)
    assert response.status_code == 201
    return response.json()

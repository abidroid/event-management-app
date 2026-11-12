"""Shared pytest fixtures: test database, HTTP client and sample data.

Tests run against the Neon `test` branch (TEST_DATABASE_URL), never the
development database, so PostgreSQL-specific behaviour is tested for real.
"""

from collections.abc import AsyncIterator, Awaitable, Callable
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
    """Create the test engine and rebuild the tables once for the whole session.

    NullPool opens a fresh connection each time instead of reusing pooled
    ones, which avoids asyncpg connections outliving the loop they were made on.
    Tables are dropped first because create_all never alters an existing
    table, so a new column (like events.created_by) would otherwise be missing.

    Yields:
        An `AsyncEngine` connected to the Neon test branch.
    """
    engine = create_db_engine(settings.test_database_url, poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
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
def make_auth_headers(
    client: AsyncClient,
) -> Callable[[str, str], Awaitable[dict[str, str]]]:
    """Provide a function that signs up and logs in a new user.

    Registration tests need several distinct users (filling an event, cancelling
    someone else's registration), so this is a factory rather than one user.

    Args:
        client: The test HTTP client.

    Returns:
        An async function taking (email, full_name) and returning an
        `Authorization: Bearer <token>` header dict for that new user.
    """

    async def _make(email: str, full_name: str) -> dict[str, str]:
        """Register and log in one user.

        Args:
            email: The new user's email address.
            full_name: The new user's display name.

        Returns:
            Headers that authenticate requests as this user.
        """
        password = "correct-horse-battery"
        response = await client.post(
            "/auth/register",
            json={"email": email, "full_name": full_name, "password": password},
        )
        assert response.status_code == 201
        # The login endpoint takes OAuth2 form fields, not JSON.
        response = await client.post(
            "/auth/login", data={"username": email, "password": password}
        )
        assert response.status_code == 200
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _make


@pytest.fixture
async def auth_headers(
    make_auth_headers: Callable[[str, str], Awaitable[dict[str, str]]],
    user_payload: dict[str, str],
) -> dict[str, str]:
    """Register and log in the default user, returning headers that authenticate as them.

    Args:
        make_auth_headers: Factory that signs up and logs in a user.
        user_payload: A valid sign-up body.

    Returns:
        An `Authorization: Bearer <token>` header dict for requests.
    """
    return await make_auth_headers(user_payload["email"], user_payload["full_name"])


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
async def event(
    client: AsyncClient, event_payload: dict[str, Any], auth_headers: dict[str, str]
) -> dict[str, Any]:
    """Create one event through the API.

    Args:
        client: The test HTTP client.
        event_payload: A valid event body.
        auth_headers: Headers for a logged-in user, who becomes the creator.

    Returns:
        The created event as returned by the API.
    """
    response = await client.post("/events", json=event_payload, headers=auth_headers)
    assert response.status_code == 201
    return response.json()

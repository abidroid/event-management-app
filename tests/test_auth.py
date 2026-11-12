"""Tests for the /auth endpoints: sign-up, login and the current user."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import AsyncClient, Response

from app.core.config import settings


async def login(client: AsyncClient, email: str, password: str) -> Response:
    """Post the OAuth2 login form, which takes the email as `username`.

    Args:
        client: The test HTTP client.
        email: Email address to log in with.
        password: Password to log in with.

    Returns:
        The login response.
    """
    return await client.post(
        "/auth/login", data={"username": email, "password": password}
    )


async def test_register_returns_201_without_password(
    client: AsyncClient, user_payload: dict[str, str]
) -> None:
    """POST /auth/register creates the account and never echoes the password."""
    response = await client.post("/auth/register", json=user_payload)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["email"] == user_payload["email"]
    assert body["full_name"] == user_payload["full_name"]
    assert "password" not in body
    assert "hashed_password" not in body


async def test_register_lowercases_email(
    client: AsyncClient, user_payload: dict[str, str]
) -> None:
    """Emails are stored in lower case so each address has one account."""
    user_payload["email"] = "Ada.Lovelace@ACME.com"

    response = await client.post("/auth/register", json=user_payload)

    assert response.status_code == 201
    assert response.json()["email"] == "ada.lovelace@acme.com"


@pytest.mark.parametrize("email", ["ada.lovelace@acme.com", "ADA.LOVELACE@acme.com"])
async def test_register_duplicate_email_returns_409(
    client: AsyncClient, user_payload: dict[str, str], email: str
) -> None:
    """Signing up again with the same email, in any letter case, returns 409."""
    await client.post("/auth/register", json=user_payload)

    response = await client.post(
        "/auth/register", json={**user_payload, "email": email}
    )

    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("email", "not-an-email"),
        ("password", "short"),
        ("full_name", "   "),
    ],
)
async def test_register_invalid_field_returns_422(
    client: AsyncClient, user_payload: dict[str, str], field: str, value: str
) -> None:
    """POST /auth/register rejects an invalid email, short password or blank name."""
    user_payload[field] = value

    response = await client.post("/auth/register", json=user_payload)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == field


async def test_login_returns_bearer_token(
    client: AsyncClient, user_payload: dict[str, str]
) -> None:
    """POST /auth/login with correct credentials returns a bearer token."""
    await client.post("/auth/register", json=user_payload)

    response = await login(client, user_payload["email"], user_payload["password"])

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


async def test_login_wrong_password_returns_401(
    client: AsyncClient, user_payload: dict[str, str]
) -> None:
    """A wrong password returns 401 with the Bearer challenge header."""
    await client.post("/auth/register", json=user_payload)

    response = await login(client, user_payload["email"], "wrong-password")

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password"}
    assert response.headers["WWW-Authenticate"] == "Bearer"


async def test_login_unknown_email_returns_401(client: AsyncClient) -> None:
    """An email with no account gets the same 401 as a wrong password."""
    response = await login(client, "nobody@acme.com", "whatever-password")

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password"}


async def test_me_returns_current_user(
    client: AsyncClient, auth_headers: dict[str, str], user_payload: dict[str, str]
) -> None:
    """GET /auth/me returns the user the token belongs to."""
    response = await client.get("/auth/me", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["email"] == user_payload["email"]


async def test_me_without_token_returns_401(client: AsyncClient) -> None:
    """GET /auth/me without an Authorization header returns 401."""
    response = await client.get("/auth/me")

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


async def test_me_with_malformed_token_returns_401(client: AsyncClient) -> None:
    """A token that is not a valid JWT returns 401."""
    response = await client.get(
        "/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}
    assert response.headers["WWW-Authenticate"] == "Bearer"


async def test_me_with_expired_token_returns_401(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    """A correctly signed token whose expiry has passed returns 401."""
    expired = jwt.encode(
        {"sub": "1", "exp": datetime.now(UTC) - timedelta(minutes=1)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {expired}"}
    )

    assert response.status_code == 401


async def test_me_with_token_for_missing_user_returns_401(client: AsyncClient) -> None:
    """A valid token for a user id that does not exist returns 401."""
    token = jwt.encode(
        {"sub": "999", "exp": datetime.now(UTC) + timedelta(minutes=5)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401

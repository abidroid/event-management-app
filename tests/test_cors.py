"""Tests that the browser frontend is allowed to call the API (CORS)."""

from httpx import AsyncClient

FRONTEND_ORIGIN = "http://localhost:5173"


async def test_preflight_allows_frontend_origin(client: AsyncClient) -> None:
    """A preflight request from the React dev server is allowed."""
    response = await client.options(
        "/events",
        headers={
            "Origin": FRONTEND_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == FRONTEND_ORIGIN


async def test_preflight_rejects_unknown_origin(client: AsyncClient) -> None:
    """A preflight request from any other origin gets no allow-origin header."""
    response = await client.options(
        "/events",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers

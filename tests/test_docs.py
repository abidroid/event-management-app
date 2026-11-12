"""Tests that the generated OpenAPI document fully describes every route."""

from typing import Any

from httpx import AsyncClient

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
ERROR_CODES = {"401", "403", "404", "409"}


async def get_operations(client: AsyncClient) -> list[tuple[str, dict[str, Any]]]:
    """Fetch /openapi.json and list every operation in it.

    Args:
        client: The test HTTP client.

    Returns:
        Pairs of a label like "GET /events" and that operation's OpenAPI object.
    """
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    return [
        (f"{method.upper()} {path}", operation)
        for path, path_item in response.json()["paths"].items()
        for method, operation in path_item.items()
        if method in HTTP_METHODS
    ]


async def test_openapi_has_app_metadata(client: AsyncClient) -> None:
    """The document carries the app's title, version and tag descriptions."""
    response = await client.get("/openapi.json")

    info = response.json()["info"]
    assert info["title"] == "Corporate Event Management API"
    assert info["version"] == "1.0.0"
    tag_names = {tag["name"] for tag in response.json()["tags"]}
    assert tag_names == {"auth", "events", "registrations", "health"}


async def test_every_route_has_tags_summary_and_description(
    client: AsyncClient,
) -> None:
    """No route shows up in Swagger without a group, title and explanation."""
    for label, operation in await get_operations(client):
        assert operation.get("tags"), f"{label} has no tags"
        assert operation.get("summary"), f"{label} has no summary"
        assert operation.get("description"), f"{label} has no description"


async def test_error_responses_use_error_schema(client: AsyncClient) -> None:
    """Every documented 401/403/404/409 uses ErrorResponse with an example."""
    for label, operation in await get_operations(client):
        for code, response in operation["responses"].items():
            if code not in ERROR_CODES:
                continue
            body = response["content"]["application/json"]
            assert body["schema"]["$ref"].endswith("/ErrorResponse"), (
                f"{label} {code} does not use ErrorResponse"
            )
            assert body["example"]["detail"], f"{label} {code} has no example"


async def test_protected_routes_document_401(client: AsyncClient) -> None:
    """Every route behind a token says it can answer 401."""
    for label, operation in await get_operations(client):
        if operation.get("security"):
            assert "401" in operation["responses"], f"{label} does not document 401"

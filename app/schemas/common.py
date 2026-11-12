"""Schemas shared across resources."""

from pydantic import BaseModel, ConfigDict, Field


class PaginationParams(BaseModel):
    """Query parameters that select one page of a list endpoint.

    Shared by every list route so paging rules are defined in one place.

    Attributes:
        skip: Number of items to skip from the start (0 or more).
        limit: Maximum number of items to return (1-100).
    """

    model_config = ConfigDict(json_schema_extra={"example": {"skip": 0, "limit": 10}})

    skip: int = Field(default=0, ge=0, description="Number of items to skip.")
    # The upper bound stops one request from pulling the whole table.
    limit: int = Field(
        default=10, ge=1, le=100, description="Maximum number of items to return."
    )


class HealthResponse(BaseModel):
    """Body returned by the health check endpoint.

    Attributes:
        status: Always "ok" when the API process is up.
    """

    model_config = ConfigDict(json_schema_extra={"example": {"status": "ok"}})

    status: str


class ErrorResponse(BaseModel):
    """Body returned for every handled error (404, 409, 401, 403).

    Attributes:
        detail: Human-readable explanation of what went wrong.
    """

    model_config = ConfigDict(
        json_schema_extra={"example": {"detail": "Event 42 not found"}}
    )

    detail: str

"""Schemas shared across resources."""

from pydantic import BaseModel, ConfigDict


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

    model_config = ConfigDict(json_schema_extra={"example": {"detail": "Event 42 not found"}})

    detail: str

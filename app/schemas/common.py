"""Schemas shared across resources."""

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Body returned by the health check endpoint.

    Attributes:
        status: Always "ok" when the API process is up.
    """

    model_config = ConfigDict(json_schema_extra={"example": {"status": "ok"}})

    status: str

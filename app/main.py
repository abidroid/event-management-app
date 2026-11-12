"""FastAPI application factory: builds the app, registers routers and /health."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import engine
from app.schemas.common import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run startup and shutdown work around the application's lifetime.

    Args:
        app: The FastAPI application being started.

    Yields:
        Control back to FastAPI while the application serves requests.
    """
    yield
    # Close pooled connections cleanly instead of letting Neon drop them.
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        The configured FastAPI instance.
    """
    app = FastAPI(
        title="Corporate Event Management API",
        version="0.1.0",
        description="Internal API for creating Acme Corp events and registering attendees.",
        lifespan=lifespan,
    )

    @app.get(
        "/health",
        tags=["health"],
        summary="Health check",
        description="Report that the API process is running. Does not touch the database.",
        response_model=HealthResponse,
        status_code=200,
    )
    async def health() -> HealthResponse:
        """Return a static OK status for uptime checks.

        Returns:
            A `HealthResponse` with status "ok".
        """
        return HealthResponse(status="ok")

    return app


app = create_app()

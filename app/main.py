"""FastAPI application factory: builds the app, registers routers and /health."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import events
from app.core.exceptions import DomainError
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


async def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Turn any domain exception raised by a service into a JSON error response.

    One handler for every `DomainError` subclass keeps status codes in a single
    place: each exception class declares its own `status_code`.

    Args:
        request: The request that failed (required by FastAPI's handler signature).
        exc: The raised exception; always a `DomainError` given how it is registered.

    Returns:
        A response with the exception's status code, `{"detail": message}` and
        any headers the exception declares (e.g. `WWW-Authenticate` on 401).
    """
    # Starlette types handlers as accepting any Exception, so the parameter must
    # say Exception. This handler is only registered for DomainError, so the
    # check always passes; it narrows the type so `status_code` and `message`
    # type-check.
    assert isinstance(exc, DomainError)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
        headers=exc.headers,
    )


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
    app.add_exception_handler(DomainError, domain_error_handler)
    app.include_router(events.router)

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

"""FastAPI application factory: builds the app, registers routers and /health."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import auth, events, registrations
from app.core.config import settings
from app.core.exceptions import DomainError
from app.db import engine
from app.schemas.common import HealthResponse

# Markdown shown at the top of /docs, so a first-time user knows how to log in.
API_DESCRIPTION = """
Internal API for creating Acme Corp events and registering attendees.

**Authentication**

1. Create an account with `POST /auth/register`.
2. Click **Authorize** and log in with your email (in the `username` field)
   and password. Swagger then sends the token with every request.

Listing and viewing events is public. Creating, updating and deleting events,
and everything to do with registrations, requires a token.

**Errors**

Every handled error returns `{"detail": "<message>"}` with status 401, 403,
404 or 409. Invalid input returns 422 with FastAPI's validation details.
"""

# Order and descriptions of the tag groups in /docs.
OPENAPI_TAGS = [
    {"name": "auth", "description": "Sign up, log in and see who you are."},
    {"name": "events", "description": "Create, browse, update and delete events."},
    {
        "name": "registrations",
        "description": "Sign up for events, list attendees and cancel your sign-ups.",
    },
    {"name": "health", "description": "Check that the API is running."},
]


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
        version="1.0.0",
        description=API_DESCRIPTION,
        openapi_tags=OPENAPI_TAGS,
        lifespan=lifespan,
    )
    # The React app runs on a different origin (port 5173), so without CORS the
    # browser would block every response. Only the listed origins are allowed.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(DomainError, domain_error_handler)
    app.include_router(auth.router)
    app.include_router(events.router)
    app.include_router(registrations.router)

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

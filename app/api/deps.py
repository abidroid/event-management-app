"""Reusable FastAPI dependencies, declared once as `Annotated` aliases."""

from typing import Annotated

from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User
from app.schemas.common import PaginationParams
from app.services import auth_service

# Type alias so routes write `session: SessionDep` instead of repeating Depends.
SessionDep = Annotated[AsyncSession, Depends(get_db)]

# Query() reads ?skip=&limit= into a PaginationParams model, so any list route
# gets validated paging (422 on bad values) by adding `pagination: Pagination`.
Pagination = Annotated[PaginationParams, Query()]

# Reads "Authorization: Bearer <token>" and answers 401 itself when the header
# is missing. tokenUrl tells Swagger's Authorize button where to log in.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep
) -> User:
    """Resolve the logged-in user from the request's bearer token.

    Args:
        token: The JWT taken from the Authorization header.
        session: Database session for this request.

    Returns:
        The user the token belongs to.

    Raises:
        InvalidCredentialsError: If the token is invalid, expired or its user
            is gone (turned into a 401 by the exception handler).
    """
    return await auth_service.get_user_from_token(session, token)


# Adding `current_user: CurrentUser` to a route makes that route require login.
CurrentUser = Annotated[User, Depends(get_current_user)]

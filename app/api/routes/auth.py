"""HTTP routes for sign-up, login and the current user's profile."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, SessionDep
from app.api.responses import BAD_LOGIN, EMAIL_TAKEN, UNAUTHORIZED
from app.models import User
from app.schemas.user import Token, UserCreate, UserRead
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    summary="Create an account",
    description="Sign up with an email, full name and password. Emails are case-insensitive.",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    responses=EMAIL_TAKEN,
)
async def register(data: UserCreate, session: SessionDep) -> User:
    """Create an account.

    Args:
        data: Validated sign-up fields from the request body.
        session: Database session for this request.

    Returns:
        The created user, without the password.
    """
    return await auth_service.register_user(session, data)


@router.post(
    "/login",
    summary="Log in",
    description=(
        "Exchange an email (sent in the `username` form field, as OAuth2 requires) "
        "and password for a bearer access token."
    ),
    response_model=Token,
    status_code=status.HTTP_200_OK,
    responses=BAD_LOGIN,
)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep
) -> Token:
    """Log in and receive an access token.

    Args:
        form: OAuth2 form data; `username` holds the email address.
        session: Database session for this request.

    Returns:
        The access token and its type.
    """
    return await auth_service.login(session, form.username, form.password)


@router.get(
    "/me",
    summary="Get the current user",
    description="Return the account that the bearer token belongs to.",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    responses=UNAUTHORIZED,
)
async def read_me(current_user: CurrentUser) -> User:
    """Return the logged-in user.

    Args:
        current_user: The user resolved from the bearer token.

    Returns:
        The logged-in user.
    """
    return current_user

"""Business logic for signing up, logging in and identifying the current user."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EmailAlreadyRegisteredError, InvalidCredentialsError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models import User
from app.schemas.user import Token, UserCreate


async def _get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Find a user by email, ignoring letter case.

    Emails are stored lower-cased, so lower-casing the input makes
    "Ada@Acme.com" and "ada@acme.com" the same account.

    Args:
        session: Active database session.
        email: Email address to look up.

    Returns:
        The matching `User`, or None if there is no account with that email.
    """
    result = await session.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def register_user(session: AsyncSession, data: UserCreate) -> User:
    """Create a new account with a hashed password.

    Args:
        session: Active database session.
        data: Validated sign-up fields.

    Returns:
        The saved `User`.

    Raises:
        EmailAlreadyRegisteredError: If an account with this email already exists.
    """
    if await _get_user_by_email(session, data.email) is not None:
        raise EmailAlreadyRegisteredError(data.email)
    user = User(
        email=data.email.lower(),
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
    )
    session.add(user)
    await session.commit()
    # Reload so the server-generated created_at is populated.
    await session.refresh(user)
    return user


async def login(session: AsyncSession, email: str, password: str) -> Token:
    """Check an email and password and issue an access token.

    Args:
        session: Active database session.
        email: Email address typed at login.
        password: Password typed at login.

    Returns:
        A `Token` holding a signed JWT for the user.

    Raises:
        InvalidCredentialsError: If the email is unknown or the password is wrong.
    """
    user = await _get_user_by_email(session, email)
    # One message for both cases, so an attacker cannot use login to discover
    # which emails have accounts.
    if user is None or not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError("Incorrect email or password")
    return Token(access_token=create_access_token(user.id))


async def get_user_from_token(session: AsyncSession, token: str) -> User:
    """Return the user a bearer token belongs to.

    Args:
        session: Active database session.
        token: The JWT sent in the Authorization header.

    Returns:
        The `User` whose id is in the token.

    Raises:
        InvalidCredentialsError: If the token is invalid or expired, or its
            user no longer exists.
    """
    user_id = decode_access_token(token)
    user = await session.get(User, user_id)
    if user is None:
        raise InvalidCredentialsError()
    return user

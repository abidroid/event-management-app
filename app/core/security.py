"""Password hashing (pwdlib, argon2) and JWT access tokens (PyJWT)."""

from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import settings
from app.core.exceptions import InvalidCredentialsError

# recommended() picks argon2, the current OWASP first choice for password hashing.
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a plain-text password for storage.

    Args:
        password: The password exactly as the user typed it.

    Returns:
        An argon2 hash string that includes its own random salt.
    """
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Check a plain-text password against a stored hash.

    Args:
        password: The password the user typed at login.
        hashed_password: The hash saved when the account was created.

    Returns:
        True if the password matches, otherwise False.
    """
    return password_hash.verify(password, hashed_password)


def create_access_token(user_id: int) -> str:
    """Create a signed JWT that identifies a user until it expires.

    Args:
        user_id: Id of the logged-in user, stored in the `sub` claim.

    Returns:
        The encoded token string.
    """
    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    # The JWT standard requires `sub` to be a string; PyJWT rejects an int.
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str) -> int:
    """Verify a JWT and return the user id it carries.

    Args:
        token: The bearer token sent by the client.

    Returns:
        The user id from the token's `sub` claim.

    Raises:
        InvalidCredentialsError: If the signature is wrong, the token has
            expired, or the `sub` claim is missing or not a number.
    """
    try:
        # Passing `algorithms` explicitly stops a forged token from choosing a
        # weaker algorithm (or "none") for itself.
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise InvalidCredentialsError() from exc

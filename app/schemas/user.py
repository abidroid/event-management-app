"""Request and response schemas for user accounts and login tokens."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints

FullName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]
# The upper bound stops a huge "password" from making argon2 hashing slow.
Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]


class UserCreate(BaseModel):
    """Body for creating an account.

    Attributes:
        email: Work email address; used as the login name.
        full_name: Name shown on registrations (1-100 characters after trimming).
        password: Plain-text password (8-128 characters); only its hash is stored.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "ada.lovelace@acme.com",
                "full_name": "Ada Lovelace",
                "password": "correct-horse-battery",
            }
        }
    )

    email: EmailStr
    full_name: FullName
    password: Password


class UserRead(BaseModel):
    """Account as returned by the API; never includes the password hash.

    Attributes:
        id: Primary key.
        email: Login email address.
        full_name: Display name.
        created_at: When the account was created.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    created_at: datetime


class Token(BaseModel):
    """Access token returned by a successful login, in the OAuth2 format.

    Attributes:
        access_token: Signed JWT to send as `Authorization: Bearer <token>`.
        token_type: Always "bearer"; Swagger's Authorize button expects it.
    """

    access_token: str
    token_type: Literal["bearer"] = "bearer"

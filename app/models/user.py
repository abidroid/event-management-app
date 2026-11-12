"""ORM model for the `users` table."""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    """An Acme Corp employee who can log in, create events and register for them.

    Attributes:
        id: Primary key.
        email: Login name; unique and stored in lower case.
        full_name: Name shown on registrations.
        hashed_password: Argon2 hash of the password (the password itself is never stored).
        created_at: When the account was created (set by the database).
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 320 is the longest address the email standard allows; the unique index
    # also makes login lookups by email fast.
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100))
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

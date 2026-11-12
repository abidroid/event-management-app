"""Reusable FastAPI dependencies, declared once as `Annotated` aliases."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db

# Type alias so routes write `session: SessionDep` instead of repeating Depends.
SessionDep = Annotated[AsyncSession, Depends(get_db)]

"""SQLAlchemy ORM models, one module per table.

Every model is re-exported here so that importing `app.models` registers all
tables on `Base.metadata`, which Alembic autogenerate relies on.
"""

from app.models.event import Event
from app.models.registration import Registration
from app.models.user import User

__all__ = ["Event", "Registration", "User"]

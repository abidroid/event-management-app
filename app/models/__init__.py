"""SQLAlchemy ORM models, one module per table.

Every model is re-exported here so that importing `app.models` registers all
tables on `Base.metadata`, which Alembic autogenerate relies on.
"""

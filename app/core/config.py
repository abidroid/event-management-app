"""Application settings loaded from environment variables and the `.env` file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration for the whole application.

    Field names are matched to environment variables case-insensitively, so
    the `DATABASE_URL` variable fills `database_url`. Keeping secrets here
    (instead of in code) means they live only in the uncommitted `.env` file.

    Attributes:
        database_url: Neon connection string for the development database.
        test_database_url: Neon connection string for the test branch used by pytest.
        jwt_secret_key: Secret used to sign and verify JWT access tokens.
        jwt_algorithm: Algorithm used to sign JWT access tokens.
        access_token_expire_minutes: Lifetime of an access token in minutes.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    test_database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


# One shared instance: the .env file is read once at import time.
settings = Settings()

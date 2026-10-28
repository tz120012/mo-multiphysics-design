"""Application settings. Host defaults use 5433/6380; compose uses postgres:5432 / redis:6379."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime config from env. DATABASE_URL / REDIS_URL names are locked."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Mo API"
    app_version: str = "1.0.0-draft"
    # Host-side defaults (API process on host → published ports).
    # In-compose override: postgresql+psycopg://mo:mo@postgres:5432/mo
    database_url: str = "postgresql+psycopg://mo:mo@127.0.0.1:5433/mo"
    redis_url: str = "redis://127.0.0.1:6380/0"
    mems_schema_version: str = "1.0.0-draft"
    # Q2-6: set CELERY_ENABLED=1 when a worker is running; else analytic uses in-process degrade.
    celery_enabled: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()

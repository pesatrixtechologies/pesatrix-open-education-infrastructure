"""Application configuration, loaded from environment variables.

Never hardcode secrets. All configuration is provided via environment
variables (see ``.env.example``).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="OE_",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "pesatrix-open-education-infrastructure"
    env: str = "development"
    debug: bool = False
    secret_key: str = (
        "dev-only-insecure-secret-key-change-me-please-1234567890-abcdefghijklmnopqrstuvwxyz"
    )
    database_url: str = "postgresql+asyncpg://oe:oe@localhost:5432/oe"

    jwt_expires_minutes: int = 15
    jwt_refresh_expires_days: int = 14

    sync_batch_size: int = 200
    sync_idempotency_ttl_seconds: int = 604800  # 7 days

    rate_limit_enabled: bool = True
    rate_limit_default_per_minute: int = 120

    cors_origins: str = ""

    log_level: str = "INFO"

    # Bootstrap administrator (development convenience only).
    bootstrap_admin_username: str = "admin"
    bootstrap_admin_password: str = Field(default="admin", exclude=True)

    @field_validator("cors_origins", mode="after")
    @classmethod
    def _parse_origins(cls, value: str) -> str:
        return ",".join(origin.strip() for origin in value.split(",") if origin.strip())

    @property
    def is_production(self) -> bool:
        return self.env.lower() in {"production", "prod"}

    def cors_origin_list(self) -> list[str]:
        """Return configured CORS origins as a list."""
        if not self.cors_origins:
            return []
        return [origin for origin in self.cors_origins.split(",") if origin]

    def validate_for_production(self) -> None:
        """Raise a descriptive error when insecure defaults are used in production."""
        if self.is_production:
            if not self.debug and self.secret_key.startswith("dev-only-"):
                raise RuntimeError(
                    "OE_SECRET_KEY must be set to a strong random value in production."
                )
            if self.bootstrap_admin_password == "admin":
                raise RuntimeError(
                    "OE_BOOTSTRAP_ADMIN_PASSWORD must be changed from the default "
                    "before running in production."
                )


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""
    settings = Settings()
    settings.validate_for_production()
    return settings

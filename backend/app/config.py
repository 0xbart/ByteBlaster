from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="BYTEBLASTER_", extra="ignore")

    database_url: str = "postgresql+asyncpg://byteblaster:byteblaster@localhost:5432/byteblaster"
    storage_dir: Path = Path("/data/sounds")
    max_upload_bytes: int = 10 * 1024 * 1024  # 10 MB

    # CORS origins for dev (vite). Comma-separated env var.
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # IPs (peer addresses) we trust to forward client IP via X-Forwarded-For.
    # Leave empty in dev to use request.client.host directly.
    trusted_proxies: list[str] = Field(default_factory=list)

    # Per-user rate limit on POST /sounds/{id}/play.
    # Superadmins are exempt. Set rate_limit_plays=0 to disable.
    rate_limit_plays: int = 5
    rate_limit_window_seconds: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="BYTEBLASTER_", extra="ignore")

    database_url: str = "postgresql+asyncpg://byteblaster:byteblaster@localhost:5432/byteblaster"
    storage_dir: Path = Path("/data/sounds")
    # Read-only local library bind-mounted from the host `./sounds` folder.
    # Top-level subfolders act as categories; browsed via the Explore "Local" tab.
    local_sounds_dir: Path = Path("/sounds")
    max_upload_bytes: int = 10 * 1024 * 1024  # 10 MB

    # CORS origins for dev (vite). Comma-separated env var.
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # IPs (peer addresses) we trust to forward client IP via X-Forwarded-For.
    # Leave empty in dev to use request.client.host directly.
    trusted_proxies: list[str] = Field(default_factory=list)

    # Per-user rate limits. Superadmins are exempt. Set the count to 0 to disable.
    rate_limit_plays: int = 5
    rate_limit_window_seconds: int = 10
    rate_limit_stopall: int = 3
    rate_limit_stopall_window_seconds: int = 5
    rate_limit_votes: int = 3
    rate_limit_votes_window_seconds: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()

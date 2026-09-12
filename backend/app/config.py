from __future__ import annotations

import tempfile
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://sentinel:sentinel@localhost:5432/sentinelai"
    scan_timeout_seconds: int = 300
    scan_work_dir: str = str(Path(tempfile.gettempdir()) / "sentinelai-scans")
    clone_depth: int = 1
    semgrep_config: str = "p/security-audit"


settings = Settings()

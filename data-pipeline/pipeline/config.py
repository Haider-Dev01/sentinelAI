from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PIPELINE_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    nvd_api_key: str | None = None
    openai_api_key: str | None = None
    nvd_request_delay_seconds: float = 6.0
    http_timeout_seconds: float = 30.0
    user_agent: str = "SentinelAI-PFE/0.2 (educational portfolio; data-pipeline)"

    data_dir: Path = PIPELINE_ROOT / "data"
    chroma_dir: Path = PIPELINE_ROOT / "data" / "chroma"
    golden_set_path: Path = REPO_ROOT / "eval" / "golden_set.json"

    owasp_raw_base: str = (
        "https://raw.githubusercontent.com/OWASP/Top10/master/2025/docs/en"
    )
    nvd_api_base: str = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    openai_embeddings_url: str = "https://api.openai.com/v1/embeddings"

    nvd_results_per_cwe: int = 15
    nvd_max_documents: int = 250

    # Provisional chunk hyperparameters — compared numerically in Phase 3.
    fixed_chunk_size: int = 800
    fixed_chunk_overlap: int = 120
    paragraph_max_chars: int = 1200
    section_max_chars: int = 1600


settings = Settings()


def raw_dir() -> Path:
    path = settings.data_dir / "raw"
    path.mkdir(parents=True, exist_ok=True)
    return path


def processed_dir() -> Path:
    path = settings.data_dir / "processed"
    path.mkdir(parents=True, exist_ok=True)
    return path

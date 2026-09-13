from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


class HashEmbedder:
    name = "hash-test"
    dimensions = 8

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        raw = [byte / 255.0 for byte in digest[: self.dimensions]]
        norm = sum(value * value for value in raw) ** 0.5 or 1.0
        return [value / norm for value in raw]


@pytest.fixture
def owasp_markdown() -> str:
    return (FIXTURES / "owasp_injection.md").read_text(encoding="utf-8")


@pytest.fixture
def nvd_payload() -> dict:
    return json.loads((FIXTURES / "nvd_sample.json").read_text(encoding="utf-8"))


@pytest.fixture
def tmp_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr("pipeline.config.settings.data_dir", tmp_path)
    monkeypatch.setattr("pipeline.config.settings.chroma_dir", tmp_path / "chroma")
    monkeypatch.setattr("pipeline.config.settings.nvd_request_delay_seconds", 0)
    return tmp_path

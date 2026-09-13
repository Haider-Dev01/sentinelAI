from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from pipeline.ingest.nvd import fetch_nvd_sample
from pipeline.ingest.owasp import fetch_owasp_pages


def test_fetch_owasp_uses_cache_then_http(tmp_data: Path, owasp_markdown: str):
    filename = "A01_2025-Broken_Access_Control.md"
    cached = tmp_data / "raw" / filename
    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_text(owasp_markdown, encoding="utf-8")

    with patch("pipeline.ingest.owasp.OWASP_2025_PAGES", (("A01:2025", "broken_access_control", filename),)):
        documents = fetch_owasp_pages()
    assert len(documents) == 1
    assert documents[0].id == "owasp:A01:2025"


def test_fetch_owasp_downloads_when_uncached(tmp_data: Path, owasp_markdown: str):
    filename = "A05_2025-Injection.md"
    with (
        patch("pipeline.ingest.owasp.OWASP_2025_PAGES", (("A05:2025", "injection", filename),)),
        patch("pipeline.ingest.owasp.request_text", return_value=owasp_markdown) as mocked,
    ):
        documents = fetch_owasp_pages()
    mocked.assert_called_once()
    assert (tmp_data / "raw" / filename).exists()
    assert documents[0].category == "injection"


def test_fetch_nvd_sample_canonical_and_cwe(tmp_data: Path, nvd_payload: dict):
    with patch("pipeline.ingest.nvd._get_cves", side_effect=lambda params, cache_name: nvd_payload):
        documents = fetch_nvd_sample(
            canonical_ids=["CVE-2021-44228"],
            seed_cwes=(("CWE-89", "A05:2025", "injection"),),
            results_per_cwe=5,
            max_documents=10,
            delay=False,
        )
    ids = {doc.id for doc in documents}
    assert "cve:CVE-2021-44228" in ids
    assert "cve:CVE-2099-0000" not in ids

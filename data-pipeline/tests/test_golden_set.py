from __future__ import annotations

import json
from pathlib import Path

from pipeline.config import REPO_ROOT
from pipeline.taxonomy import CANONICAL_CVE_IDS, OWASP_2025_PAGES

GOLDEN = REPO_ROOT / "eval" / "golden_set.json"


def test_golden_set_shape_and_coverage():
    payload = json.loads(GOLDEN.read_text(encoding="utf-8"))
    pairs = payload["pairs"]
    assert 15 <= len(pairs) <= 20
    ids = [item["id"] for item in pairs]
    assert len(ids) == len(set(ids))
    for item in pairs:
        assert item["question"].strip()
        assert item["expected_answer"].strip()
        assert item["must_contain"]
        assert item["relevant_doc_ids"]
        assert item["category"]

    owasp_ids = {f"owasp:{owasp_id}" for owasp_id, _cat, _file in OWASP_2025_PAGES}
    mentioned = {doc_id for item in pairs for doc_id in item["relevant_doc_ids"]}
    assert owasp_ids & mentioned, "golden set should ground at least one OWASP page"
    cve_mentions = {doc_id.removeprefix("cve:") for doc_id in mentioned if doc_id.startswith("cve:")}
    assert cve_mentions <= set(CANONICAL_CVE_IDS)
    assert Path(GOLDEN).is_file()

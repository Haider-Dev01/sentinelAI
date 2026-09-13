from pathlib import Path
from unittest.mock import patch

from pipeline.ingest.nvd import fetch_nvd_sample, parse_nvd_payload
from pipeline.taxonomy import category_for_cwes


def test_parse_nvd_skips_rejected_and_maps_cwe(nvd_payload: dict):
    documents = parse_nvd_payload(nvd_payload)
    assert len(documents) == 1
    doc = documents[0]
    assert doc.id == "cve:CVE-2021-44228"
    assert doc.source == "nvd"
    assert doc.severity == "critical"
    assert doc.category == "injection"
    assert "Log4j2" in doc.text
    assert "CWE-917" in doc.metadata["cwes"]
    assert doc.metadata["owasp_id"] == "A05:2025"


def test_parse_nvd_fallback_cwe():
    payload = {
        "vulnerabilities": [
            {
                "cve": {
                    "id": "CVE-2020-8203",
                    "vulnStatus": "Analyzed",
                    "descriptions": [{"lang": "en", "value": "Prototype pollution in lodash."}],
                    "metrics": {
                        "cvssMetricV30": [
                            {
                                "type": "Primary",
                                "cvssData": {"baseScore": 7.4, "baseSeverity": "HIGH"},
                            }
                        ]
                    },
                    "weaknesses": [],
                }
            }
        ]
    }
    documents = parse_nvd_payload(payload, fallback_cwe="CWE-1321")
    assert documents[0].category == "software_or_data_integrity_failures"
    assert documents[0].severity == "high"


def test_parse_nvd_edge_cases():
    payload = {
        "vulnerabilities": [
            {"cve": {"id": None}},
            {
                "cve": {
                    "id": "CVE-2022-0001",
                    "vulnStatus": "Analyzed",
                    "descriptions": [{"lang": "fr", "value": "Description française."}],
                    "metrics": {"cvssMetricV2": [{"cvssData": {"baseScore": 5.0}}]},
                    "weaknesses": [{"description": [{"value": "CWE-NOINFO"}]}],
                }
            },
            {
                "cve": {
                    "id": "CVE-2022-0002",
                    "descriptions": [],
                    "metrics": {},
                }
            },
        ]
    }
    documents = parse_nvd_payload(payload)
    assert len(documents) == 1
    assert documents[0].id == "cve:CVE-2022-0001"
    assert documents[0].severity == "medium"


def test_get_cves_uses_api_key_and_rejects_bad_payload(monkeypatch):
    from pipeline.ingest import nvd as nvd_mod

    monkeypatch.setattr(nvd_mod.settings, "nvd_api_key", "test-key")
    with patch("pipeline.ingest.nvd.request_json", return_value={"vulnerabilities": []}) as mocked:
        nvd_mod._get_cves(params={"cveId": "CVE-2021-44228"}, cache_name="x.json")
    assert mocked.call_args.kwargs["headers"]["apiKey"] == "test-key"

    with patch("pipeline.ingest.nvd.request_json", return_value=[1, 2]):
        try:
            nvd_mod._get_cves(params={"cveId": "CVE-1"}, cache_name="y.json")
        except ValueError:
            return
        raise AssertionError("expected ValueError")


def test_fetch_nvd_respects_max_documents(tmp_data: Path, nvd_payload: dict):
    fat = {
        "vulnerabilities": [
            {
                "cve": {
                    "id": f"CVE-2020-{i:04d}",
                    "vulnStatus": "Analyzed",
                    "descriptions": [{"lang": "en", "value": f"Issue {i}."}],
                    "metrics": {
                        "cvssMetricV31": [
                            {"type": "Primary", "cvssData": {"baseScore": 9.1, "baseSeverity": "CRITICAL"}}
                        ]
                    },
                    "weaknesses": [{"description": [{"value": "CWE-89"}]}],
                }
            }
            for i in range(8)
        ]
    }
    with patch("pipeline.ingest.nvd._get_cves", return_value=fat):
        documents = fetch_nvd_sample(
            canonical_ids=["CVE-2020-0000"],
            seed_cwes=(("CWE-89", "A05:2025", "injection"),),
            max_documents=3,
            delay=False,
        )
    assert len(documents) == 3


def test_category_for_unknown_cwe():
    assert category_for_cwes(["CWE-99999"]) == ("unmapped", "unmapped")
    assert category_for_cwes(["CWE-798"])[0] == "A07:2025"

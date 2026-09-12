from __future__ import annotations

from pathlib import Path

from app.models.enums import FindingType, Severity
from app.services.scanners.gitleaks import parse_gitleaks_json
from app.services.scanners.osv import parse_osv_json
from app.services.scanners.semgrep import parse_semgrep_json
from app.services.scanners.severity import cvss_vector_to_severity, score_to_severity
from tests.conftest import load_fixture


def test_parse_semgrep_json_maps_severity_and_fields():
    findings = parse_semgrep_json(load_fixture("semgrep.json"), repo_root=Path("/repo"))
    assert len(findings) == 3

    high = findings[0]
    assert high.file_path == "app/utils.py"
    assert high.line == 42
    assert high.type == FindingType.SAST
    assert high.severity == Severity.HIGH
    assert high.scanner == "semgrep"
    assert high.rule_id.endswith("dangerous-subprocess-use")
    assert "command injection" in high.description.lower()

    assert findings[1].severity == Severity.MEDIUM
    assert findings[2].severity == Severity.INFO


def test_parse_semgrep_empty_and_list_payload():
    assert parse_semgrep_json(None) == []
    assert parse_semgrep_json({}) == []
    listed = parse_semgrep_json(
        [{"check_id": "x", "path": "a.py", "start": {"line": 1}, "extra": {"message": "m", "severity": "ERROR"}}]
    )
    assert len(listed) == 1
    assert listed[0].rule_id == "x"


def test_parse_gitleaks_redacts_secrets():
    findings = parse_gitleaks_json(load_fixture("gitleaks.json"), repo_root=Path("/repo"))
    assert len(findings) == 2
    first = findings[0]
    assert first.type == FindingType.SECRET
    assert first.severity == Severity.HIGH
    assert first.file_path == "config/settings.py"
    assert first.line == 12
    assert first.rule_id == "generic-api-key"
    assert first.raw["Secret"] == "[REDACTED]"
    assert first.raw["Match"] == "[REDACTED]"
    assert first.raw["Fingerprint"] == "[REDACTED]"
    assert "sk-live" not in first.description
    assert findings[1].file_path == ".env"


def test_parse_gitleaks_wrapped_findings_key():
    findings = parse_gitleaks_json(load_fixture("gitleaks_wrapped.json"))
    assert len(findings) == 1
    assert findings[0].rule_id == "github-pat"
    assert findings[0].raw["Secret"] == "[REDACTED]"


def test_parse_gitleaks_empty():
    assert parse_gitleaks_json(None) == []
    assert parse_gitleaks_json([]) == []
    assert parse_gitleaks_json({"findings": []}) == []


def test_parse_osv_json_emits_cve_and_group_findings():
    findings = parse_osv_json(load_fixture("osv.json"), repo_root=Path("/repo"))
    assert len(findings) == 3

    lodash = findings[0]
    assert lodash.type == FindingType.DEPENDENCY
    assert lodash.severity == Severity.HIGH
    assert lodash.rule_id == "CVE-2020-8203"
    assert lodash.file_path == "frontend/package-lock.json"
    assert lodash.line is None
    assert "lodash@4.17.15" in lodash.description

    grouped = findings[1]
    assert grouped.severity == Severity.CRITICAL
    assert grouped.rule_id == "GHSA-xvch-5gv4-qwvr"
    assert "minimist@1.2.5" in grouped.description

    django = findings[2]
    assert django.file_path == "backend/requirements.txt"
    assert django.severity == Severity.CRITICAL
    assert django.rule_id == "GHSA-xxxx-yyyy-zzzz"


def test_parse_osv_empty():
    assert parse_osv_json(None) == []
    assert parse_osv_json({"results": []}) == []
    assert parse_osv_json({"unexpected": True}) == []


def test_cvss_critical_vector_and_score_buckets():
    assert cvss_vector_to_severity("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H") == Severity.CRITICAL
    assert score_to_severity(9.8) == Severity.CRITICAL
    assert score_to_severity(7.5) == Severity.HIGH
    assert score_to_severity(5.0) == Severity.MEDIUM
    assert score_to_severity(1.2) == Severity.LOW
    assert score_to_severity(0) == Severity.INFO
    assert cvss_vector_to_severity("not-a-vector") is None

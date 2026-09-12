from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from app.models.enums import FindingType, Severity
from app.services.scanners.base import NormalizedFinding
from app.services.scanners.process import (
    ensure_success,
    load_json_file,
    relativize,
    run_process,
    which_or_raise,
)

_REDACTED_KEYS = frozenset({"Secret", "secret", "Match", "match", "Fingerprint"})


class GitleaksScanner:
    name = "gitleaks"

    def scan(self, repo_path: str) -> list[NormalizedFinding]:
        binary = which_or_raise("gitleaks")
        root = Path(repo_path)
        with tempfile.NamedTemporaryFile(prefix="gitleaks-", suffix=".json", delete=False) as handle:
            report_path = Path(handle.name)
        try:
            command = [
                binary,
                "detect",
                "--source",
                str(root),
                "--report-format",
                "json",
                "--report-path",
                str(report_path),
                "--no-banner",
            ]
            if not (root / ".git").exists():
                command.append("--no-git")
            result = run_process(command, cwd=root)
            ensure_success(result, self.name)
            payload = load_json_file(report_path)
            return parse_gitleaks_json(payload, repo_root=root)
        finally:
            report_path.unlink(missing_ok=True)


def parse_gitleaks_json(payload: Any, repo_root: Path | None = None) -> list[NormalizedFinding]:
    """Normalize a Gitleaks JSON report.

    Accepts either a bare list of leaks or `{"findings": [...]}` / `{"leaks": [...]}`.
    Secret material is redacted before it is persisted.
    """
    items = _extract_items(payload)
    root = repo_root or Path(".")
    findings: list[NormalizedFinding] = []
    for item in items:
        file_path = item.get("File") or item.get("file") or item.get("Path") or "unknown"
        line = item.get("StartLine") or item.get("startLine") or item.get("line")
        rule_id = item.get("RuleID") or item.get("ruleID") or item.get("Rule")
        description = item.get("Description") or item.get("description") or "Secret detected"
        findings.append(
            NormalizedFinding(
                file_path=relativize(str(file_path), root),
                line=int(line) if line is not None else None,
                type=FindingType.SECRET,
                severity=Severity.HIGH,
                description=str(description),
                rule_id=str(rule_id) if rule_id else None,
                scanner="gitleaks",
                raw=_redact(item),
            )
        )
    return findings


def _extract_items(payload: Any) -> list[dict[str, Any]]:
    if not payload:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    for key in ("findings", "leaks", "results"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _redact(item: dict[str, Any]) -> dict[str, Any]:
    redacted = {}
    for key, value in item.items():
        if key in _REDACTED_KEYS:
            redacted[key] = "[REDACTED]"
        else:
            redacted[key] = value
    return redacted

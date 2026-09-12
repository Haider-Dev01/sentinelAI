from __future__ import annotations

from pathlib import Path
from typing import Any

from app.config import settings
from app.models.enums import FindingType
from app.services.scanners.base import NormalizedFinding
from app.services.scanners.process import (
    ensure_success,
    load_json,
    relativize,
    run_process,
    which_or_raise,
)
from app.services.scanners.severity import map_semgrep_severity


class SemgrepScanner:
    name = "semgrep"

    def scan(self, repo_path: str) -> list[NormalizedFinding]:
        binary = which_or_raise("semgrep")
        root = Path(repo_path)
        result = run_process(
            [
                binary,
                "scan",
                "--config",
                settings.semgrep_config,
                "--json",
                "--metrics=off",
                "--quiet",
                "--disable-version-check",
                str(root),
            ],
            cwd=root,
        )
        ensure_success(result, self.name)
        payload = load_json(result.stdout) or {}
        return parse_semgrep_json(payload, repo_root=root)


def parse_semgrep_json(payload: Any, repo_root: Path | None = None) -> list[NormalizedFinding]:
    """Normalize a Semgrep `--json` report into Finding records.

    Expected shape: `{"results": [{"check_id", "path", "start": {"line"}, "extra": {...}}]}`.
    """
    if not payload:
        return []
    if isinstance(payload, list):
        results = payload
    else:
        results = payload.get("results") or []

    findings: list[NormalizedFinding] = []
    root = repo_root or Path(".")
    for item in results:
        extra = item.get("extra") or {}
        start = item.get("start") or {}
        path = item.get("path") or item.get("check_id") or "unknown"
        line = start.get("line")
        message = extra.get("message") or item.get("check_id") or "Semgrep finding"
        check_id = item.get("check_id")
        findings.append(
            NormalizedFinding(
                file_path=relativize(str(path), root),
                line=int(line) if line is not None else None,
                type=FindingType.SAST,
                severity=map_semgrep_severity(extra.get("severity")),
                description=str(message),
                rule_id=str(check_id) if check_id else None,
                scanner="semgrep",
                raw={
                    "check_id": check_id,
                    "severity": extra.get("severity"),
                    "metadata": extra.get("metadata") or {},
                    "start": start,
                    "end": item.get("end") or {},
                },
            )
        )
    return findings

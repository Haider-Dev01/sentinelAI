from __future__ import annotations

from pathlib import Path
from typing import Any

from app.models.enums import FindingType, Severity
from app.services.scanners.base import NormalizedFinding
from app.services.scanners.process import (
    ScannerExecutionError,
    load_json,
    relativize,
    run_process,
    which_or_raise,
)
from app.services.scanners.severity import cvss_vector_to_severity, map_named_severity

_NO_PACKAGE_MARKERS = (
    "no packages found",
    "no package sources found",
    "scanned 0 packages",
)


class OSVScanner:
    name = "osv-scanner"

    def scan(self, repo_path: str) -> list[NormalizedFinding]:
        binary = which_or_raise("osv-scanner")
        root = Path(repo_path)
        result = run_process(
            [binary, "scan", "--format", "json", "-r", str(root)],
            cwd=root,
        )
        if result.returncode not in {0, 1}:
            combined = f"{result.stderr or ''} {result.stdout or ''}".lower()
            if any(marker in combined for marker in _NO_PACKAGE_MARKERS):
                return []
            raise ScannerExecutionError(
                f"osv-scanner failed (exit {result.returncode}): "
                f"{(result.stderr or result.stdout or '').strip()}"
            )
        payload = load_json(result.stdout) or {}
        return parse_osv_json(payload, repo_root=root)


def parse_osv_json(payload: Any, repo_root: Path | None = None) -> list[NormalizedFinding]:
    """Normalize an OSV-Scanner JSON report (`osv-scanner --format json`).

    Walks `results[].packages[].vulnerabilities[]` and emits one Finding per CVE/GHSA.
    Line is left unset: lockfiles do not give a stable source line without extra parsing.
    """
    if not payload:
        return []
    results = payload.get("results") if isinstance(payload, dict) else payload
    if not isinstance(results, list):
        return []

    root = repo_root or Path(".")
    findings: list[NormalizedFinding] = []
    for result in results:
        source = result.get("source") or {}
        source_path = source.get("path") or "unknown"
        for package in result.get("packages") or []:
            pkg = package.get("package") or {}
            name = pkg.get("name") or "unknown"
            version = pkg.get("version") or "?"
            ecosystem = pkg.get("ecosystem") or ""
            vulns = package.get("vulnerabilities") or []
            if not vulns:
                for group in package.get("groups") or []:
                    findings.append(
                        _from_group(group, source_path, name, version, ecosystem, root)
                    )
                continue
            for vuln in vulns:
                findings.append(
                    _from_vuln(vuln, source_path, name, version, ecosystem, root)
                )
    return findings


def _from_vuln(
    vuln: dict[str, Any],
    source_path: str,
    name: str,
    version: str,
    ecosystem: str,
    root: Path,
) -> NormalizedFinding:
    vuln_id = vuln.get("id") or "UNKNOWN"
    aliases = vuln.get("aliases") or []
    cve = next((alias for alias in aliases if str(alias).startswith("CVE-")), None)
    rule_id = str(cve or vuln_id)
    summary = vuln.get("summary") or vuln.get("details") or "Known vulnerability"
    description = f"{name}@{version} ({ecosystem}): {summary} [{rule_id}]"
    return NormalizedFinding(
        file_path=relativize(str(source_path), root),
        line=None,
        type=FindingType.DEPENDENCY,
        severity=_osv_severity(vuln),
        description=description,
        rule_id=rule_id,
        scanner="osv-scanner",
        raw={
            "id": vuln_id,
            "aliases": aliases,
            "package": {"name": name, "version": version, "ecosystem": ecosystem},
            "database_specific": vuln.get("database_specific") or {},
        },
    )


def _from_group(
    group: dict[str, Any],
    source_path: str,
    name: str,
    version: str,
    ecosystem: str,
    root: Path,
) -> NormalizedFinding:
    ids = group.get("ids") or []
    rule_id = str(ids[0]) if ids else "UNKNOWN"
    severity = map_named_severity(group.get("max_severity"))
    description = f"{name}@{version} ({ecosystem}): grouped advisory [{', '.join(str(i) for i in ids)}]"
    return NormalizedFinding(
        file_path=relativize(str(source_path), root),
        line=None,
        type=FindingType.DEPENDENCY,
        severity=severity,
        description=description,
        rule_id=rule_id,
        scanner="osv-scanner",
        raw={"group": group, "package": {"name": name, "version": version, "ecosystem": ecosystem}},
    )


def _osv_severity(vuln: dict[str, Any]) -> Severity:
    db_specific = vuln.get("database_specific") or {}
    named = db_specific.get("severity")
    if named:
        return map_named_severity(str(named))
    for entry in vuln.get("severity") or []:
        score = entry.get("score")
        if isinstance(score, str) and score.startswith("CVSS:"):
            mapped = cvss_vector_to_severity(score)
            if mapped:
                return mapped
        if isinstance(score, (int, float)):
            from app.services.scanners.severity import score_to_severity

            return score_to_severity(float(score))
    return Severity.MEDIUM

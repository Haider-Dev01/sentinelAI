from __future__ import annotations

from typing import Any

_SEV = ("critical", "high", "medium", "low", "info")


def dashboard_scan_url(dashboard_url: str, scan_id: str) -> str:
    return f"{dashboard_url.rstrip('/')}/scans/{scan_id}"


def severity_counts(scan: dict[str, Any], findings: list[dict[str, Any]]) -> dict[str, int]:
    """Prefer API counts; otherwise tally GET /scans/{id} findings (ScanRead has no severity_counts)."""
    raw = scan.get("severity_counts") or {}
    if isinstance(raw, dict) and any(int(raw.get(key) or 0) for key in _SEV):
        return {key: int(raw.get(key) or 0) for key in _SEV}
    counts = {key: 0 for key in _SEV}
    for item in findings:
        sev = str(item.get("severity") or "").lower()
        if sev in counts:
            counts[sev] += 1
    return counts


def format_comment(scan: dict[str, Any], dashboard_url: str) -> str:
    """Markdown summary posted on the consumer PR."""
    status = str(scan.get("status") or "unknown")
    findings = list(scan.get("findings") or [])
    counts = severity_counts(scan, findings)
    scan_id = str(scan.get("id") or "")
    repo = (scan.get("repository") or {}).get("name") or "repository"
    total = scan.get("findings_count")
    if total is None:
        total = len(findings)
    link = dashboard_scan_url(dashboard_url, scan_id)
    lines = [
        "## SentinelAI scan",
        "",
        f"**Repository:** `{repo}`  ",
        f"**Status:** `{status}`  ",
        (
            f"**Findings:** {total} "
            f"(C{int(counts.get('critical') or 0)} "
            f"H{int(counts.get('high') or 0)} "
            f"M{int(counts.get('medium') or 0)} "
            f"L{int(counts.get('low') or 0)} "
            f"I{int(counts.get('info') or 0)})"
        ),
        "",
        f"[Open in dashboard]({link})",
        "",
    ]
    error = scan.get("error_message")
    if error:
        lines.extend([f"> {error}", ""])
    if not findings:
        lines.append("_No findings reported._")
    else:
        lines.extend(
            [
                "| Severity | Type | File | Rule | Scanner |",
                "|---|---|---|---|---|",
            ]
        )
        for item in findings[:30]:
            path = str(item.get("file_path") or "")
            line = item.get("line")
            loc = f"{path}:{line}" if line else path
            rule = item.get("rule_id") or "—"
            lines.append(
                f"| {item.get('severity') or '—'} | {item.get('type') or '—'} "
                f"| `{loc}` | `{rule}` | {item.get('scanner') or '—'} |"
            )
        extra = len(findings) - 30
        if extra > 0:
            lines.append(f"| … | | _{extra} more_ | | |")
    lines.extend(["", "—", "_Posted by the reusable SentinelAI GitHub Action._"])
    return "\n".join(lines) + "\n"

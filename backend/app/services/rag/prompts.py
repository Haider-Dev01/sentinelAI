from __future__ import annotations

from typing import Any

EXPLAIN_SYSTEM = (
    "You are a senior AppSec engineer. Use ONLY the retrieved OWASP/CVE context. "
    "If the context is insufficient, say so. Never invent CVE ids. "
    "Reply in JSON with keys explanation, fix, language. "
    "`fix` must be a complete, syntactically valid code snippet in a markdown fence."
)


def finding_query(finding: Any) -> str:
    parts = [
        getattr(finding, "type", None) or (finding.get("type") if isinstance(finding, dict) else None),
        getattr(finding, "rule_id", None) or (finding.get("rule_id") if isinstance(finding, dict) else None),
        getattr(finding, "description", None) or (finding.get("description") if isinstance(finding, dict) else None),
        getattr(finding, "file_path", None) or (finding.get("file_path") if isinstance(finding, dict) else None),
    ]
    return " ".join(str(part) for part in parts if part).strip()


def build_user_prompt(finding: Any, contexts: list[str]) -> str:
    if isinstance(finding, dict):
        data = finding
        raw = finding.get("raw") or {}
    else:
        data = {
            "type": finding.type,
            "severity": finding.severity,
            "scanner": finding.scanner,
            "rule_id": finding.rule_id,
            "file_path": finding.file_path,
            "line": finding.line,
            "description": finding.description,
        }
        raw = finding.raw or {}
    snippet = raw.get("snippet") or ""
    snippet_block = f"\nVulnerable snippet:\n```\n{snippet}\n```\n" if snippet else ""
    context = "\n\n---\n\n".join(contexts) if contexts else "(no retrieved context)"
    return (
        f"Finding type: {data.get('type')}\n"
        f"Severity: {data.get('severity')}\n"
        f"Scanner: {data.get('scanner')}\n"
        f"Rule: {data.get('rule_id')}\n"
        f"File: {data.get('file_path')}:{data.get('line')}\n"
        f"Description: {data.get('description')}\n"
        f"{snippet_block}\n"
        f"Retrieved context:\n{context}\n\n"
        "Return JSON: {\"explanation\": \"...\", \"fix\": \"```python\\n...\\n```\", \"language\": \"python\"}"
    )

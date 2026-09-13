from __future__ import annotations

from typing import Any, Protocol


EXPLAIN_SYSTEM = (
    "You are a senior AppSec engineer. Use ONLY the retrieved OWASP/CVE context. "
    "If the context is insufficient, say so. Never invent CVE ids. "
    "Reply in JSON with keys explanation, fix, language. "
    "`fix` must be a complete, syntactically valid code snippet in a markdown fence."
)


def finding_query(finding: dict[str, Any]) -> str:
    parts = [
        finding.get("type") or "",
        finding.get("rule_id") or "",
        finding.get("description") or "",
        finding.get("file_path") or "",
    ]
    return " ".join(part for part in parts if part).strip()


def build_user_prompt(finding: dict[str, Any], contexts: list[str]) -> str:
    context = "\n\n---\n\n".join(contexts) if contexts else "(no retrieved context)"
    snippet = finding.get("snippet") or finding.get("raw", {}).get("snippet") or ""
    snippet_block = f"\nVulnerable snippet:\n```\n{snippet}\n```\n" if snippet else ""
    return (
        f"Finding type: {finding.get('type')}\n"
        f"Severity: {finding.get('severity')}\n"
        f"Scanner: {finding.get('scanner')}\n"
        f"Rule: {finding.get('rule_id')}\n"
        f"File: {finding.get('file_path')}:{finding.get('line')}\n"
        f"Description: {finding.get('description')}\n"
        f"{snippet_block}\n"
        f"Retrieved context:\n{context}\n\n"
        "Return JSON: {\"explanation\": \"...\", \"fix\": \"```python\\n...\\n```\", \"language\": \"python\"}"
    )


class LLMClient(Protocol):
    name: str
    usd_per_1k_input: float
    usd_per_1k_output: float

    def generate(self, prompt: str, *, system: str = EXPLAIN_SYSTEM) -> str: ...

from __future__ import annotations

import logging
from typing import Any, Iterable

from pipeline.config import raw_dir, settings
from pipeline.http import request_json, throttle_nvd
from pipeline.models import SourceDocument
from pipeline.taxonomy import (
    CANONICAL_CVE_IDS,
    NVD_SEED_CWES,
    category_for_cwes,
)

logger = logging.getLogger(__name__)


def fetch_nvd_sample(
    *,
    seed_cwes: Iterable[tuple[str, str, str]] | None = None,
    canonical_ids: Iterable[str] | None = None,
    results_per_cwe: int | None = None,
    max_documents: int | None = None,
    delay: bool = True,
) -> list[SourceDocument]:
    """Fetch a bounded NVD subset: seed CWEs + canonical CVE ids.

    Deduplicates on CVE id and stops at `max_documents`.
    """
    per_cwe = results_per_cwe if results_per_cwe is not None else settings.nvd_results_per_cwe
    cap = max_documents if max_documents is not None else settings.nvd_max_documents
    by_id: dict[str, SourceDocument] = {}

    for cve_id in canonical_ids if canonical_ids is not None else CANONICAL_CVE_IDS:
        cache_name = f"nvd-{cve_id}.json"
        if delay:
            _throttle_if_needed(cache_name)
        payload = _get_cves(params={"cveId": cve_id}, cache_name=cache_name)
        for doc in parse_nvd_payload(payload):
            by_id[doc.id] = doc
            if len(by_id) >= cap:
                break
        if len(by_id) >= cap:
            break

    for cwe, *_rest in seed_cwes if seed_cwes is not None else NVD_SEED_CWES:
        if len(by_id) >= cap:
            break
        cache_name = f"nvd-{cwe}.json"
        if delay:
            _throttle_if_needed(cache_name)
        payload = _get_cves(
            params={
                "cweId": cwe,
                "noRejected": "",
                "resultsPerPage": per_cwe,
                "startIndex": 0,
            },
            cache_name=cache_name,
        )
        for doc in parse_nvd_payload(payload, fallback_cwe=cwe):
            by_id.setdefault(doc.id, doc)
            if len(by_id) >= cap:
                break

    documents = list(by_id.values())
    logger.info("Ingested %s NVD CVE documents (cap=%s)", len(documents), cap)
    return documents


def parse_nvd_payload(payload: dict[str, Any], fallback_cwe: str | None = None) -> list[SourceDocument]:
    documents: list[SourceDocument] = []
    for item in payload.get("vulnerabilities") or []:
        cve = item.get("cve") or {}
        parsed = _parse_cve(cve, fallback_cwe=fallback_cwe)
        if parsed is not None:
            documents.append(parsed)
    return documents


def _parse_cve(cve: dict[str, Any], fallback_cwe: str | None = None) -> SourceDocument | None:
    cve_id = cve.get("id")
    if not cve_id or cve.get("vulnStatus") == "Rejected":
        return None
    description = _english_description(cve.get("descriptions") or [])
    if not description:
        return None
    cwes = _cwes(cve.get("weaknesses") or [])
    if fallback_cwe and fallback_cwe not in cwes:
        cwes.append(fallback_cwe)
    owasp_id, category = category_for_cwes(cwes)
    severity, score = _severity(cve.get("metrics") or {})
    title = f"{cve_id}: {description.split('.', 1)[0].strip()}"
    text = _cve_text(
        cve_id=cve_id,
        description=description,
        cwes=cwes,
        owasp_id=owasp_id,
        severity=severity,
        score=score,
        published=cve.get("published"),
    )
    return SourceDocument(
        id=f"cve:{cve_id}",
        source="nvd",
        title=title[:240],
        text=text,
        category=category,
        severity=severity,
        metadata={
            "cve_id": cve_id,
            "cwes": cwes,
            "owasp_id": owasp_id,
            "cvss_score": score,
            "published": cve.get("published"),
            "vuln_status": cve.get("vulnStatus"),
        },
    )


def _cve_text(
    *,
    cve_id: str,
    description: str,
    cwes: list[str],
    owasp_id: str,
    severity: str | None,
    score: float | None,
    published: str | None,
) -> str:
    lines = [
        f"# {cve_id}",
        "",
        description.strip(),
        "",
        f"OWASP mapping: {owasp_id}.",
        f"CWE: {', '.join(cwes) if cwes else 'unspecified'}.",
    ]
    if severity:
        score_bit = f" (CVSS {score})" if score is not None else ""
        lines.append(f"Severity: {severity}{score_bit}.")
    if published:
        lines.append(f"Published: {published}.")
    return "\n".join(lines)


def _english_description(descriptions: list[dict[str, Any]]) -> str:
    for item in descriptions:
        if item.get("lang") == "en" and item.get("value"):
            return str(item["value"]).strip()
    if descriptions and descriptions[0].get("value"):
        return str(descriptions[0]["value"]).strip()
    return ""


def _cwes(weaknesses: list[dict[str, Any]]) -> list[str]:
    found: list[str] = []
    for weak in weaknesses:
        for desc in weak.get("description") or []:
            value = str(desc.get("value") or "").strip().upper()
            if value.startswith("CWE-") and value not in found and value != "CWE-NOINFO":
                found.append(value)
    return found


def _severity(metrics: dict[str, Any]) -> tuple[str | None, float | None]:
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV40", "cvssMetricV2"):
        entries = metrics.get(key) or []
        if not entries:
            continue
        primary = next((item for item in entries if item.get("type") == "Primary"), entries[0])
        data = primary.get("cvssData") or {}
        severity = data.get("baseSeverity") or primary.get("baseSeverity")
        score = data.get("baseScore")
        if severity:
            return str(severity).lower(), float(score) if score is not None else None
        if score is not None:
            return _bucket(float(score)), float(score)
    return None, None


def _bucket(score: float) -> str:
    if score >= 9.0:
        return "critical"
    if score >= 7.0:
        return "high"
    if score >= 4.0:
        return "medium"
    if score > 0:
        return "low"
    return "none"


def _throttle_if_needed(cache_name: str) -> None:
    if not (raw_dir() / cache_name).exists():
        throttle_nvd()


def _get_cves(*, params: dict[str, Any], cache_name: str) -> dict[str, Any]:
    headers = {}
    if settings.nvd_api_key:
        headers["apiKey"] = settings.nvd_api_key
    logger.info("Fetching NVD %s", params)
    payload = request_json(
        settings.nvd_api_base,
        params=params,
        headers=headers or None,
        cache_name=cache_name,
    )
    if not isinstance(payload, dict):
        raise ValueError(f"Unexpected NVD payload for {params}")
    return payload

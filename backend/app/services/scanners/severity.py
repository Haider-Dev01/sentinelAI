from __future__ import annotations

from app.models.enums import Severity

_SEMGREP_SEVERITY = {
    "ERROR": Severity.HIGH,
    "WARNING": Severity.MEDIUM,
    "INFO": Severity.INFO,
    "CRITICAL": Severity.CRITICAL,
    "HIGH": Severity.HIGH,
    "MEDIUM": Severity.MEDIUM,
    "LOW": Severity.LOW,
}

_NAMED_SEVERITY = {
    "CRITICAL": Severity.CRITICAL,
    "HIGH": Severity.HIGH,
    "MEDIUM": Severity.MEDIUM,
    "MODERATE": Severity.MEDIUM,
    "LOW": Severity.LOW,
    "INFO": Severity.INFO,
    "UNKNOWN": Severity.MEDIUM,
}

def map_semgrep_severity(value: str | None) -> Severity:
    if not value:
        return Severity.MEDIUM
    return _SEMGREP_SEVERITY.get(value.upper(), Severity.MEDIUM)


def map_named_severity(value: str | None) -> Severity:
    if not value:
        return Severity.MEDIUM
    return _NAMED_SEVERITY.get(value.upper(), Severity.MEDIUM)


def cvss_vector_to_severity(vector: str | None) -> Severity | None:
    """Approximate CVSS v3 base score from the vector, then bucket it.

    Full CVSS libraries are deferred: Phase 1 only needs a stable, tested mapping
    so findings are comparable across scanners. The mapping is documented in tests.
    """
    if not vector:
        return None
    metrics = _parse_cvss_metrics(vector)
    if not metrics:
        return None
    score = _cvss3_base_score(metrics)
    return score_to_severity(score)


def score_to_severity(score: float) -> Severity:
    if score >= 9.0:
        return Severity.CRITICAL
    if score >= 7.0:
        return Severity.HIGH
    if score >= 4.0:
        return Severity.MEDIUM
    if score > 0:
        return Severity.LOW
    return Severity.INFO


def _parse_cvss_metrics(vector: str) -> dict[str, str] | None:
    cleaned = vector.strip()
    if cleaned.startswith("CVSS:"):
        cleaned = cleaned.split("/", 1)[-1]
    parts = {}
    for item in cleaned.split("/"):
        if ":" not in item:
            continue
        key, value = item.split(":", 1)
        parts[key] = value
    required = {"AV", "AC", "PR", "UI", "S", "C", "I", "A"}
    if not required.issubset(parts):
        return None
    return parts


def _cvss3_base_score(m: dict[str, str]) -> float:
    av = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2}[m["AV"]]
    ac = {"L": 0.77, "H": 0.44}[m["AC"]]
    ui = {"N": 0.85, "R": 0.62}[m["UI"]]
    scope_changed = m["S"] == "C"
    pr_table = {
        False: {"N": 0.85, "L": 0.62, "H": 0.27},
        True: {"N": 0.85, "L": 0.68, "H": 0.50},
    }
    pr = pr_table[scope_changed][m["PR"]]
    cia = {"N": 0.0, "L": 0.22, "H": 0.56}
    c, i, a = cia[m["C"]], cia[m["I"]], cia[m["A"]]
    isc_base = 1 - ((1 - c) * (1 - i) * (1 - a))
    if not scope_changed:
        impact = 6.42 * isc_base
    else:
        impact = 7.52 * (isc_base - 0.029) - 3.25 * (isc_base - 0.02) ** 15
    exploitability = 8.22 * av * ac * pr * ui
    if impact <= 0:
        return 0.0
    if not scope_changed:
        score = min(impact + exploitability, 10)
    else:
        score = min(1.08 * (impact + exploitability), 10)
    return _round_up(score)


def _round_up(value: float) -> float:
    return int(value * 10 + 0.9999) / 10 if value > 0 else 0.0

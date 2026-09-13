"""Maps NVD CWEs onto OWASP Top 10:2025 categories.

Each category is represented by a small set of high-signal CWEs rather than
the full mapped list (A01 alone has 40 CWEs). The selection favours weaknesses
that Semgrep/gitleaks/OSV actually surface in a fullstack Python/JS scan.
"""

from __future__ import annotations

OWASP_2025_PAGES: tuple[tuple[str, str, str], ...] = (
    ("A01:2025", "broken_access_control", "A01_2025-Broken_Access_Control.md"),
    ("A02:2025", "security_misconfiguration", "A02_2025-Security_Misconfiguration.md"),
    ("A03:2025", "software_supply_chain_failures", "A03_2025-Software_Supply_Chain_Failures.md"),
    ("A04:2025", "cryptographic_failures", "A04_2025-Cryptographic_Failures.md"),
    ("A05:2025", "injection", "A05_2025-Injection.md"),
    ("A06:2025", "insecure_design", "A06_2025-Insecure_Design.md"),
    ("A07:2025", "authentication_failures", "A07_2025-Authentication_Failures.md"),
    ("A08:2025", "software_or_data_integrity_failures", "A08_2025-Software_or_Data_Integrity_Failures.md"),
    ("A09:2025", "security_logging_and_alerting_failures", "A09_2025-Security_Logging_and_Alerting_Failures.md"),
    ("A10:2025", "mishandling_of_exceptional_conditions", "A10_2025-Mishandling_of_Exceptional_Conditions.md"),
)

# Primary CWEs sampled from NVD (one request per CWE).
NVD_SEED_CWES: tuple[tuple[str, str, str], ...] = (
    ("CWE-639", "A01:2025", "broken_access_control"),
    ("CWE-918", "A01:2025", "broken_access_control"),
    ("CWE-611", "A02:2025", "security_misconfiguration"),
    ("CWE-494", "A03:2025", "software_supply_chain_failures"),
    ("CWE-327", "A04:2025", "cryptographic_failures"),
    ("CWE-89", "A05:2025", "injection"),
    ("CWE-78", "A05:2025", "injection"),
    ("CWE-79", "A05:2025", "injection"),
    ("CWE-287", "A07:2025", "authentication_failures"),
    ("CWE-798", "A07:2025", "authentication_failures"),
    ("CWE-502", "A08:2025", "software_or_data_integrity_failures"),
    ("CWE-532", "A09:2025", "security_logging_and_alerting_failures"),
    ("CWE-755", "A10:2025", "mishandling_of_exceptional_conditions"),
)

# Always fetched by CVE id so the golden set has grounding documents.
CANONICAL_CVE_IDS: tuple[str, ...] = (
    "CVE-2021-44228",  # Log4Shell
    "CVE-2021-45046",  # Log4j follow-up
    "CVE-2022-22965",  # Spring4Shell
    "CVE-2022-42889",  # Text4Shell
    "CVE-2017-5638",  # Struts OGNL
    "CVE-2020-8203",  # lodash prototype pollution (Phase 1 fixture)
    "CVE-2021-44906",  # minimist (Phase 1 fixture)
    "CVE-2024-3094",  # xz-utils supply chain
    "CVE-2023-4863",  # libwebp heap buffer overflow
    "CVE-2021-26084",  # Confluence OGNL injection
    "CVE-2023-22515",  # Confluence broken access control
    "CVE-2018-7600",  # Drupalgeddon2
)

CWE_TO_CATEGORY: dict[str, tuple[str, str]] = {
    cwe: (owasp_id, category) for cwe, owasp_id, category in NVD_SEED_CWES
}

# Extra CWE mappings seen on canonical CVEs / OWASP pages.
CWE_TO_CATEGORY.update(
    {
        "CWE-20": ("A05:2025", "injection"),
        "CWE-22": ("A01:2025", "broken_access_control"),
        "CWE-77": ("A05:2025", "injection"),
        "CWE-94": ("A05:2025", "injection"),
        "CWE-200": ("A01:2025", "broken_access_control"),
        "CWE-284": ("A01:2025", "broken_access_control"),
        "CWE-285": ("A01:2025", "broken_access_control"),
        "CWE-307": ("A07:2025", "authentication_failures"),
        "CWE-319": ("A04:2025", "cryptographic_failures"),
        "CWE-326": ("A04:2025", "cryptographic_failures"),
        "CWE-352": ("A01:2025", "broken_access_control"),
        "CWE-384": ("A07:2025", "authentication_failures"),
        "CWE-400": ("A10:2025", "mishandling_of_exceptional_conditions"),
        "CWE-502": ("A08:2025", "software_or_data_integrity_failures"),
        "CWE-829": ("A03:2025", "software_supply_chain_failures"),
        "CWE-862": ("A01:2025", "broken_access_control"),
        "CWE-863": ("A01:2025", "broken_access_control"),
        "CWE-917": ("A05:2025", "injection"),
        "CWE-1321": ("A08:2025", "software_or_data_integrity_failures"),
    }
)


def category_for_cwes(cwes: list[str]) -> tuple[str, str]:
    for cwe in cwes:
        mapped = CWE_TO_CATEGORY.get(cwe.upper())
        if mapped:
            return mapped
    return ("unmapped", "unmapped")

from __future__ import annotations

import re

_IMAGE_RE = re.compile(r"!\[.*?\]\([^)]*\)(?:\{:[^}]*\})?")
_HTML_RE = re.compile(r"<[^>]+>")
_MKDOCS_ATTR_RE = re.compile(r"\{:[^}]+\}")
_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_SCORE_TABLE_RE = re.compile(
    r"^## Score table\..*?(?=^## )",
    re.MULTILINE | re.DOTALL | re.IGNORECASE,
)
_MULTI_BLANK_RE = re.compile(r"\n{3,}")


def clean_markdown(text: str) -> str:
    """Normalize OWASP mkdocs pages into plain structured text.

    Score tables are dropped: after HTML-to-markdown they become sparse numeric
    rows with no recoverable column headers, so they add tokens without signal.
    Headings, descriptions, prevention advice, attack scenarios and CWE lists
    are kept.
    """
    cleaned = text.replace("\r\n", "\n")
    cleaned = _SCORE_TABLE_RE.sub("", cleaned)
    cleaned = _IMAGE_RE.sub("", cleaned)
    cleaned = _MKDOCS_ATTR_RE.sub("", cleaned)
    cleaned = _HTML_RE.sub("", cleaned)
    cleaned = _LINK_RE.sub(r"\1", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = _MULTI_BLANK_RE.sub("\n\n", cleaned)
    return cleaned.strip()


def strip_heading_markup(title: str) -> str:
    title = _IMAGE_RE.sub("", title)
    title = _MKDOCS_ATTR_RE.sub("", title)
    return title.strip()

from __future__ import annotations

import logging
import re

from pipeline.clean import clean_markdown, strip_heading_markup
from pipeline.config import raw_dir, settings
from pipeline.http import request_text
from pipeline.models import SourceDocument
from pipeline.taxonomy import OWASP_2025_PAGES

logger = logging.getLogger(__name__)

_TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def fetch_owasp_pages() -> list[SourceDocument]:
    documents: list[SourceDocument] = []
    for owasp_id, category, filename in OWASP_2025_PAGES:
        raw = _load_page(filename)
        documents.append(parse_owasp_markdown(raw, owasp_id=owasp_id, category=category, filename=filename))
    logger.info("Ingested %s OWASP Top 10:2025 pages", len(documents))
    return documents


def parse_owasp_markdown(
    raw: str,
    *,
    owasp_id: str,
    category: str,
    filename: str,
) -> SourceDocument:
    text = clean_markdown(raw)
    match = _TITLE_RE.search(text)
    title = strip_heading_markup(match.group(1) if match else owasp_id)
    return SourceDocument(
        id=f"owasp:{owasp_id}",
        source="owasp",
        title=title,
        text=text,
        category=category,
        severity=None,
        metadata={
            "owasp_id": owasp_id,
            "edition": "2025",
            "filename": filename,
        },
    )


def _load_page(filename: str) -> str:
    cache = raw_dir() / filename
    if cache.exists():
        logger.info("Using cached OWASP page %s", filename)
        return cache.read_text(encoding="utf-8")
    url = f"{settings.owasp_raw_base}/{filename}"
    logger.info("Fetching OWASP page %s", url)
    body = request_text(url)
    cache.write_text(body, encoding="utf-8")
    return body

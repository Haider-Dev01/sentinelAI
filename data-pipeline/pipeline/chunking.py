from __future__ import annotations

import re

from pipeline.models import Chunk, ChunkStrategy, SourceDocument

_WHITESPACE_RE = re.compile(r"\s+")
_PARAGRAPH_RE = re.compile(r"\n\s*\n")
_HEADING_RE = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)


def chunk_document(
    document: SourceDocument,
    strategy: ChunkStrategy,
    *,
    fixed_size: int = 800,
    overlap: int = 120,
    paragraph_max_chars: int = 1200,
    section_max_chars: int = 1600,
) -> list[Chunk]:
    if strategy == "fixed":
        texts = fixed_size_chunks(document.text, size=fixed_size, overlap=overlap)
        extras: list[dict] = [{} for _ in texts]
    elif strategy == "paragraph":
        texts = paragraph_chunks(document.text, max_chars=paragraph_max_chars)
        extras = [{} for _ in texts]
    elif strategy == "section":
        sectioned = section_chunks(document.text, max_chars=section_max_chars)
        texts = [item[0] for item in sectioned]
        extras = [item[1] for item in sectioned]
    else:  # pragma: no cover
        raise ValueError(f"Unknown chunking strategy: {strategy}")
    return [_to_chunk(document, strategy, index, text, extras[index]) for index, text in enumerate(texts)]


def fixed_size_chunks(text: str, *, size: int = 800, overlap: int = 120) -> list[str]:
    """Sliding window on whitespace-normalized text, split on word boundaries.

    `size` and `overlap` are in characters. Overlap is clamped to size-1.
    """
    normalized = _WHITESPACE_RE.sub(" ", text).strip()
    if not normalized:
        return []
    if size <= 0:
        raise ValueError("size must be > 0")
    overlap = max(0, min(overlap, size - 1))
    chunks: list[str] = []
    start = 0
    length = len(normalized)
    while start < length:
        end = min(start + size, length)
        if end < length:
            pivot = normalized.rfind(" ", start, end)
            if pivot > start:
                end = pivot
        piece = normalized[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= length:
            break
        start = max(end - overlap, start + 1)
    return chunks


def paragraph_chunks(text: str, *, max_chars: int = 1200) -> list[str]:
    """Pack adjacent paragraphs until `max_chars`, without breaking short paragraphs.

    Oversized paragraphs fall back to `fixed_size_chunks` so no chunk exceeds the cap
    by more than a long token.
    """
    paragraphs = [part.strip() for part in _PARAGRAPH_RE.split(text) if part.strip()]
    if not paragraphs:
        return []
    packed: list[str] = []
    current: list[str] = []
    current_len = 0
    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                packed.append("\n\n".join(current))
                current, current_len = [], 0
            packed.extend(fixed_size_chunks(paragraph, size=max_chars, overlap=max(80, max_chars // 10)))
            continue
        extra = len(paragraph) + (2 if current else 0)
        if current and current_len + extra > max_chars:
            packed.append("\n\n".join(current))
            current, current_len = [paragraph], len(paragraph)
        else:
            current.append(paragraph)
            current_len += extra
    if current:
        packed.append("\n\n".join(current))
    return packed


def section_chunks(text: str, *, max_chars: int = 1600) -> list[tuple[str, dict[str, str | int]]]:
    """Split markdown on ATX headings (# / ## / ###), keeping the heading path.

    This matches OWASP Top 10 pages (Background, Description, How to prevent,
    Example attack scenarios, References, Mapped CWEs). Oversized sections are
    sub-split with paragraph packing.
    """
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        return [(chunk, {}) for chunk in paragraph_chunks(text, max_chars=max_chars)]

    sections: list[tuple[str, dict[str, str]]] = []
    preamble = text[: matches[0].start()].strip()
    if preamble:
        for piece in paragraph_chunks(preamble, max_chars=max_chars):
            sections.append((piece, {"section_title": "preamble", "heading_level": 0}))

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        title = match.group(2).strip()
        level = len(match.group(1))
        meta = {"section_title": title, "heading_level": level}
        if len(body) <= max_chars:
            sections.append((body, meta))
            continue
        for piece in paragraph_chunks(body, max_chars=max_chars):
            sections.append((piece, meta))
    return sections


def _to_chunk(
    document: SourceDocument,
    strategy: ChunkStrategy,
    index: int,
    text: str,
    extra: dict,
) -> Chunk:
    metadata = {
        "title": document.title,
        **document.metadata,
        **extra,
    }
    return Chunk(
        id=f"{document.id}::{strategy}::{index}",
        document_id=document.id,
        strategy=strategy,
        text=text,
        chunk_index=index,
        source=document.source,
        category=document.category,
        severity=document.severity,
        metadata=metadata,
    )

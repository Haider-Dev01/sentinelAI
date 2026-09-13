from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

SourceName = Literal["owasp", "nvd"]
ChunkStrategy = Literal["fixed", "paragraph", "section"]


class SourceDocument(BaseModel):
    """Unitary cleaned document before chunking."""

    id: str
    source: SourceName
    title: str
    text: str
    category: str
    severity: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Chunk(BaseModel):
    id: str
    document_id: str
    strategy: ChunkStrategy
    text: str
    chunk_index: int
    source: SourceName
    category: str
    severity: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def chroma_metadata(self) -> dict[str, str | int | float | bool]:
        """Stable scalar metadata for Chroma now and pgvector later."""
        meta = self.metadata
        cwes = meta.get("cwes")
        if isinstance(cwes, list):
            cwes_value = ",".join(str(item) for item in cwes)
        else:
            cwes_value = str(cwes or "")
        return {
            "document_id": self.document_id,
            "strategy": self.strategy,
            "source": self.source,
            "category": self.category,
            "chunk_index": self.chunk_index,
            "severity": self.severity or "",
            "title": str(meta.get("title") or ""),
            "section_title": str(meta.get("section_title") or ""),
            "heading_level": int(meta.get("heading_level") or 0),
            "owasp_id": str(meta.get("owasp_id") or ""),
            "cve_id": str(meta.get("cve_id") or ""),
            "cwes": cwes_value,
        }

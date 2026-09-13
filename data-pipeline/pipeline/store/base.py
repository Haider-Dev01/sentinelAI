from __future__ import annotations

from typing import Protocol, runtime_checkable

from pipeline.models import Chunk


class QueryMatch(dict):
    """Thin dict with attribute access for tests and later eval code."""

    @property
    def id(self) -> str:
        return str(self["id"])

    @property
    def text(self) -> str:
        return str(self["text"])

    @property
    def score(self) -> float:
        return float(self["score"])

    @property
    def metadata(self) -> dict:
        return dict(self.get("metadata") or {})


@runtime_checkable
class VectorStore(Protocol):
    """Backend-agnostic index. Chroma is Phase 2; pgvector can implement this later."""

    name: str

    def upsert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None: ...

    def query(self, embedding: list[float], k: int = 5) -> list[QueryMatch]: ...

    def count(self) -> int: ...


class PgVectorStore:
    """Placeholder so the swap in a later phase is an import change, not a rewrite."""

    name = "pgvector"

    def __init__(self, *args, **kwargs) -> None:  # pragma: no cover
        raise NotImplementedError(
            "pgvector is deferred until Phase 3 retrieval metrics justify leaving local Chroma"
        )

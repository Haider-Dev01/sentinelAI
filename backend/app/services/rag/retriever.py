from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.config import settings
from app.services.rag.prompts import finding_query


@dataclass
class RetrievedChunk:
    text: str
    document_id: str
    score: float
    source: str = ""


class Retriever(Protocol):
    def search(self, query: str, k: int = 5) -> list[RetrievedChunk]: ...


class StaticRetriever:
    """Test double / fallback when Chroma is not indexed."""

    def __init__(self, chunks: list[RetrievedChunk] | None = None) -> None:
        self.chunks = chunks or []

    def search(self, query: str, k: int = 5) -> list[RetrievedChunk]:
        return self.chunks[:k]


class ChromaRetriever:
    def __init__(
        self,
        *,
        collection: str | None = None,
        persist_dir: Path | None = None,
        embedder_name: str | None = None,
    ) -> None:
        import sys

        repo = Path(__file__).resolve().parents[4]
        pipeline_root = str(repo / "data-pipeline")
        if pipeline_root not in sys.path:
            sys.path.insert(0, pipeline_root)

        from pipeline.embeddings.minilm import get_embedder
        from pipeline.store.chroma import ChromaVectorStore

        self._embedder = get_embedder(embedder_name or settings.rag_embedder)
        self._store = ChromaVectorStore(
            collection=collection or settings.rag_collection,
            persist_dir=persist_dir or Path(settings.chroma_dir),
            in_memory=False,
        )
        self._fit_sparse_if_needed()

    def _fit_sparse_if_needed(self) -> None:
        fit = getattr(self._embedder, "fit", None)
        index = getattr(self._embedder, "_index", None)
        if callable(fit) and not index:
            corpus = self._store.documents()
            if corpus:
                fit(corpus)

    def search(self, query: str, k: int = 5) -> list[RetrievedChunk]:
        vector = self._embedder.embed_query(query)
        hits = self._store.query(vector, k=k)
        return [
            RetrievedChunk(
                text=hit.text,
                document_id=str(hit.metadata.get("document_id") or ""),
                score=float(hit.score),
                source=str(hit.metadata.get("source") or ""),
            )
            for hit in hits
        ]


def query_finding(finding) -> str:
    return finding_query(finding)

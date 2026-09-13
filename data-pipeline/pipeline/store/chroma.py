from __future__ import annotations

from pathlib import Path

import chromadb

from pipeline.config import settings
from pipeline.models import Chunk
from pipeline.store.base import QueryMatch, VectorStore


class ChromaVectorStore:
    name = "chroma"

    def __init__(
        self,
        collection: str,
        persist_dir: Path | None = None,
        in_memory: bool = False,
    ) -> None:
        if in_memory:
            if hasattr(chromadb, "EphemeralClient"):
                self._client = chromadb.EphemeralClient()
            else:
                self._client = chromadb.Client()
        else:
            path = persist_dir or settings.chroma_dir
            path.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(path))
        kwargs = {
            "name": _safe_name(collection),
            "metadata": {"hnsw:space": "cosine"},
        }
        try:
            self._collection = self._client.get_or_create_collection(
                **kwargs,
                embedding_function=None,
            )
        except TypeError:
            self._collection = self._client.get_or_create_collection(**kwargs)

    def upsert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")
        if not chunks:
            return
        self._collection.upsert(
            ids=[chunk.id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            metadatas=[chunk.chroma_metadata() for chunk in chunks],
            embeddings=embeddings,
        )

    def query(self, embedding: list[float], k: int = 5) -> list[QueryMatch]:
        if k <= 0 or self.count() == 0:
            return []
        result = self._collection.query(
            query_embeddings=[embedding],
            n_results=min(k, self.count()),
            include=["documents", "metadatas", "distances"],
        )
        ids = (result.get("ids") or [[]])[0]
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        matches: list[QueryMatch] = []
        for item_id, text, meta, distance in zip(ids, documents, metadatas, distances):
            matches.append(
                QueryMatch(
                    id=item_id,
                    text=text,
                    score=1.0 - float(distance),
                    metadata=meta or {},
                )
            )
        return matches

    def count(self) -> int:
        return int(self._collection.count())

    def documents(self) -> list[str]:
        if self.count() == 0:
            return []
        result = self._collection.get(include=["documents"])
        return list(result.get("documents") or [])


def get_vector_store(
    backend: str = "chroma",
    *,
    collection: str,
    persist_dir: Path | None = None,
    in_memory: bool = False,
) -> VectorStore:
    if backend == "chroma":
        return ChromaVectorStore(collection=collection, persist_dir=persist_dir, in_memory=in_memory)
    if backend == "pgvector":
        from pipeline.store.base import PgVectorStore

        return PgVectorStore()
    raise ValueError(f"Unknown vector store backend '{backend}'")


def _safe_name(name: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "-_." else "-" for char in name)
    return cleaned[:63] or "sentinelai"

from __future__ import annotations

import logging

from pipeline.chunking import chunk_document
from pipeline.config import processed_dir, settings
from pipeline.embeddings.base import Embedder
from pipeline.ingest.nvd import fetch_nvd_sample
from pipeline.ingest.owasp import fetch_owasp_pages
from pipeline.models import Chunk, ChunkStrategy, SourceDocument
from pipeline.persist import load_chunks, load_documents, write_jsonl
from pipeline.store.base import VectorStore

logger = logging.getLogger(__name__)

STRATEGIES: tuple[ChunkStrategy, ...] = ("fixed", "paragraph", "section")


def ingest_corpus(*, delay: bool = True) -> list[SourceDocument]:
    documents = fetch_owasp_pages() + fetch_nvd_sample(delay=delay)
    path = processed_dir() / "documents.jsonl"
    write_jsonl(path, documents)
    logger.info("Wrote %s documents to %s", len(documents), path)
    return documents


def ingest_eval_corpus(*, delay: bool = True) -> list[SourceDocument]:
    """OWASP Top 10:2025 + canonical CVEs only — aligned with the golden set."""
    documents = fetch_owasp_pages() + fetch_nvd_sample(seed_cwes=(), delay=delay)
    path = processed_dir() / "documents.jsonl"
    write_jsonl(path, documents)
    logger.info("Wrote %s eval-corpus documents to %s", len(documents), path)
    return documents


def chunk_corpus(
    documents: list[SourceDocument] | None = None,
    strategies: tuple[ChunkStrategy, ...] = STRATEGIES,
) -> dict[ChunkStrategy, list[Chunk]]:
    if documents is None:
        documents = load_documents(processed_dir() / "documents.jsonl")
    by_strategy: dict[ChunkStrategy, list[Chunk]] = {}
    for strategy in strategies:
        chunks: list[Chunk] = []
        for document in documents:
            chunks.extend(
                chunk_document(
                    document,
                    strategy,
                    fixed_size=settings.fixed_chunk_size,
                    overlap=settings.fixed_chunk_overlap,
                    paragraph_max_chars=settings.paragraph_max_chars,
                    section_max_chars=settings.section_max_chars,
                )
            )
        by_strategy[strategy] = chunks
        path = processed_dir() / f"chunks-{strategy}.jsonl"
        write_jsonl(path, chunks)
        logger.info("Wrote %s %s chunks to %s", len(chunks), strategy, path)
    return by_strategy


def index_chunks(
    chunks: list[Chunk] | None,
    embedder: Embedder,
    store: VectorStore,
    *,
    strategy: ChunkStrategy | None = None,
) -> int:
    if chunks is None:
        if strategy is None:
            raise ValueError("Provide chunks or a strategy name to load")
        chunks = load_chunks(processed_dir() / f"chunks-{strategy}.jsonl")
    if not chunks:
        return 0
    embeddings = embedder.embed_documents([chunk.text for chunk in chunks])
    store.upsert(chunks, embeddings)
    logger.info("Indexed %s chunks with %s into %s", len(chunks), embedder.name, store.name)
    return len(chunks)


def collection_name(embedder_name: str, strategy: str) -> str:
    return f"sentinelai-{embedder_name}-{strategy}"

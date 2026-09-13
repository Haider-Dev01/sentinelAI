from __future__ import annotations

import argparse
import logging
import sys

from pipeline.config import settings
from pipeline.embeddings.minilm import get_embedder
from pipeline.run import (
    STRATEGIES,
    chunk_corpus,
    collection_name,
    index_chunks,
    ingest_corpus,
    ingest_eval_corpus,
)
from pipeline.store.chroma import get_vector_store

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SentinelAI data pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Fetch OWASP Top 10:2025 + scoped NVD sample")
    ingest.add_argument("--no-delay", action="store_true", help="Skip NVD rate-limit sleep (cached/tests)")
    ingest.add_argument(
        "--eval-corpus",
        action="store_true",
        help="OWASP pages + canonical CVEs only (golden-set aligned)",
    )

    chunk = sub.add_parser("chunk", help="Chunk processed documents with all strategies")
    chunk.add_argument(
        "--strategy",
        choices=list(STRATEGIES) + ["all"],
        default="all",
    )

    index = sub.add_parser("index", help="Embed chunks and upsert into Chroma")
    index.add_argument("--embedder", choices=["minilm", "tfidf", "openai"], default="minilm")
    index.add_argument("--chunker", choices=list(STRATEGIES), default="section")
    index.add_argument("--backend", choices=["chroma", "pgvector"], default="chroma")

    sub.add_parser("build", help="ingest + chunk all strategies (no embeddings)")

    args = parser.parse_args(argv)
    if args.command == "ingest":
        if args.eval_corpus:
            ingest_eval_corpus(delay=not args.no_delay)
        else:
            ingest_corpus(delay=not args.no_delay)
    elif args.command == "chunk":
        strategies = STRATEGIES if args.strategy == "all" else (args.strategy,)
        chunk_corpus(strategies=strategies)
    elif args.command == "index":
        embedder = get_embedder(args.embedder, openai_api_key=settings.openai_api_key)
        store = get_vector_store(
            args.backend,
            collection=collection_name(embedder.name, args.chunker),
        )
        index_chunks(None, embedder, store, strategy=args.chunker)
    elif args.command == "build":
        ingest_corpus(delay=True)
        chunk_corpus()
    return 0


if __name__ == "__main__":
    sys.exit(main())

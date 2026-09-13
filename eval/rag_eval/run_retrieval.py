from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

EVAL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EVAL_ROOT.parent
sys.path.insert(0, str(REPO_ROOT / "data-pipeline"))
sys.path.insert(0, str(EVAL_ROOT))

from pipeline.chunking import chunk_document
from pipeline.config import processed_dir, settings
from pipeline.embeddings.minilm import get_embedder
from pipeline.embeddings.tfidf import TfidfEmbedder
from pipeline.models import Chunk, ChunkStrategy, SourceDocument
from pipeline.persist import load_documents
from pipeline.run import STRATEGIES, chunk_corpus, ingest_eval_corpus
from pipeline.store.chroma import ChromaVectorStore

from rag_eval.report import chart_payload, envelope, plot_recall, write_csv, write_json
from rag_eval.retrieval import evaluate_question

logger = logging.getLogger(__name__)
GOLDEN = REPO_ROOT / "eval" / "golden_set.json"
RESULTS = EVAL_ROOT / "results"


def _available_embedders(openai_key: str | None) -> list:
    embedders = [TfidfEmbedder()]
    try:
        embedders.append(get_embedder("minilm"))
        logger.info("MiniLM embedder loaded")
    except Exception as exc:
        logger.warning("MiniLM unavailable (%s); TF-IDF only for dense comparison", exc)
    if openai_key:
        try:
            embedders.append(get_embedder("openai", openai_api_key=openai_key))
        except Exception as exc:
            logger.warning("OpenAI embedder unavailable: %s", exc)
    else:
        logger.warning("OPENAI_API_KEY unset — skipping text-embedding-3-small")
    return embedders


def _load_or_ingest(delay: bool) -> list[SourceDocument]:
    path = processed_dir() / "documents.jsonl"
    if path.exists():
        return load_documents(path)
    return ingest_eval_corpus(delay=delay)


def run_retrieval_benchmark(
    *,
    documents: list[SourceDocument] | None = None,
    embedders: list | None = None,
    strategies: tuple[ChunkStrategy, ...] = STRATEGIES,
    golden_path: Path = GOLDEN,
    persist: bool = False,
    delay: bool = True,
) -> dict:
    docs = documents if documents is not None else _load_or_ingest(delay=delay)
    golden = json.loads(golden_path.read_text(encoding="utf-8"))["pairs"]
    chunked = chunk_corpus(docs, strategies=strategies) if documents is None else {
        strategy: [chunk for doc in docs for chunk in chunk_document(doc, strategy)]
        for strategy in strategies
    }
    models = embedders if embedders is not None else _available_embedders(settings.openai_api_key)
    rows = []
    per_question: list[dict] = []
    for embedder in models:
        for strategy, chunks in chunked.items():
            row, details = _eval_combo(embedder, strategy, chunks, golden, persist=persist)
            rows.append(row)
            per_question.extend(details)
    payload = envelope(rows, extra={"n_documents": len(docs), "n_questions": len(golden), "per_question": per_question})
    return payload


def _eval_combo(embedder, strategy: str, chunks: list[Chunk], golden: list[dict], persist: bool):
    texts = [chunk.text for chunk in chunks]
    if hasattr(embedder, "fit"):
        embedder.fit(texts)
    vectors = embedder.embed_documents(texts)
    store = ChromaVectorStore(
        collection=(
            f"sentinelai-{embedder.name}-{strategy}"
            if persist
            else f"eval-{embedder.name}-{strategy}"
        ),
        persist_dir=(settings.chroma_dir if persist else None),
        in_memory=not persist,
    )
    store.upsert(chunks, vectors)
    text_to_vec = {chunk.text: vec for chunk, vec in zip(chunks, vectors)}
    details = []
    for pair in golden:
        query_vec = embedder.embed_query(pair["question"])
        hits = store.query(query_vec, k=5)
        retrieved_ids = [str(hit.metadata.get("document_id") or "") for hit in hits]
        chunk_vecs = [text_to_vec.get(hit.text) or embedder.embed_query(hit.text) for hit in hits]
        scores = evaluate_question(
            relevant_doc_ids=pair["relevant_doc_ids"],
            retrieved_doc_ids=retrieved_ids,
            query_embedding=query_vec,
            chunk_embeddings=chunk_vecs,
        )
        details.append({"id": pair["id"], "embedder": embedder.name, "chunker": strategy, **scores})
    n = max(len(golden), 1)
    row = {
        "embedder": embedder.name,
        "chunker": strategy,
        "n_chunks": len(chunks),
        "recall@3": round(sum(item["recall@3"] for item in details) / n, 4),
        "recall@5": round(sum(item["recall@5"] for item in details) / n, 4),
        "mean_cosine": round(sum(item["mean_cosine"] for item in details) / n, 4),
    }
    return row, details


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Run SentinelAI retrieval eval")
    parser.add_argument("--persist", action="store_true", help="Write Chroma collections for the API")
    parser.add_argument("--no-delay", action="store_true")
    args = parser.parse_args(argv)
    payload = run_retrieval_benchmark(persist=args.persist, delay=not args.no_delay)
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_csv(RESULTS / "retrieval.csv", payload["rows"])
    write_json(RESULTS / "retrieval.json", payload)
    write_json(RESULTS / "retrieval_chart.json", chart_payload(payload["rows"]))
    write_json(RESULTS / "winner.json", payload["winner"] or {})
    plot_recall(RESULTS / "retrieval_recall.png", payload["rows"])
    print(json.dumps(payload["rows"], indent=2))
    print("winner:", payload["winner"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

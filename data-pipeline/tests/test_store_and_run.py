from pathlib import Path

from pipeline.chunking import chunk_document
from pipeline.ingest.nvd import parse_nvd_payload
from pipeline.ingest.owasp import parse_owasp_markdown
from pipeline.models import Chunk
from pipeline.run import chunk_corpus, collection_name, index_chunks, ingest_corpus
from pipeline.store.chroma import ChromaVectorStore, get_vector_store
from tests.conftest import HashEmbedder


def test_chroma_roundtrip(owasp_markdown: str):
    document = parse_owasp_markdown(
        owasp_markdown, owasp_id="A05:2025", category="injection", filename="x.md"
    )
    chunks = chunk_document(document, "section", section_max_chars=800)
    embedder = HashEmbedder()
    store = ChromaVectorStore(collection="test-section", in_memory=True)
    store.upsert(chunks, embedder.embed_documents([chunk.text for chunk in chunks]))
    assert store.count() == len(chunks)
    hits = store.query(embedder.embed_query(chunks[0].text), k=3)
    assert hits
    assert hits[0].id == chunks[0].id
    assert hits[0].score > 0.9
    assert hits[0].metadata["source"] == "owasp"
    assert chunks[0].text in store.documents()


def test_index_chunks_helper(owasp_markdown: str):
    document = parse_owasp_markdown(
        owasp_markdown, owasp_id="A05:2025", category="injection", filename="x.md"
    )
    chunks = chunk_document(document, "fixed", fixed_size=200, overlap=20)
    store = get_vector_store("chroma", collection="test-fixed", in_memory=True)
    written = index_chunks(chunks, HashEmbedder(), store)
    assert written == len(chunks)
    assert store.count() == written


def test_empty_upsert_and_query():
    store = ChromaVectorStore(collection="empty", in_memory=True)
    store.upsert([], [])
    assert store.count() == 0
    assert store.documents() == []
    assert store.query([0.1] * 8, k=5) == []
    assert store.query([0.1] * 8, k=0) == []


def test_get_vector_store_rejects_unknown():
    try:
        get_vector_store("redis", collection="x", in_memory=True)
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_pgvector_not_implemented():
    try:
        get_vector_store("pgvector", collection="x")
    except NotImplementedError:
        return
    raise AssertionError("expected NotImplementedError")


def test_chunk_corpus_writes_jsonl(tmp_data: Path, owasp_markdown: str, nvd_payload: dict):
    owasp = parse_owasp_markdown(
        owasp_markdown, owasp_id="A05:2025", category="injection", filename="x.md"
    )
    cves = parse_nvd_payload(nvd_payload)
    result = chunk_corpus([owasp, *cves], strategies=("fixed", "paragraph", "section"))
    assert set(result) == {"fixed", "paragraph", "section"}
    assert (tmp_data / "processed" / "chunks-section.jsonl").exists()


def test_ingest_corpus_mocked(tmp_data: Path, owasp_markdown: str, nvd_payload: dict):
    from unittest.mock import patch

    owasp_doc = parse_owasp_markdown(
        owasp_markdown, owasp_id="A01:2025", category="broken_access_control", filename="a.md"
    )
    with (
        patch("pipeline.run.fetch_owasp_pages", return_value=[owasp_doc]),
        patch("pipeline.run.fetch_nvd_sample", return_value=parse_nvd_payload(nvd_payload)),
    ):
        docs = ingest_corpus(delay=False)
    assert len(docs) == 2
    assert (tmp_data / "processed" / "documents.jsonl").exists()


def test_collection_name():
    assert collection_name("all-minilm-l6-v2", "section") == "sentinelai-all-minilm-l6-v2-section"


def test_index_chunks_requires_strategy_or_chunks():
    store = ChromaVectorStore(collection="need-strategy", in_memory=True)
    try:
        index_chunks(None, HashEmbedder(), store)
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_upsert_length_mismatch():
    store = ChromaVectorStore(collection="mismatch", in_memory=True)
    chunk = Chunk(
        id="x::fixed::0",
        document_id="x",
        strategy="fixed",
        text="hello",
        chunk_index=0,
        source="owasp",
        category="injection",
    )
    try:
        store.upsert([chunk], [])
    except ValueError:
        return
    raise AssertionError("expected ValueError")

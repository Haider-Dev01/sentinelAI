from pipeline.models import Chunk
from pipeline.persist import load_chunks, load_documents, write_jsonl
from pipeline.ingest.owasp import parse_owasp_markdown
from pipeline.chunking import chunk_document, section_chunks


def test_jsonl_roundtrip(tmp_path, owasp_markdown: str):
    document = parse_owasp_markdown(
        owasp_markdown, owasp_id="A05:2025", category="injection", filename="x.md"
    )
    path = tmp_path / "docs.jsonl"
    write_jsonl(path, [document])
    loaded = load_documents(path)
    assert loaded[0].id == document.id
    chunks = chunk_document(document, "paragraph", paragraph_max_chars=500)
    chunk_path = tmp_path / "chunks.jsonl"
    write_jsonl(chunk_path, chunks)
    assert load_chunks(chunk_path)[0].strategy == "paragraph"


def test_chroma_metadata_flattens_cwes():
    chunk = Chunk(
        id="cve:CVE-1::fixed::0",
        document_id="cve:CVE-1",
        strategy="fixed",
        text="hello",
        chunk_index=0,
        source="nvd",
        category="injection",
        severity="high",
        metadata={"cwes": ["CWE-89", "CWE-79"], "title": "CVE-1"},
    )
    meta = chunk.chroma_metadata()
    assert meta["cwes"] == "CWE-89,CWE-79"
    assert meta["severity"] == "high"
    assert meta["heading_level"] == 0


def test_section_fallback_without_headings():
    pieces = section_chunks("alpha paragraph.\n\nbeta paragraph.", max_chars=80)
    assert len(pieces) >= 1
    assert "alpha" in pieces[0][0]

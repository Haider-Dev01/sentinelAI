from pipeline.chunking import chunk_document, fixed_size_chunks, paragraph_chunks, section_chunks
from pipeline.ingest.owasp import parse_owasp_markdown


def test_fixed_size_respects_max_and_overlap():
    text = " ".join(f"word{i}" for i in range(80))
    chunks = fixed_size_chunks(text, size=40, overlap=10)
    assert len(chunks) >= 2
    assert all(len(chunk) <= 40 for chunk in chunks)
    # overlap: the start of chunk n+1 should appear near the end of chunk n
    assert chunks[0][-8:] in chunks[1] or any(token in chunks[1] for token in chunks[0].split()[-2:])


def test_fixed_size_empty_and_validation():
    assert fixed_size_chunks("   ") == []
    try:
        fixed_size_chunks("abc", size=0)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_paragraph_packs_and_splits_oversized():
    short = "First paragraph.\n\nSecond paragraph."
    packed = paragraph_chunks(short, max_chars=200)
    assert packed == ["First paragraph.\n\nSecond paragraph."]

    huge = "x" * 50 + " " + "y" * 50
    split = paragraph_chunks(huge, max_chars=40)
    assert len(split) >= 2
    assert all(len(chunk) <= 40 for chunk in split)

    first = "a" * 60
    second = "b" * 60
    flushed = paragraph_chunks(f"{first}\n\n{second}", max_chars=80)
    assert flushed == [first, second]


def test_section_splits_oversized_and_preamble():
    text = (
        "Intro paragraph before any heading.\n\n"
        "## Huge section\n\n" + ("word " * 200)
    )
    sections = section_chunks(text, max_chars=80)
    titles = [meta.get("section_title") for _, meta in sections]
    assert "preamble" in titles
    assert titles.count("Huge section") >= 2


def test_section_splits_owasp_headings(owasp_markdown: str):
    from pipeline.clean import clean_markdown

    cleaned = clean_markdown(owasp_markdown)
    sections = section_chunks(cleaned, max_chars=2000)
    titles = [meta.get("section_title") for _, meta in sections]
    assert "Description." in titles or any("Description" in str(title) for title in titles)
    assert any("prevent" in str(title).lower() for title in titles)
    assert any("CWE" in str(title) for title in titles)


def test_chunk_document_assigns_ids(owasp_markdown: str):
    document = parse_owasp_markdown(
        owasp_markdown, owasp_id="A05:2025", category="injection", filename="x.md"
    )
    fixed = chunk_document(document, "fixed", fixed_size=180, overlap=20)
    paragraphs = chunk_document(document, "paragraph", paragraph_max_chars=400)
    sections = chunk_document(document, "section", section_max_chars=500)
    assert fixed and paragraphs and sections
    assert fixed[0].id == "owasp:A05:2025::fixed::0"
    assert all(chunk.strategy == "section" for chunk in sections)
    assert all(chunk.source == "owasp" for chunk in fixed)
    assert sections[0].chroma_metadata()["category"] == "injection"

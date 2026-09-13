from pipeline.clean import clean_markdown
from pipeline.ingest.owasp import parse_owasp_markdown


def test_clean_markdown_drops_score_table_and_images(owasp_markdown: str):
    cleaned = clean_markdown(owasp_markdown)
    assert "Score table" not in cleaned
    assert "62445" not in cleaned
    assert "![icon]" not in cleaned
    assert "{:" not in cleaned
    assert "Description" in cleaned
    assert "CWE-89" in cleaned
    assert "parameterized" in cleaned


def test_parse_owasp_builds_unitary_document(owasp_markdown: str):
    document = parse_owasp_markdown(
        owasp_markdown,
        owasp_id="A05:2025",
        category="injection",
        filename="A05_2025-Injection.md",
    )
    assert document.id == "owasp:A05:2025"
    assert document.source == "owasp"
    assert document.category == "injection"
    assert document.severity is None
    assert document.metadata["edition"] == "2025"
    assert "A05:2025 Injection" in document.title

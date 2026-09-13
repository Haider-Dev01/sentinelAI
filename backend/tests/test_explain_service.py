from app.models.enums import FindingType, Severity
from app.models.finding import Finding
from app.services.rag.explain_service import ExplainService, _parse_generation
from app.services.rag.llms import TemplateFixClient
from app.services.rag.prompts import finding_query
from app.services.rag.retriever import RetrievedChunk, StaticRetriever


def test_parse_generation_json_and_fence():
    parsed = _parse_generation(
        '{"explanation": "Use parameters.", "fix": "```python\\nx = 1\\n```", "language": "python"}'
    )
    assert parsed["explanation"] == "Use parameters."
    assert "x = 1" in parsed["fix"]

    messy = _parse_generation("Here you go:\n```python\ny = 2\n```")
    assert "y = 2" in messy["fix"]


def test_explain_service_confidence_and_query():
    finding = Finding(
        file_path="a.py",
        line=1,
        type=FindingType.SECRET,
        severity=Severity.HIGH,
        description="hardcoded api key",
        rule_id="generic-api-key",
        scanner="gitleaks",
        raw={},
    )
    assert "generic-api-key" in finding_query(finding)
    service = ExplainService(
        StaticRetriever(
            [RetrievedChunk(text="CWE-798", document_id="owasp:A07:2025", score=0.5)]
        ),
        llm=TemplateFixClient(),
    )
    result = service.explain(finding)
    assert result.confidence == 0.5
    assert "environ" in result.fix
    assert result.retrieved_doc_ids == ["owasp:A07:2025"]

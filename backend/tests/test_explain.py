from __future__ import annotations

from uuid import uuid4

from app.main import app
from app.models.enums import FindingType, Severity
from app.models.finding import Finding
from app.models.repository import Repository
from app.models.scan import Scan
from app.routers.findings import get_explain_service
from app.services.rag.explain_service import ExplainService
from app.services.rag.llms import TemplateFixClient
from app.services.rag.retriever import RetrievedChunk, StaticRetriever


def test_explain_unknown_finding(client):
    response = client.post(f"/findings/{uuid4()}/explain")
    assert response.status_code == 404


def test_explain_finding(client, db):
    repo = Repository(name="demo", local_path="/tmp/demo")
    db.add(repo)
    db.flush()
    scan = Scan(repository_id=repo.id)
    db.add(scan)
    db.flush()
    finding = Finding(
        scan_id=scan.id,
        file_path="app/accounts.py",
        line=42,
        type=FindingType.SAST,
        severity=Severity.HIGH,
        description="SQL injection via string concat",
        rule_id="python.sql.injection",
        scanner="semgrep",
        raw={"snippet": "q = 'select ' + user"},
    )
    db.add(finding)
    db.commit()

    retriever = StaticRetriever(
        [
            RetrievedChunk(
                text="Use parameterized queries (OWASP A05 Injection).",
                document_id="owasp:A05:2025",
                score=0.82,
                source="owasp",
            )
        ]
    )
    app.dependency_overrides[get_explain_service] = lambda: ExplainService(
        retriever, llm=TemplateFixClient(), k=5
    )
    try:
        response = client.post(f"/findings/{finding.id}/explain")
    finally:
        app.dependency_overrides.pop(get_explain_service, None)
    assert response.status_code == 200
    body = response.json()
    assert body["confidence"] == 0.82
    assert body["model"] == "template-fixer"
    assert "owasp:A05:2025" in body["retrieved_doc_ids"]
    assert "```python" in body["fix"]
    assert body["explanation"]

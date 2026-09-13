from __future__ import annotations

from pipeline.embeddings.tfidf import TfidfEmbedder
from pipeline.ingest.owasp import parse_owasp_markdown
from pipeline.models import SourceDocument
from rag_eval.clients import SloppyFixClient, TemplateFixClient
from rag_eval.report import chart_payload, envelope, pick_winner, write_csv, write_json
from rag_eval.run_llm import evaluate_llms
from rag_eval.run_retrieval import run_retrieval_benchmark
from rag_eval.syntax import first_python_fix_valid


def test_tfidf_retrieval_on_tiny_corpus(tmp_path, monkeypatch):
    monkeypatch.setattr("pipeline.config.settings.data_dir", tmp_path)
    monkeypatch.setattr("pipeline.config.settings.chroma_dir", tmp_path / "chroma")
    injection = parse_owasp_markdown(
        "# A05:2025 Injection\n\n## Description.\n\n"
        "An injection flaw sends untrusted input to an interpreter.\n"
        "Use a parameterized interface.\n",
        owasp_id="A05:2025",
        category="injection",
        filename="A05.md",
    )
    access = SourceDocument(
        id="owasp:A01:2025",
        source="owasp",
        title="A01:2025 Broken Access Control",
        text="# A01:2025 Broken Access Control\n\n"
        "Insecure direct object references let users edit someone else's account.\n",
        category="broken_access_control",
        metadata={"owasp_id": "A01:2025"},
    )
    golden = tmp_path / "golden.json"
    golden.write_text(
        """
        {"pairs": [
          {"id": "q1", "question": "What is injection and parameterized queries?",
           "relevant_doc_ids": ["owasp:A05:2025"]},
          {"id": "q2", "question": "What are insecure direct object references?",
           "relevant_doc_ids": ["owasp:A01:2025"]}
        ]}
        """.strip(),
        encoding="utf-8",
    )
    payload = run_retrieval_benchmark(
        documents=[injection, access],
        embedders=[TfidfEmbedder()],
        strategies=("paragraph", "section"),
        golden_path=golden,
        persist=False,
    )
    assert payload["winner"]["embedder"] == "tfidf-baseline"
    assert payload["winner"]["recall@5"] >= 0.5
    assert len(payload["rows"]) == 2


def test_pick_winner_prefers_higher_recall():
    winner = pick_winner(
        [
            {"embedder": "a", "chunker": "fixed", "recall@5": 0.4, "recall@3": 0.4, "mean_cosine": 0.9},
            {"embedder": "b", "chunker": "section", "recall@5": 0.8, "recall@3": 0.7, "mean_cosine": 0.2},
        ]
    )
    assert winner["embedder"] == "b"


def test_report_writers(tmp_path):
    rows = [{"embedder": "tfidf-baseline", "chunker": "section", "recall@3": 1, "recall@5": 1, "mean_cosine": 0.5}]
    write_csv(tmp_path / "r.csv", rows)
    write_json(tmp_path / "r.json", envelope(rows))
    chart = chart_payload(rows)
    assert chart["kind"] == "retrieval_comparison"
    assert chart["metrics"]["recall@5"] == [1]
    assert "tfidf-baseline" in (tmp_path / "r.csv").read_text(encoding="utf-8")


def test_llm_eval_template_beats_sloppy():
    findings = [
        {
            "id": "f1",
            "type": "sast",
            "severity": "high",
            "scanner": "semgrep",
            "rule_id": "sql",
            "file_path": "a.py",
            "line": 1,
            "description": "SQL injection via string concat",
            "snippet": "q = 'select ' + user",
            "contexts": ["Use parameterized queries."],
        }
    ]
    payload = evaluate_llms(findings, clients=[TemplateFixClient(), SloppyFixClient()])
    by_name = {row["model"]: row for row in payload["rows"]}
    assert by_name["template-fixer"]["syntax_ok_rate"] == 1.0
    assert by_name["sloppy-fixer"]["syntax_ok_rate"] == 0.0
    assert payload["winner"]["model"] == "template-fixer"


def test_clients_generate_shapes():
    prompt = "Finding type: secret\nhardcoded api key"
    assert first_python_fix_valid(TemplateFixClient().generate(prompt))
    assert not first_python_fix_valid(SloppyFixClient().generate(prompt))

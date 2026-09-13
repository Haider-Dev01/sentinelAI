from rag_eval.metrics import cosine_similarity, mean, recall_at_k
from rag_eval.retrieval import evaluate_question
from rag_eval.syntax import extract_code_blocks, first_python_fix_valid, python_syntax_valid
import json


def test_recall_at_k():
    assert recall_at_k(["owasp:A01:2025", "cve:X"], ["owasp:A01:2025"], 1) == 1.0
    assert recall_at_k(["cve:X"], ["owasp:A01:2025"], 1) == 0.0
    assert recall_at_k(["cve:X", "owasp:A01:2025"], ["owasp:A01:2025"], 1) == 0.0
    assert recall_at_k(["cve:X", "owasp:A01:2025"], ["owasp:A01:2025"], 2) == 1.0
    assert recall_at_k([], ["owasp:A01:2025"], 5) == 0.0
    assert recall_at_k(["a"], ["a"], 0) == 0.0


def test_cosine_and_mean():
    assert cosine_similarity([1, 0], [1, 0]) == 1.0
    assert cosine_similarity([1, 0], [0, 1]) == 0.0
    assert cosine_similarity([], [1]) == 0.0
    assert mean([1, 3]) == 2
    assert mean([]) == 0.0


def test_evaluate_question_aggregates():
    row = evaluate_question(
        relevant_doc_ids=["doc-a"],
        retrieved_doc_ids=["doc-b", "doc-a"],
        query_embedding=[1.0, 0.0],
        chunk_embeddings=[[1.0, 0.0], [0.0, 1.0]],
    )
    assert row["recall@3"] == 1.0
    assert row["recall@5"] == 1.0
    assert 0.4 < row["mean_cosine"] < 0.6


def test_python_syntax_and_fences():
    assert python_syntax_valid("x = 1\n")
    assert not python_syntax_valid("def (")
    text = "note\n```python\nvalue = os.environ['KEY']\n```\n"
    assert extract_code_blocks(text) == ["value = os.environ['KEY']"]
    assert first_python_fix_valid(text)
    assert not first_python_fix_valid("```python\nquery = SELECT * FROM t\n```")
    envelope = json.dumps({"explanation": "x", "fix": "```python\ndef (bad\n```"})
    assert not first_python_fix_valid(envelope)
    assert not first_python_fix_valid(json.dumps({"explanation": "x"}))
    assert first_python_fix_valid("value = 1")
    assert extract_code_blocks("") == []
    assert not python_syntax_valid("   ")

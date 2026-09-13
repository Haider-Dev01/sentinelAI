from __future__ import annotations

from pathlib import Path
from uuid import uuid4


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_scan_rejects_missing_source(client):
    response = client.post("/scans", json={})
    assert response.status_code == 422


def test_create_scan_rejects_both_sources(client):
    response = client.post("/scans", json={"url": "https://example.com/repo.git", "path": "C:/tmp"})
    assert response.status_code == 422


def test_create_scan_rejects_missing_path(client):
    response = client.post("/scans", json={"path": "C:/definitely-not-a-repo-sentinelai"})
    assert response.status_code == 400


def test_get_unknown_scan(client):
    response = client.get(f"/scans/{uuid4()}")
    assert response.status_code == 404


def test_create_and_get_scan(client, tmp_path: Path):
    created = client.post("/scans", json={"path": str(tmp_path)})
    assert created.status_code == 202
    body = created.json()
    assert body["status"] in {"pending", "completed"}
    scan_id = body["id"]

    fetched = client.get(f"/scans/{scan_id}")
    assert fetched.status_code == 200
    data = fetched.json()
    assert data["status"] == "completed"
    assert data["findings_count"] == 1
    assert data["findings"][0]["type"] == "sast"
    assert data["findings"][0]["severity"] == "high"
    assert data["findings"][0]["scanner"] == "fake"
    assert data["repository"]["name"] == tmp_path.name


def test_list_scans_and_trends(client, tmp_path: Path):
    first = client.post("/scans", json={"path": str(tmp_path)})
    second = client.post("/scans", json={"path": str(tmp_path)})
    assert first.status_code == 202
    listed = client.get("/scans")
    assert listed.status_code == 200
    rows = listed.json()
    assert len(rows) == 2
    assert rows[0]["findings_count"] == 1
    assert rows[0]["severity_counts"]["high"] == 1
    repo_id = first.json()["repository"]["id"]
    repos = client.get("/repositories")
    assert repos.status_code == 200
    assert any(item["id"] == repo_id for item in repos.json())
    trends = client.get(f"/repositories/{repo_id}/trends")
    assert trends.status_code == 200
    body = trends.json()
    assert body["repository"]["id"] == repo_id
    assert len(body["points"]) == 2
    assert body["points"][0]["severity_counts"]["high"] == 1
    missing = client.get("/repositories/00000000-0000-0000-0000-000000000000/trends")
    assert missing.status_code == 404
    assert second.status_code == 202


def test_eval_artifacts(client):
    retrieval = client.get("/eval/retrieval")
    assert retrieval.status_code == 200
    payload = retrieval.json()
    assert payload["winner"]["embedder"] == "tfidf-baseline"
    assert payload["winner"]["chunker"] == "section"
    llm = client.get("/eval/llm")
    assert llm.status_code == 200
    assert llm.json()["winner"]["model"] == "template-fixer"


def test_eval_results_dir_points_at_harness_output():
    from app.routers.eval_results import results_dir

    directory = results_dir()
    assert (directory / "retrieval.json").is_file()
    assert (directory / "llm.json").is_file()

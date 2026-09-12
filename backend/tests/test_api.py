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

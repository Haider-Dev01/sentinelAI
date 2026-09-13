from unittest.mock import patch

import scan


def test_poll_scan_stops_on_completed():
    calls = [
        {"id": "s1", "status": "running"},
        {"id": "s1", "status": "completed", "findings": []},
    ]

    def fake_get(_api, _sid):
        return calls.pop(0)

    with patch.object(scan, "get_scan", side_effect=fake_get), patch.object(scan.time, "sleep"):
        result = scan.poll_scan("http://api", "s1", timeout_s=10, interval_s=0)
    assert result["status"] == "completed"


def test_default_repo_url(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "acme/app")
    monkeypatch.setenv("GITHUB_SERVER_URL", "https://github.com")
    assert scan.default_repo_url() == "https://github.com/acme/app.git"


def test_main_comments_on_pr(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_REPOSITORY", "acme/app")
    monkeypatch.setenv("PR_NUMBER", "7")
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))

    accepted = {"id": "scan-1", "status": "pending"}
    done = {
        "id": "scan-1",
        "status": "completed",
        "findings": [],
        "repository": {"name": "app"},
    }

    with (
        patch.object(scan, "create_scan", return_value=accepted) as created,
        patch.object(scan, "poll_scan", return_value=done),
        patch.object(scan, "post_pr_comment", return_value={"id": 1}) as posted,
    ):
        code = scan.main(
            [
                "--api-url",
                "http://api",
                "--dashboard-url",
                "http://ui",
                "--github-token",
                "t",
                "--github-repository",
                "acme/app",
            ]
        )

    assert code == 0
    created.assert_called_once_with("http://api", "https://github.com/acme/app.git")
    posted.assert_called_once()
    assert "SentinelAI scan" in posted.call_args.kwargs["body"]
    assert "Open in dashboard" in summary.read_text(encoding="utf-8")


def test_parse_args_from_env(monkeypatch):
    monkeypatch.setenv("INPUT_API_URL", "http://api")
    monkeypatch.setenv("INPUT_DASHBOARD_URL", "http://ui")
    args = scan.parse_args([])
    assert args.api_url == "http://api"
    assert args.dashboard_url == "http://ui"

from comment import dashboard_scan_url, format_comment


def test_format_comment_with_findings():
    scan = {
        "id": "11111111-1111-1111-1111-111111111111",
        "status": "completed",
        "findings_count": 2,
        "severity_counts": {"critical": 1, "high": 1, "medium": 0, "low": 0, "info": 0},
        "repository": {"name": "payments-api"},
        "findings": [
            {
                "severity": "critical",
                "type": "secret",
                "file_path": "config.py",
                "line": 12,
                "rule_id": "generic-api-key",
                "scanner": "gitleaks",
            },
            {
                "severity": "high",
                "type": "sast",
                "file_path": "app.py",
                "line": None,
                "rule_id": None,
                "scanner": "semgrep",
            },
        ],
    }
    body = format_comment(scan, "https://app.example")
    assert "## SentinelAI scan" in body
    assert "`payments-api`" in body
    assert "C1 H1 M0 L0 I0" in body
    assert "config.py:12" in body
    assert dashboard_scan_url("https://app.example/", scan["id"]) in body
    assert "generic-api-key" in body


def test_format_comment_failed_empty():
    body = format_comment(
        {
            "id": "abc",
            "status": "failed",
            "error_message": "clone failed",
            "findings": [],
            "repository": {},
        },
        "http://localhost:8080",
    )
    assert "`failed`" in body
    assert "clone failed" in body
    assert "_No findings reported._" in body
    assert "http://localhost:8080/scans/abc" in body


def test_format_comment_tallies_findings_when_api_omits_counts():
    body = format_comment(
        {
            "id": "s1",
            "status": "completed",
            "repository": {"name": "demo"},
            "findings": [
                {"severity": "high", "type": "sast", "file_path": "a.py", "scanner": "semgrep"},
                {"severity": "low", "type": "sast", "file_path": "b.py", "scanner": "semgrep"},
            ],
        },
        "http://ui",
    )
    assert "C0 H1 M0 L1 I0" in body
    assert "http://ui/scans/s1" in body


def test_format_comment_truncates():
    findings = [
        {
            "severity": "low",
            "type": "sast",
            "file_path": f"f{i}.py",
            "line": i,
            "rule_id": "r",
            "scanner": "semgrep",
        }
        for i in range(35)
    ]
    body = format_comment({"id": "x", "status": "completed", "findings": findings}, "http://d")
    assert "5 more" in body

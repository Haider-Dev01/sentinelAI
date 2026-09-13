#!/usr/bin/env python3
"""Call SentinelAI POST /scans, poll until done, comment the PR."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from comment import format_comment

TERMINAL = {"completed", "failed"}


def http_json(
    method: str,
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    token: str | None = None,
    timeout: float = 30.0,
) -> Any:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Accept": "application/json",
        "User-Agent": "sentinelai-github-action",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["Accept"] = "application/vnd.github+json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} → {exc.code}: {body[:400]}") from exc


def create_scan(api_url: str, repo_url: str) -> dict[str, Any]:
    return http_json("POST", f"{api_url.rstrip('/')}/scans", payload={"url": repo_url})


def get_scan(api_url: str, scan_id: str) -> dict[str, Any]:
    return http_json("GET", f"{api_url.rstrip('/')}/scans/{scan_id}")


def poll_scan(api_url: str, scan_id: str, *, timeout_s: int, interval_s: float) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_s
    latest: dict[str, Any] = {}
    while time.monotonic() < deadline:
        latest = get_scan(api_url, scan_id)
        if latest.get("status") in TERMINAL:
            return latest
        time.sleep(interval_s)
    raise TimeoutError(f"Scan {scan_id} still {latest.get('status')!r} after {timeout_s}s")


def post_pr_comment(*, repo: str, pr_number: int, token: str, body: str) -> dict[str, Any]:
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    return http_json("POST", url, payload={"body": body}, token=token)


def default_repo_url() -> str:
    name = os.environ.get("GITHUB_REPOSITORY")
    if not name:
        raise ValueError("Set repo-url or GITHUB_REPOSITORY")
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com").rstrip("/")
    return f"{server}/{name}.git"


def default_pr_number() -> int | None:
    raw = os.environ.get("PR_NUMBER") or os.environ.get("INPUT_PR_NUMBER")
    if raw:
        return int(raw)
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        return None
    payload = json.loads(Path(event_path).read_text(encoding="utf-8"))
    number = (payload.get("pull_request") or {}).get("number") or payload.get("number")
    return int(number) if number else None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SentinelAI reusable scan action")
    parser.add_argument("--api-url", default=os.environ.get("INPUT_API_URL") or os.environ.get("SENTINELAI_API_URL"))
    parser.add_argument(
        "--dashboard-url",
        default=os.environ.get("INPUT_DASHBOARD_URL") or os.environ.get("SENTINELAI_DASHBOARD_URL"),
    )
    parser.add_argument("--repo-url", default=os.environ.get("INPUT_REPO_URL") or "")
    parser.add_argument("--github-token", default=os.environ.get("INPUT_GITHUB_TOKEN") or os.environ.get("GITHUB_TOKEN"))
    parser.add_argument("--github-repository", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--timeout-seconds", type=int, default=int(os.environ.get("INPUT_TIMEOUT_SECONDS") or "300"))
    parser.add_argument("--poll-interval", type=float, default=3.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.api_url or not args.dashboard_url:
        print("api-url and dashboard-url are required", file=sys.stderr)
        return 2
    repo_url = args.repo_url or default_repo_url()
    accepted = create_scan(args.api_url, repo_url)
    scan_id = str(accepted["id"])
    print(f"Scan accepted: {scan_id} ({accepted.get('status')})")
    scan = poll_scan(args.api_url, scan_id, timeout_s=args.timeout_seconds, interval_s=args.poll_interval)
    body = format_comment(scan, args.dashboard_url)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        Path(summary).write_text(body, encoding="utf-8")
    pr_number = default_pr_number()
    if pr_number and args.github_token and args.github_repository:
        post_pr_comment(
            repo=args.github_repository,
            pr_number=pr_number,
            token=args.github_token,
            body=body,
        )
        print(f"Commented on PR #{pr_number}")
    else:
        print(body)
        if not pr_number:
            print("No PR number — skipped GitHub comment (wrote step summary if available).")
    if scan.get("status") == "failed":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.git_service import (
    GitResolutionError,
    cleanup_ephemeral,
    clone_repository,
    read_head_sha,
    resolve_repo,
)
from app.services.scanners import gitleaks as gitleaks_mod
from app.services.scanners import osv as osv_mod
from app.services.scanners import semgrep as semgrep_mod
from app.services.scanners.process import (
    ScannerExecutionError,
    ensure_success,
    load_json,
    load_json_file,
    relativize,
    run_process,
    which_or_raise,
)
from tests.conftest import load_fixture


def _completed(code: int, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["tool"], returncode=code, stdout=stdout, stderr=stderr)


def test_which_or_raise():
    with patch("app.services.scanners.process.shutil.which", return_value=None):
        with pytest.raises(ScannerExecutionError, match="semgrep"):
            which_or_raise("semgrep")
    with patch("app.services.scanners.process.shutil.which", return_value="/usr/bin/semgrep"):
        assert which_or_raise("semgrep") == "/usr/bin/semgrep"


def test_ensure_success_accepts_zero_and_one():
    ensure_success(_completed(0), "semgrep")
    ensure_success(_completed(1), "gitleaks")
    with pytest.raises(ScannerExecutionError, match="osv-scanner failed"):
        ensure_success(_completed(2, stderr="boom"), "osv-scanner")


def test_load_json_helpers(tmp_path: Path):
    assert load_json("") is None
    assert load_json('{"a": 1}') == {"a": 1}
    missing = tmp_path / "nope.json"
    assert load_json_file(missing) is None
    empty = tmp_path / "empty.json"
    empty.write_text("", encoding="utf-8")
    assert load_json_file(empty) is None
    filled = tmp_path / "ok.json"
    filled.write_text('{"ok": true}', encoding="utf-8")
    assert load_json_file(filled) == {"ok": True}


def test_relativize(tmp_path: Path):
    nested = tmp_path / "src" / "app.py"
    nested.parent.mkdir()
    nested.write_text("x", encoding="utf-8")
    assert relativize(str(nested), tmp_path) == "src/app.py"
    assert relativize("src/app.py", tmp_path) == "src/app.py"
    outside = relativize("C:/elsewhere/x.py", tmp_path)
    assert "x.py" in outside


def test_run_process_timeout():
    with patch("app.services.scanners.process.subprocess.run", side_effect=subprocess.TimeoutExpired("x", 1)):
        with pytest.raises(ScannerExecutionError, match="timed out"):
            run_process(["sleep", "999"], timeout=1)


def test_semgrep_scanner_parses_stdout(tmp_path: Path):
    payload = json.dumps(load_fixture("semgrep.json"))
    with (
        patch.object(semgrep_mod, "which_or_raise", return_value="semgrep"),
        patch.object(semgrep_mod, "run_process", return_value=_completed(0, stdout=payload)),
    ):
        findings = semgrep_mod.SemgrepScanner().scan(str(tmp_path))
    assert len(findings) == 3
    assert findings[0].scanner == "semgrep"


def test_gitleaks_scanner_writes_report(tmp_path: Path, monkeypatch):
    report = tmp_path / "gitleaks.json"
    report.write_text(json.dumps(load_fixture("gitleaks.json")), encoding="utf-8")

    class DummyTmp:
        def __init__(self):
            self.name = str(report)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    with (
        patch.object(gitleaks_mod, "which_or_raise", return_value="gitleaks"),
        patch.object(gitleaks_mod, "run_process", return_value=_completed(1)),
        patch("app.services.scanners.gitleaks.tempfile.NamedTemporaryFile", return_value=DummyTmp()),
    ):
        findings = gitleaks_mod.GitleaksScanner().scan(str(tmp_path))
    assert len(findings) == 2


def test_osv_scanner_parses_stdout(tmp_path: Path):
    payload = json.dumps(load_fixture("osv.json"))
    with (
        patch.object(osv_mod, "which_or_raise", return_value="osv-scanner"),
        patch.object(osv_mod, "run_process", return_value=_completed(1, stdout=payload)),
    ):
        findings = osv_mod.OSVScanner().scan(str(tmp_path))
    assert len(findings) == 3


def test_osv_scanner_no_packages_is_empty(tmp_path: Path):
    with (
        patch.object(osv_mod, "which_or_raise", return_value="osv-scanner"),
        patch.object(
            osv_mod,
            "run_process",
            return_value=_completed(2, stderr="No package sources found"),
        ),
    ):
        assert osv_mod.OSVScanner().scan(str(tmp_path)) == []


def test_osv_scanner_real_failure(tmp_path: Path):
    with (
        patch.object(osv_mod, "which_or_raise", return_value="osv-scanner"),
        patch.object(osv_mod, "run_process", return_value=_completed(2, stderr="crash")),
    ):
        with pytest.raises(ScannerExecutionError):
            osv_mod.OSVScanner().scan(str(tmp_path))


def test_resolve_local_path(tmp_path: Path):
    path, name, ephemeral = resolve_repo(url=None, path=str(tmp_path), work_dir=tmp_path)
    assert path == tmp_path.resolve()
    assert name == tmp_path.name
    assert ephemeral is False


def test_resolve_missing_path():
    with pytest.raises(GitResolutionError):
        resolve_repo(url=None, path="/no/such/sentinelai-path", work_dir=Path("."))


def test_resolve_url_clones_into_work_dir(tmp_path: Path):
    with patch("app.services.git_service.clone_repository") as clone:
        path, name, ephemeral = resolve_repo(
            url="https://github.com/org/demo.git",
            path=None,
            work_dir=tmp_path,
        )
    assert ephemeral is True
    assert name == "demo"
    assert path.parent == tmp_path
    clone.assert_called_once()


def test_resolve_requires_source():
    with pytest.raises(GitResolutionError):
        resolve_repo(url=None, path=None, work_dir=Path("."))


def test_clone_repository_failure(tmp_path: Path):
    dest = tmp_path / "clone"
    with (
        patch("app.services.git_service.which_or_raise", return_value="git"),
        patch(
            "app.services.git_service.run_process",
            return_value=_completed(128, stderr="auth failed"),
        ),
    ):
        with pytest.raises(GitResolutionError, match="git clone failed"):
            clone_repository("https://example.com/repo.git", dest)


def test_clone_repository_success(tmp_path: Path):
    dest = tmp_path / "clone"
    with (
        patch("app.services.git_service.which_or_raise", return_value="git"),
        patch(
            "app.services.git_service.run_process",
            return_value=_completed(0, stdout="Cloning..."),
        ),
    ):
        clone_repository("https://example.com/repo.git", dest)


def test_read_head_sha_without_git(tmp_path: Path):
    assert read_head_sha(tmp_path) is None


def test_cleanup_ephemeral(tmp_path: Path):
    target = tmp_path / "clone"
    target.mkdir()
    cleanup_ephemeral(target)
    assert not target.exists()


def test_read_head_sha_with_git_dir(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    with patch(
        "app.services.git_service.subprocess.run",
        return_value=_completed(0, stdout="abc123\n"),
    ):
        assert read_head_sha(tmp_path) == "abc123"
    with patch(
        "app.services.git_service.subprocess.run",
        return_value=_completed(128, stderr="not a git repo"),
    ):
        assert read_head_sha(tmp_path) is None
    with patch("app.services.git_service.subprocess.run", side_effect=OSError("git missing")):
        assert read_head_sha(tmp_path) is None

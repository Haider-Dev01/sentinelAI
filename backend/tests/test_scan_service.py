from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
import uuid

from app.models.enums import FindingType, ScanStatus, Severity
from app.services.git_service import GitResolutionError
from app.services.scanners.base import NormalizedFinding
from app.services.scanners.process import ScannerExecutionError
from app.services.scan_service import ScanService, default_scanners, run_scan_job


class OkScanner:
    name = "ok"

    def scan(self, repo_path: str) -> list[NormalizedFinding]:
        return [
            NormalizedFinding(
                file_path="a.py",
                line=1,
                type=FindingType.SAST,
                severity=Severity.LOW,
                description="ok",
                scanner=self.name,
            )
        ]


class BoomScanner:
    name = "boom"

    def scan(self, repo_path: str) -> list[NormalizedFinding]:
        raise ScannerExecutionError("binary missing")


def test_scan_path_isolates_scanner_failures():
    service = ScanService(db=MagicMock(), scanners=[OkScanner(), BoomScanner()])
    findings, errors = service.scan_path("/tmp/repo")
    assert len(findings) == 1
    assert findings[0].scanner == "ok"
    assert len(errors) == 1
    assert "boom" in errors[0]


def test_create_and_execute_scan_persists_findings(db, tmp_path: Path):
    service = ScanService(db, scanners=[OkScanner()])
    scan = service.create_scan(url=None, path=str(tmp_path))
    assert scan.status == ScanStatus.PENDING

    service.execute(scan.id)
    stored = service.get_scan(scan.id)
    assert stored is not None
    assert stored.status == ScanStatus.COMPLETED
    assert stored.finished_at is not None
    assert len(stored.findings) == 1
    assert stored.findings[0].file_path == "a.py"
    assert stored.findings[0].type == FindingType.SAST


def test_execute_fails_when_all_scanners_fail(db, tmp_path: Path):
    service = ScanService(db, scanners=[BoomScanner()])
    scan = service.create_scan(url=None, path=str(tmp_path))
    service.execute(scan.id)
    stored = service.get_scan(scan.id)
    assert stored.status == ScanStatus.FAILED
    assert stored.error_message is not None
    assert "boom" in stored.error_message


def test_execute_completes_with_partial_errors(db, tmp_path: Path):
    service = ScanService(db, scanners=[OkScanner(), BoomScanner()])
    scan = service.create_scan(url=None, path=str(tmp_path))
    service.execute(scan.id)
    stored = service.get_scan(scan.id)
    assert stored.status == ScanStatus.COMPLETED
    assert stored.error_message is not None
    assert len(stored.findings) == 1


def test_reuse_repository_for_same_path(db, tmp_path: Path):
    service = ScanService(db, scanners=[])
    first = service.create_scan(url=None, path=str(tmp_path))
    second = service.create_scan(url=None, path=str(tmp_path))
    assert first.repository_id == second.repository_id


def test_create_scan_from_url(db):
    service = ScanService(db, scanners=[])
    first = service.create_scan(url="https://github.com/org/demo.git", path=None)
    second = service.create_scan(url="https://github.com/org/demo.git", path=None)
    assert first.repository.name == "demo"
    assert first.repository.url == "https://github.com/org/demo.git"
    assert first.repository_id == second.repository_id


def test_execute_ephemeral_clone_is_cleaned(db, tmp_path: Path):
    clone = tmp_path / "clone"
    clone.mkdir()
    service = ScanService(db, scanners=[OkScanner()])
    scan = service.create_scan(url="https://github.com/org/demo.git", path=None)
    with (
        patch("app.services.scan_service.resolve_repo", return_value=(clone, "demo", True)),
        patch("app.services.scan_service.cleanup_ephemeral") as cleanup,
        patch("app.services.scan_service.read_head_sha", return_value="abc123"),
    ):
        service.execute(scan.id)
    cleanup.assert_called_once_with(clone)
    stored = service.get_scan(scan.id)
    assert stored.status == ScanStatus.COMPLETED
    assert stored.commit_sha == "abc123"


def test_default_scanners_names():
    assert [scanner.name for scanner in default_scanners()] == ["semgrep", "gitleaks", "osv-scanner"]


def test_run_scan_job_closes_session():
    mock_session = MagicMock()
    with (
        patch("app.database.SessionLocal", return_value=mock_session),
        patch("app.services.scan_service.ScanService") as service_cls,
    ):
        scan_id = uuid.uuid4()
        run_scan_job(scan_id)
        service_cls.assert_called_once_with(mock_session)
        service_cls.return_value.execute.assert_called_once_with(scan_id)
        mock_session.close.assert_called_once()


def test_execute_git_resolution_error_message(db, tmp_path: Path):
    service = ScanService(db, scanners=[OkScanner()])
    scan = service.create_scan(url=None, path=str(tmp_path))
    with patch(
        "app.services.scan_service.resolve_repo",
        side_effect=GitResolutionError("cannot clone"),
    ):
        service.execute(scan.id)
    stored = service.get_scan(scan.id)
    assert stored.status == ScanStatus.FAILED
    assert stored.error_message == "cannot clone"


def test_execute_unknown_scan_is_noop(db):
    service = ScanService(db, scanners=[])
    service.execute(uuid.uuid4())


def test_execute_unexpected_error(db, tmp_path: Path):
    service = ScanService(db, scanners=[OkScanner()])
    scan = service.create_scan(url=None, path=str(tmp_path))
    with patch("app.services.scan_service.resolve_repo", side_effect=Exception("boom")):
        service.execute(scan.id)
    stored = service.get_scan(scan.id)
    assert stored.status == ScanStatus.FAILED
    assert stored.error_message == "Internal error while running scanners"

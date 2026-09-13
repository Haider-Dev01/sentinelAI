from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.models import Finding, Repository, Scan
from app.models.enums import ScanStatus, Severity
from app.schemas.scan import SeverityCounts
from app.services.git_service import (
    GitResolutionError,
    cleanup_ephemeral,
    read_head_sha,
    resolve_repo,
)
from app.services.scanners.base import NormalizedFinding, Scanner
from app.services.scanners.gitleaks import GitleaksScanner
from app.services.scanners.osv import OSVScanner
from app.services.scanners.process import ScannerExecutionError
from app.services.scanners.semgrep import SemgrepScanner

logger = logging.getLogger(__name__)


def default_scanners() -> list[Scanner]:
    return [SemgrepScanner(), GitleaksScanner(), OSVScanner()]


class ScanService:
    """Orchestrates git resolution + scanner runs and persists normalized findings.

    Background execution uses FastAPI BackgroundTasks rather than Celery: scans run
    on a single API instance in Phase 1, and introducing a broker would add
    infrastructure before we have measured queue depth, retry, or multi-worker needs.
    """

    def __init__(self, db: Session, scanners: list[Scanner] | None = None) -> None:
        self.db = db
        self.scanners = scanners if scanners is not None else default_scanners()

    def create_scan(self, *, url: str | None, path: str | None) -> Scan:
        name = _preview_name(url=url, path=path)
        repository = self._get_or_create_repository(url=url, path=path, name=name)
        scan = Scan(repository_id=repository.id, status=ScanStatus.PENDING)
        self.db.add(scan)
        self.db.commit()
        self.db.refresh(scan)
        self.db.refresh(repository)
        scan.repository = repository
        return scan

    def get_finding(self, finding_id: uuid.UUID) -> Finding | None:
        return self.db.get(Finding, finding_id)

    def list_scans(self) -> list[Scan]:
        stmt = (
            select(Scan)
            .options(selectinload(Scan.repository), selectinload(Scan.findings))
            .order_by(Scan.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def list_repositories(self) -> list[Repository]:
        stmt = select(Repository).order_by(Repository.name.asc())
        return list(self.db.scalars(stmt).all())

    def get_repository(self, repository_id: uuid.UUID) -> Repository | None:
        return self.db.get(Repository, repository_id)

    def repository_trends(self, repository_id: uuid.UUID) -> list[Scan]:
        stmt = (
            select(Scan)
            .options(selectinload(Scan.findings), selectinload(Scan.repository))
            .where(Scan.repository_id == repository_id)
            .where(Scan.status == ScanStatus.COMPLETED)
            .order_by(Scan.created_at.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_scan(self, scan_id: uuid.UUID) -> Scan | None:
        stmt = (
            select(Scan)
            .options(selectinload(Scan.repository), selectinload(Scan.findings))
            .where(Scan.id == scan_id)
        )
        return self.db.scalars(stmt).first()

    def execute(self, scan_id: uuid.UUID) -> None:
        scan = self.get_scan(scan_id)
        if scan is None:
            logger.error("Scan %s not found", scan_id)
            return

        scan.status = ScanStatus.RUNNING
        scan.started_at = datetime.now(timezone.utc)
        scan.error_message = None
        self.db.commit()

        ephemeral = False
        repo_path: Path | None = None
        try:
            repo_path, name, ephemeral = resolve_repo(
                url=scan.repository.url,
                path=scan.repository.local_path if not scan.repository.url else None,
                work_dir=Path(settings.scan_work_dir),
            )
            scan.repository.name = name
            if ephemeral:
                scan.repository.local_path = str(repo_path)
            scan.commit_sha = read_head_sha(repo_path)
            self.db.commit()

            findings, errors = self.scan_path(str(repo_path))
            for item in findings:
                self.db.add(_to_orm(scan.id, item))

            if errors and not findings:
                scan.status = ScanStatus.FAILED
                scan.error_message = "; ".join(errors)
            elif errors:
                scan.status = ScanStatus.COMPLETED
                scan.error_message = "; ".join(errors)
            else:
                scan.status = ScanStatus.COMPLETED
            scan.finished_at = datetime.now(timezone.utc)
            self.db.commit()
        except GitResolutionError as exc:
            self._fail(scan, str(exc))
        except Exception:
            logger.exception("Scan %s crashed", scan_id)
            self._fail(scan, "Internal error while running scanners")
        finally:
            if ephemeral and repo_path is not None:
                cleanup_ephemeral(repo_path)

    def scan_path(self, repo_path: str) -> tuple[list[NormalizedFinding], list[str]]:
        """Run every scanner against a local checkout. Scanner failures are isolated."""
        findings: list[NormalizedFinding] = []
        errors: list[str] = []
        for scanner in self.scanners:
            try:
                findings.extend(scanner.scan(repo_path))
            except ScannerExecutionError as exc:
                logger.warning("%s: %s", scanner.name, exc)
                errors.append(f"{scanner.name}: {exc}")
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Scanner %s crashed", scanner.name)
                errors.append(f"{scanner.name}: unexpected error ({exc})")
        return findings, errors

    def _get_or_create_repository(
        self, *, url: str | None, path: str | None, name: str
    ) -> Repository:
        if url:
            existing = self.db.scalars(select(Repository).where(Repository.url == url)).first()
            if existing:
                return existing
            repo = Repository(name=name, url=url, local_path=None)
        else:
            resolved = str(Path(path).expanduser().resolve()) if path else None
            existing = self.db.scalars(
                select(Repository).where(Repository.local_path == resolved)
            ).first()
            if existing:
                return existing
            repo = Repository(name=name, url=None, local_path=resolved)
        self.db.add(repo)
        self.db.flush()
        return repo

    def _fail(self, scan: Scan, message: str) -> None:
        scan.status = ScanStatus.FAILED
        scan.error_message = message
        scan.finished_at = datetime.now(timezone.utc)
        self.db.commit()


def _to_orm(scan_id: uuid.UUID, item: NormalizedFinding) -> Finding:
    return Finding(
        scan_id=scan_id,
        file_path=item.file_path,
        line=item.line,
        type=item.type,
        severity=item.severity,
        description=item.description,
        rule_id=item.rule_id,
        scanner=item.scanner,
        raw=item.raw,
    )


def _preview_name(*, url: str | None, path: str | None) -> str:
    if url:
        cleaned = url.rstrip("/").removesuffix(".git")
        return cleaned.rsplit("/", 1)[-1] or "repository"
    if path:
        return Path(path).name or "repository"
    return "repository"


def run_scan_job(scan_id: uuid.UUID) -> None:
    """Entry point for FastAPI BackgroundTasks (own DB session)."""
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        ScanService(db).execute(scan_id)
    finally:
        db.close()


def severity_counts(findings: list[Finding]) -> SeverityCounts:
    counts = {item.value: 0 for item in Severity}
    for finding in findings:
        key = finding.severity.value if isinstance(finding.severity, Severity) else str(finding.severity)
        if key in counts:
            counts[key] += 1
    return SeverityCounts(**counts)

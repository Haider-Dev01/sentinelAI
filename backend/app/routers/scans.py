from __future__ import annotations

import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ScanAccepted, ScanCreate, ScanRead, ScanSummary
from app.services.scan_service import ScanService, run_scan_job, severity_counts

router = APIRouter(prefix="/scans", tags=["scans"])


@router.get("", response_model=list[ScanSummary])
def list_scans(db: Annotated[Session, Depends(get_db)]) -> list[ScanSummary]:
    scans = ScanService(db).list_scans()
    return [_to_summary(scan) for scan in scans]


@router.post("", response_model=ScanAccepted, status_code=status.HTTP_202_ACCEPTED)
def create_scan(
    payload: ScanCreate,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
) -> ScanAccepted:
    if payload.path:
        local = Path(payload.path).expanduser()
        if not local.exists() or not local.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Local path does not exist or is not a directory: {local}",
            )
    service = ScanService(db)
    scan = service.create_scan(
        url=payload.url.strip() if payload.url else None,
        path=payload.path.strip() if payload.path else None,
    )
    background_tasks.add_task(run_scan_job, scan.id)
    return ScanAccepted.model_validate(scan)


@router.get("/{scan_id}", response_model=ScanRead)
def get_scan(
    scan_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> ScanRead:
    scan = ScanService(db).get_scan(scan_id)
    if scan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    return ScanRead(
        id=scan.id,
        status=scan.status,
        commit_sha=scan.commit_sha,
        error_message=scan.error_message,
        started_at=scan.started_at,
        finished_at=scan.finished_at,
        created_at=scan.created_at,
        repository=scan.repository,
        findings=list(scan.findings),
        findings_count=len(scan.findings),
    )


def _to_summary(scan) -> ScanSummary:
    return ScanSummary(
        id=scan.id,
        status=scan.status,
        commit_sha=scan.commit_sha,
        error_message=scan.error_message,
        started_at=scan.started_at,
        finished_at=scan.finished_at,
        created_at=scan.created_at,
        repository=scan.repository,
        findings_count=len(scan.findings),
        severity_counts=severity_counts(scan.findings),
    )

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import RepositoryRead, TrendPoint, TrendResponse
from app.services.scan_service import ScanService, severity_counts

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.get("", response_model=list[RepositoryRead])
def list_repositories(db: Annotated[Session, Depends(get_db)]) -> list[RepositoryRead]:
    return [RepositoryRead.model_validate(repo) for repo in ScanService(db).list_repositories()]


@router.get("/{repository_id}/trends", response_model=TrendResponse)
def repository_trends(
    repository_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> TrendResponse:
    service = ScanService(db)
    repository = service.get_repository(repository_id)
    if repository is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    scans = service.repository_trends(repository_id)
    return TrendResponse(
        repository=RepositoryRead.model_validate(repository),
        points=[
            TrendPoint(
                scan_id=scan.id,
                created_at=scan.created_at,
                finished_at=scan.finished_at,
                findings_count=len(scan.findings),
                severity_counts=severity_counts(scan.findings),
            )
            for scan in scans
        ],
    )

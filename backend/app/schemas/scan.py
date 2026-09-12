from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import FindingType, ScanStatus, Severity


class ScanCreate(BaseModel):
    url: str | None = Field(default=None, description="Git remote URL to clone and scan")
    path: str | None = Field(default=None, description="Local filesystem path to an existing clone")

    @model_validator(mode="after")
    def exactly_one_source(self) -> ScanCreate:
        has_url = bool(self.url and self.url.strip())
        has_path = bool(self.path and self.path.strip())
        if has_url == has_path:
            raise ValueError("Provide exactly one of 'url' or 'path'")
        return self


class FindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_path: str
    line: int | None
    type: FindingType
    severity: Severity
    description: str
    rule_id: str | None
    scanner: str
    raw: dict[str, Any]


class RepositoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    url: str | None
    local_path: str | None


class ScanAccepted(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: ScanStatus
    repository: RepositoryRead


class ScanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: ScanStatus
    commit_sha: str | None
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    repository: RepositoryRead
    findings: list[FindingRead]
    findings_count: int


class HealthResponse(BaseModel):
    status: str

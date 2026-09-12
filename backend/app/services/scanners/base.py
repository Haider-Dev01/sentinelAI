from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field

from app.models.enums import FindingType, Severity


class NormalizedFinding(BaseModel):
    """Common finding produced by every scanner parser."""

    file_path: str
    line: int | None = None
    type: FindingType
    severity: Severity
    description: str
    rule_id: str | None = None
    scanner: str
    raw: dict[str, Any] = Field(default_factory=dict)


class Scanner(Protocol):
    name: str

    def scan(self, repo_path: str) -> list[NormalizedFinding]:
        """Run the tool against repo_path and return normalized findings."""

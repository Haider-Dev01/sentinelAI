from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database import Base
from app.models.enums import FindingType, Severity
from app.models.types import UuidPk

if TYPE_CHECKING:
    from app.models.scan import Scan


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[uuid.UUID] = mapped_column(UuidPk, primary_key=True, default=uuid.uuid4)
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UuidPk, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    type: Mapped[FindingType] = mapped_column(
        Enum(FindingType, native_enum=False, length=32), nullable=False, index=True
    )
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity, native_enum=False, length=32), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    rule_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scanner: Mapped[str] = mapped_column(String(64), nullable=False)
    raw: Mapped[dict[str, Any]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    scan: Mapped[Scan] = relationship("Scan", back_populates="findings")

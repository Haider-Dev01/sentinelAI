from __future__ import annotations

import json
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Finding, Repository, Scan  # noqa: F401
from app.models.enums import FindingType, Severity
from app.services.scanners.base import NormalizedFinding
from app.services.scan_service import ScanService

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def engine():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)
    try:
        yield test_engine
    finally:
        Base.metadata.drop_all(test_engine)
        test_engine.dispose()


@pytest.fixture
def db(engine) -> Generator[Session, None, None]:
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class FakeScanner:
    name = "fake"

    def scan(self, repo_path: str) -> list[NormalizedFinding]:
        return [
            NormalizedFinding(
                file_path="app/main.py",
                line=10,
                type=FindingType.SAST,
                severity=Severity.HIGH,
                description=f"fake finding in {repo_path}",
                rule_id="fake.rule",
                scanner=self.name,
                raw={"repo": repo_path},
            )
        ]


@pytest.fixture
def fake_scanner() -> FakeScanner:
    return FakeScanner()


@pytest.fixture
def client(db: Session, fake_scanner: FakeScanner) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db

    def fake_run_scan_job(scan_id) -> None:
        ScanService(db, scanners=[fake_scanner]).execute(scan_id)

    app.dependency_overrides[get_db] = override_get_db
    with patch("app.routers.scans.run_scan_job", fake_run_scan_job):
        with TestClient(app) as test_client:
            yield test_client
    app.dependency_overrides.clear()


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

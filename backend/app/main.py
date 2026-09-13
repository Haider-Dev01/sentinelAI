from __future__ import annotations

import logging

from fastapi import FastAPI

from app.models import Finding, Repository, Scan  # noqa: F401 — register mappers
from app.routers import findings, health, scans

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="SentinelAI",
    description="DevSecOps scan engine with measured RAG explanations.",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(scans.router)
app.include_router(findings.router)

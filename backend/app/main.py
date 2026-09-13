from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import cors_origin_list
from app.models import Finding, Repository, Scan  # noqa: F401 — register mappers
from app.routers import eval_results, findings, health, repositories, scans

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="SentinelAI",
    description="DevSecOps scan engine with measured RAG explanations.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origin_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(scans.router)
app.include_router(findings.router)
app.include_router(repositories.router)
app.include_router(eval_results.router)

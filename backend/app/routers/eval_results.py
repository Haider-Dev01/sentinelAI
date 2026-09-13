from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/eval", tags=["eval"])


def results_dir() -> Path:
    here = Path(__file__).resolve()
    candidates = [
        here.parents[3] / "eval" / "results",  # repo: backend/app/routers → root
        here.parents[2] / "eval" / "results",  # some Docker layouts
        Path("/eval/results"),
        Path("/app/eval/results"),
    ]
    for path in candidates:
        if path.is_dir():
            return path
    return candidates[0]


@router.get("/retrieval")
def retrieval_results() -> dict[str, Any]:
    return _read_json("retrieval.json")


@router.get("/llm")
def llm_results() -> dict[str, Any]:
    return _read_json("llm.json")


def _read_json(name: str) -> dict[str, Any]:
    path = results_dir() / name
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Eval artifact {name} is missing. Run the Phase 3 harness first.",
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid eval artifact")
    return payload

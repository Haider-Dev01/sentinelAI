from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from pipeline.models import Chunk, SourceDocument

T = TypeVar("T", bound=BaseModel)


def write_jsonl(path: Path, items: Iterable[BaseModel]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(item.model_dump_json() + "\n")


def load_documents(path: Path) -> list[SourceDocument]:
    return [SourceDocument.model_validate(row) for row in _read_jsonl(path)]


def load_chunks(path: Path) -> list[Chunk]:
    return [Chunk.model_validate(row) for row in _read_jsonl(path)]


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

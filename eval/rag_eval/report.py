from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def pick_winner(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Primary: recall@5, then recall@3, then mean cosine. Local embedders win ties."""

    def key(row: dict[str, Any]) -> tuple:
        local_bonus = 0 if row.get("embedder") == "text-embedding-3-small" else 1
        return (row["recall@5"], row["recall@3"], row["mean_cosine"], local_bonus)

    return max(rows, key=key)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def plot_recall(path: Path, rows: list[dict[str, Any]]) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:  # pragma: no cover
        return
    labels = [f"{row['embedder']}\n{row['chunker']}" for row in rows]
    recall5 = [row["recall@5"] for row in rows]
    recall3 = [row["recall@3"] for row in rows]
    x = range(len(labels))
    width = 0.38
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar([i - width / 2 for i in x], recall3, width, label="recall@3")
    ax.bar([i + width / 2 for i in x], recall5, width, label="recall@5")
    ax.set_xticks(list(x), labels, fontsize=8)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Recall")
    ax.set_title("Golden-set retrieval: chunking × embedding")
    ax.legend()
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140)
    plt.close(fig)


def chart_payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Frontend-friendly series for the retrieval comparison chart."""
    return {
        "kind": "retrieval_comparison",
        "labels": [f"{row['embedder']} / {row['chunker']}" for row in rows],
        "metrics": {
            "recall@3": [row["recall@3"] for row in rows],
            "recall@5": [row["recall@5"] for row in rows],
            "mean_cosine": [row["mean_cosine"] for row in rows],
        },
        "rows": rows,
    }


def envelope(rows: list[dict[str, Any]], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rows": rows,
        "winner": pick_winner(rows) if rows else None,
    }
    if extra:
        payload.update(extra)
    return payload

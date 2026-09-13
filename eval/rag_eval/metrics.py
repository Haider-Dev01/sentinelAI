from __future__ import annotations

import math


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    n_left = math.sqrt(sum(a * a for a in left))
    n_right = math.sqrt(sum(b * b for b in right))
    if n_left == 0 or n_right == 0:
        return 0.0
    return dot / (n_left * n_right)


def recall_at_k(retrieved_doc_ids: list[str], relevant_doc_ids: list[str], k: int) -> float:
    if not relevant_doc_ids or k <= 0:
        return 0.0
    top = retrieved_doc_ids[:k]
    return 1.0 if any(doc_id in relevant_doc_ids for doc_id in top) else 0.0


def mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)

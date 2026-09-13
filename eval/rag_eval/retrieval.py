from __future__ import annotations

from rag_eval.metrics import cosine_similarity, mean, recall_at_k


def evaluate_question(
    *,
    relevant_doc_ids: list[str],
    retrieved_doc_ids: list[str],
    query_embedding: list[float],
    chunk_embeddings: list[list[float]],
    ks: tuple[int, ...] = (3, 5),
) -> dict[str, float]:
    row = {
        f"recall@{k}": recall_at_k(retrieved_doc_ids, relevant_doc_ids, k) for k in ks
    }
    similarities = [
        cosine_similarity(query_embedding, chunk_vec)
        for chunk_vec in chunk_embeddings
    ]
    row["mean_cosine"] = mean(similarities)
    return row

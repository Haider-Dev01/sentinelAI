from __future__ import annotations

from pipeline.embeddings.base import Embedder


class MiniLMEmbedder:
    """Local baseline: `all-MiniLM-L6-v2` (384-d).

    Prefers FastEmbed (ONNX / onnxruntime) so indexing does not require PyTorch.
    Falls back to sentence-transformers when FastEmbed is not installed.
    """

    name = "all-minilm-l6-v2"
    dimensions = 384

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self._backend, self._model = _load_minilm(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self._backend == "fastembed":
            return [vector.tolist() for vector in self._model.embed(texts)]
        vectors = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return [vector.tolist() for vector in vectors]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def _load_minilm(model_name: str):
    try:
        from fastembed import TextEmbedding

        return "fastembed", TextEmbedding(model_name=model_name)
    except Exception:
        from sentence_transformers import SentenceTransformer

        return "st", SentenceTransformer(model_name)


def get_embedder(name: str, openai_api_key: str | None = None) -> Embedder:
    key = name.lower().strip()
    if key in {"minilm", "all-minilm-l6-v2", "all-minilm"}:
        return MiniLMEmbedder()
    if key in {"tfidf", "tfidf-baseline"}:
        from pipeline.embeddings.tfidf import TfidfEmbedder

        return TfidfEmbedder()
    if key in {"openai", "text-embedding-3-small"}:
        from pipeline.embeddings.openai import OpenAIEmbedder

        return OpenAIEmbedder(api_key=openai_api_key)
    raise ValueError(f"Unknown embedder '{name}'. Use 'minilm', 'tfidf', or 'openai'.")

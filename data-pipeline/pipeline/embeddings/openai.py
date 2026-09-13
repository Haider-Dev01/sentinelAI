from __future__ import annotations

import httpx

from pipeline.config import settings


class OpenAIEmbedder:
    """API candidate: OpenAI `text-embedding-3-small` (1536-d).

    Candidate only — Phase 3 measures retrieval quality against MiniLM.
    Requires OPENAI_API_KEY. Not used in unit tests.
    """

    name = "text-embedding-3-small"
    dimensions = 1536

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "text-embedding-3-small",
    ) -> None:
        key = api_key or settings.openai_api_key
        if not key:
            raise RuntimeError("OPENAI_API_KEY is required for the OpenAI embedder")
        self._api_key = key
        self._model = model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = httpx.post(
            settings.openai_embeddings_url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={"model": self._model, "input": texts},
            timeout=60.0,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"OpenAI embeddings failed ({response.status_code}): {response.text[:300]}")
        payload = response.json()
        data = sorted(payload.get("data") or [], key=lambda item: item.get("index", 0))
        return [item["embedding"] for item in data]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

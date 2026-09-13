from __future__ import annotations

import math
import re

_TOKEN = re.compile(r"[a-z0-9_]+", re.IGNORECASE)


def _tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


class TfidfEmbedder:
    """Sparse lexical baseline (local, no API, no neural net).

    Used in Phase 3 so the embedding choice is measured even without OPENAI_API_KEY.
    Vocabulary is fit on the indexed corpus then frozen for queries.
    """

    name = "tfidf-baseline"
    dimensions = 0

    def __init__(self, max_features: int = 2048) -> None:
        self._max_features = max_features
        self._index: dict[str, int] = {}
        self._idf: dict[str, float] = {}

    def fit(self, texts: list[str]) -> None:
        df: dict[str, int] = {}
        n_docs = max(len(texts), 1)
        for text in texts:
            for token in set(_tokenize(text)):
                df[token] = df.get(token, 0) + 1
        ranked = sorted(df.items(), key=lambda item: (-item[1], item[0]))[: self._max_features]
        self._index = {token: index for index, (token, _count) in enumerate(ranked)}
        self._idf = {
            token: math.log((n_docs + 1) / (df[token] + 1)) + 1.0 for token, _count in ranked
        }
        self.dimensions = len(self._index)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not self._index:
            self.fit(texts)
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        if not self._index:
            raise RuntimeError("TfidfEmbedder must be fit on the corpus before querying")
        vector = [0.0] * self.dimensions
        tokens = _tokenize(text)
        if not tokens:
            return vector
        tf: dict[str, int] = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
        length = len(tokens)
        for token, count in tf.items():
            index = self._index.get(token)
            if index is None:
                continue
            vector[index] = (count / length) * self._idf[token]
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

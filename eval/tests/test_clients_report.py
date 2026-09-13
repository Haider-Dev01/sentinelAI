from unittest.mock import patch

import pytest

from rag_eval.clients import OllamaClient, OpenAIChatClient
from rag_eval.report import plot_recall


def test_openai_and_ollama_clients(monkeypatch):
    class FakeResponse:
        status_code = 200
        text = "{}"

        def json(self):
            return {"choices": [{"message": {"content": "ok"}}], "response": "local-ok"}

    with patch("rag_eval.clients.httpx.post", return_value=FakeResponse()):
        assert OpenAIChatClient(api_key="sk").generate("p") == "ok"
        assert OllamaClient().generate("p") == "local-ok"

    class Err:
        status_code = 500
        text = "nope"

        def json(self):
            return {}

    with patch("rag_eval.clients.httpx.post", return_value=Err()):
        with pytest.raises(RuntimeError):
            OpenAIChatClient(api_key="sk").generate("p")
        with pytest.raises(RuntimeError):
            OllamaClient().generate("p")


def test_openai_requires_key():
    with pytest.raises(RuntimeError):
        OpenAIChatClient(api_key="")


def test_plot_recall(tmp_path):
    path = tmp_path / "r.png"
    plot_recall(
        path,
        [
            {"embedder": "tfidf-baseline", "chunker": "section", "recall@3": 0.8, "recall@5": 0.9},
            {"embedder": "tfidf-baseline", "chunker": "fixed", "recall@3": 0.5, "recall@5": 0.6},
        ],
    )
    assert path.exists()

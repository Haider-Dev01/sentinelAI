from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest

from pipeline.embeddings.minilm import get_embedder
from pipeline.embeddings.openai import OpenAIEmbedder
from pipeline.http import HttpError, request_json, request_text


def test_get_embedder_tfidf():
    embedder = get_embedder("tfidf")
    assert embedder.name == "tfidf-baseline"


def test_get_embedder_openai():
    embedder = get_embedder("openai", openai_api_key="sk-test")
    assert embedder.name == "text-embedding-3-small"


def test_get_embedder_unknown():
    with pytest.raises(ValueError):
        get_embedder("bert")


def test_openai_embedder_requires_key(monkeypatch):
    monkeypatch.setattr("pipeline.embeddings.openai.settings.openai_api_key", None)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        OpenAIEmbedder(api_key=None)


def test_openai_embedder_parses_response(monkeypatch):
    embedder = OpenAIEmbedder(api_key="sk-test")

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "data": [
                    {"index": 1, "embedding": [0.2, 0.1]},
                    {"index": 0, "embedding": [0.0, 1.0]},
                ]
            }

        text = ""

    with patch("pipeline.embeddings.openai.httpx.post", return_value=FakeResponse()):
        vectors = embedder.embed_documents(["a", "b"])
    assert vectors == [[0.0, 1.0], [0.2, 0.1]]
    with patch("pipeline.embeddings.openai.httpx.post", return_value=FakeResponse()):
        assert embedder.embed_query("a") == [0.0, 1.0]


def test_openai_embedder_error():
    embedder = OpenAIEmbedder(api_key="sk-test")

    class FakeResponse:
        status_code = 401
        text = "unauthorized"

        def json(self):
            return {}

    with patch("pipeline.embeddings.openai.httpx.post", return_value=FakeResponse()):
        with pytest.raises(RuntimeError, match="401"):
            embedder.embed_documents(["x"])


def test_openai_empty_input():
    embedder = OpenAIEmbedder(api_key="sk-test")
    assert embedder.embed_documents([]) == []


def test_request_text_and_json_cache(tmp_data, monkeypatch):
    class FakeResponse:
        status_code = 200
        text = '{"ok": true}'

    with patch("pipeline.http.httpx.get", return_value=FakeResponse()):
        payload = request_json("https://example.com/x", cache_name="example.json")
    assert payload == {"ok": True}
    assert (tmp_data / "raw" / "example.json").exists()
    with patch("pipeline.http.httpx.get") as mocked:
        again = request_json("https://example.com/x", cache_name="example.json")
    mocked.assert_not_called()
    assert again == {"ok": True}


def test_request_text_http_error():
    class FakeResponse:
        status_code = 500
        text = "boom"

    with patch("pipeline.http.httpx.get", return_value=FakeResponse()):
        with pytest.raises(HttpError):
            request_text("https://example.com/fail")


def test_http_throttle_sleeps(monkeypatch):
    monkeypatch.setattr("pipeline.http.settings.nvd_request_delay_seconds", 0.01)
    with patch("pipeline.http.time.sleep") as slept:
        from pipeline.http import throttle_nvd

        throttle_nvd()
    slept.assert_called_once()


def test_request_text_transport_error():
    with patch("pipeline.http.httpx.get", side_effect=httpx.ConnectError("nope")):
        with pytest.raises(HttpError):
            request_text("https://example.com/fail")

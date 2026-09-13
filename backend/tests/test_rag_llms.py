from unittest.mock import patch

import pytest

from app.services.rag.llms import LLMError, OllamaClient, OpenAIChatClient, TemplateFixClient, get_llm


def test_get_llm_template(monkeypatch):
    monkeypatch.setattr("app.services.rag.llms.settings.llm_provider", "template")
    assert isinstance(get_llm(), TemplateFixClient)


def test_openai_and_ollama_generate(monkeypatch):
    class FakeResponse:
        status_code = 200
        text = "{}"

        def json(self):
            return {"choices": [{"message": {"content": "api-ok"}}], "response": "local-ok"}

    monkeypatch.setattr("app.services.rag.llms.settings.openai_api_key", "sk")
    with patch("app.services.rag.llms.httpx.post", return_value=FakeResponse()):
        assert OpenAIChatClient(api_key="sk").generate("p") == "api-ok"
        assert OllamaClient().generate("p") == "local-ok"

    class Err:
        status_code = 502
        text = "down"

        def json(self):
            return {}

    with patch("app.services.rag.llms.httpx.post", return_value=Err()):
        with pytest.raises(LLMError):
            OpenAIChatClient(api_key="sk").generate("p")
        with pytest.raises(LLMError):
            OllamaClient().generate("p")


def test_openai_requires_key(monkeypatch):
    monkeypatch.setattr("app.services.rag.llms.settings.openai_api_key", None)
    with pytest.raises(LLMError):
        OpenAIChatClient(api_key=None)

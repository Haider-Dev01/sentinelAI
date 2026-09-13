from __future__ import annotations

import json

import httpx

from app.config import settings
from app.services.rag.prompts import EXPLAIN_SYSTEM


class LLMError(RuntimeError):
    pass


class OpenAIChatClient:
    name = "openai:gpt-4o-mini"

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini") -> None:
        self._api_key = api_key or settings.openai_api_key
        self.model = model
        self.name = f"openai:{model}"
        if not self._api_key:
            raise LLMError("OPENAI_API_KEY is not set")

    def generate(self, prompt: str, *, system: str = EXPLAIN_SYSTEM) -> str:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self.model,
                "temperature": 0.1,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=60.0,
        )
        if response.status_code >= 400:
            raise LLMError(f"OpenAI failed ({response.status_code})")
        choices = response.json().get("choices") or []
        if not choices:
            return ""
        return str(choices[0].get("message", {}).get("content") or "")


class OllamaClient:
    name = "ollama:llama3.1"

    def __init__(self, base_url: str | None = None, model: str = "llama3.1") -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model
        self.name = f"ollama:{model}"

    def generate(self, prompt: str, *, system: str = EXPLAIN_SYSTEM) -> str:
        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "system": system, "stream": False},
            timeout=120.0,
        )
        if response.status_code >= 400:
            raise LLMError(f"Ollama failed ({response.status_code})")
        return str(response.json().get("response") or "")


class TemplateFixClient:
    name = "template-fixer"

    def generate(self, prompt: str, *, system: str = EXPLAIN_SYSTEM) -> str:
        lower = prompt.lower()
        if "secret" in lower or "gitleaks" in lower or "hard-coded" in lower or "hardcoded" in lower:
            explanation = "Store secrets in the environment (OWASP A07 / CWE-798), never in source."
            fix = "```python\nimport os\n\napi_key = os.environ[\"API_KEY\"]\n```"
        elif "pickle" in lower or "yaml.load" in lower or "deserial" in lower:
            explanation = "Do not unpickle untrusted data (CWE-502 / OWASP A08). Use JSON or yaml.safe_load."
            fix = "```python\nimport json\n\ndata = json.loads(untrusted_bytes)\n```"
        elif "ssrf" in lower or "user-controlled url" in lower:
            explanation = "Allow-list destinations before fetching user-controlled URLs (SSRF / CWE-918)."
            fix = (
                "```python\n"
                "from urllib.parse import urlparse\n\n"
                "allowed = {\"api.internal.example\"}\n"
                "parsed = urlparse(user_url)\n"
                "if parsed.hostname not in allowed:\n"
                "    raise ValueError(\"blocked URL\")\n"
                "```"
            )
        elif "os.system" in lower or "command injection" in lower:
            explanation = "Pass arguments as a list; never concatenate untrusted input into a shell command."
            fix = "```python\nimport subprocess\n\nsubprocess.run([\"nslookup\", domain], check=True)\n```"
        elif "sql" in lower or "injection" in lower:
            explanation = "Keep untrusted data out of interpreters: parameterize queries and allow-list URLs."
            fix = (
                "```python\n"
                "cursor.execute(\n"
                "    \"SELECT * FROM accounts WHERE cust_id = %s\",\n"
                "    (cust_id,),\n"
                ")\n"
                "```"
            )
        else:
            explanation = "Validate input and keep untrusted data out of interpreters, loaders, and HTTP clients."
            fix = (
                "```python\n"
                "from urllib.parse import urlparse\n\n"
                "allowed = {\"api.internal.example\"}\n"
                "parsed = urlparse(user_url)\n"
                "if parsed.hostname not in allowed:\n"
                "    raise ValueError(\"blocked URL\")\n"
                "```"
            )
        return json.dumps({"explanation": explanation, "fix": fix, "language": "python"})


def get_llm():
    provider = (settings.llm_provider or "template").lower()
    if provider == "openai":
        return OpenAIChatClient()
    if provider == "ollama":
        return OllamaClient()
    return TemplateFixClient()

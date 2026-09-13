from __future__ import annotations

import json
import time

import httpx

from rag_eval.prompts import EXPLAIN_SYSTEM


class OllamaClient:
    """Local LLM via Ollama HTTP API (`POST /api/generate`)."""

    name = "ollama:llama3.1"
    usd_per_1k_input = 0.0
    usd_per_1k_output = 0.0

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "llama3.1",
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.name = f"ollama:{model}"

    def generate(self, prompt: str, *, system: str = EXPLAIN_SYSTEM) -> str:
        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "system": system,
                "stream": False,
            },
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Ollama failed ({response.status_code}): {response.text[:300]}")
        return str(response.json().get("response") or "")


class OpenAIChatClient:
    """OpenAI Chat Completions — default gpt-4o-mini for cost-sensitive eval."""

    # Published list prices used for cost estimates (USD / 1K tokens).
    usd_per_1k_input = 0.00015
    usd_per_1k_output = 0.0006

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        timeout: float = 60.0,
    ) -> None:
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required")
        self._api_key = api_key
        self.model = model
        self.timeout = timeout
        self.name = f"openai:{model}"

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
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"OpenAI failed ({response.status_code}): {response.text[:300]}")
        choices = response.json().get("choices") or []
        if not choices:
            return ""
        return str(choices[0].get("message", {}).get("content") or "")


class TemplateFixClient:
    """Deterministic local generator used when Ollama/OpenAI are unavailable.

    Not an LLM: type-specific Python fixes so the eval harness and the API
    still produce measurable, syntax-checkable output. Compared as a baseline
    against a sloppy generator in the LLM table when no remote model is up.
    """

    name = "template-fixer"
    usd_per_1k_input = 0.0
    usd_per_1k_output = 0.0

    def generate(self, prompt: str, *, system: str = EXPLAIN_SYSTEM) -> str:
        time.sleep(0)  # keep interface identical; latency is still measured outside
        lower = prompt.lower()
        if "secret" in lower or "gitleaks" in lower or "hard-coded" in lower or "hardcoded" in lower:
            fix = (
                "```python\n"
                "import os\n\n"
                "api_key = os.environ[\"API_KEY\"]\n"
                "```"
            )
            explanation = "Store secrets in the environment, not in source. OWASP A07 / CWE-798."
        elif "pickle" in lower or "yaml.load" in lower or "deserial" in lower:
            fix = (
                "```python\n"
                "import json\n\n"
                "data = json.loads(untrusted_bytes)\n"
                "```"
            )
            explanation = "Avoid pickle/unsafe loaders on untrusted data (CWE-502 / OWASP A08). Prefer JSON or yaml.safe_load."
        elif "ssrf" in lower or "user-controlled url" in lower:
            fix = (
                "```python\n"
                "from urllib.parse import urlparse\n\n"
                "allowed = {\"api.internal.example\"}\n"
                "parsed = urlparse(user_url)\n"
                "if parsed.hostname not in allowed:\n"
                "    raise ValueError(\"blocked URL\")\n"
                "```"
            )
            explanation = "Allow-list destinations before fetching user-controlled URLs (SSRF / CWE-918, OWASP A01)."
        elif "os.system" in lower or "command injection" in lower or "subprocess" in lower:
            fix = (
                "```python\n"
                "import subprocess\n\n"
                "subprocess.run([\"nslookup\", domain], check=True)\n"
                "```"
            )
            explanation = "Pass arguments as a list; never concatenate untrusted input into a shell command (OWASP A05)."
        elif "lodash" in lower or "cve-2020-8203" in lower:
            fix = (
                "```python\n"
                "# CVE-2020-8203: upgrade lodash to a patched release\n"
                "LODASH_VERSION = \"4.17.21\"\n"
                "```"
            )
            explanation = "Prototype pollution in lodash < 4.17.19 (CVE-2020-8203). Upgrade the dependency."
        elif "log4j" in lower or "cve-2021-44228" in lower:
            fix = (
                "```python\n"
                "# CVE-2021-44228 Log4Shell: use a patched Log4j 2.x\n"
                "LOG4J_VERSION = \"2.17.1\"\n"
                "```"
            )
            explanation = "Log4Shell (CVE-2021-44228) allows RCE via JNDI lookups. Upgrade Log4j to a patched 2.x."
        elif "sql" in lower or "injection" in lower:
            fix = (
                "```python\n"
                "cursor.execute(\n"
                "    \"SELECT * FROM accounts WHERE cust_id = %s\",\n"
                "    (cust_id,),\n"
                ")\n"
                "```"
            )
            explanation = "Keep queries parameterized so user input cannot change SQL structure (OWASP A05)."
        else:
            fix = (
                "```python\n"
                "from urllib.parse import urlparse\n\n"
                "allowed = {\"api.internal.example\"}\n"
                "parsed = urlparse(user_url)\n"
                "if parsed.hostname not in allowed:\n"
                "    raise ValueError(\"blocked URL\")\n"
                "```"
            )
            explanation = "Allow-list destinations and validate input before using it in interpreters or HTTP clients."
        return json.dumps({"explanation": explanation, "fix": fix, "language": "python"})


class SloppyFixClient:
    """Intentionally broken generator — control for the syntax-validity metric."""

    name = "sloppy-fixer"
    usd_per_1k_input = 0.0
    usd_per_1k_output = 0.0

    def generate(self, prompt: str, *, system: str = EXPLAIN_SYSTEM) -> str:
        return json.dumps(
            {
                "explanation": "Just concat the user input, it will be fine.",
                "fix": "```python\ndef (this is not valid python\n```",
                "language": "python",
            }
        )

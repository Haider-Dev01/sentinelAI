from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app.models.finding import Finding
from app.services.rag.llms import get_llm
from app.services.rag.prompts import EXPLAIN_SYSTEM, build_user_prompt
from app.services.rag.retriever import Retriever, RetrievedChunk, query_finding

_FENCE_RE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


@dataclass
class ExplainResult:
    explanation: str
    fix: str
    language: str
    confidence: float
    model: str
    retrieved_doc_ids: list[str]


class ExplainService:
    def __init__(self, retriever: Retriever, llm=None, k: int = 5) -> None:
        self.retriever = retriever
        self.llm = llm or get_llm()
        self.k = k

    def explain(self, finding: Finding) -> ExplainResult:
        hits = self.retriever.search(query_finding(finding), k=self.k)
        confidence = _mean_score(hits)
        prompt = build_user_prompt(finding, [hit.text for hit in hits])
        raw = self.llm.generate(prompt, system=EXPLAIN_SYSTEM)
        parsed = _parse_generation(raw)
        return ExplainResult(
            explanation=parsed["explanation"],
            fix=parsed["fix"],
            language=parsed["language"],
            confidence=round(confidence, 4),
            model=getattr(self.llm, "name", "unknown"),
            retrieved_doc_ids=[hit.document_id for hit in hits if hit.document_id],
        )


def _mean_score(hits: list[RetrievedChunk]) -> float:
    if not hits:
        return 0.0
    return sum(hit.score for hit in hits) / len(hits)


def _parse_generation(text: str) -> dict[str, str]:
    payload = _try_json(text)
    explanation = str(payload.get("explanation") or "").strip()
    fix = str(payload.get("fix") or "").strip()
    language = str(payload.get("language") or "python").strip()
    if not explanation:
        explanation = text.strip() or "The model returned an empty explanation."
    if not fix:
        blocks = _FENCE_RE.findall(text or "")
        fix = f"```python\n{blocks[0]}\n```" if blocks else text.strip()
    if not fix.startswith("```"):
        fix = f"```python\n{fix}\n```"
    return {"explanation": explanation, "fix": fix, "language": language}


def _try_json(text: str) -> dict:
    stripped = (text or "").strip()
    if not stripped:
        return {}
    try:
        data = json.loads(stripped)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(stripped[start : end + 1])
                return data if isinstance(data, dict) else {}
            except json.JSONDecodeError:
                return {}
        return {}

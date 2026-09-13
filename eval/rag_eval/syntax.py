from __future__ import annotations

import ast
import json
import re

_FENCE_RE = re.compile(r"```(?:python|py|javascript|js|java)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_code_blocks(text: str) -> list[str]:
    blocks = [match.group(1).strip() for match in _FENCE_RE.finditer(text or "")]
    if blocks:
        return blocks
    stripped = (text or "").strip()
    return [stripped] if stripped else []


def python_syntax_valid(code: str) -> bool:
    if not code.strip():
        return False
    try:
        ast.parse(code)
    except SyntaxError:
        return False
    return True


def first_python_fix_valid(llm_text: str) -> bool:
    candidate = _unwrap_fix_field(llm_text or "")
    blocks = [match.group(1).strip() for match in _FENCE_RE.finditer(candidate)]
    if blocks:
        return any(python_syntax_valid(block) for block in blocks)
    # Bare snippet (no fence) — never treat a JSON envelope as Python.
    if candidate.lstrip().startswith("{"):
        return False
    return python_syntax_valid(candidate)


def _unwrap_fix_field(text: str) -> str:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return text
    if isinstance(data, dict) and data.get("fix"):
        return str(data["fix"])
    return text

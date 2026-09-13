from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

EVAL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EVAL_ROOT))

from rag_eval.clients import OllamaClient, OpenAIChatClient, SloppyFixClient, TemplateFixClient
from rag_eval.prompts import EXPLAIN_SYSTEM, build_user_prompt
from rag_eval.report import write_csv, write_json
from rag_eval.syntax import first_python_fix_valid

logger = logging.getLogger(__name__)
FINDINGS = EVAL_ROOT / "findings_subset.json"
RESULTS = EVAL_ROOT / "results"


def estimate_cost_usd(prompt: str, output: str, client) -> float:
    in_tokens = max(len(prompt) // 4, 1)
    out_tokens = max(len(output) // 4, 1)
    return (in_tokens / 1000) * client.usd_per_1k_input + (out_tokens / 1000) * client.usd_per_1k_output


def resolve_clients() -> list:
    clients = []
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        clients.append(OpenAIChatClient(api_key=api_key))
    ollama = OllamaClient()
    try:
        import httpx

        health = httpx.get(f"{ollama.base_url}/api/tags", timeout=2.0)
        if health.status_code < 400:
            clients.append(ollama)
    except Exception:
        logger.warning("Ollama is not reachable at %s", ollama.base_url)
    if not clients:
        logger.warning("No LLM backends up — measuring template-fixer vs sloppy-fixer (syntax-metric control)")
        clients = [TemplateFixClient(), SloppyFixClient()]
    return clients


def _unavailable_notes() -> list[str]:
    notes = []
    if not os.environ.get("OPENAI_API_KEY"):
        notes.append("openai:gpt-4o-mini skipped — OPENAI_API_KEY unset")
    try:
        import httpx

        health = httpx.get("http://127.0.0.1:11434/api/tags", timeout=2.0)
        if health.status_code >= 400:
            notes.append("ollama:llama3.1 skipped — daemon returned an error")
    except Exception:
        notes.append("ollama:llama3.1 skipped — not reachable at http://127.0.0.1:11434")
    return notes


def evaluate_llms(findings: list[dict], clients: list | None = None) -> dict:
    models = clients if clients is not None else resolve_clients()
    rows = []
    per_finding = []
    for client in models:
        latencies = []
        costs = []
        valid = 0
        for finding in findings:
            prompt = build_user_prompt(finding, finding.get("contexts") or [])
            started = time.perf_counter()
            output = client.generate(prompt, system=EXPLAIN_SYSTEM)
            elapsed = time.perf_counter() - started
            ok = first_python_fix_valid(output)
            latencies.append(elapsed)
            costs.append(estimate_cost_usd(prompt, output, client))
            valid += int(ok)
            per_finding.append(
                {
                    "finding_id": finding["id"],
                    "model": client.name,
                    "latency_s": round(elapsed, 4),
                    "syntax_ok": ok,
                    "output_preview": output[:240],
                }
            )
        n = max(len(findings), 1)
        rows.append(
            {
                "model": client.name,
                "n": len(findings),
                "syntax_ok_rate": round(valid / n, 4),
                "hallucination_rate": round(1 - valid / n, 4),
                "mean_latency_s": round(sum(latencies) / n, 4),
                "mean_cost_usd": round(sum(costs) / n, 6),
            }
        )
    winner = min(rows, key=lambda row: (row["hallucination_rate"], row["mean_latency_s"], row["mean_cost_usd"]))
    return {"rows": rows, "winner": winner, "per_finding": per_finding}


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Run SentinelAI LLM eval")
    parser.add_argument("--findings", type=Path, default=FINDINGS)
    args = parser.parse_args(argv)
    findings = json.loads(args.findings.read_text(encoding="utf-8"))
    payload = evaluate_llms(findings)
    payload["unavailable"] = _unavailable_notes()
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_csv(RESULTS / "llm.csv", payload["rows"])
    write_json(RESULTS / "llm.json", payload)
    write_json(
        RESULTS / "llm_chart.json",
        {
            "kind": "llm_comparison",
            "labels": [row["model"] for row in payload["rows"]],
            "metrics": {
                "syntax_ok_rate": [row["syntax_ok_rate"] for row in payload["rows"]],
                "hallucination_rate": [row["hallucination_rate"] for row in payload["rows"]],
                "mean_latency_s": [row["mean_latency_s"] for row in payload["rows"]],
                "mean_cost_usd": [row["mean_cost_usd"] for row in payload["rows"]],
            },
            "rows": payload["rows"],
            "unavailable": payload["unavailable"],
        },
    )
    print(json.dumps(payload["rows"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# SentinelAI

Plateforme DevSecOps + RAG : scans Semgrep / Gitleaks / OSV, corpus OWASP Top 10:2025 + NVD, **stratégie de retrieval mesurée**, explications de findings.

![frontend coverage](https://img.shields.io/badge/coverage-94%25-brightgreen)
![backend tests](https://img.shields.io/badge/backend_pytest-54_passed-brightgreen)

La page d’accueil du frontend n’est **pas** le dashboard : c’est l’[évaluation du modèle](frontend/) (recall@k, chunking × embeddings, comparatif LLM).

## Décisions mesurées

| Sujet | Doc |
|---|---|
| Retrieval retenu | [`docs/decisions/embedding-strategy.md`](docs/decisions/embedding-strategy.md) — **TF-IDF × section**, recall@5 = 0.944 |
| Générateurs | [`docs/decisions/llm-comparison.md`](docs/decisions/llm-comparison.md) |
| Polling frontend | [`docs/decisions/007-frontend-polling.md`](docs/decisions/007-frontend-polling.md) |

## Lancer

```bash
# API
cd backend && .venv/Scripts/uvicorn app.main:app --reload

# UI (page Évaluation en /)
cd frontend && npm install && npm run dev
```

Sans API, le frontend bascule sur le bundle Phase 3 + fixtures de démo.

```bash
cd frontend && npm test && npm run coverage
```

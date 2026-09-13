# SentinelAI frontend

![coverage](https://img.shields.io/badge/coverage-94%25-brightgreen)

React + TypeScript + Tailwind. La route `/` est la **page Évaluation** (harnais Phase 3), pas le dashboard scans.

## Pages

| Route | Contenu |
|---|---|
| `/` | Tableau chunking × embeddings, recall@3/@5, comparatif LLM, justifications mesurées |
| `/scans` | Liste + polling 2 s si pending/running |
| `/scans/:id` | Findings par sévérité, « Expliquer avec l’IA », diff avant/après |
| `/trends` | Findings par sévérité dans le temps (recharts) |

`VITE_API_URL` (défaut `http://127.0.0.1:8000`). Si l’API est down, fixtures démo + JSON Phase 3 bundlés.

## Tests

```bash
npm test
npm run coverage
```

Couverture actuelle : **94 %** des lignes (Vitest + v8). Cible des composants critiques : `FindingsTable`, `FixDiffViewer`, page Évaluation.

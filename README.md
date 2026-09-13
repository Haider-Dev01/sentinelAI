# SentinelAI

Plateforme DevSecOps + RAG : scans Semgrep / Gitleaks / OSV, corpus OWASP Top 10:2025 + NVD, **stratégie de retrieval mesurée**, explications de findings.

[![CI](https://github.com/Haider-Dev01/sentinelAI/actions/workflows/ci.yml/badge.svg)](https://github.com/Haider-Dev01/sentinelAI/actions/workflows/ci.yml)
![backend coverage](https://img.shields.io/badge/backend_coverage-94%25-brightgreen)
![frontend coverage](https://img.shields.io/badge/frontend_coverage-94%25-brightgreen)

La page d’accueil du frontend n’est **pas** le dashboard : c’est l’[évaluation du modèle](frontend/) (recall@k, chunking × embeddings, comparatif LLM).

## Décisions mesurées

| Sujet | Doc |
|---|---|
| Retrieval retenu | [`docs/decisions/embedding-strategy.md`](docs/decisions/embedding-strategy.md) — **TF-IDF × section**, recall@5 = 0.944 |
| Générateurs | [`docs/decisions/llm-comparison.md`](docs/decisions/llm-comparison.md) |
| Polling frontend | [`docs/decisions/007-frontend-polling.md`](docs/decisions/007-frontend-polling.md) |

## Lancer en local

### Docker Compose (backend, frontend, Postgres, Chroma)

```bash
docker compose up --build
```

- API : http://localhost:8000/health
- UI : http://localhost:8080 (nginx reverse-proxy `/api` → backend)
- Postgres : `localhost:5432` (`sentinel` / `sentinel` / `sentinelai`)
- Chroma HTTP : http://localhost:8001 (le backend indexe encore en client embarqué sous `/data/chroma`)
- L’image backend embarque git, Semgrep, Gitleaks et OSV Scanner (scans live dans Compose / Minikube)

### Dev sans Docker

```bash
# API (venv backend)
cd backend && alembic upgrade head && uvicorn app.main:app --reload

# UI
cd frontend && npm install && npm run dev
```

Sans API, le frontend bascule sur le bundle Phase 3 + fixtures de démo.

### Minikube

```bash
minikube start
eval "$(minikube docker-env)"          # PowerShell : minikube docker-env | Invoke-Expression
docker compose build
kubectl apply -k infra/k8s
kubectl -n sentinelai rollout status deploy/backend
kubectl -n sentinelai rollout status deploy/frontend
minikube service frontend -n sentinelai
minikube service backend -n sentinelai
```

NodePorts : frontend `30081`, backend `30080`. Images `*:local` + `imagePullPolicy: IfNotPresent` pour rester hors registre.

## CI / CD

Pipeline : [`infra/workflows/ci.yml`](infra/workflows/ci.yml) (copie GitHub : [`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

Jobs : **lint** (ruff + `tsc`) → **pytest + coverage** → **vitest + coverage** → tests de l’action réutilisable → **build Docker** → sur `main`, **publication GHCR** (`ghcr.io/<owner>/sentinelai-backend|frontend`).

```bash
cd frontend && npm test && npm run coverage
cd backend && python -m pytest
cd infra/github-action && python -m pytest
```

## Action GitHub réutilisable (cœur produit)

Encapsule `POST /scans` + polling + commentaire de PR. Utilisable dans **n’importe quel** autre repo :

```yaml
# dans un autre dépôt
permissions:
  pull-requests: write
steps:
  - uses: Haider-Dev01/sentinelAI/infra/github-action@main
    with:
      api-url: https://sentinelai.example
      dashboard-url: https://sentinelai.example
      github-token: ${{ secrets.GITHUB_TOKEN }}
```

Détail : [`infra/github-action/README.md`](infra/github-action/README.md).

# SentinelAI GitHub Action (réutilisable)

À coller dans **n’importe quel** autre dépôt :

```yaml
# .github/workflows/sentinelai.yml
name: SentinelAI
on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: Haider-Dev01/sentinelAI/infra/github-action@main
        with:
          api-url: https://sentinelai.example.com
          dashboard-url: https://sentinelai.example.com
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

L’action appelle `POST /scans` avec l’URL Git du repo, poll `GET /scans/{id}` jusqu’à `completed`/`failed`, puis poste un commentaire Markdown (sévérités + tableau des findings + lien `/scans/{id}`).

Tests : `python -m pytest infra/github-action/tests -q` (depuis la racine du monorepo).

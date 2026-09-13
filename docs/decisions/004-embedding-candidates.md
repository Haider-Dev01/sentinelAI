# Modèles d’embeddings (candidats, Phase 2)

Deux encodeurs denses plus une baseline lexicale, **aucun retenu** avant le golden-set eval (Phase 3).

| Candidat | Dim | Coût / contraintes | Rôle |
|---|---|---|---|
| `tfidf-baseline` | vocabulaire ≤ 2048 | Local, gratuit, pas de modèle | Baseline lexicale mesurable sans clé API. |
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | Local, gratuit, CPU (FastEmbed/ONNX) | Encodeur dense reproductible (CI, démo PFE sans clé). |
| `text-embedding-3-small` (OpenAI) | 1536 | API, `OPENAI_API_KEY` | Candidat « plus fort » sur les benchmarks MTEB publics — à **vérifier** sur *notre* corpus OWASP/CVE. |

Les collections Chroma sont nommées `sentinelai-{embedder}-{chunker}` pour que la Phase 3 compare les combinaisons sans réindexer à l’aveugle.

**Pas de seuil de similarité fixé** (cosinus / `k`) : ce sera un paramètre du harnais d’évaluation.

Le pipeline n’appelle MiniLM ni OpenAI dans les tests unitaires : un embedder de hachage déterministe vérifie uniquement l’indexation.

**Phase 3 :** vainqueur mesuré `tfidf-baseline` × `section`. Voir [`embedding-strategy.md`](embedding-strategy.md). `text-embedding-3-small` n’a pas été mesuré (pas de clé).

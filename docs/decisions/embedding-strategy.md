# Stratégie de retrieval retenue (Phase 3)

**Décision :** indexer le corpus eval avec **TF-IDF lexical** (`tfidf-baseline`) et un chunking **par sections markdown** (`section`, cap 1600 caractères). Collection Chroma : `sentinelai-tfidf-baseline-section`. `k=5` à l’API.

Ce n’est pas un défaut d’architecture : c’est le maximum de **recall@5** mesuré sur le golden set (18 questions EN, 22 documents OWASP Top 10:2025 + CVE canoniques).

## Protocole

Harnais : `eval/rag_eval/run_retrieval.py`. Pour chaque couple (chunker ∈ {fixed, paragraph, section} × embedder ∈ {tfidf-baseline, all-minilm-l6-v2}) :

1. chunker le corpus eval (22 documents) ;
2. embedder + upsert Chroma (espace cosinus) ;
3. pour chaque question du golden set, récupérer le top-5 ;
4. **recall@k** = 1 si au moins un `document_id` pertinent est dans le top-k (k=3 et k=5) ;
5. **mean cosine** = similarité moyenne question ↔ chunks retournés, *dans l’espace de cet embedder*.

`text-embedding-3-small` est implémenté mais **n’a pas été mesuré** : `OPENAI_API_KEY` absent. Relancer le harnais avec la clé pour l’ajouter à la table.

Artefacts : [`eval/results/retrieval.csv`](../../eval/results/retrieval.csv), [`retrieval.json`](../../eval/results/retrieval.json), graphique [`retrieval_recall.png`](../../eval/results/retrieval_recall.png), série frontend [`retrieval_chart.json`](../../eval/results/retrieval_chart.json).

## Tableau mesuré (2026-09-13)

Corpus : 22 documents, 135 / 104 / 110 chunks (fixed / paragraph / section).

| Embedder | Chunker | Chunks | recall@3 | recall@5 | mean cosine |
|---|---|---:|---:|---:|---:|
| **tfidf-baseline** | **section** | 110 | **0.8889** | **0.9444** | 0.1903 |
| tfidf-baseline | paragraph | 104 | 0.8333 | 0.8333 | 0.1786 |
| tfidf-baseline | fixed | 135 | 0.7778 | 0.8889 | 0.1802 |
| all-minilm-l6-v2 | paragraph | 104 | 0.7778 | 0.8889 | 0.4762 |
| all-minilm-l6-v2 | fixed | 135 | 0.7222 | 0.8889 | 0.4850 |
| all-minilm-l6-v2 | section | 110 | 0.7222 | 0.8889 | 0.4998 |
| text-embedding-3-small | *tous* | — | *non mesuré* | *non mesuré* | — |

Règle de sélection (code : `pick_winner`) : **recall@5**, puis recall@3, puis mean cosine ; en cas d’égalité, un embedder local bat OpenAI.

## Pourquoi TF-IDF × section, pas MiniLM

1. **La métrique qui compte pour le RAG est recall@k**, pas le cosine brut. Sur ce golden set, TF-IDF + section retrouve le bon document dans le top-5 pour **17/18** questions (16/18 en top-3). MiniLM plafonne à **16/18** en top-5 quelle que soit la stratégie.
2. Les questions sont formulées avec le **vocabulaire source** (identifiants OWASP `A0x:2025`, CVE, CWE-798). Un encodeur lexical aligne exactement ces tokens ; MiniLM n’apporte pas de gain ici.
3. Le chunking **section** suit la structure réelle des pages OWASP (Description / How to prevent / Scenarios / CWEs). `fixed` casse ces blocs ; `paragraph` perd le titre de section. C’est cohérent avec l’hypothèse de [`003-chunking-strategies.md`](003-chunking-strategies.md), maintenant chiffrée.
4. **Ne pas comparer les cosinus entre embedders.** 0.50 MiniLM vs 0.19 TF-IDF ne dit pas que MiniLM « comprend mieux » : les espaces vectoriels sont différents. Le cosine sert à classer les hits *d’un même* modèle, et comme signal de confiance côté API.

Échec restant du vainqueur : **q14** (surnom « Log4Shell » pour CVE-2021-44228). Le texte NVD du CVE ne contient pas forcément ce surnom ; le recall exige l’id exact `cve:CVE-2021-44228`, pas un cousin (CVE-2021-45046). MiniLM rate aussi q14, et rate en plus q15 (Spring4Shell) en chunking section.

## Conséquences produit

| Réglage | Valeur |
|---|---|
| `RAG_EMBEDDER` | `tfidf` |
| `RAG_COLLECTION` | `sentinelai-tfidf-baseline-section` |
| `RAG_K` | 5 |
| Coût embedding | 0 €, pas de téléchargement de modèle pour la voie retenue |

MiniLM reste dans le pipeline (FastEmbed/ONNX) pour un rerun si le golden set passe à des paraphrases sans identifiants. Tant que recall@5 n’a pas montré l’inverse, l’API n’indexe pas MiniLM par défaut.

Repro :

```text
cd data-pipeline
python -m pipeline ingest --eval-corpus
cd ../eval
python -m rag_eval.run_retrieval --persist
```

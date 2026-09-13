# Comparaison des générateurs de correctifs (Phase 3)

**Décision API :** `POST /findings/{id}/explain` utilise par défaut **`template-fixer`** (`LLM_PROVIDER=template`). C’est un générateur déterministe, pas un LLM. Il a été retenu parce que, sur le sous-ensemble de 8 findings, il est le seul backend **mesuré** qui produit un correctif Python syntaxiquement valide à 100 %, à coût 0 et latence négligeable.

Les clients **Ollama (`llama3.1`)** et **OpenAI (`gpt-4o-mini`)** sont implémentés (`eval/rag_eval/clients.py` et `backend/app/services/rag/llms.py`) mais **n’ont pas été exécutés en live** dans cet environnement : pas de démon Ollama sur `127.0.0.1:11434`, pas de `OPENAI_API_KEY`. Le harnais bascule alors sur un contrôle de métrique : `template-fixer` vs `sloppy-fixer`.

## Ce que la métrique « hallucination » mesure ici

Le brief demandait un taux d’hallucination opérationnel : *le correctif proposé compile-t-il / est-il syntaxiquement valide ?* Le harnais parse le champ JSON `fix` (fence markdown) et passe le snippet à `ast.parse`. Un JSON enveloppe n’est jamais traité comme du Python (sinon tout dict JSON « compilerait »).

Ce n’est **pas** une vérif sémantique (le patch répare-t-il vraiment le CWE). Un modèle peut donc réussir la métrique avec un snippet valide mais hors-sujet. C’est documenté pour ne pas survendre le chiffre.

Sous-ensemble : [`eval/findings_subset.json`](../../eval/findings_subset.json) (8 findings Python / lockfile inspirés de Semgrep, gitleaks, OSV). Prompt : contexte RAG injecté + snippet vulnérable → JSON `{explanation, fix, language}`.

Coût : `(len/4)` tokens approximés × prix listés du client. Ollama et template : 0 USD. `gpt-4o-mini` (liste publique utilisée par le harnais) : **0.00015 USD / 1k input**, **0.00060 USD / 1k output**.

## Tableau mesuré (2026-09-13)

Artefacts : [`eval/results/llm.csv`](../../eval/results/llm.csv), [`llm.json`](../../eval/results/llm.json), [`llm_chart.json`](../../eval/results/llm_chart.json).

| Modèle | n | Syntaxe OK | Hallucination (1 − syntaxe) | Latence moyenne | Coût estimé / req | Statut |
|---|---:|---:|---:|---:|---:|---|
| **template-fixer** | 8 | **1.00** | **0.00** | ~0 s | **0 USD** | mesuré — défaut API |
| sloppy-fixer | 8 | 0.00 | 1.00 | ~0 s | 0 USD | mesuré — contrôle négatif |
| ollama:llama3.1 | — | — | — | — | 0 USD | **non mesuré** (daemon injoignable) |
| openai:gpt-4o-mini | — | — | — | — | ~0.00015 / 1k in + 0.00060 / 1k out | **non mesuré** (pas de clé) |

`sloppy-fixer` émet volontairement `def (this is not valid python`. Il sert à prouver que le harnais **peut échouer** : sans lui, un générateur toujours-valide ne démontrerait pas la métrique.

## Pourquoi ne pas afficher de « scores Ollama / GPT » inventés

Un tableau portfolio avec des latences et des taux d’hallucination pour des backends absents serait une décision *non mesurée* — exactement ce que cette phase interdit. Les lignes vides restent dans le tableau pour montrer le protocole ; les chiffres se remplissent en relançant le harnais.

Quand Ollama ou OpenAI sera up, le même script les compare **sur les mêmes 8 findings**, mêmes métriques, sans changer le prompt.

```text
# API locale
ollama serve && ollama pull llama3.1
# puis, éventuellement :
set OPENAI_API_KEY=...
cd eval
python -m rag_eval.run_llm
```

API : `LLM_PROVIDER=ollama` ou `openai`, `RAG_ENABLED=true` après `python -m rag_eval.run_retrieval --persist`.

## Conséquences produit

| Réglage | Valeur |
|---|---|
| `LLM_PROVIDER` | `template` (défaut) ; `ollama` / `openai` dès qu’un backend live bat template sur syntaxe **et** que le coût/latence est acceptable |
| Endpoint | `POST /findings/{id}/explain` → `explanation`, `fix`, `confidence` (cosine moyen des chunks), `retrieved_doc_ids`, `model` |
| Retrieval injecté | collection `sentinelai-tfidf-baseline-section` (voir [`embedding-strategy.md`](embedding-strategy.md)) |

Le template n’est pas « le meilleur LLM du marché ». C’est le seul générateur **vérifié** aujourd’hui qui ne casse pas la syntaxe et ne facture rien — donc le seul choix honnête pour la démo PFE tant que Ollama/OpenAI n’ont pas un run chiffré dans `eval/results/llm.csv`.

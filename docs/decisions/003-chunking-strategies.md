# Stratégies de chunking (candidats, Phase 2)

**Pas de vainqueur chiffré ici** — le harnais d’évaluation est la Phase 3. On indexe les trois stratégies pour pouvoir les comparer sur le golden set.

| Stratégie | Fonction | Hyperparamètres *provisoires* | Hypothèse à tester |
|---|---|---|---|
| `fixed` | `fixed_size_chunks` | 800 caractères, overlap 120 | Fenêtre régulière, baseline naïve. |
| `paragraph` | `paragraph_chunks` | pack jusqu’à 1200 caractères | Un paragraphe OWASP / description CVE ≈ une unité sémantique. |
| `section` | `section_chunks` | headings `#`/`##`/`###`, cap 1600 | Les pages OWASP sont déjà découpées (Description, How to prevent, Scenarios, CWEs). |

Les tailles sont des **points de départ en caractères** (pas de tokenizer imposé avant le benchmark). Elles seront balayées en Phase 3 (ex. 400/800/1600) ; tant que recall@k n’est pas mesuré, aucun de ces chiffres n’est « retenu ».

**Index de travail (provisoire, non justifié par une métrique) :** `section` pour itérer sur le pipeline. Ce n’est pas le choix final.

**Phase 3 :** le vainqueur mesuré est `tfidf-baseline` × `section`. Voir [`embedding-strategy.md`](embedding-strategy.md).

# Scope du corpus NVD (Phase 2)

**Décision :** ne pas ingérer les ~350k CVE de la NVD. Corpus borné à :

1. **12 CVE « canoniques »** (ids explicites) nécessaires au golden set (Log4Shell, Spring4Shell, lodash, xz-utils, etc.).
2. **13 CWE pépins** alignés sur l’OWASP Top 10:2025 et sur ce que Semgrep / gitleaks / OSV voient vraiment (injection, IDOR/SSRF, secrets hardcodés, désérialisation, supply chain…).
3. **15 CVE max par CWE**, **250 documents NVD max** après déduplication.
4. **`noRejected`**, pas de fenêtre de dates (l’API NVD limite les ranges à 120 jours, ce qui multiplierait les requêtes sans garantir un meilleur signal).

**Pourquoi ce scope**

- Le RAG doit expliquer des findings fullstack Python/JS, pas l’historique Windows/firmware.
- CWE-79 seul dépasse 30k CVE : un dump non plafonné noierait A09/A10 et ferait exploser le coût d’embedding local.
- Les ids canoniques garantissent que chaque question du golden set a un document source, indépendamment de l’ordre de pagination NVD.

**Hors scope (volontaire) :** CVE rejected, CWE `NVD-CWE-noinfo`, corpus CVSS Low. Le mapping CWE → OWASP 2025 est dans `data-pipeline/pipeline/taxonomy.py`.

Les métriques de *retrieval* (recall@k, MRR) sur ce corpus restent pour la Phase 3.

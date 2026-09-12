# FastAPI BackgroundTasks vs Celery (Phase 1)

**Décision :** FastAPI `BackgroundTasks` pour exécuter les scans.

**Justification :** en Phase 1 les scans tournent sur une seule instance API et nous n’avons pas encore de métriques de file (profondeur, retries, multi-workers) qui justifieraient un broker Celery/Redis ; on réévaluera dès que les timeouts, la persistance hors process ou le scaling horizontal deviennent mesurables.

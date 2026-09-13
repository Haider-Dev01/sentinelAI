# Vector store : Chroma local (Phase 2)

**Décision :** Chroma persistant en local (`data-pipeline/data/chroma/`), derrière le protocole `VectorStore` (`upsert` / `query` / `count`).

**Justification (infrastructure, pas retrieval) :** Phase 2 doit itérer sur chunking + embeddings sans Postgres vectoriel. Chroma évite une dépendance pgvector tant que le benchmark Phase 3 n’a pas montré qu’on a besoin du même store que l’API FastAPI.

Le code est découplé : `get_vector_store("chroma"|"pgvector")`. `PgVectorStore` lève `NotImplementedError` jusqu’à ce que les métriques Phase 3 (ou le déploiement k8s) justifient le switch. Les métadonnées de chunks sont déjà des scalaires stables (`document_id`, `source`, `category`, `severity`, `cve_id`, …) compatibles JSONB/pgvector.

**Phase 3 :** le corpus eval (22 docs) tient dans Chroma local. Rien dans le harnais ne justifie pgvector pour l’instant. La collection de prod est `sentinelai-tfidf-baseline-section` (voir [`embedding-strategy.md`](embedding-strategy.md)).

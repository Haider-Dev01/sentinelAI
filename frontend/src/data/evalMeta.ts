export const EVAL_PROTOCOL = {
  questions: 18,
  documents: 22,
  combosMeasured: 6,
  ks: [3, 5] as const,
  corpus: "OWASP Top 10:2025 + 12 CVE canoniques (NVD)",
};

export const RETRIEVAL_RATIONALE = [
  "La métrique produit est recall@k (le bon document est-il dans le top-k), pas le cosine brut.",
  "Les questions du golden set utilisent le vocabulaire source (A0x:2025, CVE, CWE) : TF-IDF aligne ces tokens.",
  "Le chunking section suit la structure réelle des pages OWASP. MiniLM plafonne à 16/18 en top-5.",
  "Les cosinus ne se comparent pas d’un embedder à l’autre : espaces vectoriels différents.",
];

export const LLM_RATIONALE = [
  "Hallucination = le correctif ne passe pas ast.parse (métrique automatique, pas un jugement sémantique).",
  "Ollama et gpt-4o-mini sont implémentés mais n’ont pas été exécutés ici : pas de daemon, pas de clé.",
  "template-fixer est le défaut API tant qu’un LLM live n’a pas un run dans eval/results/llm.csv.",
];

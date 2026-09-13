import { useEffect, useState } from "react";
import { getLlmResults, getRetrievalResults } from "../api/client";
import { LlmComparison } from "../components/LlmComparison";
import { RetrievalComparison } from "../components/RetrievalComparison";
import { SourceBadge } from "../components/StatusBadge";
import { EVAL_PROTOCOL, LLM_RATIONALE, RETRIEVAL_RATIONALE } from "../data/evalMeta";
import bundledLlm from "../data/llm.json";
import bundledRetrieval from "../data/retrieval.json";
import { pct } from "../lib/format";
import type { DataSource, LlmResults, RetrievalResults } from "../types";

export function EvaluationPage() {
  const [retrieval, setRetrieval] = useState<RetrievalResults>(bundledRetrieval as RetrievalResults);
  const [llm, setLlm] = useState<LlmResults>(bundledLlm as LlmResults);
  const [source, setSource] = useState<DataSource>("demo");

  useEffect(() => {
    void Promise.all([getRetrievalResults(), getLlmResults()]).then(([ret, models]) => {
      setRetrieval(ret.data);
      setLlm(models.data);
      setSource(ret.source === "live" && models.source === "live" ? "live" : ret.source);
    });
  }, []);

  const winner = retrieval.winner;

  return (
    <div className="space-y-10">
      <section className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <div className="rounded-3xl border border-emerald-900/50 bg-gradient-to-br from-emerald-950/40 to-[#0c1220] p-8">
          <div className="mb-4 flex items-center gap-2">
            <SourceBadge source={source} />
            <span className="font-mono text-[11px] uppercase tracking-wide text-zinc-500">
              golden set · {EVAL_PROTOCOL.questions} questions · {EVAL_PROTOCOL.documents} docs
            </span>
          </div>
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-emerald-400">Stratégie retenue</p>
          <h2 className="mt-2 text-4xl font-semibold tracking-tight text-zinc-50">
            TF-IDF × section
          </h2>
          <p className="mt-2 max-w-xl text-sm leading-relaxed text-zinc-400">
            Collection <code className="text-zinc-200">{`sentinelai-${winner.embedder}-${winner.chunker}`}</code>
            . {EVAL_PROTOCOL.corpus}. OpenAI embeddings non mesurés (pas de clé).
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <MetricCard label="recall@5" value={pct(winner["recall@5"])} hint="17 / 18 questions" />
          <MetricCard label="recall@3" value={pct(winner["recall@3"])} hint="16 / 18" />
          <MetricCard label="combos mesurées" value={String(retrieval.rows.length)} hint="chunk × embedder" />
          <MetricCard label="k API" value="5" hint="top-k retrieval" />
        </div>
      </section>

      <section className="space-y-4">
        <header>
          <h3 className="text-xl font-semibold text-zinc-50">Retrieval : chunking × embeddings</h3>
          <p className="text-sm text-zinc-400">
            Primary metric recall@5, puis recall@3. MiniLM (FastEmbed) est dans le harnais ; il ne gagne pas sur ce
            corpus lexical.
          </p>
        </header>
        <RetrievalComparison data={retrieval} />
        <ul className="grid gap-2 md:grid-cols-2">
          {RETRIEVAL_RATIONALE.map((item) => (
            <li key={item} className="rounded-xl border border-zinc-800 bg-zinc-900/40 px-4 py-3 text-sm text-zinc-300">
              {item}
            </li>
          ))}
        </ul>
      </section>

      <section className="space-y-4">
        <header>
          <h3 className="text-xl font-semibold text-zinc-50">Génération : syntaxe, latence, coût</h3>
          <p className="text-sm text-zinc-400">
            8 findings Python. Un correctif est « halluciné » s’il ne compile pas (`ast.parse`).
          </p>
        </header>
        <LlmComparison data={llm} />
        <ul className="space-y-2">
          {LLM_RATIONALE.map((item) => (
            <li key={item} className="text-sm text-zinc-400">
              → {item}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function MetricCard({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-[#0c1220] p-4">
      <p className="font-mono text-[11px] uppercase tracking-wide text-zinc-500">{label}</p>
      <p className="mt-1 font-mono text-3xl font-semibold text-zinc-50">{value}</p>
      <p className="text-xs text-zinc-500">{hint}</p>
    </div>
  );
}

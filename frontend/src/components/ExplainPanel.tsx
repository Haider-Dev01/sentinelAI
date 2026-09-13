import type { ExplainResponse, Finding } from "../types";
import { snippetFromFinding } from "../lib/findings";
import { pct } from "../lib/format";
import { FixDiffViewer } from "./FixDiffViewer";

interface ExplainPanelProps {
  finding: Finding;
  result: ExplainResponse;
}

export function ExplainPanel({ finding, result }: ExplainPanelProps) {
  return (
    <section className="space-y-4 rounded-2xl border border-emerald-900/40 bg-emerald-950/10 p-5">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-wide text-emerald-400/80">
            Explication RAG
          </p>
          <h3 className="text-base font-semibold text-zinc-50">{finding.rule_id ?? finding.file_path}</h3>
        </div>
        <dl className="flex gap-4 font-mono text-[11px] text-zinc-400">
          <div>
            <dt className="uppercase tracking-wide">Confiance retrieval</dt>
            <dd className="text-lg text-emerald-300">{pct(result.confidence)}</dd>
          </div>
          <div>
            <dt className="uppercase tracking-wide">Modèle</dt>
            <dd className="text-zinc-200">{result.model}</dd>
          </div>
        </dl>
      </header>
      <p className="text-sm leading-relaxed text-zinc-200">{result.explanation}</p>
      {result.retrieved_doc_ids.length > 0 && (
        <p className="font-mono text-xs text-zinc-500">
          Docs : {result.retrieved_doc_ids.join(" · ")}
        </p>
      )}
      <FixDiffViewer before={snippetFromFinding(finding)} after={result.fix} />
    </section>
  );
}

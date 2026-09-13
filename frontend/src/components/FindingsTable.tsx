import type { Finding } from "../types";
import { groupBySeverity } from "../lib/findings";
import { severityLabel } from "../lib/format";
import { SeverityBadge } from "./StatusBadge";

interface FindingsTableProps {
  findings: Finding[];
  explainingId?: string | null;
  onExplain: (finding: Finding) => void;
}

export function FindingsTable({ findings, explainingId, onExplain }: FindingsTableProps) {
  const groups = groupBySeverity(findings);

  if (findings.length === 0) {
    return (
      <p className="rounded-xl border border-zinc-800 bg-zinc-900/40 px-4 py-8 text-center text-sm text-zinc-400">
        Aucun finding pour ce scan.
      </p>
    );
  }

  return (
    <div className="space-y-6">
      {groups.map((group) => (
        <section key={group.severity} data-testid={`severity-group-${group.severity}`}>
          <header className="mb-2 flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-sm font-medium text-zinc-200">
              <SeverityBadge severity={group.severity} />
              <span className="text-zinc-500">
                {group.items.length} finding{group.items.length > 1 ? "s" : ""} ·{" "}
                {severityLabel(group.severity)}
              </span>
            </h3>
          </header>
          <div className="overflow-hidden rounded-xl border border-zinc-800">
            <table className="w-full border-collapse text-left text-sm">
              <thead className="bg-zinc-900/80 font-mono text-[11px] uppercase tracking-wide text-zinc-500">
                <tr>
                  <th className="px-3 py-2">Fichier</th>
                  <th className="px-3 py-2">Règle</th>
                  <th className="px-3 py-2">Scanner</th>
                  <th className="px-3 py-2">Description</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody>
                {group.items.map((finding) => (
                  <tr key={finding.id} className="border-t border-zinc-800/80 bg-[#0c1220]">
                    <td className="px-3 py-3 font-mono text-xs text-zinc-300">
                      {finding.file_path}
                      {finding.line != null ? `:${finding.line}` : ""}
                    </td>
                    <td className="px-3 py-3 font-mono text-xs text-zinc-400">
                      {finding.rule_id ?? "—"}
                    </td>
                    <td className="px-3 py-3 text-xs text-zinc-400">{finding.scanner}</td>
                    <td className="px-3 py-3 text-zinc-200">{finding.description}</td>
                    <td className="px-3 py-3 text-right">
                      <button
                        type="button"
                        onClick={() => onExplain(finding)}
                        disabled={explainingId === finding.id}
                        className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300 hover:bg-emerald-500/20 disabled:opacity-50"
                      >
                        {explainingId === finding.id ? "…" : "Expliquer avec l’IA"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ))}
    </div>
  );
}

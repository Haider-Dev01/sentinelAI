import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { LlmResults } from "../types";
import { pct } from "../lib/format";

export function LlmComparison({ data }: { data: LlmResults }) {
  const chartRows = data.rows.map((row) => ({
    name: row.model,
    syntax: Number((row.syntax_ok_rate * 100).toFixed(1)),
    hallucination: Number((row.hallucination_rate * 100).toFixed(1)),
  }));

  return (
    <div className="space-y-4">
      <div className="w-full rounded-2xl border border-zinc-800 bg-[#0c1220] p-3">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={chartRows}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
            <XAxis dataKey="name" tick={{ fill: "#a1a1aa", fontSize: 12 }} />
            <YAxis domain={[0, 100]} tick={{ fill: "#a1a1aa", fontSize: 11 }} unit="%" />
            <Tooltip
              contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", fontSize: 12 }}
            />
            <Legend />
            <Bar dataKey="syntax" name="syntaxe OK" fill="#34d399" radius={[4, 4, 0, 0]} />
            <Bar dataKey="hallucination" name="hallucination (1 − syntaxe)" fill="#fb7185" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="overflow-hidden rounded-2xl border border-zinc-800">
        <table className="w-full text-left text-sm" data-testid="llm-table">
          <thead className="bg-zinc-900/80 font-mono text-[11px] uppercase tracking-wide text-zinc-500">
            <tr>
              <th className="px-3 py-2">Modèle</th>
              <th className="px-3 py-2">n</th>
              <th className="px-3 py-2">Syntaxe OK</th>
              <th className="px-3 py-2">Hallucination</th>
              <th className="px-3 py-2">Latence</th>
              <th className="px-3 py-2">Coût / req</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((row) => {
              const winner = row.model === data.winner.model;
              return (
                <tr
                  key={row.model}
                  className={winner ? "bg-emerald-950/40" : "border-t border-zinc-800 bg-[#0c1220]"}
                >
                  <td className="px-3 py-2 font-medium text-zinc-100">
                    {row.model}
                    {winner && (
                      <span className="ml-2 rounded-full border border-emerald-500/40 px-2 py-0.5 font-mono text-[10px] uppercase text-emerald-300">
                        défaut API
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 font-mono text-xs">{row.n}</td>
                  <td className="px-3 py-2 font-mono">{pct(row.syntax_ok_rate, 0)}</td>
                  <td className="px-3 py-2 font-mono">{pct(row.hallucination_rate, 0)}</td>
                  <td className="px-3 py-2 font-mono text-xs">{row.mean_latency_s.toFixed(4)} s</td>
                  <td className="px-3 py-2 font-mono text-xs">{row.mean_cost_usd.toFixed(4)} USD</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {(data.unavailable ?? []).length > 0 && (
        <aside className="rounded-xl border border-dashed border-amber-700/50 bg-amber-950/20 px-4 py-3 text-sm text-amber-100/90">
          <p className="mb-1 font-medium text-amber-200">Backends non mesurés — pas de chiffres inventés</p>
          <ul className="list-disc space-y-1 pl-5 font-mono text-xs text-amber-100/80">
            {data.unavailable!.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </aside>
      )}
    </div>
  );
}

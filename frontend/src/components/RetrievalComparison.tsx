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
import type { RetrievalResults } from "../types";
import { pct } from "../lib/format";

export function comboLabel(embedder: string, chunker: string): string {
  const short = embedder.replace("tfidf-baseline", "TF-IDF").replace("all-minilm-l6-v2", "MiniLM");
  return `${short} × ${chunker}`;
}

export function RetrievalComparison({ data }: { data: RetrievalResults }) {
  const chartRows = data.rows.map((row) => ({
    name: comboLabel(row.embedder, row.chunker),
    recall3: Number((row["recall@3"] * 100).toFixed(1)),
    recall5: Number((row["recall@5"] * 100).toFixed(1)),
    winner: row.embedder === data.winner.embedder && row.chunker === data.winner.chunker,
  }));

  return (
    <div className="space-y-4">
      <div className="w-full rounded-2xl border border-zinc-800 bg-[#0c1220] p-3">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartRows} margin={{ top: 8, right: 8, left: 0, bottom: 24 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
            <XAxis dataKey="name" tick={{ fill: "#a1a1aa", fontSize: 11 }} interval={0} angle={-18} textAnchor="end" height={60} />
            <YAxis domain={[0, 100]} tick={{ fill: "#a1a1aa", fontSize: 11 }} unit="%" />
            <Tooltip
              contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", fontSize: 12 }}
              formatter={(value: number | string) => [`${value}%`, ""]}
            />
            <Legend />
            <Bar dataKey="recall3" name="recall@3" fill="#38bdf8" radius={[4, 4, 0, 0]} />
            <Bar dataKey="recall5" name="recall@5" fill="#34d399" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="overflow-hidden rounded-2xl border border-zinc-800">
        <table className="w-full text-left text-sm" data-testid="retrieval-table">
          <thead className="bg-zinc-900/80 font-mono text-[11px] uppercase tracking-wide text-zinc-500">
            <tr>
              <th className="px-3 py-2">Combinaison</th>
              <th className="px-3 py-2">Chunks</th>
              <th className="px-3 py-2">recall@3</th>
              <th className="px-3 py-2">recall@5</th>
              <th className="px-3 py-2">cosine*</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((row) => {
              const winner = row.embedder === data.winner.embedder && row.chunker === data.winner.chunker;
              return (
                <tr
                  key={`${row.embedder}-${row.chunker}`}
                  className={winner ? "bg-emerald-950/40 text-emerald-100" : "border-t border-zinc-800 bg-[#0c1220]"}
                  data-winner={winner ? "true" : "false"}
                >
                  <td className="px-3 py-2 font-medium">
                    {comboLabel(row.embedder, row.chunker)}
                    {winner && (
                      <span className="ml-2 rounded-full border border-emerald-500/40 px-2 py-0.5 font-mono text-[10px] uppercase">
                        retenu
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 font-mono text-xs">{row.n_chunks}</td>
                  <td className="px-3 py-2 font-mono">{pct(row["recall@3"])}</td>
                  <td className="px-3 py-2 font-mono">{pct(row["recall@5"])}</td>
                  <td className="px-3 py-2 font-mono text-zinc-400">{row.mean_cosine.toFixed(3)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-zinc-500">
        * cosine moyen question ↔ chunks, dans l’espace de <em>cet</em> embedder. Ne pas comparer MiniLM et TF-IDF
        entre eux.
      </p>
    </div>
  );
}

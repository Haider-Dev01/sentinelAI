import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TrendResponse } from "../types";

export function TrendChart({ data }: { data: TrendResponse }) {
  const rows = data.points.map((point, index) => ({
    name: `scan ${index + 1}`,
    date: new Date(point.created_at).toLocaleDateString("fr-FR"),
    critical: point.severity_counts.critical,
    high: point.severity_counts.high,
    medium: point.severity_counts.medium,
    low: point.severity_counts.low,
    info: point.severity_counts.info,
    total: point.findings_count,
  }));

  if (rows.length === 0) {
    return (
      <p className="rounded-xl border border-zinc-800 px-4 py-10 text-center text-sm text-zinc-400">
        Pas encore de scan terminé sur ce dépôt.
      </p>
    );
  }

  return (
    <div className="w-full rounded-2xl border border-zinc-800 bg-[#0c1220] p-3" data-testid="trend-chart">
        <ResponsiveContainer width="100%" height={300}>
        <LineChart data={rows}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis dataKey="date" tick={{ fill: "#a1a1aa", fontSize: 12 }} />
          <YAxis allowDecimals={false} tick={{ fill: "#a1a1aa", fontSize: 11 }} />
          <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", fontSize: 12 }} />
          <Legend />
          <Line type="monotone" dataKey="critical" stroke="#fb7185" strokeWidth={2.5} dot={{ r: 4 }} />
          <Line type="monotone" dataKey="high" stroke="#fb923c" strokeWidth={2.5} dot={{ r: 4 }} />
          <Line type="monotone" dataKey="medium" stroke="#fbbf24" strokeWidth={2.5} dot={{ r: 4 }} />
          <Line type="monotone" dataKey="low" stroke="#38bdf8" strokeWidth={2.5} dot={{ r: 4 }} />
          <Line type="monotone" dataKey="total" stroke="#d4d4d8" strokeDasharray="4 4" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

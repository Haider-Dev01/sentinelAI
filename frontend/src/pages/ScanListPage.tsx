import { type FormEvent, useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { DEMO_SCANS } from "../fixtures/demo";
import { createScan, listScans } from "../api/client";
import { SourceBadge, StatusBadge } from "../components/StatusBadge";
import { usePolling } from "../hooks/usePolling";
import { formatDate, shortId } from "../lib/format";
import type { DataSource, ScanSummary } from "../types";

export function ScanListPage() {
  const [scans, setScans] = useState<ScanSummary[]>(DEMO_SCANS);
  const [source, setSource] = useState<DataSource>("demo");
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const refresh = useCallback(async () => {
    const result = await listScans();
    setScans(result.data);
    setSource(result.source);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const live = scans.some((scan) => scan.status === "pending" || scan.status === "running");
  usePolling(() => {
    void refresh();
  }, live);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createScan({ url });
      setUrl("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Échec");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-zinc-50">Scans</h2>
          <p className="text-sm text-zinc-400">
            Polling 2 s tant qu’un scan est pending/running — pas de websocket : les jobs durent des secondes, pas du
            streaming token.
          </p>
        </div>
        <SourceBadge source={source} />
      </header>

      <form onSubmit={onSubmit} className="flex flex-wrap gap-2 rounded-2xl border border-zinc-800 bg-[#0c1220] p-4">
        <input
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          placeholder="https://github.com/org/repo.git"
          className="min-w-64 flex-1 rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 font-mono text-sm text-zinc-100 outline-none focus:border-emerald-500"
          required
        />
        <button
          type="submit"
          disabled={submitting}
          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-emerald-50 hover:bg-emerald-500 disabled:opacity-50"
        >
          Lancer un scan
        </button>
      </form>
      {error && <p className="text-sm text-rose-300">{error}</p>}

      <div className="overflow-hidden rounded-2xl border border-zinc-800">
        <table className="w-full text-left text-sm">
          <thead className="bg-zinc-900/80 font-mono text-[11px] uppercase tracking-wide text-zinc-500">
            <tr>
              <th className="px-3 py-2">Scan</th>
              <th className="px-3 py-2">Dépôt</th>
              <th className="px-3 py-2">Statut</th>
              <th className="px-3 py-2">Findings</th>
              <th className="px-3 py-2">Créé</th>
            </tr>
          </thead>
          <tbody>
            {scans.map((scan) => (
              <tr key={scan.id} className="border-t border-zinc-800 bg-[#0c1220]">
                <td className="px-3 py-3 font-mono text-xs">
                  <Link className="text-emerald-300 hover:underline" to={`/scans/${scan.id}`}>
                    {shortId(scan.id)}
                  </Link>
                </td>
                <td className="px-3 py-3">{scan.repository.name}</td>
                <td className="px-3 py-3">
                  <StatusBadge status={scan.status} />
                </td>
                <td className="px-3 py-3 font-mono text-xs text-zinc-300">
                  {scan.findings_count}{" "}
                  <span className="text-zinc-500">
                    C{scan.severity_counts.critical} H{scan.severity_counts.high} M{scan.severity_counts.medium}
                  </span>
                </td>
                <td className="px-3 py-3 text-xs text-zinc-400">{formatDate(scan.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

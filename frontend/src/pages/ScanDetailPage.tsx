import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { explainFinding, getScan } from "../api/client";
import { DEMO_SCAN_DETAIL, demoScanDetail } from "../fixtures/demo";
import { ExplainPanel } from "../components/ExplainPanel";
import { FindingsTable } from "../components/FindingsTable";
import { SourceBadge, StatusBadge } from "../components/StatusBadge";
import { usePolling } from "../hooks/usePolling";
import { formatDate } from "../lib/format";
import type { DataSource, ExplainResponse, Finding, ScanDetail } from "../types";

export function ScanDetailPage() {
  const { scanId = "" } = useParams();
  const [scan, setScan] = useState<ScanDetail | null>(scanId ? demoScanDetail(scanId) : DEMO_SCAN_DETAIL);
  const [source, setSource] = useState<DataSource>("demo");
  const [active, setActive] = useState<Finding | null>(null);
  const [explanation, setExplanation] = useState<ExplainResponse | null>(null);
  const [explainingId, setExplainingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!scanId) {
      return;
    }
    const result = await getScan(scanId);
    setScan(result.data);
    setSource(result.source);
  }, [scanId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const inFlight = scan?.status === "pending" || scan?.status === "running";
  usePolling(() => {
    void refresh();
  }, Boolean(inFlight));

  async function onExplain(finding: Finding) {
    setError(null);
    setExplainingId(finding.id);
    setActive(finding);
    try {
      const result = await explainFinding(finding.id);
      setExplanation(result.data);
      if (result.source === "demo") {
        setSource("demo");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Échec de l’explication");
    } finally {
      setExplainingId(null);
    }
  }

  if (!scan) {
    return <p className="text-sm text-zinc-400">Chargement…</p>;
  }

  return (
    <div className="space-y-6">
      <p className="text-sm text-zinc-500">
        <Link to="/scans" className="text-emerald-400 hover:underline">
          ← scans
        </Link>
      </p>
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-zinc-50">{scan.repository.name}</h2>
          <p className="font-mono text-xs text-zinc-500">
            {scan.commit_sha ?? "commit —"} · {formatDate(scan.created_at)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={scan.status} />
          <SourceBadge source={source} />
        </div>
      </header>
      {scan.error_message && <p className="text-sm text-rose-300">{scan.error_message}</p>}
      {error && <p className="text-sm text-rose-300">{error}</p>}

      <FindingsTable findings={scan.findings} explainingId={explainingId} onExplain={onExplain} />

      {active && explanation && <ExplainPanel finding={active} result={explanation} />}
    </div>
  );
}

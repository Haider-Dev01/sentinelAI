import type { ScanStatus, Severity } from "../types";
import { statusLabel, severityLabel } from "../lib/format";

const statusClass: Record<ScanStatus, string> = {
  pending: "border-amber-500/30 bg-amber-500/10 text-amber-200",
  running: "border-sky-500/30 bg-sky-500/10 text-sky-200",
  completed: "border-emerald-500/30 bg-emerald-500/10 text-emerald-200",
  failed: "border-rose-500/30 bg-rose-500/10 text-rose-200",
};

const severityClass: Record<Severity, string> = {
  critical: "border-rose-500/40 bg-rose-500/15 text-rose-200",
  high: "border-orange-500/40 bg-orange-500/15 text-orange-200",
  medium: "border-amber-500/40 bg-amber-500/15 text-amber-200",
  low: "border-sky-500/40 bg-sky-500/15 text-sky-200",
  info: "border-zinc-500/40 bg-zinc-500/15 text-zinc-300",
};

export function StatusBadge({ status }: { status: ScanStatus }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 font-mono text-[11px] uppercase tracking-wide ${statusClass[status]}`}
    >
      {(status === "pending" || status === "running") && (
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" />
      )}
      {statusLabel(status)}
    </span>
  );
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      className={`inline-flex rounded-full border px-2 py-0.5 font-mono text-[11px] uppercase tracking-wide ${severityClass[severity]}`}
    >
      {severityLabel(severity)}
    </span>
  );
}

export function SourceBadge({ source }: { source: "live" | "demo" }) {
  return (
    <span
      className={`rounded-full border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide ${
        source === "live"
          ? "border-emerald-500/30 text-emerald-300"
          : "border-zinc-600 text-zinc-400"
      }`}
    >
      {source === "live" ? "API live" : "données démo / bundle Phase 3"}
    </span>
  );
}

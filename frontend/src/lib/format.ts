import type { ScanStatus, Severity } from "../types";

export function pct(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`;
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) {
    return "—";
  }
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  return date.toLocaleString("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function shortId(id: string): string {
  return id.slice(0, 8);
}

export function statusLabel(status: ScanStatus): string {
  const labels: Record<ScanStatus, string> = {
    pending: "en attente",
    running: "en cours",
    completed: "terminé",
    failed: "échec",
  };
  return labels[status];
}

export function severityLabel(severity: Severity): string {
  const labels: Record<Severity, string> = {
    critical: "critique",
    high: "haute",
    medium: "moyenne",
    low: "basse",
    info: "info",
  };
  return labels[severity];
}

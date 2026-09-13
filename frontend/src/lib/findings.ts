import type { Finding, Severity } from "../types";

export const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low", "info"];

export interface SeverityGroup {
  severity: Severity;
  items: Finding[];
}

export function groupBySeverity(findings: Finding[]): SeverityGroup[] {
  const buckets = new Map<Severity, Finding[]>();
  for (const severity of SEVERITY_ORDER) {
    buckets.set(severity, []);
  }
  for (const finding of findings) {
    const list = buckets.get(finding.severity) ?? buckets.get("info")!;
    list.push(finding);
  }
  return SEVERITY_ORDER.map((severity) => ({
    severity,
    items: buckets.get(severity) ?? [],
  })).filter((group) => group.items.length > 0);
}

export function snippetFromFinding(finding: Finding): string {
  const raw = finding.raw ?? {};
  if (typeof raw.snippet === "string" && raw.snippet.trim()) {
    return raw.snippet;
  }
  const extra = raw.extra;
  if (extra && typeof extra === "object" && extra !== null && "lines" in extra) {
    const lines = (extra as { lines?: unknown }).lines;
    if (typeof lines === "string" && lines.trim()) {
      return lines;
    }
  }
  return "";
}

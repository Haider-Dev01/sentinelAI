export type ScanStatus = "pending" | "running" | "completed" | "failed";
export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type FindingType = "sast" | "secret" | "dependency";
export type DataSource = "live" | "demo";

export interface SeverityCounts {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
}

export interface Repository {
  id: string;
  name: string;
  url: string | null;
  local_path: string | null;
}

export interface Finding {
  id: string;
  file_path: string;
  line: number | null;
  type: FindingType;
  severity: Severity;
  description: string;
  rule_id: string | null;
  scanner: string;
  raw: Record<string, unknown>;
}

export interface ScanSummary {
  id: string;
  status: ScanStatus;
  commit_sha: string | null;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  repository: Repository;
  findings_count: number;
  severity_counts: SeverityCounts;
}

export interface ScanDetail extends ScanSummary {
  findings: Finding[];
}

export interface ExplainResponse {
  finding_id: string;
  explanation: string;
  fix: string;
  language: string;
  confidence: number;
  model: string;
  retrieved_doc_ids: string[];
}

export interface TrendPoint {
  scan_id: string;
  created_at: string;
  finished_at: string | null;
  findings_count: number;
  severity_counts: SeverityCounts;
}

export interface TrendResponse {
  repository: Repository;
  points: TrendPoint[];
}

export interface RetrievalRow {
  embedder: string;
  chunker: string;
  n_chunks: number;
  "recall@3": number;
  "recall@5": number;
  mean_cosine: number;
}

export interface RetrievalResults {
  generated_at?: string;
  n_documents?: number;
  n_questions?: number;
  winner: RetrievalRow;
  rows: RetrievalRow[];
  skipped?: string[];
}

export interface LlmRow {
  model: string;
  n: number;
  syntax_ok_rate: number;
  hallucination_rate: number;
  mean_latency_s: number;
  mean_cost_usd: number;
}

export interface LlmResults {
  rows: LlmRow[];
  winner: LlmRow;
  unavailable?: string[];
}

export interface ApiResult<T> {
  data: T;
  source: DataSource;
}

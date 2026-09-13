import type {
  ExplainResponse,
  Finding,
  Repository,
  ScanDetail,
  ScanSummary,
  TrendResponse,
} from "../types";

const REPO: Repository = {
  id: "11111111-1111-1111-1111-111111111111",
  name: "payments-api",
  url: "https://github.com/example/payments-api.git",
  local_path: null,
};

const FINDINGS: Finding[] = [
  {
    id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1",
    file_path: "app/accounts.py",
    line: 42,
    type: "sast",
    severity: "high",
    description: "SQL query concatenated with untrusted request parameter (SQL injection).",
    rule_id: "python.sql.injection",
    scanner: "semgrep",
    raw: {
      snippet: 'query = "SELECT * FROM accounts WHERE cust_id=\'" + request.args.get("id") + "\'"\ncursor.execute(query)',
    },
  },
  {
    id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2",
    file_path: "config/settings.py",
    line: 12,
    type: "secret",
    severity: "critical",
    description: "Hardcoded API key in source (CWE-798).",
    rule_id: "generic-api-key",
    scanner: "gitleaks",
    raw: { snippet: 'api_key = "sk-live-SUPER-SECRET-VALUE"' },
  },
  {
    id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3",
    file_path: "app/cache.py",
    line: 8,
    type: "sast",
    severity: "high",
    description: "Untrusted pickle.loads can execute arbitrary code (CWE-502).",
    rule_id: "python.lang.security.deserialization.pickle",
    scanner: "semgrep",
    raw: { snippet: "data = pickle.loads(request.data)" },
  },
  {
    id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa4",
    file_path: "frontend/package-lock.json",
    line: null,
    type: "dependency",
    severity: "medium",
    description: "lodash@4.17.15 prototype pollution (CVE-2020-8203).",
    rule_id: "CVE-2020-8203",
    scanner: "osv-scanner",
    raw: { snippet: '"lodash": "4.17.15"' },
  },
];

export const DEMO_SCANS: ScanSummary[] = [
  {
    id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb1",
    status: "completed",
    commit_sha: "a1b2c3d",
    error_message: null,
    started_at: "2026-09-01T08:01:00Z",
    finished_at: "2026-09-01T08:03:12Z",
    created_at: "2026-09-01T08:00:40Z",
    repository: REPO,
    findings_count: 6,
    severity_counts: { critical: 2, high: 3, medium: 1, low: 0, info: 0 },
  },
  {
    id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb2",
    status: "completed",
    commit_sha: "c4d5e6f",
    error_message: null,
    started_at: "2026-09-08T10:00:00Z",
    finished_at: "2026-09-08T10:02:40Z",
    created_at: "2026-09-08T09:59:50Z",
    repository: REPO,
    findings_count: 5,
    severity_counts: { critical: 1, high: 2, medium: 2, low: 0, info: 0 },
  },
  {
    id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb3",
    status: "running",
    commit_sha: null,
    error_message: null,
    started_at: "2026-09-13T08:10:00Z",
    finished_at: null,
    created_at: "2026-09-13T08:09:50Z",
    repository: REPO,
    findings_count: 0,
    severity_counts: { critical: 0, high: 0, medium: 0, low: 0, info: 0 },
  },
  {
    id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb4",
    status: "completed",
    commit_sha: "f7a8b9c",
    error_message: null,
    started_at: "2026-09-13T07:00:00Z",
    finished_at: "2026-09-13T07:01:55Z",
    created_at: "2026-09-13T06:59:40Z",
    repository: REPO,
    findings_count: 4,
    severity_counts: { critical: 1, high: 2, medium: 1, low: 0, info: 0 },
  },
];

export const DEMO_SCAN_DETAIL: ScanDetail = {
  ...DEMO_SCANS[3],
  findings: FINDINGS,
};

export const DEMO_REPOS: Repository[] = [REPO];

export const DEMO_TRENDS: TrendResponse = {
  repository: REPO,
  points: DEMO_SCANS.filter((scan) => scan.status === "completed")
    .slice()
    .sort((a, b) => a.created_at.localeCompare(b.created_at))
    .map((scan) => ({
      scan_id: scan.id,
      created_at: scan.created_at,
      finished_at: scan.finished_at,
      findings_count: scan.findings_count,
      severity_counts: scan.severity_counts,
    })),
};

const EXPLAINS: Record<string, ExplainResponse> = {
  "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1": {
    finding_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1",
    explanation:
      "Keep queries parameterized so user input cannot change SQL structure (OWASP A05).",
    fix: "```python\ncursor.execute(\n    \"SELECT * FROM accounts WHERE cust_id = %s\",\n    (cust_id,),\n)\n```",
    language: "python",
    confidence: 0.82,
    model: "template-fixer",
    retrieved_doc_ids: ["owasp:A05:2025"],
  },
  "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2": {
    finding_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2",
    explanation: "Store secrets in the environment, not in source. OWASP A07 / CWE-798.",
    fix: "```python\nimport os\n\napi_key = os.environ[\"API_KEY\"]\n```",
    language: "python",
    confidence: 0.77,
    model: "template-fixer",
    retrieved_doc_ids: ["owasp:A07:2025"],
  },
};

export function demoExplain(findingId: string): ExplainResponse {
  return (
    EXPLAINS[findingId] ?? {
      finding_id: findingId,
      explanation: "Validate input and keep untrusted data out of interpreters and HTTP clients.",
      fix: "```python\nfrom urllib.parse import urlparse\n\nallowed = {\"api.internal.example\"}\nparsed = urlparse(user_url)\nif parsed.hostname not in allowed:\n    raise ValueError(\"blocked URL\")\n```",
      language: "python",
      confidence: 0.41,
      model: "template-fixer",
      retrieved_doc_ids: [],
    }
  );
}

export function demoScanDetail(scanId: string): ScanDetail {
  const summary = DEMO_SCANS.find((scan) => scan.id === scanId) ?? DEMO_SCAN_DETAIL;
  if (summary.status !== "completed") {
    return { ...summary, findings: [] };
  }
  return { ...summary, findings: FINDINGS };
}

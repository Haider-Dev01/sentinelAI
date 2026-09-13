import bundledLlm from "../data/llm.json";
import bundledRetrieval from "../data/retrieval.json";
import {
  DEMO_REPOS,
  DEMO_SCANS,
  DEMO_TRENDS,
  demoExplain,
  demoScanDetail,
} from "../fixtures/demo";
import type {
  ApiResult,
  ExplainResponse,
  LlmResults,
  Repository,
  RetrievalResults,
  ScanDetail,
  ScanSummary,
  TrendResponse,
} from "../types";

const BASE = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const GET_TIMEOUT_MS = 800;

async function getJson<T>(path: string): Promise<T> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), GET_TIMEOUT_MS);
  try {
    const response = await fetch(`${BASE}${path}`, { signal: controller.signal });
    if (!response.ok) {
      throw new Error(`${response.status} ${path}`);
    }
    return (await response.json()) as T;
  } finally {
    window.clearTimeout(timer);
  }
}

async function withFallback<T>(path: string, fallback: T): Promise<ApiResult<T>> {
  try {
    const data = await getJson<T>(path);
    return { data, source: "live" };
  } catch {
    return { data: fallback, source: "demo" };
  }
}

export function listScans(): Promise<ApiResult<ScanSummary[]>> {
  return withFallback("/scans", DEMO_SCANS);
}

export function getScan(scanId: string): Promise<ApiResult<ScanDetail>> {
  return withFallback(`/scans/${scanId}`, demoScanDetail(scanId));
}

export async function createScan(payload: { url?: string; path?: string }): Promise<ApiResult<ScanSummary>> {
  try {
    const response = await fetch(`${BASE}/scans`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(8000),
    });
    if (!response.ok) {
      throw new Error(`${response.status}`);
    }
    const data = (await response.json()) as ScanSummary;
    return { data, source: "live" };
  } catch {
    throw new Error("Impossible de créer le scan (API injoignable).");
  }
}

export async function explainFinding(findingId: string): Promise<ApiResult<ExplainResponse>> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), 2500);
  try {
    const response = await fetch(`${BASE}/findings/${findingId}/explain`, {
      method: "POST",
      signal: controller.signal,
    });
    if (!response.ok) {
      throw new Error(`${response.status}`);
    }
    return { data: (await response.json()) as ExplainResponse, source: "live" };
  } catch {
    return { data: demoExplain(findingId), source: "demo" };
  } finally {
    window.clearTimeout(timer);
  }
}

export function listRepositories(): Promise<ApiResult<Repository[]>> {
  return withFallback("/repositories", DEMO_REPOS);
}

export function getTrends(repositoryId: string): Promise<ApiResult<TrendResponse>> {
  return withFallback(`/repositories/${repositoryId}/trends`, DEMO_TRENDS);
}

export function getRetrievalResults(): Promise<ApiResult<RetrievalResults>> {
  return withFallback("/eval/retrieval", bundledRetrieval as RetrievalResults);
}

export function getLlmResults(): Promise<ApiResult<LlmResults>> {
  return withFallback("/eval/llm", bundledLlm as LlmResults);
}

import { useEffect, useState } from "react";
import { DEMO_REPOS, DEMO_TRENDS } from "../fixtures/demo";
import { getTrends, listRepositories } from "../api/client";
import { SourceBadge } from "../components/StatusBadge";
import { TrendChart } from "../components/TrendChart";
import type { DataSource, Repository, TrendResponse } from "../types";

export function TrendsPage() {
  const [repos, setRepos] = useState<Repository[]>(DEMO_REPOS);
  const [selected, setSelected] = useState<string>(DEMO_REPOS[0]?.id ?? "");
  const [trends, setTrends] = useState<TrendResponse | null>(DEMO_TRENDS);
  const [source, setSource] = useState<DataSource>("demo");

  useEffect(() => {
    void listRepositories().then((result) => {
      setRepos(result.data);
      setSource(result.source);
      const first = result.data[0]?.id ?? "";
      setSelected(first);
    });
  }, []);

  useEffect(() => {
    if (!selected) {
      return;
    }
    void getTrends(selected).then((result) => {
      setTrends(result.data);
      setSource(result.source);
    });
  }, [selected]);

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-zinc-50">Tendance d’un dépôt suivi</h2>
          <p className="text-sm text-zinc-400">
            Un point par scan terminé : findings groupés par sévérité dans le temps.
          </p>
        </div>
        <SourceBadge source={source} />
      </header>
      <label className="block text-sm text-zinc-400">
        Dépôt
        <select
          value={selected}
          onChange={(event) => setSelected(event.target.value)}
          className="mt-1 block w-full max-w-md rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
        >
          {repos.map((repo) => (
            <option key={repo.id} value={repo.id}>
              {repo.name}
            </option>
          ))}
        </select>
      </label>
      {trends && <TrendChart data={trends} />}
    </div>
  );
}

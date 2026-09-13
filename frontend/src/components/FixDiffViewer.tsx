import ReactDiffViewer, { DiffMethod } from "react-diff-viewer-continued";
import { extractCodeFence, normalizeSnippet } from "../lib/diff";

interface FixDiffViewerProps {
  before: string;
  after: string;
}

export function FixDiffViewer({ before, after }: FixDiffViewerProps) {
  const oldValue = normalizeSnippet(before) || "(pas de snippet dans le finding)";
  const newValue = extractCodeFence(after) || "(pas de correctif)";

  return (
    <div className="overflow-hidden rounded-xl border border-zinc-800" data-testid="fix-diff-viewer">
      <div className="border-b border-zinc-800 bg-zinc-900/70 px-3 py-2 font-mono text-[11px] uppercase tracking-wide text-zinc-500">
        Diff avant / après
      </div>
      <ReactDiffViewer
        oldValue={oldValue}
        newValue={newValue}
        splitView
        useDarkTheme
        compareMethod={DiffMethod.WORDS}
        leftTitle="Avant (snippet vulnérable)"
        rightTitle="Correctif proposé"
        styles={{
          variables: {
            dark: {
              diffViewerBackground: "#0c1220",
              gutterBackground: "#101826",
              addedBackground: "#052e16",
              removedBackground: "#4c0519",
            },
          },
        }}
      />
    </div>
  );
}

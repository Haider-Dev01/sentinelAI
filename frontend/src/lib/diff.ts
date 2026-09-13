export function extractCodeFence(text: string): string {
  const match = /```(?:[\w+-]*)\s*\n([\s\S]*?)```/.exec(text ?? "");
  if (match?.[1]) {
    return match[1].replace(/\s+$/u, "");
  }
  return (text ?? "").trim();
}

export function normalizeSnippet(text: string): string {
  return (text ?? "").replace(/\r\n/g, "\n").trimEnd();
}

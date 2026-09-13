import { extractCodeFence, normalizeSnippet } from "../lib/diff";
import { formatDate, pct, shortId, statusLabel } from "../lib/format";

describe("extractCodeFence", () => {
  it("pulls the first fenced block", () => {
    expect(extractCodeFence("note\n```python\nx = 1\n```\n")).toBe("x = 1");
  });

  it("returns trimmed text when there is no fence", () => {
    expect(extractCodeFence("  bare  ")).toBe("bare");
  });
});

describe("normalizeSnippet", () => {
  it("strips CR and trailing space", () => {
    expect(normalizeSnippet("a\r\nb  \n")).toBe("a\nb");
  });
});

describe("format helpers", () => {
  it("formats percents, ids, dates and statuses", () => {
    expect(pct(0.9444)).toBe("94.4%");
    expect(shortId("abcdefghijkl")).toBe("abcdefgh");
    expect(statusLabel("running")).toBe("en cours");
    expect(formatDate(null)).toBe("—");
    expect(formatDate("not-a-date")).toBe("—");
    expect(formatDate("2026-09-13T08:00:00Z")).toMatch(/2026/);
  });
});

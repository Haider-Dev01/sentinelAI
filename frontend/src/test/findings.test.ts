import { groupBySeverity, snippetFromFinding } from "../lib/findings";
import type { Finding } from "../types";

function finding(partial: Partial<Finding>): Finding {
  return {
    id: "1",
    file_path: "a.py",
    line: 1,
    type: "sast",
    severity: "high",
    description: "desc",
    rule_id: "r",
    scanner: "semgrep",
    raw: {},
    ...partial,
  };
}

describe("groupBySeverity", () => {
  it("orders critical before high and drops empty buckets", () => {
    const groups = groupBySeverity([
      finding({ id: "h", severity: "high" }),
      finding({ id: "c", severity: "critical" }),
    ]);
    expect(groups.map((group) => group.severity)).toEqual(["critical", "high"]);
    expect(groups[0]?.items[0]?.id).toBe("c");
  });
});

describe("snippetFromFinding", () => {
  it("reads raw.snippet then extra.lines", () => {
    expect(snippetFromFinding(finding({ raw: { snippet: "x = 1" } }))).toBe("x = 1");
    expect(
      snippetFromFinding(finding({ raw: { extra: { lines: "y = 2" } } })),
    ).toBe("y = 2");
    expect(snippetFromFinding(finding({ raw: {} }))).toBe("");
  });
});

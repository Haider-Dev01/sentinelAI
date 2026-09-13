import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FindingsTable } from "../components/FindingsTable";
import type { Finding } from "../types";

const findings: Finding[] = [
  {
    id: "f-high",
    file_path: "app/accounts.py",
    line: 42,
    type: "sast",
    severity: "high",
    description: "SQL injection via concat",
    rule_id: "python.sql.injection",
    scanner: "semgrep",
    raw: { snippet: "q = 1" },
  },
  {
    id: "f-crit",
    file_path: "config/settings.py",
    line: 12,
    type: "secret",
    severity: "critical",
    description: "Hardcoded API key",
    rule_id: "generic-api-key",
    scanner: "gitleaks",
    raw: {},
  },
];

describe("FindingsTable", () => {
  it("groups by severity and fires onExplain", async () => {
    const onExplain = vi.fn();
    render(<FindingsTable findings={findings} onExplain={onExplain} />);
    expect(screen.getByTestId("severity-group-critical")).toBeInTheDocument();
    expect(screen.getByTestId("severity-group-high")).toBeInTheDocument();
    expect(screen.getByText("app/accounts.py:42")).toBeInTheDocument();
    const buttons = screen.getAllByRole("button", { name: /expliquer avec l’ia/i });
    await userEvent.click(buttons[1]!);
    expect(onExplain).toHaveBeenCalledWith(findings[0]);
  });

  it("renders an empty state", () => {
    render(<FindingsTable findings={[]} onExplain={vi.fn()} />);
    expect(screen.getByText(/aucun finding/i)).toBeInTheDocument();
  });
});

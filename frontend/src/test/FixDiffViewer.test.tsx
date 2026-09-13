import { render, screen } from "@testing-library/react";
import { FixDiffViewer } from "../components/FixDiffViewer";

describe("FixDiffViewer", () => {
  it("renders split titles and extracts the fenced fix", () => {
    render(
      <FixDiffViewer
        before={'query = "select " + user_id'}
        after={"```python\ncursor.execute(\"select %s\", (user_id,))\n```"}
      />,
    );
    expect(screen.getByTestId("fix-diff-viewer")).toBeInTheDocument();
    expect(screen.getByText(/avant \(snippet vulnérable\)/i)).toBeInTheDocument();
    expect(screen.getByText(/correctif proposé/i)).toBeInTheDocument();
    expect(screen.getByText(/cursor.execute/)).toBeInTheDocument();
  });

  it("falls back when the snippet is empty", () => {
    render(<FixDiffViewer before="" after="" />);
    const panel = screen.getByTestId("fix-diff-viewer");
    expect(panel.textContent).toMatch(/pas de snippet/);
  });
});

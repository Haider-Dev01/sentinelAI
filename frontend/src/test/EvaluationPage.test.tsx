import { render, screen, waitFor } from "@testing-library/react";
import { EvaluationPage } from "../pages/EvaluationPage";

describe("EvaluationPage", () => {
  it("shows the measured winner and both comparison tables", async () => {
    render(<EvaluationPage />);
    expect(screen.getByRole("heading", { name: /TF-IDF × section/ })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByTestId("retrieval-table")).toBeInTheDocument();
    });
    expect(screen.getByTestId("llm-table")).toBeInTheDocument();
    expect(screen.getAllByText(/94\.4%/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/retenu/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/backends non mesurés/i)).toBeInTheDocument();
  });
});

import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { TrendsPage } from "../pages/TrendsPage";

describe("TrendsPage", () => {
  it("renders the trend chart for the demo repository", async () => {
    render(
      <MemoryRouter>
        <TrendsPage />
      </MemoryRouter>,
    );
    expect(await screen.findByTestId("trend-chart")).toBeInTheDocument();
    expect(screen.getByText(/tendance d’un dépôt suivi/i)).toBeInTheDocument();
  });
});

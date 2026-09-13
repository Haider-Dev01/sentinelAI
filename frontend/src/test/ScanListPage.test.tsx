import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ScanListPage } from "../pages/ScanListPage";

describe("ScanListPage", () => {
  it("lists demo scans with live status badges", async () => {
    render(
      <MemoryRouter>
        <ScanListPage />
      </MemoryRouter>,
    );
    expect((await screen.findAllByText("payments-api")).length).toBeGreaterThan(0);
    expect(screen.getByText(/en cours/i)).toBeInTheDocument();
  });
});

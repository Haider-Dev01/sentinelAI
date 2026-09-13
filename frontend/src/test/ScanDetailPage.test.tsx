import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ScanDetailPage } from "../pages/ScanDetailPage";

describe("ScanDetailPage", () => {
  it("explains a finding and shows the diff viewer", async () => {
    render(
      <MemoryRouter initialEntries={["/scans/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb4"]}>
        <Routes>
          <Route path="/scans/:scanId" element={<ScanDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(await screen.findByText(/payments-api/)).toBeInTheDocument();
    const button = await screen.findAllByRole("button", { name: /expliquer avec l’ia/i });
    await userEvent.click(button[0]!);
    await waitFor(() => {
      expect(screen.getByTestId("fix-diff-viewer")).toBeInTheDocument();
    });
    expect(screen.getByText(/explication rag/i)).toBeInTheDocument();
  });
});

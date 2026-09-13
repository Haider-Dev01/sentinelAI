import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "../App";

describe("App", () => {
  it("opens on the evaluation page and navigates to scans", async () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: /TF-IDF × section/ })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("link", { name: "Scans" }));
    expect(await screen.findByRole("heading", { name: "Scans" })).toBeInTheDocument();
  });
});

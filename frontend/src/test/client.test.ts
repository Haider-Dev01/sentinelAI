import { listScans } from "../api/client";

describe("api client fallback", () => {
  it("returns bundled demo scans when the API is down", async () => {
    const result = await listScans();
    expect(result.source).toBe("demo");
    expect(result.data.length).toBeGreaterThan(0);
    expect(result.data[0]?.repository.name).toBe("payments-api");
  });
});

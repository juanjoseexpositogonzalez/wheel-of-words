import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchHealth } from "../../src/api/client";
import type { HealthResponse } from "../../src/types/health";

const health: HealthResponse = {
  status: "ok",
  service: "wheel-vocabulary-api",
  version: "0.1.0",
  timestamp: "2026-08-02T11:13:00.000Z",
};

describe("fetchHealth", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns the backend health response", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(health), { status: 200 }),
    );

    await expect(fetchHealth()).resolves.toEqual(health);
    expect(fetchMock).toHaveBeenCalledWith("http://localhost:8000/api/v1/health");
  });

  it("rejects non-success responses with their status", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 503 }));

    await expect(fetchHealth()).rejects.toThrow("HTTP 503");
  });
});

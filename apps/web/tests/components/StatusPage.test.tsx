import userEvent from "@testing-library/user-event";
import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchHealth } from "../../src/api/client";
import { StatusPage } from "../../src/pages/StatusPage";

vi.mock("../../src/api/client", () => ({ fetchHealth: vi.fn() }));

const fetchHealthMock = vi.mocked(fetchHealth);

describe("StatusPage", () => {
  afterEach(() => {
    vi.resetAllMocks();
  });

  it("shows loading while the health request is pending", () => {
    fetchHealthMock.mockReturnValue(new Promise<never>(() => undefined));
    render(<StatusPage />);

    expect(screen.getByText("Comprobando estado")).toBeVisible();
  });

  it("shows the healthy state from the backend response", async () => {
    fetchHealthMock.mockResolvedValue({
      status: "ok",
      service: "wheel-vocabulary-api",
      version: "0.1.0",
      timestamp: "2026-08-02T11:13:00.000Z",
    });
    render(<StatusPage />);

    expect(await screen.findByText("Backend disponible")).toBeVisible();
    expect(screen.getByText("wheel-vocabulary-api · 0.1.0")).toBeVisible();
  });

  it("retries an unavailable backend request", async () => {
    const user = userEvent.setup();
    fetchHealthMock.mockRejectedValueOnce(new Error("HTTP 503")).mockResolvedValueOnce({
      status: "ok",
      service: "wheel-vocabulary-api",
      version: "0.1.0",
      timestamp: "2026-08-02T11:13:00.000Z",
    });
    render(<StatusPage />);

    await user.click(await screen.findByRole("button", { name: "Reintentar" }));
    await waitFor(() => expect(fetchHealthMock).toHaveBeenCalledTimes(2));
    expect(await screen.findByText("Backend disponible")).toBeVisible();
  });
});

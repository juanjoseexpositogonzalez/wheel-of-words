import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "../src/App";
import { fetchHealth } from "../src/api/client";

vi.mock("../src/api/client", () => ({ fetchHealth: vi.fn() }));

describe("App", () => {
  afterEach(() => {
    vi.resetAllMocks();
  });

  it("mounts the status page", () => {
    vi.mocked(fetchHealth).mockReturnValue(new Promise<never>(() => undefined));
    render(<App />);

    expect(screen.getByText("Comprobando estado")).toBeVisible();
  });
});

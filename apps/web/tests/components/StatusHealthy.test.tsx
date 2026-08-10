import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatusHealthy } from "../../src/components/StatusHealthy";

describe("StatusHealthy", () => {
  it("renders the available backend version and timestamp", () => {
    render(
      <StatusHealthy
        service="wheel-vocabulary-api"
        version="0.1.0"
        timestamp="2026-08-02T11:13:00.000Z"
      />,
    );

    expect(screen.getByText("Backend disponible")).toBeVisible();
    expect(screen.getByText("wheel-vocabulary-api · 0.1.0")).toBeVisible();
    expect(screen.getByText("2026-08-02T11:13:00.000Z")).toBeVisible();
  });

  it("renders each supplied backend version", () => {
    render(<StatusHealthy service="api" version="2.3.4" timestamp="2026-08-02T12:00:00.000Z" />);

    expect(screen.getByText("api · 2.3.4")).toBeVisible();
  });
});

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatusLoading } from "../../src/components/StatusLoading";

describe("StatusLoading", () => {
  it("announces that the backend status is being checked", () => {
    render(<StatusLoading />);

    expect(screen.getByText("Comprobando estado")).toHaveAttribute("aria-live", "polite");
  });

  it("exposes the loading message as text", () => {
    render(<StatusLoading />);

    expect(screen.getByText("Comprobando estado")).toBeVisible();
  });
});

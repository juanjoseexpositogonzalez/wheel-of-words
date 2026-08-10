import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { StatusError } from "../../src/components/StatusError";

describe("StatusError", () => {
  it("shows a safe unavailable message instead of the technical error", () => {
    render(<StatusError message="HTTP 503: internal stack trace" onRetry={vi.fn()} />);

    expect(screen.getByText("Backend no disponible")).toBeVisible();
    expect(screen.queryByText(/stack trace/i)).not.toBeInTheDocument();
  });

  it("calls the accessible retry control", async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();
    render(<StatusError message="HTTP 503" onRetry={onRetry} />);

    await user.click(screen.getByRole("button", { name: "Reintentar" }));
    expect(onRetry).toHaveBeenCalledOnce();
  });
});

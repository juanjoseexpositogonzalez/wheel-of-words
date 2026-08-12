import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { DeleteImportButton } from "../../src/components/DeleteImportButton";
import { deleteImport } from "../../src/api/imports";

vi.mock("../../src/api/imports", () => ({ deleteImport: vi.fn() }));

const deleteImportMock = vi.mocked(deleteImport);

describe("DeleteImportButton", () => {
  afterEach(() => {
    vi.resetAllMocks();
  });

  it("test_requires_confirmation_before_deleting", async () => {
    const user = userEvent.setup();
    deleteImportMock.mockResolvedValue(undefined);
    render(<DeleteImportButton importId={42} onDeleted={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: /eliminar/i }));

    // One activation shows an accessibly-named confirmation control and
    // issues zero requests (AC-002-16).
    expect(deleteImportMock).not.toHaveBeenCalled();
    const confirmButton = screen.getByRole("button", { name: /confirmar/i });
    expect(confirmButton).toBeInTheDocument();

    await user.click(confirmButton);

    // Confirming issues exactly one DELETE request.
    expect(deleteImportMock).toHaveBeenCalledTimes(1);
    expect(deleteImportMock).toHaveBeenCalledWith(42);
  });

  it("cancelling the confirmation issues no request and returns to the trigger", async () => {
    const user = userEvent.setup();
    render(<DeleteImportButton importId={42} onDeleted={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: /eliminar/i }));
    await user.click(screen.getByRole("button", { name: /cancelar/i }));

    expect(deleteImportMock).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: /eliminar/i })).toBeInTheDocument();
  });

  it("calls onDeleted once the confirmed deletion succeeds", async () => {
    const user = userEvent.setup();
    deleteImportMock.mockResolvedValue(undefined);
    const onDeleted = vi.fn();
    render(<DeleteImportButton importId={7} onDeleted={onDeleted} />);

    await user.click(screen.getByRole("button", { name: /eliminar/i }));
    await user.click(screen.getByRole("button", { name: /confirmar/i }));

    expect(await vi.waitFor(() => onDeleted.mock.calls.length > 0)).toBe(true);
  });

  it("shows the backend error message perceptibly when deletion fails", async () => {
    const user = userEvent.setup();
    deleteImportMock.mockRejectedValue(new Error("La importación solicitada no existe."));
    render(<DeleteImportButton importId={42} onDeleted={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: /eliminar/i }));
    await user.click(screen.getByRole("button", { name: /confirmar/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "La importación solicitada no existe.",
    );
  });
});

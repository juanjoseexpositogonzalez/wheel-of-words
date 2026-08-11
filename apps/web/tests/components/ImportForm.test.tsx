import userEvent from "@testing-library/user-event";
import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ImportForm } from "../../src/components/ImportForm";
import { postImport } from "../../src/api/imports";
import type { ImportResult } from "../../src/types/imports";

vi.mock("../../src/api/imports", () => ({ postImport: vi.fn() }));

const postImportMock = vi.mocked(postImport);

function makeFile(name: string): File {
  return new File(["corro corro corres"], name, { type: "text/plain" });
}

const result: ImportResult = {
  import_status: "succeeded",
  distinct_form_count: 2,
  total_token_count: 3,
  forms: [
    { normalized_form: "corres", display_form: "corres", frequency: 1 },
    { normalized_form: "corro", display_form: "corro", frequency: 2 },
  ],
};

describe("ImportForm", () => {
  afterEach(() => {
    vi.resetAllMocks();
  });

  it("exposes an accessible label for the file input and reaches it by keyboard", async () => {
    const user = userEvent.setup();
    render(<ImportForm onImported={vi.fn()} />);

    const input = screen.getByLabelText("Archivo de texto (.txt)");
    await user.tab();

    expect(input).toHaveFocus();
  });

  it("shows a perceptible importing state while the request is in flight", async () => {
    const user = userEvent.setup();
    let resolveImport: (value: ImportResult) => void = () => undefined;
    postImportMock.mockReturnValue(
      new Promise<ImportResult>((resolve) => {
        resolveImport = resolve;
      }),
    );
    render(<ImportForm onImported={vi.fn()} />);

    await user.upload(screen.getByLabelText("Archivo de texto (.txt)"), makeFile("muestra.txt"));
    await user.click(screen.getByRole("button", { name: "Importar" }));

    expect(await screen.findByText("Importando…")).toBeVisible();

    await act(async () => {
      resolveImport(result);
      await Promise.resolve();
    });
  });

  it("shows the backend error message perceptibly when the import fails", async () => {
    const user = userEvent.setup();
    postImportMock.mockRejectedValue(new Error("Solo se admiten archivos .txt."));
    render(<ImportForm onImported={vi.fn()} />);

    await user.upload(screen.getByLabelText("Archivo de texto (.txt)"), makeFile("notes.pdf"));
    await user.click(screen.getByRole("button", { name: "Importar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Solo se admiten archivos .txt.");
  });
});

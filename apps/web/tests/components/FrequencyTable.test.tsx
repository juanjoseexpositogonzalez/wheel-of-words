import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { FrequencyTable } from "../../src/components/FrequencyTable";
import type { ImportResult } from "../../src/types/imports";

const zeroResult: ImportResult = {
  id: 1,
  import_status: "succeeded",
  distinct_form_count: 0,
  total_token_count: 0,
  forms: [],
};

// Deliberately non-alphabetical: `zorro` < `arbol` < `strasse` would be the
// alphabetical order; this is not it. `strasse`/`Straße` is the pinned case
// where the display form must not be re-derived from the normalized form.
const nonAlphabeticalResult: ImportResult = {
  id: 2,
  import_status: "succeeded",
  distinct_form_count: 3,
  total_token_count: 4,
  forms: [
    { normalized_form: "zorro", display_form: "Zorro", frequency: 1 },
    { normalized_form: "arbol", display_form: "árbol", frequency: 2 },
    { normalized_form: "strasse", display_form: "Straße", frequency: 1 },
  ],
};

describe("FrequencyTable", () => {
  it("renders an explicit zero-state message instead of an error", () => {
    render(<FrequencyTable result={zeroResult} />);

    expect(screen.getByText(/0 formas normalizadas/)).toBeVisible();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("renders each received display form, grouping key, and frequency in server order", () => {
    render(<FrequencyTable result={nonAlphabeticalResult} />);

    const dataRows = screen.getAllByRole("row").slice(1);
    const cellTexts = dataRows.map((row) =>
      within(row).getAllByRole("cell").map((cell) => cell.textContent),
    );

    expect(cellTexts).toEqual([
      ["Zorro", "zorro", "1"],
      ["árbol", "arbol", "2"],
      ["Straße", "strasse", "1"],
    ]);
  });

  it("explains the shown text and grouping key without linguistic claims", () => {
    render(<FrequencyTable result={nonAlphabeticalResult} />);

    expect(screen.getByRole("columnheader", { name: "Texto mostrado" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Clave de agrupación" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Apariciones" })).toBeInTheDocument();
    expect(screen.getByText(/texto mostrado y su clave de agrupación/i)).toBeVisible();

    const tableText = screen.getByRole("table").textContent?.toLowerCase();
    expect(tableText).not.toContain("canónica");
    expect(tableText).not.toContain("lema");
    expect(tableText).not.toContain("lexema");
  });
});

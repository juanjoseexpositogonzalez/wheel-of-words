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

  it("test_renders_received_order_and_display_form_verbatim", () => {
    render(<FrequencyTable result={nonAlphabeticalResult} />);

    const dataRows = screen.getAllByRole("row").slice(1);
    const firstCellTexts = dataRows.map((row) => within(row).getAllByRole("cell")[0]?.textContent);

    expect(firstCellTexts).toEqual(["Zorro", "árbol", "Straße"]);
    expect(screen.getByText("Straße")).toBeVisible();
    expect(screen.queryByText("strasse")).not.toBeInTheDocument();
  });

  it("test_frequency_column_is_not_colour_only", () => {
    render(<FrequencyTable result={nonAlphabeticalResult} />);

    expect(screen.getByRole("columnheader", { name: "Forma mostrada" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Apariciones" })).toBeInTheDocument();
    // Frequency is exposed as plain text content, not as a colour-only cue.
    expect(screen.getByText("2")).toBeVisible();
  });
});

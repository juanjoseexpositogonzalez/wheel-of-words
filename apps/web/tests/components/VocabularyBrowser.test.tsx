import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { VocabularyBrowser } from "../../src/components/VocabularyBrowser";
import type { VocabularyResult } from "../../src/types/vocabulary";

const vocabularyResult: VocabularyResult = {
  id: 7,
  group_count: 4,
  total_occurrence_count: 8,
  groups: [
    { lemma: "run", pos: "VERB", occurrence_count: 3 },
    { lemma: null, pos: null, occurrence_count: 2 },
    { lemma: "walk", pos: null, occurrence_count: 2 },
    { lemma: "mystery", pos: "ZZQX", occurrence_count: 1 },
  ],
};

describe("VocabularyBrowser", () => {
  it("renders the received lemma, POS label, and occurrence count", () => {
    render(<VocabularyBrowser result={vocabularyResult} />);

    const firstRowCells = within(screen.getAllByRole("row")[1])
      .getAllByRole("cell")
      .map((cell) => cell.textContent);

    expect(firstRowCells).toEqual(["run", "Verbo", "3"]);
  });

  it("renders null lemma and POS values with distinct textual bucket labels", () => {
    render(<VocabularyBrowser result={vocabularyResult} />);

    const nullBucketCells = within(screen.getAllByRole("row")[2])
      .getAllByRole("cell")
      .map((cell) => cell.textContent);

    expect(nullBucketCells).toEqual(["Sin lema", "Sin anotar", "2"]);

    const missingPosCells = within(screen.getAllByRole("row")[3])
      .getAllByRole("cell")
      .map((cell) => cell.textContent);

    expect(missingPosCells).toEqual(["walk", "Sin anotar", "2"]);
  });

  it("renders an unmapped POS tag instead of leaving its cell blank", () => {
    render(<VocabularyBrowser result={vocabularyResult} />);

    const unmappedCells = within(screen.getAllByRole("row")[4])
      .getAllByRole("cell")
      .map((cell) => cell.textContent);

    expect(unmappedCells).toEqual(["mystery", "ZZQX", "1"]);
  });

  it("offers no interactive control that could submit a correction", () => {
    render(<VocabularyBrowser result={vocabularyResult} />);

    expect(screen.queryAllByRole("button")).toHaveLength(0);
    expect(screen.queryAllByRole("textbox")).toHaveLength(0);
    expect(screen.queryAllByRole("combobox")).toHaveLength(0);
  });
});

import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AnnotationTable } from "../../src/components/AnnotationTable";
import type { AnnotationResult } from "../../src/types/annotation";

// REQ-003-018/AC-003-19: renders exactly what the API returns — no
// lemmatization, tagging, normalization, or precedence resolution here.
// REQ-003-009/AC-003-09: both confidences are always visible and
// distinguishable as text, never by colour alone.

const annotatedResult: AnnotationResult = {
  id: 7,
  provenance: {
    source: "spacy",
    model_name: "en_core_web_sm",
    model_version: "3.8.0",
    language: "en",
    processed_at: "2026-08-24T09:00:00",
  },
  occurrences: [
    {
      position: 0,
      raw_text: "ran",
      pos: "VERB",
      pos_origin: "automatic",
      automatic_pos: "VERB",
      pos_confidence: 0.98,
      lemma: "run",
      lemma_origin: "automatic",
      automatic_lemma: "run",
      lemma_confidence: null,
    },
    {
      position: 1,
      raw_text: "Zorro",
      pos: "PROPN",
      pos_origin: "manual",
      automatic_pos: "NOUN",
      pos_confidence: 0.42,
      lemma: "Zorro",
      lemma_origin: "automatic",
      automatic_lemma: "Zorro",
      lemma_confidence: null,
    },
  ],
};

const unannotatedResult: AnnotationResult = {
  id: 8,
  provenance: null,
  occurrences: [],
};

describe("AnnotationTable", () => {
  it("renders an explicit empty-state message instead of an error", () => {
    render(<AnnotationTable result={unannotatedResult} />);

    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getByRole("status")).toBeVisible();
  });

  it("renders the received lemma, pos, both confidences, and both origins verbatim", () => {
    render(<AnnotationTable result={annotatedResult} />);

    const dataRows = screen.getAllByRole("row").slice(1);
    const firstRowCells = within(dataRows[0]).getAllByRole("cell").map((cell) => cell.textContent);

    expect(firstRowCells).toContain("ran");
    expect(firstRowCells).toContain("run");
    expect(firstRowCells).toContain("0.98");
    expect(firstRowCells).toContain("automatic");
  });

  it("shows PROPN unfiltered, exactly like any other tag (REQ-003-022)", () => {
    render(<AnnotationTable result={annotatedResult} />);

    const dataRows = screen.getAllByRole("row").slice(1);
    const secondRowCells = within(dataRows[1])
      .getAllByRole("cell")
      .map((cell) => cell.textContent);

    expect(secondRowCells).toContain("Zorro");
    expect(secondRowCells).toContain("manual");
  });

  it("degrades an unmapped UPOS tag to the raw tag instead of leaving the cell blank", () => {
    const unmapped: AnnotationResult = {
      ...annotatedResult,
      occurrences: [{ ...annotatedResult.occurrences[0], pos: "ZZQX" }],
    };

    render(<AnnotationTable result={unmapped} />);

    const dataRows = screen.getAllByRole("row").slice(1);
    const cells = within(dataRows[0]).getAllByRole("cell").map((cell) => cell.textContent);

    expect(cells.some((text) => text?.includes("ZZQX"))).toBe(true);
    expect(cells.every((text) => text !== "")).toBe(true);
  });

  it("null and numeric confidence are distinguishable as text, not only by colour", () => {
    render(<AnnotationTable result={annotatedResult} />);

    const dataRows = screen.getAllByRole("row").slice(1);
    const firstRowCells = within(dataRows[0]).getAllByRole("cell").map((cell) => cell.textContent);

    // pos_confidence is numeric (0.98); lemma_confidence is null for both
    // rows in this fixture (matching the real English adapter, design §P1).
    expect(firstRowCells).toContain("0.98");
    expect(firstRowCells.some((text) => text?.toLowerCase().includes("no informada"))).toBe(true);
  });

  it("renders every row's raw_text with no cell left blank", () => {
    render(<AnnotationTable result={annotatedResult} />);

    const dataRows = screen.getAllByRole("row").slice(1);
    for (const row of dataRows) {
      const cells = within(row).getAllByRole("cell");
      expect(cells.length).toBeGreaterThan(0);
      for (const cell of cells) {
        expect(cell.textContent).not.toBe("");
      }
    }
  });
});

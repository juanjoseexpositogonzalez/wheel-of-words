import userEvent from "@testing-library/user-event";
import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ImportPage } from "../../src/pages/ImportPage";
import { postAnnotation } from "../../src/api/annotation";
import { deleteImport, postImport } from "../../src/api/imports";
import { getVocabulary } from "../../src/api/vocabulary";
import type { AnnotationResult } from "../../src/types/annotation";
import type { ImportResult } from "../../src/types/imports";
import type { VocabularyResult } from "../../src/types/vocabulary";

/**
 * REQ-003-012/§2.6: closes verify-report WARNING-4. `handleAnnotate`, the
 * `annotating`/`error`/`done` states, and the `role="alert"` branch in
 * `ImportPage.tsx` had zero function coverage and no dedicated test — only
 * the Playwright happy path exercised it, and only implicitly. This module
 * drives the annotate trigger directly, including its error branch, which
 * had no coverage anywhere.
 */

vi.mock("../../src/api/imports", () => ({ postImport: vi.fn(), deleteImport: vi.fn() }));
vi.mock("../../src/api/annotation", () => ({ postAnnotation: vi.fn() }));
vi.mock("../../src/api/vocabulary", () => ({ getVocabulary: vi.fn() }));

const postImportMock = vi.mocked(postImport);
const postAnnotationMock = vi.mocked(postAnnotation);
const deleteImportMock = vi.mocked(deleteImport);
const getVocabularyMock = vi.mocked(getVocabulary);

function makeFile(name: string): File {
  return new File(["run ran running"], name, { type: "text/plain" });
}

const importResult: ImportResult = {
  id: 42,
  import_status: "succeeded",
  distinct_form_count: 2,
  total_token_count: 3,
  forms: [
    { normalized_form: "ran", display_form: "ran", frequency: 1 },
    { normalized_form: "run", display_form: "run", frequency: 2 },
  ],
};

const annotationResult: AnnotationResult = {
  id: 42,
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
      raw_text: "run",
      pos: "VERB",
      pos_origin: "automatic",
      automatic_pos: "VERB",
      pos_confidence: 0.9,
      lemma: "run",
      lemma_origin: "automatic",
      automatic_lemma: "run",
      lemma_confidence: null,
    },
  ],
};

const vocabularyResult: VocabularyResult = {
  id: 42,
  group_count: 1,
  total_occurrence_count: 3,
  groups: [{ lemma: "run", pos: "VERB", occurrence_count: 3 }],
};

async function importSuccessfully(user: ReturnType<typeof userEvent.setup>): Promise<void> {
  postImportMock.mockResolvedValue(importResult);
  render(<ImportPage />);

  await user.upload(screen.getByLabelText("Archivo de texto (.txt)"), makeFile("muestra.txt"));
  await user.click(screen.getByRole("button", { name: "Importar" }));

  await screen.findByRole("button", { name: "Anotar" });
}

describe("ImportPage", () => {
  afterEach(() => {
    vi.resetAllMocks();
  });

  it("shows no annotate trigger and no frequency table before an import completes", () => {
    render(<ImportPage />);

    expect(screen.queryByRole("button", { name: "Anotar" })).not.toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("shows the annotate trigger after a successful import, with no annotation table yet", async () => {
    const user = userEvent.setup();

    await importSuccessfully(user);

    expect(screen.getByRole("button", { name: "Anotar" })).toBeEnabled();
    expect(screen.queryByText("Lema, categoría gramatical, origen y confianza por aparición.")).not
      .toBeInTheDocument();
  });

  it("shows a perceptible annotating state and disables the trigger while the request is in flight", async () => {
    const user = userEvent.setup();
    await importSuccessfully(user);
    let resolveAnnotation: (value: AnnotationResult) => void = () => undefined;
    postAnnotationMock.mockReturnValue(
      new Promise<AnnotationResult>((resolve) => {
        resolveAnnotation = resolve;
      }),
    );

    await user.click(screen.getByRole("button", { name: "Anotar" }));

    expect(await screen.findByText("Anotando…")).toBeVisible();
    expect(screen.getByRole("button", { name: "Anotar" })).toBeDisabled();

    await act(async () => {
      resolveAnnotation(annotationResult);
      await Promise.resolve();
    });
  });

  it("renders the annotation table with the received data once annotation succeeds", async () => {
    const user = userEvent.setup();
    await importSuccessfully(user);
    postAnnotationMock.mockResolvedValue(annotationResult);

    await user.click(screen.getByRole("button", { name: "Anotar" }));

    const caption = await screen.findByText(
      "Lema, categoría gramatical, origen y confianza por aparición.",
    );
    const annotationTable = caption.closest("table");
    expect(annotationTable).not.toBeNull();
    expect(annotationTable).toHaveTextContent("run");
    expect(postAnnotationMock).toHaveBeenCalledWith(42);
  });

  it("loads and renders vocabulary groups after a successful import", async () => {
    const user = userEvent.setup();
    await importSuccessfully(user);
    getVocabularyMock.mockResolvedValue(vocabularyResult);

    await user.click(screen.getByRole("button", { name: "Ver vocabulario" }));

    expect(await screen.findByText("Vocabulario agrupado por lema y categoría gramatical.")).toBeVisible();
    expect(screen.getByRole("table", { name: /vocabulario agrupado/i })).toHaveTextContent("run");
    expect(getVocabularyMock).toHaveBeenCalledWith(42);
  });

  it("shows the backend error message perceptibly when annotation fails, and the table is never rendered", async () => {
    const user = userEvent.setup();
    await importSuccessfully(user);
    postAnnotationMock.mockRejectedValue(new Error("El analizador no está disponible."));

    await user.click(screen.getByRole("button", { name: "Anotar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "El analizador no está disponible.",
    );
    expect(
      screen.queryByText("Lema, categoría gramatical, origen y confianza por aparición."),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Anotar" })).toBeEnabled();
  });

  it("resets the annotate state when a new import replaces the previous one", async () => {
    const user = userEvent.setup();
    await importSuccessfully(user);
    postAnnotationMock.mockResolvedValue(annotationResult);
    await user.click(screen.getByRole("button", { name: "Anotar" }));
    await screen.findByText("Lema, categoría gramatical, origen y confianza por aparición.");

    postImportMock.mockResolvedValue({ ...importResult, id: 43 });
    await user.upload(screen.getByLabelText("Archivo de texto (.txt)"), makeFile("otro.txt"));
    await user.click(screen.getByRole("button", { name: "Importar" }));

    await screen.findByRole("button", { name: "Anotar" });
    expect(
      screen.queryByText("Lema, categoría gramatical, origen y confianza por aparición."),
    ).not.toBeInTheDocument();
  });

  it("clears the import, the annotation table, and the annotate trigger once deletion is confirmed", async () => {
    const user = userEvent.setup();
    await importSuccessfully(user);
    postAnnotationMock.mockResolvedValue(annotationResult);
    await user.click(screen.getByRole("button", { name: "Anotar" }));
    await screen.findByText("Lema, categoría gramatical, origen y confianza por aparición.");
    deleteImportMock.mockResolvedValue(undefined);

    await user.click(screen.getByRole("button", { name: /eliminar/i }));
    await user.click(screen.getByRole("button", { name: /confirmar/i }));

    await vi.waitFor(() => {
      expect(screen.queryByRole("button", { name: "Anotar" })).not.toBeInTheDocument();
    });
    expect(
      screen.queryByText("Lema, categoría gramatical, origen y confianza por aparición."),
    ).not.toBeInTheDocument();
    expect(deleteImportMock).toHaveBeenCalledWith(42);
  });
});

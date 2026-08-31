import { useState, type JSX } from "react";
import { postAnnotation } from "../api/annotation";
import { getVocabulary } from "../api/vocabulary";
import { AnnotationTable } from "../components/AnnotationTable";
import { DeleteImportButton } from "../components/DeleteImportButton";
import { FrequencyTable } from "../components/FrequencyTable";
import { ImportForm } from "../components/ImportForm";
import { VocabularyBrowser } from "../components/VocabularyBrowser";
import type { AnnotationResult } from "../types/annotation";
import type { ImportResult } from "../types/imports";
import type { VocabularyResult } from "../types/vocabulary";

// REQ-003-012/§2.6: annotation is its own explicit step, never part of
// import — this trigger is what makes that separation visible to the user
// (design §Delivery lists no dedicated "AnnotateButton.tsx"; wiring lives
// here to keep the new surface to one file beyond design's own list).
type AnnotateState =
  | { kind: "idle" }
  | { kind: "annotating" }
  | { kind: "done"; result: AnnotationResult }
  | { kind: "error"; message: string };

type VocabularyState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "done"; result: VocabularyResult }
  | { kind: "error"; message: string };

export function ImportPage(): JSX.Element {
  const [result, setResult] = useState<ImportResult | null>(null);
  const [annotateState, setAnnotateState] = useState<AnnotateState>({ kind: "idle" });
  const [vocabularyState, setVocabularyState] = useState<VocabularyState>({ kind: "idle" });
  const [selectedPos, setSelectedPos] = useState<string | null>(null);

  function handleImported(imported: ImportResult): void {
    setResult(imported);
    setAnnotateState({ kind: "idle" });
    setVocabularyState({ kind: "idle" });
    setSelectedPos(null);
  }

  function handleDeleted(): void {
    setResult(null);
    setAnnotateState({ kind: "idle" });
    setVocabularyState({ kind: "idle" });
    setSelectedPos(null);
  }

  function handleAnnotate(): void {
    if (result === null) {
      return;
    }
    setAnnotateState({ kind: "annotating" });
    void postAnnotation(result.id).then(
      (annotationResult) => {
        setAnnotateState({ kind: "done", result: annotationResult });
      },
      (error: unknown) => {
        setAnnotateState({
          kind: "error",
          message: error instanceof Error ? error.message : "Error desconocido",
        });
      },
    );
  }

  function handleVocabulary(): void {
    loadVocabulary(null);
  }

  function handlePosChange(pos: string | null): void {
    setSelectedPos(pos);
    loadVocabulary(pos);
  }

  function loadVocabulary(pos: string | null): void {
    if (result === null) {
      return;
    }
    setVocabularyState({ kind: "loading" });
    const request = pos === null ? getVocabulary(result.id) : getVocabulary(result.id, pos);
    void request.then(
      (vocabularyResult) => {
        setVocabularyState({ kind: "done", result: vocabularyResult });
      },
      (error: unknown) => {
        setVocabularyState({
          kind: "error",
          message: error instanceof Error ? error.message : "Error desconocido",
        });
      },
    );
  }

  return (
    <section aria-label="Importar un texto">
      <ImportForm onImported={handleImported} />
      {result && (
        <>
          <FrequencyTable result={result} />
          <DeleteImportButton importId={result.id} onDeleted={handleDeleted} />
          <div>
            <button
              type="button"
              onClick={handleAnnotate}
              disabled={annotateState.kind === "annotating"}
            >
              Anotar
            </button>
            {annotateState.kind === "annotating" && <p aria-live="polite">Anotando…</p>}
            {annotateState.kind === "error" && <p role="alert">{annotateState.message}</p>}
          </div>
          <div>
            <button
              type="button"
              onClick={handleVocabulary}
              disabled={vocabularyState.kind === "loading"}
            >
              Ver vocabulario
            </button>
            {vocabularyState.kind === "loading" && <p aria-live="polite">Cargando vocabulario…</p>}
            {vocabularyState.kind === "error" && <p role="alert">{vocabularyState.message}</p>}
          </div>
          {annotateState.kind === "done" && <AnnotationTable result={annotateState.result} />}
          {vocabularyState.kind === "done" && (
            <VocabularyBrowser
              result={vocabularyState.result}
              selectedPos={selectedPos}
              onPosChange={handlePosChange}
            />
          )}
        </>
      )}
    </section>
  );
}

import { useState, type JSX } from "react";
import { postAnnotation } from "../api/annotation";
import { AnnotationTable } from "../components/AnnotationTable";
import { DeleteImportButton } from "../components/DeleteImportButton";
import { FrequencyTable } from "../components/FrequencyTable";
import { ImportForm } from "../components/ImportForm";
import type { AnnotationResult } from "../types/annotation";
import type { ImportResult } from "../types/imports";

// REQ-003-012/§2.6: annotation is its own explicit step, never part of
// import — this trigger is what makes that separation visible to the user
// (design §Delivery lists no dedicated "AnnotateButton.tsx"; wiring lives
// here to keep the new surface to one file beyond design's own list).
type AnnotateState =
  | { kind: "idle" }
  | { kind: "annotating" }
  | { kind: "done"; result: AnnotationResult }
  | { kind: "error"; message: string };

export function ImportPage(): JSX.Element {
  const [result, setResult] = useState<ImportResult | null>(null);
  const [annotateState, setAnnotateState] = useState<AnnotateState>({ kind: "idle" });

  function handleImported(imported: ImportResult): void {
    setResult(imported);
    setAnnotateState({ kind: "idle" });
  }

  function handleDeleted(): void {
    setResult(null);
    setAnnotateState({ kind: "idle" });
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
          {annotateState.kind === "done" && <AnnotationTable result={annotateState.result} />}
        </>
      )}
    </section>
  );
}

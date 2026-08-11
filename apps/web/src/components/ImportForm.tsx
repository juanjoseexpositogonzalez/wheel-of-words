import { useRef, useState, type ChangeEvent, type FormEvent, type JSX } from "react";
import { postImport } from "../api/imports";
import type { ImportResult } from "../types/imports";

interface ImportFormProps {
  onImported: (result: ImportResult) => void;
}

type FormState =
  | { kind: "idle" }
  | { kind: "selected"; file: File }
  | { kind: "importing" }
  | { kind: "error"; message: string };

export function ImportForm({ onImported }: ImportFormProps): JSX.Element {
  const [state, setState] = useState<FormState>({ kind: "idle" });
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>): void {
    const file = event.target.files?.[0];
    setState(file ? { kind: "selected", file } : { kind: "idle" });
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (state.kind !== "selected") {
      return;
    }
    const { file } = state;
    setState({ kind: "importing" });
    void postImport(file).then(
      (result) => {
        onImported(result);
        setState({ kind: "idle" });
        if (inputRef.current) {
          inputRef.current.value = "";
        }
      },
      (error: unknown) => {
        setState({
          kind: "error",
          message: error instanceof Error ? error.message : "Error desconocido",
        });
      },
    );
  }

  const importing = state.kind === "importing";

  return (
    <form onSubmit={handleSubmit} aria-label="Importar texto">
      <label htmlFor="import-file-input">Archivo de texto (.txt)</label>
      <input
        id="import-file-input"
        ref={inputRef}
        type="file"
        accept=".txt,text/plain"
        onChange={handleFileChange}
        disabled={importing}
      />
      <div>
        <button type="submit" disabled={state.kind !== "selected"}>
          Importar
        </button>
      </div>
      {importing && <p aria-live="polite">Importando…</p>}
      {state.kind === "error" && <p role="alert">{state.message}</p>}
    </form>
  );
}

import { useState, type JSX } from "react";
import { deleteImport } from "../api/imports";

interface DeleteImportButtonProps {
  importId: number;
  onDeleted: () => void;
}

/**
 * Requires an explicit confirmation step before issuing DELETE (AC-002-16,
 * Art. IX.5's confirmation branch). Deletion is permanent — REQ-002-011
 * forbids a soft delete, so there is no undo once the request succeeds.
 */
type ButtonState =
  | { kind: "idle" }
  | { kind: "confirming" }
  | { kind: "deleting" }
  | { kind: "error"; message: string };

export function DeleteImportButton({ importId, onDeleted }: DeleteImportButtonProps): JSX.Element {
  const [state, setState] = useState<ButtonState>({ kind: "idle" });

  function handleActivate(): void {
    setState({ kind: "confirming" });
  }

  function handleCancel(): void {
    setState({ kind: "idle" });
  }

  function handleConfirm(): void {
    setState({ kind: "deleting" });
    void deleteImport(importId).then(
      () => {
        onDeleted();
      },
      (error: unknown) => {
        setState({
          kind: "error",
          message: error instanceof Error ? error.message : "Error desconocido",
        });
      },
    );
  }

  if (state.kind === "confirming" || state.kind === "deleting") {
    const deleting = state.kind === "deleting";
    return (
      <div role="group" aria-label="Confirmar eliminación de la importación">
        <p>¿Eliminar esta importación? Esta acción no se puede deshacer.</p>
        <button type="button" onClick={handleConfirm} disabled={deleting}>
          Confirmar eliminación
        </button>
        <button type="button" onClick={handleCancel} disabled={deleting}>
          Cancelar
        </button>
      </div>
    );
  }

  return (
    <div>
      <button type="button" onClick={handleActivate}>
        Eliminar importación
      </button>
      {state.kind === "error" && <p role="alert">{state.message}</p>}
    </div>
  );
}

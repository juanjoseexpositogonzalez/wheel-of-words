import type { JSX } from "react";

interface StatusErrorProps {
  message: string;
  onRetry: () => void;
}

export function StatusError({ onRetry }: StatusErrorProps): JSX.Element {
  return (
    <section aria-live="assertive">
      <p>Backend no disponible</p>
      <button type="button" aria-label="Reintentar" onClick={onRetry}>
        Reintentar
      </button>
    </section>
  );
}

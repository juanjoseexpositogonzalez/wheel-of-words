import { useState, type JSX } from "react";
import { FrequencyTable } from "../components/FrequencyTable";
import { ImportForm } from "../components/ImportForm";
import type { ImportResult } from "../types/imports";

export function ImportPage(): JSX.Element {
  const [result, setResult] = useState<ImportResult | null>(null);

  return (
    <section aria-label="Importar un texto">
      <ImportForm onImported={setResult} />
      {result && <FrequencyTable result={result} />}
    </section>
  );
}

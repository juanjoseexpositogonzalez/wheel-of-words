import type { JSX } from "react";
import type { ImportResult } from "../types/imports";

interface FrequencyTableProps {
  result: ImportResult;
}

/**
 * Renders `result.forms` exactly as received (REQ-002-014). This module
 * performs no client-side linguistic transformation and MUST NOT derive
 * `display_form` from `normalized_form` — both arrive from the API already
 * computed (AC-002-19).
 */
export function FrequencyTable({ result }: FrequencyTableProps): JSX.Element {
  if (result.distinct_form_count === 0) {
    return (
      <p role="status">
        0 formas normalizadas. El archivo estaba vacío o solo contenía espacios y saltos de línea.
        Esto no es un error.
      </p>
    );
  }

  return (
    <table>
      <caption>
        Lista de formas normalizadas del texto importado, en el orden que devuelve el servidor.
      </caption>
      <thead>
        <tr>
          <th scope="col">Forma mostrada</th>
          <th scope="col">Apariciones</th>
        </tr>
      </thead>
      <tbody>
        {result.forms.map((row, index) => (
          <tr key={`${row.normalized_form}-${index}`}>
            <td>{row.display_form}</td>
            <td>{row.frequency}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

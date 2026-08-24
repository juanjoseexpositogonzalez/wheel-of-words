import type { JSX } from "react";
import type { AnnotatedOccurrence, AnnotationResult } from "../types/annotation";

interface AnnotationTableProps {
  result: AnnotationResult;
}

/**
 * Renders `result.occurrences` exactly as received (REQ-003-018). This
 * module performs no lemmatization, tagging, normalization, or precedence
 * resolution — every effective value, origin marker, and confidence arrives
 * already computed from the API.
 *
 * **UI copy is Spanish**, matching every other shipped component
 * (`FrequencyTable.tsx`, `ImportForm.tsx`, `DeleteImportButton.tsx`) and
 * design §P6's own explicit recommendation: the Spanish singular "Lema"
 * matches neither `lemma` nor `lexeme` (single vs. double `m`), so it is the
 * one column-header spelling that satisfies REQ-003-023's guard without an
 * allow-list entry. An English header ("Lemma") has no such escape — it
 * fails `no-lemma-naming.test.ts`'s exact-match check outright, and per that
 * guard's own precedent (slices 3 and 4), the fix is to rename the UI copy,
 * never to extend the allow-list or weaken the guard.
 *
 * The part-of-speech label map is presentational localization only (spec
 * §6 PV-3, REQ-003-018): it is total over the 17-tag UPOS set and an
 * unmapped or unexpected tag degrades to the received tag rather than a
 * blank cell. `PROPN` carries no special case (REQ-003-022).
 *
 * Confidence is rendered as text, never conveyed by colour alone
 * (REQ-003-009): a missing value reads a distinct "not reported" label; a
 * reported value is shown verbatim as the number the API returned.
 *
 * The origin marker (`pos_origin`/`lemma_origin`) is rendered VERBATIM —
 * the raw `"automatic"`/`"manual"` wire value, never translated — per
 * AC-003-19's "origin marker verbatim" wording.
 */
const UPOS_LABELS: Readonly<Record<string, string>> = {
  ADJ: "Adjetivo",
  ADP: "Adposición",
  ADV: "Adverbio",
  AUX: "Auxiliar",
  CCONJ: "Conjunción coordinante",
  DET: "Determinante",
  INTJ: "Interjección",
  NOUN: "Sustantivo",
  NUM: "Numeral",
  PART: "Partícula",
  PRON: "Pronombre",
  PROPN: "Nombre propio",
  PUNCT: "Puntuación",
  SCONJ: "Conjunción subordinante",
  SYM: "Símbolo",
  VERB: "Verbo",
  X: "Otro",
};

function posLabel(tag: string | null): string {
  if (tag === null) {
    return "Sin anotar";
  }
  return UPOS_LABELS[tag] ?? tag;
}

function confidenceLabel(value: number | null): string {
  if (value === null) {
    return "No informada";
  }
  return String(value);
}

function AnnotationRow({ occurrence }: { occurrence: AnnotatedOccurrence }): JSX.Element {
  return (
    <tr>
      <td>{occurrence.raw_text}</td>
      <td>{occurrence.lemma ?? "Sin lema"}</td>
      <td>{occurrence.lemma_origin}</td>
      <td>{confidenceLabel(occurrence.lemma_confidence)}</td>
      <td>{posLabel(occurrence.pos)}</td>
      <td>{occurrence.pos_origin}</td>
      <td>{confidenceLabel(occurrence.pos_confidence)}</td>
    </tr>
  );
}

export function AnnotationTable({ result }: AnnotationTableProps): JSX.Element {
  if (result.occurrences.length === 0) {
    return <p role="status">No hay apariciones anotadas todavía.</p>;
  }

  return (
    <table>
      <caption>Lema, categoría gramatical, origen y confianza por aparición.</caption>
      <thead>
        <tr>
          <th scope="col">Forma textual</th>
          <th scope="col">Lema</th>
          <th scope="col">Origen del lema</th>
          <th scope="col">Confianza del lema</th>
          <th scope="col">Categoría gramatical</th>
          <th scope="col">Origen de la categoría gramatical</th>
          <th scope="col">Confianza de la categoría gramatical</th>
        </tr>
      </thead>
      <tbody>
        {result.occurrences.map((occurrence) => (
          <AnnotationRow key={occurrence.position} occurrence={occurrence} />
        ))}
      </tbody>
    </table>
  );
}

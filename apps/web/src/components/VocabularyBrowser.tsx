import type { JSX } from "react";
import type { VocabularyGroup, VocabularyResult } from "../types/vocabulary";
import { posLabel, UPOS_LABELS } from "./uposLabels";

interface VocabularyBrowserProps {
  result: VocabularyResult;
  selectedPos: string | null;
  onPosChange: (pos: string | null) => void;
}

function VocabularyRow({ group }: { group: VocabularyGroup }): JSX.Element {
  return (
    <tr>
      <td>{group.lemma ?? "Sin lema"}</td>
      <td>{posLabel(group.pos)}</td>
      <td>{group.occurrence_count}</td>
    </tr>
  );
}

export function VocabularyBrowser({
  result,
  selectedPos,
  onPosChange,
}: VocabularyBrowserProps): JSX.Element {
  const selector = (
    <label>
      Filtrar por categoría gramatical
      <select
        value={selectedPos ?? ""}
        onChange={(event) => onPosChange(event.target.value || null)}
      >
        <option value="">Todas</option>
        <option value="null">Sin anotar</option>
        {Object.entries(UPOS_LABELS).map(([tag, label]) => (
          <option key={tag} value={tag}>
            {label}
          </option>
        ))}
      </select>
    </label>
  );

  if (result.groups.length === 0) {
    return (
      <>
        {selector}
        <p role="status">No hay grupos de vocabulario todavía.</p>
      </>
    );
  }

  return (
    <>
      {selector}
      <table>
        <caption>Vocabulario agrupado por lema y categoría gramatical.</caption>
        <thead>
          <tr>
            <th scope="col">Lema</th>
            <th scope="col">Categoría gramatical</th>
            <th scope="col">Apariciones</th>
          </tr>
        </thead>
        <tbody>
          {result.groups.map((group, index) => (
            <VocabularyRow key={`${group.lemma ?? "null"}-${group.pos ?? "null"}-${index}`} group={group} />
          ))}
        </tbody>
      </table>
    </>
  );
}

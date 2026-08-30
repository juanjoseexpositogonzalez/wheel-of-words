import type { JSX } from "react";
import type { VocabularyGroup, VocabularyResult } from "../types/vocabulary";
import { posLabel } from "./uposLabels";

interface VocabularyBrowserProps {
  result: VocabularyResult;
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

export function VocabularyBrowser({ result }: VocabularyBrowserProps): JSX.Element {
  if (result.groups.length === 0) {
    return <p role="status">No hay grupos de vocabulario todavía.</p>;
  }

  return (
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
  );
}

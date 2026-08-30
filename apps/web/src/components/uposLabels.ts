export const UPOS_LABELS: Readonly<Record<string, string>> = {
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

export function posLabel(tag: string | null): string {
  if (tag === null) {
    return "Sin anotar";
  }
  return UPOS_LABELS[tag] ?? tag;
}

import { describe, expect, it } from "vitest";
import { posLabel, UPOS_LABELS } from "../../src/components/uposLabels";

const UPOS_TAGS = [
  "ADJ",
  "ADP",
  "ADV",
  "AUX",
  "CCONJ",
  "DET",
  "INTJ",
  "NOUN",
  "NUM",
  "PART",
  "PRON",
  "PROPN",
  "PUNCT",
  "SCONJ",
  "SYM",
  "VERB",
  "X",
];

describe("UPOS labels", () => {
  it("maps every UPOS tag to its existing Spanish label", () => {
    expect(Object.keys(UPOS_LABELS).sort()).toEqual(UPOS_TAGS);
    expect(UPOS_TAGS.map(posLabel)).toEqual([
      "Adjetivo",
      "Adposición",
      "Adverbio",
      "Auxiliar",
      "Conjunción coordinante",
      "Determinante",
      "Interjección",
      "Sustantivo",
      "Numeral",
      "Partícula",
      "Pronombre",
      "Nombre propio",
      "Puntuación",
      "Conjunción subordinante",
      "Símbolo",
      "Verbo",
      "Otro",
    ]);
  });

  it("preserves null and unmapped values as explicit labels", () => {
    expect(posLabel(null)).toBe("Sin anotar");
    expect(posLabel("ZZQX")).toBe("ZZQX");
  });
});

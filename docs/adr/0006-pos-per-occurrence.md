# ADR-0006 — POS assigned per occurrence; no single global POS per lemma

Status: Accepted

Date: 2026-07-15

## Context

Constitution Art. V defines the integrity rules for the linguistic model. Two clauses ground this decision directly:

- Art. V.2: "Un lema puede tener múltiples categorías gramaticales."
- Art. V.3: "La categoría se registra por aparición y se agrega posteriormente."

AGENTS.md §4 makes the operational rule explicit:

> "No asignar necesariamente una única categoría gramatical global a cada lema."
> "Conservar la categoría de cada aparición."

These rules exist because literary language is not dictionary language. In a novel, the word "run" may appear as a verb ("she ran") and as a noun ("a good run of luck") in successive paragraphs. Assigning a single global POS to the lemma "run" would either lose one of its roles or require a tie-breaking heuristic that is inherently lossy.

The domain entities relevant to this decision are named in `docs/architecture/overview.md §4`:
- `WordForm`: the exact textual form as it appears in the text.
- `Lexeme` (or `Lema`): the canonical lemma grouping inflected forms.
- `Occurrence`: an individual instance of a form at a specific position in text.
- `PartOfSpeech`: the grammatical category assigned contextually to an `Occurrence`.

POS belongs to `Occurrence`, not to `Lexeme`. The `Lexeme` entity does not carry a POS field as ground truth. Aggregated POS distributions (e.g., "run is 80% verb, 20% noun in this corpus") are derived computations, never stored as primary data.

## Decision

Part-of-speech is stored as a property of each `Occurrence` entity, not of the `Lexeme` or `Lema`. Every time a word form appears in the text, its contextual POS is recorded on that occurrence independently.

Aggregated POS distributions — such as frequency counts per POS for a given lemma — are computed on query, not stored as ground truth. They are derived from the occurrence stream.

The domain model MUST distinguish `WordForm`, `Lexeme`, `Occurrence`, and contextual `PartOfSpeech` as separate, first-class concepts. Collapsing any two of these into one entity (e.g., storing POS on WordForm rather than Occurrence, or treating Lexeme and Occurrence as the same thing) violates Constitution Art. V.2–3.

## Consequences

### Positive

- Accurate handling of homographs and words with multiple grammatical roles; literary corpora are especially rich in these.
- POS data for each occurrence is preserved in full fidelity; nothing is lost to a global-label heuristic.
- Aligns with Constitution Art. V.2–3 and AGENTS.md §4 without any approximation.
- Supports future features such as POS-filtered vocabulary queries or context-aware card generation.

### Negative

- More storage per occurrence: every token record carries a POS tag rather than the POS being stored once per lemma.
- Aggregation queries (e.g., "what POS does this lemma take?") require scanning occurrences and computing distributions, rather than reading a single stored field.

## Alternatives considered

- **Single global POS per lemma** — Rejected: Constitution Art. V.2 explicitly states "Un lema puede tener múltiples categorías gramaticales." A single-POS-per-lemma model cannot represent this. The rejection is constitutional, not a performance tradeoff.
- **POS stored on `WordForm` rather than `Occurrence`** — Rejected: the same word form may appear in multiple syntactic positions within a single text; the POS of a form is not constant across its occurrences. Storing POS on the form rather than the occurrence would produce the same information loss as the single-global-POS alternative, just at a finer granularity.

## References

- [`docs/constitution.md` Art. V.2–3](../constitution.md#artículo-v--integridad-del-modelo-lingüístico)
- [`AGENTS.md §4 — Restricciones del dominio`](../../AGENTS.md#4-restricciones-del-dominio)
- [`docs/architecture/overview.md §4 — Dominio`](../architecture/overview.md#4-backend)
- [`docs/glossary.md`](../glossary.md) (landing in Slice C) — Aparición, Categoría gramatical contextual, Lema
- [`docs/architecture/architecture-baseline.md`](../architecture/architecture-baseline.md) (landing in Slice C)
- See also: ADR-0007 (manual corrections precedence), ADR-0008 (multi-language scope) — Wave 2, landing in Slice C

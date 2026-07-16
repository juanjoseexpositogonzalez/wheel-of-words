# ADR-0009 — Multiword expressions as language-specific instances

Status: Accepted

Date: 2026-07-16

## Context

AGENTS.md §4 contains the following pre-amendment clause:

> "Los phrasal verbs y expresiones multipalabra deben modelarse separadamente."

Constitution Art. V.6 states:

> "Los phrasal verbs se modelan como expresiones multipalabra."

Both rules encode the separate-modeling principle correctly for English, but use English-specific terminology ("phrasal verbs") as the primary framing. Before ADR-0008, the domain implicitly assumed an English-only scope, so naming the MWE concept after its English instance was adequate. ADR-0008 Part (c) changes that: once the domain supports any human language, "phrasal verb" cannot serve as the name of the abstract category — it names only the English instance.

This ADR resolves the abstraction: the domain adopts an abstract, language-agnostic MWE category and maps each language's specific phenomenon to that abstraction via a `mwe_kind` attribute.

The entity `MultiwordExpression` is already listed in `docs/architecture/overview.md §4` as a first-class domain entity. This ADR defines its `mwe_kind` field and the enumeration policy for per-language values.

The canonical Spanish term for the abstract concept is **"expresiones multipalabra específicas del idioma"** — the OQ-10 resolution from design §2.3. This term is used verbatim in the glossary entry heading and wherever the abstract concept is referenced in Spanish-language artifacts.

> **Forward reference — Slice E**: Effective with the v2.0.0 constitution amendment (Slice E of docs-methodology-overhaul), the AGENTS.md §4 MWE clause will be rewritten to name phrasal verbs as the English instance of "expresiones multipalabra específicas del idioma" and preserve the separate-modeling rule in language-agnostic terms. Until Slice E ships, AGENTS.md still carries the pre-amendment phrasing.

## Decision

1. The domain model uses the abstract entity `MultiwordExpression` with a `mwe_kind` field. `mwe_kind` is a string storing the language-specific type of the multiword expression for a given occurrence. Example values:
   - `"phrasal_verb"` — English (verb + particle; e.g., "give up", "look into")
   - `"locución_verbal"` — Spanish (fixed verbal phrase; e.g., "tener en cuenta")
   - `"perífrasis_verbal"` — Spanish (periphrastic construction; e.g., "estar + gerundio")
   - `"trennbares_verb"` — German (separable verb; e.g., "aufmachen")
   - Additional values are registered in the glossary as new language adapters are added.

2. Phrasal verbs are the English instance of this abstraction. `mwe_kind = "phrasal_verb"` is the correct value for English corpora. English-specific plans in product-vision §10 and §12 that reference "phrasal verbs" map to this value — no data loss, no special-casing.

3. `MultiwordExpression` entities are stored separately from `Lexeme`/`WordForm` entities. A MWE is not a single-word lemma entry. The separate-modeling rule from Constitution Art. V.6 and AGENTS.md §4 is preserved; this ADR generalizes the scope of that rule, not its content.

4. Per-language extraction heuristics (how the NLP adapter detects a MWE) are the responsibility of the NLP adapter for that language. The domain model accepts whatever the adapter identifies; the domain does not contain language-specific detection logic.

## Consequences

### Positive

- The domain schema is language-agnostic: adding a new language requires registering a new `mwe_kind` value and writing one NLP adapter; the domain entity, storage, and query layer are unchanged.
- Existing English-specific vocabulary plans map cleanly: "phrasal verb" becomes a `mwe_kind` value rather than a hard-coded entity type.
- OQ-10 canonical wording — "expresiones multipalabra específicas del idioma" — is consistently applied as the abstract concept name in ES artifacts; "language-specific multiword expressions" is the EN equivalent in methodology artifacts.
- Constitution Art. V.6 post-amendment reading is codified without modifying the body of Art. V.6 (the amendment generalizes the scope; this ADR provides the implementation model).

### Negative

- `mwe_kind` becomes a controlled vocabulary that requires maintenance: a new language addition MUST register its `mwe_kind` values in the glossary before the NLP adapter for that language ships.
- Per-language extraction logic must be implemented in each NLP adapter separately — there is no shared detection algorithm.
- UI copy that refers to MWEs must use the canonical Spanish term consistently; ad-hoc translations or synonyms in UI strings must be avoided.

## Alternatives considered

- **Separate top-level entity types per language** (e.g., `PhrasalVerb`, `LocucionVerbal` as distinct domain entities) — Rejected: this approach requires schema changes and migration scripts each time a new language is added; it is the definition of the problem this ADR solves.
- **Fold MWEs into single-word lemmas with a boolean `is_mwe` flag** — Rejected: this collapses the conceptual distinction between a lexical unit and its component tokens; it also directly contradicts Constitution Art. V.6 and AGENTS.md §4, which require separate modeling.
- **Name the abstract category "compound expressions" or "idioms"** — Rejected: "compound expressions" is too broad (it includes compound nouns that are not idiomatic), and "idioms" is a subset of MWEs, not the full category. The canonical ES term "expresiones multipalabra específicas del idioma" is precise and already adopted as the OQ-10 resolution.

## References

- [`docs/constitution.md` Art. V.6](../constitution.md#artículo-v--integridad-del-modelo-lingüístico)
- [`AGENTS.md §4 — Restricciones del dominio`](../../AGENTS.md#4-restricciones-del-dominio)
- [ADR-0006](0006-pos-per-occurrence.md) — POS-per-occurrence model that MWE occurrences also carry
- [ADR-0008](0008-multi-language-scope.md) — Multi-language scope decision that makes this abstraction necessary
- [`docs/glossary.md`](../glossary.md) — Expresión multipalabra específica del idioma (abstract entry), Phrasal verb (English instance)
- [`docs/architecture/overview.md §4`](../architecture/overview.md#4-backend) — `MultiwordExpression` domain entity
- OQ-10 resolution: design §2.3 — "expresiones multipalabra específicas del idioma"

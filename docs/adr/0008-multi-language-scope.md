# ADR-0008 — Multi-language scope from day one

Status: Accepted

Date: 2026-07-16

## Context

The original constitution (v1.0.0, line 9) scoped Wheel Vocabulary explicitly to English vocabulary:

> "Wheel Vocabulary es una aplicación web destinada a extraer, clasificar, consultar y estudiar vocabulario inglés procedente de obras literarias aportadas legalmente por el usuario."

The product-vision §4 (pre-amendment, line 21) defined the target user as:

> "Persona adulta que lee literatura en inglés, desea ampliar vocabulario…"

This English-only framing was a pragmatic starting point, not an architectural constraint. During the docs-methodology-overhaul cycle, the decision was made to generalize the scope to any human language from day one. This decision escalates the constitution amendment from a minor to a MAJOR version bump (v1.0.0 → v2.0.0), because removing the English-only scope qualifier is a breaking change to the product's stated purpose.

The technical architecture — hexagonal split (ADR-0002), spaCy as replaceable NLP adapter (ADR-0001), local-first processing (ADR-0005) — already supports multi-language at the adapter level. No schema changes are required for Part (a) and Part (b) of this decision. Part (c) introduces the `mwe_kind` attribute to handle language-specific MWE modeling (see ADR-0009 for the full treatment).

Three open questions are deferred and do NOT block this decision: language detection strategy (OQ-2), translation provider and consent model (OQ-3), and per-language NLP library selection (OQ-4). These will be addressed in future ADRs when multi-language vertical slices are implemented.

> **Forward reference — Slice E**: Effective with the v2.0.0 constitution amendment (Slice E of docs-methodology-overhaul), the four-file amendment payload will materialize this decision in `docs/constitution.md` (preamble generalization), `docs/product-vision.md` (§4 user targeting, §10 step 6, §12 item 7), `README.md` (line 3), and `AGENTS.md` §4 (MWE clause generalization). Until Slice E ships, those source files still carry the pre-amendment English-only wording.

## Decision

This ADR captures three co-dependent sub-decisions that must be adopted together.

**Part (a) — Corpus scope**: Books analyzed by the application MAY be in any human language legally provided by the user. The system is not restricted to English-language corpora. English is the first-implemented language for continuity, not the exclusive scope.

**Part (b) — User targeting**: The target user is defined as "persona que lee literatura en el idioma que estudia" — framed by study intent, not by a specific language. This replaces the earlier "lee literatura en inglés" framing. A reader studying Japanese by reading Japanese novels is exactly the intended user, as much as an English learner reading English fiction.

**Part (c) — Abstract MWE category**: Language-specific linguistic phenomena that span multiple tokens are modeled as instances of a single abstract category "expresiones multipalabra específicas del idioma" (language-specific multiword expressions). Concrete instantiations: phrasal verbs in English, locuciones y perífrasis verbales in Spanish, Trennbare Verben in German, and equivalent constructs in other languages as NLP adapter support is added. The domain model uses a `mwe_kind` field (see ADR-0009) rather than language-named entity types. This decision eliminates the need for schema changes when a new language is supported.

## Consequences

### Positive

- The architecture is multi-language by design from day one; adding a new language requires only a new NLP adapter, not schema migrations.
- User targeting is language-inclusive; the product serves any reader studying any language, not just English learners.
- The abstract MWE category (Part c) provides a consistent domain model across languages; English-specific plans (product-vision §10, §12) map cleanly to `mwe_kind: "phrasal_verb"` without special-casing.
- The constitution amendment is a single clean MAJOR bump, not a patchwork of partial generalizations.

### Negative

- Language detection (OQ-2) must be resolved before multi-language corpora can be processed without user disambiguation.
- Per-language NLP library selection (OQ-4) — spaCy supports many languages, but quality varies; a future ADR must govern model selection per language.
- The consent model for translation APIs (OQ-3) must be designed before any cloud translation integration (consistent with ADR-0005 local-first, Art. IV.5).
- Testing surface grows proportionally with the number of supported languages.

## Alternatives considered

- **English-only for MVP, multi-language post-MVP** — Rejected: retrofitting multi-language later requires touching every domain type that currently assumes English-specific naming (e.g., a hard-coded `PhrasalVerb` entity type). The incremental cost of adopting multi-language from day one at the architecture level is essentially zero; the retro-fit cost is high.
- **Generic language-agnostic pipeline with no language-aware MWE modeling** — Rejected: MWE detection and POS quality are fundamentally language-dependent. A fully generic pipeline that treats all languages identically would collapse MWE and POS accuracy to the point where the core product promise — accurate vocabulary extraction — cannot be delivered.
- **Multi-language scope but hard-coded to EN + ES only** — Rejected: an arbitrary two-language ceiling constrains future NLP adapter additions without any architectural benefit. The `mwe_kind` model (Part c) already removes the need for such a ceiling.

## References

- [`docs/constitution.md` preamble (post-amendment, Slice E)](../constitution.md)
- [`docs/product-vision.md` §4, §10, §12 (post-amendment, Slice E)](../product-vision.md)
- [`AGENTS.md §4 — Restricciones del dominio`](../../AGENTS.md#4-restricciones-del-dominio) (post-amendment, Slice E)
- [ADR-0001](0001-monorepo-and-stack.md) — spaCy as replaceable NLP adapter via `LinguisticAnalyzer` port
- [ADR-0005](0005-local-first.md) — Local-first constraint; cloud integrations require consent (OQ-3)
- [ADR-0009](0009-mwe-language-specific-instances.md) — Full treatment of the abstract MWE category and `mwe_kind` field
- [`docs/glossary.md`](../glossary.md) — Expresión multipalabra específica del idioma
- Open questions OQ-2, OQ-3, OQ-4 tracked in `openspec/changes/docs-methodology-overhaul/design.md §9`

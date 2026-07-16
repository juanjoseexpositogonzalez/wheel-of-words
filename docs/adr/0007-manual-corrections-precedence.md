# ADR-0007 — Manual corrections take precedence and survive reprocessing

Status: Accepted

Date: 2026-07-16

## Context

The linguistic model in Wheel Vocabulary is built on an automated NLP pipeline. spaCy (or a future adapter) provides tokenization, lemmatization, POS tagging, and MWE detection. Automated results are useful by default but are not infallible: literary corpora contain domain-specific vocabulary, archaic forms, and proper nouns that NLP models frequently mis-tag.

Constitution Art. V codifies the invariants that govern how manual corrections interact with the pipeline. Two clauses are directly binding here:

- Art. V.8: "Una corrección manual prevalece sobre el resultado automático."
- Art. V.9: "El reprocesamiento no borra silenciosamente correcciones manuales."

AGENTS.md §4 makes the operational rules explicit:

> "Las correcciones manuales prevalecen sobre resultados automáticos."
> "El reprocesamiento nunca debe sobrescribir silenciosamente una corrección manual."

The domain entity `ManualCorrection` (listed in `docs/architecture/overview.md §4`) represents a user-made override for a specific field on a specific `Occurrence`. Without a first-class entity to track these overrides, a reprocessing run has no way to distinguish an original automated result from a value the user intentionally changed.

**The risk without this ADR**: If a new version of spaCy is installed and the corpus is reanalyzed, a naive implementation overwrites all `Occurrence` fields with the new pipeline output. Every manual correction the user made is silently lost. The user discovers the loss only when reviewing vocabulary — with no way to recover their work.

> **Open item OQ-1**: The UX shape of manual correction (day-one interactive editing vs. a deferred correction queue) is not resolved by this ADR. This ADR records only the invariant — manual corrections always win. When the UX is shipped, its design must conform to this constraint. OQ-1 remains open.

## Decision

1. Any `ManualCorrection` entity MUST take precedence over NLP automatic results for the same field on the same `Occurrence`. The automatic value is retained for auditability but is not the effective value when a manual correction exists.

2. A reprocessing run MUST check for existing `ManualCorrection` records before overwriting any field. If a `ManualCorrection` exists for a given (occurrence, field) pair, the reprocessing result for that pair MUST be discarded or stored as a shadow value — never applied as the active value.

3. Provenance metadata MUST be stored for all automatic results: source pipeline identifier, model version, processing date, and confidence score. This enables auditability, conflict detection, and future review tooling.

4. If the `ManualCorrection` model shape changes (e.g., a field is renamed or split), a migration strategy MUST be defined before the shape change is deployed. Silent schema drift that makes existing corrections unreadable is not acceptable.

## Consequences

### Positive

- User corrections are durable across software upgrades and model updates; the system earns trust.
- Corpus quality improves cumulatively: every correction persists across reprocessing cycles, building a correction layer that grows with use.
- Constitution Art. V.8–9 is satisfied without approximation.
- Reprocessing is safe by default — users do not need to re-apply corrections after a model update.

### Negative

- Reprocessing logic is more complex: a correction-check step is required per (occurrence, field) pair before overwriting.
- Repository storage grows over time as both the automatic result (with provenance) and the manual correction are retained.
- If the `ManualCorrection` entity shape evolves, a migration story is required — the data model cannot be changed casually.
- The UI must surface the override state (e.g., "this field was manually corrected on 2026-07-20") so users understand why a value differs from the pipeline output. This is deferred (OQ-1).

## Alternatives considered

- **Last-write-wins (reprocessing overwrites everything)** — Rejected: directly violates Constitution Art. V.9, which explicitly forbids silent reprocessing overwrite of manual corrections. This alternative is constitutionally inadmissible.
- **Manual corrections stored as flags only (boolean `is_corrected`)** — Rejected: a boolean flag records that a correction was made but not what the corrected value is or when it was made. A `ManualCorrection` entity captures the corrected value, the timestamp, and the provenance of the original automatic result that was overridden. The flag-only model cannot support auditability or migration.
- **Manual corrections applied as suggestions pending review (suggestion queue)** — Rejected: this model inverts the trust hierarchy. Constitution Art. V.8 is unconditional — manual corrections prevail. Treating them as suggestions that may or may not be applied contradicts the constitutional invariant.

## References

- [`docs/constitution.md` Art. V.7–9](../constitution.md#artículo-v--integridad-del-modelo-lingüístico)
- [`AGENTS.md §4 — Restricciones del dominio`](../../AGENTS.md#4-restricciones-del-dominio)
- [`docs/glossary.md`](../glossary.md) — Corrección manual, Reprocesamiento, Procedencia
- [`docs/architecture/overview.md §4 — Dominio`](../architecture/overview.md#4-backend) (`ManualCorrection` entity)
- [ADR-0005](0005-local-first.md) — Local-first constraint means corrections are stored locally; same privacy model applies
- [ADR-0006](0006-pos-per-occurrence.md) — POS on Occurrence is the primary field type that manual corrections override

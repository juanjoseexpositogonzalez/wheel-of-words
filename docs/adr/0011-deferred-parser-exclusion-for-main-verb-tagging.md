# ADR-0011 — Deferred: `parser` stays excluded, accepting AUX-for-VERB mistagging on main-verb be/have/do

Status: Accepted

Date: 2026-08-25

## Context

`SpacyLinguisticAnalyzer` (`apps/api/src/wheel_vocabulary/infrastructure/nlp/spacy_analyzer.py`) loads
`en_core_web_sm` with `exclude=_EXCLUDED_PIPES`, where `_EXCLUDED_PIPES = ("parser", "ner", "senter")`
(design §P1/P2). This trims the pipeline to only the components `SPEC-003`'s POS/lemma capability
needs, avoiding the cost of running dependency parsing, named-entity recognition, and sentence
segmentation the product never consumes.

`attribute_ruler` — the component that maps the tagger's fine-grained Penn Treebank tag to the UPOS
this project persists (`REQ-003-002`, `REQ-003-005`) — has a small number of rules keyed on the
syntactic dependency relation (`DEP`), not only on the fine tag. `DEP` is populated exclusively by
`parser`. With `parser` excluded, `DEP` is unset on every token, so those `DEP`-conditioned rules can
structurally never fire, and an earlier, `DEP`-agnostic rule wins unconditionally instead. For the
lexical items `be`/`have`/`do` in their finite forms (`is`, `are`, `was`, `were`, `has`, `have`, `had`,
`do`, `does`, `did`, and contractions), this means the adapter always publishes `AUX`, even when the
word is functioning as a genuine main verb (`"I have a car"`) rather than an auxiliary (`"I have
eaten"`) — a distinction only a syntactic parse can make. spaCy's own full pipeline, with `parser`
included, correctly distinguishes the two; this adapter's reduced pipeline cannot.

This is a linguistic-accuracy defect the project's own risk register already names generically:
`docs/product-vision.md §11` lists "Riesgo lingüístico: Los modelos pueden equivocarse con prosa
literaria," mitigated by "confianza, revisión manual y fixtures de regresión" — `pos_confidence` is
exactly the channel through which this specific mistagging becomes visible to the user (a main-verb
`have`/`do`/`be` still reports a high `pos_confidence` for the tag actually assigned, `VBZ`/`VBP`/etc.,
per `AUX`'s own rule; the number does not flag the ambiguity by itself). Constitution Art. V.3 requires
the category to be "registrada por aparición" — this decision keeps that per-occurrence category
correct for every UPOS except this one narrow main-verb/auxiliary distinction, which is recorded
honestly rather than silently accepted as equivalent to the full pipeline's output.

`docs/product-vision.md §11` also names "Riesgo de rendimiento: Un libro completo puede requerir
procesamiento prolongado," mitigated by "estados de trabajo, progreso, lotes e idempotencia" — the
alternative to this deferral (re-including `parser`) trades directly against that same risk. ADR-0005
establishes local-first processing on the user's own machine as the default, with no stated hardware
floor for a single-user desktop application — a fixed percentage cost increase lands differently on a
constrained machine than on a developer workstation.

## Decision

`_EXCLUDED_PIPES` keeps `parser` excluded. `SpacyLinguisticAnalyzer` continues to publish `AUX` for
every finite form of `be`/`have`/`do`, including when the token is functioning as a main verb rather
than an auxiliary — the adapter's reduced pipeline cannot make that distinction without `parser`, and
no `DEP`-free heuristic reliably can either (`"I have a car"` vs. `"I have eaten"` differ only by a
syntactic relation `parser` computes; approximating it risks a shadow parser reimplementation with its
own, undocumented failure modes — worse than the one, well-understood gap this ADR records).

This gap is measured, not merely acknowledged:

- **Correctness.** Reproduced on 3 short declarative sentences ("She has a cat.", "I do my homework.",
  "There is a problem."): 3 of 15 tokens (`has`/`do`/`is`) differ between this adapter's reduced
  pipeline and the full model, each with a `pos_confidence` of 0.998–0.9999 for the (wrong, relative to
  the full pipeline) `AUX` tag — the number does not signal the ambiguity.
- **Cost of the alternative.** Re-including `parser` (`tagger`/`attribute_ruler`/`lemmatizer`
  unchanged; `ner`/`senter` still excluded), median of 5 isolated-subprocess runs on a 10,000-token
  synthetic `Doc`: **wall time +30%** (1.09s → 1.42s) and **peak RSS +19%** at 30,000 tokens (652 MB →
  777 MB, measured via `resource.getrusage(...).ru_maxrss`). This lands on top of the already-tracked,
  already-deferred ~2.3 GB at 300k tokens single-`Doc` memory footprint (`product-vision.md §11`,
  `tasks.md §Known debt` — explicitly out of scope for this decision).

The module docstring in `spacy_analyzer.py` (§P2) and the self-check docstrings in the same file MUST
NOT claim this exclusion has no linguistic effect — an earlier docstring omitted that `attribute_ruler`
reads `DEP` at all, which is corrected regardless of this deferral standing.

## Consequences

### Positive

- Avoids a measured +30% wall-time / +19% peak-RSS regression on top of an already-large, already-
  accepted memory budget, for a capability (`parser`'s full dependency graph) this product does not
  otherwise consume.
- The gap is precisely bounded and documented — a future contributor does not need to rediscover it by
  reading rule tables; the 3 mis-tagged lexical classes (`be`/`have`/`do` finite forms) are enumerated
  here.
- `pos_confidence`'s honest semantics (design.md §P1, corrected under Judgment Day round 2 R4) mean the
  UI never overstates certainty for a mistagged token — the number is a real posterior for the
  (possibly wrong) tag assigned, not a fabricated confidence in the correct UPOS.
- Keeps the reduced-pipeline self-check (`_run_self_check`) meaningful: both legs compare the SAME
  reduced pipeline against itself, so this decision does not need to be re-litigated every time that
  check runs (see its own docstring for what it does and does not verify).

### Negative

- A real, measured linguistic-accuracy defect ships: main-verb `be`/`have`/`do` is tagged `AUX` instead
  of `VERB`, disagreeing with what the same pinned model's own full pipeline would report for the
  identical input.
- The defect is invisible to `pos_confidence` alone — a user cannot distinguish "high confidence,
  correct tag" from "high confidence, tag correct only because `parser` was excluded" without external
  knowledge of this ADR.
- Every occurrence of a finite `be`/`have`/`do` form carries this risk, not only rare sentence
  constructions — these are among the highest-frequency lexical items in English prose.

## Alternatives considered

- **Re-include `parser`.** Rejected for now: measured +30% wall time / +19% peak RSS is a real cost for
  a single-user desktop app with no stated hardware floor (ADR-0005), for a capability (full dependency
  parsing) nothing else in `SPEC-003` consumes. Revisit trigger below keeps this open, not foreclosed.
- **A `DEP`-free heuristic to approximate the parser's distinction** (e.g., a fixed lexical/positional
  rule for `have`/`do`/`be`). Rejected: `"I have a car"` vs. `"I have eaten"` differ only by a syntactic
  relation; a heuristic strong enough to resolve that reliably is a shadow parser reimplementation,
  with its own undocumented failure modes and no shared test/maintenance surface with spaCy's own
  `parser`. Assessed and rejected as a mechanical fix, not merely undesirable.
- **Silently accept `AUX` as equivalent to `VERB` for this capability's purposes and say nothing.**
  Rejected outright: `docs/decisions-log.md` line 14 requires `Ref` to point to an authoritative
  artifact and forbids silently skipping a known defect; this ADR exists specifically so the deferral
  is a recorded decision, not an unrecorded gap.

## Revisit trigger

Revisit this decision when either becomes true:

1. A product decision determines that main-verb `be`/`have`/`do` tagging accuracy is worth the measured
   throughput/memory cost for the target user base, or
2. spaCy exposes a narrower `DEP`-only reduced parse (a `parser` mode that populates `DEP` without the
   full dependency-graph cost this ADR measured) — closing the accuracy gap without paying the full
   `parser` cost.

## References

- [`docs/constitution.md` Art. V.3](../constitution.md#artículo-v--integridad-del-modelo-lingüístico) — "La categoría se registra por aparición y se agrega posteriormente"
- [`docs/product-vision.md` §11 — Riesgos y mitigaciones](../product-vision.md#11-riesgos-y-mitigaciones) — riesgo lingüístico and riesgo de rendimiento
- [ADR-0005](0005-local-first.md) — local-first processing; no stated hardware floor for a single-user desktop app
- [ADR-0006](0006-pos-per-occurrence.md) — POS assigned per occurrence, the granularity at which this gap is measured and disclosed
- `openspec/changes/lemmatization-pos/design.md` §P1 (`pos_confidence` semantics, corrected under Judgment Day round 2 R4), §P2 (`_EXCLUDED_PIPES` rationale)
- `apps/api/src/wheel_vocabulary/infrastructure/nlp/spacy_analyzer.py` (`_EXCLUDED_PIPES`, `_assert_decomposed_path_agrees_with_the_plain_pipeline`)
- [`docs/decisions-log.md`](../decisions-log.md) — 2026-08-25 entry, superseded by this ADR as the authoritative `Ref`

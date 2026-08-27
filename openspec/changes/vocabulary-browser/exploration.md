# Exploration: Vocabulary Browser (005-vocabulary-browser)

Roadmap item 5 (`docs/product-vision.md` §12, "Navegador de vocabulario"). Anchor scope, fixed by
the user: group annotation occurrences by lemma, filter by POS. This document investigates fit with
the shipped architecture and surfaces what the proposal phase must decide. It does not redesign the
product shape.

**Numbering**: this change is `005-vocabulary-browser`. `SPEC-004` is reserved for the manual-correction
write path (`openspec/specs/003-lemmatization-pos/spec.md` R6, line 185; `docs/release-notes.md`
lines 47, 55, 60). This exploration does not claim 004 and does not propose folding manual
corrections into this change.

## Current State

### Data model (after SPEC-003)

Four tables, defined in `apps/api/src/wheel_vocabulary/infrastructure/persistence/models.py` and
created by `apps/api/migrations/versions/0003_annotation.py`:

- `book` (`models.py:33-56`) — one row per import. `token_count`, no `lemma`/`pos` fields.
- `occurrence` (`models.py:59-90`) — one row per token. Columns relevant here:
  - `book_id` (FK, `ondelete="CASCADE"`)
  - `raw_text`, `normalized_text` (from SPEC-002, unrelated to lemma/POS)
  - `position` (zero-based token index)
  - `pos: str | None` (`models.py:84`) — the *automatic* UPOS tag, `NULL` until annotated
  - `lemma: str | None` (`models.py:88`, `Text` column) — the *automatic* lemma, `NULL` until annotated
  - Only index: `ix_occurrence_book_norm_raw` on `(book_id, normalized_text, raw_text)` (`models.py:72-74`).
    **There is no index on `lemma` or `pos`, alone or combined with `book_id`.**
- `annotation_provenance` (`models.py:93-124`) — one row per occurrence (`occurrence_id` UNIQUE),
  holding `source`, `model_name`, `model_version`, `language`, `processed_at`, `pos_confidence`,
  `lemma_confidence`. Deleted and re-inserted on every annotation run, never updated in place.
- `manual_correction` (`models.py:127-152`) — `(occurrence_id, field)` UNIQUE, `field ∈ {"pos","lemma"}`,
  `corrected_value`. Schema-only in this codebase: nothing writes to it yet (SPEC-004).

`occurrence.pos` and `occurrence.lemma` are the **automatic** values only. The **effective**
(precedence-resolved) value is computed at read time, never stored — see below.

### Read path today

`GET /api/v1/imports/{id}/annotation` (`apps/api/src/wheel_vocabulary/api/routes/annotation.py:120-131`,
handler `read_annotation`) calls `SqlAlchemyAnnotationReadRepository.read(book_id)`
(`apps/api/src/wheel_vocabulary/infrastructure/persistence/annotation_repository.py:106-136`). That
method:

1. Confirms the book exists (`None` → 404 upstream).
2. Runs one `SELECT` joining `occurrence` to `annotation_provenance` (`LEFT OUTER JOIN`), ordered by
   `position` — **no `GROUP BY`, one row per occurrence** (lines 113-133).
3. Runs one additional batched `SELECT` against `manual_correction`, chunked at 10,000 ids
   (`_read_corrections`, lines 138-160), matching the pattern already used by
   `book_repository.py::_insert_occurrences`.
4. Builds one `AnnotatedOccurrence` per row (`annotation_repository.py:59-97`), whose `__post_init__`
   applies `resolve_effective` (precedence: manual correction wins, else automatic value) to produce
   `effective_pos`/`pos_origin` and `lemma`/`lemma_origin`. This is where SPEC-003's read-time
   precedence rule (§2.5) lives — in pure Python, not SQL.

The route wraps that list into `AnnotationResultResponse` (`apps/api/src/wheel_vocabulary/api/dtos/annotation.py:84-91`):
`{ id, provenance, occurrences: AnnotationOccurrenceResponse[] }`, one entry per occurrence,
position-ordered.

**This existing repository method cannot be reused as-is for a grouped view.** It returns
one-row-per-occurrence with pagination absent — a 688k-occurrence book (see Scale below) would
serialize 688k JSON objects to answer "give me the lemma groups." A grouped view needs either a new
repository method issuing its own aggregate query, or a new application-layer step that consumes
`read()`'s output and groups it in Python. Both are real options (see Approaches).

### Frontend today

- `apps/web/src/types/annotation.ts` — `AnnotatedOccurrence` interface mirrors the DTO one-to-one:
  `position`, `raw_text`, `pos`, `pos_origin`, `automatic_pos`, `pos_confidence`, `lemma`,
  `lemma_origin`, `automatic_lemma`, `lemma_confidence`.
- `apps/web/src/api/annotation.ts` — `postAnnotation(importId)` and `getAnnotation(importId)`, both
  plain `fetch` wrappers with no query parameters (no pagination, no filter, no group-by argument
  exists on the wire today).
- `apps/web/src/components/AnnotationTable.tsx` — renders `result.occurrences` as a flat table, one
  `<tr>` per occurrence, in server order. No grouping, no filtering, no sorting client-side. The
  UPOS→Spanish label map (`UPOS_LABELS`, lines 37-55) is presentational-only, and the component
  docstring is explicit that "This module performs no lemmatization, tagging, normalization, or
  precedence resolution" (lines 8-12) — every value arrives pre-computed from the API.

A browser view reuses: the `AnnotatedOccurrence`/`AnnotationResult` type shapes as a base (extended,
not replaced), the `UPOS_LABELS` map or an equivalent for POS display, and the existing fetch-wrapper
pattern in `api/annotation.ts`. It adds: a new endpoint or query parameters, new response DTOs shaped
around groups rather than occurrences, and new frontend types/components for the grouped view and the
POS filter control.

### Existing SQL grouping precedent

`book_repository.py::frequency_pairs` (`apps/api/src/wheel_vocabulary/infrastructure/persistence/book_repository.py:94-114`)
already does `SELECT raw_text, normalized_text, count() ... GROUP BY raw_text, normalized_text` for
SPEC-002's frequency table, and `models.py:68-71`'s comment states that index exists specifically
to serve that `GROUP BY` as a covering, ordered index scan with no sort. This is the one place in the
codebase that already groups occurrences server-side — a template for how a lemma group-by query
would be shaped, but its covering index does not extend to `lemma`.

## Constraints Inherited From SPEC-003

Binding on this change (`openspec/specs/003-lemmatization-pos/spec.md`):

| ID | Rule | Effect on this change |
|----|------|------------------------|
| **C6** (line 132) | "In this capability confidence is **informational only**. No filter, sort, threshold, warning, block, or automatic re-run MAY key off it." | **A browser that sorts or filters lemma groups by confidence, or that displays a group differently based on an aggregate confidence score, violates the shipped baseline.** Confidence may be *shown* per occurrence inside a group (as `AnnotationTable.tsx` already does) but MUST NOT drive group ordering, group visibility, a confidence threshold control, or a "low-confidence" visual treatment. |
| **R6** (line 185) | "No code path in this capability writes a `ManualCorrection` row." Manual-correction write UX is SPEC-004. | This change MUST NOT add a write path for corrections, even incidentally (e.g., an inline "fix this lemma" affordance in the browser). Read-time precedence resolution (already computed by `AnnotatedOccurrence`) may and should be reused/displayed; writing a correction is out of scope. |
| **P5** (§2.2) | POS is recorded per occurrence. No entity may carry a global/aggregate POS field. Aggregate POS distributions are derived on query, never stored. | A "POS of this lemma" concept cannot be a stored column. Any per-lemma POS view must be computed at query time from the occurrence stream — this directly shapes the grouping-semantics question below. |
| **L6** (§2.1) | "The lemma is recorded per occurrence, never per normalized form and never per book." (`saw` is `see` VERB in one sentence, `saw` NOUN in another.) | Confirms occurrence-level granularity is the only source of truth; a lemma-level table/cache would need to be a derived, on-query view, not a new persisted entity, unless a future migration is proposed and justified separately. |
| **S1-S4** (§2.6) | Annotation is a separate step from import; the browser reads whatever has been annotated so far. | The browser must handle the pre-annotation state gracefully: every occurrence has `pos = NULL`, `lemma = NULL`. `GET .../annotation` already returns this state today (`read_annotation`'s docstring, `annotation.py:126-130`) — "valid before any POST has ever run." |
| REQ-002-011 (deletion) | Deletion is permanent, no tombstone. | A book/import deleted via `DeleteImport` removes its occurrences; the browser has nothing to reconcile beyond the existing 404-on-unknown-book behavior already implemented (`read()` returns `None` for unknown `book_id`). |

## ADR-0006 — Why Grouping "by Lemma" Is Not a Single Well-Defined Operation

`docs/adr/0006-pos-per-occurrence.md` establishes: POS belongs to `Occurrence`, not to `Lexeme`/lemma.
The worked example in the ADR is exactly the ambiguity this feature runs into: "run" appears as VERB
in one sentence and NOUN in another. **The ADR explicitly rejects a single global POS per lemma** —
"Rejected: Constitution Art. V.2 explicitly states 'Un lema puede tener múltiples categorías
gramaticales.' A single-POS-per-lemma model cannot represent this."

The ADR does anticipate this feature by name: its Positive Consequences list "Supports future
features such as POS-filtered vocabulary queries." It does not, however, specify what a "lemma group"
means when POS varies within it — that decision was deliberately deferred.

### The concrete ambiguity

Given the occurrence stream `[("run", VERB), ("run", VERB), ("run", NOUN)]` for lemma `run`, does
"grouping by lemma" produce:

- **One group** `run` with 3 occurrences and a POS breakdown `{VERB: 2, NOUN: 1}`, or
- **Two groups**, `run (VERB)` with 2 occurrences and `run (NOUN)` with 1, because POS is the finer
  discriminator ADR-0006 protects?

The user's stated scope ("group by lemma, filter by POS") is compatible with either reading:
"filter by POS" could mean *filter which occurrences show inside a lemma group* (one-group reading)
or *filter which lemma+POS groups appear at all* (two-group reading). Both are legitimate
interpretations of the anchor and the proposal phase must pick one — this is not something
exploration can resolve on the user's behalf, per the constraint that product scope was already
decided and should not be re-litigated, but the *mechanics* of that scope need a decision.

## Approaches — Grouping Semantics

### Option 1: Group by lemma only; POS filter narrows occurrences within a group

Each group's key is the effective `lemma` alone (`NULL` lemma is its own group, or excluded —
another open question). A group shows every occurrence sharing that lemma, spanning POS values. The
POS filter, when applied, filters which *occurrences* are shown/counted inside the still-lemma-keyed
groups (or hides groups with zero occurrences at the selected POS).

- Pros: Matches "one lemma = one dictionary entry" intuition, which is closest to how a vocabulary
  learner mentally models a word. Single `GROUP BY lemma` in SQL, straightforward frequency count.
- Cons: A group can mix wildly different meanings (a homograph group is confusing to a learner —
  "run" the VERB and "run" the NOUN are different vocabulary items to study). Requires a secondary
  aggregation step to show the POS breakdown per group, since UPOS is not a group key.
- Effort: Low.

### Option 2: Group by (lemma, POS) pair — one group per distinct combination

Each group's key is `(lemma, effective_pos)`. `run (VERB)` and `run (NOUN)` are two separate rows in
the browser. The POS filter narrows which groups are shown, a direct `WHERE effective_pos = ?`
equivalent.

- Pros: Directly matches ADR-0006's own framing — POS is per-occurrence, and this makes the
  browser's unit of study exactly the entity ADR-0006 says is real (`(lemma, POS)`, not bare
  lemma). Simple `GROUP BY lemma, pos` in SQL. The POS filter becomes a trivial predicate, no
  secondary logic needed.
- Cons: A learner scanning the list sees `run` twice with no visual link between the two rows unless
  the UI explicitly re-groups them for display. `NULL` POS (pre-annotation or an occurrence the
  analyzer didn't tag) needs an explicit bucket, visible as its own row.
- Effort: Low — this is structurally the same query shape as `frequency_pairs` in
  `book_repository.py:94-114`, just swapping the group-by columns.

### Option 3: Hierarchical — lemma groups containing a POS breakdown, POS filter as a facet

Same top-level grouping as Option 1 (by lemma), but the API/DB layer additionally returns, per
group, a POS-count breakdown (`{VERB: 2, NOUN: 1}`), and the POS filter is a facet that both narrows
visible groups (hide `run` if the user filters to `ADJ` and `run` has zero `ADJ` occurrences) and
narrows the occurrence list *within* a group when expanded.

- Pros: Most faithful to "group by lemma, filter by POS" read literally, and gives the richest UI
  affordance (a facet, matching how vocabulary-app users expect filters to behave).
  Positions the feature for the roadmap item 6 (proper nouns) and item 7 (multi-word expressions)
  that will also need per-lemma faceting.
- Cons: Highest implementation cost — two levels of aggregation (`GROUP BY lemma` for the group list,
  a second `GROUP BY lemma, pos` for breakdowns, or one query with conditional aggregation). Requires
  new DTOs on both sides for the two-level shape. Largest vertical slice of the three options.
- Effort: Medium.

**No recommendation is stated here.** All three satisfy "group by lemma, filter by POS" under a
different reading of what those two words mean when POS varies within a lemma; picking one is a
proposal-phase decision, not an exploration-phase one, because it determines the DTO shape, the SQL
query shape, and the smallest deliverable slice.

## Scale and Performance

- SPEC-002's size ceiling is `MAX_IMPORT_SIZE_BYTES = 4194304` (4 MiB), quantified at **~688,000
  occurrence rows** and ~3.4s of synchronous import work (`openspec/specs/002-text-import/spec.md`
  lines 213-215, 834). This is the realistic upper bound for one book's occurrence count today.
- The only occurrence index, `ix_occurrence_book_norm_raw` (`models.py:72-74`), does not cover
  `lemma` or `pos`. A `GROUP BY lemma` (or `lemma, pos`) query at 688k rows scoped to one `book_id`
  would currently require SQLite to build a temporary B-tree for the aggregation (no covering index
  to serve it as an ordered scan) — the same situation the code comment at `models.py:68-71`
  describes solving for `frequency_pairs`'s grouping key, but not yet solved for `lemma`/`pos`.
  Whether that gap needs a new index is a design-phase decision informed by a benchmark, mirroring
  how SPEC-002/003 handled scale decisions (`test_import_bench.py` marks this pattern explicitly:
  `@pytest.mark.bench`, not part of default CI).
- Grouping belongs in SQL, not in the application layer or the frontend, for the same reason
  `frequency_pairs` groups in SQL rather than in Python: at 688k rows, transferring every occurrence
  to Python (or to the browser) merely to group it client-side reproduces exactly the scale problem
  SPEC-002's design already solved once. The read-time precedence resolution (manual correction vs.
  automatic value) currently happens in Python (`AnnotatedOccurrence.__post_init__`) precisely
  because that step is *not* aggregatable in SQL without duplicating `resolve_effective`'s logic in
  a SQL `CASE` expression — that duplication risk is itself a design-phase question: does a grouped
  query resolve precedence before or after `GROUP BY`? Resolving after `GROUP BY` (i.e., grouping on
  the raw `occurrence.lemma` column) would silently ignore manual corrections in the browser, which
  is a correctness gap the design phase must close explicitly, not by omission.

## Vertical Slice Boundary

Per Constitution Art. III, the smallest slice producing observable user value: a read-only endpoint
(`GET /api/v1/imports/{id}/vocabulary` or similar — exact route naming is a proposal-phase call) that
returns lemma groups with occurrence counts, plus a minimal frontend list view, with the POS filter
as a **second** vertical slice layered on top once the group shape is settled. This mirrors how
SPEC-002 shipped `frequency_pairs`/`FrequencyTable` before SPEC-003 added annotation on top, and how
SPEC-003 shipped read-then-write as two ordered concerns (§2.6). Deferring the POS filter to slice 2
is an option to raise in the proposal phase, not a decision made here.

## Open Questions for the Proposal Phase

1. **Grouping semantics** — which of Options 1/2/3 above (or a variant) implements "group by lemma,
   filter by POS"? This is the single highest-impact decision; it determines the DTO shape and the
   SQL query shape.
2. **`NULL` lemma handling** — an unannotated occurrence has `lemma = NULL` (and, per L4, so does a
   whitespace-only lemma the analyzer emitted). Does the browser show an "unannotated" group, exclude
   `NULL`-lemma occurrences entirely, or something else? SPEC-003's own read path (`read_annotation`)
   is explicit that the pre-annotation state (`provenance: null`, everything `NULL`) is a valid,
   documented state, not an error — the browser must handle it, but *how* is undecided.
3. **Manual-correction precedence in aggregate queries** — does grouping key on the automatic
   `occurrence.lemma`/`.pos` columns, or on the precedence-resolved effective value (which requires
   joining `manual_correction`, currently only done in Python)? Grouping on the raw column would
   silently produce wrong groups for any occurrence with a manual correction, once SPEC-004 ships a
   write path — even though SPEC-004 hasn't shipped yet, this change should not bake in an assumption
   that has to be revisited the moment it does.
4. **Pagination / result size** — a lemma-group list is much smaller than an occurrence list (distinct
   lemma count, not occurrence count), but is still unbounded at scale. Does the endpoint need
   pagination from slice 1, or is "all groups for one book" small enough to return whole? No existing
   endpoint in this codebase paginates; `frequency_pairs` returns everything. This needs a bound
   before commit, not a `TODO`.
5. **Indexing** — does `lemma`/`pos` need a new index (and thus a new Alembic migration) to serve the
   grouping query at the 688k-row ceiling without a temp B-tree, or is unindexed aggregation fast
   enough at that scale to defer? This needs a benchmark, not a guess, mirroring
   `test_import_bench.py`'s existing pattern.
6. **Route/contract shape** — new endpoint vs. new query parameters on the existing
   `GET .../annotation` route. A new endpoint keeps `annotation.v1.json`'s existing contract
   byte-identical (a constraint `spec-003-harden-guards-and-claims` treats as load-bearing state to
   preserve); reusing the existing route risks widening a contract that hardening work just locked
   down.

## Affected Areas

- `apps/api/src/wheel_vocabulary/infrastructure/persistence/annotation_repository.py` — new read
  method or a sibling repository for the grouped query; existing `read()`/`AnnotatedOccurrence` stay
  untouched (they still serve `AnnotationTable.tsx`'s per-occurrence view).
- `apps/api/src/wheel_vocabulary/infrastructure/persistence/models.py` — possible new index on
  `occurrence(book_id, lemma)` or `(book_id, lemma, pos)`, pending the benchmark in Open Question 5.
- New Alembic migration if an index is added (would be `0004_*`, since `0003_annotation` is the last
  one and `004` as a *capability* number is reserved, not the migration numbering — migration and
  capability numbers are independent sequences in this repo).
- `apps/api/src/wheel_vocabulary/application/annotation/` — a new use case or an extension, depending
  on whether grouping logic lives in the repository (SQL) or a use case orchestrating it.
- `apps/api/src/wheel_vocabulary/api/routes/annotation.py` and `api/dtos/annotation.py` — new route
  and DTOs, or new query parameters, per Open Question 6.
- `apps/web/src/api/annotation.ts`, `apps/web/src/types/annotation.ts` — new client function and
  types for the grouped shape.
- `apps/web/src/components/AnnotationTable.tsx` — untouched; a new component is needed for the
  grouped view (reusing `UPOS_LABELS` or an equivalent).

## Ready for Proposal

Yes, with the six open questions above carried into `sdd-propose` explicitly. The proposal phase
should resolve at minimum Open Questions 1 (grouping semantics) and 3 (precedence-in-aggregation)
before scoping requirements, since both change the shape of every requirement that follows. Questions
4-6 can be resolved as part of the technical design if the proposal defers them with a stated
default.

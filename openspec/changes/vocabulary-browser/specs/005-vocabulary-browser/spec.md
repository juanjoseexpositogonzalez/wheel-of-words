# Specification for 005-vocabulary-browser

This is the specification for capability `005-vocabulary-browser`: a read-only grouped vocabulary
view over an import's annotated occurrences — `(lemma, POS)` study units with occurrence counts,
narrowable by POS, computed over precedence-resolved effective values.

It is a **new capability**, so the requirements below (`REQ-005-001` … `REQ-005-011`) are a full
specification, not a delta. **No `MODIFIED` delta is emitted against any existing capability.** This
capability adds a new endpoint and a new frontend component; it changes no shipped route, no shipped
contract, and no shipped table column. See §5 `DEC-3`.

Section references of the form `§2.x` refer to sections of this document. References prefixed
`SPEC-003` refer to `openspec/specs/003-lemmatization-pos/spec.md`; references prefixed `SPEC-002`
refer to `openspec/specs/002-text-import/spec.md`.

## 1. Metadata

| Field | Value |
|-------|-------|
| Capability | `005-vocabulary-browser` |
| Requirement prefix | `REQ-005-###` |
| Acceptance prefix | `AC-005-##` |
| Roadmap item | 5 — Navegador de vocabulario (`docs/product-vision.md:152`) |
| Governing constitution | v2.0.0 (`docs/constitution.md:3`) |
| Governing ADRs | 0002, 0005, 0006, 0007, 0008, 0010 |
| Language | English (methodology artifact, ADR-0010). Product docs stay Spanish |
| Test runner | `cd apps/api && uv run pytest` — strict TDD, zero-warning `filterwarnings` gate |
| Depends on | `003-lemmatization-pos` (shipped): `occurrence.lemma`, `occurrence.pos`, `annotation_provenance`, `manual_correction` (schema only, no writer) |
| Endpoint | `GET /api/v1/imports/{id}/vocabulary` (proposal Q6) |
| State to preserve | `annotation.v1.json` byte-identical; `import.v1.json` byte-identical at the SHA-256 recorded at `SPEC-003 spec.md:37`; `GET`/`POST /api/v1/imports/{id}/annotation` behaviour, response body and error codes unchanged; `SqlAlchemyAnnotationReadRepository.read` (`annotation_repository.py:106`) unchanged; `apps/web/src/components/AnnotationTable.tsx` rendering, behaviour and tests unchanged — its label-map definition site MAY move (§5 `AMB-8`) |
| Slice split | `REQ-005-006` (POS filter) is slice 2; every other requirement is slice 1. The capability is **not complete** until slice 2 ships — see §6 PV-3 |

**What this capability is.** The one shipped read path over annotations
(`SqlAlchemyAnnotationReadRepository.read`, `annotation_repository.py:106-136`) issues a `SELECT`
with no `GROUP BY` and returns one object per occurrence, ordered by `position`. At SPEC-002's
quantified ceiling of ~688,000 occurrence rows (`SPEC-002 spec.md:213-215`) that path serializes
688,000 objects to answer "what are the study units". This capability adds a second, aggregate read
path and a view over it.

**What this capability is not.** It writes nothing. It stores nothing new beyond an optional
additive index. It adds no correction affordance and no confidence-driven behaviour. §7 enumerates
the non-additions in full.

---

## 2. Vocabulary contract (normative)

Everything in this section is normative and binding on the domain, the application, the persistence
layer, the API and the frontend.

### 2.1 The group — key, count, and stability

A **group** is a derived, non-persisted view over the occurrences of one `book_id`.

| # | Rule | Reason |
|---|------|--------|
| G1 | The group key SHALL be the ordered pair `(effective lemma, effective POS)` for that occurrence, as §2.2 defines *effective*. Neither half alone is a key | ADR-0006 rejects a single global POS per lemma: `run` VERB and `run` NOUN are distinct study items. Keying on lemma alone merges homographs and leaves "filter by POS" with no well-defined subject (proposal Decision A) |
| G2 | A group's count SHALL be the number of occurrences of that `book_id` whose effective pair equals the key. It is a count of occurrences, never of distinct textual forms and never of distinct normalized forms | `raw_text` and `normalized_text` answer SPEC-002's question, not this one. Counting them here would report a different number under the same name |
| G3 | A pair with zero occurrences MUST NOT appear as a group. The response enumerates observed pairs, never the Cartesian product of observed lemmas and the 17-tag set | An enumerated-but-empty group is a claim about a study unit that does not exist in this corpus |
| G4 | The group set SHALL be scoped to one `book_id`. An occurrence of another import MUST NOT contribute to any count | |
| G5 | Two identical requests against unchanged data SHALL return the same groups in the same order (Art. VI.2). The ordering key MUST NOT be a confidence value (§2.4 K1) | An unordered aggregate makes the list view reshuffle between renders and makes every acceptance scenario a set comparison. The specific sort key is a design decision — see §5 `AMB-1` |
| G6 | A group SHALL carry no aggregate provenance, no aggregate confidence, and no aggregate origin marker | One group spans occurrences from one annotation run, but a per-group provenance field would be a new claim this capability does not compute. Per-occurrence provenance stays where SPEC-003 put it |

### 2.2 Effective values — grouping resolves precedence before it aggregates

The effective value of a field is the one SPEC-003 §2.5 already defines:

```
effective(occurrence, field) =
    ManualCorrection[occurrence, field].corrected_value   if such a row exists
    Occurrence.<field>                                    otherwise   (MAY be NULL)
```

where `field ∈ {pos, lemma}`. The shipped implementation is `resolve_effective`
(`apps/api/src/wheel_vocabulary/domain/annotation.py:132`), applied per occurrence inside
`AnnotatedOccurrence.__post_init__` (`annotation_repository.py:91-97`).

| # | Rule | Reason |
|---|------|--------|
| E1 | Grouping SHALL key on the effective lemma and the effective POS, for every occurrence, on every request | SPEC-003 §2.5 R1: precedence applies on every read of an effective value, without exception. A grouped read is a read |
| E2 | Grouping on the raw `occurrence.lemma` or raw `occurrence.pos` column is **FORBIDDEN** | Art. V.8–9 and ADR-0007 require a manual correction to win. Raw-column grouping puts a corrected occurrence in the group its superseded automatic value names — the correction is still stored, still returned by `GET .../annotation`, and silently absent from the browser. That defect would be introduced today and observable only after SPEC-004 ships a writer (proposal Decision B) |
| E3 | Whatever resolves precedence for the aggregate MUST agree with `resolve_effective`, value for value, for every `(automatic, corrected)` input pair. A second precedence implementation with different semantics is **FORBIDDEN** | SPEC-003 built precedence as a constructor rather than a branch precisely so a missing check would stop being a bug one can write. A divergent SQL `CASE` re-introduces the branch |
| E4 | This capability SHALL read `manual_correction` and SHALL NOT write it (§2.5 N2). Reading it is what E1 requires; writing it is SPEC-004 | SPEC-003 R6. The read/write distinction is load-bearing here and is the one place this capability's guard differs from the annotation write path's — see `REQ-005-008` |
| E5 | The effective value MAY be `NULL`. `NULL` is a group key half, never a reason to drop an occurrence (§2.3) | |

### 2.3 Absent values are visible buckets, never silent drops

| # | Rule | Reason |
|---|------|--------|
| N1 | An occurrence whose effective lemma is `NULL` SHALL belong to a group whose key is `(NULL, effective POS)`, and that group MUST be present in the response | A pre-annotation import is a valid documented state (SPEC-003 §2.6 S1–S4; `read_annotation`'s docstring, `api/routes/annotation.py:126-131`). Dropping those occurrences would report a book as having no vocabulary when it has 688,000 unannotated tokens |
| N2 | An occurrence whose effective POS is `NULL` SHALL belong to a group whose key is `(effective lemma, NULL)`, and that group MUST be present in the response | The analyzer MAY emit a lemma and no tag. Hiding that group would make the counts fail to sum to the token count with no stated reason |
| N3 | An absent key half MUST be transmitted as JSON `null`. It MUST NOT be omitted from the key, MUST NOT be the empty string, and MUST NOT be a sentinel string — in particular MUST NOT be `X`, which is a real UPOS tag meaning "the model could not classify this" | SPEC-003 §2.3 C4's rule for confidence applies to the same failure mode here: collapsing "not annotated" into a legitimate value destroys the one signal the state exists to carry. `X` and `NULL` are different facts |
| N4 | The view SHALL render each `NULL` bucket with an explicit label distinguishing it from a tagged or lemmatized group, readable as text without colour (Art. IX.4) | |
| N5 | Consequently: an import whose occurrences are all unannotated SHALL return exactly one group, keyed `(NULL, NULL)`, whose count equals the import's occurrence count | This is the falsifiable form of N1+N2. It is the scenario a silent-drop implementation fails |

### 2.4 Confidence is not an input to anything here

SPEC-003 C6 (`spec.md:132`) states that in that capability confidence is informational only and that
no filter, sort, threshold, warning, block, or automatic re-run may key off it. That prohibition
binds this capability unchanged, and is restated here because a browser is exactly where it would be
violated first.

| # | Rule | Reason |
|---|------|--------|
| K1 | No group key, count, ordering, default ordering, filter, threshold, visibility rule, badge, warning, or visual treatment MAY read `pos_confidence` or `lemma_confidence` | SPEC-003 C6. Acting on low confidence requires a correction path, and that path is SPEC-004 |
| K2 | A group MUST NOT carry an aggregate confidence of any kind — no minimum, maximum, mean, sum, or count-below-threshold | An aggregate confidence is a fabricated value SPEC-003 C3 forbids computing, wearing a group's name |
| K3 | The endpoint MUST NOT accept a confidence-valued request parameter | A parameter that exists is a behaviour that keys off confidence, whether or not the current client sends it |
| K4 | Confidence MAY be displayed per occurrence wherever an individual occurrence is shown, unchanged from `AnnotationTable.tsx` | SPEC-003 C5 requires it there. K1–K3 forbid acting on it, not showing it |

### 2.5 Nothing is stored

| # | Rule | Reason |
|---|------|--------|
| P1 | No entity introduced by this capability MAY carry a stored aggregate POS, a stored aggregate lemma, or a persisted `(lemma, POS)` group row. Groups are computed at query time on every request | SPEC-003 §2.2 P5 and §2.1 L6, ADR-0006, Art. V.2–3. A stored group would be a cache of an effective value, stale the moment a correction is written |
| P2 | No column of `book`, `occurrence`, `annotation_provenance` or `manual_correction` MAY be added, dropped, renamed, retyped, or made non-nullable by this capability | Rollback isolation (proposal §Rollback Plan) |
| P3 | An **additive, reversible index** MAY be added if the design's benchmark shows one is needed. An index is not a stored aggregate and does not violate P1. Its migration's `downgrade()` MUST return the schema to the SPEC-003 baseline (Art. VI.4) | Proposal Q5 gates the index on a benchmark, not on assumption. The only occurrence index today, `ix_occurrence_book_norm_raw` (`models.py:72-74`), covers neither `lemma` nor `pos` |

---

## 3. Requirements

### Requirement: REQ-005-001 — The study unit is the `(lemma, POS)` pair with an occurrence count

The API SHALL expose, for one import, the set of distinct `(effective lemma, effective POS)` pairs
observed among that import's occurrences, each with the number of occurrences carrying that pair
(§2.1 G1–G4). One textual lemma appearing under two POS tags MUST produce two groups, never one
merged group and never a single group with a chosen tag. The response ordering MUST be stable across
identical requests (G5). No group MAY carry aggregate provenance, aggregate confidence, or an
aggregate origin marker (G6).

Acceptance: **AC-005-01** — Given an annotated import whose occurrences include `run` tagged `VERB`
twice and `run` tagged `NOUN` once, when the vocabulary read runs, then the response contains exactly
two groups for lemma `run` — `(run, VERB)` with count `2` and `(run, NOUN)` with count `1` — and no
group merging them; and given the same import read twice with no intervening write, then the two
responses are equal including order; and given any returned group, when its properties are
enumerated, then none is a confidence, a provenance identity, or an origin marker.

#### Scenario: A homograph produces two groups, not one

- GIVEN an import with `run` (VERB) twice and `run` (NOUN) once
- WHEN the vocabulary read runs
- THEN `(run, VERB)` is returned with count `2` and `(run, NOUN)` with count `1`
- AND no group keyed on lemma alone is returned

#### Scenario: Counts are occurrence counts

- GIVEN an import where `ran` and `running` both resolve to lemma `run` with POS `VERB`
- WHEN the vocabulary read runs
- THEN one group `(run, VERB)` is returned whose count is the number of those occurrences
- AND the distinct `raw_text` count is not reported as the group count

#### Scenario: The result is stable across identical requests

- GIVEN an import and no intervening write
- WHEN the vocabulary read runs twice
- THEN the two responses are equal, including group order

#### Scenario: A group carries no aggregate confidence or provenance

- GIVEN any group in the response
- WHEN its properties are enumerated
- THEN none is a confidence value, a provenance identity, or an origin marker

### Requirement: REQ-005-002 — Groups are computed on precedence-resolved effective values

Grouping SHALL key on `effective(occurrence, lemma)` and `effective(occurrence, pos)` as SPEC-003
§2.5 defines them (§2.2 E1). Grouping on the raw `occurrence.lemma` or `occurrence.pos` column is
FORBIDDEN (E2). Any precedence resolution this capability performs MUST agree with
`resolve_effective` (`domain/annotation.py:132`) for every `(automatic, corrected)` input pair (E3).

This requirement is testable **now**, before any correction writer exists, by seeding
`manual_correction` rows directly — the mechanism SPEC-003 §2.5 shipped one cycle early for exactly
this reason.

Acceptance: **AC-005-02** — Given an import where one occurrence has automatic lemma `saw` with POS
`NOUN` and a seeded `ManualCorrection` setting `lemma` to `see` and `pos` to `VERB`, when the
vocabulary read runs, then that occurrence is counted in group `(see, VERB)` and is **not** counted in
group `(saw, NOUN)`, and if no other occurrence carries `(saw, NOUN)` then that group is absent
entirely; and given a correction on `lemma` only, then the occurrence lands in
`(corrected lemma, automatic POS)`; and given a Hypothesis strategy over `(automatic, corrected)`
pairs, when the grouping's resolution and `resolve_effective` are compared, then they agree on every
generated pair.

#### Scenario: A seeded correction moves an occurrence to a different group

- GIVEN an occurrence with automatic `(saw, NOUN)` and a seeded correction to `(see, VERB)`
- WHEN the vocabulary read runs
- THEN the occurrence is counted in group `(see, VERB)`
- AND it is not counted in group `(saw, NOUN)`

#### Scenario: A group vacated by corrections disappears

- GIVEN an import where the only occurrence of `(saw, NOUN)` carries a correction to `(see, VERB)`
- WHEN the vocabulary read runs
- THEN no group `(saw, NOUN)` is returned

#### Scenario: Precedence is per field in the aggregate too

- GIVEN an occurrence with a seeded correction for `lemma` only
- WHEN the vocabulary read runs
- THEN it is counted in the group keyed `(corrected lemma, automatic POS)`

#### Scenario: The aggregate's precedence agrees with the shipped rule

- GIVEN generated `(automatic, corrected)` pairs
- WHEN the aggregate's resolution is compared against `resolve_effective`
- THEN the two agree on every generated pair

### Requirement: REQ-005-003 — Absent lemma and absent POS are visible, labelled buckets

An occurrence whose effective lemma is `NULL` SHALL be counted in a group keyed `(NULL, effective
POS)`, and an occurrence whose effective POS is `NULL` SHALL be counted in a group keyed `(effective
lemma, NULL)` (§2.3 N1, N2). Both groups MUST be present in the response. An absent key half MUST be
transmitted as JSON `null`, never omitted, never `""`, and never a sentinel string — in particular
never `X`, which is a legitimate UPOS tag (N3). The view MUST label each bucket explicitly and
distinguishably as text, without relying on colour (N4).

Acceptance: **AC-005-03** — Given an import where every occurrence is unannotated, when the
vocabulary read runs, then exactly one group is returned, its key is `(null, null)` in the response
body, and its count equals the import's occurrence count; and given an import with one occurrence
carrying a lemma and no POS, then a group `(lemma, null)` is returned with `null` present as a JSON
`null` rather than an omitted key, `""`, or `X`; and given a mocked response containing a `(null,
null)` group, a `(lemma, null)` group and a fully tagged group, when the view renders, then each
bucket carries a distinct text label and no cell is blank.

#### Scenario: A fully unannotated import returns one visible bucket

- GIVEN an import whose occurrences all have `lemma IS NULL` and `pos IS NULL`
- WHEN the vocabulary read runs
- THEN exactly one group is returned, keyed `(null, null)`
- AND its count equals the import's occurrence count

#### Scenario: A lemma with no tag gets its own bucket

- GIVEN an occurrence with an effective lemma and an effective POS of `NULL`
- WHEN the vocabulary read runs
- THEN a group keyed `(lemma, null)` is returned

#### Scenario: Absence is JSON null, not a sentinel

- GIVEN a returned group with an absent key half
- WHEN the response body is inspected
- THEN that half is present as JSON `null`
- AND it is neither omitted, nor `""`, nor `X`

#### Scenario: Buckets are labelled as text

- GIVEN a mocked response with a `(null, null)` group, a `(lemma, null)` group and a tagged group
- WHEN the view renders
- THEN each bucket carries a distinct text label readable without colour

### Requirement: REQ-005-004 — The vocabulary read has its own endpoint and the annotation contract is frozen

The grouped read SHALL be exposed at `GET /api/v1/imports/{id}/vocabulary`, on a contract distinct
from `annotation.v1.json`. `annotation.v1.json` MUST remain byte-identical and MUST NOT gain a
property. `GET` and `POST /api/v1/imports/{id}/annotation` MUST keep their current status codes,
response bodies, error codes and persisted effects. `SqlAlchemyAnnotationReadRepository.read`
(`annotation_repository.py:106`) MUST remain in service for those routes and MUST NOT be modified to
serve grouping.

Whether the new contract is additionally pinned as a versioned JSON Schema document is a design
decision; this requirement fixes only that it is not `annotation.v1.json`.

Acceptance: **AC-005-04** — Given the shipped `annotation.v1.json`, when it is compared against its
pre-change bytes, then it is byte-identical; and given the complete `003-lemmatization-pos`
acceptance suite, when it is re-run after this capability ships, then it passes with no requirement
weakened; and given the served OpenAPI document, when its paths are enumerated, then
`/api/v1/imports/{import_id}/vocabulary` is present and the two annotation operations are unchanged.

#### Scenario: The annotation contract is untouched

- GIVEN the shipped `annotation.v1.json`
- WHEN it is compared against its pre-change bytes
- THEN it is byte-identical

#### Scenario: The annotation routes still behave identically

- GIVEN the `003-lemmatization-pos` acceptance suite
- WHEN it is re-run after this capability ships
- THEN it passes with no requirement weakened

#### Scenario: The new route is additive

- GIVEN the served OpenAPI document
- WHEN its paths are enumerated
- THEN the vocabulary path is present alongside the two unchanged annotation operations

### Requirement: REQ-005-005 — An unknown import is a 404; an import with no occurrences is an empty success

The vocabulary read SHALL return HTTP 404 with code `IMPORT_NOT_FOUND` for an unknown or
already-deleted import `id`, and SHALL return a successful response with an empty group set for an
import that exists and has zero occurrences. The two states MUST NOT be conflated, and existence MUST
be established independently of whether the aggregation returns any row — the distinction
`BookRepository.frequency_pairs` already documents (`book_repository.py:94-101`,
`application/imports/ports.py:67-74`).

Acceptance: **AC-005-05** — Given an `id` that has never existed, when the vocabulary read runs, then
the response is HTTP 404 with code `IMPORT_NOT_FOUND`; and given an import deleted through the
SPEC-002 delete path, then the same 404 is returned; and given an import that exists with zero
occurrences, then the response is a success carrying an empty group set, not a 404 and not a `null`
body; and given any error body this endpoint emits, when it is inspected, then it contains no textual
form, no lemma, no stack trace and no filesystem path (`REQ-003-019`).

#### Scenario: An unknown id is a 404

- GIVEN an import `id` that has never existed
- WHEN the vocabulary read runs
- THEN the response is HTTP 404 with code `IMPORT_NOT_FOUND`

#### Scenario: A deleted import is a 404

- GIVEN an import deleted through the SPEC-002 delete path
- WHEN the vocabulary read runs
- THEN the response is HTTP 404 with code `IMPORT_NOT_FOUND`

#### Scenario: Zero occurrences is an empty success, not a 404

- GIVEN an import that exists and has zero occurrences
- WHEN the vocabulary read runs
- THEN the response is a success carrying an empty group set
- AND it is neither a 404 nor a `null` body

#### Scenario: Error bodies carry no imported text

- GIVEN any error body this endpoint emits
- WHEN it is inspected
- THEN it contains no textual form, no lemma, no stack trace and no filesystem path

### Requirement: REQ-005-006 — The POS filter narrows which groups are returned (slice 2)

The endpoint SHALL accept an optional POS selector that narrows the returned group set to the groups
whose effective POS matches it. The selector operates on the **group key**, not on occurrences within
a group: a group whose POS does not match is absent from the response, and the counts of the groups
that do match are unchanged by the filter being applied. The selector MUST be able to select the
`NULL`-POS bucket explicitly (§2.3 N2). A selector value that is neither a member of the 17-tag UPOS
set of SPEC-003 §2.2 nor the `NULL`-bucket selector MUST be rejected with `INVALID_REQUEST`; it MUST
NOT be silently ignored and MUST NOT return the unfiltered set.

An absent selector returns every group. A selector matching no group returns an empty group set, not
a 404 (`REQ-005-005`).

Acceptance: **AC-005-06** — Given an import with groups `(run, VERB)` count `2`, `(run, NOUN)` count
`1` and `(house, NOUN)` count `4`, when the read runs with the selector `NOUN`, then exactly
`(run, NOUN)` count `1` and `(house, NOUN)` count `4` are returned and `(run, VERB)` is absent, and
both counts are identical to their unfiltered values; and given the `NULL`-bucket selector on an
import holding a `(lemma, null)` group, then that group is returned; and given a selector value
outside the 17-tag set and outside the `NULL`-bucket selector, then the response is `INVALID_REQUEST`
and no group set is returned; and given no selector, then every group is returned.

#### Scenario: The selector narrows the group set without changing counts

- GIVEN groups `(run, VERB)` `2`, `(run, NOUN)` `1` and `(house, NOUN)` `4`
- WHEN the read runs with selector `NOUN`
- THEN `(run, NOUN)` `1` and `(house, NOUN)` `4` are returned and `(run, VERB)` is absent
- AND each returned count equals its unfiltered value

#### Scenario: The null-POS bucket is selectable

- GIVEN an import holding a `(lemma, null)` group
- WHEN the read runs with the `NULL`-bucket selector
- THEN that group is returned

#### Scenario: An invalid selector is rejected, not ignored

- GIVEN a selector value outside the 17-tag set and outside the `NULL`-bucket selector
- WHEN the read runs
- THEN the response is `INVALID_REQUEST`
- AND the unfiltered group set is not returned

#### Scenario: A selector matching nothing is an empty success

- GIVEN a selector whose tag no group in the import carries
- WHEN the read runs
- THEN an empty group set is returned with a success status

### Requirement: REQ-005-007 — No behaviour in this capability keys off confidence

No group key, count, ordering, default ordering, filter, threshold, visibility rule, badge, warning,
or visual treatment introduced by this capability SHALL read `pos_confidence` or `lemma_confidence`
(§2.4 K1). No group MAY carry an aggregate confidence of any kind (K2). The endpoint MUST NOT accept
a confidence-valued request parameter (K3). Confidence MAY still be displayed per occurrence wherever
an individual occurrence is shown (K4).

This is an **absence assertion**, so it carries SPEC-003 §3.3's evidence obligations: a mutation
check with the observed failure output recorded verbatim in the test docstring (M1), a non-vacuity
test that fails closed when the scan reaches none of this capability's modules (M2), and a boundary
control (M3). It MUST NOT be satisfied by adding this capability's modules to an exclusion list, by
weakening the existing pattern, or by narrowing the scanned inputs (SPEC-003 §3.4 W1, W2).

Acceptance: **AC-005-07** — Given every backend and frontend module this capability introduces, when
each is inspected structurally for an identifier naming a confidence action — reusing the shared
mechanism of `apps/api/tests/unit/test_no_confidence_action_or_propn_filter.py:35` rather than a
second copy of it — then there are zero matches; and given the served OpenAPI document, when the
vocabulary operation's parameters are enumerated, then none is a confidence value; and given the
group response shape, when its properties are enumerated, then none is confidence-derived; and given
each of three mutations applied in turn — a `min_confidence` query parameter on the route, a
`mean_confidence` property on the group shape, and a `sort_by_confidence` helper in the vocabulary
repository — when the guard runs, then **each** produces a violation, with the observed failure output
recorded in the test docstring; and given a scan that reaches none of this capability's modules, when
the suite runs, then it fails rather than passing vacuously.

#### Scenario: Nothing in the capability acts on confidence

- GIVEN every backend and frontend module this capability introduces
- WHEN each is inspected structurally for a confidence-action identifier
- THEN there are zero matches

#### Scenario: The endpoint accepts no confidence parameter

- GIVEN the served OpenAPI document
- WHEN the vocabulary operation's parameters are enumerated
- THEN none is a confidence value

#### Scenario: The group shape carries no aggregate confidence

- GIVEN the group response shape
- WHEN its properties are enumerated
- THEN none is confidence-derived

#### Scenario: Each forbidden addition is caught

- GIVEN a `min_confidence` query parameter, a `mean_confidence` group property, and a `sort_by_confidence` helper, applied in turn
- WHEN the guard runs on each
- THEN each produces a violation
- AND the observed failure output is recorded in the test docstring

#### Scenario: The confidence scan fails closed

- GIVEN a scan that reaches none of this capability's modules
- WHEN the suite runs
- THEN it fails rather than passing vacuously

### Requirement: REQ-005-008 — No code path in this capability writes a `ManualCorrection` row

No module this capability introduces SHALL insert, update, or delete a `manual_correction` row, and
no frontend surface it introduces SHALL offer an affordance that submits a correction — not as a
button, not inline, not as an editable cell (SPEC-003 §2.5 R6; proposal §Scope). The correction write
path and its UX are SPEC-004.

**This guard differs from the annotation write path's, deliberately.** SPEC-003 R3 forbids the
annotation write path from *referencing* `ManualCorrection` at all — anything it cannot touch, it
cannot corrupt. This capability's aggregate query **must read** `manual_correction` to satisfy
`REQ-005-002`. Its guard therefore MUST distinguish read from write: a `SELECT` is permitted, an
`INSERT`, `UPDATE` or `DELETE` is a violation. Satisfying it by exempting this capability's modules
from the existing walk is FORBIDDEN (SPEC-003 §3.4 W1).

This is an **absence assertion** and carries SPEC-003 §3.3 M1–M3 in full.

Acceptance: **AC-005-08** — Given every module this capability introduces, when each is checked by
two mechanisms — structural inspection for `sqlalchemy` Core calls and raw SQL text, and, for every
ORM-instance form a static pass cannot verify (`session.add`/`.merge`/`.delete`,
`Query.delete`/`.update`, bulk mappings), runtime observation of every statement an operation issues
— then no `INSERT`, `UPDATE` or `DELETE` targeting `manual_correction` reaches either check, whether
expressed through the ORM class or as SQL text (§5 AMB-11); and given the vocabulary repository with a
seeded correction present, when the vocabulary read runs, then the `manual_correction` rows are
byte-identical afterwards and the row count is unchanged; and given each of two mutations applied in
turn — an insert against `ManualCorrection` and a delete against it, both inside the vocabulary
repository — when the guard runs, then **each** produces a violation, with the observed failure output
recorded in the test docstring; and given the same statement placed in a module outside this
capability, then it still produces a violation (M3); and given the frontend client module this
capability introduces, when its requests are enumerated, then every one is a `GET`; and given the
rendered vocabulary view, when its interactive controls are enumerated, then none submits a
correction.

#### Scenario: No write statement reaches the correction table, structurally or at runtime

- GIVEN every module this capability introduces
- WHEN each is inspected structurally for `sqlalchemy` Core calls and raw SQL text, and every
  operation is run once under statement-level observation (§5 AMB-11)
- THEN none contains, and no statement it issues is, an `INSERT`, `UPDATE` or `DELETE` targeting
  `manual_correction`, whether expressed through the ORM class or as SQL text

#### Scenario: Reading is permitted and leaves the table untouched

- GIVEN an import with a seeded manual correction
- WHEN the vocabulary read runs
- THEN the correction rows are byte-identical afterwards and the row count is unchanged

#### Scenario: A write added to the vocabulary repository is caught

- GIVEN an insert against `ManualCorrection`, then a delete against it, added in turn to the vocabulary repository
- WHEN the guard runs on each
- THEN each produces a violation
- AND the observed failure output is recorded in the test docstring

#### Scenario: The exemption boundary holds

- GIVEN the same write statement placed in a module outside this capability
- WHEN the guard runs
- THEN it still produces a violation

#### Scenario: The frontend offers no correction affordance

- GIVEN the vocabulary client module and the rendered view
- WHEN its requests and interactive controls are enumerated
- THEN every request is a `GET` and no control submits a correction

### Requirement: REQ-005-009 — Groups are computed at query time and never stored

No entity introduced by this capability SHALL carry a stored aggregate POS, a stored aggregate lemma,
or a persisted `(lemma, POS)` group row (§2.5 P1). No column of `book`, `occurrence`,
`annotation_provenance` or `manual_correction` MAY be added, dropped, renamed, retyped or made
non-nullable (P2). An **additive, reversible index** MAY be added if the design's benchmark shows one
is needed; its `downgrade()` MUST return the schema to the SPEC-003 baseline (P3).

Acceptance: **AC-005-09** — Given the persisted schema after this capability ships, when its tables
are enumerated, then no table holds a lemma-keyed or `(lemma, POS)`-keyed aggregate row, and `book`,
`occurrence`, `annotation_provenance` and `manual_correction` carry exactly the columns of the
SPEC-003 baseline; and given a seeded correction written after a vocabulary read has already run,
when the vocabulary read runs again, then the new group set reflects the correction with no cache
invalidation step; and given any migration this capability adds, when `alembic upgrade head` then
`alembic downgrade -1` run, then both exit `0` and the schema returns to the SPEC-003 baseline.

#### Scenario: No aggregate is persisted

- GIVEN the persisted schema after this capability ships
- WHEN its tables are enumerated
- THEN none holds a lemma-keyed or `(lemma, POS)`-keyed aggregate row
- AND the four existing tables carry exactly the SPEC-003 baseline columns

#### Scenario: A correction written between reads changes the next read

- GIVEN a vocabulary read, then a seeded correction, then a second vocabulary read
- WHEN the second read returns
- THEN its groups reflect the correction with no cache invalidation step

#### Scenario: Any added migration reverses cleanly

- GIVEN a database at the SPEC-003 baseline
- WHEN `alembic upgrade head` then `alembic downgrade -1` run
- THEN both exit `0` and the schema returns to the SPEC-003 baseline

### Requirement: REQ-005-010 — The frontend renders what the API returns and duplicates no linguistic rules

The vocabulary view SHALL render the groups the API returns. It MUST NOT group, re-group, merge,
split, lemmatize, tag, tokenize, normalize, case-fold, infer, or re-derive any lemma, POS, or count,
and MUST NOT apply correction precedence (Art. VII.5, `REQ-002-014`, `REQ-003-018`). Presentational
localization of a received UPOS tag into a readable label is permitted and is presentation, not a
linguistic rule; the mapping MUST be total over the 17-tag set and an unmapped value MUST be rendered
as the received tag rather than replaced by a guess or an empty cell. The view MUST be
keyboard-navigable, MUST carry accessible labels, and MUST NOT depend on colour alone
(Art. IX.1–4). `apps/web/src/components/AnnotationTable.tsx`'s rendering, behaviour and tests MUST
remain unchanged; its UPOS label-map definition site MAY move to a shared module that both views
import (§5 `AMB-8`). Duplicating the 17-tag map into a second table is FORBIDDEN.

Acceptance: **AC-005-10** — Given the vocabulary view's sources, when they are searched for grouping,
counting, lemmatization, tagging, normalization and precedence resolution, then there are zero
matches; and given a mocked response, when the view renders, then each row shows the received lemma,
POS and count verbatim; and given a mocked group whose POS the label map does not cover, then the raw
tag is displayed and no cell is blank; and given `AnnotationTable.tsx` after any label-map
extraction, when its existing test suite runs, then it passes unchanged and its rendered output is
identical, and the repository holds exactly one UPOS label map rather than two.

#### Scenario: No grouping or linguistic derivation client-side

- GIVEN the vocabulary view's sources
- WHEN they are searched for grouping, counting, lemmatization, tagging, normalization and precedence resolution
- THEN there are zero matches

#### Scenario: Received values render verbatim

- GIVEN a mocked vocabulary response
- WHEN the view renders
- THEN each row shows the received lemma, POS and count unchanged

#### Scenario: An unmapped tag degrades to the raw tag

- GIVEN a mocked group whose POS the label map does not cover
- WHEN the row renders
- THEN the received tag is displayed and the cell is not blank

#### Scenario: The existing annotation table keeps its behaviour and the label map stays single

- GIVEN `AnnotationTable.tsx` after any label-map extraction
- WHEN its existing test suite runs
- THEN it passes unchanged and its rendered output is identical
- AND exactly one UPOS label map exists in the repository, not two

### Requirement: REQ-005-011 — The unpaginated result is bounded by an externally anchored budget and an executable benchmark

The endpoint SHALL return every group for the requested import, with no pagination control, matching
`BookRepository.frequency_pairs`'s established shape (`book_repository.py:94-114`). That default is
conditional: the design phase MUST state a numeric bound for response body size and a numeric bound
for latency, MUST measure the response at SPEC-002's ~688,000-occurrence ceiling
(`SPEC-002 spec.md:213-215`), and MUST add pagination if a measurement exceeds its bound.

Each bound MUST cite an anchor **outside this capability's own measurements**, and that citation MUST
be arithmetically checkable: a stated derivation that does not compute is a violation of this
requirement, not a wording defect. A bound justified only by this capability's measurement clearing
it is **FORBIDDEN**.

Where a bound is a judgment rather than a derivation, the design MUST say so **in those words** and
MUST name what the judgment protects. An honest judgment is permitted; a judgment presented as a
derivation is not.

The benchmark MUST assert against exactly the bounds the budget names, and MUST NOT assert against a
quantity the budget leaves unbounded. A quantity the design reports without a bound MUST be recorded
as an observation, never asserted. Lowering any named bound below its measured value MUST make the
benchmark fail.

The measurement MUST be an executable benchmark, marked as the repository already marks one
(`@pytest.mark.bench`, `apps/api/tests/integration/test_import_bench.py`), and MUST NOT be replaced by
an estimate in prose.

Acceptance: **AC-005-11** — Given the design artifact's stated response-body and latency bounds, when
each bound's cited anchor is recomputed, then every derivation computes to the bound it claims to
produce, or the design names that bound a judgment in those words and states what it protects, and no
bound cites this capability's own measurement as its justification; and given a synthetic import at
the ~688,000-occurrence ceiling, when the benchmark runs, then it asserts the response body size and
the latency against the bounds the budget names and asserts no quantity the budget leaves unbounded;
and given the benchmark with a named bound mutated below its measured value, when it runs, then it
fails; and given the shipped endpoint, when its parameters are enumerated, then either no pagination
parameter exists and the benchmark passes, or a pagination parameter exists and the design records
the exceeded bound that required it.

#### Scenario: Every bound's derivation is checkable and none is self-justified

- GIVEN the design artifact's stated response-body and latency bounds
- WHEN each bound's cited anchor is recomputed
- THEN each derivation computes to the bound it claims to produce, or the design names that bound a judgment in those words and states what it protects
- AND no bound is justified by this capability's own measurement clearing it

#### Scenario: The benchmark asserts the named bounds and nothing unbounded

- GIVEN a synthetic import at the ~688,000-occurrence ceiling
- WHEN the benchmark runs
- THEN it asserts the response body size and the latency against the bounds the budget names
- AND it asserts no quantity the budget leaves unbounded

#### Scenario: The benchmark is not vacuous

- GIVEN the benchmark with a named bound mutated below its measured value
- WHEN it runs
- THEN it fails

#### Scenario: Pagination exists only if a bound was exceeded

- GIVEN the shipped endpoint
- WHEN its parameters are enumerated
- THEN either no pagination parameter exists and the benchmark passes
- OR a pagination parameter exists and the design records the exceeded bound that required it

---

## 4. Error contract

This capability reuses the shared error envelope of `SPEC-002 §4` and introduces **no new error
code**. The rows below are the codes this endpoint emits.

| Code | HTTP | Trigger | Class (Art. X.3) |
|------|------|---------|------------------|
| `IMPORT_NOT_FOUND` | 404 | Vocabulary requested for an unknown or already-deleted import `id` (`REQ-005-005`) — reused from `SPEC-002 §4` | User |
| `INVALID_REQUEST` | 422 | The POS selector is neither a member of the 17-tag UPOS set nor the `NULL`-bucket selector (`REQ-005-006`) — reused from `SPEC-002 §4` | User |

**Empty is not an error.** An import that exists with zero occurrences, and a filter that matches no
group, are both successes carrying an empty group set. Existence is checked with its own query,
independent of whether the aggregation returns a row — the distinction
`BookRepository.frequency_pairs` documents at `book_repository.py:94-101` and
`application/imports/ports.py:67-74`. Conflating them would report an existing empty import as
deleted.

Every error body MUST carry a distinct code and a comprehensible, actionable message (Art. VIII.4),
and MUST NOT contain imported text, textual forms, lemmas, corrected values, stack traces, filesystem
paths, or environment values (`REQ-003-019`, unchanged and inherited).

---

## 5. Ambiguities, contradictions and decisions recorded and resolved (AGENTS.md §9)

Each item below was an ambiguity or a contradiction in the inputs. None was resolved silently.

| ID | Ambiguity, contradiction or open decision | Resolution | Status |
|----|-------------------------------------------|------------|--------|
| **DEC-1** | **Grouping semantics.** The anchor "group by lemma, filter by POS" is satisfiable by three incompatible readings (exploration §Approaches): lemma-only groups, `(lemma, POS)` groups, or a hierarchical lemma group with a POS facet. Each produces a different DTO shape and a different meaning for the filter. | **`(lemma, POS)` pairs** (§2.1 G1). ADR-0006 rejects a single global POS per lemma, so a bare-lemma group has no well-defined POS and the filter has no well-defined subject. Settled in the proposal (Decision A). | **Closed. Do not re-open** |
| **DEC-2** | **Precedence in the aggregate.** Group on the raw `occurrence.lemma`/`.pos` columns (cheap, index-friendly, wrong once SPEC-004 ships) or on precedence-resolved effective values (requires joining `manual_correction` before `GROUP BY`). | **Effective values** (§2.2 E1, E2). Raw-column grouping is an Art. V violation introduced today and observable only later: the correction is stored, returned by `GET .../annotation`, and silently missing from the browser. Settled in the proposal (Decision B). | **Closed. Do not re-open. `REQ-005-002` is testable now against seeded corrections, so SPEC-004 extends a proven mechanism instead of retrofitting one** |
| **DEC-3** | **Whether this capability modifies `003-lemmatization-pos`.** It inherits C6, R6, P5, L6 and S1–S4 and restates several of them in §2. | **`ADDED` only; no `MODIFIED` delta is emitted.** No inherited requirement is wrong or incomplete — each is silent about a grouped read because no grouped read existed. Under the delta convention a `MODIFIED` block replaces the whole requirement at archive time, so re-stating a correct requirement to inherit from it risks losing scenarios for no gain (precedent: `SPEC-003 §6 DEC-3`). | Accepted |
| **AMB-1** | **Group ordering is unspecified by the anchor.** An unordered aggregate makes the list view reshuffle between renders and turns every acceptance scenario into a set comparison. | The ordering MUST be **deterministic** (§2.1 G5, Art. VI.2) and MUST NOT key off confidence (§2.4 K1). The **sort key itself is a design decision**, not a product one — SPEC-002 `AMB-5` already settled that a deterministic diacritic-insensitive key over the grouping key is the repository's approach for the analogous case, and locale collation was rejected there on reproducibility grounds. This specification fixes determinism and forbids the confidence key; it names no sort column. | Accepted |
| **AMB-2** | **`NULL` versus the UPOS tag `X`.** Both can be described as "unknown POS". Collapsing them is the available mistake. | They are different facts and MUST stay distinguishable (§2.3 N3). `X` means the model classified the token and could not place it; `NULL` means no annotation exists for that field. This mirrors `SPEC-003 §2.3 C4`'s rule for `NULL` versus `0.0` confidence. | Accepted |
| **AMB-3** | **The isolation guard's rule differs between capabilities.** SPEC-003 R3 forbids the annotation write path from referencing `ManualCorrection` at all. `REQ-005-002` requires this capability's aggregate to read it. A single "no reference" guard applied to both would block Decision B. | **Not a contradiction — the two paths have different obligations.** The write path must not touch what it must not corrupt; the read path must read what precedence requires. The guard for this capability distinguishes **read from write** (`REQ-005-008`): `SELECT` permitted, `INSERT`/`UPDATE`/`DELETE` a violation. Exempting this capability's modules from the existing walk is FORBIDDEN (`SPEC-003 §3.4 W1`). | **Closed. The distinction is written into `REQ-005-008` rather than inferred** |
| **AMB-4** | **The POS filter's subject.** "Filter by POS" could narrow which groups appear, or narrow which occurrences count inside a still-visible group. The two produce different counts for the same request. | **It narrows the group set; counts are unchanged by filtering** (`REQ-005-006`). Under Decision A, POS is half the group key, so filtering on it is a predicate over keys. Narrowing within a group would require a group to have a POS-heterogeneous membership, which Decision A eliminated. | **Closed. Follows from DEC-1** |
| **AMB-5** | **The POS filter ships in slice 2**, so the anchor's stated scope is only fully delivered at the second PR. | Accepted with the consequence stated: slice 1 delivers observable value (grouped counts, Art. III) and the capability is **incomplete** until `REQ-005-006` ships. Recorded in §1 and §6 PV-3 rather than implied by a task list. Delivery strategy is `ask-on-risk` and the forecast exceeds the 400-line review budget, so a human slicing decision is expected before apply (proposal §Vertical Slice). | **Accepted tradeoff, recorded** |
| **AMB-6** | **Pagination.** No endpoint in this codebase paginates; `frequency_pairs` returns everything. The group count is far below the occurrence count but is still unbounded. | **Unpaginated by default, gated on a benchmark** (`REQ-005-011`). Each bound cites an anchor outside this capability's own measurements, and the measurement is executable (`@pytest.mark.bench`), so "small enough" becomes falsifiable instead of assumed. `REQ-005-011` originally required the budget to be written down before the measurement; that clause was replaced — see `AMB-9`. | Accepted |
| **AMB-7** | **Indexing.** The only occurrence index (`models.py:72-74`) covers neither `lemma` nor `pos`, and Decision B's join means a plain `(book_id, lemma, pos)` covering index does not fully serve effective-value grouping. | **Deferred to design, gated on the same benchmark** (`REQ-005-011`, §2.5 P3). An index MAY be added additively and reversibly; it is not a stored aggregate and does not violate P1. Index strategy is entangled with Decision B and MUST be measured, not assumed. | Accepted |
| **AMB-8** | **`AnnotationTable.tsx` cannot be both byte-identical and the source of a shared label map.** The proposal states the file is untouched *and* that the new view reuses `UPOS_LABELS`. That const is non-exported at `AnnotationTable.tsx:37`, so both cannot hold. This specification first wrote the byte-identical reading as a normative MUST while the design resolved the same contradiction by extracting the map, leaving the two artifacts in direct conflict. | **Behaviour is preserved, not bytes.** `UPOS_LABELS`/`posLabel` move verbatim into a shared module both views import; rendering, behaviour and the existing test suite are unchanged, and only the definition site moves. Duplicating the 17-tag map is FORBIDDEN — two label tables drift, and the drift is silent. The artifacts that stay byte-exact are `annotation.v1.json` and `import.v1.json`, which are published contracts; a private frontend const is not. | **Closed. Registered and resolved per `AGENTS.md` §9, not changed silently** |
| **AMB-9** | **`REQ-005-011` demanded a temporally-prior budget this change could not supply.** The original requirement read "The budget MUST be written down before the measurement, not inferred from it", and `AC-005-11` scenario 1 checked document order. The design phase had already benchmarked V3 by the time the budget was written, so the clause was unsatisfiable for this change: no artifact could truthfully claim a priority the work did not have. Satisfying it anyway produced a fabricated derivation — the design stated "8 MiB is the midpoint of that shipped range" for `test_import_bench.py`'s 200 KB-20 MB bound. That arithmetic does not compute: the midpoint of 200,000 and 20,000,000 bytes is 10,100,000 bytes (9.63 MiB), and the geometric mean is 2,000,000 bytes. 8 MiB is 8,388,608 bytes, 4.07x the measured 2,063,621 bytes — the bound was back-derived from the measurement and presented as prior art. | **The requirement is rewritten.** `REQ-005-011` now requires each bound to cite an anchor outside this capability's own measurements, requires that citation to be arithmetically checkable, forbids a bound justified only by its own measurement clearing it, requires a bound that is a judgment to say so in those words and name what it protects, and requires the benchmark to assert exactly the named bounds and to fail when one is lowered below its measured value. An auditable derivation and a mutation test are what the temporal clause was proxying for, and unlike document order both stay checkable after the fact. `design.md` §Response budget is restated on anchors that compute. | **Closed. Decided by the maintainer** |
| **AMB-10** | **§2.1 G2 and G4 presuppose one consistent database state and no requirement names the conditions that produce one.** G2 defines a count as "the number of occurrences of that `book_id` whose effective pair equals the key" and G4 scopes the group set to one `book_id`. Both phrases have a determinate subject only if the read observes a single state. `design.md` D1 is the one artifact that named the mechanism — "Both legs MUST run in one `Session` (one snapshot)" — and it named no journal mode under which sharing a `Session` produces a snapshot. It does not: pysqlite emits `BEGIN` only before `INSERT`/`UPDATE`/`DELETE`, so each leg of the shipped `groups()` (`ac5b4b9`) runs in its own implicit transaction, and an `UPDATE` committing between the legs made a group present in both the pre-write and the post-write state disappear while producing a group present in neither. | **No requirement is deleted, weakened, or restated, and no acceptance scenario changes.** Every `AC-005` scenario names a read against a fixed corpus with no interleaved committed write — `AC-005-01` scenario 3 says "no intervening write" in those words, and `AC-005-09` scenario 2 sequences its write strictly between two reads — so each stays verifiable exactly as written, and the shipped repository satisfies them. What this entry records is that G2's "the occurrences" and G4's "an occurrence of another import" have no stated meaning while a write is committing, and that this specification chooses that deliberately: §7 already excludes transaction boundaries from its scope, so the concurrency model belongs to the design, and D1a now carries it. The obligation moves to its own work unit with the journal-mode decision open (`design.md` §D1a, §Open Questions). Until that unit ships, `groups()` under a concurrent committed write is unspecified behaviour, not specified-and-satisfied behaviour — recorded here, not left to be inferred from a requirement's silence. | **Registered per `AGENTS.md` §9. Resolution is a scope move, not a behaviour change; the journal-mode decision stays open** |
| **AMB-11** | **AC-005-08 scenario 1 requires structural inspection of every module for `INSERT`/`UPDATE`/`DELETE` "whether expressed through the ORM class or as SQL text", and a docstring in `test_vocabulary_write_guard.py` read that phrase as "the class as a call argument versus the table name in a string — both covered." Four implementation rounds (Judgment Day rounds 1-4, `tasks.md` T13) established that an AST pass over untyped Python cannot verify that a receiver is a `Session`, so ORM-instance forms — `session.add`, `.merge`, `.delete`, `Query.delete`/`.update`, bulk mappings — cannot be structurally inspected without claims that get falsified; every attempt to infer the receiver's type produced a claim a later round disproved. `session.query(ManualCorrection).delete()` is exactly such a form and is not detected by the shipped guard, contradicting the docstring's "both covered" reading, which was invented in a test docstring and never registered here (a round-5 Judgment Day finding, AGENTS.md §9). | **The requirement is satisfied by two mechanisms, not one.** Structural inspection (the shipped `test_vocabulary_write_guard.py`) covers the forms a static AST pass can verify without receiver-type inference: `sqlalchemy` Core calls (`insert`/`update`/`delete`, import- and module-alias resolved, `ManualCorrection`-or-its-alias as an argument) and raw SQL text naming the table. Runtime statement observation (`tasks.md` Phase 3b: a `before_cursor_execute` listener recording every statement an operation issues) covers every write regardless of expression, including the ORM-instance forms the structural pass cannot see — it observes what was executed, not what a static reading can infer about a receiver. Neither mechanism alone satisfies the scenario; together they do, and no requirement text is deleted or weakened to reach that reading. **AC-005-08 scenario 1's wording needed amending** — "when each is inspected structurally" names a single mechanism, and the two-mechanism reading does not fit that wording as written, so scenario 1 below is restated to name both mechanisms explicitly. `ManualCorrection.__table__.delete()` is a separate case: it has no `Session` receiver to infer, so it needs neither mechanism above, only more AST (`tasks.md` Phase 3c) — it is not evidence that the two-mechanism split is wrong, only that one form was mis-filed under it (`tasks.md` correction, round 5). | **Registered per `AGENTS.md` §9. AC-005-08 scenario 1 amended below. REQ-005-008 is not fully discharged until Phase 3b ships — see `tasks.md` Phase 3a's split note** |

---

## 6. Product-visible decisions

These change what appears on screen. They are decisions, not implementation details.

| # | Decision | What the user sees | Status |
|---|----------|--------------------|--------|
| PV-1 | The study unit is `(lemma, POS)`, not bare lemma | `run` appears twice — once as a verb, once as a noun — with separate counts, and no visual link between them unless the view re-groups for display | Accepted, tradeoff stated (proposal Decision A) |
| PV-2 | Unannotated and untagged occurrences are visible buckets | A never-annotated import shows one labelled bucket with the full token count rather than an empty list. A lemma the analyzer could not tag shows in its own labelled bucket | Accepted (§2.3) |
| PV-3 | The POS filter arrives in slice 2 | Slice 1 ships a grouped list with counts and no filter control. "Filter by POS" is delivered at slice 2 | Accepted, explicitly incomplete (§5 AMB-5) |
| PV-4 | Confidence drives nothing in this view | No low-confidence badge, no confidence sort, no confidence threshold control. Confidence remains visible per occurrence where occurrences are shown | Accepted (§2.4, SPEC-003 C6) |
| PV-5 | Corrections are visible here but not editable here | A corrected occurrence is counted under its corrected `(lemma, POS)`. There is no way to make a correction from this view; that arrives with SPEC-004 | Accepted (§2.2 E4, SPEC-003 R6) |
| PV-6 | Proper nouns appear like every other word | A `PROPN` group is listed unfiltered, unchanged from `SPEC-003 PV-4`. `docs/product-vision.md` §10 step 4 stays knowingly unimplemented until roadmap item 6 | Accepted, inherited |
| PV-7 | Multiword expressions are not grouped | `give up` remains two groups with their own lemmas. Unchanged from `SPEC-003 PV-7` | Accepted; roadmap item 7 / ADR-0009 |

---

## 7. Explicit non-additions

This capability does NOT specify: the manual-correction write path, endpoint, or UI (SPEC-004); a
proper-noun filter or separate proper-noun entity (roadmap item 6); multiword-expression detection
(roadmap item 7, ADR-0009); language detection; a second installed language model; a translation
provider; a `Lexeme`, `WordForm`, or any lemma-keyed entity; a stored aggregate POS or lemma;
export to Anki or any deck-building step; a lemma-level detail or drill-down view; occurrence-level
context or concordance lines; sorting controls; search over lemmas; or any change to
`GET`/`POST /api/v1/imports/{id}/annotation`.

It also explicitly does NOT permit: grouping on the raw `occurrence.lemma` or `occurrence.pos`
column; a second precedence implementation whose semantics differ from `resolve_effective`; dropping,
hiding, or merging away a `NULL`-lemma or `NULL`-POS bucket; transmitting an absent key half as `""`,
as an omitted key, or as the tag `X`; any filter, sort, threshold, badge, warning, or visual treatment
keying off `pos_confidence` or `lemma_confidence`; an aggregate confidence on a group; a
confidence-valued request parameter; any `INSERT`, `UPDATE` or `DELETE` against `manual_correction`; a
correction affordance in the vocabulary view; a persisted group row or aggregate column; a
non-additive or irreversible migration; modifying `annotation.v1.json` or `import.v1.json`; client-side
grouping, counting, or precedence resolution; or exempting this capability's modules from an existing
guard's walk in place of extending that guard.

This specification chooses no module names, file layouts, DTO shapes, column types, index strategy,
sort key, query plan, transaction boundaries, task ordering, or slice contents beyond the slice split
recorded in §1 — `sdd-design` and `sdd-tasks` own those.

---

## 8. Verification hooks

| Hook | Check | Verifies |
|------|-------|----------|
| V1 | A homograph produces two groups with separate counts; counts are occurrence counts; two identical requests return an equal ordered response; no group property is a confidence, provenance, or origin marker | AC-005-01 |
| V2 | Seeded corrections move occurrences between groups, vacate a group entirely, resolve per field, and the aggregate's resolution agrees with `resolve_effective` over generated pairs | AC-005-02 |
| V3 | A fully unannotated import returns exactly one `(null, null)` group whose count equals the occurrence count; a `(lemma, null)` group is returned; absence is JSON `null`, never `""`, an omitted key, or `X`; each bucket carries a distinct text label | AC-005-03 |
| V4 | `annotation.v1.json` byte-identical; the full `003-lemmatization-pos` acceptance suite passes unweakened; the served OpenAPI carries the new path alongside the two unchanged annotation operations | AC-005-04 |
| V5 | Unknown id → 404 `IMPORT_NOT_FOUND`; deleted id → the same 404; existing-but-empty → empty success; every error body free of textual forms, lemmas, stack traces and paths | AC-005-05 |
| V6 | The selector narrows the group set with counts unchanged; the `NULL`-POS bucket is selectable; an out-of-set selector returns `INVALID_REQUEST` and not the unfiltered set; a selector matching nothing returns an empty success | AC-005-06 |
| V7 | Zero confidence-action identifiers across this capability's modules via the shared mechanism; no confidence parameter on the served operation; no confidence-derived group property; each of the three mutations (`min_confidence` parameter, `mean_confidence` property, `sort_by_confidence` helper) produces a violation with observed output in the docstring; the scan fails closed | AC-005-07 |
| V8 | Zero write statements against `manual_correction` in this capability's modules; correction rows byte-identical after a vocabulary read; an insert and a delete each produce a violation with observed output in the docstring; the same statement outside the capability still violates; every frontend request is a `GET`; no control submits a correction | AC-005-08 |
| V9 | No persisted lemma-keyed or `(lemma, POS)`-keyed aggregate row; the four existing tables carry exactly the SPEC-003 baseline columns; a correction written between two reads changes the second; any added migration upgrades and downgrades to exit `0` | AC-005-09 |
| V10 | Zero matches for grouping, counting, lemmatization, tagging, normalization and precedence in the view's sources; received values render verbatim; an unmapped tag degrades to the raw tag; `AnnotationTable.tsx`'s suite passes unchanged with identical rendered output, and exactly one UPOS label map exists | AC-005-10 |
| V11 | Each stated bound cites an anchor outside this capability's measurements and its derivation recomputes to the bound, or is named a judgment in those words with what it protects; no bound is justified by its own measurement; the `@pytest.mark.bench` benchmark at the ~688,000-occurrence ceiling asserts response body size and latency against exactly those bounds and asserts no unbounded quantity; a bound mutated below its measured value fails; pagination exists only alongside a recorded exceeded bound | AC-005-11 |
| V12 | Every fixture is synthetic or public domain; no book text is committed (Art. IV.1–2) | Art. IV compliance |
| V13 | Coverage gates hold: `domain/` and `application/` at 90% or above, global at 80% or above (Art. II); linters and type checks clean; the zero-warning `filterwarnings` gate unchanged | Art. II compliance |

---

## 9. Traceability

`docs/traceability-matrix.md` MUST carry **one row per requirement** `REQ-005-001` … `REQ-005-011`,
each carrying its `AC-005-##` reference, its test file(s), its task ID(s) and its status, before this
capability can be considered done (Art. I.5, Art. XI, `AGENTS.md` §10).

Each row's acceptance cell MUST cite this document by path — matching the citation form the existing
`REQ-002-###` and `REQ-003-###` rows use — and each cited Python test node MUST resolve against
pytest collection. That resolution is enforced, not aspirational: the guard at
`apps/api/tests/unit/test_traceability.py:190`
(`test_every_cited_python_test_node_resolves_against_the_collected_suite`) fails on a matrix row
citing a test that does not exist, and no cell may hold a placeholder
(`test_traceability.py:19`, `_PLACEHOLDER_RE`).

Rows for `REQ-005-006` MAY carry an unfulfilled status while slice 2 is outstanding; the capability is
not done until every row is fulfilled (§1, §5 AMB-5). `docs/` is Spanish (ADR-0010); these rows stay
Spanish while this specification stays English.

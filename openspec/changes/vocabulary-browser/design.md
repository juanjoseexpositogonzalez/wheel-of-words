# Design: Vocabulary Browser (005-vocabulary-browser)

## Technical Approach

`GET /api/v1/imports/{id}/vocabulary` returns every `(lemma, POS)` group for one import, keyed on
precedence-resolved effective values (Decision B), computed at query time (P5). A new
`SqlAlchemyVocabularyReadRepository` runs an **index-ordered aggregation over the raw columns plus a
bounded correction delta**, not a `COALESCE` grouping. `annotation_repository.py`,
`AnnotationTable.tsx`, and `annotation.v1.json` are untouched.

## Response budget (stated before measuring — `REQ-005-011`, `AC-005-11` scenario 1)

These are the bounds this endpoint must clear at SPEC-002's ~688,000-occurrence ceiling. They are
fixed here **before** any number below was produced, and are derived from prior art rather than from
this design's own results:

| Bound | Value | Where it comes from |
|---|---|---|
| Response body size | **≤ 8 MiB** | `test_import_bench.py` already bounds SPEC-002's occurrence-level `GET` body at 200 KB-20 MB at the same ceiling. A grouped result aggregates that stream, so it must land well inside the endpoint it summarises; 8 MiB is the midpoint of that shipped range |
| Latency | **≤ 1500 ms p95** | The interaction is a user clicking through to a list view. SPEC-002's synchronous import already spends ~3.4 s at the ceiling and is accepted as a one-off; a read the user repeats gets a tighter bound, set at under half of it |
| Group cardinality | **no bound** | Recorded as an observation, not a gate. It is an input to the pagination decision, not a pass/fail criterion |

**If a measurement exceeds either bound, pagination is required** (`REQ-005-011`). The benchmark in
`test_vocabulary_bench.py` asserts against these two numbers, and `AC-005-11` scenario 3 requires that
lowering either below the measured value makes the test fail.

## Benchmark (measured, not estimated)

688,000 occurrence rows, one book, Zipfian synthetic vocabulary (30k lemmas), each lemma bound to one
primary UPOS tag with a 12% homograph minority, 2% unannotated, 5,000 seeded `manual_correction` rows.
Script: throwaway, not committed. macOS/SQLite, 9 runs interleaved, warm cache.

| Strategy | no index p50 | indexed p50 | indexed p95 | groups |
|---|---|---|---|---|
| Raw-column `GROUP BY` (violates Decision B — baseline only) | 2589 ms | 222 ms | — | 30,817 |
| **V1** two `LEFT JOIN manual_correction` + `COALESCE` | 2951 ms | 1375 ms | 1664 ms | 34,827 |
| **V2** pivoted-CTE + one `LEFT JOIN` + `COALESCE` | 2911 ms | 966 ms | 1293 ms | 34,827 |
| **V3** index-ordered raw `GROUP BY` + correction delta | 3049 ms | **389 ms** | **533 ms** | 34,827 |

With `manual_correction` empty — the state SPEC-003 actually ships (R6): V1 661 ms, V2 611 ms,
**V3 177 ms p50 / 222 ms p95**. All three produced byte-identical group dictionaries (asserted in the
benchmark), so V3's speed is not bought with a different answer.

Query plans (indexed): V3 leg A is `SEARCH o USING COVERING INDEX ix_occurrence_book_lemma_pos
(book_id=?)` with **no temp B-tree**. V1 and V2 both keep `USE TEMP B-TREE FOR GROUP BY` — unavoidable,
because their grouping key is a computed expression that no index can pre-sort.

## Architecture Decisions

### D1 — Query strategy: V3 (hybrid), not SQL `COALESCE` grouping

| Option | Measured | Why it loses |
|---|---|---|
| V1 two `LEFT JOIN` + `COALESCE` | 1375 ms p50 | 3.5x slower; duplicates the precedence rule in SQL |
| V2 pivoted CTE + `COALESCE` | 966 ms p50 | 2.5x slower; same rule duplication |
| Load-and-group in `application/` | 5927 ms p50 (v1 bench) | Transfers 688k rows to Python — the scale problem SPEC-002 already solved |
| **V3 raw `GROUP BY` + delta** | **389 ms p50** | **Chosen** |

V3: leg A groups every occurrence on the raw columns (index-ordered, no temp B-tree). Leg B returns
one row per *corrected* occurrence carrying its raw values and its correction. The repository then
moves each corrected occurrence from its raw group to its effective group by calling
`domain.annotation.resolve_effective` — one call per corrected field. Work is O(groups + corrections),
never O(occurrences).

Two non-performance reasons V1/V2 lose, either sufficient on its own:

1. `domain/annotation.py:133` documents `resolve_effective` as "the ONLY place [§2.5's precedence rule]
   runs". A SQL `COALESCE` is a second definition of that rule and makes the docstring false. V3 keeps
   one definition.
2. `COALESCE(mc.corrected_value, o.lemma)` is only equivalent to `resolve_effective` because
   `manual_correction.corrected_value` is `nullable=False` (`models.py:151`). If SPEC-004 ever allows a
   correction that clears a value, `COALESCE` silently falls through to the automatic value while
   `resolve_effective` returns the correction. V3 has no such coupling.

**Correctness obligation.** V3's equivalence is non-obvious. Both legs MUST run in one `Session` (one
snapshot), and a Hypothesis property test MUST assert V3 ≡ naive per-occurrence Python grouping over
arbitrary seeded corrections. This is a RED-first requirement, not a review note.

### D2 — Index required: `ix_occurrence_book_lemma_pos (book_id, lemma, pos)`

Measured 2589 ms → 222 ms on the aggregation leg (**11.6x**). Without it every strategy sits near 3 s.
Column order matches the display sort and mirrors `ix_occurrence_book_norm_raw`'s covering-scan intent
(`models.py:68-71`).

**Partial index rejected.** `WHERE lemma IS NOT NULL` would stay empty during import (SPEC-002 writes
every row NULL), but the NULL-lemma leg then falls back to `ix_occurrence_book_norm_raw` + temp B-tree:
measured **4238 ms vs 791 ms** for the full index on the same data. The full index serves both buckets
because NULL sorts first.

**Write cost, honestly.** Disk is stable and reproducible: **+14.1 MiB on a 110.5 MiB annotated
database (+13%)**; index build 1.25 s. Import/annotate time cost did **not** converge across three
attempts (+43%/+147%, then +81%/+333%, then a physically impossible negative) — this hardware's noise
exceeds the effect. The annotate path itself measures 156-281 s at the ceiling, dominated by
`annotation_write_repository.py:_update_occurrences`' deliberate one-`UPDATE`-per-row design; index
maintenance is not the term that matters there. Reported as unresolved, not as zero.

### D3 — No pagination

Both bounds stated in §Response budget are cleared:

| Bound | Budget | Measured | Verdict |
|---|---|---|---|
| Response body size | ≤ 8 MiB | **1.97 MiB** (2,063,621 bytes) | clears, 4.1x headroom |
| Latency p95 | ≤ 1500 ms | **533 ms** | clears, 2.8x headroom |

688,000 occurrences collapse to **34,827 groups (19.8:1)**; 28,705 distinct lemmas, 17 NULL-lemma
groups, 43 NULL-POS groups. Neither bound is exceeded, so `REQ-005-011`'s pagination trigger does not
fire and the endpoint returns every group, matching `frequency_pairs`.

Had either bound been exceeded, pagination would be mandatory and this section would record which one
and by how much. It is not a decision the measurement was allowed to justify after the fact.

### D4 — Confidence is structurally absent (C6)

The query joins `occurrence` and `manual_correction` only. `annotation_provenance` — the sole holder of
`pos_confidence`/`lemma_confidence` — is never joined, so confidence cannot reach this endpoint at all.
Stronger than "nothing branches on it". Enforced by an AST test asserting
`vocabulary_repository.py` never names `AnnotationProvenance`, mirroring
`test_annotation_write_repository_isolation.py`. Result ordering is `occurrence_count DESC, lemma, pos`
— frequency, never confidence.

## Data Flow

    GET /imports/{id}/vocabulary
        │
    api/routes/vocabulary.py ──► application/vocabulary/use_cases.ReadVocabulary
                                          │  (VocabularyReader port)
                                          ▼
                    infrastructure/persistence/vocabulary_repository.py
                        leg A: GROUP BY o.lemma, o.pos   (covering index, no temp B-tree)
                        leg B: corrected occurrences only (bounded by correction count)
                        merge: domain.annotation.resolve_effective  ◄── ONE definition of §2.5
                                          │
                                   list[VocabularyGroup] | None   (None ⇒ 404)

## File Changes

| File | Action | Description |
|---|---|---|
| `infrastructure/persistence/models.py` | Modify | Add `Index("ix_occurrence_book_lemma_pos", "book_id", "lemma", "pos")` |
| `apps/api/migrations/versions/0004_vocabulary_group_index.py` | Create | `revision="0004_vocabulary_group_index"`, `down_revision="0003_annotation"` |
| `infrastructure/persistence/vocabulary_repository.py` | Create | `VocabularyGroup` + `SqlAlchemyVocabularyReadRepository.groups()` |
| `application/vocabulary/{__init__,ports,use_cases}.py` | Create | `VocabularyReader` Protocol + `ReadVocabulary` (mirrors `ReadImport`) |
| `api/dtos/vocabulary.py` | Create | `VocabularyGroupResponse`, `VocabularyResponse` |
| `api/routes/vocabulary.py` | Create | New router; `api/routes/annotation.py` untouched |
| `api/schemas/vocabulary.v1.json` | Create | New contract; `annotation.v1.json` byte-identical |
| `api/dependencies.py`, `api/main.py` | Modify | Provider + router registration |
| `apps/web/src/types/vocabulary.ts` | Create | `VocabularyGroup`, `VocabularyResult` |
| `apps/web/src/api/vocabulary.ts` | Create | `getVocabulary(importId)` |
| `apps/web/src/components/uposLabels.ts` | Create | `UPOS_LABELS` + `posLabel` extracted (see Deviation) |
| `apps/web/src/components/AnnotationTable.tsx` | Modify | Import the extracted map; rendering unchanged |
| `apps/web/src/components/VocabularyBrowser.tsx` | Create | Grouped list; no linguistic computation |

## Interfaces

```python
@dataclass(frozen=True, slots=True)
class VocabularyGroup:
    lemma: str | None      # effective, precedence-resolved
    pos: str | None        # effective, precedence-resolved
    occurrence_count: int
```

```json
{ "id": 12, "group_count": 34827, "total_occurrence_count": 688000,
  "groups": [ { "lemma": "correr", "pos": "VERB", "occurrence_count": 42 },
              { "lemma": null, "pos": null, "occurrence_count": 137 } ] }
```

`group_count`/`total_occurrence_count` mirror `import.v1.json`'s `distinct_form_count`/
`total_token_count` and give the bench two deterministic invariants (`len(groups) == group_count`,
`Σ occurrence_count == total_occurrence_count`).

**Guard landmine — apply phase will hit this.** `test_no_lemma_naming.py` binds allow-listed symbols to
owning files. Adding a `lemma` symbol requires extending `_LEMMA_OWNING_FILES` (`:169-190`),
`_SCHEMA_OWNERS` + `_EXPECTED_SCHEMA_FILES` (`:219-229`, `:406`), `_OPENAPI_OWNERS` (`:230-236`), and
the mirrored `LEMMA_OWNING_FILES` in `apps/web/tests/contracts/no-lemma-naming.test.ts`. The wire and
internal field MUST be named exactly `lemma` — `effective_lemma` or `lemma_group` fail the exact-match
allow-list. The DTO needs `Field(title="lemma")` (`dtos/annotation.py:78`) and its docstrings must not
spell the word (published to OpenAPI). Frontend UI copy uses "Lema", never "Lemma".

## Testing Strategy

| Layer | What | Approach |
|---|---|---|
| Unit | DTO strictness; `resolve_effective` reuse | pytest; `extra="forbid"` |
| Property | **V3 ≡ naive Python grouping** under arbitrary corrections | Hypothesis (AGENTS.md §6) |
| Integration | NULL-lemma/NULL-POS buckets visible; seeded corrections change groups; unknown id → `None` | pytest + SQLite |
| Integration | `0004` upgrade/downgrade; `PRAGMA index_list('occurrence')` | mirrors `test_alembic_0003.py` |
| Bench | 688k ceiling, group count, payload size | `@pytest.mark.bench`, non-gating (per `test_import_bench.py`) |
| Structural | `vocabulary_repository.py` never names `AnnotationProvenance` (C6) | AST |
| API | 200 shape, 404 unknown id, `annotation.v1.json` unchanged | TestClient |
| E2E | Groups render with counts | Playwright |

## Threat Matrix

N/A — no shell, subprocess, VCS/PR automation, executable-file classification, or process-integration
boundary. The added surface is one read-only FastAPI GET with an `int` path parameter, validated by the
existing framework machinery.

## Migration / Rollout

`0004_vocabulary_group_index`, `down_revision="0003_annotation"`. Upgrade: `op.create_index(...)`.
Downgrade: `op.drop_index(...)`. No `batch_alter_table` — that is only needed for column add/drop on
SQLite, which this migration does not do. Additive only; no column or table is altered, so the
proposal's rollback plan holds unchanged. Verified by `test_alembic_0004.py` and the existing
`cd apps/api && uv run alembic upgrade head` CI job.

## Changed-Line Estimate (per layer)

| Layer | Est. lines |
|---|---|
| Backend source (models, migration, repository, application, DTOs, route, schema, wiring) | ~360 |
| Backend tests (property, integration, API, alembic, bench, guard-map updates) | ~430 |
| Frontend (types, client, extracted labels, component, page wiring, tests, guard map) | ~290 |
| **Total** | **~1080** |

**This contradicts the proposal's ~400-430 slice-1 forecast.** That forecast did not account for this
repo's docstring density, the guard-map maintenance above, or mandatory TDD test volume. At ~1080 lines
the work is 2.7x the 400-line review budget. Recommended chain: **PR A** migration + index + repository
+ property/equivalence tests + bench (~430); **PR B** application + DTOs + route + schema + API tests
(~330); **PR C** frontend (~290). PR A alone is not user-observable (Art. III) — the observable unit is
A+B. Delivery strategy is `ask-on-risk`, so this needs a human decision before apply.

## Open Questions

- [ ] Slicing: accept the 3-PR chain above, or a 2-PR backend/frontend split at ~760/~290? Requires a
      human decision (`ask-on-risk`, budget exceeded either way).

## Deviation From Proposal

The proposal states `AnnotationTable.tsx` is untouched *and* that the new component reuses
`UPOS_LABELS`. `UPOS_LABELS` is a private const inside `AnnotationTable.tsx:37-55` and is not exported,
so both cannot hold. Resolution: extract `UPOS_LABELS`/`posLabel` verbatim into
`components/uposLabels.ts` and import it in both components. `AnnotationTable.tsx`'s rendering,
behaviour, and tests are unchanged — only the definition site moves. The alternative, duplicating the
17-tag map, creates a drift risk between two label tables with no compensating benefit.

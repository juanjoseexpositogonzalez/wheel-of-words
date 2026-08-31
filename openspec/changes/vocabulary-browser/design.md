# Design: Vocabulary Browser (005-vocabulary-browser)

## Technical Approach

`GET /api/v1/imports/{id}/vocabulary` returns every `(lemma, POS)` group for one import, keyed on
precedence-resolved effective values (Decision B), computed at query time (P5). A new
`SqlAlchemyVocabularyReadRepository` runs an **index-ordered aggregation over the raw columns plus a
bounded correction delta**, not a `COALESCE` grouping. `annotation_repository.py`,
`AnnotationTable.tsx`, and `annotation.v1.json` are untouched.

## Response budget

The bounds this endpoint must clear at SPEC-002's ~688,000-occurrence ceiling. Each cites an anchor
outside this design's own measurements, as `REQ-005-011` requires.

| Bound | Value | Anchor |
|---|---|---|
| Response body size | **≤ 4 MiB (4,194,304 bytes)** | **Derivation.** `max_import_size_bytes: int = 4_194_304` (`apps/api/src/wheel_vocabulary/infrastructure/settings.py:32`) is SPEC-002's import size ceiling — the largest file this system accepts. A summary of an import must not exceed the input that produced it, so the bound is that constant. The derivation is checkable: the bound equals the constant exactly, 4,194,304 = 4,194,304 |
| Latency | **≤ 1000 ms p95** | **This is a judgment, not a derivation.** One second is the threshold for keeping a user's flow of thought uninterrupted, the standard interaction-design bound for a view the user opens repeatedly. What the judgment protects: a list view the user returns to must not feel like a wait. No arithmetic produces this number, and none is claimed |

**If a measurement exceeds either bound, pagination is required** (`REQ-005-011`). The benchmark in
`test_vocabulary_bench.py` asserts response body size and **p95** latency against exactly these two
bounds and asserts nothing else; `AC-005-11` scenario 3 requires that lowering either below its
measured value makes the test fail. Group cardinality carries no bound, so the benchmark records it as
an observation and does not assert it — see D3.

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

**Correctness obligation.** V3's equivalence is non-obvious. A Hypothesis property test MUST assert
V3 ≡ naive per-occurrence Python grouping over arbitrary seeded corrections. This is a RED-first
requirement, not a review note. Both legs MUST also observe one database snapshot — the obligation
D1a carries, because this design stated it without naming a journal mode under which it is
satisfiable.

### D1a — Snapshot isolation across the two legs: unsatisfied, outside WU2

Sharing one `Session` does not give the two legs one snapshot. pysqlite's legacy transactional mode
emits `BEGIN` before `INSERT`, `UPDATE` and `DELETE` and never before a plain `SELECT`, so each leg
runs in its own implicit transaction. An `UPDATE` committing between the legs made a group present in
both the pre-write and the post-write consistent state disappear from the result, and produced a
group present in neither.

Two fixes were implemented and both were rejected by re-judgment:

| Round | Change | Measured outcome |
|---|---|---|
| 1 | `connect`/`begin` event listeners on `create_engine_from_url` | Every session, write sessions included, opens a deferred transaction. `SqlAlchemyBookRepository.delete()` opens with `session.get(Book, book_id)` — a `SELECT`, taking SHARED — then issues its `DELETE`s, so it needs a SHARED→RESERVED promotion inside its own session, and SQLite does not run the busy handler for that promotion. `delete()` went from returning `True` in 1.08 s to raising `OperationalError: database is locked` in 0.19 s. Reverted; `engine.py` is byte-identical to `ac5b4b9` |
| 2 | `exec_driver_sql("BEGIN")` as the first statement inside `groups()` | Closes the torn read, and holds SHARED for the method's whole span. At 700,000 occurrences and 120,000 corrections `groups()` runs 6.4–9.6 s, past the 5 s pysqlite busy timeout `engine.py` never overrides. Measured on byte-identical database copies, 2/2 runs each: `groups(A)` succeeded in 9.648 s while `delete(B)` — an unrelated book — raised `OperationalError: database is locked` at 5.279 s; with only that one line removed, `delete(B)` returned `True` at 1.113 s. SQLite locks the whole file, so an unrelated book buys nothing |

Both rounds failed the same way because under SQLite's rollback journal, holding a read snapshot and
committing concurrently are mutually exclusive. Under `PRAGMA journal_mode=WAL` the round-2
implementation returned the correct snapshot and the interleaved writer committed in 0.001 s.

`create_engine_from_url` (`infrastructure/persistence/engine.py:14-16`) passes no `journal_mode` and
no `busy_timeout`, so every session runs on the rollback journal with pysqlite's 5 s default timeout.
Which journal mode this system runs under is an open decision — see §Open Questions. Snapshot
isolation is therefore outside WU2's scope and becomes its own work unit carrying that decision,
including the regression test that proves the snapshot rather than the locking. The round-2
implementation and its test are preserved on `feat/vocabulary-read-snapshot-isolation` at `ed7e9f3`,
stacked on `ac5b4b9`; that commit message records that it is not ready to merge and enumerates four
defects two independent judges each confirmed.

What WU2 shipped at `ac5b4b9` is the sequential behaviour: one `Session`, two legs, correct groups
for a read with no interleaved committed write. `vocabulary_repository.py`'s module docstring calls
that one snapshot. It is not one, and the file is not modified here — the claim is recorded as a
known defect in `apply-progress.md` §Batch 2 rather than left unstated.

### D2 — Index required: `ix_occurrence_book_lemma_pos (book_id, lemma, pos)`

Measured 2589 ms p50 → 222 ms p50 on the aggregation leg (**11.6x**). Without it every strategy sits
near 3 s.
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
| Response body size | ≤ 4 MiB (4,194,304 bytes) | **1.97 MiB** (2,063,621 bytes) | clears — 4,194,304 / 2,063,621 = **2.03x** headroom |
| Latency p95 | ≤ 1000 ms p95 | **533 ms p95** | clears — 1000 / 533 = **1.88x** headroom |

Neither bound is exceeded, so `REQ-005-011`'s pagination trigger does not fire and the endpoint
returns every group, matching `frequency_pairs`.

**Measured observations, not bounds.** 688,000 occurrences collapse to **34,827 groups** (19.8:1);
28,705 distinct lemmas, 17 NULL-lemma groups, 43 NULL-POS groups. Group cardinality has no stated
bound, so the benchmark reports these numbers and asserts nothing against them (`REQ-005-011`).

Had either bound been exceeded, pagination would be mandatory and this section would record which
bound and by how much.

### D4 — Confidence is structurally absent (C6)

The query joins `occurrence` and `manual_correction` only. `annotation_provenance` — the sole holder of
`pos_confidence`/`lemma_confidence` — is never joined, so confidence cannot reach this endpoint at all.
Stronger than "nothing branches on it". Enforced by an AST test asserting
`vocabulary_repository.py` never names `AnnotationProvenance`, mirroring
`test_annotation_write_repository_isolation.py`. The ordering that carries this prohibition into the
returned sequence is D5.

### D5 — Result ordering

The returned sequence carries the total order **`occurrence_count DESC, lemma, pos`**.

It is applied **after** the leg-A/leg-B merge (D1), not inside leg A's SQL. Leg B moves rows between
groups, so an order established before the merge is not the order returned.

`NULL` sorts **before** any string in both key halves, matching SQLite's ASC ordering and the physical
order of `ix_occurrence_book_lemma_pos` (D2, which relies on the same property). That position is
fixed and documented here, so a `NULL`-lemma group and a `NULL`-POS group each have one defined place
among their tied peers and the order is total, never partial. `occurrence_count` alone is not a total
order at this scale: 34,827 groups over a Zipfian distribution produce many ties, which `lemma` then
`pos` break.

The sort key is never a confidence value (SPEC-003 C6, spec §2.4 K1, D4) — it is frequency, then the
group key itself.

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

### Corrective slice — POS selector

The optional `pos` query parameter accepts one of `UPOS_TAGS` or the literal
`null`. `null` selects groups whose `pos` field is JSON `null`; omitting the
parameter leaves the result unfiltered. FastAPI validates the parameter before
the route runs, so an invalid selector uses the shared `INVALID_REQUEST`
envelope. The route filters the completed group sequence by its `pos` key,
leaving each included group's `occurrence_count` unchanged.

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
| Bench | 688k ceiling: **asserts** body size and p95 latency against §Response budget; **records** group count | `@pytest.mark.bench`, non-gating (per `test_import_bench.py`) |
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
- [ ] Journal mode (D1a). D1's one-snapshot obligation is satisfiable under
      `PRAGMA journal_mode=WAL` — measured: correct snapshot, interleaved writer committing in
      0.001 s — and not under the rollback journal `create_engine_from_url` leaves in place. WAL is
      the only mode measured to satisfy it; nothing else has been measured, and WAL's own cost on
      the annotate write path (156–281 s at the ceiling, D2) has not been measured either. Choosing
      the mode changes every session in the process, not only this read, so it is a decision for the
      snapshot-isolation work unit and not for WU2.

## Deviation From Proposal

The proposal states `AnnotationTable.tsx` is untouched *and* that the new component reuses
`UPOS_LABELS`. `UPOS_LABELS` is a private const inside `AnnotationTable.tsx:37-55` and is not exported,
so both cannot hold. Resolution: extract `UPOS_LABELS`/`posLabel` verbatim into
`components/uposLabels.ts` and import it in both components. `AnnotationTable.tsx`'s rendering,
behaviour, and tests are unchanged — only the definition site moves. The alternative, duplicating the
17-tag map, creates a drift risk between two label tables with no compensating benefit.

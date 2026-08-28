# Tasks: Vocabulary Browser (005-vocabulary-browser)

## Review Workload Forecast

Independent estimate below, built by comparing each new/edited file against the closest
shipped comparable in THIS repo (not a generic per-layer guess). Comparables used: file sizes
are actual `wc -l` counts as of this session.

| Field | Value |
|-------|-------|
| Estimated changed lines (slice 1, this document's scope) | **~2,270-2,335** (range from two independent groupings below) |
| Proposal's own estimate | ~400-430 |
| Design's own estimate | ~1,080 |
| This estimate vs. proposal | **~5.3x** |
| This estimate vs. design | **~2.1x** |
| 400-line budget risk | **High** |
| Chained PRs recommended | **Yes** |
| Suggested split | 10 work units, see below — no single unit stays observable AND under 400 alone |
| Delivery strategy | `ask-on-risk` |
| Chain strategy | **pending — human decision required** (Stacked-to-main recommended; Feature Branch Chain as alternative) |

**Decision needed before apply: Yes**
**Chained PRs recommended: Yes**
**Chain strategy: pending**
**400-line budget risk: High**

### Why this estimate differs from both prior ones

The proposal's ~400-430 assumed one PR could cover repository + endpoint + minimal frontend.
The design's ~1,080 is closer but is a top-down per-layer guess. Grounding line-by-line
against real files in this repo pushes the number higher, mainly because:

- `test_annotation_write_repository_isolation.py` (the closest precedent for a structural
  no-reference guard) is **465 lines** for one guard with its mutation-check battery.
  REQ-005-008 needs a **new, different** guard (read permitted, write forbidden) — not a
  copy of that file, but comparable in kind. REQ-005-007 needs a **second**, separate
  structural absence guard (confidence-action). The design's ~430 backend-test figure
  implicitly assumes these are small additions; they are each new AST-walking test modules.
- `test_annotate_import_properties.py` (Hypothesis precedent) is **553 lines**; even a
  narrower single-property V3≡`resolve_effective` test is unlikely to land under 100-120.
- `test_annotation_route.py` (API-level tests for one capability) is **269 lines**;
  `test_annotation_dependencies.py` is **73**. The design's ~330 for "application + DTOs +
  route + schema + API tests" (backend PR B) does not leave enough room for the API test
  file alone once counted at this repo's real density.
- Two backend guard-map files (`test_no_lemma_naming.py`, `test_no_confidence_action_or_
  propn_filter.py`) and one frontend one (`no-linguistic-rules.test.ts`, `no-lemma-naming.
  test.ts`) all require edits across up to 4 separate allow-list locations
  (`_LEMMA_OWNING_FILES`, `_SCHEMA_OWNERS`+`_EXPECTED_SCHEMA_FILES`, `_OPENAPI_OWNERS`,
  `_EXPECTED_FILES`/`_CONFIDENCE_ACTION_PATTERN`) — each a small edit, but there are many.
- REQ-005-011's bench needs a **new** synthetic occurrence-level corpus generator (Zipfian
  lemma distribution, homograph minority, seeded corrections) — `_bench_corpus.py`'s
  existing 62-line ASCII-text generator does not produce annotated occurrences and cannot
  be reused as-is.

**Where the design may have over-counted:** none identified. The design's ~1,080 undercounts,
it does not overcount — every layer it names turned out larger against real comparables, and
it did not budget a line for the two structural guards individually, the bench corpus
generator, or the traceability rows (small, ~15 lines, but omitted).

**A genuine finding, not just recount:** `test_no_confidence_action_or_propn_filter.py:35`'s
`_CONFIDENCE_ACTION_PATTERN` — `"threshold|filter_by_confidence|min_confidence|sort_by_
confidence"` — does **not** contain `mean_confidence`. AC-005-07's required mutation ("a
`mean_confidence` property on the group shape... produces a violation") would not be caught by
the existing pattern as shipped today. This is a real gap the design did not flag; task T19
below extends the pattern before the mutation-check tests are written.

### Suggested Work Units

| Unit | Goal | Est. lines | Observable | Rollback boundary |
|------|------|-----------|------------|-------------------|
| WU1 | Additive index migration + reversibility proof | ~140 | No | `alembic downgrade -1`; delete `0004_*.py`, revert `models.py` index line |
| WU2 | Repository core query (V3 hybrid) + Hypothesis equivalence proof | ~270 | No | Delete `vocabulary_repository.py` and its property test |
| WU3 | Two structural absence guards (no-`AnnotationProvenance`, read/write split) + confidence-guard fix | ~390 | No | Delete the two new guard test files; revert the pattern/`_EXPECTED_FILES` edit |
| WU4 | Repository integration tests (NULL buckets, corrections, unknown/empty) | ~200 | No | Delete the integration test file |
| WU5 | Application layer (port + use case) + DTOs + their tests | ~285 | No | Delete `application/vocabulary/`, `api/dtos/vocabulary.py`, their tests |
| WU6 | Route + schema + wiring + API tests | ~400 | **Yes** (HTTP/OpenAPI, no UI yet) | Remove router registration in `main.py`; delete route/schema/DTO files |
| WU7 | Benchmark (asserts the two anchored bounds, corpus generator) | ~250 | No | Delete both new bench files (`@pytest.mark.bench`, non-gating) |
| WU8 | Frontend extraction (`uposLabels.ts`) + types/client + guard-map edits | ~150 | No | Revert `AnnotationTable.tsx` diff; delete extracted files |
| WU9 | `VocabularyBrowser.tsx` + wiring + E2E | ~235 | **Yes** (full user-visible slice) | Revert `ImportPage.tsx` wiring; delete component/test/E2E spec |
| WU10 | Traceability matrix rows | ~15 | No | Revert matrix rows |

Focused test commands and runtime harness per unit are listed under each phase below.

### Honest answer on the 400-line floor

**No unit that is independently user-observable (Art. III) stays under 400 lines.** WU6 is the
first HTTP-observable unit (endpoint reachable, verifiable by `curl`/OpenAPI) and lands at
~400 — right at the edge, not comfortably under it. WU9 is the first UI-observable unit and
is a comfortable ~235. Every unit strictly under 400 (WU1, WU2, WU4, WU5, WU7, WU8, WU10) is
backend-internal or non-shipped-surface work with no observable output by itself. The floor
for *a single fully-observable slice* (repository → route → frontend, WU2+WU5+WU6+WU9) is
~1,190 lines — well above 400. Ten work units is the finest useful split found; splitting WU6
or WU3 further (e.g. route+schema separate from API tests) is possible but adds PRs without
changing the fundamental floor.

### Chain strategy — human decision required

Every work unit through WU9 is strictly additive: no shipped route, contract, or table column
is modified (P2, `annotation.v1.json` byte-identical). Nothing in main after WU1-WU8 lands
changes behavior for an existing user — the new code is unreachable until WU6 registers the
router and WU9 wires the UI. This makes **Stacked PRs to main** viable and is the recommended
default: each unit merges to main in order, CI proves it, and the capability activates only at
WU6 (API) and WU9 (UI).

**Alternative — Feature Branch Chain**: if the team prefers to hold the whole capability off
`main` until it is fully reviewable end to end (e.g. to avoid an inactive endpoint sitting on
`main` for several PR cycles), use a tracker branch: WU1 targets the tracker, WU2 targets
WU1's branch, and so on through WU10; only the tracker merges to `main`.

Both are legitimate. This document does not choose for the team — `sdd-apply` should not start
until the human confirms `stacked-to-main` or `feature-branch-chain` (or accepts `size:
exception` for a different grouping).

---

## Phase 1 — Additive index migration (WU1, ~140 lines)

Focused test: `cd apps/api && uv run pytest tests/integration/test_alembic_0004.py -q`
Runtime harness: `cd apps/api && uv run alembic upgrade head && uv run alembic downgrade -1` (both must exit 0)

- [x] T1 [TEST] Write `apps/api/tests/integration/test_alembic_0004.py` — mirrors `test_alembic_0003.py`: upgrade adds `ix_occurrence_book_lemma_pos` on `occurrence(book_id, lemma, pos)` (`PRAGMA index_list`); downgrade removes it and returns `alembic_version` to `0003_annotation`. RED: file/revision does not exist.
- [x] T2 [MIGRATION] Create `apps/api/migrations/versions/0004_vocabulary_group_index.py`: `revision="0004_vocabulary_group_index"`, `down_revision="0003_annotation"`; `upgrade()` → `op.create_index("ix_occurrence_book_lemma_pos", "occurrence", ["book_id", "lemma", "pos"])`; `downgrade()` → `op.drop_index(...)`.
- [x] T3 [TEST] Extend `apps/api/tests/unit/test_no_lemma_naming.py::_LEMMA_OWNING_FILES` (`:169-190`) with `"migrations/versions/0004_vocabulary_group_index.py": frozenset({"lemma"})` — the migration's column-list literal `"lemma"` would otherwise fail the existing lemma-naming guard. **Deviation**: also required adding the exact index-name literal `"ix_occurrence_book_lemma_pos"` to `_ALLOWED_LEMMA_SYMBOLS` and its owning-file entries (`models.py`, `0004_vocabulary_group_index.py`) — `_FORBIDDEN` is a substring match, not word-bounded, so the index name itself (not just the bare `"lemma"` column-list literal) trips the guard. See apply-progress for detail.
- [x] T4 [IMPL] Modify `apps/api/src/wheel_vocabulary/infrastructure/persistence/models.py` (`Occurrence.__table_args__`, `:72-74`): add `Index("ix_occurrence_book_lemma_pos", "book_id", "lemma", "pos")` alongside the existing `ix_occurrence_book_norm_raw`.
- [x] T5 [TEST] Run T1 green (AC-005-09 scenario 3); run the runtime harness above to prove both directions exit 0.

## Phase 2 — Vocabulary repository core (WU2, ~270 lines)

Depends on: Phase 1.
Focused test: `cd apps/api && uv run pytest tests/unit/test_vocabulary_repository_properties.py -q`

- [x] T6 [TEST] Write a Hypothesis strategy over `(automatic, corrected)` `(lemma, pos)` pairs (`apps/api/tests/unit/test_vocabulary_repository_properties.py`), asserting the repository's per-occurrence effective resolution agrees with `domain.annotation.resolve_effective` (`:132`) on every generated case (AC-005-02 scenario 4). RED: repository does not exist.
- [x] T7 [TEST] Extend the same property test module: given generated seeded corrections, V3's group-by-group counts equal a naive Python `groupby` over `resolve_effective`-resolved values, value for value.
- [x] T8 [IMPL] Create `apps/api/src/wheel_vocabulary/infrastructure/persistence/vocabulary_repository.py`: `@dataclass(frozen=True, slots=True) VocabularyGroup(lemma: str | None, pos: str | None, occurrence_count: int)` and `SqlAlchemyVocabularyReadRepository.groups(book_id)` implementing design D1's leg A (raw `GROUP BY o.lemma, o.pos`) + leg B (corrected-occurrence delta) merged via `resolve_effective`, one `Session` for both legs. Existence check mirrors `annotation_repository.py::read`'s `session.get(Book, book_id) is None → return None` pattern. **The returned sequence MUST carry design D5's total order `occurrence_count DESC, lemma, pos`, applied after the leg-A/leg-B merge, not inside leg A's SQL** — leg B moves rows between groups, so an order established before the merge is not the order returned. `NULL` sorts before any string in both key halves (design D5), so the order is total, never partial (§2.1 G5, AC-005-01 scenario 3).
- [x] T9 [TEST] Extend `test_no_lemma_naming.py::_LEMMA_OWNING_FILES` with `"infrastructure/persistence/vocabulary_repository.py": frozenset({"lemma"})`.
- [x] T10 [TEST] Run T6/T7 green; run the full backend suite to confirm no regression in `annotation_repository.py`'s existing tests (untouched file).
- [x] T11 [REFACTOR] If leg A/leg B merge logic duplicates code across the two Hypothesis assertions, extract a shared `_naive_groups(...)` test helper — no production-code change.

## Phase 3 — Structural absence guards (WU3, ~390 lines)

Depends on: Phase 2.
Focused test: `cd apps/api && uv run pytest tests/unit/test_vocabulary_repository_isolation.py tests/unit/test_vocabulary_write_guard.py tests/unit/test_no_confidence_action_or_propn_filter.py -q`

- T12 [TEST] Write `apps/api/tests/unit/test_vocabulary_repository_isolation.py`: AST-walk `vocabulary_repository.py` and assert it never names `AnnotationProvenance` (D4/C6) — narrower than `test_annotation_write_repository_isolation.py`, one forbidden name, one mutation check (temporarily import `AnnotationProvenance`, observe the failure, revert), one non-vacuity assertion. RED: repository does not join provenance yet, so this test is vacuous until T8 lands — sequence after T8, before archiving Phase 3.
- T13 [TEST] Write `apps/api/tests/unit/test_vocabulary_write_guard.py` — the REQ-005-008 guard that MUST differ from `test_annotation_write_repository_isolation.py`: it permits `select(ManualCorrection...)`/`ManualCorrection.field` reads and forbids only `insert(ManualCorrection)`, `update(ManualCorrection)`, `delete(ManualCorrection)` SQLAlchemy calls and raw `INSERT/UPDATE/DELETE ... manual_correction` SQL text, scanned across every module this capability introduces. Do NOT reuse or extend the existing no-reference guard, and do NOT exempt this capability's modules from it (SPEC-003 §3.4 W1) — this is a distinct, narrower rule (AMB-3).
- T14 [TEST] Extend T13's module with the two required mutation checks (AC-005-08 scenario 3): a synthetic `insert(ManualCorrection, ...)` and a synthetic `delete(ManualCorrection)`, each in turn, each asserted to produce a violation with the observed failure text recorded in the test docstring.
- T15 [TEST] Extend T13's module with the boundary control (AC-005-08 scenario 4/M3): the same forbidden write statement placed in a module OUTSIDE this capability still produces a violation.
- T16 [IMPL] Implement the write-detector in `test_vocabulary_write_guard.py` itself (test-only code, no production module): AST `ast.Call` matching on `insert`/`update`/`delete` imported from `sqlalchemy` with a `ManualCorrection` argument, plus a substring scan over string/`BinOp`-folded literals for `insert into manual_correction`/`update manual_correction`/`delete from manual_correction` (case-insensitive).
- T17 [TEST] Write the vocabulary-repository read scenario (AC-005-08 scenario 2): seed a `ManualCorrection` row, run `groups()`, assert `manual_correction` row count and bytes are unchanged afterwards.
- T18 [TEST] Extend `apps/api/tests/unit/test_no_confidence_action_or_propn_filter.py::_EXPECTED_FILES` (`:37-45`) with `infrastructure/persistence/vocabulary_repository.py`, `application/vocabulary/use_cases.py`, `api/routes/vocabulary.py` — non-vacuity, no code change yet.
- T19 [IMPL] Extend `_CONFIDENCE_ACTION_PATTERN` (`:35`) to add `mean_confidence` (see forecast note above — the current pattern does not catch it). Verify `pos_confidence`/`lemma_confidence` identifiers package-wide still pass (the added term is a distinct substring, no false positive).
- T20 [TEST] Add three synthetic mutation-check tests to the same module mirroring `test_a_confidence_threshold_helper_would_be_caught`: a `min_confidence` query-parameter-shaped identifier, a `mean_confidence` property-shaped identifier, and a `sort_by_confidence` helper — each in turn asserted to violate (AC-005-07 scenario 4).
- T21 [TEST] Run all of Phase 3 green; run the full backend suite once to confirm the confidence-pattern extension does not break any existing test.

## Phase 4 — Repository integration tests (WU4, ~200 lines)

Depends on: Phase 2.
Focused test: `cd apps/api && uv run pytest tests/integration/test_vocabulary_repository.py -q`

- T22 [TEST] Write `apps/api/tests/integration/test_vocabulary_repository.py`: homograph produces two groups with separate counts (AC-005-01); a seeded `ManualCorrection` row (inserted directly via the ORM — no writer exists yet, per REQ-005-002's "testable now" note) moves an occurrence between groups and can vacate a group entirely (AC-005-02 scenarios 1-3); an all-`NULL` import returns exactly one `(null, null)` group equal to the occurrence count (AC-005-03 scenario 1); a lemma with `NULL` POS gets its own bucket (AC-005-03 scenario 2); unknown `book_id` returns `None`; an existing import with zero occurrences returns `[]`, not `None` (AC-005-05 scenario 3); **the returned sequence equals a literal expected ordering written out in the test** — seed a fixture whose correct design-D5 order (`occurrence_count DESC, lemma, pos`, `NULL` before any string in both halves) is known in advance, write that order out as a literal list, and assert equality element-for-element; **and** two consecutive `groups(book_id)` calls with no intervening write return sequences equal element-for-element including order (AC-005-01 scenario 3). The repeat-read check alone proves stability, not correctness — insertion order, ascending count, or `NULL` in the wrong half-position is stable and passes it, so both assertions are required. Assert on the ordered sequence, never on a set or a sorted copy, or the test cannot fail on a reordering. Seed at least two groups sharing an `occurrence_count` so the tie-break on `lemma`/`pos` is exercised rather than accidentally satisfied by distinct counts, and at least one `NULL`-lemma and one `NULL`-POS group so `NULL`'s position is pinned by the literal order.
- T23 [IMPL] Fix any repository defect T22 surfaces (expected to be minimal — logic already proven by Phase 2's property tests).
- T24 [TEST] Run T22 green; run `uv run pytest --cov=wheel_vocabulary --cov-report=term-missing` for `vocabulary_repository.py` and confirm ≥90% (`domain`/`application` bar — this file sits in `infrastructure`, so confirm it clears the global 80% floor at minimum and does not drag the run below Art. II).

## Phase 5 — Application layer + DTOs (WU5, ~285 lines)

Depends on: Phase 2.
Focused test: `cd apps/api && uv run pytest tests/unit/test_vocabulary_ports.py tests/unit/test_vocabulary_dtos.py tests/integration/test_vocabulary_dependencies.py -q`

- T25 [TEST] Write `apps/api/tests/unit/test_vocabulary_ports.py`: a plain stdlib double satisfies `VocabularyReader` structurally (mirrors `test_annotation_ports.py`'s precedent for `AnnotationReader`).
- T26 [IMPL] Create `apps/api/src/wheel_vocabulary/application/vocabulary/__init__.py` (module docstring, mirrors `application/annotation/__init__.py`) and `ports.py`: `VocabularyReader` Protocol with `groups(book_id: int) -> Sequence[VocabularyGroup] | None`.
- T27 [IMPL] Create `apps/api/src/wheel_vocabulary/application/vocabulary/use_cases.py`: `ReadVocabulary.execute(book_id) -> Sequence[VocabularyGroup] | None`, mirrors `ReadImport` (`application/imports/use_cases.py:218-241`) — a thin pass-through, no aggregation logic duplicated here (E3).
- T28 [TEST] Extend `test_no_lemma_naming.py::_LEMMA_OWNING_FILES` with `"application/vocabulary/ports.py"` and `"application/vocabulary/use_cases.py"`, each `frozenset({"lemma"})`.
- T29 [TEST] Write `apps/api/tests/unit/test_vocabulary_dtos.py`: `VocabularyGroupResponse`/`VocabularyResponse` both reject unknown fields (`extra="forbid"`, mirrors `test_annotation_contract.py`'s DTO-strictness pattern).
- T30 [IMPL] Create `apps/api/src/wheel_vocabulary/api/dtos/vocabulary.py`: `VocabularyGroupResponse(lemma: str | None = Field(title="lemma"), pos: str | None, occurrence_count: int)`, `VocabularyResponse(id: int, group_count: int, total_occurrence_count: int, groups: list[VocabularyGroupResponse])`.
- T31 [TEST] Extend `test_no_lemma_naming.py::_LEMMA_OWNING_FILES` with `"api/dtos/vocabulary.py": frozenset({"lemma"})`.
- T32 [TEST] Write `apps/api/tests/integration/test_vocabulary_dependencies.py` (mirrors `test_annotation_dependencies.py`, 73 lines): `get_vocabulary_repository`/`get_read_vocabulary` resolve against a real engine.
- T33 [IMPL] Extend `apps/api/src/wheel_vocabulary/api/dependencies.py`: add `get_vocabulary_repository` (mirrors `get_annotation_read_repository`) and `get_read_vocabulary` (mirrors `get_read_import`), both added to `__all__`.
- T34 [TEST] Run Phase 5 green.

## Phase 6 — Route + schema + wiring + API tests (WU6, ~400 lines)

Depends on: Phase 5.
Focused test: `cd apps/api && uv run pytest tests/api/test_vocabulary_route.py -q`
Runtime harness: `cd apps/api && uv run uvicorn wheel_vocabulary.api.main:create_app --factory & curl -s localhost:8000/api/v1/imports/1/vocabulary` (manual smoke; kill the server after)

- T35 [TEST] Write `apps/api/tests/api/test_vocabulary_route.py` (mirrors `test_annotation_route.py`): `GET /api/v1/imports/{id}/vocabulary` returns 200 with the design's shape for a seeded import; unknown id → 404 `IMPORT_NOT_FOUND` (AC-005-05); an error body contains no textual form, lemma, stack trace, or path (REQ-003-019 inherited); `annotation.v1.json` byte-identical before/after (AC-005-04); served OpenAPI lists the new path alongside the two unchanged annotation operations; **the parsed `groups` list equals a literal expected ordering** — seed a fixture whose correct design-D5 order (`occurrence_count DESC, lemma, pos`, `NULL` before any string in both halves) is known in advance and assert the parsed list equals that literal, positionally; **and** two identical `GET` requests with no intervening write return equal response bodies including `groups` order (AC-005-01 scenario 3). The repeat-request check proves serialization stability; the literal-order check proves the order is the specified one, which a stable-but-wrong order would otherwise pass. Compare positionally, never as a set or a sorted copy. Seed tied `occurrence_count` groups and at least one `NULL` key half so the tie-break and `NULL`'s position are proved at the wire level and not only inside the repository.
- T36 [IMPL] Create `apps/api/src/wheel_vocabulary/api/schemas/vocabulary.v1.json` (Draft 2020-12, mirrors `annotation.v1.json`'s shape): `id`, `group_count`, `total_occurrence_count`, `groups[]` with `lemma`/`pos`/`occurrence_count`.
- T37 [TEST] Extend `test_no_lemma_naming.py`: add `"vocabulary.v1.json"` to `_EXPECTED_SCHEMA_FILES` (`:406`); add a `_SCHEMA_OWNERS["vocabulary.v1.json"]` entry (`:219-229`) with `OwningDefinition` scoped to the group shape, `exempt={"lemma"}`; extend `_OPENAPI_OWNERS` (`:230-236`) with a second `OwningDefinition` for the served `VocabularyGroupResponse` component.
- T38 [IMPL] Create `apps/api/src/wheel_vocabulary/api/routes/vocabulary.py`: `GET /api/v1/imports/{import_id}/vocabulary`, thin adapter over `ReadVocabulary`, mirrors `read_import`/`read_annotation`'s shape (`X-Schema-Version` header, `ImportNotFoundError` on `None`).
- T39 [TEST] Extend `test_no_lemma_naming.py::_LEMMA_OWNING_FILES` with `"api/routes/vocabulary.py": frozenset({"lemma"})`.
- T40 [IMPL] Register the router in `apps/api/src/wheel_vocabulary/api/main.py` (`app.include_router(vocabulary_router_module.router)`, alongside the existing three).
- T41 [TEST] Run T35 green; re-run the full `003-lemmatization-pos` acceptance suite unweakened (AC-005-04 scenario 2); run the runtime harness once manually.

## Phase 7 — Benchmark (WU7, ~250 lines)

Depends on: Phase 6 (AC-005-11 measures through the shipped endpoint, mirroring `test_import_bench.py`'s pattern).
Focused test: `cd apps/api && uv run pytest tests/integration/test_vocabulary_bench.py -m bench -q`

- T42 [DOC] Verify `design.md` §Response budget states the two numeric bounds — response body **≤ 4 MiB (4,194,304 bytes)** and latency **≤ 1000 ms p95** — and that each names an anchor outside this capability's own measurements (AC-005-11 scenario 1). Recompute the body-size derivation: it must equal `max_import_size_bytes: int = 4_194_304` (`apps/api/src/wheel_vocabulary/infrastructure/settings.py:32`) exactly, 4,194,304 = 4,194,304. Confirm the latency bound is stated as a **judgment** in those words with what it protects named, not presented as arithmetic. Neither bound may cite V3's own results (533 ms p95, 1.97 MiB) as its justification — a bound restated from the measurement it is meant to bound satisfies nothing. T44 asserts against these two bounds and no others; group cardinality has no bound and is recorded, not asserted.
- T43 [TEST] Create `apps/api/tests/integration/_vocabulary_bench_corpus.py`: a synthetic occurrence-level generator producing a Zipfian lemma distribution (30k lemmas), a 12% homograph minority, 2% unannotated occurrences, and N seeded `manual_correction` rows — occurrence-level, unlike `_bench_corpus.py`'s ASCII-text generator, which cannot be reused as-is.
- T44 [TEST] Write `apps/api/tests/integration/test_vocabulary_bench.py` (`@pytest.mark.bench`, mirrors `test_import_bench.py`'s deterministic-invariants-always-fail-CI / wall-clock-behind-`WHEEL_BENCH_STRICT` split): at 688,000 occurrences, **assert** response body size ≤ 4,194,304 bytes and **p95** latency ≤ 1000 ms — the two bounds §Response budget names — and **record** group count as a reported observation with no assertion on it, because the budget leaves it unbounded (AC-005-11 scenario 2). Latency is measured and asserted as p95 across runs, never p50; V3's p50 is 389 ms and its p95 is 533 ms, and only the p95 is the bounded quantity.
- T45 [TEST] Extend T44 with the mutated-bound failure check (AC-005-11 scenario 3): lower each named bound below its measured value in turn — 4,194,304 bytes to below 2,063,621, and 1000 ms p95 to below 533 ms p95 — and confirm the test fails on each.
- T46 [TEST] Run T44 green (default CI invocation); optionally run with `WHEEL_BENCH_STRICT=1` locally to record wall-clock numbers.

## Phase 8 — Frontend extraction (WU8, ~150 lines)

Depends on: none (can run parallel to Phases 1-7; only needs `AnnotationTable.tsx` as it exists today).
Focused test: `cd apps/web && pnpm run test -- uposLabels`

- T47 [TEST] Write `apps/web/tests/components/uposLabels.test.ts`: the extracted `posLabel`/`UPOS_LABELS` map is total over the 17-tag UPOS set and degrades an unmapped tag to the raw value. RED: `uposLabels.ts` does not exist.
- T48 [IMPL] Create `apps/web/src/components/uposLabels.ts`: move `UPOS_LABELS` and `posLabel` verbatim from `AnnotationTable.tsx:37-62` — no behavior change, only the definition site moves (design's Deviation section).
- T49 [IMPL] Modify `apps/web/src/components/AnnotationTable.tsx`: delete the moved `UPOS_LABELS`/`posLabel` definitions, import `posLabel` from `./uposLabels`. `AnnotationTable.test.tsx` MUST pass unchanged, byte-for-byte behavior (AC-005-10 scenario 4).
- T50 [IMPL] Create `apps/web/src/types/vocabulary.ts`: `VocabularyGroup { lemma: string | null; pos: string | null; occurrence_count: number }`, `VocabularyResult { id: number; group_count: number; total_occurrence_count: number; groups: VocabularyGroup[] }` (mirrors `types/annotation.ts`).
- T51 [IMPL] Create `apps/web/src/api/vocabulary.ts`: `getVocabulary(importId)` (mirrors `getAnnotation` in `api/annotation.ts`, single `GET`, no POST).
- T52 [TEST] Extend `apps/web/tests/contracts/no-lemma-naming.test.ts::LEMMA_OWNING_FILES` (`:60-68`) with `"src/types/vocabulary.ts": new Set(["lemma"])` **only**. Do NOT register `VocabularyBrowser.tsx` here — no task creates it until T56 in Phase 9, and these manifests are enumerated and checked, so an entry pointing at a missing file fails the guard. Its registration is T57.
- T53 [TEST] Extend `apps/web/tests/contracts/no-linguistic-rules.test.ts::FRONTEND_FEATURE_MODULES` (`:28-38`) with **the three files this phase creates** — `src/types/vocabulary.ts`, `src/api/vocabulary.ts`, `src/components/uposLabels.ts`; extend `FEATURE_NAME_PATTERN` (`:40`) to also match `[Vv]ocab`. The component is added to this manifest by T57, not here.
- T54 [TEST] Run T47 and the existing `AnnotationTable.test.tsx` green; run `pnpm run typecheck` and `pnpm run lint`.

## Phase 9 — VocabularyBrowser + wiring + E2E (WU9, ~235 lines)

Depends on: Phase 6 (needs the live endpoint contract) and Phase 8 (needs `uposLabels.ts`, `types/vocabulary.ts`, `api/vocabulary.ts`).
Focused test: `cd apps/web && pnpm run test -- VocabularyBrowser`
Runtime harness: `cd apps/web && pnpm exec playwright test e2e/vocabulary.spec.ts`

- T55 [TEST] Write `apps/web/tests/components/VocabularyBrowser.test.tsx` (mirrors `AnnotationTable.test.tsx`): a mocked response renders lemma/pos/count verbatim (AC-005-10 scenario 2); a `(null, null)` group, a `(lemma, null)` group, and a tagged group each carry a distinct text label (AC-005-03 scenario 4); an unmapped POS tag degrades to the raw tag, no blank cell (AC-005-10 scenario 3); zero interactive controls submit a correction (AC-005-08 scenario 5).
- T56 [IMPL] Create `apps/web/src/components/VocabularyBrowser.tsx` (mirrors `AnnotationTable.tsx`'s shape): renders `result.groups` using `posLabel` from `uposLabels.ts`; no grouping, counting, lemmatization, tagging, normalization, or precedence logic (REQ-005-010); `NULL` buckets rendered with an explicit distinguishing label, no colour-only signal (N4, Art. IX.4).
- T57 [TEST] Register the component in both frontend guard manifests now that T56 has created it: add `"src/components/VocabularyBrowser.tsx": new Set(["lemma"])` to `no-lemma-naming.test.ts::LEMMA_OWNING_FILES` (`:60-68`) and add the same path to `no-linguistic-rules.test.ts::FRONTEND_FEATURE_MODULES` (`:28-38`). Then run both guards: zero matches for grouping/lemmatization/tagging/normalization/precedence identifiers (AC-005-10 scenario 1). Registering before T56 would point a checked manifest at a file that does not exist — that is why these two entries are here and not in Phase 8.
- T58 [IMPL] Modify `apps/web/src/pages/ImportPage.tsx`: add a "Ver vocabulario" trigger and state slice (mirrors the existing `handleAnnotate`/`AnnotateState` pattern, `:14-50`), calling `getVocabulary(result.id)` and rendering `<VocabularyBrowser>` on success.
- T59 [TEST] Write `apps/web/e2e/vocabulary.spec.ts` (mirrors `annotation.spec.ts`, 25 lines): import → annotate → view vocabulary → grouped table with counts is visible.
- T60 [TEST] Run T55/T57 green; run the E2E harness; run `pnpm run typecheck`, `pnpm run lint`, `pnpm run test:coverage`.

## Phase 10 — Traceability (WU10, ~15 lines)

Depends on: every requirement's implementing phase having landed (this task can be split per-requirement and attached to the PR that closes each requirement, per work-unit-commits — listed together here for completeness).

- T61 [DOC] Add 11 rows to `docs/traceability-matrix.md` — `REQ-005-001` through `REQ-005-011`, each citing this spec's path + its `AC-005-##`, the test file(s)/node(s) from the phases above, the task IDs (`T#`), and status. `REQ-005-006` (POS filter, slice 2) MAY carry an unfulfilled status until slice 2 ships (§1, §5 AMB-5) — every other row MUST be `Cumplido` before this capability is archived.
- T62 [DOC] Run `cd apps/api && uv run pytest tests/unit/test_traceability.py -q` to confirm every cited Python test node resolves against pytest collection (`:190`) and no cell is a placeholder (`:19`).

---

## Notes on requirement coverage

Every requirement `REQ-005-001`…`REQ-005-011` maps to at least one task above:
001→T8,T22,T35 · 002→T6,T7,T22 · 003→T22,T55 · 004→T35,T41 · 005→T22,T35 · 006→**slice 2, not in
this document** · 007→T18-T20 · 008→T12-T17 · 009→T1-T5,T22 · 010→T49,T55-T57 · 011→T42-T46.

`REQ-005-001` carries three tasks because its ordering-stability scenario is proved at two levels:
T8 establishes the total order, T22 asserts it survives two repository reads, and T35 asserts it
survives serialization across two HTTP requests.
`docs/product-vision.md` roadmap item 5 stays incomplete until slice 2 (`REQ-005-006`) ships,
per spec §1/§5 AMB-5 — not a gap in this task list.

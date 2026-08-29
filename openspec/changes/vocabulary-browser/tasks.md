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
| Suggested split | 11 work units, see below — no single unit stays observable AND under 400 alone. WU2b was carved out of WU2 after apply (see §Snapshot isolation carved out of WU2). WU3 was briefly shrunk and split into WU3a/WU3b/WU3c after Judgment Day round 4 on the premise that an AST pass cannot verify a `Session` receiver; round 6 falsified that premise and the split was withdrawn — see Phase 3's split-and-withdrawal note |
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
| WU2 | Repository core query (V3 hybrid) + Hypothesis equivalence proof, sequential reads only | ~270 | No | Delete `vocabulary_repository.py` and its property test |
| WU2b | Snapshot isolation across the two legs + the journal-mode decision | unestimated | No | Revert the journal-mode setting and the `BEGIN`; delete the snapshot regression test |
| WU3 | Two structural absence guards (no-`AnnotationProvenance`, read/write split) + confidence-guard fix | ~390 | No | Delete the two new guard test files; revert the pattern/`_EXPECTED_FILES` edit |
| WU4 | Repository integration tests (NULL buckets, corrections, unknown/empty) | ~200 | No | Delete the integration test file |
| WU5 | Application layer (port + use case) + DTOs + their tests | ~285 | No | Delete `application/vocabulary/`, `api/dtos/vocabulary.py`, their tests |
| WU6 | Route + schema + wiring + API tests | ~400 | **Yes** (HTTP/OpenAPI, no UI yet) | Remove router registration in `main.py`; delete route/schema/DTO files |
| WU7 | Benchmark (asserts the two anchored bounds, corpus generator) | ~250 | No | Delete both new bench files (`@pytest.mark.bench`, non-gating) |
| WU8 | Frontend extraction (`uposLabels.ts`) + types/client + guard-map edits | ~150 | No | Revert `AnnotationTable.tsx` diff; delete extracted files |
| WU9 | `VocabularyBrowser.tsx` + wiring + E2E | ~235 | **Yes** (full user-visible slice) | Revert `ImportPage.tsx` wiring; delete component/test/E2E spec |
| WU10 | Traceability matrix rows | ~15 | No | Revert matrix rows |

Focused test commands and runtime harness per unit are listed under each phase below.

### Snapshot isolation carved out of WU2

WU2 shipped at `ac5b4b9` and an adversarial dual-judge review found that its two legs do not observe
one database snapshot. T8 below required "one `Session` for both legs", quoting design D1; sharing a
`Session` does not produce a snapshot, because pysqlite emits `BEGIN` only before `INSERT`, `UPDATE`
and `DELETE` and never before a plain `SELECT`. Two fixes were implemented and both were rejected by
re-judgment — an engine-level listener pair that broke `SqlAlchemyBookRepository.delete()`, and a
read-scoped `BEGIN` that starves unrelated writers past the 5 s pysqlite busy timeout. The
measurements and the query-level detail are in `design.md` §D1a; the round-2 implementation and its
test are preserved on `feat/vocabulary-read-snapshot-isolation` at `ed7e9f3`.

WU2b owns the fix. It is unestimated because its size depends on the journal-mode decision, which is
open (`design.md` §Open Questions): under `PRAGMA journal_mode=WAL` the round-2 implementation
already returns the correct snapshot with the interleaved writer committing in 0.001 s, and the mode
applies to every session in the process, not to this read alone. WU2b's task list is written once
that decision is made. Two obligations are already fixed regardless of which mode is chosen:

- The regression test MUST assert the returned groups, not the locking. Reverting the fix must fail
  it on a group comparison; a test that fails first on `OperationalError` proves mutual exclusion and
  never reaches the corruption.
- The interleaved write MUST commit. The preserved test's writer is rolled back, so the post-run
  database dump still reads `[(1,'alpha'), (2,'beta')]` while the test's name and docstring claim a
  committed write.

No `REQ-005` requirement covers this — see spec §5 `AMB-10`. WU2b closes an obligation that lives in
the design, and every `AC-005` scenario stays verifiable without it because each names a read with no
interleaved committed write.

### Honest answer on the 400-line floor

**No unit that is independently user-observable (Art. III) stays under 400 lines.** WU6 is the
first HTTP-observable unit (endpoint reachable, verifiable by `curl`/OpenAPI) and lands at
~400 — right at the edge, not comfortably under it. WU9 is the first UI-observable unit and
is a comfortable ~235. Every unit strictly under 400 (WU1, WU2, WU4, WU5, WU7, WU8, WU10) is
backend-internal or non-shipped-surface work with no observable output by itself. The floor
for *a single fully-observable slice* (repository → route → frontend, WU2+WU5+WU6+WU9) is
~1,190 lines — well above 400. Eleven work units is the finest useful split found; splitting WU6
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

**Completion condition outstanding for every task below.** AGENTS.md §10 and
`docs/definition-of-done.md` §Puerta de trazabilidad both make the `docs/traceability-matrix.md` row
a per-task condition of done. This document defers all eleven `REQ-005` rows to T61/T62 in Phase 10,
and that deferral stands. A `[x]` below therefore records that the task's tests, lint, type check and
format are green — not that its definition of done is met. `docs/traceability-matrix.md` holds zero
`REQ-005` rows today.

- [x] T1 [TEST] Write `apps/api/tests/integration/test_alembic_0004.py` — mirrors `test_alembic_0003.py`: upgrade adds `ix_occurrence_book_lemma_pos` on `occurrence(book_id, lemma, pos)` (`PRAGMA index_list`); downgrade removes it and returns `alembic_version` to `0003_annotation`. RED: file/revision does not exist.
- [x] T2 [MIGRATION] Create `apps/api/migrations/versions/0004_vocabulary_group_index.py`: `revision="0004_vocabulary_group_index"`, `down_revision="0003_annotation"`; `upgrade()` → `op.create_index("ix_occurrence_book_lemma_pos", "occurrence", ["book_id", "lemma", "pos"])`; `downgrade()` → `op.drop_index(...)`.
- [x] T3 [TEST] Extend `apps/api/tests/unit/test_no_lemma_naming.py::_LEMMA_OWNING_FILES` (`:169-190`) with `"migrations/versions/0004_vocabulary_group_index.py": frozenset({"lemma"})` — the migration's column-list literal `"lemma"` would otherwise fail the existing lemma-naming guard. **Deviation**: also required adding the exact index-name literal `"ix_occurrence_book_lemma_pos"` to `_ALLOWED_LEMMA_SYMBOLS` and its owning-file entries (`models.py`, `0004_vocabulary_group_index.py`) — `_FORBIDDEN` is a substring match, not word-bounded, so the index name itself (not just the bare `"lemma"` column-list literal) trips the guard. See apply-progress for detail.
- [x] T4 [IMPL] Modify `apps/api/src/wheel_vocabulary/infrastructure/persistence/models.py` (`Occurrence.__table_args__`, `:72-74`): add `Index("ix_occurrence_book_lemma_pos", "book_id", "lemma", "pos")` alongside the existing `ix_occurrence_book_norm_raw`.
- [x] T5 [TEST] Run T1 green (AC-005-09 scenario 3); run the runtime harness above to prove both directions exit 0.

## Phase 2 — Vocabulary repository core (WU2, ~270 lines)

Depends on: Phase 1.
Focused test: `cd apps/api && uv run pytest tests/unit/test_vocabulary_repository_properties.py -q`

**Completion condition outstanding for every task below**, on the same terms as Phase 1: the eleven
`REQ-005` matrix rows are deferred to T61/T62, so a `[x]` here records green tests, lint, type check
and format, not a met definition of done.

**Scope carved out after apply.** Snapshot isolation across the two legs left this phase and became
WU2b — see §Snapshot isolation carved out of WU2 and `design.md` §D1a. T8's "one `Session` for both
legs" is shipped and is not one snapshot.

- [x] T6 [TEST] Write a Hypothesis strategy over `(automatic, corrected)` `(lemma, pos)` pairs (`apps/api/tests/unit/test_vocabulary_repository_properties.py`), asserting the repository's per-occurrence effective resolution agrees with `domain.annotation.resolve_effective` (`:132`) on every generated case (AC-005-02 scenario 4). RED: repository does not exist.
- [x] T7 [TEST] Extend the same property test module: given generated seeded corrections, V3's group-by-group counts equal a naive Python `groupby` over `resolve_effective`-resolved values, value for value.
- [x] T8 [IMPL] Create `apps/api/src/wheel_vocabulary/infrastructure/persistence/vocabulary_repository.py`: `@dataclass(frozen=True, slots=True) VocabularyGroup(lemma: str | None, pos: str | None, occurrence_count: int)` and `SqlAlchemyVocabularyReadRepository.groups(book_id)` implementing design D1's leg A (raw `GROUP BY o.lemma, o.pos`) + leg B (corrected-occurrence delta) merged via `resolve_effective`, one `Session` for both legs. Existence check mirrors `annotation_repository.py::read`'s `session.get(Book, book_id) is None → return None` pattern. **The returned sequence MUST carry design D5's total order `occurrence_count DESC, lemma, pos`, applied after the leg-A/leg-B merge, not inside leg A's SQL** — leg B moves rows between groups, so an order established before the merge is not the order returned. `NULL` sorts before any string in both key halves (design D5), so the order is total, never partial (§2.1 G5, AC-005-01 scenario 3). **Post-apply correction**: "one `Session` for both legs" is shipped and does not produce one snapshot — pysqlite opens no transaction for a `SELECT`, so each leg reads independently. The snapshot obligation moved to WU2b; what T8 delivers is the sequential behaviour every `AC-005` scenario specifies.
- [x] T9 [TEST] Extend `test_no_lemma_naming.py::_LEMMA_OWNING_FILES` with `"infrastructure/persistence/vocabulary_repository.py": frozenset({"lemma"})`.
- [x] T10 [TEST] Run T6/T7 green; run the full backend suite to confirm no regression in `annotation_repository.py`'s existing tests (untouched file).
- [x] T11 [REFACTOR] If leg A/leg B merge logic duplicates code across the two Hypothesis assertions, extract a shared `_naive_groups(...)` test helper — no production-code change.

## Phase 2b — Snapshot isolation (WU2b, unestimated)

Depends on: Phase 2. **Blocked on an open decision, so this phase carries no task IDs yet.** The
journal mode is unchosen (`design.md` §Open Questions), and it decides whether the fix is one engine
setting, a read-scoped transaction, or both — which in turn decides the tasks, their order and their
size. Numbering tasks now would record a plan that has not been made.

What is already fixed, and what any future task list must satisfy:

- The fix must not starve unrelated writers. Round 2's read-scoped `BEGIN` made `delete()` of an
  unrelated book raise `OperationalError: database is locked` at 5.279 s where the control returned
  `True` at 1.113 s (`design.md` §D1a).
- The regression test must assert the returned groups, and its interleaved write must commit. The
  preserved test at `ed7e9f3` does neither.
- `vocabulary_repository.py`'s module docstring and `groups()`'s docstring both describe a snapshot
  and a blocked writer. Both must match whatever this phase ships.

Preserved work: `feat/vocabulary-read-snapshot-isolation` @ `ed7e9f3`, stacked on `ac5b4b9`.

## Phase 3 — Structural absence guards (WU3, ~390 lines)

**Split-and-withdrawal note.** This phase briefly split into WU3a/WU3b/WU3c after Judgment Day
round 4 shrank the write guard from 1437 lines to 465 by dropping every ORM-instance detection
branch whose claims could not be proven. The split's premise, registered as spec §5 AMB-11, was
that an AST pass over untyped Python cannot verify a receiver is a `Session`, so ORM-instance forms
needed a second mechanism — Phase 3b's runtime `before_cursor_execute` listener — to be covered at
all, with Phase 3c closing two remaining detector gaps. **Judgment Day round 6 falsified that
premise in one paragraph**: `session.add(ManualCorrection(...))`,
`session.query(ManualCorrection).delete()`, and every other ORM-instance idiom carries
`ManualCorrection` in its own AST — a detector can flag on callee name plus `ManualCorrection`
appearing anywhere in the call expression, including the receiver chain, and never ask what the
receiver is. Detection was rewritten on exactly that rule (T13/T16 below), closing every form the
split existed to cover. Phase 3b and Phase 3c are withdrawn, their T21a-T21g tasks deleted, and
spec §5 no longer carries AMB-11 — `spec.md` is reverted to its pre-AMB-11 text (AC-005-08 and its
scenario 1 read exactly as they did before this split, byte-for-byte against `b874f62`).

Depends on: Phase 2.
Focused test: `cd apps/api && uv run pytest tests/unit/test_vocabulary_repository_isolation.py tests/unit/test_vocabulary_write_guard.py tests/unit/test_no_confidence_action_or_propn_filter.py -q`

- [x] T12 [TEST] Write `apps/api/tests/unit/test_vocabulary_repository_isolation.py`: AST-walk `vocabulary_repository.py` and assert it never names `AnnotationProvenance` (D4/C6) — narrower than `test_annotation_write_repository_isolation.py`, one forbidden name, one mutation check (temporarily import `AnnotationProvenance`, observe the failure, revert), one non-vacuity assertion. RED: repository does not join provenance yet, so this test is vacuous until T8 lands — sequence after T8, before archiving Phase 3. **Correction (Judgment Day round 1, JD-W3-3)**: the shipped module's docstring claimed "the same coverage as `test_annotation_write_repository_isolation.py::_references_to`" — false; the sibling has a SECOND call site checking the snake_case persisted table name (`annotation_provenance`), and this guard had only the CamelCase class-name check, so `text("SELECT pos_confidence FROM annotation_provenance")`, reflection, and a `Base.metadata.tables[...]` subscript all passed undetected. Added the second call site, a docstring exemption for the module's own legitimate use of the table name in prose (mirroring the sibling's reviewed-docstring pin), and corrected the false coverage claim. **Correction (Judgment Day round 2, JD-W3-10 + Judge B suspect)**: the table-name mutation check's recorded output, `['vocabulary_repository.py:46 string literal 'annotation_provenance'']`, was not producible by any Python `repr` (the inner quotes clash with the outer ones) — recorded the actual verbatim output instead. Separately, the docstring-exemption comment pinned "Two legs run inside ONE `Session` — one snapshot" as the "REVIEWED" text without qualifying that the claim itself is KNOWN FALSE (carved out to WU2b, see Phase 2b below) — reworded the comment to state the pin fixes the text AS OF this review point, not that its claims hold.
- [x] T13 [TEST] Write `apps/api/tests/unit/test_vocabulary_write_guard.py` — the REQ-005-008 guard that MUST differ from `test_annotation_write_repository_isolation.py`: it permits `select(ManualCorrection...)`/`ManualCorrection.field` reads and forbids only `insert(ManualCorrection)`, `update(ManualCorrection)`, `delete(ManualCorrection)` SQLAlchemy calls and raw `INSERT/UPDATE/DELETE ... manual_correction` SQL text, scanned across every module this capability introduces. Do NOT reuse or extend the existing no-reference guard, and do NOT exempt this capability's modules from it (SPEC-003 §3.4 W1) — this is a distinct, narrower rule (AMB-3). **Rewritten a fourth time (round 4, this work unit)**, after rounds 1-3 accumulated into a 1437-line module (146 of them one module docstring) that escalated three straight Judgment Day rounds over prose claims the tests did not pin, never over the detection logic itself — six judge passes confirmed the scan was genuinely unfiltered. The file was deleted and rewritten to 465 lines with a 20-line module docstring, aiming for every remaining prose sentence to carry a test that would fail if it stopped being true. **Correction (Judgment Day round 5, tasks.md finding)**: that aim was claimed as achieved and was not — Judge A's audit found `_WRITE_FUNCS`'s `"update"` element and `_FORBIDDEN_RAW_SQL`'s `"update manual_correction"` entry were named in the module docstring, REQ-005-008 and AC-005-08, but pinned by no test; removing both left the 25-test suite green (JD-A1). The claim is deleted rather than reasserted — round 5 closed this specific gap (two new pinning tests, mutation-verified) but a per-sentence audit of every remaining claim was not repeated exhaustively enough to re-assert "every". Detection is now a closed list of two forms — a `sqlalchemy` `insert`/`update`/`delete` call (import- and module-alias resolved) carrying `ManualCorrection` as an argument, and a case-insensitive raw-SQL substring/`+`-folded scan — dropping every ORM-instance idiom (`session.add`/`.merge`/`.delete`, `Query.delete`/`.update`, bulk mappings, `__table__` writes) and the local-binding tracker that generated round 3's receiver-origin false claims; `test_orm_instance_idioms_are_out_of_scope` now pins that exclusion directly. `_scanned_modules` still walks the package and migrations root unconditionally, `rglob` on BOTH roots (round 3 used `glob` on migrations while claiming full recursion). `_EXEMPT_WRITE_MODULES` still names exactly `book_repository.py`'s `DeleteImport` cascade delete, applied at `_write_violations` aggregation, never by excluding the module from the walk — `test_the_scan_reaches_every_expected_module`'s anchor set includes it, proving the walk still reaches it. Round 3's naming-convention invariant (`"vocabulary" in label.lower()`) is deleted rather than repeated: it re-tested the exact convention the round-3 rewrite had just removed from the scan, and the file's own sibling test used a token-free module as its counter-example — the invariant refuted itself. The replacement, `test_the_exempt_set_is_exactly_book_repository`, asserts set equality only: any addition requires editing that assertion, which forces review, not a claim that exemption is impossible. **Correction (Judgment Day round 6, tasks.md and spec.md finding).** The premise the round-4 rewrite and the Phase 3b/3c split rested on — that an AST pass cannot verify a `Session` receiver, so ORM-instance forms cannot be structurally detected — was false: detection does not need to verify the receiver at all. The detector was rewritten a fifth time (T16 below) on a callee-name-plus-argument rule: any call whose callee names a write verb and whose call expression names `ManualCorrection` anywhere, receiver included, is flagged — `session.add(ManualCorrection(...))`, `session.query(ManualCorrection).delete()`, and `ManualCorrection.__table__.delete()` are now all caught (`test_session_receiver_idioms_are_now_caught`, `test_table_attribute_write_is_now_caught`). The stale citation this text previously carried — `test_orm_instance_idioms_are_out_of_scope`, itself already renamed once to `test_session_receiver_idioms_are_out_of_scope` without this task being updated to match — is corrected here rather than left dangling: neither test exists any more; both asserted these idioms were OUT of scope, and that assertion is now false. REQ-005-008 is fully discharged by T12-T17 again; Phase 3b and Phase 3c are withdrawn — see this phase's split-and-withdrawal note above.
- [x] T14 [TEST] Extend T13's module with the required mutation check (AC-005-08 scenario 3): an insert against `ManualCorrection`, then a delete against it, each appended in turn to the vocabulary repository, each asserted to produce a violation with the observed failure text recorded in the test docstring. **Rewritten (round 4)**: `test_writes_appended_to_the_vocabulary_repository_are_caught` appends both mutations to the REAL `vocabulary_repository.py` source (181 lines today) and records both verbatim outputs — `infrastructure/persistence/vocabulary_repository.py:183 insert(ManualCorrection)` / `...183 delete(ManualCorrection)` — re-run against this rewrite's detector, not carried forward from round 3's differently-shaped output (round 3 recorded `ORM write call insert(ManualCorrection)` against a synthetic-only fixture and never re-ran the real-file variant it declared itself to be).
- [x] T15 [TEST] Extend T13's module with the boundary control (AC-005-08 scenario 4/M3): the same forbidden write statement placed in a module OUTSIDE this capability still produces a violation. **Rewritten (round 4)**: `test_the_exemption_boundary_holds_through_write_violations` and `test_emptying_the_exempt_set_fails_through_write_violations` both call `_write_violations` — never `_detect_writes` directly — because Judgment Day round 3 (Judge B) proved a prior boundary control bypassed aggregation entirely and would have passed against a mutant that suppressed the whole default scan.
- [x] T16 [IMPL] Implement the write-detector in `test_vocabulary_write_guard.py` itself (test-only code, no production module): AST `ast.Call` matching on `insert`/`update`/`delete` imported from `sqlalchemy` with a `ManualCorrection` argument (import- and module-alias resolved), plus a substring scan over string/`BinOp`-folded literals for `insert into manual_correction`/`update manual_correction`/`delete from manual_correction` (case-insensitive). **Rewritten (round 4, this work unit)**: the detector is now exactly the two forms above — `_sqlalchemy_write_call` plus the raw-SQL substring/`+`-fold scan (`_folded_string`, `_string_literals`). Removed entirely: `_instance_add_call`, `_instance_delete_call`, `_query_write_call`, `_bulk_mapping_call`, `_table_write_call`, `_receiver_name`, and `_manual_correction_bindings` (the local-binding tracker) — all carried unmodified through rounds 1-3 and all named by judges as the source of unverifiable receiver-origin claims. Their removal, combined with the file's full replacement (49 old tests → 25 new tests), moves the backend suite from 617 to 593 passing tests total — a decrease is the correct outcome here, not a regression. The "Known gaps" section is reduced to the raw-SQL adjacency limits alone (`REPLACE INTO`, whitespace, quoting), stated as non-exhaustive, pinned by one parametrized test (`test_raw_sql_adjacency_gaps_are_not_exhaustive`); no other gap catalogue is claimed. **Correction (Judgment Day round 5, JD-A4)**: `_names_manual_correction` matched only the literal identifier `ManualCorrection`, so `from ... import ManualCorrection as MC` then `delete(MC)` evaded detection entirely (a third under-approximation, assigned to no phase until this correction) — Judge B rendered its SQL as `DELETE FROM manual_correction`. Fixed in place, in this same phase, by the same mechanism already used for `sqlalchemy` write-function aliases: `_manual_correction_aliases` collects `from ... import ManualCorrection as X` bindings and `_names_manual_correction` now matches any of them, plus a control proving an unrelated class aliased to a similar-looking name is not mistaken for it. Also fixed in the same round, same mechanism-reuse principle: a `+`-folded raw-SQL chain was reported once per sub-expression (three times for a two-`+` chain) instead of once, and the raw-SQL scan walked docstrings as if they were executable SQL, flagging ordinary prose — both closed with tests (`test_a_folded_chain_is_reported_once_not_once_per_sub_expression`, `test_a_docstring_mentioning_manual_correction_is_not_a_violation`). One over-approximation was found and left deliberately unfixed: name resolution is not flow-sensitive, so a parameter shadowing an imported write name, or a later rebinding, is still reported as a write — pinned as an accepted known gap (`test_a_shadowed_or_rebound_name_is_a_known_over_approximation`), not narrowed, because narrowing it means re-adding the local-binding/receiver-origin tracking that rounds 1-3 already proved unverifiable. **Correction (Judgment Day round 6).** The detector is rewritten a fifth time on the rule described in T13's round-6 correction: `_call_write_verb` matches the callee's bare name or final attribute against `_WRITE_VERBS` (`insert`, `update`, `delete`, `add`, `add_all`, `merge`, `bulk_insert_mappings`, `bulk_update_mappings`) with no receiver check at all, and `_call_names_manual_correction` walks the whole call expression — not just its argument list — for `ManualCorrection` or a tracked class alias. The `sqlalchemy`-import/module-alias origin-resolution helpers (`_sqlalchemy_call_aliases`, `_sqlalchemy_module_aliases`) are deleted rather than left unused, because origin is never checked; a write verb imported under a renamed binding (`from sqlalchemy import delete as sa_delete`) is a new, documented gap this drops (`test_a_renamed_write_verb_import_is_a_known_gap`) — the file moves from 34 collected tests to 49. Round 5's docstring exclusion from the raw-SQL scan is also removed (SPEC-003 §3.2 E3: a docstring is runtime-reachable through `__doc__`, and excluding it let `session.execute(text(__doc__))` read past the exemption) — `test_a_docstring_mentioning_manual_correction_is_not_a_violation` is replaced by `test_a_docstring_containing_the_forbidden_fragment_is_flagged`, which pins the opposite outcome. `test_a_shadowed_or_rebound_name_is_a_known_over_approximation` is replaced by `test_no_receiver_or_origin_is_verified_a_known_over_approximation`, `test_an_unrelated_class_genuinely_named_manual_correction_is_flagged`, and `test_a_rebound_class_alias_is_still_treated_as_manual_correction` — the old test's framing ('a parameter shadows an IMPORTED write name') no longer applies once no import is ever resolved. One new known gap is added and pinned, not silently absorbed: `session.add(correction)` where `correction` was built on an earlier line is not tracked (`test_a_binding_constructed_elsewhere_then_passed_is_a_known_gap`) — a one-hop binding tracker was considered and deliberately not built, to avoid re-introducing the kind of tracking machinery three Judgment Day rounds already found unreliable.
- [x] T17 [TEST] Write the vocabulary-repository read scenario (AC-005-08 scenario 2): seed a `ManualCorrection` row, run `groups()`, assert `manual_correction` row count and bytes are unchanged afterwards. **Correction (Judgment Day round 1, JD-W3-5)**: `_read_all_corrections` ordered by `ManualCorrection.id` but did not include `id` in the compared tuple, so a delete of a correction row followed by the insert of a value-identical replacement (a new `id`, every other column unchanged) compared equal — defeating AC-005-08's byte-identical-rows requirement. Added `id` to the compared tuple and a regression test (`test_read_all_corrections_detects_a_delete_then_reinsert`) proving the helper now detects exactly this case.
- [x] T18 [TEST] Extend `apps/api/tests/unit/test_no_confidence_action_or_propn_filter.py::_EXPECTED_FILES` (`:37-45`) with `infrastructure/persistence/vocabulary_repository.py`, `application/vocabulary/use_cases.py`, `api/routes/vocabulary.py` — non-vacuity, no code change yet. **Deferred**: the guard asserts `scanned >= _EXPECTED_FILES` (non-vacuity over files that actually exist), so `application/vocabulary/use_cases.py` and `api/routes/vocabulary.py` were confirmed absent, added temporarily to reproduce the failure (`AssertionError: ... Extra items in the right set`), then removed. Only `infrastructure/persistence/vocabulary_repository.py` was added now. Add the other two when T27 (WU5) and T38 (WU6) ship them.
- [x] T19 [IMPL] Extend `_CONFIDENCE_ACTION_PATTERN` (`:35`) to add `mean_confidence` (see forecast note above — the current pattern does not catch it). Verify `pos_confidence`/`lemma_confidence` identifiers package-wide still pass (the added term is a distinct substring, no false positive).
- [x] T20 [TEST] Add three synthetic mutation-check tests to the same module mirroring `test_a_confidence_threshold_helper_would_be_caught`: a `min_confidence` query-parameter-shaped identifier, a `mean_confidence` property-shaped identifier, and a `sort_by_confidence` helper — each in turn asserted to violate (AC-005-07 scenario 4). **Correction (Judgment Day round 1, JD-W3-4)**: the `min_confidence` check's handler body echoed the parameter (`return min_confidence`), so it passed via the pre-existing `ast.Name` branch and never actually exercised the parameter-declaration position AC-005-07 sc.4 is about (the served OpenAPI parameter list, present whether or not the handler body reads the parameter back). `def list_groups(min_confidence: float = 0.0) -> None: return None` — a handler that declares the parameter without echoing it — returned `[]` against the shipped detector. Extended `_confidence_action_violations` to inspect `ast.arg` (and `ast.Attribute`) and rewrote the test to use a non-echoing handler, which now genuinely requires the `ast.arg` branch to pass.
- [x] T21 [TEST] Run all of Phase 3 green; run the full backend suite once to confirm the confidence-pattern extension does not break any existing test. **Note (Judgment Day round 1)**: "green" at T21 did not mean "correct" — five of the six defects corrected above (JD-W3-1 through JD-W3-6, excluding JD-W3-4 which sits in Phase 3.2) were present in code that passed this exact Phase 3 run; the guards were vacuous or falsely scoped in ways their own tests could not detect. See T12/T13/T14/T16/T17 above for the specific corrections.

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
this document** · 007→T18-T20 · 008→T12-T17 · 009→T1-T5,T22 · 010→T49,T55-T57 ·
011→T42-T46.

**Correction (Judgment Day round 5, tasks.md finding), withdrawn by round 6.** Round 5 split
`008→T12-T17` into `008→T12-T17,T21a-T21g`, on the finding that Phase 3b (runtime observation) and
Phase 3c (detector hardening) both covered forms — the ORM-instance idioms and the `__table__`
write — the then-shipped guard did not detect (spec §5 AMB-11). Round 6 closed those forms inside
T12-T17 itself, by rewriting the detector on a rule that never inspects the receiver (see Phase 3's
split-and-withdrawal note and T13's round-6 correction). REQ-005-008 is fully discharged by T12-T17
again; there is no `T21a-T21g` for this map to cite.

WU2b maps to no requirement, and that is the finding spec §5 `AMB-10` registers: the one-snapshot
obligation lives in `design.md` D1, never in a `REQ-005` requirement, and §7 excludes transaction
boundaries from the specification's scope. Every `AC-005` scenario names a read with no interleaved
committed write, so none of them is weakened by WU2b being outstanding, and none of them would catch
the torn read either.

`REQ-005-001` carries three tasks because its ordering-stability scenario is proved at two levels:
T8 establishes the total order, T22 asserts it survives two repository reads, and T35 asserts it
survives serialization across two HTTP requests.
`docs/product-vision.md` roadmap item 5 stays incomplete until slice 2 (`REQ-005-006`) ships,
per spec §1/§5 AMB-5 — not a gap in this task list.

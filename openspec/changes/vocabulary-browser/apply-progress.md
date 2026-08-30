# Apply Progress — vocabulary-browser

## Batch 1 — Phase 1 / WU1 (T1–T5)

**Mode**: Strict TDD
**Delivery**: chained, stacked-to-main
**Branch**: `feat/vocabulary-browser-wu1-index-migration`

### Completed Tasks

- [x] T1 [TEST] `apps/api/tests/integration/test_alembic_0004.py` — mirrors `test_alembic_0003.py`.
- [x] T2 [MIGRATION] `apps/api/migrations/versions/0004_vocabulary_group_index.py`.
- [x] T3 [TEST] Extended `test_no_lemma_naming.py::_LEMMA_OWNING_FILES` (plus a required allow-list extension — see Deviations).
- [x] T4 [IMPL] `Occurrence.__table_args__` — added `ix_occurrence_book_lemma_pos`.
- [x] T5 [TEST] T1 green; runtime harness (`alembic upgrade head` + `alembic downgrade -1` + `alembic upgrade head`) all three exit 0.

### Files Changed

| File | Action | What Was Done |
|------|--------|---------------|
| `apps/api/migrations/versions/0004_vocabulary_group_index.py` | Created | `revision="0004_vocabulary_group_index"`, `down_revision="0003_annotation"`; additive `op.create_index`/`op.drop_index` on `ix_occurrence_book_lemma_pos`. |
| `apps/api/src/wheel_vocabulary/infrastructure/persistence/models.py` | Modified | Added `Index("ix_occurrence_book_lemma_pos", "book_id", "lemma", "pos")` to `Occurrence.__table_args__`. |
| `apps/api/tests/integration/test_alembic_0004.py` | Created, then modified | Originally created navigating by `head`/`-1` (RED observed in that form — see RED evidence note below). Adversarial review found relative navigation defective for this file too, for the same reason already documented for `test_alembic_0003.py`; pinned both `command.upgrade`/`command.downgrade` calls to explicit revision strings (`0004_vocabulary_group_index`/`0003_annotation`) and verified GREEN (RED for the pinned form not re-observed — see note). Three tests: upgrade adds the index / downgrade removes it and restores `alembic_version`; downgrade touches no other schema object; the migrated index's reflected columns match `Occurrence.__table__.indexes` in `models.py`. |
| `apps/api/tests/unit/test_no_lemma_naming.py` | Modified | `_LEMMA_OWNING_FILES` extended for `models.py` and the new migration; `_ALLOWED_LEMMA_SYMBOLS` extended with the exact index-name literal; the allow-list self-check test updated to match. |
| `apps/api/tests/integration/test_alembic_0003.py` | Modified | Pinned `test_upgrade_adds_lemma_provenance_and_correction` to explicit revision strings (`0003_annotation`/`0002_book_occurrence`) instead of `head`/`-1` — see Deviations. |

### TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| T1 | `tests/integration/test_alembic_0004.py` | Integration | ✅ 546/546 (pre-existing baseline, full suite) | ⚠️ Observed only against the test's original (unpinned) form — see RED evidence note below | ✅ 3/3 passed after T2+T4 | ✅ 3 cases (upgrade/downgrade positive; downgrade-touches-nothing-else negative; migrated-index-matches-declarative-model cross-check) | ➖ None needed |
| T2 | N/A (migration, not test) | — | N/A | — | — | — | — |
| T3 | `tests/unit/test_no_lemma_naming.py` | Unit | ✅ 32/33 passing pre-change (1 pre-existing pass, guard test itself) | ✅ Ran guard, observed real failure: 3 violations for `ix_occurrence_book_lemma_pos`/`lemma` literals in the new migration before the allow-list extension | ✅ 33/33 after extending `_LEMMA_OWNING_FILES` + `_ALLOWED_LEMMA_SYMBOLS` + the self-check test | ➖ Single (guard is structural, one behavior) | ➖ None needed |
| T4 | Covered by T1's integration test | — | ✅ | ✅ (T1's RED covered this) | ✅ | ➖ Covered by T1 | ➖ None needed |
| T5 | Full suite + runtime harness | Integration | ✅ 546/546 baseline | N/A | ✅ 549/549 | N/A | N/A |

**RED evidence note (T1).** The RED above was observed against the test's
original form, which navigated by `head`/`-1` and failed with
`AssertionError: assert 'ix_occurrence_book_lemma_pos' in
{'ix_occurrence_book_norm_raw'}` (revision `0004` did not exist yet; `head`
resolved to `0003_annotation`). Adversarial review then found that relative
navigation is defective here — it silently tests the wrong revision boundary
once a later migration lands — so the test was pinned to explicit revision
strings (`0004_vocabulary_group_index`/`0003_annotation`), matching the fix
in `test_alembic_0003.py`. The pinned form was verified GREEN. The RED for
the pinned form was **not re-observed**: this is a limitation of the record,
not a claim that a RED was run against the shipped test. For the pinned
form, the equivalent RED would surface as an Alembic `CommandError: Can't
locate revision identified by '0004_vocabulary_group_index'` when the
revision is absent — a resolution failure, not the behavioural-absence RED
this evidence trail is meant to demonstrate.

### Test Summary

- **Total tests written**: 3 (new file) + 1 modified (pre-existing regression fix, not new)
- **Total tests passing**: 549/549 (baseline 546 + 3 new)
- **Layers used**: Integration (3 new + 1 fixed)
- **Approval tests**: None — no refactoring tasks in this batch
- **Pure functions created**: 0 (migration + declarative index only)

### Deviations from Design

1. **Guard allow-list gap (T3)**: the task text said extend `_LEMMA_OWNING_FILES` with `frozenset({"lemma"})` only. `_FORBIDDEN` in `test_no_lemma_naming.py` is a plain substring match with no word boundary (`re.compile("lemma|lemas|lexeme|lexema", re.IGNORECASE)`), so the index name literal `"ix_occurrence_book_lemma_pos"` itself also matches — not just the bare `"lemma"` column-list literal the task called out. `_is_exempt` requires exact equality against `_ALLOWED_LEMMA_SYMBOLS`, which did not contain this string. Resolution: added `"ix_occurrence_book_lemma_pos"` as its own entry in `_ALLOWED_LEMMA_SYMBOLS`, bound to its owning files (`models.py`, the new migration) — the same pattern already used for `lemma_confidence`. Also updated the guard's own self-check test (`test_the_allow_list_is_a_finite_enumeration_of_exact_lemma_symbols`) which pins the allow-list's exact contents.
2. **Pre-existing regression in `test_alembic_0003.py`**: `test_upgrade_adds_lemma_provenance_and_correction` used relative `command.upgrade(alembic_config, "head")` then `command.downgrade(alembic_config, "-1")`. Adding revision `0004` moved `head` past `0003_annotation`, so `-1` from head landed on `0003_annotation` (not `0002_book_occurrence`) and the assertions failed — `annotation_provenance` was still present. Fixed by pinning both calls to explicit revision strings (`"0003_annotation"`, `"0002_book_occurrence"`), matching the pattern the file's other two tests already use. Not in the WU1 task list, but required to keep the full suite green (AGENTS.md §10).

### Issues Found

None beyond the two deviations above.

### Remaining Tasks (WU2+, not in this batch)

- [ ] T6–T62 (Phases 2–10) — not started; out of WU1 scope.

### Verification (batch 1)

- Focused: `cd apps/api && uv run pytest tests/integration/test_alembic_0004.py -q` → 3 passed
- Guard: `cd apps/api && uv run pytest tests/unit/test_no_lemma_naming.py -q` → 33 passed
- Runtime harness: `cd apps/api && uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head` → all three exit 0
- Full suite + coverage: `cd apps/api && uv run pytest --cov=wheel_vocabulary --cov-fail-under=80` → 549 passed, 100.00% coverage
- Lint: `cd apps/api && uv run ruff check .` → All checks passed
- Format: `cd apps/api && uv run ruff format --check .` → 114 files already formatted
- Typecheck: `cd apps/api && uv run mypy src/wheel_vocabulary` → Success: no issues found in 47 source files
- Baseline (before this batch): 546 tests passing, 100% coverage (confirmed by re-run before any edit)
- DB left at `0004_vocabulary_group_index (head)` after the harness run, per instruction.

### Workload / PR Boundary

- Mode: chained PR slice (stacked-to-main)
- Current work unit: WU1 — additive index migration
- Boundary: starts from `main` (`00bf792`); ends with the migration + model index + their tests + guard-map maintenance + the pre-existing alembic-test regression fix. Rollback: `alembic downgrade -1`, delete `migrations/versions/0004_vocabulary_group_index.py`, revert the `models.py` index line, revert the guard-map and `test_alembic_0003.py` edits.
- Estimated review budget impact: authored code diff (excluding pre-existing untracked planning docs committed separately) — see final report for exact line count.

## Batch 2 — Phase 2 / WU2 (T6–T11)

**Mode**: Strict TDD
**Delivery**: chained, stacked-to-main
**Branch**: `feat/vocabulary-browser-wu2-repository` (created off `main` @ `9c74152`)

### Completed Tasks

- [x] T6 [TEST] `apps/api/tests/unit/test_vocabulary_repository_properties.py` — Hypothesis property: repository's per-occurrence effective resolution agrees with `resolve_effective`.
- [x] T7 [TEST] Same module — Hypothesis property: V3's group-by-group counts equal a naive Python groupby over `resolve_effective`-resolved values.
- [x] T8 [IMPL] `apps/api/src/wheel_vocabulary/infrastructure/persistence/vocabulary_repository.py` — `VocabularyGroup` + `SqlAlchemyVocabularyReadRepository.groups()`, design D1's V3 hybrid (leg A raw `GROUP BY`, leg B correction delta, merged via `resolve_effective`), design D5's total order applied after the merge.
- [x] T9 [TEST] Extended `test_no_lemma_naming.py::_LEMMA_OWNING_FILES` with `"infrastructure/persistence/vocabulary_repository.py": frozenset({"lemma"})`.
- [x] T10 [TEST] T6/T7 green; full backend suite re-run, no regression.
- [x] T11 [REFACTOR] Extracted shared `_naive_groups(...)` test helper, used by both T6 (one-spec call) and T7 (multi-spec call) — no production-code change.

### Files Changed

| File | Action | What Was Done |
|------|--------|---------------|
| `apps/api/src/wheel_vocabulary/infrastructure/persistence/vocabulary_repository.py` | Created | `VocabularyGroup` dataclass; `SqlAlchemyVocabularyReadRepository.groups(book_id)` — leg A (`GROUP BY Occurrence.lemma, Occurrence.pos`, index-ordered), leg B (correction delta bounded by correction count), merge via `resolve_effective` (the one place §2.5's precedence rule runs), `_sort_key`/`_ordered` applying design D5's total order (`occurrence_count DESC, lemma, pos`, `NULL` first in both halves) strictly after the merge. Existence check mirrors `annotation_repository.py::read`. Never references `AnnotationProvenance`; joins `occurrence` and `manual_correction` only (design D4). |
| `apps/api/tests/unit/test_vocabulary_repository_properties.py` | Created | Two Hypothesis property tests (T6, T7) plus three example-based tests: the `NULL`-ordering landmine test (D5), unknown-`book_id` → `None`, and zero-occurrence → `[]`. Local `session_factory` fixture (SQLite, `tmp_path`), mirroring `test_annotation_models.py`'s precedent. `_seed_occurrences`/`_naive_groups` helpers seed `ManualCorrection` rows directly through the ORM (no writer exists yet, per `REQ-005-002`'s "testable now" note). |
| `apps/api/tests/unit/test_no_lemma_naming.py` | Modified | `_LEMMA_OWNING_FILES` extended with `"infrastructure/persistence/vocabulary_repository.py": frozenset({"lemma"})` (T9). `_ALLOWED_LEMMA_SYMBOLS` unchanged — no new symbol was introduced, only a new owning file for the existing bare `"lemma"` entry. |

### TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| T6 | `tests/unit/test_vocabulary_repository_properties.py` | Unit (SQLite-backed, mirrors `test_annotation_models.py`) | ✅ 549/549 (pre-change baseline, full suite) | ✅ Written against a deliberately-wrong stub repository (`groups()` always returns `[]`) so the failure is a real assertion mismatch, not a `ModuleNotFoundError` — AGENTS.md §3 does not accept an import error as RED. Observed: `assert {} == {(None, None): 1}` (T7's property) and `assert [] == [VocabularyGroup(lemma='bb', ...)]` (ordering test) and `assert [] is None` (unknown-id test) — see RED evidence note below | ✅ 5/5 passed after implementing the real V3 hybrid | ✅ Hypothesis, `max_examples=50` per property — dozens of distinct `(automatic, corrected)` combinations per run, `None`/string on both sides | ✅ See T11 |
| T7 | Same module | Unit (SQLite-backed) | ✅ Same | ✅ Same run (see RED evidence note) | ✅ Passed | ✅ Hypothesis, `max_examples=50`, `1-8` occurrences per generated example, including groups vacated entirely by corrections | ✅ See T11 |
| T8 | Same module (ordering + existence tests) | Unit (SQLite-backed) | ✅ Same | ✅ Written before the ordering/existence logic existed — same RED run as T6/T7 (stub returned `[]` unconditionally, ordering test failed `assert [] == [VocabularyGroup(...), ...]`, unknown-id test failed `assert [] is None`) | ✅ Passed | ✅ 2 cases minimum (ordering: tie-break + `NULL`-first fixture with `NULL`-lemma and `NULL`-POS groups at the same count tier, deliberately forcing a `None`-vs-`str` comparison a naive `sorted()` would raise `TypeError` on; existence: unknown id vs. zero-occurrence import, both required so neither is conflated with the other per §2.3) | ➖ None needed beyond T11 |
| T9 | `tests/unit/test_no_lemma_naming.py` | Unit | ✅ 39/39 passing pre-change (guard suite itself) | ✅ Ran the guard before extending `_LEMMA_OWNING_FILES`, observed a real violation: `infrastructure/persistence/vocabulary_repository.py:...` naming `"lemma"` (both the dataclass field and the `ManualCorrection.field` string literal) with no owning-file entry | ✅ 39/39 after extending `_LEMMA_OWNING_FILES` | ➖ Single (guard is structural, one behavior) | ➖ None needed |
| T10 | Full suite | Integration | ✅ 549/549 baseline | N/A | ✅ 554/554 | N/A | N/A |
| T11 | `tests/unit/test_vocabulary_repository_properties.py` | Unit | ✅ 5/5 green before refactor | N/A (refactor, not new behavior) | ✅ 5/5 still green after extracting `_naive_groups` | N/A | ✅ Both Hypothesis assertions now call the same helper; T6 as a one-spec call, T7 as a multi-spec call — no production-code change |

**RED evidence note (T6/T7/T8).** All three tasks' new behavior was driven by ONE red run: `apps/api/tests/unit/test_vocabulary_repository_properties.py` was written in full against a deliberately-wrong stub `vocabulary_repository.py` (`SqlAlchemyVocabularyReadRepository.groups()` always returning `[]`, `VocabularyGroup` dataclass present so the import succeeds). This kept the failure a genuine assertion mismatch at the line invoking `repository.groups(...)`, never a `ModuleNotFoundError` at collection time — AGENTS.md §3 explicitly does not accept a syntax/import/fixture failure as RED. Observed failures, verbatim:
- T7's property: `assert {} == {(None, None): 1}` (Hypothesis-shrunk to `specs=[(None, None, None, None)]`).
- Ordering test (T8): `assert [] == [VocabularyGroup(lemma='bb', pos='NOUN', occurrence_count=2), ...]`.
- Unknown-id test (T8): `assert [] is None`.
- T6's property failed identically to T7's (same stub, same comparison shape) once the naive-groups extraction (T11) unified the assertion; before that extraction T6 failed as `assert [] == [VocabularyGroup(lemma=None, pos=None, occurrence_count=1)]`.
- The zero-occurrence test passed trivially against the stub (both stub and real implementation return `[]` for that case) — not a driving RED on its own, triangulated by the other four failures in the same run.

Then the real V3 hybrid was implemented (`_raw_group_counts` leg A, `_corrected_deltas` leg B, `_merge`, `_sort_key`/`_ordered`) and all 5 tests passed unmodified.

### The `NULL`-ordering landmine (design flagged, this batch solved)

Design D5 requires `NULL` to sort before any string in both key halves of `occurrence_count DESC, lemma, pos`, applied after the leg-A/leg-B merge — which happens in Python, where `None < "aa"` raises `TypeError` under default tuple comparison. `_sort_key` avoids ever comparing `None` against `str` directly: each key half is split into a presence flag (`key_half is not None`, `False` sorts before `True`) plus a filler string (`key_half or ""`) used only to break ties among *present* values. The filler is never returned to a caller — `VocabularyGroup.lemma`/`.pos` keep their real `None`/`""` values — so an empty-string value and a `NULL` value stay distinguishable on the wire per spec §2.3 N3; the filler only decides order, never identity.

`test_the_returned_sequence_is_ordered_by_count_desc_then_lemma_then_pos_with_null_first` proves this: it seeds a `("bb", "NOUN")` group at count 2 and three count-1 groups — `(None, None)`, `(None, "VERB")`, `("aa", None)` — deliberately placing a `None`-lemma group and a string-lemma group (`"aa"`) at the *same* count tier, which is exactly the comparison a naive `sorted(groups, key=lambda g: (-g.occurrence_count, g.lemma, g.pos))` would raise `TypeError` on. The test asserts the full returned list positionally against a literal expected order (never a set or a sorted copy), so a stable-but-wrong order (e.g. insertion order) cannot pass it either.

### Guard maps checked, not modified

- `test_no_lemma_naming.py::_LEMMA_OWNING_FILES` — extended (T9, required).
- `test_no_lemma_naming.py::_ALLOWED_LEMMA_SYMBOLS` — unchanged; no new lemma-shaped symbol was introduced by this batch (only the existing bare `"lemma"` gained a new owning file), so the guard's own self-check test (`test_the_allow_list_is_a_finite_enumeration_of_exact_lemma_symbols`) needed no edit.
- `test_no_confidence_action_or_propn_filter.py::_EXPECTED_FILES` — **checked, not modified**. This is Phase 3 / WU3's task T18, out of this batch's scope. Verified it is not required for WU2 to pass: `_EXPECTED_FILES` is used only in a non-vacuity assertion (`scanned >= _EXPECTED_FILES`, a superset check) — adding `vocabulary_repository.py` to `scanned` without adding it to `_EXPECTED_FILES` does not fail that assertion. The actual confidence-action scan (`test_nothing_acts_on_confidence_anywhere_in_the_package`) walks every `*.py` under `_PACKAGE_ROOT` via `rglob`, regardless of `_EXPECTED_FILES`, so it already scans `vocabulary_repository.py` today — confirmed by running the full guard suite (39/39 passed) with the new repository file present and `_EXPECTED_FILES` untouched.

### Deviations from Design

The implementation matches design D2 (relies on the WU1 index), D4 (no `AnnotationProvenance` reference) and D5 (total order, applied post-merge). `VocabularyGroup`'s field names (`lemma`, `pos`, `occurrence_count`) match design's `## Interfaces` block verbatim. Two records below correct what this section originally claimed.

1. **D1's one-snapshot obligation is not met (corrects "None" in the original record).** D1 required both legs to run in one `Session` (one snapshot); the shipped `groups()` runs both legs in one `Session` and gets two snapshots. pysqlite's legacy transactional mode emits `BEGIN` before `INSERT`, `UPDATE` and `DELETE` and never before a plain `SELECT`, so each leg runs in its own implicit transaction. Measurements, the two rejected fix rounds, and the journal-mode premise D1 never named are recorded in `design.md` §D1a; the scope move is `tasks.md` §Snapshot isolation carved out of WU2 (WU2b) and spec §5 `AMB-10`. What this batch shipped is the sequential behaviour the `AC-005` scenarios specify — each names a read with no interleaved committed write, and the five tests in this batch exercise exactly that.
2. **Traceability rows outstanding for T1–T11.** AGENTS.md §10 and `docs/definition-of-done.md` §Puerta de trazabilidad make the `docs/traceability-matrix.md` row a per-task condition of done. `tasks.md` defers all eleven `REQ-005` rows to T61/T62 in Phase 10, and that deferral predates this batch and stands. The `[x]` marks in Phases 1 and 2 therefore record green tests, lint, type check and format — not a met definition of done. `docs/traceability-matrix.md` holds zero `REQ-005` rows today. Recorded here and at both phase headers in `tasks.md`, so the deferral is visible where completion is claimed.

### Issues Found

1. **Torn read across the two legs.** An `UPDATE` committing between leg A and leg B made a group present in both the pre-write and the post-write consistent state disappear from the result, and produced a group present in neither. Found by adversarial dual-judge review of `ac5b4b9`, after this batch was recorded. Two fix rounds were implemented and both were rejected by re-judgment — see `design.md` §D1a for the measurements. Owned by WU2b; `engine.py` and `vocabulary_repository.py` are unmodified from `ac5b4b9`, and the round-2 implementation with its test is preserved on `feat/vocabulary-read-snapshot-isolation` at `ed7e9f3`, whose commit message enumerates four defects two independent judges each confirmed.
2. **`vocabulary_repository.py`'s module docstring states a snapshot the runtime does not provide.** Its opening paragraph reads "Two legs run inside ONE `Session` — one snapshot, a correctness obligation design D1 states explicitly". The `Session` claim is accurate; the snapshot claim is not. The file is not edited by this specification change, so the wrong claim is recorded here rather than left unstated (AGENTS.md §10: no known defect hidden). Correcting it is WU2b's, alongside the fix the docstring would then describe.

### Remaining Tasks (WU2b+, not in this batch)

- [ ] WU2b (Phase 2b) — snapshot isolation; no task IDs yet, blocked on the open journal-mode decision (`design.md` §Open Questions).
- [ ] T12–T62 (Phases 3–10) — not started; out of WU2 scope.
- [ ] T61/T62 — the eleven `REQ-005` traceability rows, outstanding for T1–T11 as well as for every later phase (see Deviations 2).

### Verification (batch 2)

- Focused: `cd apps/api && uv run pytest tests/unit/test_vocabulary_repository_properties.py -q` → 5 passed
- Guards: `cd apps/api && uv run pytest tests/unit/test_no_lemma_naming.py tests/unit/test_no_confidence_action_or_propn_filter.py -q` → 39 passed
- Full suite + coverage: `cd apps/api && uv run pytest --cov=wheel_vocabulary --cov-fail-under=80` → 554 passed, 100.00% coverage
- Lint: `cd apps/api && uv run ruff check .` → All checks passed
- Format: `cd apps/api && uv run ruff format --check .` → 116 files already formatted
- Typecheck: `cd apps/api && uv run mypy src/wheel_vocabulary` → Success: no issues found in 48 source files
- Baseline (before this batch, re-confirmed by re-run before any edit): 549 tests passing, 100.00% coverage

### Workload / PR Boundary

- Mode: chained PR slice (stacked-to-main)
- Current work unit: WU2 — vocabulary repository core (V3 hybrid) + Hypothesis equivalence proof
- Boundary: starts from `feat/vocabulary-browser-wu1-index-migration`'s tip (branched at `main` @ `9c74152`, which already carries the WU1 index migration); ends with `vocabulary_repository.py` + its property test file + the one guard-map extension. Rollback: delete `apps/api/src/wheel_vocabulary/infrastructure/persistence/vocabulary_repository.py` and `apps/api/tests/unit/test_vocabulary_repository_properties.py`; revert the `test_no_lemma_naming.py::_LEMMA_OWNING_FILES` entry.
- Estimated review budget impact: 449 authored lines added (263 new test file + 181 new implementation file + 5-line guard-map extension), against the tasks.md estimate of ~270 — 1.66x. The implementation file itself (181 lines) is close to a typical "repository + dataclass" comparable; the overrun is concentrated in the test file, consistent with this repo's established density for Hypothesis property-test modules (design's own forecast note: `test_annotate_import_properties.py` is 553 lines for a comparable precedent).

## Batch 3 — Phase 3 / WU3 (T12–T21)

**Mode**: Strict TDD
**Delivery**: chained, stacked-to-main
**Branch**: `feat/vocabulary-browser-wu3-guards`

### Completed Tasks

- [x] T12–T17 [TEST/IMPL] Added vocabulary repository provenance-isolation and manual-correction write guards, including mutation and boundary controls.
- [x] T18–T20 [TEST/IMPL] Registered the repository with the confidence guard, added `mean_confidence`, and added three confidence-action mutation checks.
- [x] T21 [TEST] Ran Phase 3 and full backend validation.

### Verification

- Focused Phase 3: `cd apps/api && uv run pytest tests/unit/test_vocabulary_repository_isolation.py tests/unit/test_vocabulary_write_guard.py tests/unit/test_no_confidence_action_or_propn_filter.py -q` → 24 passed.
- Backend suite: `make test-backend` → 574 passed.
- Quality: `make lint-backend`, `make typecheck-backend`, and `make format` → passed.

### Workload / PR Boundary

- Mode: chained PR slice (stacked-to-main).
- Boundary: WU3 added only structural guards and their test controls. Rollback deletes the two guard files and reverts the confidence-guard update.

## Batch 4 — Phase 4 / WU4 (T22)

**Mode**: Strict TDD
**Delivery**: chained, stacked-to-main
**Branch**: `feat/vocabulary-browser-wu4-repository-tests`

### Completed Tasks

- [x] T22 [TEST] Added repository integration coverage for homographs, direct ORM-seeded corrections, `NULL` buckets, unknown versus empty books, literal D5 ordering, and repeated-read stability.

### Files Changed

| File | Action | What Was Done |
|------|--------|---------------|
| `apps/api/tests/integration/test_vocabulary_repository.py` | Created | Five SQLite-backed repository integration tests covering T22 scenarios and positional ordering. |
| `openspec/changes/vocabulary-browser/tasks.md` | Modified | Marked T22 complete. |
| `openspec/changes/vocabulary-browser/apply-progress.md` | Modified | Preserved WU1–WU3 history and recorded WU4 evidence. |

### TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| T22 | `tests/integration/test_vocabulary_repository.py` | Integration (SQLite) | ✅ 8/8 existing repository tests passed before the new file | ➖ Existing WU2 behavior already satisfied the repository scenarios; no honest behavior-absence RED was possible without deleting implementation. Mutation control: changing D5 from count-descending to ascending made the new suite fail, 2 failed / 3 passed. | ✅ 5/5 passed | ✅ Five scenarios include non-empty homographs, full and per-field corrections, NULL buckets, empty versus unknown, and literal tie-break ordering | ➖ None needed; only a new test file was added. |

### Test Summary

- **Total tests written**: 5 integration tests.
- **Total tests passing**: 13 repository/vocabulary tests; `vocabulary_repository.py` reached 100% line and branch coverage in that run.
- **Layers used**: Integration (5 new tests).
- **Approval tests**: None — no production refactor.
- **Pure functions created**: 0.

### Work Unit Evidence

| Evidence | Result |
|----------|--------|
| Focused test command and exact result | `cd apps/api && uv run pytest tests/integration/test_vocabulary_repository.py -q` → 5 passed in 0.26s. |
| Runtime harness command/scenario and exact result | `cd apps/api && uv run pytest tests/integration/test_vocabulary_repository.py tests/unit/test_vocabulary_repository_properties.py tests/integration/test_vocabulary_read_scenario.py --cov=wheel_vocabulary --cov-report=term-missing -q` → 13 passed in 1.70s; exercised repository reads against temporary SQLite databases. |
| Rollback boundary | Delete `apps/api/tests/integration/test_vocabulary_repository.py`; no production behavior changes. |

### Verification

- Mutation control: temporary count-ascending D5 mutation → 2 failed, 3 passed; restored before final validation.
- Relevant repository/vocabulary tests with coverage: 13 passed in 1.70s; `vocabulary_repository.py` 100% line and branch coverage. The selected run reports 58% project-wide coverage because it does not execute unrelated modules; it does not replace the full-suite 80% gate.
- Quality: `cd apps/api && uv run ruff check . && uv run ruff format --check . && uv run mypy src/wheel_vocabulary` → all checks passed; 120 files already formatted; 48 source files typechecked.

### Deviations from Design

None — the tests assert the design D5 sequence and existing repository behavior without changing production code.

### Issues Found

The prior failed verification report remains untracked and unchanged. It records incomplete WU5–WU10 work and the deferred WU2b snapshot-isolation defect; neither is in WU4 scope.

### Remaining Tasks

- [ ] T23–T62 — pending; T23 applies only if T22 exposes a repository defect, which it did not.
- [ ] WU2b — snapshot-isolation work remains blocked on the journal-mode decision.

### Workload / PR Boundary

- Mode: chained PR slice (stacked-to-main).
- Current work unit: WU4 — repository integration tests.
- Boundary: starts from WU3 on main and ends with one integration test file plus SDD completion evidence. Rollback deletes only the new test file and reverts the two SDD artifact updates.
- Estimated review budget impact: 196 authored test lines plus artifact updates, within the 400-line budget.

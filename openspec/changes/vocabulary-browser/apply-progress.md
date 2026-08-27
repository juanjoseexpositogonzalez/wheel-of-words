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
- [x] T5 [TEST] T1 green; runtime harness (`alembic upgrade head` + `alembic downgrade -1`) both exit 0.

### Files Changed

| File | Action | What Was Done |
|------|--------|---------------|
| `apps/api/migrations/versions/0004_vocabulary_group_index.py` | Created | `revision="0004_vocabulary_group_index"`, `down_revision="0003_annotation"`; additive `op.create_index`/`op.drop_index` on `ix_occurrence_book_lemma_pos`. |
| `apps/api/src/wheel_vocabulary/infrastructure/persistence/models.py` | Modified | Added `Index("ix_occurrence_book_lemma_pos", "book_id", "lemma", "pos")` to `Occurrence.__table_args__`. |
| `apps/api/tests/integration/test_alembic_0004.py` | Created | Two tests: upgrade adds the index / downgrade removes it and restores `alembic_version`; downgrade touches no other schema object. |
| `apps/api/tests/unit/test_no_lemma_naming.py` | Modified | `_LEMMA_OWNING_FILES` extended for `models.py` and the new migration; `_ALLOWED_LEMMA_SYMBOLS` extended with the exact index-name literal; the allow-list self-check test updated to match. |
| `apps/api/tests/integration/test_alembic_0003.py` | Modified | Pinned `test_upgrade_adds_lemma_provenance_and_correction` to explicit revision strings (`0003_annotation`/`0002_book_occurrence`) instead of `head`/`-1` — see Deviations. |

### TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| T1 | `tests/integration/test_alembic_0004.py` | Integration | ✅ 546/546 (pre-existing baseline, full suite) | ✅ Written — asserted failure: `AssertionError: assert 'ix_occurrence_book_lemma_pos' in {'ix_occurrence_book_norm_raw'}` (revision `0004` did not exist, `head` resolved to `0003_annotation`) | ✅ 2/2 passed after T2+T4 | ✅ 2 cases (upgrade/downgrade positive; downgrade-touches-nothing-else negative) | ➖ None needed |
| T2 | N/A (migration, not test) | — | N/A | — | — | — | — |
| T3 | `tests/unit/test_no_lemma_naming.py` | Unit | ✅ 32/33 passing pre-change (1 pre-existing pass, guard test itself) | ✅ Ran guard, observed real failure: 3 violations for `ix_occurrence_book_lemma_pos`/`lemma` literals in the new migration before the allow-list extension | ✅ 33/33 after extending `_LEMMA_OWNING_FILES` + `_ALLOWED_LEMMA_SYMBOLS` + the self-check test | ➖ Single (guard is structural, one behavior) | ➖ None needed |
| T4 | Covered by T1's integration test | — | ✅ | ✅ (T1's RED covered this) | ✅ | ➖ Covered by T1 | ➖ None needed |
| T5 | Full suite + runtime harness | Integration | ✅ 546/546 baseline | N/A | ✅ 548/548 | N/A | N/A |

### Test Summary

- **Total tests written**: 2 (new file) + 1 modified (pre-existing regression fix, not new)
- **Total tests passing**: 548/548 (baseline 546 + 2 new)
- **Layers used**: Integration (2 new + 1 fixed)
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

- Focused: `cd apps/api && uv run pytest tests/integration/test_alembic_0004.py -q` → 2 passed
- Guard: `cd apps/api && uv run pytest tests/unit/test_no_lemma_naming.py -q` → 33 passed
- Runtime harness: `cd apps/api && uv run alembic upgrade head && uv run alembic downgrade -1` → both exit 0
- Full suite + coverage: `cd apps/api && uv run pytest --cov=wheel_vocabulary --cov-fail-under=80` → 548 passed, 100.00% coverage
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

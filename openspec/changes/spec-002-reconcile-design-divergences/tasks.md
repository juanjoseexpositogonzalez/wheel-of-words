# Tasks: Reconcile SPEC-002 Design Divergences

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | 30–50 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single documentation-only PR |
| Delivery strategy | single-pr |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|
| 1 | Reconcile SPEC-002 contracts | Single PR | `cd apps/api && uv run pytest tests/unit/test_import_contract.py tests/unit/test_tokenizer.py tests/unit/test_normalizer.py tests/unit/test_traceability.py` | N/A — documentation-only | Revert the two OpenSpec documents |

No new RED test is planned: the threat matrix is N/A and this change documents already-tested behavior.

## Phase 1: Evidence Baseline

- [x] T101 [TEST] Run the focused existing contract, tokenizer/normalizer, and traceability checks; files: `apps/api/tests/unit/{test_import_contract,test_tokenizer,test_normalizer,test_traceability}.py`; REQ-RECONCILE-001..004 / AC-002-01, AC-002-24; done when green before edits; est. 0 lines.

## Phase 2: Specification Reconciliation

- [x] T201 [IMPL] Replace §2.2 T1 in `openspec/changes/text-import/specs/002-text-import/spec.md` with SHY-transparent tokenization, verbatim raw/display preservation, and normalization/grouping-key-only removal; REQ-RECONCILE-002 / AC-002-24; done when no document pre-pass is authorized; est. 8–12 lines.
- [x] T202 [IMPL] Add the `INVALID_REQUEST`/422 request-validation row to §4 of `openspec/changes/text-import/specs/002-text-import/spec.md`, citing `AC-002-01` and the shared actionable error envelope; REQ-RECONCILE-001; done when existing error rows remain distinct; est. 3–5 lines.

## Phase 3: Design Reconciliation

- [x] T301 [IMPL] Update §5 and §10 `CONTRA-2` in `openspec/changes/text-import/design.md` to remove divergence framing, mark it Closed, and mirror T1/`AC-002-24`; REQ-RECONCILE-003; done when no document-level rewrite is permitted; est. 10–16 lines.

## Phase 4: Documentation Verification

- [x] T401 [REFACTOR] Review the two changed documents together for identical SHY, envelope, and closed-contradiction language; files: both targets; REQ-RECONCILE-001..003; done when no scope expands to runtime or test sources; est. 0–4 lines.
- [x] T402 [TEST] Re-run the Phase 1 focused checks and inspect `git diff -- docs/traceability-matrix.md`; REQ-RECONCILE-004; done when checks pass and the matrix has no diff; est. 0 lines.
- [x] T403 [DOC] Inspect `docs/traceability-matrix.md` without editing it; REQ-RECONCILE-004; done when `REQ-001-*`, `REQ-002-*`, and AC rows remain unchanged; est. 0 lines.

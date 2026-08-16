# Apply Progress: Reconcile SPEC-002 Design Divergences

## Status

Completed all assigned tasks (`T101`, `T201`, `T202`, `T301`, `T401`, `T402`, and `T403`). This is a documentation-only reconciliation; no runtime, API schema, test, migration, frontend, or traceability-matrix source was changed.

## Completed Tasks

- [x] T101 [TEST] Ran focused baseline contract, tokenizer/normalizer, and traceability checks.
- [x] T201 [IMPL] Replaced T1 with the SHY-transparent, source-preserving contract.
- [x] T202 [IMPL] Added the `INVALID_REQUEST`/422 request-validation error row and shared-envelope statement.
- [x] T301 [IMPL] Reconciled §5 and closed `CONTRA-2` in the text-import design.
- [x] T401 [REFACTOR] Reviewed both documents for identical SHY, envelope, and contradiction language.
- [x] T402 [TEST] Re-ran focused checks and confirmed the traceability matrix has no diff.
- [x] T403 [DOC] Inspected the traceability matrix without editing it.

## Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command and exact result | `cd apps/api && uv run pytest tests/unit/test_import_contract.py tests/unit/test_tokenizer.py tests/unit/test_normalizer.py tests/unit/test_traceability.py` — baseline: `92 passed in 0.57s`; post-edit: `92 passed in 0.48s`. |
| Runtime harness command/scenario and exact result | N/A — this documentation-only work changes no runtime boundary; existing unit contract and tokenizer checks exercise the shipped behavior cited by the documentation. |
| Traceability inspection | `git diff -- docs/traceability-matrix.md` — exit 0 with no output; the matrix was inspected and remains unchanged. |
| Rollback boundary | Revert only `openspec/changes/text-import/specs/002-text-import/spec.md` and `openspec/changes/text-import/design.md`; runtime behavior and unrelated artifacts remain untouched. |

## TDD Cycle Evidence

Strict TDD is configured project-wide, but the approved scope is documentation-only and explicitly authorizes no production or test-source changes. No RED test was applicable or written; existing focused tests were run before and after the documentation update.

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| T101 | `test_import_contract.py`, `test_tokenizer.py`, `test_normalizer.py`, `test_traceability.py` | Unit | 92/92 passed before edits | N/A — existing evidence baseline | 92/92 passed after edits | N/A — no behavior changed | N/A — no code refactor |
| T201 | Existing tokenizer/normalizer checks | Unit | 92/92 passed before edits | N/A — documentation-only contract reconciliation | 92/92 passed after edits | N/A — no behavior changed | Reviewed for T1/AC-002-24 consistency |
| T202 | Existing import-contract checks | Unit | 92/92 passed before edits | N/A — documentation-only contract reconciliation | 92/92 passed after edits | N/A — no behavior changed | Reviewed for shared-envelope consistency |
| T301 | Existing tokenizer/normalizer checks | Unit | 92/92 passed before edits | N/A — documentation-only design reconciliation | 92/92 passed after edits | N/A — no behavior changed | Reviewed §5 and §10 consistency |
| T401–T403 | Existing focused checks and matrix diff | Unit / documentation | 92/92 passed before edits | N/A — verification-only tasks | 92/92 passed after edits; matrix diff empty | N/A — no behavior changed | Completed document and matrix review |

## TDD Test Summary

- Total tests written: 0 — no behavior change was authorized.
- Total focused tests passing: 92.
- Layers used: Unit (92 tests).
- Approval tests: None — no runtime refactor.
- Pure functions created: 0.

## Design Conformance

- `INVALID_REQUEST` is documented as HTTP 422 for missing multipart files or incompatible request bodies, cites `AC-002-01`, and uses the shared actionable error envelope.
- T1 prohibits a document-level SHY rewrite, preserves SHY in `raw_text`/`display_form`, and limits removal to normalization/grouping keys.
- `CONTRA-2` is Closed and uses the same contract as T1 and `AC-002-24`.
- Traceability identifiers and rows remain unchanged.

## Workload / PR Boundary

- Mode: single PR.
- Current work unit: Reconcile SPEC-002 contracts.
- Boundary: the two active text-import OpenSpec documents plus this change's tasks and apply-progress artifacts.
- Estimated review budget impact: documentation-only change, below the 400-line budget.

## Deviations and Issues

None — implementation matches the approved documentation-only design. The native runtime attempt was already authorized by the orchestrator; no settlement command was run.

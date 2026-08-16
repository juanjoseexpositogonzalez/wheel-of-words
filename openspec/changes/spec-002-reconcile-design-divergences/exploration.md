## Exploration: Reconcile SPEC-002 design divergences before apply

### Current State
Issue #17 is a documentation/specification reconciliation pass over the active SPEC-002 OpenSpec artifacts; no product implementation change is required.

The two divergences are still present in the repository:

- `openspec/changes/text-import/design.md` §9.2 defines `INVALID_REQUEST` as a 422 response for FastAPI `RequestValidationError`, with the JSON-body/no-file-part case explicitly tied to `AC-002-01`. The spec's §4 error table at lines 867–877 omits this code.
- The spec's §2.2 T1 currently says that U+00AD SOFT HYPHEN is “removed from the text before tokenization.” This wording permits a document-level rewrite, while the design's §5 and §10 CONTRA-2 establish that the character must remain in `raw_text` so `AC-002-24` can continue to require a verbatim source substring. The implementation and tests already reflect the transparent-tokenizer interpretation: the tokenizer test expects the SHY to remain in `raw_text`, and the normalizer removes it from the grouping key.

The design is partially reconciled already: its amendment preamble says CONTRA-2 is resolved, and §5 documents the correct behavior. However, the authoritative contradiction table at §10 still says “Confirm the reading; no spec edit strictly required,” so the design artifact is internally inconsistent with its own amendment and with the requested issue resolution.

`docs/traceability-matrix.md` contains the existing REQ-002 rows and already references `AC-002-24` and the relevant tests. No requirement or acceptance-criterion identifier needs to change, and the protected `REQ-001-*` range must remain untouched.

### Affected Areas
- `openspec/changes/text-import/specs/002-text-import/spec.md` — add `INVALID_REQUEST` to §4 with HTTP 422, its request-validation trigger, and an explicit `AC-002-01`/error-envelope contract reference; reword §2.2 T1 to describe transparent tokenization plus normalization rather than a document-level pre-pass, and cross-reference `AC-002-24`.
- `openspec/changes/text-import/design.md` — update §10 CONTRA-2 from provisional confirmation to closed, matching the already-implemented behavior documented in §5 and the amendment preamble.
- `docs/traceability-matrix.md` — inspect only; no row update is indicated because identifiers and existing REQ-002 evidence remain unchanged.
- `apps/api/tests/api/test_imports.py` and `apps/api/tests/unit/test_import_contract.py` — existing tests already cover the `INVALID_REQUEST` envelope and its `AC-002-01` rejection path; they are validation evidence, not expected implementation targets.
- `apps/api/tests/unit/test_tokenizer.py` — existing T1 regression test pins SHY in `raw_text`, which protects the intended `AC-002-24` interpretation.

### Approaches
1. **Minimal artifact reconciliation** — change only the two specified sections in `spec.md` and the CONTRA-2 status/wording in `design.md`; leave traceability and product code untouched.
   - Pros: exactly matches issue #17 scope, preserves all identifiers, avoids editorial drift, and aligns normative wording with already-tested behavior.
   - Cons: relies on existing tests rather than adding a dedicated documentation consistency test.
   - Effort: Low

2. **Reconciliation plus new documentation guard** — make the same artifact edits and add a static test asserting the error-table and T1/CONTRA-2 wording.
   - Pros: future drift in these prose contracts would be detected automatically.
   - Cons: expands a narrow documentation-only issue into test-maintenance work, risks coupling tests to exact prose, and does not add product behavior coverage.
   - Effort: Medium

### Recommendation
Use the minimal artifact reconciliation. Add `INVALID_REQUEST` as a §4 contract row whose trigger is request validation (for example, a JSON body or missing multipart file), explicitly mapping the rejection to `AC-002-01` while also stating that the row closes the §4 requirement that every route error use the shared envelope. Reword T1 to say that SHY is transparent to token boundary detection and removed only from the normalized grouping key; retain it in the emitted/raw token text and cross-reference `AC-002-24`. Mark CONTRA-2 **Closed** and state that no document-level rewrite is permitted. Do not modify the traceability matrix because no REQ/AC identifier changes.

For validation, run the existing focused tests (`tests/api/test_imports.py` request-validation case, `tests/unit/test_import_contract.py`, and `tests/unit/test_tokenizer.py`) plus the repository documentation/traceability guard. No new test is necessary unless the proposal explicitly chooses to enforce prose consistency mechanically.

### Risks
- If T1 is reworded as removing SHY from the emitted token rather than only from normalization/grouping, it would contradict the existing `raw_text` test and undermine `AC-002-24`.
- If `INVALID_REQUEST` is described only as an implementation detail, the spec will still lack a complete error contract; the row should reference both `AC-002-01` and the shared-envelope completeness rule.
- The design contains other historical provisional notes (for example, CONTRA-3, CONTRA-4, and CONTRA-6); changing them would exceed issue #17 scope.
- `mockups/` is already untracked and must not be included in this change.

### Ready for Proposal
Yes. No additional product or business clarification is required: the issue supplies the intended resolution, and current implementation/tests establish the observable semantics. The proposal should remain documentation-only, explicitly preserve all REQ/AC identifiers, and list `docs/traceability-matrix.md` as inspected with no change expected.

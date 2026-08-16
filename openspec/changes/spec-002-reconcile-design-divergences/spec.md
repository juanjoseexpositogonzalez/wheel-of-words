# Delta for 002-text-import: Design Divergence Reconciliation

This documentation-only delta preserves all existing `REQ-002-*`, `AC-002-*`, and
`REQ-001-*` identifiers. It changes no runtime, schema, test, migration, or frontend behavior.

## ADDED Requirements

### Requirement: REQ-RECONCILE-001 — Complete request-validation error contract

The SPEC-002 error table MUST document `INVALID_REQUEST` as HTTP 422 for request-validation
failures, including requests that omit the required multipart file or submit an incompatible body.
The row MUST reference `AC-002-01` and state that the response uses the shared error envelope,
including a distinct code and actionable message.

#### Scenario: Request validation is represented in the error table

- GIVEN the SPEC-002 §4 error table is inspected
- WHEN request-validation errors are reviewed
- THEN `INVALID_REQUEST`, HTTP 422, its request-validation trigger, `AC-002-01`, and shared-envelope completeness are present

#### Scenario: Existing error semantics remain distinct

- GIVEN the documented file-type, size, encoding, and not-found errors
- WHEN the reconciled table is compared with the existing rows
- THEN those rows and their identifiers remain unchanged

### Requirement: REQ-RECONCILE-002 — Preserve SOFT HYPHEN source text

T1 MUST define U+00AD SOFT HYPHEN as transparent to token-boundary detection. It MUST NOT permit
a document-level rewrite. SOFT HYPHEN MUST remain in emitted raw/display text for `AC-002-24` and
MAY be removed only from normalization/grouping keys.

#### Scenario: SHY remains verbatim while grouping normally

- GIVEN source text containing `inter\u00ADnational`
- WHEN T1 is applied and the result is checked against `AC-002-24`
- THEN the raw/display value retains U+00AD while the normalization/grouping key omits it

#### Scenario: No document pre-pass is authorized

- GIVEN a source containing SOFT HYPHEN and a decomposed Unicode sequence
- WHEN the T1 contract is interpreted
- THEN neither source text nor raw token slices are rewritten before tokenization

### Requirement: REQ-RECONCILE-003 — Close CONTRA-2 consistently

The design record `CONTRA-2` MUST be marked **Closed** and MUST state that no document-level
rewrite is permitted. Its resolution MUST agree with T1 and `AC-002-24`, including preservation of
raw/display text and removal of SOFT HYPHEN only from normalization/grouping keys.

#### Scenario: Contradiction status agrees across artifacts

- GIVEN T1, `AC-002-24`, design §5, and design §10 `CONTRA-2`
- WHEN their normative statements are compared
- THEN they all express the same no-document-rewrite behavior and `CONTRA-2` is Closed

### Requirement: REQ-RECONCILE-004 — Preserve traceability identity

Inspection of `docs/traceability-matrix.md` MUST confirm that all existing identifiers and rows,
including the protected `REQ-001-*` range, remain unchanged. The reconciliation MUST NOT add a
documentation guard unless a later approved change explicitly requires one.

#### Scenario: Matrix inspection produces no identifier changes

- GIVEN the traceability matrix before reconciliation
- WHEN it is inspected after the documentation delta
- THEN its requirement and acceptance-criterion identifiers and rows are unchanged

#### Scenario: Validation uses existing evidence

- GIVEN the documentation delta is ready for verification
- WHEN focused request-contract, tokenizer, and traceability/documentation guard checks run
- THEN they pass without product or test-source changes

## Validation Expectations

Run the existing request-validation contract tests, `test_import_contract.py`, the tokenizer tests,
and the repository documentation/traceability guard. No new guard is required by this delta.

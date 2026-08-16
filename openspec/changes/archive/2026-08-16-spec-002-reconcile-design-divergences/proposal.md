# Proposal: Reconcile SPEC-002 Design Divergences

## Intent

Remove two conflicting documentation contracts in SPEC-002 so users, maintainers, and implementers share the behavior already protected by tests: request-validation failures use the common error envelope, and SOFT HYPHEN does not invalidate verbatim display forms.

## Scope

### In Scope
- Add `INVALID_REQUEST` (HTTP 422) to the SPEC-002 error table, tied to `AC-002-01` and the shared error-envelope completeness contract.
- Reword T1: U+00AD SOFT HYPHEN is transparent to token boundaries, preserved in raw/display text for `AC-002-24`, and removed only from normalization/grouping keys.
- Close design `CONTRA-2` with the same no-document-rewrite decision.
- Inspect `docs/traceability-matrix.md`; retain it unchanged because REQ/AC identifiers do not change.

### Out of Scope
- Product/runtime code, API schemas, tests, migrations, and frontend changes.
- New documentation guards, edits to other contradiction records, or editorial cleanup beyond GitHub issue #17.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `002-text-import`: reconcile its normative T1 and error-envelope requirements without changing identifiers or runtime semantics.

## Approach

Apply a minimal documentation-only delta to the active SPEC-002 spec and design. Preserve existing REQ-002 and AC-002 identifiers; use the current API contract and tokenizer tests as validation evidence. Sizing: a small single PR, below the 400-line review budget; no chained slice is needed.

## Reconciliation Acceptance Criteria

- `INVALID_REQUEST` is documented as HTTP 422 for request validation, references `AC-002-01`, and is included in the shared error envelope.
- T1 forbids document-level SHY rewriting while preserving SHY in `raw_text`/`display_form` and removing it only from normalization/grouping keys.
- `CONTRA-2` is marked Closed and agrees with the T1 and `AC-002-24` contracts.
- Traceability identifiers and rows remain unchanged.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `openspec/changes/text-import/specs/002-text-import/spec.md` | Modified | Error table and T1 wording |
| `openspec/changes/text-import/design.md` | Modified | Close `CONTRA-2` |
| `docs/traceability-matrix.md` | Inspected | No change expected |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| SHY wording loses verbatim-source guarantee | Low | Check against `AC-002-24` and tokenizer test |
| Error row omits envelope completeness | Low | Require both `AC-002-01` and shared-contract references |
| Scope expands into historic notes | Low | Limit edits to issue #17 |

## Rollback Plan

Revert the documentation-only commit. Runtime behavior, schemas, tests, and persisted data are unchanged.

## Dependencies

- Existing SPEC-002 API-contract and tokenizer tests as validation evidence.

## Success Criteria

- [ ] The reconciliation acceptance criteria are met by the updated artifacts.
- [ ] Focused contract/tokenizer tests and the documentation/traceability guard pass without code changes.

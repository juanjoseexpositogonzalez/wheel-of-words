# Design: Reconcile SPEC-002 Design Divergences

## Technical Approach

Make a narrow documentation-only reconciliation of the implemented `002-text-import` contract. Update the active text-import delta, not runtime sources: complete §4's error table, replace §2.2 T1's document-rewrite wording, and close `CONTRA-2` in the design. This implements `REQ-RECONCILE-001` through `REQ-RECONCILE-004` while preserving `REQ-002-*`, `AC-002-*`, and `REQ-001-*` identities.

## Architecture Decisions

| Decision | Alternatives considered | Rationale |
|---|---|---|
| Align documentation with shipped behavior | Change handler/tokenizer/schema/tests | `api/errors.py` already maps validation failures to `INVALID_REQUEST`/422 in the shared envelope; tokenizer and normalizer already retain SHY in `raw_text` and remove it from the grouping key. Runtime changes would be unrelated scope expansion. |
| Define SHY as tokenizer-transparent, normalization-only removal | Document a pre-tokenization removal; weaken `AC-002-24` | A document pre-pass would make emitted `raw_text` not verbatim source text. The existing T1 tests prove a single raw token retains SHY and normalization removes it. |
| Inspect, do not modify the traceability matrix | Add reconciliation rows or renumber existing rows | No protected requirement or acceptance identifier changes. `test_traceability.py` requires exactly one row per `REQ-001-001..018` and `REQ-002-001..018`; new rows would create false traceability scope. |

## Data Flow

No runtime data flow changes. Documentation alignment follows:

    shipped handler/tokenizer tests
              │
              ▼
    SPEC-002 §2.2 / §4 ──→ text-import design §5 / §10
              │
              ▼
      unchanged traceability matrix

## File Changes

| File | Action | Description |
|---|---|---|
| `openspec/changes/text-import/specs/002-text-import/spec.md` | Modify | In §2.2, replace T1's document-level removal with SHY-transparent tokenization, raw/display preservation, and normalization/grouping-key removal. In §4, add `INVALID_REQUEST` / 422 for request validation, reference `AC-002-01`, and state the shared envelope. |
| `openspec/changes/text-import/design.md` | Modify | In §5, remove the now-resolved divergence framing; in §10, mark `CONTRA-2` Closed and state the same no-document-rewrite contract. |
| `docs/traceability-matrix.md` | Inspect only | Confirm all existing `REQ-001-*`, `REQ-002-*`, and AC references/rows remain unchanged; do not edit. |

## Interfaces / Contracts

No new interface, schema, or runtime contract is introduced. The documentation will explicitly describe the existing error envelope and tokenization semantics:

```text
422 INVALID_REQUEST → { "error": { "code", "message" } }
source "inter<U+00AD>national" → raw/display retain U+00AD
                                → normalization/grouping key: "international"
```

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | Shared request-validation envelope | Run `cd apps/api && uv run pytest tests/unit/test_import_contract.py`; it asserts 422 and `INVALID_REQUEST`. |
| Unit | T1 raw-text preservation and key normalization | Run `cd apps/api && uv run pytest tests/unit/test_tokenizer.py tests/unit/test_normalizer.py`; existing cases retain SHY in `raw_text` and strip it in `normalize()`. |
| Documentation | Identifier/row stability | Run `cd apps/api && uv run pytest tests/unit/test_traceability.py`; inspect the matrix diff is empty and confirm no `REQ-001-*`, `REQ-002-*`, or AC identifier changed. |
| Review | Exact normative reconciliation | Review changed sections against `AC-002-01`, `AC-002-24`, and `REQ-RECONCILE-001..004`; no RED test or new test source is planned because behavior is unchanged. |

## Threat Matrix

N/A — this change edits documentation only and introduces no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

No migration required. Deliver one documentation-only PR below the 400-line budget. Roll back by reverting that commit; deployed behavior, schemas, persisted data, and tests are unchanged.

## Open Questions

None. The existing implementation and focused tests resolve the wording choices.

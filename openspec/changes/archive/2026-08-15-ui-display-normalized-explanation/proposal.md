# Proposal: Show Normalized Keys in Frequency Results

## Intent

Users can see the textual form selected for a frequency group but cannot inspect
the API-provided key that groups related forms. Show both values so grouping is
understandable without implying a canonical spelling or applying linguistic logic
in the browser.

## Scope

### In Scope
- Show the API-provided `display_form` and `normalized_form` for every frequency row.
- Add concise, accessible explanatory copy that distinguishes the visible text from
  the grouping key; use `Straße` / `strasse` in tests and supporting copy.
- Add focused frontend coverage and a minimal SPEC-002 delta for this observable UI behavior.

### Out of Scope
- Backend, API schema, persistence, import, or linguistic-processing changes.
- Deriving, normalizing, or transforming either form in the frontend.
- Heavy Unicode-oriented UI copy, canonical-spelling claims, or lemma/lexeme labels.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `002-text-import`: record that each frequency row presents both API-provided forms and a simple explanation of their distinct roles.

## Approach

Extend `FrequencyTable` with a secondary normalized-key presentation while keeping
the display form primary. Render both values directly from `FormFrequency`; add
simple localized copy such as “Shown text” and “Grouping key,” illustrated by
`Straße` and `strasse`. Preserve received row order and all existing naming guards.

## Acceptance Criteria

- Each rendered row exposes its API-provided display form and normalized key.
- `Straße` remains the displayed text while `strasse` is visible as its grouping key.
- Explanatory copy is accessible, simple, and does not present the key as a canonical form.
- Tests prove the UI performs no linguistic transformation or derivation.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `apps/web/src/components/FrequencyTable.tsx` | Modified | Present both values and explanatory copy. |
| `apps/web/tests/components/FrequencyTable.test.tsx` | Modified | Cover row values, copy, and API-only rendering. |
| `openspec/changes/ui-display-normalized-explanation/specs/002-text-import/spec.md` | New | Minimal observable-behavior delta. |

## Risks and Validation

| Risk | Likelihood | Mitigation |
|---|---|---|
| Key appears to be canonical spelling | Medium | Secondary label and `Straße`/`strasse` assertion. |
| Frontend adds linguistic rules | Low | Contract tests and direct-value component tests. |
| SPEC-002 hotspot contention | Medium | Keep delta isolated and minimal. |

Validate with focused Vitest component/contract tests, frontend typecheck and lint;
add Playwright coverage only if the resulting copy is part of the primary import flow.

## Rollback Plan

Revert the UI presentation and its delta spec together; API and stored data remain unchanged.

## Dependencies

- Existing `FormFrequency.display_form` and `FormFrequency.normalized_form` API contract.

## Delivery Size

Estimated 60–120 changed lines. Chained slice need: No; fits the 400-line single-PR budget.

## Success Criteria

- [ ] The acceptance criteria pass without backend or linguistic-processing changes.
- [ ] The frequency screen clearly distinguishes displayed text from its grouping key.

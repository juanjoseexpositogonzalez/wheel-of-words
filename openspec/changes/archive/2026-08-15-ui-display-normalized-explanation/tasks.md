# Tasks: Display Normalized-Form Explanation

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | 90–140 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single UI-only PR |
| Delivery strategy | single-pr |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|
| 1 | Render API display text and grouping key | Single PR | `cd apps/web && pnpm exec vitest run tests/components/FrequencyTable.test.tsx tests/contracts/no-linguistic-rules.test.ts` | Import a fixture and visually confirm three columns at narrow width | `FrequencyTable.tsx`, its component test, and this delta |

## Phase 1: Test-First UI Contract

- [x] T101 [TEST] `apps/web/tests/components/FrequencyTable.test.tsx` — RED: require three columns and direct display/key/frequency cells for each received row. REQ-UI-DISPLAY-NORMALIZED-001/-004; done when the focused component test fails solely for the absent column; est. 25–40 lines.
- [x] T102 [TEST] `apps/web/tests/components/FrequencyTable.test.tsx` — RED: assert `Straße` stays first-cell display text, `strasse` is its grouping-key cell, and caption/headers explain roles without canonical, lemma, or lexeme claims. REQ-UI-DISPLAY-NORMALIZED-002/-003; done when failing against current markup; est. 20–35 lines.

## Phase 2: Minimal Rendering

- [x] T201 [IMPL] `apps/web/src/components/FrequencyTable.tsx` — add a secondary grouping-key header/cell between primary display text and frequency; revise caption using concise role-based copy. REQ-UI-DISPLAY-NORMALIZED-001/-003; done when T101–T102 pass with received order and zero state unchanged; est. 20–35 lines.
- [x] T202 [REFACTOR] `apps/web/src/components/FrequencyTable.tsx`, `apps/web/tests/components/FrequencyTable.test.tsx` — remove duplication and preserve direct field rendering; do not sort, normalize, or derive strings. REQ-UI-DISPLAY-NORMALIZED-004/-005; done when focused component and existing contract tests pass; est. 5–15 lines.

## Phase 3: Verification and Traceability

- [x] T301 [TEST] `apps/web/tests/contracts/no-linguistic-rules.test.ts` — run, do not edit, the existing AST guard with the component test: `cd apps/web && pnpm exec vitest run tests/components/FrequencyTable.test.tsx tests/contracts/no-linguistic-rules.test.ts`. REQ-UI-DISPLAY-NORMALIZED-004/-005; done when both pass; est. 0 lines.
- [x] T302 [SPEC] `openspec/changes/ui-display-normalized-explanation/spec.md` — verify REQ-UI-DISPLAY-NORMALIZED-001 through -005 map to T101–T301; refine only missing task traceability without broadening behavior. Done when the delta remains UI-only; est. 0–10 lines.
- [x] T303 [TEST] `apps/web` — run `pnpm run typecheck` and `pnpm run lint`. REQ-UI-DISPLAY-NORMALIZED-005; done when both commands pass; est. 0 lines.

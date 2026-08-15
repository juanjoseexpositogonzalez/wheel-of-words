# Design: Display Normalized-Form Explanation

## Technical Approach

Extend `FrequencyTable` only. Keep `display_form` as the first, primary table
cell; render the received `normalized_form` in a new secondary **Grouping key**
column, followed by frequency. Update the caption and column headers with short
Spanish UI copy that explains the distinction without describing either value as
a lemma, lexeme, or canonical spelling. This implements
REQ-UI-DISPLAY-NORMALIZED-001 through -005 using the existing `FormFrequency`
contract; no API, import, persistence, or linguistic behavior changes.

## Architecture Decisions

| Decision | Options / trade-off | Rationale |
|---|---|---|
| Present both values as table columns | Row disclosure reduces width but hides the key; a third column makes all values scannable. | The proposal requires every row to expose its grouping key. A semantic table already represents the results. |
| Keep display form first | Put the key first or derive a single display value. | The API-provided textual form remains primary and direct rendering prevents a synthetic key from appearing authoritative. |
| Use caption plus scoped headers | Add helper controls or ARIA-only explanations. | A caption and `scope="col"` headers are concise, visible, and available to assistive technology without extra interaction. |
| Enforce direct rendering with two test layers | Rely only on DOM tests or add transformation code. | Component tests prove exact field-to-cell assignment; the existing AST contract rejects sorting, case folding, normalization, and `Intl.Collator` in this feature. |

## Data Flow

```text
POST /imports response
  -> ImportForm receives ImportResult unchanged
  -> ImportPage stores it unchanged
  -> FrequencyTable maps result.forms in received order
  -> display_form | normalized_form | frequency cells
```

`FrequencyTable` must neither sort `forms` nor transform either string. React
keys may continue to use `normalized_form` and index; they are not user-visible
content.

## File Changes

| File | Action | Description |
|---|---|---|
| `apps/web/src/components/FrequencyTable.tsx` | Modify | Add grouping-key header/cell and revise the caption while preserving the zero state and row order. |
| `apps/web/tests/components/FrequencyTable.test.tsx` | Modify | Update column expectations; assert each row maps received display/key/frequency values, `Straße` remains primary, `strasse` is secondary, and accessible explanatory text avoids overclaiming. |
| `apps/web/tests/contracts/no-linguistic-rules.test.ts` | Retain | Run the existing AST guard; no manifest or rule change is needed because `FrequencyTable` is already covered. |
| `openspec/changes/ui-display-normalized-explanation/spec.md` | Retain | Existing minimal SPEC-002 delta defines the five observable requirements; implementation must not broaden it. |

## Interfaces / Contracts

No interface changes are required. `FormFrequency` is consumed as received:

```ts
interface FormFrequency {
  normalized_form: string; // secondary grouping key
  display_form: string;    // primary shown text
  frequency: number;
}
```

The UI copy should use role-based labels equivalent to `Texto mostrado`, `Clave de agrupación`, and `Apariciones`. The caption must say that rows show text and its grouping key, without explaining Unicode mechanics or making linguistic claims.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Component (RED) | All three values, order, primary/secondary roles, headers/caption, and `Straße`/`strasse`. | Add focused Testing Library assertions to `FrequencyTable.test.tsx`; run it RED before the component edit. |
| Contract | No frontend derivation, sorting, or linguistic APIs. | Run `no-linguistic-rules.test.ts`; its AST scan already includes `FrequencyTable.tsx`. |
| Quality | Type safety and lint compliance. | Run frontend typecheck and lint after focused tests. |
| E2E | Primary upload flow. | No new assertion planned: the existing E2E already proves the table renders, while component tests cover static semantics. Add one only if review identifies a rendered-flow regression. |

Validation commands:

```sh
cd apps/web && pnpm exec vitest run tests/components/FrequencyTable.test.tsx tests/contracts/no-linguistic-rules.test.ts
cd apps/web && pnpm run typecheck
cd apps/web && pnpm run lint
```

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file
classification, or process-integration boundary.

## Migration / Rollout

No migration required. Ship as one UI-only, single-PR slice (estimated under the
400-line review budget). Roll back by reverting the component/test changes and
the SPEC delta together; API and stored data are unaffected.

## Risks

- A prominent key can be mistaken for canonical spelling; keep it secondary and
  use role-based copy only.
- A compact third column may constrain narrow layouts; this plain table has no
  responsive layout abstraction, so verify visually during review before adding
  responsive behavior outside scope.
- Editing the active SPEC-002 area may conflict with parallel work; keep the
  delta isolated at the current change path.

## Open Questions

None.

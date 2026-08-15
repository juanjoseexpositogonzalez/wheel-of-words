# Apply Progress: Display Normalized-Form Explanation

## Status

Complete. The maintainer-authorized pnpm build approval enabled the frontend
toolchain, and the runtime harness was completed after the conflicting
`estimator` container was stopped, the SQLite development database was migrated,
and the existing E2E assertion was made unambiguous for the new grouping-key
cell. All seven tasks are now complete.

## Work Performed

- Added component assertions for three direct API values per row, received order,
  the `Straße`/`strasse` case, and role-based Spanish copy.
- Added the minimal `FrequencyTable` grouping-key column between display text and
  frequency, rendering `row.normalized_form` directly.
- Verified the existing requirement-to-task traceability without changing
  observable behavior.
- Updated the pre-existing import E2E assertion from ambiguous visible text to
  the first matching table cell; this preserves its intent after `lobo` appears
  in both display and grouping-key cells.

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| T101 | `apps/web/tests/components/FrequencyTable.test.tsx` | Component | Existing zero-state test passed | RED reproduced: historical two-column markup failed with missing grouping-key cells | GREEN: 3/3 component tests passed | Three distinct received rows specified | None needed; direct field rendering remains minimal |
| T102 | `apps/web/tests/components/FrequencyTable.test.tsx` | Component | Existing zero-state test passed | RED reproduced: historical markup lacked `Texto mostrado` and `Clave de agrupación` | GREEN: 3/3 component tests passed | `Straße`/`strasse` distinguishes assigned roles | None needed; copy remains role-based |
| T201 | `apps/web/tests/components/FrequencyTable.test.tsx` | Component | Covered by T101/T102 | RED evidence is T101/T102; the historical two-column component cannot satisfy their assertions | GREEN: 3/3 component tests passed after restoring the grouping-key column | Covered by all three received rows | None needed; rendering is direct fields only |
| T202 | `apps/web/tests/components/FrequencyTable.test.tsx` | Component / Contract | Existing component and AST guard tests pass | Covered by T101 direct-rendering assertion | GREEN: focused command passed 10/10 | Contract guard rejects sorting and linguistic APIs | None needed; no duplication introduced |
| T301 | `apps/web/tests/contracts/no-linguistic-rules.test.ts` | Contract | Existing guard retained | Existing AST guard is the RED safety net | GREEN: focused command passed 10/10 | N/A: existing guard | None needed |
| T302 | `openspec/changes/ui-display-normalized-explanation/spec.md` | Documentation | N/A | N/A | Verified REQ-UI-DISPLAY-NORMALIZED-001 through -005 map to T101–T301 | N/A | None needed |
| T303 | `apps/web` | Quality | N/A | N/A | `pnpm run typecheck` and `pnpm run lint` passed | N/A | None needed |

## Work Unit Evidence

| Evidence | Result |
|---|---|
| Focused test command and exact result | `cd apps/web && pnpm exec vitest run tests/components/FrequencyTable.test.tsx tests/contracts/no-linguistic-rules.test.ts` passed: 2 files, 10 tests. The focused component-only GREEN command also passed: 1 file, 3 tests. |
| Runtime harness command/scenario and exact result | `cd apps/web && pnpm exec playwright test e2e/import.spec.ts` passed: 1 test. The `estimator` container that owned port 8000 was stopped; `make migrate` prepared the SQLite development database. The locator now targets `page.getByRole("cell", { name: "lobo" }).first()` because the added grouping-key cell legitimately duplicates that text. |
| Rollback boundary | Revert `FrequencyTable.tsx`, `FrequencyTable.test.tsx`, `apps/web/e2e/import.spec.ts`, `pnpm-workspace.yaml`, this SPEC delta, and these apply artifacts together; no API, persistence, import semantics, or linguistic behavior is affected. |

## Validation Attempts

| Command | Result |
|---|---|
| Maintainer-authorized pnpm build approval | Approved the previously ignored `esbuild@0.21.5` build script; `pnpm-workspace.yaml` records `allowBuilds.esbuild: true`, enabling frontend validation. |
| Historical component markup against the new test | RED reproduced: 2 failures of 3 tests, solely due to the missing grouping-key column and role-based headers/caption. |
| `cd apps/web && pnpm exec vitest run tests/components/FrequencyTable.test.tsx tests/contracts/no-linguistic-rules.test.ts` | PASSED: 2 files, 10 tests. |
| `cd apps/web && pnpm run typecheck` | PASSED (exit 0). |
| `cd apps/web && pnpm run lint` | PASSED (exit 0). |
| Initial runtime attempt | BLOCKED before test execution: port 8000 served the unrelated `estimator` container and its health endpoint returned HTTP 404. |
| Runtime remediation | Stopped `estimator`, then ran `make migrate` from the repository root to prepare the SQLite development database. |
| E2E locator adjustment | Replaced ambiguous `getByText("lobo")` with `getByRole("cell", { name: "lobo" }).first()` because the new grouping-key column displays the same received value. |
| `cd apps/web && pnpm exec playwright test e2e/import.spec.ts` | PASSED: 1 test. |
| `git diff --check` | PASSED (exit 0). |

## Completed Tasks

- [x] T101 through T303 are complete.

## Delivery Boundary

- Mode: single PR.
- Work unit: Render API display text and grouping key.
- Estimated review impact: within the 90–140 line forecast; no size exception required.

```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:eec6bb8906ba08341b9be114f090529d7f56c1878dc3f4a5aa92b4211be8af89
verdict: pass_with_warnings
blockers: 0
critical_findings: 0
requirements: 5/5
scenarios: 5/5
test_command: (cd apps/web && pnpm exec vitest run tests/components/FrequencyTable.test.tsx tests/contracts/no-linguistic-rules.test.ts) && make migrate && (cd apps/web && pnpm exec playwright test e2e/import.spec.ts)
test_exit_code: 0
test_output_hash: sha256:9c5f13ec621e2580c6d3865e86530c14dd1673eaadd193a8db82834d7fbf3872
build_command: (cd apps/web && pnpm run typecheck) && (cd apps/web && pnpm run lint) && git diff --check
build_exit_code: 0
build_output_hash: sha256:da5252feb1a816a7d3b344877109d47d93617826950786b6f11de1f79295a6a8
```

## Verification Report

**Change**: ui-display-normalized-explanation  
**Version**: N/A  
**Mode**: Strict TDD

### Completeness

| Metric | Value |
|---|---:|
| Tasks total | 7 |
| Tasks complete | 7 |
| Tasks incomplete | 0 |

All task checkboxes in `tasks.md` are complete, native SDD status reports `7/7`, and `apply-progress.md` contains matching completion evidence for T101 through T303.

### Candidate Boundary

| Changed area | In scope? | Evidence |
|---|---|---|
| `apps/web/src/components/FrequencyTable.tsx` | ✅ Yes | Adds the grouping-key column and direct `normalized_form` rendering. |
| `apps/web/tests/components/FrequencyTable.test.tsx` | ✅ Yes | Covers direct values, ordering, `Straße`/`strasse`, and explanatory copy. |
| `apps/web/e2e/import.spec.ts` | ✅ Yes | Makes the existing `lobo` assertion unambiguous after both display and key cells contain it. |
| `pnpm-workspace.yaml` | ✅ Yes | Records the maintainer-authorized `esbuild` build-script policy required to run the frontend toolchain. |
| `openspec/changes/ui-display-normalized-explanation/` | ✅ Yes | Contains the SDD proposal, spec, design, tasks, exploration, and apply-progress artifacts. |

No backend, API schema, persistence model, import semantics, or linguistic-processing source changed. The tracked product/config diff is 25 additions and 12 deletions across four files, below the 400-line single-PR review budget.

### Build & Tests Execution

**Tests and runtime harness**: ✅ Passed

```text
(cd apps/web && pnpm exec vitest run tests/components/FrequencyTable.test.tsx tests/contracts/no-linguistic-rules.test.ts) && make migrate && (cd apps/web && pnpm exec playwright test e2e/import.spec.ts)
Vitest: 2 files passed, 10 tests passed.
Alembic: upgraded the SQLite development database to head successfully.
Playwright: 1 Chromium test passed.
Exit code: 0
Output hash: sha256:9c5f13ec621e2580c6d3865e86530c14dd1673eaadd193a8db82834d7fbf3872
```

The previously stopped `estimator` container was not restarted. Playwright started and stopped the project web servers it required.

**Build and static checks**: ✅ Passed

```text
(cd apps/web && pnpm run typecheck) && (cd apps/web && pnpm run lint) && git diff --check
TypeScript: passed.
ESLint: passed with zero warnings.
Diff integrity: passed with empty output.
Exit code: 0
Output hash: sha256:da5252feb1a816a7d3b344877109d47d93617826950786b6f11de1f79295a6a8
```

**Coverage**: ✅ 100% statements, branches, functions, and lines for `FrequencyTable.tsx`.

```text
cd apps/web && pnpm exec vitest run tests/components/FrequencyTable.test.tsx tests/contracts/no-linguistic-rules.test.ts --coverage
2 files passed, 10 tests passed; coverage command exited 0.
```

### Spec Compliance Matrix

| Requirement | Scenario | Runtime test evidence | Static evidence | Result |
|---|---|---|---|---|
| REQ-UI-DISPLAY-NORMALIZED-001 | Every row exposes both values | `FrequencyTable.test.tsx` exact three-row cell matrix passed | `row.display_form` and `row.normalized_form` occupy separate cells. | ✅ COMPLIANT |
| REQ-UI-DISPLAY-NORMALIZED-002 | German sharp-s remains readable | `FrequencyTable.test.tsx` passed with `Straße` and `strasse` in distinct assigned cells | Display form is the first cell and grouping key is the second. | ✅ COMPLIANT |
| REQ-UI-DISPLAY-NORMALIZED-003 | Copy avoids linguistic overclaiming | Caption/header and prohibited-term assertions passed | Visible copy uses `Texto mostrado` and `Clave de agrupación`; no canonical, lemma, or lexeme claim is present. | ✅ COMPLIANT |
| REQ-UI-DISPLAY-NORMALIZED-004 | Non-derived values remain unchanged | Exact-value component assertions and the AST linguistic-rule guard passed | The component renders both received fields directly and does not sort or transform them. | ✅ COMPLIANT |
| REQ-UI-DISPLAY-NORMALIZED-005 | Existing contract remains sufficient | Focused Vitest, typecheck, lint, migration, and Playwright checks passed | The diff contains no backend, API-contract, persistence, or import-semantic change. | ✅ COMPLIANT |

**Compliance summary**: 5/5 scenarios compliant; 5/5 requirements satisfied.

### Correctness (Static Evidence)

| Requirement | Status | Notes |
|---|---|---|
| REQ-UI-DISPLAY-NORMALIZED-001 | ✅ Implemented | Every non-empty row renders display form, grouping key, and frequency in received order. |
| REQ-UI-DISPLAY-NORMALIZED-002 | ✅ Implemented | `display_form` is preserved verbatim as the primary first cell. |
| REQ-UI-DISPLAY-NORMALIZED-003 | ✅ Implemented | Semantic caption and scoped headers explain the secondary role without linguistic overclaiming. |
| REQ-UI-DISPLAY-NORMALIZED-004 | ✅ Implemented | API fields are rendered directly; the AST contract rejects normalization, case folding, and sorting APIs. |
| REQ-UI-DISPLAY-NORMALIZED-005 | ✅ Implemented | Existing `FormFrequency` remains sufficient and the solution boundary is frontend-only plus build policy and SDD evidence. |

### Coherence (Design)

| Decision | Followed? | Notes |
|---|---|---|
| Present both values as semantic table columns | ✅ Yes | The table now has display, grouping-key, and frequency columns. |
| Keep display form first and grouping key secondary | ✅ Yes | Cell order matches the design and direct API contract. |
| Use caption plus scoped headers | ✅ Yes | The visible caption and three `scope="col"` headers are present. |
| Preserve server order and avoid derivation | ✅ Yes | The component maps `result.forms` without sorting or transforming values. |
| Keep the change UI-only | ✅ Yes | No backend/API/persistence/import source changed; the E2E locator and pnpm policy are supporting verification changes. |

### TDD Compliance

| Check | Result | Details |
|---|---|---|
| TDD evidence reported | ✅ | `apply-progress.md` contains the TDD Cycle Evidence table. |
| All tasks have test or inspection evidence | ✅ | 7/7 tasks have component, contract, quality, or specification inspection evidence. |
| RED confirmed | ✅ | The two behavioral test tasks identify the historical two-column failures; both referenced test files exist. |
| GREEN confirmed | ✅ | 10/10 focused tests and 1/1 E2E test passed independently. |
| Triangulation adequate | ✅ | Three varied rows distinguish ordering, accents, casing, and `Straße`/`strasse`. |
| Safety net for modified behavior | ✅ | The zero-state test and existing AST contract remain green. |

**TDD Compliance**: 6/6 checks passed.

### Test Layer Distribution

| Layer | Tests | Files | Tools |
|---|---:|---:|---|
| Unit / contract | 7 | 1 | Vitest + TypeScript AST |
| Integration / component | 3 | 1 | Vitest + Testing Library |
| E2E | 1 | 1 | Playwright Chromium |
| **Total** | **11** | **3** | |

### Changed File Coverage

| File | Line % | Branch % | Uncovered Lines | Rating |
|---|---:|---:|---|---|
| `apps/web/src/components/FrequencyTable.tsx` | 100% | 100% | — | ✅ Excellent |

**Average changed executable-file coverage**: 100%. Test, configuration, and Markdown artifacts are not executable coverage targets.

### Assertion Quality

The changed component and E2E tests and the retained contract test were inspected. Assertions execute production behavior, use non-empty result sets, verify concrete values and semantics, and contain no tautologies, ghost loops, type-only checks, CSS coupling, or mock-heavy patterns.

**Assertion quality**: ✅ All assertions verify real behavior; 0 CRITICAL and 0 WARNING findings.

### Quality Metrics

**Linter**: ✅ No errors or warnings  
**Type Checker**: ✅ No errors  
**Diff integrity**: ✅ `git diff --check` passed

### Issues Found

**CRITICAL**: None  
**WARNING**: The change-local spec maps every requirement to tasks, but `docs/definition-of-done.md` describes `docs/traceability-matrix.md` as a hard gate while that matrix also states that feature-specific traceability lives in per-spec artifacts. The current change does not add global matrix rows. This governance ambiguity does not invalidate the five tested scenarios, but archive should resolve whether the global matrix needs rows for these UI requirements.  
**SUGGESTION**: Verify the three-column table at a narrow viewport during review, as identified in the design risk assessment.

### Verdict

**PASS WITH WARNINGS**

All seven tasks are complete, all five requirements and scenarios are independently proven by passing runtime evidence, direct API rendering is preserved, and every changed implementation/configuration area is in scope. The only warning is the repository's conflicting guidance about global versus per-spec traceability ownership.

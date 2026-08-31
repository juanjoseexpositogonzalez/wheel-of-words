```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:39429242a6706518f1198de0adebb6cf27377855d0b7631ee088f734ea4c183f
verdict: fail
blockers: 4
critical_findings: 4
requirements: 8/11
scenarios: 39/44
test_command: cd apps/api && uv run pytest --cov=wheel_vocabulary --cov-branch --cov-report=term-missing --cov-fail-under=80 && WHEEL_BENCH_STRICT=1 uv run pytest tests/integration/test_vocabulary_bench.py -m bench -q -s && cd ../web && pnpm run test:coverage && pnpm exec playwright test e2e/vocabulary.spec.ts
test_exit_code: 1
test_output_hash: sha256:ff9b266097140518fe65234bcbbc79459f6d466ff76c31dd9510ca71b4b94d5d
build_command: cd apps/api && uv run ruff check . && uv run ruff format --check . && uv run mypy src/wheel_vocabulary && cd ../web && pnpm run typecheck && pnpm run lint && pnpm run build && cd ../.. && git diff --check
build_exit_code: 0
build_output_hash: sha256:a55c69d93d57a561775d1b1a6f08d1ba94b630dd89584ff19bad50c9ecf1ec26
```

## Verification Report

**Change**: vocabulary-browser  
**Version**: 005-vocabulary-browser  
**Mode**: Strict TDD  
**Revision**: `sha256:39429242a6706518f1198de0adebb6cf27377855d0b7631ee088f734ea4c183f`

### Completeness

| Metric | Value |
|---|---:|
| Requirements total | 11 |
| Requirements fully compliant | 8 |
| Scenarios total | 44 |
| Scenarios compliant | 39 |
| Native tasks total | 64 |
| Native tasks complete | 64 |
| Native tasks incomplete | 0 |

Native status reports `apply: all_done`, `tasks: 64/64 complete`, and `next: verify`. The corrective task entries T63-T66 are checked, and the traceability row for `REQ-005-006` is now `Cumplido`.

### Build & Tests Execution

**Backend full suite with coverage**: ✅ 702 passed in 244.44s; 100.00% line and branch coverage.  
**Strict vocabulary benchmark**: ❌ 1 failed, 2 deselected; 688,000 occurrences, 35,732 groups, 1,872,122-byte response, 1084 ms p95 against the 1000 ms bound.  
**Frontend coverage suite**: ✅ 81 passed; 100% line coverage and 86.76% branch coverage. Output hash: `sha256:da189792121596a3f313b2f9fe12a0564072f6863675e035d47e014913472c08`.  
**Playwright E2E**: ✅ 1 passed against `127.0.0.1:8010`; no listener remained on port 8010. The external process on port 8000 was not modified.  
**Build and quality checks**: ✅ Ruff, Ruff format, mypy, TypeScript typecheck, ESLint, Vite production build, and `git diff --check` passed.

The strict benchmark failure stopped the combined test command before its frontend legs. Those legs were then executed independently and passed; their output hash is recorded above. The strict envelope correctly retains exit code 1 and the exact output hash of the failing combined command.

### Spec Compliance Matrix

| Requirement | Scenario | Runtime evidence | Result |
|---|---|---|---|
| REQ-005-001 | Homograph produces two groups | repository/API tests in 702-test run | ✅ COMPLIANT |
| REQ-005-001 | Counts are occurrence counts | repository/API tests in 702-test run | ✅ COMPLIANT |
| REQ-005-001 | Stable identical requests | repository/API tests in 702-test run | ✅ COMPLIANT |
| REQ-005-001 | No aggregate confidence/provenance | DTO, API, and structural tests | ✅ COMPLIANT |
| REQ-005-002 | Seeded correction moves group | property/integration tests | ✅ COMPLIANT |
| REQ-005-002 | Vacated group disappears | repository integration test | ✅ COMPLIANT |
| REQ-005-002 | Precedence is per field | repository integration test | ✅ COMPLIANT |
| REQ-005-002 | Aggregate agrees with `resolve_effective` | Hypothesis tests | ✅ COMPLIANT |
| REQ-005-003 | Fully unannotated bucket | repository integration test | ✅ COMPLIANT |
| REQ-005-003 | Lemma with NULL POS bucket | repository integration test | ✅ COMPLIANT |
| REQ-005-003 | Absence is JSON null | API contract test | ✅ COMPLIANT |
| REQ-005-003 | Buckets labelled as text | frontend component test | ✅ COMPLIANT |
| REQ-005-004 | Annotation contract untouched | frozen-schema API test | ✅ COMPLIANT |
| REQ-005-004 | Annotation routes behave identically | full annotation suite passed | ✅ COMPLIANT |
| REQ-005-004 | New route is additive | OpenAPI/API test | ✅ COMPLIANT |
| REQ-005-005 | Unknown id is 404 | vocabulary API test | ✅ COMPLIANT |
| REQ-005-005 | Deleted import is 404 | no vocabulary-after-delete test found | ❌ UNTESTED |
| REQ-005-005 | Zero occurrences is empty success | repository integration test | ✅ COMPLIANT |
| REQ-005-005 | Error bodies carry no imported text | vocabulary API test | ✅ COMPLIANT |
| REQ-005-006 | Selector narrows groups without changing counts | `test_vocabulary_pos_selector_narrows_groups_without_changing_their_counts` | ✅ COMPLIANT |
| REQ-005-006 | NULL-POS bucket is selectable | `test_vocabulary_pos_selector_can_select_the_null_pos_bucket` | ✅ COMPLIANT |
| REQ-005-006 | Invalid selector is rejected | `test_vocabulary_rejects_an_invalid_pos_selector` | ✅ COMPLIANT |
| REQ-005-006 | Selector matching nothing is empty success | `test_vocabulary_pos_selector_without_matching_groups_is_an_empty_success` | ✅ COMPLIANT |
| REQ-005-007 | Nothing acts on confidence | structural tests | ✅ COMPLIANT |
| REQ-005-007 | Endpoint accepts no confidence parameter | OpenAPI/structural tests | ✅ COMPLIANT |
| REQ-005-007 | Group carries no aggregate confidence | DTO/structural tests | ✅ COMPLIANT |
| REQ-005-007 | Forbidden additions are caught | mutation tests | ✅ COMPLIANT |
| REQ-005-007 | Confidence scan fails closed | structural non-vacuity tests | ✅ COMPLIANT |
| REQ-005-008 | Structural write guard covers declared scope | guard tests | ✅ COMPLIANT |
| REQ-005-008 | Read leaves correction table untouched | repository runtime test | ✅ COMPLIANT |
| REQ-005-008 | Repository writes are caught | mutation tests | ✅ COMPLIANT |
| REQ-005-008 | Exemption boundary holds | boundary tests | ✅ COMPLIANT |
| REQ-005-008 | Frontend offers no correction affordance | component/client tests | ✅ COMPLIANT |
| REQ-005-009 | No aggregate is persisted | schema/migration tests | ✅ COMPLIANT |
| REQ-005-009 | Correction between reads changes next read | no covering between-reads test found | ❌ UNTESTED |
| REQ-005-009 | Added migration reverses cleanly | Alembic integration tests | ✅ COMPLIANT |
| REQ-005-010 | No client-side derivation | frontend structural tests | ✅ COMPLIANT |
| REQ-005-010 | Received values render verbatim | component tests | ✅ COMPLIANT |
| REQ-005-010 | Unmapped tag renders raw tag | label/component tests | ✅ COMPLIANT |
| REQ-005-010 | Annotation table unchanged and label map single | component/structural tests | ✅ COMPLIANT |
| REQ-005-011 | Bound derivations are externally anchored | document audit exists, but no covering runtime test | ❌ UNTESTED |
| REQ-005-011 | Benchmark asserts named bounds | strict benchmark failed at 1084 ms p95 | ❌ FAILING |
| REQ-005-011 | Benchmark is non-vacuous | mutation test passed in full suite | ✅ COMPLIANT |
| REQ-005-011 | Pagination exists only if a bound was exceeded | no pagination while strict latency exceeds bound | ❌ FAILING |

**Compliance summary**: 39/44 scenarios compliant; 2 failing; 3 untested.

### Correctness (Static Evidence)

| Requirement area | Status | Notes |
|---|---|---|
| Pair grouping, effective precedence, NULL buckets | ✅ Implemented | V3 merge reuses `resolve_effective` and preserves NULL keys. |
| Additive endpoint and frozen annotation contract | ✅ Implemented | Vocabulary remains a separate GET endpoint. |
| POS selector | ✅ Implemented | Validates 17 UPOS tags plus `null`, filters completed group keys, and preserves counts. |
| Frontend selector | ✅ Implemented | Accessible selector reloads API-owned groups; the client serializes `pos`. |
| Confidence isolation and correction-write prohibition | ✅ Implemented | Structural guards passed. |
| Query-time groups and reversible index | ✅ Implemented | Repository derives groups and migration tests passed. |
| Unpaginated response budget | ❌ Failing | Current strict p95 is 1084 ms against the 1000 ms bound. |

### Coherence (Design)

| Decision | Followed? | Notes |
|---|---|---|
| D1 V3 raw aggregation plus correction delta | ✅ Yes | Source follows the two-leg merge and reuses `resolve_effective`. |
| D1a one-snapshot obligation | ⚠️ No | WU2b remains unresolved; concurrent committed writes remain unspecified. |
| D2 `(book_id, lemma, pos)` index | ✅ Yes | Additive migration and model declaration are present. |
| D3 no pagination while both bounds clear | ❌ No | The strict latency measurement exceeds the named bound. |
| D4 confidence structurally absent | ✅ Yes | Isolation guard passed. |
| D5 total result ordering | ✅ Yes | Repository and API tests pin count-descending, NULL-first ordering. |
| Corrective POS selector | ✅ Yes | `pos=null` selects NULL-POS groups; omission remains unfiltered. |
| Hexagonal layer split | ✅ Yes | Route → use case/port → infrastructure remains intact. |

### TDD Compliance

| Check | Result | Details |
|---|---|---|
| TDD evidence reported | ✅ | Apply-progress includes corrective RED/GREEN evidence for T63-T66. |
| All native tasks complete | ✅ | Native status reports 64/64 complete. |
| Corrective RED confirmed | ✅ | Four API failures and selector/client absence are recorded before implementation. |
| GREEN confirmed | ❌ | Corrective tests pass, but the independent strict benchmark is red. |
| Triangulation adequate | ✅ | All four AC-005-06 scenarios have distinct API cases plus client/component/page coverage. |
| Historical RED quality | ⚠️ | Several earlier work units record missing-module collection failures, which AGENTS.md §3 does not accept as behavioral RED. |

**TDD compliance**: 4/6 checks passed without qualification.

### Test Layer Distribution

| Layer | Executed evidence | Tools |
|---|---:|---|
| Backend unit/integration/API/structural | 702 passed plus 1 strict benchmark failure | pytest, Hypothesis, SQLite, FastAPI TestClient |
| Frontend unit/component/structural | 81 passed | Vitest, Testing Library |
| E2E | 1 passed | Playwright/Chromium |

### Changed File Coverage

| Area | Line coverage | Branch coverage | Rating |
|---|---:|---:|---|
| Backend package, including `api/routes/vocabulary.py` | 100% | 100% | ✅ Excellent |
| Frontend `api/vocabulary.ts` | 100% | 100% | ✅ Excellent |
| Frontend `VocabularyBrowser.tsx` | 100% | 80% | ✅ Excellent line coverage |
| Frontend `ImportPage.tsx` | 100% | 78.57% | ⚠️ Branch coverage below 80% |

**Aggregate coverage**: backend 100.00%; frontend 100% lines / 86.76% branches.

### Assertion Quality

The corrective tests call the API, client, rendered selector, or page workflow and assert concrete response bodies, query serialization, option values, and reload behavior. No tautology, production-code-free assertion, ghost loop, or orphan empty-result assertion was found in the corrective test files.

**Assertion quality**: ✅ All corrective assertions verify observable behavior.

### Quality Metrics

**Backend linter/formatter**: ✅ No errors  
**Backend type checker**: ✅ No errors  
**Frontend linter**: ✅ No errors  
**Frontend type checker/build**: ✅ No errors; production build succeeded

### Issues Found

**CRITICAL**

1. The strict 688,000-occurrence benchmark failed at 1084 ms p95 against the design's 1000 ms p95 limit. `REQ-005-011` requires pagination when either named bound is exceeded.
2. The deleted-import vocabulary scenario has no covering runtime test. Existing delete tests and unknown-id vocabulary tests do not prove the required delete-then-vocabulary sequence.
3. The correction-between-reads refresh scenario has no covering runtime test. Existing correction tests seed corrections before one read rather than between two reads.
4. The response-budget derivation scenario has no covering runtime test. The design text can be audited manually, but the verification contract requires a passing covering test for scenario compliance.

**WARNING**

1. Design D1a/WU2b remains unresolved: the repository's two legs do not share a SQLite snapshot under the configured rollback journal.
2. Several historical apply RED records are missing-module or collection failures rather than behavioral failures under AGENTS.md §3.
3. `ImportPage.tsx` has 78.57% branch coverage, below the strict-TDD module's 80% warning threshold, despite 100% line coverage.

**SUGGESTION**: None.

### Verdict

**FAIL**

`REQ-005-006` is implemented and all four POS-filter scenarios pass, but the strict latency gate still fails and three required scenarios lack passing covering tests. The change is not archive-ready.

### Apply remediation addendum — corrective coverage slice

This addendum records apply evidence after the failed verification revision above. It does not replace
the independent verdict or its strict benchmark failure.

- `REQ-005-005` is covered by `test_deleted_vocabulary_import_returns_import_not_found`: create,
  delete through the shipped API, then vocabulary read returns `404 IMPORT_NOT_FOUND`.
- `REQ-005-009` is covered by
  `test_vocabulary_read_refreshes_after_a_correction_committed_between_requests`: a committed direct
  correction between two GETs changes the second group sequence.
- `REQ-005-011` response-budget derivation is covered by
  `test_response_body_budget_is_derived_from_the_external_import_size_limit`: the executable check
  equates the response budget to `Settings.max_import_size_bytes` and pins the design's arithmetic.

Focused remediation validation: `cd apps/api && uv run pytest tests/api/test_vocabulary_route.py
tests/integration/test_vocabulary_bench.py -q` → 14 passed. The strict performance/pagination
findings remain outside this corrective coverage slice.

### Apply remediation addendum — response serialization

This addendum records apply evidence after the failed verification revision. It does not replace the
independent verdict above.

- The route now returns the unchanged response envelope through `JSONResponse`, preserving the
  declared `VocabularyResponse` OpenAPI model and `X-Schema-Version: 1` header while avoiding
  per-group Pydantic response-model construction.
- RED: before the production change, `WHEEL_BENCH_STRICT=1 uv run pytest
  tests/integration/test_vocabulary_bench.py -m bench -q -s` failed at 3,096 ms p95 against the
  1,000 ms bound.
- GREEN: `WHEEL_BENCH_STRICT=1 uv run pytest tests/api/test_vocabulary_route.py
  tests/integration/test_vocabulary_bench.py -q -s` passed 14 tests in 24.40s; the strict benchmark
  reported 35,732 groups, a 1,872,122-byte response, and 822 ms p95.
- WU2b snapshot isolation remains explicitly out of this slice.

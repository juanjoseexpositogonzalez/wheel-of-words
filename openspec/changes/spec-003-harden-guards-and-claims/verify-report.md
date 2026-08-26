```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:c3d1e713b541de55ebc604213ccc801215eeb6cc09c642b19e04439b1c5154fe
verdict: fail
blockers: 2
critical_findings: 2
requirements: 5/7
scenarios: 37/39
test_command: cd apps/api && uv run pytest --cov=wheel_vocabulary --cov-report=term-missing
test_exit_code: 0
test_output_hash: sha256:f9710197f9f778cf639d097a46fbdb3c3a40904caf067d9cb7873b90535a9b6c
build_command: cd apps/api && uv run mypy src/wheel_vocabulary
build_exit_code: 0
build_output_hash: sha256:d65cae0083d77ec23a4483dfe03fa5cbfde2ebbad3bc4205bfa20ae5ff3edceb
```

## Verification Report

**Change**: `spec-003-harden-guards-and-claims`
**Branch**: `feat/spec-003-08f-traceability-matrix` @ `0ae9318`
**Mode**: Strict TDD
**Artifact mode**: OpenSpec primary + Engram
**Verdict**: **FAIL**

### Contract Counts

| Source | Requirements | Acceptance criteria | Scenarios |
|---|---:|---:|---:|
| `specs/003-lemmatization-pos/spec.md` | 6 | 6 | 28 |
| `specs/002-text-import/spec.md` (`REQ-002-007` amendment) | 1 | 1 | 11 |
| **Total** | **7** | **7** | **39** |

### Completeness

| Metric | Value |
|---|---:|
| Tasks total | 47 |
| Tasks complete | 47 |
| Tasks incomplete | 0 |
| Requirements fully compliant | 5 / 7 |
| Scenarios compliant | 37 / 39 |

All task checkboxes from 1.1 through 6.7 are complete. The six `REQ-003H-*` traceability rows are present, populated, and marked `Cumplido`; the `REQ-003-004` row describes content equality plus `source_index == position` and cites current test nodes.

### Build & Tests Execution

| Command | Exit | Result | Output SHA-256 |
|---|---:|---|---|
| `cd apps/api && uv run pytest --cov=wheel_vocabulary --cov-report=term-missing` | 0 | 544 passed; 100% statements and branches | `f9710197f9f778cf639d097a46fbdb3c3a40904caf067d9cb7873b90535a9b6c` |
| `cd apps/api && uv run ruff check` | 0 | All checks passed | `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18` |
| `cd apps/api && uv run mypy src/wheel_vocabulary` | 0 | No issues in 47 source files | `d65cae0083d77ec23a4483dfe03fa5cbfde2ebbad3bc4205bfa20ae5ff3edceb` |
| `cd apps/web && pnpm run test` | 0 | 15 files, 69 tests passed | `8eda24c22d51308327c533c4a312265b83e936831babe2a7ba595d2547f869ae` |
| `cd apps/web && pnpm exec eslint .` | 0 | No output; clean | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `cd apps/web && pnpm exec tsc --noEmit` | 0 | No output; clean | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `cd apps/web && pnpm exec playwright test` | 0 | 4 Chromium E2E specs passed | `16b78ce05aae531e591279be5f7969170e6cedcaf3915b526e4121a45c044f4d` |
| schema SHA-256 checks | 0 | Both pinned hashes match | `2d3bd6e4f403a01e73973bc35ee9980ff400e93470cf869a2dc5cb9c3be2e932` |

Pinned schemas:

- `import.v1.json`: `def94cb6361531b21f382c862120914419b867b6601aa58d763d49d65a554258`
- `annotation.v1.json`: `ab5439de465d768ebaf1be629315b78aef652aa175c2aaf09ab2c35a7d1de309`

### Spec Compliance Matrix

| Requirement | Scenario | Runtime evidence | Result |
|---|---|---|---|
| REQ-003H-001 | Sibling properties renamed to `lemma` are caught | Parameterized tests in `test_no_lemma_naming.py` and `test_annotation_contract.py` | ✅ COMPLIANT |
| REQ-003H-001 | Genuine lemma properties pass and schemas remain identical | `test_the_genuine_annotation_lemma_properties_remain_exempt`; schema hashes | ✅ COMPLIANT |
| REQ-003H-001 | Dotted key inherits no ancestor exemption | `test_walk_json_preserves_dotted_keys_as_single_segments` | ✅ COMPLIANT |
| REQ-003H-001 | Frontend owning sets grant only declared names | `no-lemma-naming.test.ts` owning-set and M3 tests | ✅ COMPLIANT |
| REQ-003H-001 | Binding helper exists once | `test_the_binding_helper_exists_once` | ✅ COMPLIANT |
| REQ-003H-001 | Schema scan fails closed | backend schema non-vacuity tests | ✅ COMPLIANT |
| REQ-003H-002 | Forbidden SQL in module docstring is caught | `test_a_module_docstring_holding_the_raw_forbidden_sql_would_be_caught` | ✅ COMPLIANT |
| REQ-003H-002 | Reviewed prose docstring passes | `test_only_the_reviewed_module_docstring_stays_exempt` | ✅ COMPLIANT |
| REQ-003H-002 | Exempted content is pinned | `test_a_changed_reviewed_module_docstring_would_be_caught` | ✅ COMPLIANT |
| REQ-003H-002 | Function/class/plain-string legs remain closed | `test_sql_in_function_class_docstrings_and_plain_literals_remains_in_scope` | ✅ COMPLIANT |
| REQ-003H-002 | Module walk fails closed | `test_write_repository_module_walk_fails_closed_when_empty_or_incomplete` | ✅ COMPLIANT |
| REQ-003H-003 | Claim comes from runtime enumeration | runtime enumeration shape and exact-mapping derivation tests | ✅ COMPLIANT |
| REQ-003H-003 | No handwritten model-internal claim survives | `test_primary_governed_documents_contain_no_model_internal_claim_signatures` | ✅ COMPLIANT |
| REQ-003H-003 | Enumeration mutation is rejected | `test_mutating_one_runtime_value_is_rejected_by_a_fresh_enumeration` | ✅ COMPLIANT |
| REQ-003H-003 | Missing model cannot silently pass | No passing test executes the missing-model branch; fixture only loads the present model | ❌ UNTESTED |
| REQ-003H-003 | Domain stays stdlib-only | `test_domain_imports_remain_stdlib_only_after_enumeration_lands` | ✅ COMPLIANT |
| REQ-003H-004 | Port states pairing obligations and failure | `test_analyze_docstring_states_the_source_index_failure_obligation` | ✅ COMPLIANT |
| REQ-003H-004 | Fully conformant adapter is accepted | normal and consistently-reindexed acceptance tests | ✅ COMPLIANT |
| REQ-003H-004 | Every rejection branch has a documented obligation | `test_each_annotation_validation_rejection_has_a_port_obligation` | ✅ COMPLIANT |
| REQ-003H-004 | Documentation guard is non-vacuous | obligation guard with recorded RED plus `test_docs_name_source_index` | ✅ COMPLIANT |
| REQ-003H-005 | Matrix row describes shipped checks | matrix text plus cited-node resolver | ✅ COMPLIANT |
| REQ-003H-005 | Superseded identity wording is absent | `test_matrix_contains_no_identity_based_pairing_claim` | ✅ COMPLIANT |
| REQ-003H-005 | Every cited Python test exists | resolver, stale-node, and relative-node tests | ✅ COMPLIANT |
| REQ-003H-005 | New requirements are traceable | six populated matrix rows; traceability suite passed | ✅ COMPLIANT |
| REQ-003H-006 | One bounded statement appears in three locations | `test_bounded_source_index_guarantee_is_verbatim_in_all_required_locations` | ✅ COMPLIANT |
| REQ-003H-006 | Consistently-reindexed same-text swap is accepted | `test_same_text_swap_with_consistently_reassigned_source_index_is_accepted` | ✅ COMPLIANT |
| REQ-003H-006 | Non-reindexed same-text swap fails | `test_same_text_swap_without_reassigning_source_index_fails_and_writes_nothing` | ✅ COMPLIANT |
| REQ-003H-006 | Shipped adapter derives `source_index` from document enumeration | Implementation uses `enumerate(doc)`, but no test asserts returned `source_index` values | ❌ UNTESTED |
| REQ-002-007 | No forbidden naming leaks into contract surfaces | backend/frontend structural guards | ✅ COMPLIANT |
| REQ-002-007 | Prose may name concept; naming may not | Python docstring and frontend comment boundary tests | ✅ COMPLIANT |
| REQ-002-007 | Inflected forms remain separate | `test_inflected_forms_stay_separate_rows` | ✅ COMPLIANT |
| REQ-002-007 | Genuine lemma names are admitted | backend/frontend exact allow-list tests | ✅ COMPLIANT |
| REQ-002-007 | Normalized form renamed to lemma-shaped name fails | backend/frontend rename tests | ✅ COMPLIANT |
| REQ-002-007 | Allow-listed name at non-owning site fails | Python, JSON/OpenAPI, reflected-column, and frontend boundary tests | ✅ COMPLIANT |
| REQ-002-007 | Sibling property renamed inside owner fails | both parameterized Python guards | ✅ COMPLIANT |
| REQ-002-007 | Dotted key inherits nothing | shared-helper dotted-segment test | ✅ COMPLIANT |
| REQ-002-007 | One shared binding implementation | helper uniqueness test | ✅ COMPLIANT |
| REQ-002-007 | Guard narrowed rather than weakened | exact allow-list, expected-input, and source-walk tests | ✅ COMPLIANT |
| REQ-002-007 | Guard assertions are non-vacuous | positive mutations, expected-input checks, and boundary controls | ✅ COMPLIANT |

**Compliance summary**: 37/39 scenarios compliant; 5/7 requirements fully compliant.

### Correctness (Static Evidence)

| Requirement | Status | Evidence |
|---|---|---|
| REQ-003H-001 / REQ-002-007 amendment | ✅ Implemented | Shared manifest-pinned helper carries traversal segments; both Python guards import it; frontend owners are per-file subsets. |
| REQ-003H-002 | ✅ Implemented | One module path plus exact reviewed docstring is exempt; all other docstrings remain in scope. |
| REQ-003H-003 | ⚠️ Partial verification | Runtime enumeration and document guard are implemented; missing-model behavior lacks executed scenario coverage. |
| REQ-003H-004 | ✅ Implemented | Port documents count, pairing, UPOS, confidence, and `ANNOTATION_FAILED` obligations. |
| REQ-003H-005 | ✅ Implemented | Matrix rows and collected-node resolver match the shipped mechanism. |
| REQ-003H-006 | ⚠️ Partial verification | Bounded behavior tests pass; shipped adapter implementation uses `enumerate(doc)`, but the scenario lacks a direct assertion. |

### Coherence (Design)

| Decision | Followed? | Notes |
|---|---|---|
| D1 shared helper under `tests/unit` | ✅ Yes | `_guard_binding.py` is the sole implementation. |
| D2 name + declaring definition + pinned manifest | ✅ Yes | `OwningDefinition` and `is_exempt` match the design. |
| D3 governed prose contains no model-internal values | ✅ Yes | Fixed document set and four signature families are active. |
| D4 integration enumeration fails loudly | ✅ Implementation / ⚠️ scenario evidence | Real model test passes; absent-model branch was not executed. |
| D5 one pinned module docstring exemption | ✅ Yes | Exact module label and exact content are required. |
| D6 bounded statement copied verbatim | ✅ Yes | Port/spec/matrix guard passed. |
| No runtime/schema behavior change | ✅ Yes | Only port documentation changed in production; schemas match pinned hashes. |

### TDD Compliance

| Check | Result | Details |
|---|---|---|
| TDD evidence reported | ✅ | Engram apply-progress contains TDD tables; per-slice observations and test docstrings preserve RED/GREEN evidence. |
| Test files exist | ✅ | All ten changed backend/frontend test files and the integration helper are present. |
| GREEN reconfirmed | ✅ | Backend, frontend, and E2E suites all passed during verification. |
| Triangulation adequate | ✅ | Mutation, non-vacuity, and boundary controls cover the guard behaviors. |
| Safety-net reporting | ⚠️ | The final 08f table is complete, but earlier slices are summarized across observations rather than one normalized all-slice table. |

**TDD compliance**: runtime GREEN and assertion quality are confirmed; historical evidence normalization is incomplete but is not the substantive blocker.

### Test Layer Distribution

| Layer | Tests | Files | Tool |
|---|---:|---:|---|
| Unit / static contract | 142 | 9 | pytest + Vitest |
| Integration | 4 | 1 | pytest + real `en_core_web_sm` |
| E2E regression | 4 | 4 unchanged specs | Playwright |
| **Total executed relevant tests** | **150** | **14** | |

### Changed File Coverage

| File | Line % | Branch % | Uncovered | Rating |
|---|---:|---:|---|---|
| `apps/api/src/wheel_vocabulary/application/annotation/ports.py` | 100% | N/A | — | ✅ Excellent |

Test-side helpers are not included in the production coverage source set. Backend aggregate coverage is 100% statements and branches.

### Assertion Quality

**Assertion quality**: ✅ No tautologies, orphan empty assertions, uncovered ghost loops, smoke-only checks, or mock-heavy files were found in the changed tests. Absence assertions have positive mutation/non-vacuity companions.

### Quality Metrics

**Linter**: ✅ Ruff and ESLint clean  
**Type checker**: ✅ Mypy and TypeScript clean  
**Coverage**: ✅ Backend 100%  
**E2E**: ✅ 4/4 passed

### Issues Found

**CRITICAL**

1. `REQ-003H-003` missing-model scenario is untested at runtime. The integration fixture proves the installed model loads, but no passing test simulates load failure and proves the test cannot skip or return a vacuous pass.
2. `REQ-003H-006` shipped-adapter scenario is untested. `SpacyLinguisticAnalyzer.analyze` visibly assigns `source_index=index` from `enumerate(doc)`, but no runtime assertion checks `[annotation.source_index]` against input/document positions.

**WARNING**

1. Strict-TDD historical safety-net evidence for pre-08f slices is distributed across per-slice Engram observations and test docstrings instead of one complete normalized apply-progress table.

**SUGGESTION**: None.

### Native Attempt Settle Evidence

- Attempt token: `sha256:c420cc7a80584882109931ed90f0a3161f14bc377598e68faa82c09d025acd00`
- Work unit: `verify-spec-003h`
- Candidate commit: `0ae9318`
- Verification result: `failed` because 2 required scenarios have no passing runtime coverage.
- Harness disposition: `reused`; all declared quality commands executed successfully and no mutation or cleanup artifact touched the repository.
- Cleanup evidence: repository was clean before verification; the report is the only intended repository change after validator admission; `.atl/skill-registry.md` was not touched or restored.
- Process evidence: full backend/frontend/E2E gates and schema checks ran with the exact command hashes above.
- Canonical verification-evidence preimage SHA-256: `c3d1e713b541de55ebc604213ccc801215eeb6cc09c642b19e04439b1c5154fe`.

Exact canonical verification-evidence bytes:

```json
{"attempt_token":"sha256:c420cc7a80584882109931ed90f0a3161f14bc377598e68faa82c09d025acd00","build_command":"cd apps/api && uv run mypy src/wheel_vocabulary","build_exit_code":0,"build_output_hash":"sha256:d65cae0083d77ec23a4483dfe03fa5cbfde2ebbad3bc4205bfa20ae5ff3edceb","commit":"0ae9318","other_output_hashes":{"eslint":"sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","playwright":"sha256:16b78ce05aae531e591279be5f7969170e6cedcaf3915b526e4121a45c044f4d","ruff":"sha256:82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18","schema_checks":"sha256:2d3bd6e4f403a01e73973bc35ee9980ff400e93470cf869a2dc5cb9c3be2e932","tsc":"sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","web_test":"sha256:8eda24c22d51308327c533c4a312265b83e936831babe2a7ba595d2547f869ae"},"requirements":"5/7","scenarios":"37/39","schema_hashes":{"annotation.v1.json":"ab5439de465d768ebaf1be629315b78aef652aa175c2aaf09ab2c35a7d1de309","import.v1.json":"def94cb6361531b21f382c862120914419b867b6601aa58d763d49d65a554258"},"test_command":"cd apps/api && uv run pytest --cov=wheel_vocabulary --cov-report=term-missing","test_exit_code":0,"test_output_hash":"sha256:f9710197f9f778cf639d097a46fbdb3c3a40904caf067d9cb7873b90535a9b6c","verdict":"fail","work_unit":"verify-spec-003h"}
```

### Verdict

**FAIL**

All quality gates are green and implementation/design coherence is strong, but strict spec-driven verification cannot mark scenarios compliant from source inspection alone. Two required scenarios lack passing runtime coverage, so the change is not archive-ready.

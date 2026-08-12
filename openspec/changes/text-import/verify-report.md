```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:7993678a9709e94a47f9d2b175df3bd59abf2ea24c1bb21e1a620af7ccfa256b
verdict: pass_with_warnings
blockers: 0
critical_findings: 0
requirements: 18/18
scenarios: 45/45
test_command: cd apps/api && uv run pytest -q
test_exit_code: 0
test_output_hash: sha256:7c199fa28f9dc503b26372c3480d4e9d093b3e14be7437ea77a4934e5015736c
build_command: cd apps/api && uv run mypy src/wheel_vocabulary
build_exit_code: 0
build_output_hash: sha256:32c1f154f636757bc9df6843701b18b495673a7cf2e0f68b592d2055d6ae6c07
```

# Verification Report — SPEC-002 `text-import`

| Field | Value |
|---|---|
| Change | `text-import` (capability `002-text-import`) |
| Repo state | `fix/spec-002-critical-evidence-gaps` based on `main` @ `ed100d2`, local remediation changes present; untracked `mockups/` intentionally ignored |
| Mode | Remediation verification, full artifact set (proposal, spec, design, tasks, traceability) |
| Requirements | 18 (`REQ-002-001` … `REQ-002-018`) |
| Acceptance criteria | 24 (`AC-002-01` … `AC-002-24`) |
| Scenarios in spec | 45 |
| Tasks | 77 / 77 checked, 0 unchecked — claim verified by count |
| Verdict | **PASS WITH WARNINGS** — 0 CRITICAL, 8 WARNING, 3 SUGGESTION |

## 1. Executive summary

The shipped implementation is behaviourally sound and the two evidentiary blockers from
the previous verification have now been pinned by permanent integration tests. The
feature remains correct, every gate I ran is green, every reported number is accurate,
and the remediation specifically closes the structural-absence properties that were
previously satisfied only by inspection.

The verdict is now `pass_with_warnings`: the two CRITICAL findings are resolved, all
18 requirements are proven, and all 45 spec scenarios have runtime or structural-test
evidence. The remaining WARNING and SUGGESTION findings are guard-strength or paperwork
quality issues that do not block testing the feature today.

## 2. Measured evidence — all commands executed, actuals reported

| Command | Result | Expected per apply report | Match |
|---|---|---|---|
| `cd apps/api && uv run pytest` | **298 passed**, 0 warnings, exit 0 | all backend tests green | ✅ |
| `uv run ruff check .` | `All checks passed!`, exit 0 | clean | ✅ |
| `uv run ruff format --check .` | `72 files already formatted`, exit 0 | clean | ✅ |
| `uv run mypy src/wheel_vocabulary` | `Success: no issues found in 35 source files`, exit 0 | clean | ✅ |
| `uv run pytest tests/unit/test_traceability.py -q` | **5 passed**, exit 0 | 5 passed | ✅ (but see W3) |
| `uv run alembic upgrade head && downgrade -1 && upgrade head` | exits 0 / 0 / 0; `0001_baseline ↔ 0002_book_occurrence` | clean round trip | ✅ |
| `cd apps/web && pnpm run test` | **37 passed** (12 files), exit 0 | 37 passed | ✅ |
| `pnpm run typecheck` (`tsc --noEmit`) | exit 0 | clean | ✅ |
| `pnpm run lint` (`eslint --max-warnings 0`) | exit 0 | clean | ✅ |
| `CI_COVERAGE_MODE=fail pnpm run test:coverage` | 37 passed; **100% stmts / 100% lines / 100% funcs / 84% branch**, exit 0 | pass | ✅ (but see W6) |
| `pnpm exec playwright test` | **3 passed** (`status`, `import`, `delete-import`), exit 0 | 3 specs | ✅ |
| `make test` | Backend **298 passed**, frontend **37 passed**, Playwright **3 passed** | green | ✅ |
| `make lint` | Backend ruff clean, frontend ESLint clean | clean | ✅ |
| `make typecheck` | Backend mypy clean, frontend TypeScript clean | clean | ✅ |
| `cd apps/api && uv run ruff format --check .` | `72 files already formatted`, exit 0 | clean | ✅ |

Every number in the last apply report is accurate. Nothing was overstated.

### 2.1 T-BENCH, both modes (measured on this machine)

| Mode | Result | Measurements |
|---|---|---|
| Default (`uv run pytest tests/integration/test_import_bench.py`) | **3 passed** | `corpus=4194304B import=7.491s GET_total=0.280s aggregation_segment=0.175s (§3.5 250 ms trigger: within budget) rows=28180 response_body=1925522B strict_mode=off` |
| Strict (`WHEEL_BENCH_STRICT=1`) | **1 failed, 2 passed** — `assert 7.637844791999669 < 6.0` | `import=7.638s GET_total=0.333s aggregation_segment=0.219s (§3.5 250 ms trigger: within budget) rows=28180 response_body=1925522B strict_mode=on` |

The T215 amendment behaves exactly as recorded in `tasks.md` note 7: the default run fails
only on deterministic invariants (`Σfrequency == total_token_count`, row-count
self-consistency, body-size range, `distinct_form_count > 1000`), the wall-clock budget
assertions are reached only under `WHEEL_BENCH_STRICT=1`, and the §3.5 250 ms
aggregation-segment comparison is computed and printed on **every** run. The strict failure
is a genuine hardware-variance failure (7.64 s against a 6.0 s budget), which is precisely
why it is gated out of default CI. **Confirmed as amended.**

The §3.5 comparison: aggregation segment measured at **0.175 s (default) / 0.219 s (strict)**
against the **250 ms** p95 trigger — *within budget*, so the `form_frequency` aggregate table
correctly stays unbuilt. This matches design §3.4.5's English-corpus prediction of 0.23 s.

### 2.2 Prior-cycle remediations — verified landed, not trusted

| Record | Claim | Verification on `main` |
|---|---|---|
| #4006 / #4010 / #4021 | Frontend lemma guard converted from text search to TS AST, comment exemption pinned by permanent tests | **Landed.** `apps/web/tests/contracts/no-lemma-naming.test.ts` runs **8 tests**: 1 non-vacuity (glob reaches 5 named files), 1 absence over real sources, and 6 `findViolations` direct tests asserting `kind` + `text` + `line` for identifier / string literal / template literal / JSX text, plus two comment-exemption tests (`//` and `/* */` → zero violations). Both directions pinned. Symmetric with the backend leg's three. |
| #4051 / #4061 | `BookRepository.delete()` and `.exists()` stripped before merging cut 2 | **Landed.** `grep` for `def exists` / `.exists(` across `apps/api/src` and `apps/api/tests` returns **nothing** in production or capability tests (only `database_path.exists()` in a SPEC-001 alembic test). `delete()` is now fully wired: `ports.py:76` → `book_repository.py:111` → `use_cases.py:258` (`DeleteImport`) → `dependencies.py:106` (`get_delete_import`) → `routes/imports.py:96` (`DELETE` route). |
| #4075 | Cut 3 closes SPEC-002 | **Landed**, with the caveats below. |

### 2.3 Orphan-symbol sweep (the check that caught the cut-2 deviation)

Swept every public `class`/`def` and every public method in `apps/api/src/wheel_vocabulary/`
and every `export` in `apps/web/src/`, counting production references.

- **`apps/api/src`: zero orphans.** The only two symbols with a single reference are
  `routes/imports.py:60 create_import` and `routes/imports.py:97 delete_import`, both FastAPI
  route handlers registered by decorator — correct by construction, not orphans.
- **`apps/web/src`: zero orphans.** Every export has production references. `FormFrequency`
  (`types/imports.ts:18`) has no direct test reference but is consumed by `ImportResult`.

**No repeat of the cut-2 scope deviation.**

## 3. Per-requirement verdict

| REQ | Verdict | Proving test(s), confirmed by reading the assertions |
|---|---|---|
| REQ-002-001 | **PROVEN** | `tests/api/test_imports.py::test_a_synthetic_txt_upload_is_created` (201 + body); `::test_a_json_filesystem_path_is_refused_and_nothing_is_computed` (422, nothing computed) |
| REQ-002-002 | **PROVEN** | `tests/unit/test_import_text.py::test_unsupported_filename_is_rejected_before_any_byte_is_read`, `::test_unsupported_content_type_is_rejected_before_any_byte_is_read`, `::test_extension_matching_is_case_insensitive`, `::test_traversal_shaped_filename_is_judged_on_its_suffix_alone`; `tests/api/test_imports.py::test_a_wrong_extension_is_refused_naming_the_accepted_one`, `::test_an_uppercase_extension_is_accepted` |
| REQ-002-003 | **PROVEN** | `tests/unit/test_settings.py::test_max_import_size_bytes_defaults_to_four_mebibytes` (asserts `4194304`), `::test_max_import_size_bytes_env_override`; `tests/unit/test_import_text.py::test_body_one_byte_over_the_limit_is_rejected`, `::test_body_exactly_at_the_limit_is_accepted`, `::test_an_oversized_body_is_abandoned_mid_stream_not_after_the_fact`, `::test_a_lying_declared_size_does_not_bypass_the_streaming_gate`; `tests/api/test_imports.py::test_an_oversized_upload_is_refused_with_the_limit_surfaced` |
| REQ-002-004 | **PROVEN** | `tests/unit/test_text_extraction.py` (8 tests: strict decode, BOM strip, BOM-only, only-leading-BOM, Latin-1 rejection, broken exception chain, no offset leak); `tests/api/test_imports.py::test_non_utf8_bytes_are_refused_with_conversion_guidance`, `::test_the_rejection_body_never_carries_a_byte_offset`, `::test_a_bom_prefixed_upload_is_accepted_without_the_bom_entering_a_form` |
| REQ-002-005 | **PROVEN** | `tests/unit/test_tokenizer.py` (21 tests, parametrized `T1`–`T10`); `tests/unit/test_normalizer.py` (44 tests, `N1`–`N5` + adversarial code points); `tests/unit/test_domain_isolation.py` (3 tests, AST-based, with an explicit non-vacuity test asserting the walk reaches 6 named modules) |
| REQ-002-006 `+` | **PROVEN** | Domain: `tests/unit/test_frequency.py::test_repeated_forms_collapse_with_frequency_and_sum`. `POST`: `tests/api/test_imports.py::test_rows_arrive_already_ordered_by_the_grouping_key`, `::test_the_token_count_equals_the_sum_of_the_returned_frequencies`. `GET` (cut-2 closure): `::test_get_imports_returns_the_ordered_table_with_the_persisted_id`, `::test_get_imports_diacritic_insensitive_order`. Frontend order: `FrequencyTable.test.tsx::test_renders_received_order_and_display_form_verbatim`. Spanning closure at cut 2 is genuine. |
| REQ-002-007 `+` | **PROVEN** | All four legs run and are two-directional. Backend AST: `tests/unit/test_no_lemma_naming.py` (12 tests — non-vacuity, absence, docstring exemption, identifier-still-fails, response-key-literal-still-fails, published-docstring-not-exempt). JSON Schema + served OpenAPI: same file. Persisted columns (cut-2 closure, T217): `::test_persisted_columns_contain_no_lemma_naming`, which checks the migration source **and** reflects real column names from `Base.metadata`. Frontend AST: `no-lemma-naming.test.ts` (8 tests). Spanning closure at cut 2 is genuine. |
| REQ-002-008 | **PROVEN** | `tests/integration/test_alembic_0002.py::test_upgrade_and_downgrade_book_occurrence` (both tables created, both removed, version back to `0001_baseline`); `tests/integration/test_book_repository.py::test_frequency_pairs_survives_a_new_session_against_the_same_database`, `::test_create_batches_occurrence_inserts_at_the_configured_size` |
| REQ-002-009 | **PROVEN** | `tests/integration/test_book_repository.py::test_content_hash_matches_an_independently_computed_sha256` — the expected digest is computed independently with `hashlib`, not read back from the implementation; `::test_a_one_byte_difference_changes_the_hash` |
| REQ-002-010 | **PROVEN** | `tests/integration/test_occurrence_pos.py::test_every_persisted_occurrence_has_pos_none` ✅, `::test_raw_text_and_normalized_text_stay_separate_values` ✅, and `::test_book_table_has_no_part_of_speech_column` ✅. AC-002-14's third clause is now pinned by a real column-level assertion. |
| REQ-002-011 | **PROVEN** | `tests/integration/test_delete_import.py` (5 tests: 204 + subsequent 404 envelope + zero orphans; empty 204 body; cascade-independence with `PRAGMA foreign_keys` off; unknown id → domain envelope with `"detail" not in body`; already-deleted id → 404). UI: `DeleteImportButton.test.tsx` (4 tests covering all three AC-002-16 legs). E2E: `e2e/delete-import.spec.ts`. Guard: `tests/unit/test_no_soft_delete.py` (3 tests, both directions). |
| REQ-002-012 | **PROVEN** | `tests/unit/test_import_text.py::test_a_content_free_upload_succeeds_with_zero_forms` (parametrized), `::test_a_digits_only_upload_succeeds_with_zero_forms`; `tests/api/test_imports.py::test_a_content_free_upload_is_a_success_with_a_zero_state`; `FrequencyTable.test.tsx` zero-state test asserting `queryByRole("alert")` is absent |
| REQ-002-013 `+` | **PROVEN** | `tests/api/test_imports_logging.py` (5 tests). The success leg is explicitly non-vacuous: it asserts the sentinel actually reached a row (`forms[0]`, `forms[1].frequency == 2`) before asserting it is absent from every captured record. Also asserts no byte offset, no `0xff`, no `exc_info`. Cut-2 closure: `tests/integration/test_book_repository.py::test_a_persistence_failure_during_create_logs_code_and_no_raw_text`, `::test_reading_an_unknown_import_logs_the_attempted_id`. Spanning closure at cut 2 is genuine. See **W7** on `import_status`. |
| REQ-002-014 | **PROVEN** | `FrequencyTable.test.tsx::test_renders_received_order_and_display_form_verbatim` — mock order `zorro, arbol, strasse` is genuinely non-alphabetical, DOM asserted equal to received order, and `queryByText("strasse")` asserted absent, which is what proves `display_form` is not re-derived. `::test_frequency_column_is_not_colour_only`. `no-linguistic-rules.test.ts` (3 tests). Source read directly: `FrequencyTable.tsx` renders `result.forms.map(...)` with no transformation. See **W1/W2** on the guard's strength. |
| REQ-002-015 | **PROVEN** | `tests/unit/test_normalizer.py::test_normalize_is_idempotent` (Hypothesis) + the parametrized `N1`–`N5` table + the internal-occurrence ordering case the spec mandates at §2.3 (`a\u0149b`), not just the standalone `ŉ` |
| REQ-002-016 | **PROVEN** | `tests/unit/test_frequency.py::test_aggregation_is_order_independent_hypothesis` — asserts key set, form→frequency map, form→display-form map, **and** full table equality under `st.permutations`; `::test_permuting_a_tied_group_does_not_change_the_display_form` rotates a 3-way tie and pins `STRASSE` every time. A positional tie-break cannot survive either. |
| REQ-002-017 | **PROVEN** | `tests/unit/test_frequency.py::test_frequencies_are_never_negative_hypothesis`; `::test_non_positive_counts_are_rejected` parametrized over `[0, -1]` expecting `ValueError`; JSON-Schema leg `test_import_contract.py::test_schema_rejects_a_zero_frequency_row` |
| REQ-002-018 `+` | **PROVEN** | AC-002-23 ✅ `tests/unit/test_frequency.py::test_majority_and_tie_break_display_form` (both worked examples, `Straße` @4 and `STRASSE` tie-break); `tests/api/test_imports.py::test_each_row_carries_both_the_grouping_key_and_the_display_form`. AC-002-24 clause 1 ✅ `::test_display_form_is_substring_of_source`. AC-002-24 clause 2 ✅ `tests/integration/test_alembic_0002.py::test_upgrade_adds_no_display_form_column`, which inspects real `book` and `occurrence` columns after the migration reaches head. |

**Totals: 18 PROVEN, 0 PARTIALLY PROVEN, 0 UNPROVEN.**

## 4. CRITICAL findings

None remain.

### Resolved C1 — AC-002-24 clause 2 now has a permanent migration-column guard

`apps/api/tests/integration/test_alembic_0002.py::test_upgrade_adds_no_display_form_column`
now upgrades the migration to head, reflects the real `book` and `occurrence` table columns,
and asserts that neither table contains `display_form`. The `AC-24` map in
`openspec/changes/text-import/tasks.md` now names an existing test, and the focused command
passes:

```text
cd apps/api && uv run pytest tests/integration/test_alembic_0002.py::test_upgrade_adds_no_display_form_column -q
1 passed
```

### Resolved C2 — AC-002-14 clause 3 now has a permanent book-table POS guard

`apps/api/tests/integration/test_occurrence_pos.py::test_book_table_has_no_part_of_speech_column`
now reflects the real `book` table and asserts that neither `pos` nor `part_of_speech` exists
there. `docs/traceability-matrix.md` and the `AC-14` row in `tasks.md` now include this guard.
The focused command passes:

```text
cd apps/api && uv run pytest tests/integration/test_occurrence_pos.py::test_book_table_has_no_part_of_speech_column -q
1 passed
```

## 5. WARNING findings

### W1 — `no-linguistic-rules.test.ts` is a plain text search with no comment exemption

`apps/web/tests/contracts/no-linguistic-rules.test.ts:30` defines
`FORBIDDEN_PATTERN = /\.sort\(|toLowerCase\(|localeCompare\(|normalize\(|NFC|NFD|NFKC|NFKD/`
and applies it at line 80 to the **raw source text** of each manifest module.

I verified the consequence empirically, outside the repo, by running the exact regex:

```
true  | COMMENT containing .sort(   | // do not call .sort( on the rows
true  | COMMENT containing NFC      | /* NFC is applied server-side */
```

This is precisely the pathology cut 1b removed from the backend naming guard and cut 1c's
remediation removed from the frontend naming guard — a text search that forbids the word
inside the sentence explaining why the word is forbidden. `spec.md:494-500` states the
principle explicitly ("A text search is the weaker instrument, not the stronger one") and
`spec.md:927` (hook H1) says "do not revert this to a grep". That reasoning was applied to
`AC-002-10` and never carried across to `AC-002-19`, which is the other guard over the same
directory. `AC-002-19`'s own wording asks for a search, so the shipped guard is
*spec-compliant*; the inconsistency is between the two guards, and the first person to write
an explanatory comment in `FrequencyTable.tsx` will hit the false positive that has already
cost this project one reworded docstring.

### W2 — the same guard's detection direction is pinned by no permanent test, and it under-detects

Two distinct problems in one guard.

**(a) No detection test.** `no-lemma-naming.test.ts` got six permanent `findViolations` tests
in the cut-1c remediation; `test_no_soft_delete.py` got
`test_a_column_identifier_named_deleted_at_still_fails`; `test_no_lemma_naming.py` has three.
`no-linguistic-rules.test.ts` has **none** — nothing calls the forbidden-pattern check with a
known violation and asserts it fires. Its non-vacuity is protected (assertion 1 forces every
manifest entry to exist on disk, so the walk cannot silently empty), but its *detection* is
not. `T1C09`'s recorded RED was the on-disk existence assertion failing on a missing
`ImportPage.tsx` — that proves assertion 1, and says nothing about the pattern check.

**(b) Under-detection.** Measured against the same regex:

```
false | toSorted (ES2023 immutable sort) | const sorted = [...rows].toSorted()
false | reverse                          | rows.reverse()
false | Intl.Collator                    | new Intl.Collator('es').compare(a,b)
```

`REQ-002-014` (`spec.md:701-704`) forbids the frontend to "re-sort the list". `toSorted()` is
the modern immutable sort and is exactly what a developer would reach for in a React render
path where mutating `.sort()` is a known bug. The guard would not see it. `AC-002-19` names
only the five legacy patterns, so the guard matches the AC literally while under-enforcing
the requirement the AC exists to serve.

*(For the record: the shipped `FrequencyTable.tsx` uses none of these — it renders
`result.forms.map(...)` verbatim. This is a guard-strength finding, not a live defect.)*

### W3 — `test_traceability.py` contains zero SPEC-002 assertions

`apps/api/tests/unit/test_traceability.py` is entirely SPEC-001 scoped: it asserts on
`REQ-001-007`, `REQ-001-015`, `REQ-001-001…018`, the README command surface, and the archived
`project-foundation-bootstrap` tasks. A grep for `REQ-002` in that file returns **0 matches**.

Yet five tasks — `T1A11`, `T1B22`, `T1C15`, `T218`, `T311` — each end with "Re-run
`cd apps/api && uv run pytest tests/unit/test_traceability.py -q`" as the verification step
for the SPEC-002 matrix rows they add, and `#4075` cites "traceability 5 passed" as
whole-capability evidence. **Those 5 passing tests are silent about SPEC-002.** The matrix
rows could have been omitted, duplicated, or left `En progreso` and the suite would still be
green.

The matrix itself is correct — I checked independently: all **18** `REQ-002-*` rows are
present, each appears once, and all are `Cumplido`. So AGENTS.md §10's DoD clause is
satisfied in substance. The gap is that the automated check everyone is citing does not
check it.

### W4 — eleven test-function names in the `tasks.md` AC map do not exist

I resolved every `::test_*` reference in `tasks.md` against the test tree. Missing:

| Cited in AC map | Real equivalent on `main` |
|---|---|
| `test_max_import_size_bytes_default_and_override` (AC-03) | `test_max_import_size_bytes_defaults_to_four_mebibytes` + `::test_max_import_size_bytes_env_override` |
| `test_filename_and_content_type_gate[wrong_extension]` (AC-02) | `test_unsupported_filename_is_rejected_before_any_byte_is_read` |
| `test_size_gate_streaming_abort[oversized]`/`[at_limit]` (AC-04) | `test_body_one_byte_over_the_limit_is_rejected` + `::test_body_exactly_at_the_limit_is_accepted` |
| `test_strict_utf8_decode_and_bom_strip` (AC-05) | `test_valid_utf8_decodes_verbatim` + `::test_leading_bom_is_stripped` + 6 more |
| `test_post_imports_multipart_returns_201_with_forms` (AC-01) | `test_a_synthetic_txt_upload_is_created` |
| `test_post_imports_json_path_returns_422` (AC-01) | `test_a_json_filesystem_path_is_refused_and_nothing_is_computed` |
| `test_post_notes_pdf_returns_422_invalid_file_type` (AC-02) | `test_a_wrong_extension_is_refused_naming_the_accepted_one` |
| `test_empty_and_whitespace_only_upload_succeeds` (AC-17) | `test_a_content_free_upload_succeeds_with_zero_forms` |
| `test_post_empty_file_returns_201_zero_forms` (AC-17) | `test_a_content_free_upload_is_a_success_with_a_zero_state` |
| `test_post_imports_response_includes_display_form` (AC-23) | `test_each_row_carries_both_the_grouping_key_and_the_display_form` |
| `test_upgrade_adds_no_display_form_column` (AC-24) | **resolved in this remediation — the test now exists and passes** |

Ten were renames with real, adequate equivalents, so the evidence exists and the requirements
stand. The only genuinely missing citation (`test_upgrade_adds_no_display_form_column`) now
exists after this remediation. The remaining ten names are still paperwork drift: the AC map is
the artifact a verifier is meant to navigate by, and these citations do not resolve by their
historical names. `tasks.md` note 5 already fixed one instance of exactly this
(`test_backend_sources_contain_no_lemma_naming`), calling it "pre-existing paperwork drift" —
the sweep was never widened. `docs/traceability-matrix.md`, by contrast, resolves **100%
clean**; I checked every `::test_*` reference in it and found no dangling name.

### W5 — the "99 % coverage gate" cited in tasks and design does not exist

`T311` says to confirm "the 0-warning / 99% coverage gate holds"; design §13 says the suite is
at "99 % coverage" and that nothing "weakens it: … no `--cov-fail-under` change". The actual
enforced gates:

- `apps/api/pyproject.toml` `[tool.coverage.report]` — **no `fail_under` at all**.
- `.github/workflows/ci.yml:33` — `uv run pytest --cov=wheel_vocabulary --cov-fail-under=80`.

The real backend gate is **80 %**. Measured coverage is **100.00 %**, so there is no live
risk, but the margin between the gate and reality is 20 points, not 1, and three artifacts
state a number that is not enforced anywhere.

### W6 — frontend branch coverage is ungated and materially incomplete

`apps/web/vitest.config.ts:18` sets `thresholds: { lines: 70 }` under `CI_COVERAGE_MODE=fail`
— **lines only**. Measured: 100 % stmts / 100 % lines / 100 % funcs / **84 % branch**, with
`ImportForm.tsx` at **57.14 % branch** and `DeleteImportButton.tsx` at 85.71 %.

Reading `ImportForm.tsx`, the uncovered branches are: the no-file-selected reset
(`event.target.files?.[0]` falsy → `{kind:"idle"}`, line 21), the non-`Error` rejection
fallback (`"Error desconocido"`, line 42), the `if (inputRef.current)` guard (line 35), and
the `state.kind !== "selected"` early return (line 26). None carries an acceptance criterion,
so no AC is affected — but "Error desconocido" is a user-facing string on the error path that
Art. IX.3 makes perceptible, and nothing exercises it.

### W7 — `import_status: "failed"` is specified but unreachable, and the pinned schema admits only `"succeeded"`

`REQ-002-013` (`spec.md:673-681`) states "`import_status` MUST be one of `succeeded` or
`failed`". The shipped contract narrows this:

- `api/schemas/import.v1.json` — `$.properties.import_status` is
  `{"type": "string", "enum": ["succeeded"]}`.
- `persistence/models.py:27-29` — "terminal-only: every row here is `succeeded`, because a
  failed import is never persisted".

No code path anywhere writes or returns `"failed"`, and no test asserts it. The narrowing is
defensible (a failed import returns an error envelope, never a 201 body, so `"failed"` can
never be serialised) and arguably *tighter* than the requirement. But the spec names a
two-value enum and ships a one-value one, which is a contract/spec divergence a reader will
trip over. Worth an explicit spec note rather than leaving `failed` as vestigial surface.

### W8 — design §6.1's contiguity rationale is false in a reachable edge case

`design.md:366-369` justifies omitting the `(book_id, position)` unique index with: "an
invariant that a pure `domain` property test proves for free (positions are `0..n-1`,
contiguous, by construction of `tokenize`)".

That is not true once `ImportText._gate_5_aggregate` filters. I found a concrete input by
scanning the Unicode range:

```
tokens that normalize to empty: [('0x2bc', 'MODIFIER LETTER APOSTROPHE')]
```

`U+02BC` has general category `Lm`, so it is an `L*` character: `tokenize` emits it (T6 is
satisfied), but `normalize` folds it to `U+0027` at N4 and then N5 strips it to `""`. The
comprehension at `use_cases.py:178-182` drops it, so persisted `position` values gap.

**The behaviour is correct** — spec §2.3 N5 explicitly says "discard the token if nothing
remains", and `_gate_5_aggregate`'s docstring documents the drop. Two second-order notes:
`REQ-002-008`'s literal "one `Occurrence` row per emitted token" is not literally true for
such a token, and the design's stated reason for omitting the index is wrong even though the
decision itself remains fine (nothing depends on contiguity, and no uniqueness constraint
exists to violate).

## 6. SUGGESTION findings

- **S1** — `AC-002-24`'s substring clause is proven only at domain level
  (`test_frequency.py::test_display_form_is_substring_of_source`). There is no assertion over
  a real `GET` response that every returned `display_form` occurs in the imported source.
  Risk is low because design §1 makes `build_table()` the single implementation for both
  paths, and that sharing is itself tested
  (`test_counts_from_the_read_path_are_summed_not_recounted`).
- **S2** — `apps/api/pyproject.toml` sets `strict = true` only for `wheel_vocabulary.domain.*`
  and `wheel_vocabulary.application.*`; `infrastructure` and `api` run non-strict against
  Art. VIII.1 ("Python y TypeScript utilizarán tipado estricto"). This is a pre-existing
  SPEC-001 posture, not introduced by SPEC-002 — flagged only so it is a decision rather than
  a drift. The frontend is fully strict (`tsconfig.json:8`).
- **S3** — `mockups/text-import.html` is untracked in the working tree. Not committed, so
  Art. IV is unaffected, but it should be either committed deliberately or ignored.

## 7. Constitutional compliance

| Article | Verdict | Evidence |
|---|---|---|
| **Art. IV** (copyright, privacy, deletion) | ✅ **PASS** | The **only** text fixture tracked in git is `apps/web/e2e/fixtures/bosque.txt` (95 bytes, synthetic Spanish prose: "El lobo corre por el bosque…"). `git ls-files` for `.txt/.epub/.pdf/.mobi/.azw*` returns that single file. Provenance is recorded in both consuming specs (`import.spec.ts:3`, `delete-import.spec.ts:3`: "synthetic prose authored for this repository (T1C13, Art. IV.1-2, H6)"). The T-BENCH 4 MiB corpus is generated in-test by `_bench_corpus.generate_synthetic_corpus` and never committed — verified. Art. IV.8 (deletion) is shipped and tested. Hook H6 satisfied. |
| **Art. V** (linguistic model integrity) | ✅ **PASS** | Token / textual form / normalized form / occurrence are four distinct concepts in code: `Token.raw_text` + `Token.position`, `Occurrence.raw_text` vs `Occurrence.normalized_text` (separate columns, asserted distinct by `test_raw_text_and_normalized_text_stay_separate_values`), `FormFrequency.normalized_form` vs `.display_form`. `pos` is per-occurrence, nullable, `None` for every row (`test_every_persisted_occurrence_has_pos_none`), and absent from `Book`, now pinned by `test_book_table_has_no_part_of_speech_column`. Art. V.4 (inflected forms not merged) is asserted by `test_inflected_forms_stay_separate_rows` (`corres`/`corría`/`corro` → 3 rows). |
| **Art. VII** (architecture) | ✅ **PASS** | `test_domain_isolation.py` is AST-based, runs 3 tests, and carries an explicit non-vacuity assertion (`{relative paths} >= _EXPECTED_MODULES` over 6 named modules) — so the walk cannot silently resolve to zero. It bans `fastapi\|sqlalchemy\|pydantic\|spacy` imports, ISO-639-shaped literals, and language parameters. Art. VII.5: `FrequencyTable.tsx` renders `result.forms` verbatim with zero transformation; read directly, confirmed. |
| **Art. VIII** (code quality) | ⚠️ **PASS WITH NOTE** | Lint, format, and type checks all exit 0. No secrets tracked (`git ls-files` for `.env`/`secret`/`credential` → empty). Strict typing is partial on the backend — see **S2**. Art. VIII.4: error messages are actionable and content-free (`test_validation_envelope_never_echoes_the_rejected_input`). |
| **Art. IX** (accessibility) | ✅ **PASS** | IX.1 keyboard: `ImportForm.test.tsx` asserts `user.tab()` focuses the labelled input. IX.2 labels: `<label htmlFor="import-file-input">`, `aria-label="Importar texto"`, `aria-label="Importar un texto"` on the page section. IX.3 states: `aria-live="polite"` importing, `role="alert"` error, `role="status"` zero state — all three asserted. IX.4 no colour dependence: `<th scope="col">` headers plus text-content frequency, asserted by `test_frequency_column_is_not_colour_only`. IX.5 destructive confirm: three-leg assertion in `DeleteImportButton.test.tsx` plus an E2E confirming the table survives the first activation. IX.6 long-operation state: "Importando…" — the `CONTRA-1` disjunction resolution, correctly implemented. |

## 8. Design coherence

| Design decision | Shipped | Note |
|---|---|---|
| §3.5 no `form_frequency` aggregate table | ✅ | Trigger measured at 0.175–0.219 s vs 250 ms — correctly silent |
| §3.3 Core batched insert, never `Session.add_all()` | ✅ | `test_create_batches_occurrence_inserts_at_the_configured_size` |
| §6.2 two explicit `DELETE`s, never `ON DELETE CASCADE` | ✅ | `test_delete_removes_occurrences_without_relying_on_a_cascade` proves it with the pragma off |
| §5 no document-level NFC (protects `AC-002-24`) | ✅ | `raw_text` is a byte-exact slice; substring test passes |
| §7.2 no `exists()` on the port | ✅ | Verified absent; §7.2 snippet updated |
| §11 cut-scoped manifest | ✅ | `DeleteImportButton.tsx` appended by T309; assertion 3 would have caught its omission |
| §6.1 index-omission rationale | ⚠️ | Rationale factually wrong in an edge case — **W8** |
| §13 "99 % coverage" | ⚠️ | Gate is 80 % — **W5** |
| §13 T-BENCH "asserts …" wording | ⚠️ | Still hard-gate wording; superseded by `tasks.md` note 7. Flagged in note 7 as a pending maintainer edit; still unedited on `main`. |

## 9. Is SPEC-002 ready to archive?

**Yes, from the perspective of the two CRITICAL evidence gaps.**

The feature is correct, the gates are green, the numbers are honest, and the two missing
structural-absence guards now exist and pass. The remaining §5 and §6 findings are
maintainer judgement calls, not archival blockers.

## 10. What I checked hardest, and what I did not find

I did not manufacture findings. Specifically, these came back **clean**:

- **Orphan production symbols** — the check that caught the cut-2 deviation. Swept both apps.
  Zero orphans. `delete()` is wired end to end; `exists()` is entirely gone.
- **Vacuous absence guards** — every structural guard has an explicit non-vacuity assertion:
  `test_domain_isolation.py::test_domain_package_scan_is_not_vacuous`,
  `test_no_lemma_naming.py::test_the_scan_reaches_the_shipped_backend_sources`,
  `no-lemma-naming.test.ts::test_the_scan_reaches_the_shipped_frontend_sources`,
  and `no-linguistic-rules.test.ts`'s on-disk manifest assertion. None can pass over an empty
  walk.
- **Status-only assertions where the body matters** — checked every 404/422 path.
  `test_deleting_an_unknown_id_returns_the_domain_404_envelope` asserts
  `"detail" not in body` **and** `body["error"]["code"]`;
  `test_get_imports_on_an_unknown_id_is_the_domain_404_envelope` does the same. The trap the
  tasks warned about is genuinely closed.
- **Tests asserting on their own implementation's output** — `test_content_hash_matches_an_
  independently_computed_sha256` computes the expected digest with `hashlib` in the test.
  `test_display_form_is_substring_of_source` checks against the literal source string.
  `FrequencyTable.test.tsx` uses a hand-written non-alphabetical fixture. No tautologies found.
- **Mocked responses that never exercise the real path** — the logging success leg explicitly
  asserts the sentinel reached `forms[0]`/`forms[1]` before asserting log absence; T-BENCH
  asserts `distinct_form_count > 1_000` to prove the real pipeline ran at scale.
- **Spanning requirements flipped by T218** — `REQ-002-006`, `-007`, `-013`, `-018` each have
  a genuine cut-2 closing leg that runs and asserts. `-018`'s formerly incomplete closure is
  now pinned by `test_upgrade_adds_no_display_form_column`.
- **Copyright** — one 95-byte synthetic fixture, provenance documented, nothing else.

## 11. Report metadata

- Updated in `openspec/changes/text-import/verify-report.md` in the working tree.
  **Not committed, not pushed, not staged.**
- Remediation changes modify tests, tasks, traceability, and this report only; no production
  source changed.

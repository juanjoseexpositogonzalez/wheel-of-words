# Tasks: SPEC-002 — Import a .txt and view word frequencies

> Repo `main` @ `aefbcf0`. Capability `002-text-import`. Authoritative cut allocation: spec §1.2
> (reconciled with `design.md` §12.4), five cuts, `stacked-to-main`, no `size:exception`. Not
> re-litigated here. Test runner: `cd apps/api && uv run pytest`; frontend: `cd apps/web && npx vitest run`.

**Size-budget note.** This artifact intentionally exceeds the generic ~530-word `sdd-tasks` template
budget. The orchestrator brief requires a complete 18-REQ / 24-AC → task → test map with named test
functions across five cuts under strict TDD — that deliverable cannot fit in 530 words. Reporting the
deviation explicitly rather than truncating the map (AGENTS.md §9).

**Task-type convention (AGENTS.md §8).** The most specific admitted type wins: a Playwright task is
`[E2E]` and a design §15 threat-matrix task is `[SECURITY]` even when the deliverable is a test file.
The `[TEST]` → `[IMPL]` → `[REFACTOR]` order is therefore preserved **by position**, not by literal
tag — every RED-authoring task still precedes the production task it drives. `[SPEC]` and `[CI]` are
unused because this change authors no specification and touches no workflow or CI configuration;
they are omitted rather than forced. Three tasks genuinely mix two kinds and are left on their
primary type rather than mislabelled: **T1B07** (strict-decode behaviour, with `from None` log
hygiene as a secondary effect) and **T1B13** (use-case orchestration, with the §8 gate order as a
secondary effect) stay `[IMPL]`; **T201** stays `[TEST]` because it is an integration test *of* a
migration, not a migration.

**Expected-RED standard (AGENTS.md §3).** Every task that authors a test states the concrete failure
it must produce — the exception class, the HTTP status, or the failing assertion — and why that
failure is attributable to the absent behaviour rather than to mis-wiring, a broken fixture, or
configuration. Absence assertions (`H1`, `H2`, `H8`, and the frontend lemma-naming leg) cannot fail
naturally: they pass on their first run over correct code, which is evidence of nothing. Those tasks
therefore specify a **mutation check** — introduce the violation, see the named `AssertionError`,
revert — and are not complete until that failure has been observed.

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | 1a ≈435 · 1b ≈660 · 1c ≈525 · 2 ≈490 · 3 ≈330 (design §12.4, re-checked against this task list's file set — holds) |
| 400–700 authored-line band (spec §1.2) | All five cuts inside or below it; **1b sits closest to the 700 ceiling** |
| 400-line budget risk | Medium — no cut needs `size:exception`, but 1b (~660) has the least margin: 3 threat-matrix RED-test groups + CORS + error taxonomy + JSON Schema all land there |
| Chained PRs recommended | Yes — already the plan (5 cuts = 5 PRs) |
| Suggested split | PR 1 (1a) → PR 2 (1b) → PR 3 (1c) → PR 4 (2) → PR 5 (3) |
| Delivery strategy | Cached by the authoritative plan — cut boundaries and chain strategy are not re-litigated |
| Chain strategy | `stacked-to-main` |

```text
Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: Medium
```

### Suggested Work Units (= the five cuts, each one PR)

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|
| 1a | Language engine: tokenize/normalize/aggregate, pure, stdlib-only | PR 1 | `cd apps/api && uv run pytest tests/unit/test_tokenizer.py tests/unit/test_normalizer.py tests/unit/test_frequency.py tests/unit/test_domain_isolation.py -q` | N/A — *verificable* cut, no UI/route exists yet (Art. III.2 disjunction); proven by the pytest suite alone | Delete `domain/{models.py,text/,frequency.py}` + their tests; nothing else references them yet |
| 1b | `POST /api/v1/imports` returns the ordered table (no persistence yet) | PR 2 | `cd apps/api && uv run pytest tests/unit/test_settings.py tests/unit/test_import_errors.py tests/unit/test_text_extraction.py tests/unit/test_import_ports.py tests/unit/test_import_text.py tests/api/test_imports.py tests/api/test_imports_cors.py tests/api/test_imports_logging.py tests/unit/test_no_lemma_naming.py -q` | N/A — *verificable* cut, no UI yet; proven by pytest + OpenAPI + `import.v1.json` | Revert `application/imports/`, `infrastructure/text_extraction.py`, `api/routes/imports.py`, `api/dtos/imports.py`, `api/errors.py`, `api/schemas/import.v1.json`, and the `main.py` router/CORS additions; 1a's `domain/` stays valid standalone |
| 1c | Upload form + frequency table + zero/loading state | PR 3 | `cd apps/web && npx vitest run tests/api/imports.test.ts tests/components/ImportForm.test.tsx tests/components/FrequencyTable.test.tsx tests/contracts/no-linguistic-rules.test.ts` | `cd apps/web && npx playwright test e2e/import.spec.ts` — real browser, real CORS preflight (design §14.1 backstop) | Remove `apps/web/src/{pages/ImportPage.tsx,components/{ImportForm,FrequencyTable}.tsx,api/imports.ts,types/imports.ts}` + their tests; backend cuts 1a/1b stay valid without a UI |
| 2 | Persist `Book`/`Occurrence`; `GET` survives a restart | PR 4 | `cd apps/api && uv run pytest tests/integration/test_alembic_0002.py tests/integration/test_book_repository.py tests/integration/test_occurrence_pos.py tests/integration/test_import_bench.py tests/api/test_imports.py -q` | `cd apps/api && uv run alembic upgrade head && uv run uvicorn wheel_vocabulary.api.main:app &` then restart the process and re-`GET` the same import id — proves restart survival, not just the test DB session | `alembic downgrade -1`; revert `infrastructure/persistence/{models.py,book_repository.py}` and `ImportText`'s persistence branch; 1b's non-persisting response path still works standalone |
| 3 | `DELETE` with confirmation UI | PR 5 | `cd apps/api && uv run pytest tests/integration/test_delete_import.py tests/api/test_imports_cors.py -q -k delete` `&& cd apps/web && npx vitest run tests/components/DeleteImportButton.test.tsx` | `cd apps/web && npx playwright test e2e/delete-import.spec.ts` | Revert the `DELETE` route, `DeleteImportButton.tsx`, `BookRepository.delete()`, and the `main.py` `DELETE` CORS addition; cuts 1a–2 stay fully functional without deletion |

---

## Requirement → Acceptance → Cut → Task → Test map

All 18 requirements, all 24 acceptance criteria. `+` marks a spanning requirement whose full closure
is at cut 2 (spec §1.2 spanning table) — `sdd-verify` MUST NOT mark it satisfied earlier.

| AC | REQ | Cut(s) | Task(s) | Test file :: function |
|---|---|---|---|---|
| AC-01 | REQ-002-001 | 1b | T1B15, T1B16 | `tests/api/test_imports.py::test_post_imports_multipart_returns_201_with_forms`, `::test_post_imports_json_path_returns_422` |
| AC-02 | REQ-002-002 | 1b | T1B10, T1B13, T1B16 | `tests/unit/test_import_text.py::test_filename_and_content_type_gate[wrong_extension]`, `tests/api/test_imports.py::test_post_notes_pdf_returns_422_invalid_file_type` |
| AC-03 | REQ-002-003 | 1b | T1B01, T1B02 | `tests/unit/test_settings.py::test_max_import_size_bytes_default_and_override` |
| AC-04 | REQ-002-003 | 1b | T1B11, T1B13 | `tests/unit/test_import_text.py::test_size_gate_streaming_abort[oversized]`, `[at_limit]` |
| AC-05 | REQ-002-004 | 1b | T1B06, T1B07 | `tests/unit/test_text_extraction.py::test_strict_utf8_decode_and_bom_strip` |
| AC-06 | REQ-002-005 | 1a | T1A10 | `tests/unit/test_domain_isolation.py::test_domain_has_no_framework_imports_or_iso639_literals` |
| AC-07 | REQ-002-005 | 1a | T1A01, T1A04 | `tests/unit/test_tokenizer.py::test_tokenization_rules[T1..T10]`, `tests/unit/test_normalizer.py::test_normalization_rules[N1..N5]` |
| AC-08 | REQ-002-006 `+` | 1a→1b→**2** | T1A07, T1B15, T211 | `tests/unit/test_frequency.py::test_repeated_forms_collapse_with_frequency_and_sum`; `tests/api/test_imports.py::test_a_synthetic_txt_upload_is_created`; `::test_get_imports_returns_the_ordered_table_with_the_persisted_id` (sum check) |
| AC-09 | REQ-002-006 `+` | **2** | T211, T212 | `tests/api/test_imports.py::test_get_imports_diacritic_insensitive_order` |
| AC-10 | REQ-002-007 `+` | 1b→1c→**2** | T1B20, T1C14, T217 | `tests/unit/test_no_lemma_naming.py::test_no_backend_identifier_or_literal_names_a_lemma_or_a_lexeme`; `apps/web/tests/contracts/no-lemma-naming.test.ts::test_frontend_sources_contain_no_lemma_naming`; `apps/web/tests/contracts/no-lemma-naming.test.ts` describe block `findViolations (remediation — pins the comment exemption directly)` (5 tests, pins the comment exemption and the identifier/string-literal/template-literal/JSX-text detection directly, see contradiction note 6); `tests/unit/test_no_lemma_naming.py::test_persisted_columns_contain_no_lemma_naming` (cut 2, closed — checks `infrastructure/persistence/models.py`, the `0002_book_occurrence` migration, and the reflected `Base.metadata` column names) |
| AC-11 | REQ-002-008 | 2 | T201, T202 | `tests/integration/test_alembic_0002.py::test_upgrade_and_downgrade_book_occurrence` |
| AC-12 | REQ-002-008 | 2 | T207, T208, T209 | `tests/integration/test_book_repository.py::test_frequency_pairs_survives_a_new_session_against_the_same_database` |
| AC-13 | REQ-002-009 | 2 | T206 | `tests/integration/test_book_repository.py::test_content_hash_matches_an_independently_computed_sha256` |
| AC-14 | REQ-002-010 | 2 | T205 | `tests/integration/test_occurrence_pos.py::test_every_persisted_occurrence_has_pos_none`, `::test_raw_text_and_normalized_text_stay_separate_values` |
| AC-15 | REQ-002-011 | 3 | T301, T302, T304 | `tests/integration/test_delete_import.py::test_delete_removes_book_and_occurrences_with_zero_orphans` |
| AC-16 | REQ-002-011 | 3 | T308, T309 | `apps/web/tests/components/DeleteImportButton.test.tsx::test_requires_confirmation_before_deleting` |
| AC-17 | REQ-002-012 | 1b | T1B12, T1B13 | `tests/unit/test_import_text.py::test_empty_and_whitespace_only_upload_succeeds`, `tests/api/test_imports.py::test_post_empty_file_returns_201_zero_forms` |
| AC-18 | REQ-002-013 `+` | 1b(partial)→**2**(closed) | T1B18, T1B19, T213, T214 | `tests/api/test_imports_logging.py::test_a_successful_import_logs_no_imported_text`, `::test_a_decode_failure_logs_the_error_code_and_the_import_id`; `tests/integration/test_book_repository.py::test_a_persistence_failure_during_create_logs_code_and_no_raw_text`, `::test_reading_an_unknown_import_logs_the_attempted_id` |
| AC-19 | REQ-002-014 | 1c | T1C07, T1C09 | `apps/web/tests/components/FrequencyTable.test.tsx::test_renders_received_order_and_display_form_verbatim`, `::test_frequency_column_is_not_colour_only`; `apps/web/tests/contracts/no-linguistic-rules.test.ts::test_import_modules_have_no_linguistic_rules` |
| AC-20 | REQ-002-015 | 1a | T1A04 | `tests/unit/test_normalizer.py::test_normalize_is_idempotent` |
| AC-21 | REQ-002-016 | 1a | T1A07 | `tests/unit/test_frequency.py::test_aggregation_is_order_independent_hypothesis` |
| AC-22 | REQ-002-017 | 1a | T1A07 | `tests/unit/test_frequency.py::test_frequencies_are_never_negative_hypothesis` |
| AC-23 | REQ-002-018 `+` | 1a→1b→**2** | T1A07, T1B15 | `tests/unit/test_frequency.py::test_majority_and_tie_break_display_form`; `tests/api/test_imports.py::test_post_imports_response_includes_display_form` |
| AC-24 | REQ-002-018 `+` | 1a→1b→**2** | T1A07, T1B15, T202 | `tests/unit/test_frequency.py::test_display_form_is_substring_of_source`; `tests/integration/test_alembic_0002.py::test_upgrade_adds_no_display_form_column` |

**REQ index (all 18) → primary cut:** `-001` 1b · `-002` 1b · `-003` 1b · `-004` 1b · `-005` 1a ·
`-006`+ 1a/1b/**2** · `-007`+ 1b/1c/**2** · `-008` 2 · `-009` 2 · `-010` 2 · `-011` 3 · `-012` 1b ·
`-013`+ 1b/**2** · `-014` 1c · `-015` 1a · `-016` 1a · `-017` 1a · `-018`+ 1a/1b/**2**.

---

## Cut 1a — language engine (verificable, ~435 lines)

- [x] T1A01 `[TEST]` Parametrized tokenizer rule table for T1–T10 in `tests/unit/test_tokenizer.py::test_tokenization_rules[...]`. Expects `ModuleNotFoundError` — `domain/text/tokenizer.py` does not exist yet; that is the correct RED because no production code has been written.
- [x] T1A02 `[IMPL]` Create `domain/models.py::Token` and `domain/text/tokenizer.py::tokenize()` per spec §2.2.
- [x] T1A03 `[REFACTOR]` Extract the §2.1 word-char/joiner/separator Unicode-category checks into named private helpers in `tokenizer.py` for reuse by `normalizer.py`. T1A01 stays green.
- [x] T1A04 `[TEST]` Parametrized rule table for N1–N5, adversarial code points (`ŉ`, `Straße`, `ẞ`, `İ`, `ΣΊΣΥΦΟΣ`), and the Hypothesis idempotence property (AC-002-20) in `tests/unit/test_normalizer.py`. Expects `ModuleNotFoundError: No module named 'wheel_vocabulary.domain.text.normalizer'` at collection — `domain/text/normalizer.py` does not exist yet; that is the correct RED because no production code has been written, so the failure cannot be a fixture or configuration fault.
- [x] T1A05 `[IMPL]` Create `domain/text/normalizer.py::normalize()` implementing N1–N5 in the normative order (N4 after N2/N3, per §2.3).
- [x] T1A06 `[REFACTOR]` Name each N1–N5 step as a private helper for direct spec-row traceability. No behavior change.
- [x] T1A07 `[TEST]` `build_table()` D1–D3 worked examples (both AC-002-23 cases), `sort_key()` §2.4, the order-independence Hypothesis property over keys+frequencies+display forms (AC-002-21), and the non-negative-frequency Hypothesis property (AC-002-22) in `tests/unit/test_frequency.py`. Expects `ModuleNotFoundError: No module named 'wheel_vocabulary.domain.frequency'` at collection — `domain/frequency.py` does not exist yet; that is the correct RED because no production code has been written, so the failure cannot be a fixture or configuration fault.
- [x] T1A08 `[IMPL]` Create `domain/models.py::FormFrequency` and `domain/frequency.py::build_table()`/`sort_key()` per spec §2.4–2.5.
- [x] T1A09 `[REFACTOR]` Extract D1 (count), D2 (max), D3 (tie-break) into named private helpers inside `build_table()` for auditability.
- [x] T1A10 `[TEST]` Structural guard (hook H2, AC-002-06): no `fastapi|sqlalchemy|pydantic|spacy` import and no ISO-639 literal across `domain/`, run **after** T1A02/T1A05/T1A08 so the scan is meaningful (an earlier run would vacuously pass on an empty package). **RED is a deliberate mutation check, not a natural failure** — an absence assertion over correct code passes on the first run, which proves nothing. Before accepting it, add `import sqlalchemy` to `domain/frequency.py`, confirm the test fails with `AssertionError` naming `frequency.py` and the matched pattern, then revert the import and confirm green. That two-step is what distinguishes a guard that detects the violation from one that is vacuously true because its file walk resolved to zero files. **Bookkeeping fix (remediation work unit):** the checkbox had been left `[ ]` since cut 1a even though `tests/unit/test_domain_isolation.py::test_domain_has_no_framework_imports_or_iso639_literals` matches this description exactly, exists, passes (3 tests in the file), and sits inside the 100%-covered suite — confirmed by re-running `cd apps/api && uv run pytest tests/unit/test_domain_isolation.py -q` (3 passed) before flipping. No new test or production code required.
- [x] T1A11 `[DOC]` Add `docs/traceability-matrix.md` rows for REQ-002-005/-015/-016/-017 (`Cumplido`) and note the domain leg of REQ-002-006/-018 (`En progreso`, "complete at cut 2"). Re-run `cd apps/api && uv run pytest tests/unit/test_traceability.py -q`.

## Cut 1b — callable import (verificable, ~660 lines — tightest cut)

- [x] T1B01 `[TEST]` `Settings.max_import_size_bytes` default `4194304` + `MAX_IMPORT_SIZE_BYTES` override (AC-002-03) in `tests/unit/test_settings.py`. Expects `AttributeError: 'Settings' object has no attribute 'max_import_size_bytes'` — the module imports fine, so the failure is not a wiring or fixture fault; it is the field itself being absent, which is exactly the missing behavior.
- [x] T1B02 `[IMPL]` Add `max_import_size_bytes: int = 4_194_304` to `infrastructure/settings.py`.
- [x] T1B03 `[TEST]` Five exception classes carry a `code` `ClassVar` and only safe fields (no text/offset/path) in `tests/unit/test_import_errors.py`. Expects `ModuleNotFoundError: No module named 'wheel_vocabulary.application.imports.errors'` at collection — the package does not exist yet, so no partial implementation can mask the gap.
- [x] T1B04 `[IMPL]` Create `application/imports/errors.py` (five classes per design §9.1) + `api/errors.py` handlers (incl. `INVALID_REQUEST` for `RequestValidationError`) + `api/dtos/imports.py` error DTO (`extra="forbid"`) + `api/schemas/import.v1.json` (Draft 2020-12, `X-Schema-Version: 1`). Per the T1B13 resolution, the 1b success schema declares **no `id` property at all** — not `"id": {"type": ["integer", "null"]}` — and does not list `id` in `required`; cut 2 (T212) then adds it additively.
- [x] T1B05 `[REFACTOR]` Align `api/errors.py` handler registration with `dtos/health.py`/`main.py` conventions. No behavior change.
- [x] T1B06 `[TEST]` Strict UTF-8 decode rejects `0xFF` with `InvalidEncodingError`; a leading `EF BB BF` BOM is stripped and tolerated (AC-002-05) in `tests/unit/test_text_extraction.py`. Expects `ModuleNotFoundError: No module named 'wheel_vocabulary.infrastructure.text_extraction'` at collection — no extractor exists, so neither leg can pass accidentally through Python's own default decode.
- [x] T1B07 `[IMPL]` Create `infrastructure/text_extraction.py::PlainTextExtractor` (strict decode, BOM strip, `raise ... from None` — no offset leakage).
- [x] T1B08 `[TEST]` `ByteStream`/`TextExtractor`/`BookRepository` `Protocol` shapes are structural (a plain stub satisfies them without inheritance) in `tests/unit/test_import_ports.py`. Expects `ModuleNotFoundError: No module named 'wheel_vocabulary.application.imports.ports'` at collection — the Protocols do not exist, so the `isinstance`-against-`runtime_checkable` assertions have no target to be satisfied by.
- [x] T1B09 `[IMPL]` Create `application/imports/ports.py` with the three Protocols per design §7.2.
- [x] T1B10 `[SECURITY]` Threat-matrix — filename/content-type classification (design §15 row 1): `notes.pdf`→422 `INVALID_FILE_TYPE`; `SAMPLE.TXT`→accepted; `../../etc/passwd.txt`→judged on suffix only, no path constructed; missing filename→422, in `tests/unit/test_import_text.py`. Expects `ModuleNotFoundError: No module named 'wheel_vocabulary.application.imports.use_cases'` at collection — `ImportText` doesn't exist. That is the correct RED because gate #1 (design §8) must reject before any byte is read: with no use case at all there is no earlier code path that could reject for an unrelated reason and make the test pass while the gate is still missing.
- [x] T1B11 `[SECURITY]` Threat-matrix — unbounded resource intake (design §15, adjacent boundary 1): 65-byte body against a 64-byte limit → `FileTooLargeError`, bounded to ≤64 KiB read; absent `Content-Length` still rejected at the streaming gate; exactly-at-limit → accepted (`>` not `>=`, AC-002-04) in `tests/unit/test_import_text.py`. Same `ModuleNotFoundError` RED as T1B10, and correct for a sharper reason: the ≤64 KiB read-volume assertion can only be satisfied by a streaming gate, so no post-hoc `len(body) > limit` check added later could turn it green without the bounded loop actually existing.
- [x] T1B12 `[TEST]` Empty and whitespace-only uploads succeed with zero forms (AC-002-17/REQ-002-012) in `tests/unit/test_import_text.py`. Same `ModuleNotFoundError` RED as T1B10 — `ImportText` is absent, so the zero-form success path cannot be reached at all, let alone mistaken for an error path.
- [x] T1B13 `[IMPL]` Create `application/imports/use_cases.py::ImportText` implementing the ordered gate (design §8: ext/type → size → decode → tokenize → normalize → `build_table`), **no `BookRepository.create()` call yet** — persistence is cut 2. **Ambiguity resolved by maintainer decision: the cut-1b `201` body OMITS `id` entirely; it is NOT `id: null`.** Three reasons, binding on T1B04, T1B15, T1B16 and T1C02: (1) `null` asserts the concept exists but its value is unknown, which is false at 1b — there is no `Book` row and therefore no identity to report; omission says the true thing, that this version of the endpoint has no import identity yet. (2) It keeps cut 2 purely additive under the versioned JSON Schema with `extra="forbid"` — adding an absent field is additive, whereas turning an existing `null` into a real value is a semantic change to a field clients already read. (3) Cut 1c's UI therefore never branches on a null id, because it never sees one.
- [x] T1B14 `[REFACTOR]` Extract the five-gate pipeline into named private methods on `ImportText`, one per design §8 row.
- [x] T1B15 `[TEST]` `POST /api/v1/imports` contract: multipart `.txt` → 201 with ordered `forms` carrying `normalized_form`+`display_form` (AC-002-01 success leg, AC-002-08 response half, AC-002-23/24 field presence); JSON `{"path": ...}` → 422, nothing computed (AC-002-01 rejection leg) in `tests/api/test_imports.py`. Per the T1B13 resolution, assert `"id" not in body` — presence with a `null` value must fail this test as loudly as presence with an integer. Expects `404` from Starlette's router — `POST /api/v1/imports` is not registered yet, so the `assert response.status_code == 201` fails on `404`, not on a body assertion. That distinction is the proof: a `404` can only come from a wholly absent route, whereas a `422`/`500` here would mean the route exists and is mis-wired.
- [x] T1B16 `[IMPL]` Create `api/routes/imports.py` (thin `POST`), `api/dependencies.py` (`get_text_extractor`, `get_book_repository` stub, `get_import_text`), wire the router into `api/main.py`, extend `allow_methods=["GET", "POST"]` at `main.py:36`. The 1b success DTO declares no `id` field at all (T1B13 resolution) — do not add an `id: int | None = None`, which would serialise as `"id": null`.
- [x] T1B17 `[TEST]` CORS preflight for `POST`: `OPTIONS /api/v1/imports` with explicit `Origin` + `Access-Control-Request-Method: POST` → 200, `access-control-allow-methods` contains `POST`, in `tests/api/test_imports_cors.py`. Expects `assert response.status_code == 200` to fail on `400`: Starlette's `CORSMiddleware` answers a preflight whose requested method is outside `allow_methods` with `400` and the body `Disallowed CORS method`, so against today's `allow_methods=["GET"]` the RED is a concrete status mismatch, not a missing header. That proves the middleware is reached and rejecting — a mis-wired route would give `404`/`405` instead. A default `TestClient` request without `Origin` + `Access-Control-Request-Method` would NOT catch this; this test sends both explicitly.
- [x] T1B18 `[SECURITY]` Threat-matrix — sensitive-content egress (design §15, adjacent boundary 2): a sentinel `zzqxsentinel` import yields zero log records containing it on the success path; a decode failure logs only `code`+`import_id`, never a byte offset (AC-002-18, success + decode-failure legs) in `tests/api/test_imports_logging.py`. Two distinct REDs, and only the second is load-bearing: the success leg passes vacuously before T1B19 because nothing logs at all, so verify it the T1A10 way — temporarily log the decoded text, confirm the sentinel assertion fails, revert. The decode-failure leg is a genuine `AssertionError`: the assertion that some captured record matches `code=INVALID_ENCODING` finds zero records, because no handler emits one yet. Both must be seen failing before T1B19; a green-on-first-run success leg is a vacuous guard, not a pass.
- [x] T1B19 `[SECURITY]` Wire the module logger to emit `code=<CODE> import_id=-` only; `raise ... from None` on the UTF-8 decode path; no `logger.exception()` on `UnicodeDecodeError`.
- [x] T1B20 `[TEST]` Repo-wide lemma-naming guard, backend leg (hook H1, AC-002-10): zero `lemma|lemas|lexeme|lexema` matches across `apps/api/src/wheel_vocabulary/`; POST response keys are exactly `normalized_form`/`display_form`, in `tests/unit/test_no_lemma_naming.py`. Meaningful from the moment `routes/imports.py`/`dtos/imports.py` exist (T1B16). **Two REDs of different quality, and the task is not done until both are seen.** The response-key half is a real `AssertionError`: run it before T1B16 and the `POST` returns `404`, so the key-set assertion has no body to read. The repo-wide half is an absence assertion that passes on the first run — verify it the T1A10 way by renaming `normalized_form` to `lemma_form` in `dtos/imports.py`, confirming an `AssertionError` that names the file and the matched token, then reverting. Without that step the guard is indistinguishable from one whose file walk silently matched nothing. **Amended: the repo-wide half is AST-based, not a grep** — identifiers and non-docstring literals for Python, every key and string value for `import.v1.json` and for the served OpenAPI document. A grep forbade the word inside the sentence explaining why the word is forbidden and forced a cut-1a docstring to be reworded for no benefit; this now matches the T1A10 domain isolation guard, which was AST-based for exactly the same reason. See the AC-002-10 rationale in `spec.md` before changing it back.
- [x] T1B21 `[REFACTOR]` Align `api/dtos/imports.py` field order/docstrings with `dtos/health.py`. No behavior change.
- [x] T1B22 `[DOC]` Add `docs/traceability-matrix.md` rows for REQ-002-001/-002/-003/-004/-012 (`Cumplido`); update REQ-002-006/-007/-013/-018 rows noting the 1b leg (`En progreso`, "complete at cut 2"). Re-run `cd apps/api && uv run pytest tests/unit/test_traceability.py -q`.

## Cut 1c — visible import (observable, ~525 lines)

- [x] T1C01 `[TEST]` `apps/web/src/api/imports.ts` posts multipart and parses a typed `ImportResult` in `apps/web/tests/api/imports.test.ts`. Expects Vitest to fail the file at transform time with `Failed to resolve import "../../src/api/imports"` — the module does not exist, so zero assertions run. That is the correct RED: a resolution error can only mean absent production code, never a wrong assertion.
- [x] T1C02 `[IMPL]` Create `apps/web/src/api/imports.ts` + `apps/web/src/types/imports.ts` mirroring `client.ts`/`health.ts`. Per the T1B13 resolution, type the cut-1b result with **no `id` member at all** — not `id: number | null`. Cut 2 widens the type by adding `id: number`; until then the UI has no null id to branch on, so no `id == null` guard may be written in this cut.
- [x] T1C03 `[TEST]` `ImportForm` is keyboard-navigable with an accessible label and shows a perceptible "importando…" state while in flight (discharges Art. IX.6 per Amendment 1/CONTRA-1) in `apps/web/tests/components/ImportForm.test.tsx`. Expects `Failed to resolve import "../../src/components/ImportForm"` — the component file does not exist, so the render never happens and no query can be mis-targeted.
- [x] T1C04 `[IMPL]` Create `apps/web/src/components/ImportForm.tsx`.
- [x] T1C05 `[TEST]` Zero state renders an explicit "0 unique forms" message, not an error, for `distinct_form_count: 0` (AC-002-17) in `apps/web/tests/components/FrequencyTable.test.tsx`. Expects `Failed to resolve import "../../src/components/FrequencyTable"` — the component does not exist yet, so the zero-state branch cannot be confused with an unrendered error branch.
- [x] T1C06 `[IMPL]` Create `apps/web/src/components/FrequencyTable.tsx` with the zero-state branch.
- [x] T1C07 `[TEST]` A mocked non-alphabetical response renders DOM rows in the exact received order; a `normalized_form: "strasse"` / `display_form: "Straße"` row renders `Straße` verbatim, not re-derived; column headers are accessible and frequency is not colour-only (AC-002-19, Art. IX.1–4) in `apps/web/tests/components/FrequencyTable.test.tsx`. `FrequencyTable.tsx` already exists here (T1C06), so this is **not** a resolution error: expect a Vitest `AssertionError` from `expect(rowTexts).toEqual(receivedOrder)` reporting the rendered array reordered alphabetically, and a second from `expect(cell).toHaveTextContent("Straße")` receiving `strasse`. Those two are the proof the behavior is genuinely missing rather than mis-wired — the component renders and is queryable, it simply renders the wrong values, which is the exact defect AC-002-19 forbids.
- [x] T1C08 `[IMPL]` Confirm `FrequencyTable.tsx` performs zero `.sort(`/`toLowerCase(`/`localeCompare(`/`normalize(` calls; render `data.forms` as received.
- [x] T1C09 `[TEST]` Pinned-manifest contract test (design §11): `IMPORT_FEATURE_MODULES` is non-empty, every entry exists on disk, none matches the forbidden patterns, and every `/[Ii]mport|[Ff]requenc/`-named file under `apps/web/src/` appears in the manifest, in `apps/web/tests/contracts/no-linguistic-rules.test.ts`. Expects a Vitest `AssertionError` from the on-disk existence assertion, **not** a resolution error: `ImportForm.tsx`, `FrequencyTable.tsx`, `api/imports.ts` and `types/imports.ts` already exist by T1C02–T1C06, so the failure names `src/pages/ImportPage.tsx` — created later, in T1C11 — as missing. That is the correct RED because it is the one failure a stale manifest would hide; a forbidden-pattern-only RED would pass vacuously over a manifest that had silently shrunk to zero live entries. The manifest is cut-scoped and therefore does **not** list `DeleteImportButton.tsx`, which cut 3 creates in T309; listing a future module would make the on-disk assertion unsatisfiable inside a cut that must ship independently. Assertion 3 (every feature-named file appears in the manifest) is what stops cut 3 from forgetting to append it. Resolved — see design §11.
- [x] T1C10 `[IMPL]` Create the manifest test file per design §11.
- [x] T1C11 `[IMPL]` Create `apps/web/src/pages/ImportPage.tsx` composing `ImportForm` + `FrequencyTable`, wired to `api/imports.ts`.
- [x] T1C12 `[E2E]` Playwright: upload a synthetic public-domain `.txt` fixture → frequency table becomes visible, in `apps/web/e2e/import.spec.ts`. Expects a Playwright `TimeoutError` from `expect(page.getByRole("table")).toBeVisible()` — the route `ImportPage.tsx` is not mounted yet, so the locator resolves to zero elements for the full timeout. That is the correct RED: a timeout on a role-based locator means the UI never rendered, whereas a strict-mode violation or a wrong-text mismatch would mean it rendered and is merely mis-wired. Also the CORS-`POST` backstop (design §14.1) — a real browser issues the real preflight, so a `allow_methods` regression surfaces here as a failed network request rather than a missing element.
- [x] T1C13 `[E2E]` Add a synthetic or public-domain fixture under `apps/web/e2e/fixtures/` for T1C12 (Art. IV.1–2, H6); one-line provenance comment. Fixture text MUST be authored for this repo or taken from a public-domain source and MUST resemble no copyrighted series.
- [x] T1C14 `[TEST]` **Amended by remediation work units — see contradiction notes 5 and 6.** Add `apps/web/tests/contracts/no-lemma-naming.test.ts`, closing AC-002-10's UI half with a genuine TypeScript AST walk (the `typescript` package's own compiler API — already an `apps/web` devDependency, no new dependency added), unified with the backend leg's AST criterion instead of the plain text search cut 1c originally shipped. Checks identifiers and non-comment string literals (including JSX text and template literals) across `apps/web/src/**/*.{ts,tsx}`; `//`/block comments never reach the TS AST, so they are exempt by construction, mirroring the backend leg's docstring exemption. Absence assertion — it passes on the first run over correct UI copy, which proves nothing. **Two-legged mutation check, both required:** (1) temporarily set a `FrequencyTable.tsx` column header to `Lemma`, confirmed `AssertionError: lemma naming leaked into the frontend sources: src/components/FrequencyTable.tsx:31 JSX text "Lemma"`, reverted, confirmed green; (2) added a real code comment `// a form is not a lemma and not a lexeme` to `FrequencyTable.tsx`, confirmed the new guard stayed GREEN while the (now-removed) old plain-text guard in `test_no_lemma_naming.py` failed with `AssertionError: lemma naming leaked into the frontend sources: components/FrequencyTable.tsx:14 'lemma'` — proof the comment exemption works and the plain-text pathology is gone. Reverted. Also added a non-vacuity/mutation-resistance test asserting the glob reaches the expected frontend files, which fails (not silently passes) if the walk stops reaching them. The former frontend leg in `apps/api/tests/unit/test_no_lemma_naming.py` (`test_the_scan_reaches_the_shipped_frontend_sources`, `test_frontend_sources_contain_no_lemma_naming`) is removed; the backend leg is unchanged.
- [x] T1C15 `[DOC]` Add `docs/traceability-matrix.md` row for REQ-002-014 (`Cumplido`); update REQ-002-007 noting the frontend leg (`En progreso`, "complete at cut 2"). Re-run `cd apps/api && uv run pytest tests/unit/test_traceability.py -q`.

## Cut 2 — persistence (observable, ~490 lines)

- [x] T201 `[TEST]` `alembic upgrade head` / `downgrade -1` both exit 0; upgrade creates `book`+`occurrence`; downgrade removes both and returns to the empty-schema baseline (AC-002-11, H3) in `tests/integration/test_alembic_0002.py`. Expects an `AssertionError` on the table-existence check, not a command error: with no `0002` revision on disk `alembic upgrade head` legitimately exits `0` at `0001_baseline`, so the run succeeds and `assert "book" in inspector.get_table_names()` fails on a schema that has neither table. That is the correct RED — the migration runner is proven working, so the only thing missing is the revision itself.
- [x] T202 `[MIGRATION]` Create `migrations/versions/0002_book_occurrence.py` (`down_revision="0001_baseline"`) — `book`(id, language, content_hash, import_status, token_count, created_at), `occurrence`(id, book_id FK, raw_text, normalized_text, position, pos), covering index `ix_occurrence_book_norm_raw`, non-unique `ix_book_content_hash`. No `(book_id, position)` unique index (design §6.1 rationale); no new column for `display_form` (AC-002-24).
- [x] T203 `[IMPL]` Create `infrastructure/persistence/models.py` (`Book`, `Occurrence` mapped classes).
- [x] T204 `[TEST]` `SqlAlchemyBookRepository.create()` uses a **batched Core `insert()`** (`_INSERT_BATCH = 10_000`), never `Session.add_all()` — asserted via SQL-echo/statement-count capture, in `tests/integration/test_book_repository.py`. Expects `ModuleNotFoundError: No module named 'wheel_vocabulary.infrastructure.persistence.book_repository'` at collection — the adapter does not exist, so no accidental ORM path can satisfy the statement-count assertion.
- [x] T205 `[TEST]` Every persisted `Occurrence.pos is None`; `raw_text`/`normalized_text` are separate values (e.g. `Straße`/`strasse`) (AC-002-14) in `tests/integration/test_occurrence_pos.py`. Same `ModuleNotFoundError` RED as T204 — with no repository nothing is written, so the "two columns stay distinct" assertion has no row that could satisfy it by coincidence.
- [x] T206 `[TEST]` Two uploads of identical bytes → equal `content_hash`, matching an independently computed SHA-256 hex digest; one-byte-different files → different hashes (AC-002-13) in `tests/integration/test_book_repository.py`. Same `ModuleNotFoundError` RED as T204. Note the test computes the expected digest independently with `hashlib`, so once the module exists the failure mode shifts to an `AssertionError` comparing two hex strings — never a tautology against the implementation's own hash.
- [x] T207 `[TEST]` `frequency_pairs()` returns `None` for an unknown id, `[]` for an empty import, and the same list from a **new session** against the same database (AC-002-12) in `tests/integration/test_book_repository.py`. Same `ModuleNotFoundError` RED as T204. The `None`-vs-`[]` distinction is what makes it non-vacuous: a stub returning `[]` for both would pass a weaker test and still break the 404 path.
- [x] T208 `[IMPL]` Create `infrastructure/persistence/book_repository.py::SqlAlchemyBookRepository` — `create()` (Core batched insert), `frequency_pairs()`. `delete()` is added in cut 3. **Amended by remediation work unit — see contradiction note 8.** The original text also prescribed `exists()`, which shipped with the rest of cut 2 despite having no caller anywhere in `src/`; removed from the prescribed method list.
- [x] T209 `[IMPL]` Wire `ImportText`'s persistence branch (calls `BookRepository.create()`, 201 body now carries a real `id` for the first time — the **additive** completion of the T1B13 resolution: cut 1b omitted the field, so adding it here introduces a new property rather than changing the meaning of an existing one) and add `ReadImport` use case (`frequency_pairs` → `domain.frequency.build_table()`).
- [x] T210 `[REFACTOR]` Extract the streaming SHA-256 helper (already incremental per design §8) into a shared function used by `ImportText` and the T-BENCH fixture generator (T216).
- [x] T211 `[TEST]` `GET /api/v1/imports/{id}` returns the ordered list with `distinct_form_count`+`total_token_count`, diacritic-insensitive order (AC-002-09), and `Σfrequency == total_token_count` (AC-002-08 full closure), in `tests/api/test_imports.py`. Expects `404` from Starlette's router because `GET /api/v1/imports/{id}` is not registered — distinguishable from the domain-level `404 IMPORT_NOT_FOUND` by its body, which carries FastAPI's bare `{"detail": "Not Found"}` instead of the `{"error": {"code": ...}}` envelope. Assert on that body shape, not the status alone, or a wired route returning a spurious `IMPORT_NOT_FOUND` would look identical.
- [x] T212 `[IMPL]` Create the `GET /api/v1/imports/{id}` route + response DTO; update `api/schemas/import.v1.json` to the closed shape by **adding** the `id` property and listing it in `required`. Purely additive over the 1b schema, which omitted `id` rather than nulling it (T1B13 resolution) — no existing property changes type or meaning, so `X-Schema-Version` stays `1`.
- [x] T213 `[TEST]` Closing leg of AC-002-18: a persistence-layer failure during `ImportText.create` and a `ReadImport` 404 lookup both log only `code=<CODE> import_id=<id|->`, never raw text, in `tests/integration/test_book_repository.py`. Expects an `AssertionError` from `assert any(r.getMessage().startswith("code=") for r in caplog.records)` finding zero records — before T214 the persistence-failure and 404 paths emit nothing at all. That is the correct RED: the failure is an empty capture, which can only mean the logging call is absent, not that it logged the wrong thing.
- [x] T214 `[IMPL]` Extend the T1B19 logger to the persistence-failure and 404 paths.
- [x] T215 `[TEST]` **Amended by maintainer decision this session — see contradiction note 7.** `T-BENCH`, in `tests/integration/test_import_bench.py`: a generated synthetic corpus at the 4 MiB ceiling is imported and read back on every default CI run. Only DETERMINISTIC invariants fail the default build — response row count self-consistency (`len(forms) == distinct_form_count`), a sane response-body-size range, and `Σfrequency == total_token_count` on both the `POST` and `GET` responses. Import wall time, `GET` total latency, and the isolated aggregation segment (`BookRepository.frequency_pairs()` + `domain.frequency.build_table()`, timed as one span) are measured and printed in the test output; the aggregation segment is compared against the design §3.5 250 ms p95 trigger and the comparison is reported, but a breach does not fail this run — shared CI runners produce intermittent red on second-scale wall-clock budgets with no defect behind it, and design §3.5's trigger is a decision signal, not a build gate. A `WHEEL_BENCH_STRICT=1` env var (documented via the `bench` pytest marker registered in `pyproject.toml`) additionally asserts the §3.3/§3.4.5 wall-clock budgets, for use on known, calibrated hardware — not the default CI job. Fixture generated in-test by `tests/integration/_bench_corpus.py::generate_synthetic_corpus`, never committed (Art. IV.1–2, H6, T216). Expected RED: `ModuleNotFoundError` on the in-test generator helper (T216) at collection; once that exists, the RED becomes an `AssertionError` on the `Σfrequency == total_token_count`/row-count-consistency invariants until T209/T212's persistence and `GET` wiring exist — a genuinely wired, non-mocked exercise of the persisted path, or the invariants would measure nothing. Observed exactly as stated.
- [x] T216 `[IMPL]` Implement the in-test synthetic corpus generator (English-prose-like token distribution) and wire the benchmark assertions. Test-infrastructure only — no `wheel_vocabulary` source change.
- [x] T217 `[TEST]` Closing legs of two structural guards: AC-002-10's persisted-column leg (`persistence/models.py` column names contain no `lemma|lemas|lexeme|lexema`) extends `test_no_lemma_naming.py`; hook H8 (`deleted_at|is_deleted|tombstone` = 0 across the revision and models) in `tests/unit/test_no_soft_delete.py`. Written now because `Book`/`Occurrence` first exist here, ahead of cut 3's `DELETE`, so it stays green through cut 3. Both legs are absence assertions and both pass on the first run — verify RED the T1A10 way, twice: rename `Occurrence.normalized_text` to `lemma_text` and confirm the H1 leg raises `AssertionError` naming `persistence/models.py`; add a `deleted_at` column to the `0002` revision and confirm the H8 leg raises `AssertionError` naming the revision file. Revert both. A guard that has never been seen failing is not evidence that soft delete is absent — it is only evidence that the file walk ran.
- [x] T218 `[DOC]` Add `docs/traceability-matrix.md` rows for REQ-002-008/-009/-010 (`Cumplido`); **flip REQ-002-006/-007/-013/-018 to `Cumplido`** — spanning requirements are complete at this cut per spec §1.2, not before. Re-run `cd apps/api && uv run pytest tests/unit/test_traceability.py -q`.

## Cut 3 — deletion (observable, ~330 lines)

- [ ] T301 `[TEST]` `DELETE /api/v1/imports/{id}` on an import with occurrences → 204; subsequent `GET` → 404 `IMPORT_NOT_FOUND`; zero `Occurrence` rows remain for that `book_id` (AC-002-15) in `tests/integration/test_delete_import.py`. Expects `404` from Starlette's router — the `DELETE` route is unregistered (T304), so `assert response.status_code == 204` fails on `404` with FastAPI's bare `{"detail": "Not Found"}` body rather than the `IMPORT_NOT_FOUND` envelope. Asserting on that body shape is what separates "route absent" from "route present and wrongly reporting the import missing".
- [ ] T302 `[TEST]` Deletion issues **two explicit `DELETE` statements in one transaction** (`occurrence` then `book`) and does **not** rely on `ON DELETE CASCADE` — proven by asserting zero orphan rows with SQLite's default `PRAGMA foreign_keys = OFF` left unset, in `tests/integration/test_delete_import.py`. Same router-`404` RED as T301. Its lasting value is the failure mode *after* the route exists: with the pragma left off, an implementation that leans on the FK declaration alone leaves the child rows behind, so this test fails with `AssertionError: 3 != 0` on the orphan count — the exact defect a cascade-based "fix" would introduce and that T301 alone would not catch.
- [ ] T303 `[TEST]` Deleting an unknown or already-deleted `id` → 404 `IMPORT_NOT_FOUND` in `tests/integration/test_delete_import.py`. Same router-`404` RED as T301, and it is only meaningful because it asserts the error **body** — the status alone is accidentally correct before the route exists, which is precisely the trap that makes a status-only assertion a false green here.
- [ ] T304 `[IMPL]` Implement `SqlAlchemyBookRepository.delete()` (explicit two-statement transaction, design §6.2); wire `application/imports/use_cases.py::DeleteImport` + `api/routes/imports.py` `DELETE` route + `api/dependencies.py::get_delete_import`.
- [ ] T305 `[TEST]` CORS preflight for `DELETE`: `OPTIONS /api/v1/imports/{id}` with explicit `Origin` + `Access-Control-Request-Method: DELETE` → 200, `access-control-allow-methods` contains `DELETE`, in `tests/api/test_imports_cors.py`. Expects `assert response.status_code == 200` to fail on `400` with Starlette's `Disallowed CORS method` body, because `allow_methods` is still `["GET", "POST"]` after cut 1b. Same concrete failure mode as T1B17, and it proves the middleware is reached and refusing rather than the route being absent.
- [ ] T306 `[IMPL]` Extend `main.py:36` to `allow_methods=["GET", "POST", "DELETE"]`.
- [ ] T307 `[REFACTOR]` Confirm `allow_headers=[]` is unchanged (multipart's `Content-Type` is Starlette-safelisted; `DELETE` sends no body) — add a one-line comment referencing design §14.1 so it is not "fixed" speculatively (Art. VII.6).
- [ ] T308 `[TEST]` `DeleteImportButton` requires explicit confirmation: one activation shows an accessibly-named confirmation control and issues no request; confirming issues exactly one `DELETE`; cancelling issues none (AC-002-16) in `apps/web/tests/components/DeleteImportButton.test.tsx`. Expects `Failed to resolve import "../../src/components/DeleteImportButton"` — the component does not exist, so no render occurs and the "zero requests issued" assertion cannot pass vacuously for the wrong reason.
- [ ] T309 `[IMPL]` Create `apps/web/src/components/DeleteImportButton.tsx`; wire into `ImportPage.tsx`. Append `"src/components/DeleteImportButton.tsx"` to `IMPORT_FEATURE_MODULES` in `apps/web/tests/contracts/no-linguistic-rules.test.ts` (design §11, cut-scoped manifest). Skipping the append fails T1C09's assertion 3, because the new file matches `/[Ii]mport/` and would be outside the checked surface — that failure is the intended guard, not an obstacle to work around.
- [ ] T310 `[E2E]` Playwright: import → delete with confirmation → zero state renders, in `apps/web/e2e/delete-import.spec.ts`. Expects a Playwright `TimeoutError` from `page.getByRole("button", { name: /eliminar/i }).click()` — `DeleteImportButton` is not mounted into `ImportPage.tsx` until T309, so the locator never resolves. A timeout on the trigger proves the control is absent; a later failure on the zero-state assertion would instead mean the control exists and the flow is mis-wired. Also the CORS-`DELETE` backstop (design §14.1) — a real browser issues the real preflight.
- [ ] T311 `[DOC]` Add `docs/traceability-matrix.md` row for REQ-002-011 (`Cumplido`); re-run `cd apps/api && uv run pytest tests/unit/test_traceability.py -q`; run the full suite once (`cd apps/api && uv run pytest -q` and `cd apps/web && npx vitest run`) confirming the 0-warning / 99% coverage gate holds for the whole capability.

---

## Contradiction and ambiguity report (AGENTS.md §9 — surfaced, not resolved)

1. **Spec/design agreement confirmed.** Spec §1.2 and design §12.4 give identical cut names, requirement
   allocations, and line estimates (1a ~435, 1b ~660, 1c ~525, 2 ~490, 3 ~330). No divergence found
   between the two after Amendment 3's reconciliation — this task set re-derives the same file-level
   task counts independently and they are consistent with those totals.
2. **Ambiguity raised in this phase and now CLOSED by maintainer decision.** Neither artifact
   specified the exact `201` response shape for cut 1b, where `ImportText` returns a frequency table
   with **no** `Book` row yet. AC-002-01 states an `id` appears "from cut 2 onward," which left open
   whether cut 1b omits the field or returns `id: null`. **Resolution: the cut-1b `201` body omits
   `id` entirely. It is not `null`.** Reasoning of record: `null` asserts that the concept exists but
   its value is unknown, which is false at 1b — there is no `Book` row and therefore no identity to
   report; omission states the true thing, that this version of the endpoint has no import identity
   yet. It also keeps cut 2 purely additive under a versioned JSON Schema with `extra="forbid"`,
   because adding an absent property is additive whereas turning an existing `null` into a real value
   is a semantic change to a field clients already read. Consequently cut 1c's UI never branches on a
   null id, because it never sees one. Folded into T1B13 (decision), T1B04 and T212 (JSON Schema),
   T1B15 (`"id" not in body` assertion), T1B16 and T1C02 (DTO and TS type), T209 (additive completion).
   No requirement, acceptance criterion or cut allocation changed.
3. **Contradiction found in a prior phase — design §11's manifest spanning cuts — CLOSED by maintainer
   decision during cut 1c apply.** `IMPORT_FEATURE_MODULES` does not list `src/components/DeleteImportButton.tsx`
   in cut 1c; cut 3 (T309) appends it. Of the two candidate readings this artifact previously left open —
   (a) the manifest is seeded per cut and gains each new module in the cut that creates it, or (b) the
   existence assertion is scoped to entries whose owning cut has landed — **reading (a) is adopted**.
   Design §11 already states this explicitly ("The manifest is cut-scoped... `DeleteImportButton.tsx`
   is created in cut 3 (T309)") and T1C09's own task text already builds a manifest that omits the
   button and explains why: listing a future module would make the on-disk existence assertion
   (assertion 1) unsatisfiable inside a cut required to ship independently, and the reverse assertion
   (assertion 3 — every feature-named file on disk must appear in the manifest) is what stops a later
   cut from forgetting to append its own component. Assertions 1 and 3 are deliberately opposed: 1
   forbids listing what does not exist yet, 3 forbids omitting what already does; together they make a
   cut-scoped manifest safe without needing reading (b) at all. No task substance, test behaviour, or
   file list changed by closing this — the implementation in T1C09/T1C10 and T309 already matched
   reading (a); only this note was stale.
   **Which task owns the manifest constant, now confirmed and non-redundant:** T1C09 `[TEST]` is the
   task that authors `apps/web/tests/contracts/no-linguistic-rules.test.ts` in full, including the
   `IMPORT_FEATURE_MODULES` constant itself — the constant is test fixture data, not production code,
   so it belongs in the file that consumes it. T1C10 `[IMPL]` is not a second authoring step for the
   same constant; it is the pairing that satisfies the `[TEST]` → `[IMPL]` → `[REFACTOR]` convention
   (AGENTS.md §8) for a task whose "production" deliverable *is* the test file itself — T1C09 supplies
   the RED (the assertion fails because `ImportPage.tsx` does not exist yet), and T1C10 is the
   confirmation step once T1C11 creates that file and the suite goes GREEN. T1C10 performs no
   additional edit to `no-linguistic-rules.test.ts` beyond what T1C09 already wrote.
4. Design's own non-blocking open items (§17: two consecutive non-observable cuts under Art. III.3;
   CONTRA-3's provenance-column scope; CONTRA-6's cut-1b requirement move) are design-level and already
   marked "confirm at review" there — not re-litigated here, carried forward as-is.
5. **Deviation found in cut 1c, rejected by the maintainer, and CLOSED by a remediation work unit.**
   Cut 1c originally shipped T1C14's frontend leg (`apps/web/tests/unit/test_no_lemma_naming.py`
   extension, at the time) as a plain case-insensitive text search over `apps/web/src/**/*.{ts,tsx}`,
   with no comment exemption, because Python's `ast` module cannot parse TypeScript/TSX and no TS
   parser was named in the design. That was recorded as a deliberate, non-blocking deviation
   (AGENTS.md §9) pending a maintainer decision. **Why plain text was rejected:** it reintroduces the
   exact pathology cut 1b converted the backend leg away from (grep → AST) — a text search forbids the
   word "lemma" inside the sentence that explains why "lemma" is forbidden, which forced a cut-1a
   docstring to be reworded for no benefit. A frontend leg with no comment exemption guarantees the
   identical false positive the first time anyone writes an explanatory comment or code comment in
   `apps/web/src/`. **Resolution adopted:** the frontend leg moved to
   `apps/web/tests/contracts/no-lemma-naming.test.ts`, a genuine TypeScript AST walk using the
   `typescript` package's own compiler API (already an `apps/web` devDependency that powers
   `tsc --noEmit`; no new dependency added). It checks identifiers and non-comment string literals
   (including JSX text and template literal parts); `//`/block comments never reach the TS AST
   produced by `ts.createSourceFile`, so they are exempt by construction — the same mechanism Python's
   `ast` module already gave the backend leg. Verified with the same two-legged mutation protocol as
   T1A10/T1B20/T1C14: a positive leg (mutate a real column header, confirm the guard fails naming the
   file/line/token, revert) and a negative leg (add a real code comment naming the forbidden concept,
   confirm the new guard stays green while the old plain-text guard — run one last time before removal
   — failed on it). Both observed exactly as expected; see T1C14 above for the transcripts. The old
   frontend leg tests in `apps/api/tests/unit/test_no_lemma_naming.py` are removed; the backend leg is
   unchanged. **AC-002-10's own wording is now literally satisfied, not deviated from:** its text lists
   "Python sources (`apps/api/src/wheel_vocabulary/`, `apps/web/src/`), parsed as an AST" as one
   bullet — the frontend leg is now parsed as a TypeScript AST, which is the closest TypeScript
   equivalent of that wording; `spec.md` itself is unchanged because it never named a specific parser
   or dependency, only "parsed as an AST", and that is what now ships. No requirement, acceptance
   criterion, or cut allocation changed. Also fixed in this pass, found while re-verifying: the AC-10
   map row above cited a backend test function name that never existed
   (`test_backend_sources_contain_no_lemma_naming`); corrected to the real name
   (`test_no_backend_identifier_or_literal_names_a_lemma_or_a_lexeme`), pre-existing paperwork drift
   unrelated to the frontend-leg deviation.
6. **Gap found in cut 1c's remediation (note 5) and CLOSED by a follow-up remediation work unit.**
   The AST conversion in note 5 fixed the frontend guard's detection but left its defining
   property — that `//` and `/* */` comments are exempt because they never enter the tree
   `ts.createSourceFile` produces — pinned by nothing but a one-time manual mutation described in a
   code comment (`no-lemma-naming.test.ts` lines 136-145). The backend leg has never had this gap:
   `test_no_lemma_naming.py` carries `test_docstrings_and_comments_may_name_the_concept_they_rule_out`,
   `test_a_field_identifier_named_lemma_still_fails`, and
   `test_a_response_key_string_literal_named_lemma_still_fails` as permanent regression tests, not
   prose. The frontend leg was supposed to mirror that and did not — the exemption could regress
   silently (e.g. a future "improvement" to the walk using `sourceFile.getFullText()` or
   `ts.getLeadingCommentRanges`) and CI would stay green. **Resolution adopted:** `findViolations` was
   exported (no logic change) and five permanent tests were added directly to
   `apps/web/tests/contracts/no-lemma-naming.test.ts`, calling it with inline source strings: a `//`
   comment and a block comment naming the concept each produce zero violations; an identifier, a
   string literal, and a template literal naming the concept each produce exactly one violation of
   the correct `kind`, matched `text`, and reported `line`; JSX text naming the concept over a `.tsx`
   source produces exactly one `"JSX text"` violation. Because `findViolations` was already correct
   and unchanged, all five passed on first run (Approval Testing, `strict-tdd.md` §"Approval Testing
   (for refactoring existing code)"), so non-vacuity was proven by three temporary mutations instead,
   each reverted after observation: (a) disabling `report()` entirely made the four detection tests
   fail (`toHaveLength(1)` got `0`), proving they are not vacuous; (b) adding a temporary
   `ts.getLeadingCommentRanges` scan to `visit()` made both comment tests fail with the comment text
   reported as a violation, proving they would catch exactly the regression this work unit exists to
   guard against; (c) hardcoding the reported position to `0` made all four line-number assertions
   fail (`line: 1` instead of the correct line), proving the `getLineAndCharacterOfPosition` usage is
   pinned, not merely asserted. No requirement, acceptance criterion, or cut allocation changed; the
   existing two tests in the file were not weakened.
7. **Misalignment found in cut 2 apply, CLOSED by maintainer decision (binding, this session).**
   `design.md` §13's testing-strategy table describes `T-BENCH` as a test that "asserts import wall
   time (§3.3), `GET` total (§3.4.5), response row count and body size (§3.4.3), and the aggregation
   segment against the 250 ms p95 trigger (§3.5)" — read literally, that is a hard CI gate on
   second-scale wall-clock numbers. §3.5 itself, read in full, describes the same benchmark as a
   **decision trigger**: its stated purpose is to decide, later, whether a `form_frequency` aggregate
   table is warranted, by comparing the aggregation segment against 250 ms p95 — not to fail every CI
   run that happens to land on a slow shared runner. **Why it matters:** `tests/integration/` runs
   inside the `backend-test` CI job on GitHub-hosted shared runners, where absolute wall-clock budgets
   at the scale design §3.3/§3.4.5 quantifies (~4.9 s import, 0.53–1.26 s `GET`) produce intermittent
   red with no defect behind it. This project has been treating a green suite as evidence across three
   prior work units (cuts 1a–1c); a flaky test converts that evidence into a lie, and the practical
   effect of a flaky test is that people stop looking at it — which would blind the project to the one
   test carrying the §3.5 architecture trigger, exactly backwards from what a decision trigger is for.
   **Resolution adopted:** `T215`/`test_import_bench.py` fails the default build only on deterministic
   invariants (row-count self-consistency, a sane response-body-size range, `Σfrequency ==
   total_token_count`); it measures and reports import wall time, `GET` total latency, and the
   aggregation segment on every run; it compares the aggregation segment against the §3.5 250 ms
   trigger and reports the comparison without failing on a breach; and a `WHEEL_BENCH_STRICT=1`
   env-gated mode (documented by the `bench` marker in `pyproject.toml`) asserts the full §3.3/§3.4.5
   wall-clock budgets for use on known, calibrated hardware, never by default CI. §3.5's decision
   trigger therefore remains observable — every run reports the aggregation-segment-vs-250ms
   comparison in its output — without being a build gate that hardware variance can trip for free.
   **Flagged back per the apply-phase instruction, not silently resolved:** `design.md` §13's
   "asserts ... asserts" wording still reads as a hard-gate description and was NOT edited by this
   work unit — that edit needs a maintainer decision, since it is a design-artifact wording change,
   not a task-substance change. No requirement, acceptance criterion, or cut allocation changed; T216
   stays test-infrastructure only, and the fixture remains generated in-test and never committed.
8. **Deviation found in cut 2 apply, CLOSED by maintainer decision (remediation work unit, this
   session).** Cut 2 (T208) shipped `BookRepository.delete()` and `.exists()` with zero callers
   anywhere in `apps/api/src/`, discovered by the orchestrator via `git grep` after PR #23 was already
   open (16/16 checks green, not merged). Two different provenances, not one: **`delete()` contradicted
   T208's own task text**, which explicitly said "`delete()` is added in cut 3" — the implementation
   ignored its own task description. **`exists()` had no such contradiction on paper** — T208 as
   originally written prescribed it directly, so that deviation was in the task text itself, not just
   the implementation. **Why it matters beyond AGENTS.md §3 GREEN** ("No anticipar funcionalidades
   futuras. No introducir abstracciones sin uso real"): shipping a repository method ahead of the route
   that will use it pre-burns the RED of the task meant to introduce it. Cut 3's T301–T303 delete tests
   are written to expect a router-level `404` (the route does not exist) as their RED; had `delete()`
   already existed with its own tests already green, T304 would have nothing left to make fail for the
   right reason — the exact trap already hit twice during cut 1c (notes 5–6). **Resolution adopted:**
   both methods removed entirely — from the port (`application/imports/ports.py`), the adapter
   (`infrastructure/persistence/book_repository.py`), the 2 dedicated `delete()` integration tests, the
   1 dedicated `exists()` integration test, and the `exists()`/`delete()` stubs in all 3 test doubles
   (`_ExplodingRepository`, `_PlainRepository`, `_FakeRepository`). T208's task text amended above to
   drop `exists()` from its prescribed method list; the existing "`delete()` is added in cut 3" clause
   is unchanged, because it was always correct — the implementation was the thing that ignored it.
   **Cut 3's tasks (T301–T311) were checked and require no amendment:** T304 already reads "Implement
   `SqlAlchemyBookRepository.delete()`" as new work, and design §6.2's `DELETE` route flow calls
   `delete()` directly for both the `204` and `404` legs — no caller anywhere in the design ever needed
   a separate `exists()` check. Coverage held at 100.00%; backend suite 293 → 290 tests, all passing.
   No requirement, acceptance criterion, or cut allocation changed.

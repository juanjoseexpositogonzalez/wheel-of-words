# Tasks: SPEC-002 — Import a .txt and view word frequencies

> Repo `main` @ `aefbcf0`. Capability `002-text-import`. Authoritative cut allocation: spec §1.2
> (reconciled with `design.md` §12.4), five cuts, `stacked-to-main`, no `size:exception`. Not
> re-litigated here. Test runner: `cd apps/api && uv run pytest`; frontend: `cd apps/web && npx vitest run`.

**Size-budget note.** This artifact intentionally exceeds the generic ~530-word `sdd-tasks` template
budget. The orchestrator brief requires a complete 18-REQ / 24-AC → task → test map with named test
functions across five cuts under strict TDD — that deliverable cannot fit in 530 words. Reporting the
deviation explicitly rather than truncating the map (AGENTS.md §9).

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
| AC-08 | REQ-002-006 `+` | 1a→1b→**2** | T1A07, T1B15, T211 | `tests/unit/test_frequency.py::test_repeated_forms_collapse_with_frequency_and_sum`; `tests/api/test_imports.py::test_post_imports_multipart_returns_201_with_forms`; `::test_get_imports_returns_ordered_table` (sum check) |
| AC-09 | REQ-002-006 `+` | **2** | T211, T212 | `tests/api/test_imports.py::test_get_imports_diacritic_insensitive_order` |
| AC-10 | REQ-002-007 `+` | 1b→1c→**2** | T1B20, T1C14, T217 | `tests/unit/test_no_lemma_naming.py::test_backend_sources_contain_no_lemma_naming`, `::test_frontend_sources_contain_no_lemma_naming`, `::test_persisted_columns_contain_no_lemma_naming` |
| AC-11 | REQ-002-008 | 2 | T201, T202 | `tests/integration/test_alembic_0002.py::test_upgrade_and_downgrade_book_occurrence` |
| AC-12 | REQ-002-008 | 2 | T207, T208, T209 | `tests/integration/test_book_repository.py::test_frequency_pairs_survive_new_session` |
| AC-13 | REQ-002-009 | 2 | T206 | `tests/integration/test_book_repository.py::test_content_hash_matches_independent_sha256` |
| AC-14 | REQ-002-010 | 2 | T205 | `tests/integration/test_occurrence_pos.py::test_pos_is_none_and_raw_normalized_stay_distinct` |
| AC-15 | REQ-002-011 | 3 | T301, T302, T304 | `tests/integration/test_delete_import.py::test_delete_removes_book_and_occurrences_with_zero_orphans` |
| AC-16 | REQ-002-011 | 3 | T308, T309 | `apps/web/tests/components/DeleteImportButton.test.tsx::test_requires_confirmation_before_deleting` |
| AC-17 | REQ-002-012 | 1b | T1B12, T1B13 | `tests/unit/test_import_text.py::test_empty_and_whitespace_only_upload_succeeds`, `tests/api/test_imports.py::test_post_empty_file_returns_201_zero_forms` |
| AC-18 | REQ-002-013 `+` | 1b(partial)→**2**(closed) | T1B18, T1B19, T213, T214 | `tests/api/test_imports_logging.py::test_no_sentinel_in_logs_success`, `::test_no_sentinel_in_logs_decode_failure`; `tests/integration/test_book_repository.py::test_persistence_and_read_failures_log_code_only` |
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

- [ ] T1A01 `[TEST]` Parametrized tokenizer rule table for T1–T10 in `tests/unit/test_tokenizer.py::test_tokenization_rules[...]`. Expects `ModuleNotFoundError` — `domain/text/tokenizer.py` does not exist yet; that is the correct RED because no production code has been written.
- [ ] T1A02 `[IMPL]` Create `domain/models.py::Token` and `domain/text/tokenizer.py::tokenize()` per spec §2.2.
- [ ] T1A03 `[REFACTOR]` Extract the §2.1 word-char/joiner/separator Unicode-category checks into named private helpers in `tokenizer.py` for reuse by `normalizer.py`. T1A01 stays green.
- [ ] T1A04 `[TEST]` Parametrized rule table for N1–N5, adversarial code points (`ŉ`, `Straße`, `ẞ`, `İ`, `ΣΊΣΥΦΟΣ`), and the Hypothesis idempotence property (AC-002-20) in `tests/unit/test_normalizer.py`. Expects `ModuleNotFoundError` — `normalizer.py` does not exist yet.
- [ ] T1A05 `[IMPL]` Create `domain/text/normalizer.py::normalize()` implementing N1–N5 in the normative order (N4 after N2/N3, per §2.3).
- [ ] T1A06 `[REFACTOR]` Name each N1–N5 step as a private helper for direct spec-row traceability. No behavior change.
- [ ] T1A07 `[TEST]` `build_table()` D1–D3 worked examples (both AC-002-23 cases), `sort_key()` §2.4, the order-independence Hypothesis property over keys+frequencies+display forms (AC-002-21), and the non-negative-frequency Hypothesis property (AC-002-22) in `tests/unit/test_frequency.py`. Expects `ModuleNotFoundError` — `frequency.py` does not exist yet.
- [ ] T1A08 `[IMPL]` Create `domain/models.py::FormFrequency` and `domain/frequency.py::build_table()`/`sort_key()` per spec §2.4–2.5.
- [ ] T1A09 `[REFACTOR]` Extract D1 (count), D2 (max), D3 (tie-break) into named private helpers inside `build_table()` for auditability.
- [ ] T1A10 `[TEST]` Structural guard (hook H2, AC-002-06): no `fastapi|sqlalchemy|pydantic|spacy` import and no ISO-639 literal across `domain/`, run **after** T1A02/T1A05/T1A08 so the scan is meaningful (an earlier run would vacuously pass on an empty package).
- [ ] T1A11 `[DOC]` Add `docs/traceability-matrix.md` rows for REQ-002-005/-015/-016/-017 (`Cumplido`) and note the domain leg of REQ-002-006/-018 (`En progreso`, "complete at cut 2"). Re-run `cd apps/api && uv run pytest tests/unit/test_traceability.py -q`.

## Cut 1b — callable import (verificable, ~660 lines — tightest cut)

- [ ] T1B01 `[TEST]` `Settings.max_import_size_bytes` default `4194304` + `MAX_IMPORT_SIZE_BYTES` override (AC-002-03) in `tests/unit/test_settings.py`. Expects `AttributeError` — the field doesn't exist on `Settings` yet.
- [ ] T1B02 `[IMPL]` Add `max_import_size_bytes: int = 4_194_304` to `infrastructure/settings.py`.
- [ ] T1B03 `[TEST]` Five exception classes carry a `code` `ClassVar` and only safe fields (no text/offset/path) in `tests/unit/test_import_errors.py`. Expects `ModuleNotFoundError` — `application/imports/errors.py` doesn't exist.
- [ ] T1B04 `[IMPL]` Create `application/imports/errors.py` (five classes per design §9.1) + `api/errors.py` handlers (incl. `INVALID_REQUEST` for `RequestValidationError`) + `api/dtos/imports.py` error DTO (`extra="forbid"`) + `api/schemas/import.v1.json` (Draft 2020-12, `X-Schema-Version: 1`).
- [ ] T1B05 `[REFACTOR]` Align `api/errors.py` handler registration with `dtos/health.py`/`main.py` conventions. No behavior change.
- [ ] T1B06 `[TEST]` Strict UTF-8 decode rejects `0xFF` with `InvalidEncodingError`; a leading `EF BB BF` BOM is stripped and tolerated (AC-002-05) in `tests/unit/test_text_extraction.py`. Expects `ModuleNotFoundError` — `text_extraction.py` doesn't exist.
- [ ] T1B07 `[IMPL]` Create `infrastructure/text_extraction.py::PlainTextExtractor` (strict decode, BOM strip, `raise ... from None` — no offset leakage).
- [ ] T1B08 `[TEST]` `ByteStream`/`TextExtractor`/`BookRepository` `Protocol` shapes are structural (a plain stub satisfies them without inheritance) in `tests/unit/test_import_ports.py`. Expects `ModuleNotFoundError` — `ports.py` doesn't exist.
- [ ] T1B09 `[IMPL]` Create `application/imports/ports.py` with the three Protocols per design §7.2.
- [ ] T1B10 `[TEST]` Threat-matrix — filename/content-type classification: `notes.pdf`→422 `INVALID_FILE_TYPE`; `SAMPLE.TXT`→accepted; `../../etc/passwd.txt`→judged on suffix only, no path constructed; missing filename→422, in `tests/unit/test_import_text.py`. Expects `ModuleNotFoundError` — `ImportText` doesn't exist. This RED is correct because gate #1 (design §8) must reject before any byte is read.
- [ ] T1B11 `[TEST]` Threat-matrix — unbounded resource intake: 65-byte body against a 64-byte limit → `FileTooLargeError`, bounded to ≤64 KiB read; absent `Content-Length` still rejected at the streaming gate; exactly-at-limit → accepted (`>` not `>=`, AC-002-04) in `tests/unit/test_import_text.py`. Same RED reason as T1B10.
- [ ] T1B12 `[TEST]` Empty and whitespace-only uploads succeed with zero forms (AC-002-17/REQ-002-012) in `tests/unit/test_import_text.py`. Same RED reason.
- [ ] T1B13 `[IMPL]` Create `application/imports/use_cases.py::ImportText` implementing the ordered gate (design §8: ext/type → size → decode → tokenize → normalize → `build_table`), **no `BookRepository.create()` call yet** — persistence is cut 2. **Ambiguity flagged, not silently resolved:** neither spec nor design states whether the 1b response body omits `id` or returns `id: null` while unpersisted. Confirm with the maintainer before finalizing the DTO in T1B15/T1B16; do not guess.
- [ ] T1B14 `[REFACTOR]` Extract the five-gate pipeline into named private methods on `ImportText`, one per design §8 row.
- [ ] T1B15 `[TEST]` `POST /api/v1/imports` contract: multipart `.txt` → 201 with ordered `forms` carrying `normalized_form`+`display_form` (AC-002-01 success leg, AC-002-08 response half, AC-002-23/24 field presence); JSON `{"path": ...}` → 422, nothing computed (AC-002-01 rejection leg) in `tests/api/test_imports.py`. Expects `404` — the route doesn't exist yet.
- [ ] T1B16 `[IMPL]` Create `api/routes/imports.py` (thin `POST`), `api/dependencies.py` (`get_text_extractor`, `get_book_repository` stub, `get_import_text`), wire the router into `api/main.py`, extend `allow_methods=["GET", "POST"]` at `main.py:36`.
- [ ] T1B17 `[TEST]` CORS preflight for `POST`: `OPTIONS /api/v1/imports` with explicit `Origin` + `Access-Control-Request-Method: POST` → 200, `access-control-allow-methods` contains `POST`, in `tests/api/test_imports_cors.py`. Expects failure against today's `allow_methods=["GET"]` — a default `TestClient` request without these two headers would NOT catch this; this test sends both explicitly.
- [ ] T1B18 `[TEST]` Threat-matrix — sensitive-content egress: a sentinel `zzqxsentinel` import yields zero log records containing it on the success path; a decode failure logs only `code`+`import_id`, never a byte offset (AC-002-18, success + decode-failure legs) in `tests/api/test_imports_logging.py`. Expects failure — no logging call exists yet to capture, or a naive `logger.exception()` would leak the offset.
- [ ] T1B19 `[IMPL]` Wire the module logger to emit `code=<CODE> import_id=-` only; `raise ... from None` on the UTF-8 decode path; no `logger.exception()` on `UnicodeDecodeError`.
- [ ] T1B20 `[TEST]` Repo-wide lemma-naming guard, backend leg (hook H1, AC-002-10): zero `lemma|lemas|lexeme|lexema` matches across `apps/api/src/wheel_vocabulary/`; POST response keys are exactly `normalized_form`/`display_form`, in `tests/unit/test_no_lemma_naming.py`. Meaningful from the moment `routes/imports.py`/`dtos/imports.py` exist (T1B16).
- [ ] T1B21 `[REFACTOR]` Align `api/dtos/imports.py` field order/docstrings with `dtos/health.py`. No behavior change.
- [ ] T1B22 `[DOC]` Add `docs/traceability-matrix.md` rows for REQ-002-001/-002/-003/-004/-012 (`Cumplido`); update REQ-002-006/-007/-013/-018 rows noting the 1b leg (`En progreso`, "complete at cut 2"). Re-run `cd apps/api && uv run pytest tests/unit/test_traceability.py -q`.

## Cut 1c — visible import (observable, ~525 lines)

- [ ] T1C01 `[TEST]` `apps/web/src/api/imports.ts` posts multipart and parses a typed `ImportResult` in `apps/web/tests/api/imports.test.ts`. Expects module-not-found — file doesn't exist.
- [ ] T1C02 `[IMPL]` Create `apps/web/src/api/imports.ts` + `apps/web/src/types/imports.ts` mirroring `client.ts`/`health.ts`.
- [ ] T1C03 `[TEST]` `ImportForm` is keyboard-navigable with an accessible label and shows a perceptible "importando…" state while in flight (discharges Art. IX.6 per Amendment 1/CONTRA-1) in `apps/web/tests/components/ImportForm.test.tsx`. Expects component-not-found.
- [ ] T1C04 `[IMPL]` Create `apps/web/src/components/ImportForm.tsx`.
- [ ] T1C05 `[TEST]` Zero state renders an explicit "0 unique forms" message, not an error, for `distinct_form_count: 0` (AC-002-17) in `apps/web/tests/components/FrequencyTable.test.tsx`. Expects component-not-found.
- [ ] T1C06 `[IMPL]` Create `apps/web/src/components/FrequencyTable.tsx` with the zero-state branch.
- [ ] T1C07 `[TEST]` A mocked non-alphabetical response renders DOM rows in the exact received order; a `normalized_form: "strasse"` / `display_form: "Straße"` row renders `Straße` verbatim, not re-derived; column headers are accessible and frequency is not colour-only (AC-002-19, Art. IX.1–4) in `apps/web/tests/components/FrequencyTable.test.tsx`. Expects failure against a naive first draft that alphabetizes or lowercases client-side.
- [ ] T1C08 `[IMPL]` Confirm `FrequencyTable.tsx` performs zero `.sort(`/`toLowerCase(`/`localeCompare(`/`normalize(` calls; render `data.forms` as received.
- [ ] T1C09 `[TEST]` Pinned-manifest contract test (design §11): `IMPORT_FEATURE_MODULES` is non-empty, every entry exists on disk, none matches the forbidden patterns, and every `/[Ii]mport|[Ff]requenc/`-named file under `apps/web/src/` appears in the manifest, in `apps/web/tests/contracts/no-linguistic-rules.test.ts`. Expects file-not-found.
- [ ] T1C10 `[IMPL]` Create the manifest test file per design §11.
- [ ] T1C11 `[IMPL]` Create `apps/web/src/pages/ImportPage.tsx` composing `ImportForm` + `FrequencyTable`, wired to `api/imports.ts`.
- [ ] T1C12 `[TEST]` E2E: upload a synthetic public-domain `.txt` fixture → frequency table becomes visible, in `apps/web/e2e/import.spec.ts`. Expects page/route-not-found. Also the CORS-`POST` backstop (design §14.1) — a real browser issues the real preflight.
- [ ] T1C13 `[DOC]` Add a synthetic or public-domain fixture under `apps/web/e2e/fixtures/` for T1C12 (Art. IV.1–2, H6); one-line provenance comment.
- [ ] T1C14 `[TEST]` Extend `tests/unit/test_no_lemma_naming.py` with the frontend leg (`apps/web/src/`), closing AC-002-10's UI half. Expects failure only if UI copy accidentally says "lemma"/"lexeme".
- [ ] T1C15 `[DOC]` Add `docs/traceability-matrix.md` row for REQ-002-014 (`Cumplido`); update REQ-002-007 noting the frontend leg (`En progreso`, "complete at cut 2"). Re-run `cd apps/api && uv run pytest tests/unit/test_traceability.py -q`.

## Cut 2 — persistence (observable, ~490 lines)

- [ ] T201 `[TEST]` `alembic upgrade head` / `downgrade -1` both exit 0; upgrade creates `book`+`occurrence`; downgrade removes both and returns to the empty-schema baseline (AC-002-11, H3) in `tests/integration/test_alembic_0002.py`. Expects failure — revision `0002_book_occurrence` doesn't exist.
- [ ] T202 `[IMPL]` Create `migrations/versions/0002_book_occurrence.py` (`down_revision="0001_baseline"`) — `book`(id, language, content_hash, import_status, token_count, created_at), `occurrence`(id, book_id FK, raw_text, normalized_text, position, pos), covering index `ix_occurrence_book_norm_raw`, non-unique `ix_book_content_hash`. No `(book_id, position)` unique index (design §6.1 rationale); no new column for `display_form` (AC-002-24).
- [ ] T203 `[IMPL]` Create `infrastructure/persistence/models.py` (`Book`, `Occurrence` mapped classes).
- [ ] T204 `[TEST]` `SqlAlchemyBookRepository.create()` uses a **batched Core `insert()`** (`_INSERT_BATCH = 10_000`), never `Session.add_all()` — asserted via SQL-echo/statement-count capture, in `tests/integration/test_book_repository.py`. Expects failure — repository doesn't exist.
- [ ] T205 `[TEST]` Every persisted `Occurrence.pos is None`; `raw_text`/`normalized_text` are separate values (e.g. `Straße`/`strasse`) (AC-002-14) in `tests/integration/test_occurrence_pos.py`. Same RED reason as T204.
- [ ] T206 `[TEST]` Two uploads of identical bytes → equal `content_hash`, matching an independently computed SHA-256 hex digest; one-byte-different files → different hashes (AC-002-13) in `tests/integration/test_book_repository.py`. Same RED reason.
- [ ] T207 `[TEST]` `frequency_pairs()` returns `None` for an unknown id, `[]` for an empty import, and the same list from a **new session** against the same database (AC-002-12) in `tests/integration/test_book_repository.py`. Same RED reason.
- [ ] T208 `[IMPL]` Create `infrastructure/persistence/book_repository.py::SqlAlchemyBookRepository` — `create()` (Core batched insert), `exists()`, `frequency_pairs()`. `delete()` is added in cut 3.
- [ ] T209 `[IMPL]` Wire `ImportText`'s persistence branch (calls `BookRepository.create()`, 201 body now carries the real `id` — resolves T1B13's flagged ambiguity) and add `ReadImport` use case (`frequency_pairs` → `domain.frequency.build_table()`).
- [ ] T210 `[REFACTOR]` Extract the streaming SHA-256 helper (already incremental per design §8) into a shared function used by `ImportText` and the T-BENCH fixture generator (T216).
- [ ] T211 `[TEST]` `GET /api/v1/imports/{id}` returns the ordered list with `distinct_form_count`+`total_token_count`, diacritic-insensitive order (AC-002-09), and `Σfrequency == total_token_count` (AC-002-08 full closure), in `tests/api/test_imports.py`. Expects `404` — route doesn't exist.
- [ ] T212 `[IMPL]` Create the `GET /api/v1/imports/{id}` route + response DTO; update `api/schemas/import.v1.json` to the closed shape (`id` always present).
- [ ] T213 `[TEST]` Closing leg of AC-002-18: a persistence-layer failure during `ImportText.create` and a `ReadImport` 404 lookup both log only `code=<CODE> import_id=<id|->`, never raw text, in `tests/integration/test_book_repository.py`. Expects failure — no persistence-failure logging path exists before T209.
- [ ] T214 `[IMPL]` Extend the T1B19 logger to the persistence-failure and 404 paths.
- [ ] T215 `[TEST]` `T-BENCH`: a generated synthetic corpus at the 4 MiB ceiling asserts import wall time (~4.9 s budget), `GET` total latency (~0.53–1.26 s), response row count/body size, and the aggregation segment against the 250 ms p95 trigger (design §3.5), in `tests/integration/test_import_bench.py`. Fixture generated in-test, never committed (Art. IV.1–2, H6). Expects failure — generator + timing assertions don't exist; genuinely exercises the wired persistence path from T209/T212.
- [ ] T216 `[IMPL]` Implement the in-test synthetic corpus generator (English-prose-like token distribution) and wire the benchmark assertions. Test-infrastructure only — no `wheel_vocabulary` source change.
- [ ] T217 `[TEST]` Closing legs of two structural guards: AC-002-10's persisted-column leg (`persistence/models.py` column names contain no `lemma|lemas|lexeme|lexema`) extends `test_no_lemma_naming.py`; hook H8 (`deleted_at|is_deleted|tombstone` = 0 across the revision and models) in `tests/unit/test_no_soft_delete.py`. Written now because `Book`/`Occurrence` first exist here, ahead of cut 3's `DELETE`, so it stays green through cut 3.
- [ ] T218 `[DOC]` Add `docs/traceability-matrix.md` rows for REQ-002-008/-009/-010 (`Cumplido`); **flip REQ-002-006/-007/-013/-018 to `Cumplido`** — spanning requirements are complete at this cut per spec §1.2, not before. Re-run `cd apps/api && uv run pytest tests/unit/test_traceability.py -q`.

## Cut 3 — deletion (observable, ~330 lines)

- [ ] T301 `[TEST]` `DELETE /api/v1/imports/{id}` on an import with occurrences → 204; subsequent `GET` → 404 `IMPORT_NOT_FOUND`; zero `Occurrence` rows remain for that `book_id` (AC-002-15) in `tests/integration/test_delete_import.py`. Expects failure — `BookRepository.delete()` isn't implemented.
- [ ] T302 `[TEST]` Deletion issues **two explicit `DELETE` statements in one transaction** (`occurrence` then `book`) and does **not** rely on `ON DELETE CASCADE` — proven by asserting zero orphan rows with SQLite's default `PRAGMA foreign_keys = OFF` left unset, in `tests/integration/test_delete_import.py`. Expects failure for the same reason as T301; this is the specific test that would still fail if someone "fixed" deletion by relying on the FK declaration alone.
- [ ] T303 `[TEST]` Deleting an unknown or already-deleted `id` → 404 `IMPORT_NOT_FOUND` in `tests/integration/test_delete_import.py`. Same RED reason.
- [ ] T304 `[IMPL]` Implement `SqlAlchemyBookRepository.delete()` (explicit two-statement transaction, design §6.2); wire `application/imports/use_cases.py::DeleteImport` + `api/routes/imports.py` `DELETE` route + `api/dependencies.py::get_delete_import`.
- [ ] T305 `[TEST]` CORS preflight for `DELETE`: `OPTIONS /api/v1/imports/{id}` with explicit `Origin` + `Access-Control-Request-Method: DELETE` → 200, `access-control-allow-methods` contains `DELETE`, in `tests/api/test_imports_cors.py`. Expects failure against today's `allow_methods` (still `["GET", "POST"]` after cut 1b).
- [ ] T306 `[IMPL]` Extend `main.py:36` to `allow_methods=["GET", "POST", "DELETE"]`.
- [ ] T307 `[REFACTOR]` Confirm `allow_headers=[]` is unchanged (multipart's `Content-Type` is Starlette-safelisted; `DELETE` sends no body) — add a one-line comment referencing design §14.1 so it is not "fixed" speculatively (Art. VII.6).
- [ ] T308 `[TEST]` `DeleteImportButton` requires explicit confirmation: one activation shows an accessibly-named confirmation control and issues no request; confirming issues exactly one `DELETE`; cancelling issues none (AC-002-16) in `apps/web/tests/components/DeleteImportButton.test.tsx`. Expects component-not-found.
- [ ] T309 `[IMPL]` Create `apps/web/src/components/DeleteImportButton.tsx`; wire into `ImportPage.tsx`.
- [ ] T310 `[TEST]` E2E: import → delete with confirmation → zero state renders, in `apps/web/e2e/delete-import.spec.ts`. Expects flow-not-found; also the CORS-`DELETE` backstop (design §14.1).
- [ ] T311 `[DOC]` Add `docs/traceability-matrix.md` row for REQ-002-011 (`Cumplido`); re-run `cd apps/api && uv run pytest tests/unit/test_traceability.py -q`; run the full suite once (`cd apps/api && uv run pytest -q` and `cd apps/web && npx vitest run`) confirming the 0-warning / 99% coverage gate holds for the whole capability.

---

## Contradiction and ambiguity report (AGENTS.md §9 — surfaced, not resolved)

1. **Spec/design agreement confirmed.** Spec §1.2 and design §12.4 give identical cut names, requirement
   allocations, and line estimates (1a ~435, 1b ~660, 1c ~525, 2 ~490, 3 ~330). No divergence found
   between the two after Amendment 3's reconciliation — this task set re-derives the same file-level
   task counts independently and they are consistent with those totals.
2. **New ambiguity found in this phase (flagged in T1B13, not silently resolved):** neither artifact
   specifies the exact `201` response shape for cut 1b, where `ImportText` returns a frequency table
   with **no** `Book` row yet. AC-002-01 states an `id` appears "from cut 2 onward," implying its cut-1b
   presence is either omitted or `null`, but no DTO is pinned for that intermediate state. Flagged as a
   task-level blocker for whoever implements T1B15/T1B16 — confirm with the maintainer before writing
   the DTO, do not guess the shape.
3. Design's own non-blocking open items (§17: two consecutive non-observable cuts under Art. III.3;
   CONTRA-3's provenance-column scope; CONTRA-6's cut-1b requirement move) are design-level and already
   marked "confirm at review" there — not re-litigated here, carried forward as-is.

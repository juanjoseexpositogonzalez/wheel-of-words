# Tasks: SPEC-003 — Lemmatization and per-occurrence POS

Capability `003-lemmatization-pos`. Feature-branch-chain onto tracker
`feat/spec-003-annotation-tracker` (draft, no-merge). Re-cut 3→5: cut 1 would
have shipped `lemma` before the guard narrowing landed (red PR#1). Slice 1
lands the guard first.

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 250 + 300 + 400 + 400 + 400 ≈ 1,750 total |
| 400-line budget risk | High (per-slice; slice 4 tightest) |
| Chained PRs recommended | Yes |
| Suggested split | 5 slices, feature-branch-chain |
| Delivery strategy | auto-chain (user pre-approved chained PRs) |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| # | Slice | Branch | Base | Est. lines | Focused test | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|---|---|
| 1 | Pin + guard narrowing | `feat/spec-003-01-pin-guard` | tracker | ~250 | `uv run pytest tests/unit/test_no_lemma_naming.py tests/unit/test_domain_isolation.py tests/unit/test_python_pin.py` | `uv sync` install log (no source build) | Revert pin + guard files; no prod code exists yet |
| 2 | Domain + port | `feat/spec-003-02-domain-port` | slice-1 | ~300 | `uv run pytest tests/unit/test_annotation_domain.py tests/unit/test_annotation_ports.py` | N/A — pure stdlib, no I/O | Delete `domain/annotation.py`, `application/annotation/{ports,errors}.py` |
| 3 | Persistence | `feat/spec-003-03-persistence` | slice-2 | ~400 | `uv run pytest tests/integration/test_alembic_0003.py tests/integration/test_annotation_*.py` | `uv run alembic upgrade head && alembic downgrade -1` on seeded SPEC-002 DB | `alembic downgrade -1`; delete repos + migration |
| 4 | Adapter + use case | `feat/spec-003-04-adapter-usecase` | slice-3 | ~400 | `uv run pytest -m integration tests/integration/test_spacy_analyzer.py tests/unit/test_annotate_import.py` | Real `en_core_web_sm` run over a synthetic import, network disabled | Delete adapter/registry/use case; settings fields revert |
| 5 | API + frontend | `feat/spec-003-05-api-frontend` | slice-4 | ~400 | `uv run pytest tests/api/test_annotation_route.py && cd apps/web && pnpm run test` | `pnpm exec playwright test annotation.spec.ts` | Delete route/DTOs/schema; revert frontend files |

**Riskiest slice: 4 (adapter + use case).** Carries the P1 softmax self-check
(subtle numeric correctness — `softmax_normalize` flip must not silently emit
logits), the atomicity/rollback guarantee, offline-network proof, and the two
Hypothesis properties that must explicitly *reject* the naive idempotence/
token-permutation forms the domain would naively assert. If it exceeds 400
lines, split the adapter (with its self-check) from `AnnotateImport` along the
port boundary, per design §Delivery.

## Phase 1 — Pin + guard narrowing (`feat/spec-003-01-pin-guard`)

Closes: REQ-003-001, REQ-003-002 (isolation extension only), REQ-003-023, `002-text-import` REQ-002-007 delta.

- [x] 1.1 [TEST] `test_python_pin.py`: venv 3.12.x, `requires-python` excludes ≥3.14, mypy matches (REQ-003-001)
- [x] 1.2 [IMPL] Pin `pyproject.toml` (`>=3.12,<3.14`), `.python-version`, `uv python pin 3.12`, `[tool.mypy] python_version="3.12"`
- [x] 1.3 [IMPL] `uv add spacy`; then add the model as a URL-pinned dependency — `en_core_web_sm` is NOT on PyPI (404), it ships as a GitHub release asset `en_core_web_sm-3.8.0-py3-none-any.whl`. Use `uv add "en_core_web_sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl"`, NOT `spacy download` (unpinned, unreproducible, violates ADR-0005). Confirm zero source compilation in the install log (OQ-3, AC-003-01 sc.3)
- [x] 1.4 [TEST] `test_domain_isolation.py`: mutation-check proving pattern misses `thinc`/`stanza`
- [x] 1.5 [IMPL] Extend `_FORBIDDEN_IMPORT_PATTERN` to `...|thinc|stanza`
- [x] 1.6 [TEST] `test_no_lemma_naming.py` + `no-lemma-naming.test.ts`: mutation-checks proving 3 gaps — no allow-list, hardcoded migration path, book/occurrence-only tables (REQ-003-023)
- [x] 1.7 [IMPL] Both legs: exact-match `_ALLOWED_LEMMA_SYMBOLS`/`ALLOWED_LEMMA_SYMBOLS`; glob `migrations/versions/*.py`; iterate all `Base.metadata.tables` (AC-003-24)
- [x] 1.8 [TEST] Both legs: `normalized_form` renamed to lemma-shaped name still fails despite allow-list (AC-003-24 sc.2)
- [x] 1.9 [SPEC] Land `002-text-import` `REQ-002-007`/`AC-002-10` delta text
- [x] 1.10 [DOC] `docs/traceability-matrix.md`: REQ-003-001, 002 (partial), 023; REQ-002-007 (modified)

## Phase 2 — Domain + port (`feat/spec-003-02-domain-port`)

Closes: REQ-003-002, 003, 005 (shape), 006 (shape), 008 (pure rules), 010 (pure rule), 022 (no `"pos"` literal).

- [x] 2.1 [TEST] `test_annotation_domain.py`: `LinguisticAnnotation` frozen/stdlib-only, `UPOS_TAGS` 17-member, no `"pos"` literal
- [x] 2.2 [IMPL] `domain/annotation.py`: value object + `UPOS_TAGS` + `validate_confidence()`
- [x] 2.3 [TEST] `test_domain_isolation.py`: extend `_EXPECTED_MODULES` with `annotation.py`
- [x] 2.4 [TEST] `test_annotation_domain.py::resolve_effective`: correction wins, origin marker set, automatic retained (R1/R4/R5)
- [x] 2.5 [IMPL] `domain/annotation.py::resolve_effective()`
- [x] 2.6 [TEST] Hypothesis: `resolve_effective` output ∈ {automatic, corrected}, never a third value (C3); confidence validator rejects any float outside `[0,1]`
- [x] 2.7 [TEST] `test_annotation_ports.py`: fake analyzer satisfies `LinguisticAnalyzer` structurally, no NLP import; port/domain carry zero ISO-639 literals or language defaults (AC-003-03)
- [x] 2.8 [IMPL] `application/annotation/ports.py` (`LinguisticAnalyzer`, `AnalyzerIdentity`, required `language` kwarg, no default) + `application/annotation/errors.py` (`UnsupportedLanguageError`, `AnnotationFailedError`, `AnalyzerUnavailableError`)
- [x] 2.9 [DOC] `docs/traceability-matrix.md`: REQ-003-002–006, 008, 010 (partial)

## Phase 3 — Persistence (`feat/spec-003-03-persistence`)

Closes: REQ-003-006, 007, 010, 011, 014, 015.

- [x] 3.1 [TEST] `test_alembic_0003.py`: upgrade adds `lemma`/provenance/correction; downgrade returns to `0002` baseline; SPEC-002 rows survive (AC-003-16)
- [x] 3.2 [MIGRATION] `migrations/versions/0003_annotation.py` — additive, `batch_alter_table`, reversible
- [x] 3.3 [TEST] `test_annotation_models.py`: ORM mapping drives the models — `Occurrence.lemma` nullable, `AnnotationProvenance` and `ManualCorrection` mapped with their relationships and constraints. **Added by the slice-2 task audit**: task 3.1 drives the *migration*, not the ORM mapping, so without this the old 3.3 `[IMPL]` had no preceding `[TEST]` (same defect class as `errors.py` in task 2.8)
- [x] 3.4 [IMPL] `infrastructure/persistence/models.py`: `Occurrence.lemma`, `AnnotationProvenance`, `ManualCorrection`
- [x] 3.5 [TEST] `test_persisted_columns_contain_no_lemma_naming` re-run against real columns — proves slice 1's allow-list mechanism
- [x] 3.6 [TEST] `test_annotation_write_repository_isolation.py`: AST-based, write repo never imports/references `ManualCorrection` (R3)
- [x] 3.7 [TEST] `test_annotation_write_repository.py`: writes unconditionally regardless of existing correction (R2); mid-batch failure leaves zero rows touched (AC-003-15)
- [x] 3.8 [IMPL] `infrastructure/persistence/annotation_write_repository.py` — one transaction: DELETE provenance → UPDATE occurrence → INSERT provenance
- [x] 3.9 [TEST] `test_annotation_read_repository.py`: precedence-join resolves effective values + origin markers (AC-003-10); reprocessing leaves correction byte-identical (AC-003-11)
- [x] 3.10 [IMPL] `infrastructure/persistence/annotation_repository.py` — `AnnotationReadRepository`, one LEFT JOIN, `resolve_effective` applied in `__post_init__`
- [x] 3.11 [TEST] Hypothesis: seeded corrections survive generated re-annotation runs
- [x] 3.12 [DOC] `docs/traceability-matrix.md`: REQ-003-006, 007, 010, 011, 014, 015

## Phase 4 — Adapter + use case (`feat/spec-003-04-adapter-usecase`)

Closes: REQ-003-003 (adapter), 004, 005, 006, 007, 009 (backend half), 013, 016, 019, 020, 021.

- [x] 4.1 [TEST] `test_spacy_analyzer.py`: load-time self-check — score rows sum to 1.0±1e-4, decomposed `pos_` == plain `nlp(doc)` `pos_`; failure raises `ANALYZER_UNAVAILABLE` (`@pytest.mark.integration`)
- [x] 4.2 [TEST] Same file: `Doc(vocab, words=tokens)` only, never `nlp(text)`; `run/ran/running` → lemma `run`; `PROPN` unfiltered; `lemma_confidence` always `NULL` for English, never derived from `pos_confidence`
- [x] 4.3 [TEST] Same file: offline run succeeds, zero socket connections. **Scope discovery during apply (recorded per AGENTS.md §9)**: this task's other two clauses — `1.4`/`NN`/length-mismatch failing `ANNOTATION_FAILED` with zero rows written — are untestable against the REAL adapter (it cannot mathematically emit an out-of-range confidence, a non-UPOS tag, or a length mismatch) and are properly exercised in task 4.9's `test_annotate_import.py` against a stub analyzer instead, where `ANNOTATION_FAILED` is actually raised (spec §4: by the caller, never self-raised by the adapter)
- [x] 4.4 [IMPL] `infrastructure/nlp/spacy_analyzer.py::SpacyLinguisticAnalyzer` — exclude `parser`/`ner`/`senter`; flip `softmax_normalize=True`; run self-check at load. **Reordered by the slice-2 task audit**: this `[IMPL]` previously sat at 4.2, ahead of the 4.2/4.3 tests that drive most of its behavior, so the implementation was scoped wider than its driving test
- [x] 4.5 [TEST] `test_settings.py`: `annotation_language: str = "en"`, `analyzer_models: dict[str, str]`
- [x] 4.6 [IMPL] `infrastructure/settings.py`: the two fields
- [x] 4.7 [TEST] `test_analyzer_registry.py`: unsupported language raises `UnsupportedLanguageError` before pipeline load, zero writes (AC-003-03)
- [x] 4.8 [IMPL] `infrastructure/nlp/registry.py::resolve(language)` — lazy-load, cache per code
- [x] 4.9 [TEST] `test_annotate_import.py`: 6 stub failure modes (short return, `NN`, `1.4`, whitespace lemma, mid-run raise, unsupported language); full validation completes before transaction opens
- [x] 4.10 [IMPL] `application/annotation/use_cases.py::AnnotateImport` — read ordered tokens → registry.resolve → analyze whole import as one `Doc` → validate all → write
- [x] 4.11 [TEST] Hypothesis: stability under re-run with pinned model — identical `pos`/`lemma` across 2 runs, only `processed_at` differs; note that naive lemma-of-lemma idempotence is deliberately NOT asserted (AC-003-21, §5 AMB-1)
- [x] 4.12 [TEST] Hypothesis: batch-size + read-order + cross-import order independence on `position→(pos,lemma)`; note that token-permutation invariance is deliberately NOT asserted (AC-003-22, §5 AMB-3)
- [x] 4.13 [TEST] Sentinel token absent from every captured log and error body; failure carries code+id+position only (AC-003-20)
- [x] 4.14 [DOC] `docs/traceability-matrix.md`: REQ-003-003, 004, 005, 006, 007, 009 (backend), 013, 016, 019, 020, 021

## Phase 5 — API + frontend (`feat/spec-003-05-api-frontend`)

Closes: REQ-003-009, 012, 017, 018; tracker merges to `main` after this slice.

- [x] 5.1 [TEST] `test_import_contract.py` + full SPEC-002 suite re-run: `import.v1.json` byte-identical, all green unchanged (AC-003-12, 18)
- [x] 5.2 [TEST] `test_annotation_contract.py`: `annotation.v1.json` validates — provenance envelope + per-occurrence effective pos/lemma/confidences/origin
- [x] 5.3 [IMPL] `api/schemas/annotation.v1.json`, `api/dtos/annotation.py`
- [x] 5.4 [TEST] `test_annotation_route.py`: POST writes+returns; GET returns precedence-resolved occurrences with both confidence keys incl. `null`; `UNSUPPORTED_LANGUAGE` → 422, no partial write; unknown import → 404
- [x] 5.5 [IMPL] `api/routes/annotation.py`; wire `api/dependencies.py`, `api/errors.py` (3 codes), `api/main.py`
- [x] 5.6 [TEST] `AnnotationTable.test.tsx`: renders lemma/pos/confidence/origin verbatim; unmapped UPOS degrades to raw tag not blank; null vs numeric confidence distinguishable without colour
- [x] 5.7 [IMPL] `apps/web/src/types/annotation.ts`, `api/annotation.ts`, `components/AnnotationTable.tsx`
- [x] 5.8 [TEST] `no-linguistic-rules.test.ts`: extend module manifest to annotation view, zero lemmatize/tag/normalize/precedence matches
- [x] 5.9 [E2E] `apps/web/e2e/annotation.spec.ts`: import → annotate → table shows lemma/pos/confidence
- [x] 5.10 [DOC] Final `docs/traceability-matrix.md` sweep: REQ-003-009, 012, 017, 018, 023 (frontend leg); confirm all 23 rows + AC-002-10 delta row; coverage gate check (domain/application ≥90%, global ≥80%)

## Chain diagram

Stale as of corte 4: the real chain has 11 branches, not 5 — slices 2, 3 and
4 were each split into sub-slices at existing commit boundaries after
exceeding their line estimates (see "Estimation note" above).

```
main
 └─ feat/spec-003-annotation-tracker (draft, no-merge)
     └─ 01-pin-guard ✅
         └─ 02a-domain ✅ → 02b-port-errors ✅
             └─ 03a-migration-models ✅ → 03b-write-repo ✅ → 03c-read-repo ✅
                 └─ 04a-analyzer ✅ → 04b-registry ✅ → 04c-use-case ✅ → 04d-properties ✅
                     └─ 05-api-frontend ✅
```

## Estimation note — read before planning slices 4 and 5

Slices 2 and 3 were each split at existing commit boundaries after measuring
**2.6x** and **4.5x** their line estimates.

Cause: the estimates counted *source* lines while the budget counts *total*
changed lines, and this repository writes roughly **2.5 lines of test per line
of source** — AST structural guards, mutation-check documentation, Hypothesis
properties, and a 100% coverage baseline. That ratio is house style, not bloat,
and trimming tests or documentation to fit a number is explicitly forbidden
(AGENTS.md §10).

Multiply any source-line estimate by ~3.5 to get the reviewable total, and plan
commit boundaries so a slice can be split with zero rebase.

## Known debt — deferred, not forgotten

`SqlAlchemyAnnotationWriteRepository._update_occurrences` issues one `UPDATE`
per occurrence so a mid-run failure can be injected per statement (AC-003-15).
Over a full novel that is hundreds of thousands of statements in a single
transaction. Product vision §11 names performance as a risk and batching as its
mitigation, and roadmap item 10 owns performance. Revisit there, with a failure
injection mechanism that does not depend on per-row statement granularity.

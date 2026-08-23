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

- [x] 1.1 [TEST] `test_python_pin.py`: venv 3.12.x, `requires-python` excludes ≥3.13, mypy matches (REQ-003-001)
- [x] 1.2 [IMPL] Pin `pyproject.toml` (`>=3.12,<3.13`), `.python-version`, `uv python pin 3.12`, `[tool.mypy] python_version="3.12"`
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

- [ ] 2.1 [TEST] `test_annotation_domain.py`: `LinguisticAnnotation` frozen/stdlib-only, `UPOS_TAGS` 17-member, no `"pos"` literal
- [ ] 2.2 [IMPL] `domain/annotation.py`: value object + `UPOS_TAGS` + `validate_confidence()`
- [ ] 2.3 [TEST] `test_domain_isolation.py`: extend `_EXPECTED_MODULES` with `annotation.py`
- [ ] 2.4 [TEST] `test_annotation_domain.py::resolve_effective`: correction wins, origin marker set, automatic retained (R1/R4/R5)
- [ ] 2.5 [IMPL] `domain/annotation.py::resolve_effective()`
- [ ] 2.6 [TEST] Hypothesis: `resolve_effective` output ∈ {automatic, corrected}, never a third value (C3); confidence validator rejects any float outside `[0,1]`
- [ ] 2.7 [TEST] `test_annotation_ports.py`: fake analyzer satisfies `LinguisticAnalyzer` structurally, no NLP import; port/domain carry zero ISO-639 literals or language defaults (AC-003-03)
- [ ] 2.8 [IMPL] `application/annotation/ports.py` (`LinguisticAnalyzer`, `AnalyzerIdentity`, required `language` kwarg, no default) + `application/annotation/errors.py` (`UnsupportedLanguageError`, `AnnotationFailedError`, `AnalyzerUnavailableError`)
- [ ] 2.9 [DOC] `docs/traceability-matrix.md`: REQ-003-002–006, 008, 010 (partial)

## Phase 3 — Persistence (`feat/spec-003-03-persistence`)

Closes: REQ-003-006, 007, 010, 011, 014, 015.

- [ ] 3.1 [TEST] `test_alembic_0003.py`: upgrade adds `lemma`/provenance/correction; downgrade returns to `0002` baseline; SPEC-002 rows survive (AC-003-16)
- [ ] 3.2 [MIGRATION] `migrations/versions/0003_annotation.py` — additive, `batch_alter_table`, reversible
- [ ] 3.3 [IMPL] `infrastructure/persistence/models.py`: `Occurrence.lemma`, `AnnotationProvenance`, `ManualCorrection`
- [ ] 3.4 [TEST] `test_persisted_columns_contain_no_lemma_naming` re-run against real columns — proves slice 1's allow-list mechanism
- [ ] 3.5 [TEST] `test_annotation_write_repository_isolation.py`: AST-based, write repo never imports/references `ManualCorrection` (R3)
- [ ] 3.6 [TEST] `test_annotation_write_repository.py`: writes unconditionally regardless of existing correction (R2); mid-batch failure leaves zero rows touched (AC-003-15)
- [ ] 3.7 [IMPL] `infrastructure/persistence/annotation_write_repository.py` — one transaction: DELETE provenance → UPDATE occurrence → INSERT provenance
- [ ] 3.8 [TEST] `test_annotation_read_repository.py`: precedence-join resolves effective values + origin markers (AC-003-10); reprocessing leaves correction byte-identical (AC-003-11)
- [ ] 3.9 [IMPL] `infrastructure/persistence/annotation_repository.py` — `AnnotationReadRepository`, one LEFT JOIN, `resolve_effective` applied in `__post_init__`
- [ ] 3.10 [TEST] Hypothesis: seeded corrections survive generated re-annotation runs
- [ ] 3.11 [DOC] `docs/traceability-matrix.md`: REQ-003-006, 007, 010, 011, 014, 015

## Phase 4 — Adapter + use case (`feat/spec-003-04-adapter-usecase`)

Closes: REQ-003-003 (adapter), 004, 005, 006, 007, 009 (backend half), 013, 016, 019, 020, 021.

- [ ] 4.1 [TEST] `test_spacy_analyzer.py`: load-time self-check — score rows sum to 1.0±1e-4, decomposed `pos_` == plain `nlp(doc)` `pos_`; failure raises `ANALYZER_UNAVAILABLE` (`@pytest.mark.integration`)
- [ ] 4.2 [IMPL] `infrastructure/nlp/spacy_analyzer.py::SpacyLinguisticAnalyzer` — exclude `parser`/`ner`/`senter`; flip `softmax_normalize=True`; run self-check at load
- [ ] 4.3 [TEST] Same file: `Doc(vocab, words=tokens)` only, never `nlp(text)`; `run/ran/running` → lemma `run`; `PROPN` unfiltered; `lemma_confidence` always `NULL` for English, never derived from `pos_confidence`
- [ ] 4.4 [TEST] Same file: `1.4` confidence and `NN` tag fail `ANNOTATION_FAILED`, not clamped/coerced; length mismatch fails, zero rows written; offline run succeeds, zero socket connections
- [ ] 4.5 [TEST] `test_settings.py`: `annotation_language: str = "en"`, `analyzer_models: dict[str, str]`
- [ ] 4.6 [IMPL] `infrastructure/settings.py`: the two fields
- [ ] 4.7 [TEST] `test_analyzer_registry.py`: unsupported language raises `UnsupportedLanguageError` before pipeline load, zero writes (AC-003-03)
- [ ] 4.8 [IMPL] `infrastructure/nlp/registry.py::resolve(language)` — lazy-load, cache per code
- [ ] 4.9 [TEST] `test_annotate_import.py`: 6 stub failure modes (short return, `NN`, `1.4`, whitespace lemma, mid-run raise, unsupported language); full validation completes before transaction opens
- [ ] 4.10 [IMPL] `application/annotation/use_cases.py::AnnotateImport` — read ordered tokens → registry.resolve → analyze whole import as one `Doc` → validate all → write
- [ ] 4.11 [TEST] Hypothesis: stability under re-run with pinned model — identical `pos`/`lemma` across 2 runs, only `processed_at` differs; note that naive lemma-of-lemma idempotence is deliberately NOT asserted (AC-003-21, §5 AMB-1)
- [ ] 4.12 [TEST] Hypothesis: batch-size + read-order + cross-import order independence on `position→(pos,lemma)`; note that token-permutation invariance is deliberately NOT asserted (AC-003-22, §5 AMB-3)
- [ ] 4.13 [TEST] Sentinel token absent from every captured log and error body; failure carries code+id+position only (AC-003-20)
- [ ] 4.14 [DOC] `docs/traceability-matrix.md`: REQ-003-003, 004, 005, 006, 007, 009 (backend), 013, 016, 019, 020, 021

## Phase 5 — API + frontend (`feat/spec-003-05-api-frontend`)

Closes: REQ-003-009, 012, 017, 018; tracker merges to `main` after this slice.

- [ ] 5.1 [TEST] `test_import_contract.py` + full SPEC-002 suite re-run: `import.v1.json` byte-identical, all green unchanged (AC-003-12, 18)
- [ ] 5.2 [TEST] `test_annotation_contract.py`: `annotation.v1.json` validates — provenance envelope + per-occurrence effective pos/lemma/confidences/origin
- [ ] 5.3 [IMPL] `api/schemas/annotation.v1.json`, `api/dtos/annotation.py`
- [ ] 5.4 [TEST] `test_annotation_route.py`: POST writes+returns; GET returns precedence-resolved occurrences with both confidence keys incl. `null`; `UNSUPPORTED_LANGUAGE` → 422, no partial write; unknown import → 404
- [ ] 5.5 [IMPL] `api/routes/annotation.py`; wire `api/dependencies.py`, `api/errors.py` (3 codes), `api/main.py`
- [ ] 5.6 [TEST] `AnnotationTable.test.tsx`: renders lemma/pos/confidence/origin verbatim; unmapped UPOS degrades to raw tag not blank; null vs numeric confidence distinguishable without colour
- [ ] 5.7 [IMPL] `apps/web/src/types/annotation.ts`, `api/annotation.ts`, `components/AnnotationTable.tsx`
- [ ] 5.8 [TEST] `no-linguistic-rules.test.ts`: extend module manifest to annotation view, zero lemmatize/tag/normalize/precedence matches
- [ ] 5.9 [E2E] `apps/web/e2e/annotation.spec.ts`: import → annotate → table shows lemma/pos/confidence
- [ ] 5.10 [DOC] Final `docs/traceability-matrix.md` sweep: REQ-003-009, 012, 017, 018, 023 (frontend leg); confirm all 23 rows + AC-002-10 delta row; coverage gate check (domain/application ≥90%, global ≥80%)

## Chain diagram

```
main
 └─ feat/spec-003-annotation-tracker (draft, no-merge)
     └─ 01-pin-guard 📍→ 02-domain-port → 03-persistence → 04-adapter-usecase → 05-api-frontend
```

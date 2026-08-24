```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:8e4643cfc7d15eaa9bc98f46ab040bfa3b709c216138882bbebb67368ec6fcfd
verdict: fail
blockers: 1
critical_findings: 4
requirements: 17/24
scenarios: 57/64
test_command: cd apps/api && uv run pytest -q
test_exit_code: 0
test_output_hash: sha256:fceefccd78fedffe1f8194fc0be0f3bddbce31941f4a2a8734d3c470407529aa
build_command: cd apps/api && uv run mypy src/wheel_vocabulary
build_exit_code: 0
build_output_hash: sha256:b8d3eac4c0777f9e6b0550d4404e94e833d4e7dd5bb8ea2dd258b827c4ba33f1
```

## Verification Report

**Change**: `lemmatization-pos` (capability `003-lemmatization-pos`, SPEC-003, all 5 slices)
**Branch**: `feat/spec-003-05d-e2e-docs` @ `bc34620` (clean tree, nothing pushed, no PR)
**Version**: SPEC-003, governing constitution v2.0.0
**Mode**: Strict TDD

### Contract counts (counted by this verification, not inherited)

| Source | Requirements | Acceptance criteria | Scenarios |
|--------|--------------|---------------------|-----------|
| `specs/003-lemmatization-pos/spec.md` | 23 | 23 (`AC-003-13` does not exist — numbering jumps 12 → 14) | 58 |
| `specs/002-text-import/spec.md` (MODIFIED delta) | 1 (`REQ-002-007`) | 1 (`AC-002-10`) | 6 |
| **Total** | **24** | **24** | **64** |

> The launch brief stated "23 requirements, 24 ACs, 61 scenarios". Requirements and ACs
> reconcile (23 SPEC-003 requirements + the `REQ-002-007` delta; 23 SPEC-003 ACs + `AC-002-10`).
> **The scenario total does not**: the specs contain **64** `#### Scenario:` headings
> (58 + 6), not 61. Counts in this envelope are the counted values.

### Completeness

| Metric | Value |
|--------|-------|
| Tasks total | 51 (10 + 9 + 12 + 14 + 10, five phases) |
| Tasks complete (`[x]`) | 51 |
| Tasks incomplete | 0 |
| Traceability rows for `REQ-003-*` | 23 / 23 present, each exactly once |
| `AC-002-10` delta row present | Yes (`docs/traceability-matrix.md:76`) |
| Traceability rows **not** `Cumplido` | **1 — `REQ-003-002` is `En progreso`** |

### Build & Tests Execution

**Backend tests**: ✅ 452 passed, 1 warning, exit `0`

```text
$ cd apps/api && uv run pytest -q
452 passed, 1 warning in 16.93s
```

**Backend coverage**: ✅ 100% (928/928 statements, 90/90 branches, 0 missed)

```text
$ cd apps/api && uv run pytest --cov=wheel_vocabulary --cov-report=term-missing
TOTAL   928   0   90   0   100%
```

**Type check**: ✅ `mypy src/wheel_vocabulary` — Success: no issues found in 47 source files, exit `0`
**Lint**: ✅ `ruff check .` — All checks passed, exit `0`
**Format**: ✅ `ruff format --check .` — 102 files already formatted, exit `0`

**Migrations**: ✅ round-trip verified against a fresh temp database

```text
$ uv run alembic upgrade head      -> 0003_annotation (head)
$ uv run alembic downgrade -1      -> 0002_book_occurrence
$ uv run alembic upgrade head      -> 0003_annotation
```

**Frontend tests**: ✅ 56 passed / 14 files, exit `0`
**Frontend coverage**: 100% statements, 100% lines, 84.61% branch, 88% functions
**Frontend lint**: ✅ `eslint --max-warnings 0`, exit `0`
**Frontend typecheck**: ✅ `tsc --noEmit`, exit `0`
**E2E**: ✅ 4 passed (`playwright test`, real backend + real `en_core_web_sm`), exit `0`

**Coverage gates (Constitution Art. II)**: ✅ met
`domain/` 100%, `application/` 100% (≥90% required); global backend 100%, frontend 100% statements / 84.61% branch (≥80% required).

---

### Claims Audit — each independently re-executed or re-read

| # | Claim | Verdict | Evidence |
|---|-------|---------|----------|
| 1 | 452 backend, 56 frontend, 4 E2E, 100% backend coverage | ✅ **Confirmed** | All four re-run above; coverage `928/928` statements, `90/90` branches |
| 2 | `import.v1.json` byte-identical to `main`; SPEC-002 suite passes unchanged | ✅ **Confirmed** | Blob SHA identical on both refs: `git rev-parse HEAD:…/import.v1.json` == `git rev-parse main:…` == `6726750…`. File SHA-256 `def94cb6…554258`, 1852 bytes — exactly the value the matrix pins. `git diff --stat main..HEAD` shows the schema directory gained only `annotation.v1.json` |
| 3 | Naming guard narrowed, never weakened, both legs | ✅ **Confirmed** | See dedicated section below |
| 4 | `domain/` stdlib only; spaCy in exactly one file | ✅ **Confirmed (fact)** / ⚠️ **unguarded** | `domain/` imports only `unicodedata`, `collections`, `dataclasses`, `typing` + intra-domain. `grep -rn "^\s*(import\|from) (spacy\|thinc\|stanza)"` over `src/` returns only `infrastructure/nlp/spacy_analyzer.py:52-54,63-64`. **But no test enforces the "outside the adapter" half — see CRITICAL-1** |
| 5 | Confidence honest; `lemma_confidence` NULL, never derived | ✅ **Confirmed** | `softmax_normalize = True` flip at `spacy_analyzer.py:129`; `_run_self_check()` called at `:133`; both legs raise `AnalyzerUnavailableError` (`:88`, `:97`). `lemma_confidence=None` is a **literal** at `:154`, not a computation. `test_a_broken_softmax_normalization_fails_construction` multiplies scores ×10 and asserts the error — the self-check is genuinely wired. `test_lemma_confidence_is_always_null_never_derived_from_pos_confidence` asserts *all* `lemma_confidence is None` **and** *some* `pos_confidence is not None` — that second clause is what rules out mirroring. `test_every_pos_confidence_is_within_the_closed_unit_interval` runs the real model |
| 6 | Re-tokenization: `Doc(vocab, words=…)`, never `nlp(text)` | ✅ **Confirmed** | `_build_doc` at `:174`. `test_analyze_builds_the_doc_directly_and_never_calls_the_pipeline_as_text` monkeypatches `type(nlp).__call__` to raise — runtime proof, not inspection |
| 7 | Write repo never imports/references `ManualCorrection`; correction survives byte-identical | ✅ **Confirmed** | Imports only `AnnotationProvenance`, `Occurrence` (`:35`). AST guard `test_annotation_write_repository_isolation.py` checks `ast.Name`/`Attribute`/`alias`/`ImportFrom`/`Constant`, with two synthetic detector proofs. The string `ManualCorrection` appears only inside the module **docstring** (`:4`, `:8`) — exempt under the same AST criterion the project applies everywhere. Survival proven by `test_reprocessing_leaves_the_correction_byte_identical` + a Hypothesis property |
| 8 | Atomicity: mid-batch failure leaves zero rows touched | ✅ **Confirmed** | `test_a_failure_mid_transaction_leaves_zero_rows_touched` installs a `before_cursor_execute` listener that raises on the **second** `UPDATE occurrence`, then asserts the **first** occurrence's already-issued update did not survive and `provenance_count == 0`. Genuine DB-level injection |
| 9 | Offline: zero socket connections | ✅ **Confirmed** | `block_outbound_sockets` monkeypatches `socket.socket.connect` **and** `connect_ex` to raise; `test_construction_and_analysis_succeed_with_outbound_network_disabled` covers both model load and analysis |
| 10 | Privacy: no raw text in logs or error bodies | ✅ **Confirmed** | `test_annotate_import_logging.py` — sentinel `zzqxsentinel` across the success path and 4 failure paths; asserts code + import id + position only, and no traceback. Documented mutation check (raw-token log added, failure observed, reverted) |
| 11 | Hypothesis properties assert the **rejections** | ✅ **Confirmed** | `test_annotate_import_properties.py:14-25` — numbered docstring block naming both non-assertions and citing §5 AMB-1 / AMB-3, `REQ-003-020`, `REQ-003-021`. No token-permutation assertion exists anywhere in the annotation suite (`grep -rn "permut"` returns only SPEC-002's `test_frequency.py`, which is context-free and legitimate) |
| 12 | All 23 REQ-003 rows + AC-002-10 delta, accurate, none stale | ❌ **Refuted** | 23 rows + delta row all present. **`REQ-003-002` is still `En progreso`** — and its own note is *accurate*, not stale: the pending item genuinely remains untested. `REQ-003-009` **is** correctly `Cumplido`. Two lesser inaccuracies noted in WARNINGs |

---

### The naming guard (claim 3) — examined in detail, both legs

| Check | Python leg (`test_no_lemma_naming.py`) | TypeScript leg (`no-lemma-naming.test.ts`) |
|-------|----------------------------------------|--------------------------------------------|
| Still AST-based? | ✅ `ast.parse` + `ast.walk` | ✅ `ts.createSourceFile` + `forEachChild` |
| Pattern unchanged? | ✅ `lemma\|lemas\|lexeme\|lexema`, `re.IGNORECASE` | ✅ `/lemma\|lemas\|lexeme\|lexema/i` |
| Any file/directory excluded? | ✅ None — `_PACKAGE_ROOT.rglob("*.py")`, plus `migrations/versions/*.py` and **all** `Base.metadata.tables` | ✅ None — `import.meta.glob("../../src/**/*.{ts,tsx}")` |
| Allow-list = exact enumeration? | ✅ 5 names, `frozenset`, matched by `name not in …` (equality, never substring) | ✅ 4 names, `Set.has(text)` |
| Allow-list drifted since slice 1? | ✅ **No.** `git log -S'_ALLOWED_LEMMA_SYMBOLS'` returns exactly one commit: `e065730` (slice 1). `git diff e065730..HEAD` on the file shows **only an additive test** (`test_the_allow_list_is_now_exercised_by_a_genuine_persisted_lemma_column`, task 3.5) | ✅ **No.** `git diff e065730..HEAD` on the file is **empty** |
| Coverage widened, not narrowed | ✅ slice 1 fixed 3 gaps: no allow-list → allow-list; hardcoded `0002` migration → glob all; `("book","occurrence")` → all tables | ✅ same allow-list mechanism |

Allow-list contents, verified identical to slice 1's enumeration and pinned by an equality test in each leg:

- Python (5): `lemma`, `lemma_confidence`, `lemma_origin`, `automatic_lemma`, `lemmatizer`
- TypeScript (4): the same minus `lemmatizer` (a backend-only spaCy pipe-name literal) — correctly omitted

**The strongest evidence the guard was not weakened is behavioural, not textual.** Slices 3–5 each hit the guard and each time bent *their own code*, never the guard:

- Slice 4 named the adapter attribute `self.lemmatizer`, not `self._lemmatizer`, because the guard matches by exact equality (`spacy_analyzer.py:120-124`, with the reason in a comment).
- Slice 5 discovered Pydantic auto-titles `lemma` → `"Lemma"` and publishes it into `components.schemas.*`, where the OpenAPI leg exempts nothing. The fix was explicit `Field(title="lemma")` overrides — **the served document was changed to satisfy the guard, not the allow-list extended to admit `"Lemma"`.**
- Slice 5's UI header is Spanish `Lema` (single `m`), which the pattern does not match, so no allow-list entry was needed.

This is exactly the direction `REQ-003-023` and `AC-002-10`'s rationale demand.

---

### Spec Compliance Matrix — non-compliant scenarios only

57 of 64 scenarios are ✅ COMPLIANT with a covering test that passed in this run. The 7 that are not:

| Requirement | Scenario | Covering test | Result |
|-------------|----------|---------------|--------|
| REQ-003-001 | sc.3 — "The NLP dependency installs from a wheel, not a source build" | (none — `test_python_pin.py` has 3 tests covering sc.1 and sc.2 only) | ❌ UNTESTED |
| REQ-003-002 | sc.2 — "No spaCy type escapes the adapter" | (none — `test_domain_isolation.py` walks `domain/` only; `test_annotation_ports.py` inspects `ports.py`/`domain/annotation.py` only) | ❌ UNTESTED |
| REQ-003-004 | sc.3 — "SPEC-002 token boundaries survive annotation" (`state-of-the-art`, `don't`) | (none — those fixtures appear only in SPEC-002's `test_tokenizer.py`/`test_normalizer.py`, never through the annotation path) | ❌ UNTESTED |
| REQ-003-005 | sc.2 — "The same form takes different tags in different contexts" | (none — the `saw` rows in `test_annotation_read_repository.py` are hand-seeded storage fixtures, not analyzer output) | ❌ UNTESTED |
| REQ-003-009 | sc.3 — "Nothing acts on confidence in this capability" | (partial — `no-linguistic-rules.test.ts` forbids `sort`/`reverse` in the annotation modules; no filtering/threshold search, and no backend leg. `grep -rn "threshold"` over both suites: zero hits) | ⚠️ PARTIAL |
| REQ-003-013 | sc.2 — "Reprocessing changes no tokenization output" (`raw_text`/`normalized_text`/`position` byte-identical after a run) | (none — the only such assertion is in `test_alembic_0003.py`, which covers the **migration**, `AC-003-16`, not an annotation run) | ❌ UNTESTED |
| REQ-003-022 | sc.2 — "No proper-noun special case exists anywhere" | (partial — positive scenario covered on both legs; the structural zero-match search does not exist) | ⚠️ PARTIAL |

**Compliance summary**: 57/64 scenarios compliant; 5 UNTESTED, 2 PARTIAL.

Requirements fully satisfied (every scenario covered): **17/24**. Not fully satisfied:
`REQ-003-001`, `REQ-003-002`, `REQ-003-004`, `REQ-003-005`, `REQ-003-009`, `REQ-003-013`, `REQ-003-022`.

### Verification hook H10 — partially unimplemented

Spec §8 hook H10 enumerates the Hypothesis properties that must exist. Present and passing:
confidence-within-range, re-run stability, batch/read/write-order independence, seeded corrections
surviving reprocessing. **Missing**: *"annotation never mutates `raw_text`/`normalized_text`/`position`"*.
`test_annotate_import_properties.py` contains exactly four properties and none of them is this one.

Mitigating structural fact: `_update_occurrences` issues
`update(Occurrence).values(pos=…, lemma=…)` and nothing else, so the three columns are
unreachable by the write path. The guarantee holds today by construction; it is simply unguarded
against a future edit — which is precisely what `AC-003-04`/`AC-003-14` and H10 exist to prevent.

---

### Registered deviations — judged

| # | Deviation | Judgment |
|---|-----------|----------|
| 1 | `AnnotatedOccurrence.lemma` rather than `effective_lemma` | ⚠️ **Acceptable but not ideal.** Within the class it is unambiguous — `lemma` (effective), `automatic_lemma` (retained audit, R4), `lemma_origin` (R5), and the docstring explains the asymmetry. **However** the same identifier `lemma` means the *automatic* value on `Occurrence` (persistence model) and the *effective* value on `AnnotatedOccurrence` — two meanings, one name, same package, while POS keeps the unambiguous `effective_pos`/`automatic_pos`. The claimed constraint is soft: `REQ-003-023` permits any allow-list entry that "denotes a genuine lemma", and `effective_lemma` qualifies, so extending the enumeration by one reviewed name was available and legitimate. Not a spec breach; a readability debt |
| 2 | One `UPDATE` per occurrence in `_update_occurrences` | ✅ **Deferring is defensible.** No SPEC-003 requirement constrains write throughput; `product-vision §11` names performance as a risk and roadmap item 10 owns it. The granularity is load-bearing for `AC-003-15`'s injectable mid-run failure, which is a real requirement it *does* serve. One caveat: the debt is recorded in `tasks.md` §Known debt — a change artifact that moves on archive. It should be promoted to a durable backlog entry before this change is archived, or it will be forgotten exactly as the section title warns |
| 3 | Spanish UI copy (`Lema`) | ✅ **Correct.** Verified against the shipped convention: `FrequencyTable.tsx`, `ImportForm.tsx`, `DeleteImportButton.tsx`, `StatusPage` and `App.tsx` are all Spanish. Design §P6 anticipated it. `Lema` (single `m`) matches neither `lemma` nor `lemas`, so the guard needed no new entry — the code bent, not the guard |
| 4 | Explicit `Field(title=…)` overrides on the annotation DTOs | ✅ **Correct and necessary.** Pydantic auto-titles `lemma` → `"Lemma"`, FastAPI publishes it into `components.schemas.*`, and the OpenAPI leg exempts nothing. Fixing the published document rather than admitting `"Lemma"` to the allow-list is the honest resolution and strengthens the guard's non-vacuity |
| 5 | Task 4.3's two other clauses moved to task 4.9 | ✅ **Verified true; nothing dropped.** All three assertions exist in `tests/unit/test_annotate_import.py`: `test_a_short_return_fails_annotation_failed_and_writes_nothing` (length mismatch), `test_a_non_upos_tag_fails_annotation_failed_and_writes_nothing` (stub emits `NN`, `:270`), `test_an_out_of_range_confidence_fails_annotation_failed_and_writes_nothing` (stub emits `1.4`, `:282`, asserting no clamp). The stated rationale is also sound — the real adapter cannot emit a non-UPOS tag (`attribute_ruler`), an out-of-range confidence (softmax-normalised), or a length mismatch (`zip` by construction), and spec §4 assigns `ANNOTATION_FAILED` to the caller, never to the adapter |
| 6 | Slice 2's strict-TDD violation; "no further violations in 3–5" | ⚠️ **Partially refuted.** The **plans** for phases 3, 4 and 5 are clean — every `[IMPL]`/`[MIGRATION]` is preceded by a driving `[TEST]`, and the audit's two fixes (task 3.3, task 4.4 reorder) are visible in `tasks.md`. **But two slice-5 items contradict the claim**: (a) `apps/web/src/api/annotation.ts` was implemented before its test — self-caught and corrected by removing the implementation, re-observing a genuine RED (module not found), then restoring; disclosed in the apply-progress artifact, and the remediation is the right one; (b) `apps/web/src/pages/ImportPage.tsx` was modified to add the annotate trigger without appearing in **any** task and without a component test — see WARNING-4 |

### Known accepted product consequences — are they durably documented?

| Consequence | Documented? | Where |
|---|---|---|
| Confidence visible but **not actionable** until SPEC-004; UI must not imply otherwise | ✅ Behaviour correct, ⚠️ record incomplete | `AnnotationTable.tsx` has no filter, sort, threshold or action control — only `<td>` text; verified by reading the component and by `no-linguistic-rules.test.ts`'s `FORBIDDEN_METHODS`. Recorded in spec §5 AMB-2, §6 PV-2 and the `REQ-003-009` matrix row. **But AMB-2's explicit instruction — "Record it as such in the release notes" — is unsatisfied: no release-notes or changelog file exists anywhere in the repository** (`docs/` contains only `adr/`, `architecture/`, `assets/`, `constitution.md`, `decisions-log.md`, `definition-of-done.md`, `glossary.md`, `product-vision.md`, `traceability-matrix.md`) |
| No proper-noun filter; `product-vision §10` step 4 stays incomplete | ⚠️ Partially | Recorded in spec §6 PV-4 and §7 (both survive archive into `openspec/specs/`). **`docs/product-vision.md` itself carries no marker** — line 111 still reads "Excluye nombres propios" with nothing indicating it is knowingly unimplemented, and `git diff main..HEAD -- docs/` shows only `traceability-matrix.md` was touched. A reader of the product vision cannot tell |
| Punctuation-free stream ⇒ tagger scores below the model card's `0.973` | ✅ **Yes, durably and well** | `design.md` §P2 lines 108-125: names the cause (SPEC-002 T6 `_contains_letter`), states the effect ("accuracy on this stream will be measurably lower, concentrated at sentence junctions"), and records a three-option decision table with "Accept the degraded signal — **Chosen**". This is a genuine durable record. It is **not** in release notes (none exist), so it is engineering-facing only |

---

### TDD Compliance

| Check | Result | Details |
|-------|--------|---------|
| TDD Evidence reported | ⚠️ | No `TDD Cycle Evidence` table in the apply-progress artifact. Evidence is present but in prose + per-test docstrings |
| All tasks have tests | ✅ | Every `[IMPL]` in phases 1–5 has a preceding `[TEST]` in `tasks.md` |
| RED confirmed (test files exist) | ✅ | Every test file named in `tasks.md` exists on disk; verified by path |
| GREEN confirmed (tests pass) | ✅ | 452 + 56 + 4 re-executed by this verification, all green |
| Triangulation adequate | ✅ | e.g. `test_annotate_import.py` triangulates 6 distinct stub failure modes; the guard suites pin both positive and negative directions |
| Safety net for modified files | ✅ | `test_alembic_0002.py`, `test_import_contract.py`, `test_domain_isolation.py`, both guard suites were re-pinned rather than replaced |
| Mutation checks documented | ✅ **Unusually strong** | Absence assertions carry recorded RED evidence in-repo: `test_no_lemma_naming.py` documents 4 distinct mutations with their exact `AssertionError` output; the write-repo isolation guard, the reflected-column guard, and the frontend guard each document theirs |

**TDD compliance**: 6/7 checks passed. The strict-TDD module's default for a missing evidence table is CRITICAL; I am recording it as **WARNING** and stating that explicitly so the orchestrator can overrule me. Reasoning: the concern the rule protects against is "apply did not follow the protocol", and here the protocol demonstrably *was* followed — per-test mutation/RED evidence is committed in the repository (a more durable location than a report table), the one ordering slip was self-caught and remediated with genuine re-established RED, and I re-ran every test myself. What is missing is the reporting artifact, not the discipline.

### Test Layer Distribution

| Layer | Tests | Files | Tools |
|-------|-------|-------|-------|
| Unit (backend) | — | 18 `tests/unit/` | pytest, Hypothesis |
| Integration (backend) | — | 12 `tests/integration/` | pytest + SQLite + real spaCy |
| API (backend) | — | `tests/api/` | FastAPI `TestClient` |
| **Backend total** | **452** | | |
| Frontend unit + component | 56 | 14 | Vitest + Testing Library + `typescript` compiler API |
| E2E | 4 | 4 | Playwright (real backend, real model) |
| **Total** | **512** | | |

### Changed File Coverage

Backend: every file changed by this capability is at **100%** line and branch coverage — `domain/annotation.py`, `application/annotation/{ports,errors,use_cases}.py`, `infrastructure/nlp/{registry,spacy_analyzer}.py`, `infrastructure/persistence/annotation{_write,}_repository.py`, `api/routes/annotation.py`, `api/dtos/annotation.py`, `api/dependencies.py`, `infrastructure/settings.py`.

Frontend changed files:

| File | Stmts | Branch | Funcs | Rating |
|------|-------|--------|-------|--------|
| `src/types/annotation.ts` | 100% | 100% | 100% | ✅ |
| `src/api/annotation.ts` | 100% | 100% | 100% | ✅ |
| `src/components/AnnotationTable.tsx` | 100% | 75% | 100% | ⚠️ Acceptable |
| `src/pages/ImportPage.tsx` | 100% | 100% | **0%** | ⚠️ See WARNING-4 |

### Assertion Quality

Audited every test file added by this change for tautologies, orphan empty-collection assertions,
type-only assertions, ghost loops, smoke-only renders, implementation-detail coupling and
mock-heavy ratios.

**Assertion quality**: ✅ 0 CRITICAL, 0 WARNING. Assertions verify real behaviour throughout.
Absence assertions — the class most prone to vacuity — are explicitly paired with non-vacuity
tests (`test_the_scan_reaches_the_shipped_backend_sources`,
`test_the_scan_reaches_the_shipped_frontend_sources`, `test_the_write_repository_file_exists`,
`test_domain_package_scan_is_not_vacuous`) and with documented mutation checks. This is materially
better than typical.

### Quality Metrics

**Linter**: ✅ ruff clean; eslint clean at `--max-warnings 0`
**Type checker**: ✅ mypy clean (47 files); tsc clean
**Formatter**: ✅ no pending changes

---

### Issues Found

#### CRITICAL

**CRITICAL-1 — `REQ-003-002` is not satisfied and the project's own traceability says so.**
`AC-003-02` has two clauses; only the first is guarded. `tests/unit/test_domain_isolation.py`
walks `_DOMAIN_ROOT.rglob("*.py")` — `domain/` only. `tests/unit/test_annotation_ports.py`
inspects exactly two files (`application/annotation/ports.py`,
`domain/annotation.py`). **Nothing scans the whole source tree for spaCy references outside
the adapter package**, which is the second clause and spec §8 hook H2.
`docs/traceability-matrix.md:84` correctly records `En progreso` and names the reason
("Pendiente para el corte 4 …"). Slice 4 shipped the adapter; the guard and the row were never
revisited. Spec §9 makes an accurate, complete matrix a precondition for done, and `AGENTS.md` §10
repeats it. *The underlying fact is true* — I verified spaCy is imported only in
`infrastructure/nlp/spacy_analyzer.py` — but it is unenforced, which is the whole point of H2.
**This is the blocker.**

**CRITICAL-2 — `AC-003-04` scenario 3 is untested.** "SPEC-002 token boundaries survive
annotation": the AC names `state-of-the-art` and `don't` explicitly and requires that after
annotation each remains one occurrence with its original `raw_text` and `position`. Those fixtures
appear only in `tests/unit/test_tokenizer.py` and `test_normalizer.py` — SPEC-002's own suite,
never through `AnnotateImport`.

**CRITICAL-3 — `AC-003-05` scenario 2 is untested.** "The same form takes different tags in
different contexts" is the scenario that demonstrates POS is genuinely per-occurrence and
contextual — the premise of ADR-0006, §2.1 L6 and §2.2 P5. No test feeds the real adapter one
textual form in two grammatical roles. The `saw` rows in
`tests/integration/test_annotation_read_repository.py:143,183,278,375` are hand-seeded
`OccurrenceAnnotation` values proving the storage/precedence layer; they assert nothing about the
analyzer's contextual behaviour.

**CRITICAL-4 — `AC-003-14` scenario 2 is untested, and spec hook H10 is incomplete.** No test
asserts that `raw_text`, `normalized_text` and `position` are byte-identical after an annotation
run, and the H10 property *"annotation never mutates `raw_text`/`normalized_text`/`position`"*
does not exist — `test_annotate_import_properties.py` contains four properties and this is not one.
Mitigated by construction (`_update_occurrences` sets only `pos` and `lemma`), so today's risk is
low; the regression risk it was specified to prevent is unguarded.

#### WARNING

**WARNING-1 — AMB-2's release-note obligation is unmet.** Spec §5 AMB-2 closes with "**Record it
as such in the release notes**". No release-notes or changelog artifact exists in the repository.
The same gap affects the punctuation-free/`0.973` consequence, which is well recorded in
`design.md` §P2 but nowhere product-facing.

**WARNING-2 — `docs/product-vision.md` §10 step 4 carries no "knowingly unimplemented" marker.**
`REQ-003-022` says it "MUST be recorded as such". It is recorded in the spec (§6 PV-4, §7) but
`git diff main..HEAD -- docs/` touches only `traceability-matrix.md`; line 111 still reads
"Excluye nombres propios" as if delivered.

**WARNING-3 — `AC-003-09` sc.3 and `AC-003-23` sc.2 have no structural zero-match search.**
Both ACs specify a search over *backend and frontend* sources — for confidence
filtering/sorting/thresholding, and for a proper-noun filter/exclusion/special case. Neither exists;
`grep -rn "threshold"` over both suites returns zero. I verified both facts by reading
`AnnotationTable.tsx` and the backend annotation modules. Additionally, the comment at
`no-linguistic-rules.test.ts:50-52` justifies omitting a `PROPN` pattern by claiming coverage from
"the structural absence of the literal `PROPN` in this view's sources" — **that rationale is
factually wrong**: `AnnotationTable.tsx:49` contains the literal `PROPN` in `UPOS_LABELS`. The
*substance* is fine (a total 17-tag map is mandated by `REQ-003-018`, and a map entry is not a
special case), but the stated justification does not hold.

**WARNING-4 — `ImportPage.tsx` annotate wiring: unplanned and unit-untested.** The slice-5 trigger
(`handleAnnotate`, the `annotating`/`error`/`done` states, the `role="alert"` branch) lives in
`src/pages/ImportPage.tsx`, which appears in **no** task in `tasks.md` (task 5.7 lists only
`types/annotation.ts`, `api/annotation.ts`, `AnnotationTable.tsx`). There is no `ImportPage` test
file, and v8 reports **0% function coverage** for it. Only the Playwright happy path
(`e2e/annotation.spec.ts`, passing) exercises it; the error branch appears unexercised. The
apply-progress artifact does disclose the file as an out-of-design scope decision.

**WARNING-5 — `AC-003-01` scenario 3 is untested.** "installs from a wheel, not a source build" has
no automated check; `test_python_pin.py` covers scenarios 1 and 2 only. The manual observation is
recorded in the matrix. Reasonable to leave manual, but it is not a passing covering test.

**WARNING-6 — A new `DeprecationWarning` was introduced under a spec that claims a
"zero-warning `filterwarnings` gate" (§1 metadata).** `uv run pytest` emits one warning, from
`tests/integration/test_alembic_0003.py::test_upgrade_preserves_pre_existing_spec_002_rows` —
a SPEC-003 test — via sqlite3's deprecated default datetime adapter. **The gate itself was not
weakened**: `git log -S'filterwarnings'` on `pyproject.toml` returns no SPEC-003 commit, and the
three `error::` entries are intact. The gate is deliberately scoped to three classes and does not
error on `DeprecationWarning`, so the suite is green — but the suite is no longer warning-free.

**WARNING-7 — `AnnotatedOccurrence.lemma` collides semantically with `Occurrence.lemma`.**
See deviation 1. Same identifier, "effective" in the read model and "automatic" in the persistence
model, in the same package, while POS uses the unambiguous `effective_pos`/`automatic_pos`.

**WARNING-8 — Two small inaccuracies in `docs/traceability-matrix.md`.** The `REQ-003-012` row
states "449 pruebas backend en total, 424 preexistentes"; the suite is **452**. The `REQ-003-011`
and `REQ-003-014` rows are marked `Cumplido` but still carry "Pendiente para el corte 4 …" notes
that slice 4 has since closed.

#### SUGGESTION

1. The write-repo isolation guard matches the exact string `ManualCorrection`. A raw-SQL literal
   such as `text("UPDATE manual_correction …")` would slip past. No such code exists; adding the
   snake_case table name to the guard would close it cheaply.
2. `FRONTEND_EXPECTED_FILES` in `no-lemma-naming.test.ts` was not extended with the three new
   annotation modules, so a glob regression that dropped only annotation files would not trip the
   non-vacuity check.
3. `confidenceLabel` renders `String(value)`, producing a full-precision float
   (e.g. `0.9998773336410522`). Verbatim is the safe reading of AC-003-19, but it is poor UX;
   worth an explicit spec note in SPEC-004 rather than an unreviewed rounding decision later.
4. Promote the `_update_occurrences` performance debt out of `tasks.md` (a change artifact) into a
   durable backlog entry before archiving.
5. `pos_confidence` is `float(scores[index].max())` on a row validated to sum to `1.0 ± 1e-4`; a
   degenerate row could in principle exceed `1.0` by ~1e-7 and be rejected as out of range.
   Not observed; cheap to pin with a property test.

---

### Verdict

**FAIL**

One blocker and four CRITICAL findings. `REQ-003-002` is not satisfied — its second acceptance
clause (no spaCy type outside the adapter, spec hook H2) has no guard, and the project's own
traceability matrix still marks the row `En progreso`, so by spec §9 and `AGENTS.md` §10 the
capability is not done. Three further acceptance scenarios (`AC-003-04` sc.3, `AC-003-05` sc.2,
`AC-003-14` sc.2) have no covering test, and spec hook H10's "annotation never mutates
`raw_text`/`normalized_text`/`position`" property was never written.

**This is a documentation-and-coverage failure, not an implementation failure.** Every executable
gate is green — 452 + 56 + 4 tests, 100% backend coverage, clean mypy/ruff/eslint/tsc, reversible
migration — and every one of the twelve substantive claims about the *implementation* held up under
independent re-execution, including the four highest-risk ones (the softmax/`lemma_confidence`
honesty check, the `Doc(vocab, words=…)` proof, the correction-isolation AST guard, and the
cursor-level atomicity injection). The naming guard was not weakened in either leg; the allow-list
is byte-identical to slice 1's, and slices 3–5 renamed their own code rather than touch it. The
gaps are missing *guards* for facts that are currently true, plus records that were specified and
not written.

The remediation is small and additive — roughly five tests, one traceability status flip, and two
documentation records. None of it requires reworking shipped code.

**Do not open the 14 PRs on this state.** Close CRITICAL-1 through CRITICAL-4 and flip
`REQ-003-002` to `Cumplido` first; the WARNINGs can be triaged into the chain or deferred with an
explicit decision.

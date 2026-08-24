```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:9e18297837bb4c07e23aff1aee21967234cdf0e1ee035356509ceec188869124
verdict: pass_with_warnings
blockers: 0
critical_findings: 0
requirements: 24/24
scenarios: 64/64
test_command: cd apps/api && uv run pytest -q
test_exit_code: 0
test_output_hash: sha256:10fb90b73dcc6322b4b764ca78acd9172e67971793af57d770857fcacee1ccfc
build_command: cd apps/api && uv run mypy src/wheel_vocabulary
build_exit_code: 0
build_output_hash: sha256:b8d3eac4c0777f9e6b0550d4404e94e833d4e7dd5bb8ea2dd258b827c4ba33f1
```

## Verification Report — RE-VERIFICATION

**Change**: `lemmatization-pos` (capability `003-lemmatization-pos`, SPEC-003, 5 slices + remediation)
**Branch**: `feat/spec-003-06-remediation` @ `e581891` (working tree clean, nothing pushed, no PR)
**Prior verdict**: `FAIL` — 1 blocker, 4 CRITICAL, 8 WARNING, 5 SUGGESTION
**This verdict**: `PASS WITH WARNINGS` — 0 blockers, 0 CRITICAL, 1 WARNING, 3 SUGGESTION
**Mode**: Strict TDD
**Posture**: adversarial. Every claim below was re-executed or re-read against the repository. No self-report was accepted on trust.

### Contract counts (recounted by this verification)

| Source | Requirements | Acceptance criteria | Scenarios |
|--------|--------------|---------------------|-----------|
| `specs/003-lemmatization-pos/spec.md` | 23 | 23 (`AC-003-13` does not exist — numbering jumps 12 → 14) | 58 |
| `specs/002-text-import/spec.md` (MODIFIED delta) | 1 (`REQ-002-007`) | 1 (`AC-002-10`) | 6 |
| **Total** | **24** | **24** | **64** |

**Scenario count — the agent's claim is confirmed.** `58 + 6 = 64`, identical to my prior recount. The figure `61` appears exactly once in the entire repository, at `verify-report.md:32` — inside *my own prior report*, quoting the launch brief. It has never existed in any spec, task, or planning artifact. The agent's assertion is accurate.

### Completeness

| Metric | Value |
|--------|-------|
| Tasks total | 55 (51 original + 4 remediation) |
| Tasks complete (`[x]`) | 55 |
| Tasks incomplete (`[ ]`) | 0 |
| Traceability rows for `REQ-003-*` | 23 / 23 unique, each exactly once |
| `AC-002-10` delta row present | Yes (`docs/traceability-matrix.md:76`) |
| Rows marked `En progreso` | **0** |
| Rows marked `Pendiente` / `Bloqueado` | **0** |

> Status-scan note: a naive `grep` for `Pendiente` returns three hits — all false positives. Two are the legend (`:22`) and the process description (`:115`, `:118`); the third (`:93`) is the word appearing *inside prose* on a `Cumplido` row, quoting the stale note that WARNING-8 asked to be corrected. No row carries a non-`Cumplido` status.

### Build & Tests Execution — all re-run by this verification

**Backend tests**: ✅ **470 passed**, **0 warnings**, exit `0` (was 452 + 1 `DeprecationWarning`)

```text
$ cd apps/api && uv run pytest -q
470 passed in 17.63s
```

**Backend coverage**: ✅ **100%** — 928/928 statements, 90/90 branches, 0 missed, every module 100%

```text
$ cd apps/api && uv run pytest --cov=wheel_vocabulary --cov-report=term-missing
TOTAL   928   0   90   0   100%
```

**Type check**: ✅ `mypy src/wheel_vocabulary` — Success: no issues found in 47 source files, exit `0`
**Lint**: ✅ `ruff check .` — All checks passed, exit `0`
**Format**: ✅ `ruff format --check .` — 105 files already formatted, exit `0`

**Migrations**: ✅ full round-trip re-executed

```text
$ uv run alembic upgrade head    -> 0003_annotation (head)
$ uv run alembic downgrade -1    -> 0002_book_occurrence
$ uv run alembic upgrade head    -> 0003_annotation
```

**Frontend tests**: ✅ 66 passed / 15 files, exit `0` (was 56 / 14)
**Frontend coverage**: 100% statements, 100% lines, **100% functions**, **81.81% branch**
**Frontend lint**: ✅ `eslint --max-warnings 0`, exit `0`
**Frontend typecheck**: ✅ `tsc --noEmit`, exit `0`
**E2E**: ✅ 4 passed (`playwright test`, real backend + real `en_core_web_sm`), exit `0`

**Pinned schema**: ✅ unchanged
`shasum -a 256 apps/api/src/wheel_vocabulary/api/schemas/import.v1.json` → `def94cb6361531b21f382c862120914419b867b6601aa58d763d49d65a554258`, **1852 bytes** — byte-identical to the pinned value.

**Working tree**: ✅ `git status` → clean. No leftover mutation from any mutation check.

**Coverage gates (Constitution Art. II)**: ✅ met with margin
`domain/` 100%, `application/` 100% (≥90% required); backend global 100%, frontend 100% statements / 81.81% branch (≥80% required).

---

## Regression risk — frontend branch coverage drop

**Verdict: benign, confirmed, and above the floor — but the reported number is slightly wrong.**

| Claim | Observed | Judgment |
|---|---|---|
| Drop from 84.61% | 84.61% (prior report) | ✅ correct baseline |
| Now 82.6% | **81.81%** | ⚠️ self-report off by 0.79 pt |
| Above ≥80% floor | 81.81% ≥ 80% | ✅ **yes**, 1.81 pt margin |
| Cause = one defensive unreachable guard in `ImportPage.tsx` | Confirmed | ✅ |

`apps/web` exposes exactly one coverage invocation (`vitest run --coverage`); there is no second configuration that yields 82.6%. The true current figure is **81.81%**.

The cause is confirmed genuine. `ImportPage.tsx:35`:

```tsx
function handleAnnotate(): void {
  if (result === null) {
    return;
  }
```

`handleAnnotate` is bound to a button rendered **inside** `{result && ( … )}` (`:55`), so `result` cannot be `null` at call time. The guard is unreachable by construction — a defensive early return, not lost coverage. **No coverage was lost anywhere else**: statements, lines and functions are all 100%, and every other file's branch percentage is unchanged from the prior run (`AnnotationTable.tsx` 75%, `ImportForm.tsx` 57.14%, `ExportButton` 85.71% are all pre-existing).

---

## Findings claimed closed — independently audited

| # | Finding | Verdict | Evidence |
|---|---------|---------|----------|
| 1 | **BLOCKER / CRITICAL-1** — whole-package NLP isolation guard | ✅ **Genuinely closed, and strong** | See dedicated section below |
| 2 | **CRITICAL-2** — `AC-003-04` sc.3 token boundaries | ✅ **Closed** | `tests/integration/test_annotate_import_token_boundaries.py`. Runs the **real** `ImportText` → **real** `SqlAlchemyBookRepository` → **real** `AnnotateImport` → **real** read/write annotation repositories over the same DB. Only the analyzer is a deterministic stdlib fake, and the docstring justifies exactly that ("token-boundary preservation across the SPEC-002/SPEC-003 boundary, not the real model's linguistic output"). Fixtures are SPEC-002's own hardest cases: `state-of-the-art` and `don't` |
| 3 | **CRITICAL-3** — `AC-003-05` sc.2 contextual POS via the real model | ✅ **Closed — real adapter confirmed** | `test_spacy_analyzer.py:220-240`. Constructs `SpacyLinguisticAnalyzer(_MODEL_NAME)` — the **real** adapter loading the **real** `en_core_web_sm` — then calls `analyzer.analyze(["I","saw","him","yesterday"])` → asserts `[1].pos == "VERB"`, and `analyzer.analyze(["I","cut","wood","with","a","saw"])` → asserts `[5].pos == "NOUN"`. **Not** hand-seeded; the docstring explicitly contrasts itself against the seeded `saw` rows in `test_annotation_read_repository.py`. This genuinely proves ADR-0006's per-occurrence POS |
| 4 | **CRITICAL-4** — H10 property, no mutation of token fields | ✅ **Closed** | `test_annotate_import_properties.py:403` `test_property_annotation_never_mutates_raw_text_normalized_text_or_position`. Property count is now **5** (was 4), matching spec §8 hook H10's enumeration. Documented mutation check reproduces the claimed shrink |
| 5 | **CRITICAL** — `docs/release-notes.md` | ✅ **Closed — all four recorded and accurate** | 5694 bytes. (a) sub-`0.973` accuracy from the punctuation-free stream, naming SPEC-002 rule T6 as cause and stating the effect concentrates at sentence junctions (`:27-40`); (b) confidence visible but **not actionable** until SPEC-004, naming `AnnotationTable.tsx` and recording the rejected alternative (`:43-60`); (c) no proper-noun filter, tying the gap to `product-vision.md` §10 step 4 and roadmap item 6 (`:62-76`); (d) `lemma_confidence` always `NULL` for English, by design not omission, with the user-facing consequence (`:76-84`) |
| 6 | **WARNING-4** — `ImportPage.tsx` component test | ✅ **Closed** | `apps/web/tests/pages/ImportPage.test.tsx`, **7 behavioral tests**: absence of trigger before import; trigger present after import with no table; in-flight state with disabled trigger; table rendered on success; error rendered perceptibly with table never rendered; state reset on re-import; full clear on delete. 27 behavioral queries, zero smoke-only renders. Function coverage `0% → 100%` confirmed in the coverage run |
| 7 | **Scenario count** — 58+6=64, "61" never in repo | ✅ **Confirmed** | See contract counts above |
| 8 | **WARNING-2** — `product-vision.md` proper-noun marker | ✅ **Closed** | `docs/product-vision.md:111` now reads `4. Excluye nombres propios. **[Conocido, no implementado todavía]** SPEC-003` |
| 9 | **WARNING-3** — structural zero-match searches | ✅ **Closed, including the wrong rationale** | New `tests/unit/test_no_confidence_action_or_propn_filter.py` adds package-wide backend legs for both `AC-003-09` sc.3 and `AC-003-23` sc.2. Separately, the factually-wrong comment in `no-linguistic-rules.test.ts` is now corrected in place (`:52-62`), explicitly stating the prior claim "was FACTUALLY WRONG" and pointing at the real structural proof. Honest correction, not a quiet edit |
| 10 | **WARNING-5** — `AC-003-01` sc.3 (wheel, not source build) | ✅ **Closed via an honest proxy** | `test_python_pin.py::test_the_locked_resolution_carries_a_cp312_wheel_not_only_an_sdist` parses `uv.lock` and asserts `spacy`/`thinc` carry a `cp312` wheel rather than only an `sdist`. The docstring is explicit that this is a proxy ("cannot be observed from inside the test process"). Sound: a lock entry with a matching wheel is precisely what prevents `uv sync` attempting a source build |
| 11 | **WARNING-6** — `DeprecationWarning` under a zero-warning gate | ✅ **Closed** | `470 passed` with **no** warning line (was `452 passed, 1 warning`). Fixed at source in `aa3883c` by not binding a raw `datetime` through sqlite3's deprecated adapter — the gate was not loosened |
| 12 | **WARNING-8** — matrix inaccuracies | ⚠️ **Partially closed — see WARNING-1** | The stale "Pendiente para el corte 4" notes on `REQ-003-011`/`REQ-003-014` are now corrected in place with explicit `**Corrección (verify-report WARNING-8):**` markers naming the test that closed each. The test-count correction, however, reintroduced a stale number |
| 13 | **SUGGESTION-1** — snake_case `manual_correction` | ✅ **Closed** | Write-repo guard now scans for the snake_case table name; mutation-checked |
| 14 | **SUGGESTION-2** — `FRONTEND_EXPECTED_FILES` non-vacuity | ✅ **Closed** | Extended with `AnnotationTable.tsx`, `api/annotation.ts`, `types/annotation.ts`, with the reason recorded inline |
| 15 | **SUGGESTION-4** — promote `_update_occurrences` debt | ✅ **Closed durably** | `docs/decisions-log.md:50` — full row with rationale, roadmap item 10 as owner, and an explicit note that it was promoted so the debt survives archive |

---

## CRITICAL-1 (the blocker) — examined in depth

`tests/unit/test_nlp_isolation.py` (154 lines, 5 tests). **This is not vacuous.** Audited against all four criteria:

| Criterion | Finding |
|---|---|
| Whole-package scan | ✅ `_PACKAGE_ROOT.rglob("*.py")` over `src/wheel_vocabulary` — every layer, no directory excluded |
| Non-vacuity test present | ✅ `test_the_scan_reaches_the_whole_package_across_every_layer` asserts `scanned >= _EXPECTED_FILES`, a 9-file set deliberately spanning `domain/`, `application/`, `infrastructure/nlp/`, `infrastructure/persistence/` and `api/` — so a walk that collapsed to `domain/` alone (the pre-existing guard's scope) still fails |
| Allow-list correctly scoped | ✅ Exempted by **string equality** on one exact path (`label == _ALLOWED_FILE`), never a prefix. Proven by a dedicated test — `test_the_allow_list_exemption_is_applied_by_exact_path_not_a_directory_prefix` — which confirms `registry.py`, a *sibling in the same directory*, is still scanned. Plus `test_the_adapter_file_itself_does_import_spacy` guards against a stale/mistyped allow-list path silently exempting the wrong file |
| Mutation-checked | ✅ Two ways. Documented real mutation in the module docstring (`:27-35`) with the verbatim observed `AssertionError`, **and** `test_an_nlp_import_outside_the_adapter_would_be_caught`, which feeds the detector synthetic `spacy`/`thinc`/`stanza` sources so the detector's own liveness is asserted on every run, not just once by hand |

The AST criterion is correct: `ast.Import` and `ast.ImportFrom` with `level == 0`, root-package extraction via `.split(".")[0]`. Relative imports are correctly ignored (they cannot reach `spacy`).

**Is flipping `REQ-003-002` to `Cumplido` now genuinely accurate?** ✅ **Yes.** The row's second clause (spec hook H2, "no spaCy type outside the adapter") is now enforced by an executing test, not merely true by accident. I independently confirmed the underlying fact as well:

```text
$ grep -rnE '^[[:space:]]*(import|from)[[:space:]]+(spacy|thinc|stanza)\b' src/
src/wheel_vocabulary/infrastructure/nlp/spacy_analyzer.py:53,54,63,64
```

Exactly one file. `registry.py` matches a naive `grep spacy` only because it imports *our own* `SpacyLinguisticAnalyzer` class — not the library.

---

## Mutation-check audit — all five claims verified

The repository convention is that every absence assertion carries its RED evidence in the test docstring. **12 documented `MUTATION CHECK` blocks** exist across the suite. All five specifically claimed were found with output matching the claim verbatim:

| Claimed mutation | Location | Observed output in docstring | Match |
|---|---|---|---|
| `import spacy` in `use_cases.py` | `test_nlp_isolation.py:27` | `application/annotation/use_cases.py imports 'spacy' (only infrastructure/nlp/spacy_analyzer.py may)` | ✅ |
| `raw_text="MUTATION_CHECK"` in `_update_occurrences` | `test_annotate_import_properties.py:413` | `assert {383: ('MUTATION_CHECK','a_norm',0)} == {383: ('a','a_norm',0)}` — consistent with the claimed shrink to a single token | ✅ |
| `occurrence.pos === "PROPN"` in `AnnotationTable.tsx` | `no-linguistic-rules.test.ts:233` | violation at **line 72** | ✅ |
| `filter_by_confidence` stub in `annotation_repository.py` | `test_no_confidence_action_or_propn_filter.py:125` | `annotation_repository.py:51 identifier 'filter_by_confidence'` | ✅ |
| `"manual_correction"` literal in write repo | `test_annotation_write_repository_isolation.py:95` | `annotation_write_repository.py:47 string literal 'manual_correction'` | ✅ |

Each block records the revert. **`git status` is clean** — no mutation was left behind.

---

## Deferrals — judged individually

| Deferral | Judgment | Reasoning |
|---|---|---|
| **WARNING-7** — `AnnotatedOccurrence.lemma` vs `Occurrence.lemma` collision | ✅ **Accept on substance** / ⚠️ **record is not durable** | Substantively correct to defer: it is a readability debt, not a spec breach. `REQ-003-023` permits any allow-list entry denoting a genuine lemma, so renaming was *available* but never *required*, and no scenario fails because of it. **However** the deferral is recorded nowhere durable — `effective_lemma` appears in exactly one file in the repo: this verify-report, which lives under `openspec/changes/lemmatization-pos/` and moves on archive. `tasks.md §Known debt` contains only the `_update_occurrences` entry. This is the same disappearing-record failure mode as SUGGESTION-4, which the agent *did* fix correctly — the pattern simply was not applied here. Not hiding a gap; carried forward as SUGGESTION-1 below |
| **SUGGESTION-3** — confidence float precision | ✅ **Accept on substance** / ⚠️ **record is not durable** | The reasoning is right. `confidenceLabel` returns `String(value)` (`AnnotationTable.tsx:64-69`), and verbatim rendering **is** the safe `AC-003-19` reading — `REQ-003-018` forbids the frontend from duplicating linguistic rules, and an unreviewed rounding decision would be exactly the kind of presentational logic the spec pushes back to the API. Deferring to a SPEC-004 spec note is correct. But no such note exists yet in any durable artifact; the claim describes an intention, not a record. Carried forward as SUGGESTION-2 |
| **SUGGESTION-5** — `pos_confidence` > 1.0 edge | ✅ **Accept fully** | Verified the fail-safe claim directly. `domain/annotation.py:83-99`: `if not 0.0 <= value <= 1.0: raise ValueError`. It **raises**, never clamps — which is what `REQ-003-008` demands. Worst case for a degenerate softmax row is a spurious `ANNOTATION_FAILED`, never silent corruption. Not observed, and the failure direction is safe. Honest deferral |
| **`_update_occurrences`** one-UPDATE-per-occurrence | ✅ **Accept — and the record exists** | Confirmed at `docs/decisions-log.md:50`. The row names the file, the rationale (per-statement granularity is load-bearing for `AC-003-15`'s injectable mid-run failure), the risk over a full novel, and roadmap item 10 as owner — plus an explicit note that it was promoted out of `tasks.md` so it survives archive. This is exactly the handling SUGGESTION-4 asked for |

**None of the four deferrals hides a real gap.** Two of them, though, are recorded only in an artifact that will not survive archive.

---

## Nothing regressed — explicitly re-checked

| Check | Result |
|---|---|
| Naming guard not weakened (either leg) | ✅ **Confirmed, and it was strengthened** |
| `domain/` imports stdlib only | ✅ Only `dataclasses`, `unicodedata`, `collections`, `typing`, `__future__` + intra-domain |
| spaCy imported in exactly one file | ✅ `infrastructure/nlp/spacy_analyzer.py` only — and now *enforced* |
| `import.v1.json` unchanged | ✅ `def94cb6…554258`, 1852 bytes |
| All 23 REQ-003 rows + `AC-002-10` delta | ✅ Present, each exactly once |
| No row `En progreso` that is complete | ✅ Zero rows carry that status |
| No row `Cumplido` that is not | ✅ All 24 verified against passing tests |

**On the naming guard, a note about the pickaxe command.** Run unrestricted, `git log -S'_ALLOWED_LEMMA_SYMBOLS'` now returns **7** commits, not one — which looks alarming and is not. Five of the seven merely *mention* the symbol in prose (a code comment in `spacy_analyzer.py`, a docstring in `annotation_repository.py`, and three doc files); `-S` counts occurrences anywhere in the diff, including documentation. Scoped to the test tree, `git log -S'_ALLOWED_LEMMA_SYMBOLS' -- apps/api/tests/` returns **2**: `e065730` (slice 1, the original) and `57ad111`, which introduced a *separate* allow-list for the new `annotation.v1.json` contract test — additive, not a relaxation.

The decisive evidence is the diff, not the log:

- `git diff e065730 HEAD -- tests/unit/test_no_lemma_naming.py` contains **only an added test** (`test_the_allow_list_is_now_exercised_by_a_genuine_persisted_lemma_column`). The `_ALLOWED_LEMMA_SYMBOLS` frozenset itself is untouched — still the same 5 exact names.
- The frontend leg was **strengthened**: `FRONTEND_EXPECTED_FILES` gained the three annotation modules (SUGGESTION-2's fix), widening the non-vacuity check.

The guard ends this change stricter than it started.

---

## Spec Compliance Matrix

**64 / 64 scenarios ✅ COMPLIANT**, each with a covering test that passed at runtime in this verification.

The seven previously non-compliant scenarios, re-checked individually:

| Requirement | Scenario | Covering test (all passing) | Prior → Now |
|---|---|---|---|
| REQ-003-001 | sc.3 — wheel, not source build | `test_python_pin.py::test_the_locked_resolution_carries_a_cp312_wheel_not_only_an_sdist` | UNTESTED → ✅ |
| REQ-003-002 | sc.2 — no spaCy type escapes the adapter | `test_nlp_isolation.py::test_no_nlp_library_import_escapes_the_adapter_package` | UNTESTED → ✅ |
| REQ-003-004 | sc.3 — SPEC-002 token boundaries survive | `test_annotate_import_token_boundaries.py` | UNTESTED → ✅ |
| REQ-003-005 | sc.2 — same form, different tags | `test_spacy_analyzer.py::test_the_same_surface_form_takes_different_tags_in_different_contexts` | UNTESTED → ✅ |
| REQ-003-009 | sc.3 — nothing acts on confidence | `test_no_confidence_action_or_propn_filter.py::test_nothing_acts_on_confidence_anywhere_in_the_package` | PARTIAL → ✅ |
| REQ-003-013 | sc.2 — reprocessing changes no tokenization output | `test_annotate_import_properties.py::test_property_annotation_never_mutates_raw_text_normalized_text_or_position` | UNTESTED → ✅ |
| REQ-003-022 | sc.2 — no proper-noun special case | `test_no_confidence_action_or_propn_filter.py::test_propn_appears_nowhere_outside_the_upos_tags_membership_set` | PARTIAL → ✅ |

**Requirements fully satisfied: 24 / 24.**
**Spec §8 verification hooks: H10 complete** — the fifth Hypothesis property now exists; the enumerated set is whole.

---

## TDD Compliance

| Check | Result | Details |
|-------|--------|---------|
| TDD Evidence reported | ⚠️ | Still no `TDD Cycle Evidence` table in apply-progress; evidence is prose + per-test docstrings |
| All tasks have tests | ✅ | Every `[IMPL]` preceded by a driving `[TEST]`; the 4 remediation tasks are all `[TEST]`/`[DOC]` |
| RED confirmed (test files exist) | ✅ | 55/55; every file named in `tasks.md` exists on disk |
| GREEN confirmed (tests pass) | ✅ | 470 + 66 + 4 re-executed by this verification, all green |
| Triangulation adequate | ✅ | `test_nlp_isolation.py` triangulates 3 forbidden roots × 2 import forms; `ImportPage.test.tsx` covers 7 distinct states |
| Safety net for modified files | ✅ | Both guard suites, `test_python_pin.py` and `test_annotate_import_properties.py` were extended, never replaced |
| Mutation checks documented | ✅ **Exceptional** | 12 documented mutations with verbatim `AssertionError` output; several detectors additionally self-test synthetically on every run |

**TDD compliance: 6/7.** As in my prior report, I record the missing evidence *table* as **WARNING**, not CRITICAL, and state so explicitly for the orchestrator to overrule. The discipline the rule protects is demonstrably present — in a more durable location than a report table — and I re-executed every test myself.

### Test Layer Distribution

| Layer | Tests | Files | Tools |
|-------|-------|-------|-------|
| Unit + integration + API (backend) | 470 | 33 | pytest, Hypothesis, SQLite, real spaCy |
| Frontend unit + component | 66 | 15 | Vitest, Testing Library, TypeScript compiler API |
| E2E | 4 | 4 | Playwright (real backend, real model) |
| **Total** | **540** | **52** | |

### Assertion Quality

Audited every test file added or modified by the remediation for tautologies, orphan empty-collection assertions, type-only assertions, ghost loops, smoke-only renders, implementation-detail coupling and mock-heavy ratios.

**Assertion quality: ✅ 0 CRITICAL, 0 WARNING.**

Zero tautologies. Every new absence assertion is paired with both a non-vacuity test and a documented mutation check — `test_nlp_isolation.py` goes further and asserts its own detector's liveness synthetically on every run, so the guard cannot silently rot. `ImportPage.test.tsx` is behavioral throughout (27 behavioral queries across 7 states, including negative assertions that the table is *never* rendered on error) with no smoke-only render.

### Quality Metrics

**Linter**: ✅ ruff clean; eslint clean at `--max-warnings 0`
**Type checker**: ✅ mypy clean (47 files); tsc clean
**Formatter**: ✅ no pending changes

---

## Issues Found

### CRITICAL

**None.** All four prior CRITICAL findings and the blocker are genuinely closed, each with an executing test rather than an assertion of fact.

### WARNING

**WARNING-1 — the WARNING-8 test-count fix reintroduced a stale number in the same row.**
`docs/traceability-matrix.md:103` (`REQ-003-012`) now reads:

> `452 pruebas backend en total al cierre del corte de remediación; 424 preexistentes sin cambio`

The actual count **at the close of the remediation slice** is **470**, not 452. The correction replaced the old `449` with `452` — the count as of slice 5 — and then labelled it "at the close of the remediation slice", but the remediation itself added 18 backend tests after that number was taken. The row is off by 18 and its own qualifier makes the claim falsifiable.

Severity is WARNING, not CRITICAL, deliberately: `REQ-003-012`'s substantive claim is independently verified (the import route is unmodified, `import.v1.json` is byte-pinned, the full SPEC-002 suite passes), so no `Cumplido` status is made false. But `AGENTS.md` §10 and spec §9 make matrix accuracy a precondition for done, and this is the second time this specific figure has gone stale — a hardcoded test count in a document updated by hand will keep drifting. Recommend either correcting it to 470 or, better, removing the absolute count and citing only the invariant that matters ("424 preexisting SPEC-002 tests unchanged").

### SUGGESTION

1. **Promote the WARNING-7 lemma-collision deferral to `docs/decisions-log.md`.** It currently lives only in this verify-report, which archives with the change — the same failure mode SUGGESTION-4 identified and that the `_update_occurrences` debt was correctly promoted to escape. One row, mirroring line 50.
2. **Record the SUGGESTION-3 confidence-precision decision as a real SPEC-004 spec note.** The reasoning is sound and the deferral is right, but "belongs in a SPEC-004 spec note" is presently an intention with no artifact behind it. It will not survive archive either.
3. **`test_nlp_isolation.py` catches static imports only.** `importlib.import_module("spacy")` or `__import__("spacy")` would evade the AST criterion. This does **not** weaken the guard for the clause it claims — the docstring's argument is correct that a spaCy *type* cannot appear without a name import — but a one-line check for `import_module`/`__import__` string arguments would close the dynamic path cheaply and make the guard total rather than sufficient.

---

## Verdict

**PASS WITH WARNINGS** — and the chain is ready for delivery.

Every finding the remediation claimed to close is genuinely closed, and I confirmed each one against the repository by running the commands myself rather than reading the self-report. The blocker is closed properly: `REQ-003-002` moved to `Cumplido` because a real, non-vacuous, mutation-checked, whole-package guard now enforces spec hook H2 — not because someone edited a status cell. The three remaining CRITICALs are closed with tests that exercise the real thing: real `ImportText` + real `AnnotateImport` over a real database for token boundaries; the **real** spaCy adapter and real model for contextual `saw` VERB/NOUN, which is the scenario ADR-0006 rests on; and the fifth Hypothesis property that completes hook H10.

All 24 requirements and all 64 scenarios are compliant with covering tests that passed at runtime in this run. Every executable gate is green — 470 backend (now warning-free, up from 452 + 1 `DeprecationWarning`), 66 frontend, 4 E2E, 100% backend line *and* branch coverage, clean mypy/ruff/eslint/tsc, reversible migration, byte-identical pinned schema, clean working tree. Both coverage gates hold with margin.

The naming guard survived scrutiny and ended **stricter** than it started — the allow-list frozenset is untouched since slice 1, and the frontend non-vacuity list was widened. The alarming-looking 7-commit pickaxe result is prose mentions, not drift.

All four deferrals are honest. None hides a real gap; `pos_confidence` fails safe by raising rather than clamping, exactly as `REQ-003-008` requires.

What remains is one documentation nit and three record-keeping suggestions — zero code changes. The single WARNING is a hardcoded test count that went stale *again* inside the very row that was correcting it; it makes no status claim false. Worth fixing before archive, since two of the three SUGGESTIONs concern records that will vanish when this change archives, and archive is the moment to catch them.

**Open the PRs.** Nothing here should block delivery.

# Tasks: Harden SPEC-003 Guards and Model-Internal Claims

Feature-branch-chain onto sub-tracker `feat/spec-003-08-harden-guards` @ `975a0a9`
(itself stacked on `feat/spec-003-07-judgment-fixes` @ `b4092c4`). Six slices, fixed
order (design §Delivery Plan): `08f` is mandatorily last because it asserts every
test name the matrix cites resolves against the suite, so `08a`–`08e` must exist
first. `08e` cannot split further — G2 requires the bounded `source_index`
statement copied into all three locations inside one work unit.

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 08a ~380, 08b ~130, 08c ~260, 08d ~415, 08e ~250, 08f ~180 ≈ 1,615 total (test:code ≈2.5:1 applied per slice, not production lines alone — the ratio that was ignored the last three rounds) |
| 400-line budget risk | 08d **over budget at ~415, cut expected**; 08a High (~380, closest to ceiling); Low–Medium for 08b/08c/08e/08f |
| Chained PRs recommended | Yes |
| Suggested split | 6 slices, feature-branch-chain; 08a and 08d each carry a pre-identified contingency cut (see below) |
| Delivery strategy | auto-chain |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Pre-identified split points (Mandate 1 — do not improvise mid-apply)

- **08a** — cut after task 1.6. `08a-1` = tasks 1.1–1.6: `_guard_binding.py` (B1–B4 + D2
  manifest pinning), the Mandate-2 RED test, and `test_no_lemma_naming.py` rebound onto it.
  `08a-2` = tasks 1.7–1.10, based on `08a-1`'s branch: `test_annotation_contract.py`
  rebound onto the same helper (B5 dedup) + the single-implementation check. Each half is
  independently revertible; `08a-1` alone still leaves one guard exploitable, so `08a-2`
  must land before `08b` starts.
- **08d** — cut after task 4.4. **This cut is now expected, not contingent**: task 4.10 (matrix
  cleanup) was added to close the red-at-slice-close hole, pushing the estimate over the ceiling.
  `08d-1` = tasks 4.1–4.4: the `attribute_ruler` enumeration (K1–K4), integration-marked.
  `08d-2` = tasks 4.5–4.11, based on `08d-1`'s branch: the model-free document guard (four regex
  families + false-positive boundary), the `lemmatization-pos` §P1 rewrite, and the matrix
  cleanup. Design already establishes these as independent ("the document guard depends on no
  earlier slice"), so the cut is a natural boundary, not an improvised one.

### Suggested Work Units

| # | Slice | Branch | Base | Est. lines | Focused test | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|---|---|
| 1 | Shared binding helper | `08a-guard-binding-helper` | tracker | ~380 (cut: 1.1–1.6 / 1.7–1.10) | `uv run pytest tests/unit/test__guard_binding.py tests/unit/test_no_lemma_naming.py tests/unit/test_annotation_contract.py` | N/A — pure static analysis over committed schema/source files, no runtime I/O | Delete `_guard_binding.py`; both guards revert to their pre-change local helpers |
| 2 | Frontend owning sets | `08b-frontend-owning-sets` | 08a | ~130 | `cd apps/web && pnpm exec vitest run tests/contracts/no-lemma-naming.test.ts` | N/A — static AST scan over `src/**`, no runtime I/O | Revert `LEMMA_OWNING_FILES` to the pre-change full-set mapping |
| 3 | Docstring instance exemption | `08c-docstring-instance-exemption` | 08b | ~260 | `uv run pytest tests/unit/test_annotation_write_repository_isolation.py` | N/A — AST walk over committed source, no runtime I/O | Revert `_DOCSTRING_OWNERS`/pinned-content dict to the pre-change tuple-of-types form |
| 4 | Model-claim enumeration + document guard | `08d-model-claim-enumeration` | 08c | ~415 — **over budget, cut expected** (4.1–4.4 / 4.5–4.11) | `uv run pytest -m integration tests/integration/test_attribute_ruler_enumeration.py && uv run pytest tests/unit/test_no_model_internal_claims.py` | Real `en_core_web_sm` load at test time (integration mark); network disabled | Delete `_attribute_ruler_enumeration.py` + its test; revert `openspec/changes/lemmatization-pos/design.md` §P1 and the `docs/traceability-matrix.md` value removals to the pre-change prose |
| 5 | Port contract + bounded guarantee | `08e-port-contract-bound` | 08d | ~250 (no further split — G2) | `uv run pytest tests/unit/test_annotation_ports.py tests/unit/test_annotate_import.py` | N/A — docstring + stub-analyzer unit tests, no real model needed | Revert `ports.py` docstring, `docs/glossary.md` entry, and the two `test_annotate_import.py` cases together (single G2 unit) |
| 6 | Traceability matrix | `08f-traceability-matrix` | 08e | ~180 | `uv run pytest tests/unit/test_traceability.py` | N/A — matrix text scan against collected pytest node IDs | Revert `docs/traceability-matrix.md` rows; delete the cited-test resolution check |

Each slice also runs `ruff check`, `mypy` (08b additionally `eslint`/`tsc`). Rollback is a
single-slice revert; no slice touches runtime behaviour or persisted data.

## Phase 1 — Shared binding helper (`08a-guard-binding-helper`)

Closes: REQ-003H-001 (B1–B6), most of AC-003H-01, and `002-text-import`'s amended
`REQ-002-007`/`AC-002-10` (same guard, same binding invariant by reference).

- [x] 1.1 [TEST] `apps/api/tests/unit/test__guard_binding.py` (new): unit tests for `walk_json`, `render`, `OwningDefinition`, `is_exempt` — exact name+position with intact manifest is exempt; `occurrence.extra` key does not decompose into an ancestor segment (B4); a name outside the declared set at an owning position is a violation. RED — module doesn't exist.
- [x] 1.2 [TEST] **Mandate 2 (D2 manifest pinning) — RED**: `test_manifest_pinning_catches_sibling_property_renamed_into_owning_definition` — mutate `annotation.v1.json`'s `$defs.occurrence.properties.raw_text` key to `lemma` (AC-003H-01's own scenario); assert `is_exempt` reports a violation. Add an inline, non-exported positional-only predicate (name + declared-position match, no manifest-completeness check) as a control and assert it WOULD return exempt for the identical mutated document. Record both observed outputs verbatim in the docstring — proof that plain `(name, site)` binding is empirically incapable of catching this mutation.
- [x] 1.3 [IMPL] Create `apps/api/tests/unit/_guard_binding.py`: `JsonMatch`, `walk_json`, `render`, `OwningDefinition(path, declared, exempt)`, `is_exempt` implementing B1–B4 plus D2 manifest-equality. Makes 1.1–1.2 pass (GREEN).
- [x] 1.4 [TEST] `test_no_lemma_naming.py`: rename each of `position`, `raw_text`, `pos`, `pos_origin`, `automatic_pos`, `pos_confidence` to `lemma` in turn — each produces ≥1 violation (AC-003H-01); the four genuine lemma properties still pass; schema-glob fails-closed retained (M2). RED against the still-unmigrated guard.
- [x] 1.5 [IMPL] Rebind `test_no_lemma_naming.py`'s JSON + OpenAPI legs onto `_guard_binding.OwningDefinition` manifests for `import.v1.json` / `annotation.v1.json` / `health.v1.json` and `AnnotationOccurrenceResponse`; delete the local `_path_segments` / `_SCHEMA_OWNING_PATH_SEGMENTS`.
- [x] 1.6 [REFACTOR] Confirm zero duplicated binding code remains in `test_no_lemma_naming.py`; `cd apps/api && uv run pytest tests/unit/test_no_lemma_naming.py tests/unit/test__guard_binding.py`.
- [x] 1.7 [TEST] `test_annotation_contract.py`: same six rename-in-turn scenarios against `annotation.v1.json` via the shared helper. RED against the file's current local `_path_segments`/`_OWNING_PATH_SEGMENT`.
- [x] 1.8 [IMPL] Rebind `test_annotation_contract.py` onto `_guard_binding` directly; delete its duplicated local helper (B5).
- [x] 1.9 [TEST] `test_the_binding_helper_exists_once`: static check that exactly one binding module exists and both guard files import it (helper-uniqueness scenario, M2).
- [x] 1.10 [DOC] `docs/traceability-matrix.md`: draft stub row for `REQ-003H-001` (finalized in Phase 6).

## Phase 2 — Frontend owning sets (`08b-frontend-owning-sets`)

Closes: REQ-003H-001 B6 clause.

- [x] 2.1 [TEST] `no-lemma-naming.test.ts`: assert each `LEMMA_OWNING_FILES` entry contains only names that file's identifiers/JSX/string literals structurally declare, not a blanket reference to `ALLOWED_LEMMA_SYMBOLS`. RED if any file is over-granted.
- [x] 2.2 [IMPL] Narrow `LEMMA_OWNING_FILES` entries in `apps/web/tests/contracts/no-lemma-naming.test.ts` to each file's genuinely declared subset; confirm `lemmatizer` remains absent everywhere in `apps/web`.
- [x] 2.3 [TEST] Boundary control (M3): a name in `ALLOWED_LEMMA_SYMBOLS` not declared by a given owning file still fails when introduced there.
- [x] 2.4 [DOC] Traceability stub update for the B6 clause of `REQ-003H-001`.

## Phase 3 — Docstring instance exemption (`08c-docstring-instance-exemption`)

Closes: REQ-003H-002 (E1–E4), AC-003H-02.

- [x] 3.1 [TEST] `test_annotation_write_repository_isolation.py`: a synthetic module whose module docstring is `DELETE FROM manual_correction WHERE 1=1` is caught even though it's a module docstring. RED against `_DOCSTRING_OWNERS = (ast.Module,)`.
- [x] 3.2 [IMPL] Replace `_DOCSTRING_OWNERS` with `_EXEMPT_MODULE_DOCSTRINGS: dict[str, str]` — `{module path: pinned exact docstring text}` for the one legitimate module; every other module's docstring stays in scope.
- [x] 3.3 [TEST] E4 content pinning — RED: replace the exempted module's docstring with non-reviewed text, assert a violation.
- [x] 3.4 [DOC] Record the E2(b-ii) justification (specific instance + no re-catch leg) as a comment adjacent to the exemption.
- [x] 3.5 [TEST] Boundary control (M3): identical SQL in a function docstring, a class docstring, and a plain string literal each still produce violations — the already-closed legs stay closed.
- [x] 3.6 [TEST] M2 non-vacuity: a module walk reaching zero modules or missing `annotation_write_repository.py` fails closed.
- [x] 3.7 [DOC] Traceability stub row for `REQ-003H-002`.

## Phase 4 — Model-claim enumeration + document guard (`08d-model-claim-enumeration`)

Closes: REQ-003H-003 (K1–K5), AC-003H-03. Split point per Mandate 1: cut after 4.4.

- [ ] 4.1 [TEST] `apps/api/tests/integration/test_attribute_ruler_enumeration.py`, `@pytest.mark.integration`: assert **shape and computed predicates only** — no committed expected constant is permitted (design D4, `openspec/changes/spec-003-harden-guards-and-claims/design.md:60`). Assert the enumeration returns a non-empty rule collection; that every target's fine-tag set is non-empty and disjoint from the others where the model declares them so; that the reachable/unreachable partition computed under `_EXCLUDED_PIPES` is total and non-overlapping; and that the exact-mapping subset is derived at run time from the enumeration's own output, never compared to a literal. The single permitted expected constant is the K2 mutation fixture: flip one enumerated value inside the fixture and assert the run fails, recording the observed output verbatim. A missing model fails loudly, never a vacuous pass (K4). RED — files don't exist.
- [ ] 4.2 [IMPL] `apps/api/tests/integration/_attribute_ruler_enumeration.py`: pure computation over the loaded pipeline, imports `_EXCLUDED_PIPES` from `infrastructure/nlp/spacy_analyzer.py` (K3, single source of truth).
- [ ] 4.3 [TEST] `domain/` stdlib-only structural re-check after the enumeration module lands — no import leak (K4).
- [ ] 4.4 [REFACTOR] `cd apps/api && uv run pytest -m integration tests/integration/test_attribute_ruler_enumeration.py`; confirm the reachable/unreachable partition is consistent with the ledger's finding that excluding the dependency parser renders the catch-all rule unreachable. **State no rule identifier, index, or count in this task or in any commit message for it** (K5) — the partition is asserted by the test, cited by node ID, never transcribed.
- [ ] 4.5 [TEST] `apps/api/tests/unit/test_no_model_internal_claims.py` — RED: define four signature-family regexes — (a) decimal literal with **three or more fractional digits, or any scientific-notation mantissa**, not `%`-suffixed and not part of an `x.y.z` version triple (the explicit precision threshold; one- and two-decimal ratios are legitimate prose, see 4.7); (b) explicit posterior notation (`posterior`/`probabilidad posterior`/`P(...)=`); (c) rule/pattern counts, with the separator class admitting whitespace **and hyphen** so a hyphen-joined identifier cannot escape (`\d+[\s-]+(rules?|reglas?)` or `(rule|regla)[\s-]+\d+`); (d) uppercase tag→UPOS arrow (`[A-Z]{2,5}\s*(→|->|=>)\s*[A-Z]{2,6}`, plus Spanish `mapea(n)? a`). Assert zero matches against `openspec/changes/lemmatization-pos/design.md` §P1 and `docs/traceability-matrix.md` — expected to FAIL against the current text of both.
- [ ] 4.6 [TEST] Non-vacuity (M2): one synthetic fixture per family is reported when it contains that family's pattern.
- [ ] 4.7 [TEST] **False-positive boundary** (this phase owns the exact patterns, per design D3): scan the real Spanish `docs/` tree and this change's own committed artifacts for zero matches on legitimate content — test counts (`503 backend`), coverage percentages (`100%`/`90%`/`80%`), **one- and two-decimal ratio literals such as the test:code ratio stated in this file's forecast and in `openspec/changes/spec-003-harden-guards-and-claims/design.md`**, section refs (`§2.1`), SHA-256 hashes, ADR numbers, semantic-version strings (`2.0.0`), ISO dates, **and the regex-family definitions in task 4.5 themselves**, which contain arrow and character-class syntax but no tag pair. RED until patterns exclude every one of these.
- [ ] 4.8 [IMPL] `test_no_model_internal_claims.py`: implement the scan + four regex families over the fixed document set — `openspec/changes/lemmatization-pos/design.md`, `docs/traceability-matrix.md`, and this change's own artifacts under `openspec/changes/spec-003-harden-guards-and-claims/` per K5. Every member is named by full repository-relative path; a bare file name is ambiguous because two `design.md` files are in scope. Tune until 4.5–4.7 pass.
- [ ] 4.9 [IMPL] **GREEN side of 4.5, first of two documents** (4.5 → 4.8 → 4.9 → 4.10 is one RED with a three-part remediation, not three orphaned `[IMPL]`s). Rewrite `openspec/changes/lemmatization-pos/design.md` §P1: delete the rule-count table, the fine-tag lists tied to counts, the measured diffs, and every fine-tag-to-UPOS exactness claim; keep the `pos_confidence` predicate/mechanism explanation and the load-time self-check; replace the deleted values with a citation to the enumeration test's node ID (K1; W3's sole permitted exception — deleting the claim, not the guard). **Do not restate any deleted value in this task, in the commit message, or in the replacement prose.**
- [ ] 4.10 [IMPL] **GREEN side of 4.5, second of two documents — required for 4.5 to reach GREEN inside this slice**: remove from `docs/traceability-matrix.md` every rule count, measured diff, and fine-tag-to-UPOS exactness claim the guard reports, replacing each with the same enumeration node-ID citation. Without this task the slice's focused test command closes red, because Phase 6's matrix tasks only correct requirement rows and add new ones — they never remove value-bearing text.
- [ ] 4.11 [DOC] Traceability stub row for `REQ-003H-003`. Self-check: this task, and every task in Phase 4, states no rule count, rule identifier, fine-tag set, or exact-mapping pair (K5) — the phase that forbids transcription must not transcribe.

## Phase 5 — Port contract + bounded guarantee (`08e-port-contract-bound`)

Closes: REQ-003H-004 (AC-003H-04), REQ-003H-006 (AC-003H-06). No further split — G2 requires one work unit.

- [ ] 5.1 [TEST] `test_annotation_ports.py` — RED: assert `LinguisticAnalyzer.analyze`'s docstring states `source_index == i` and names `ANNOTATION_FAILED`, alongside the retained `raw_text` obligation; deleting the sentence fails the test, observed output recorded verbatim (non-vacuity).
- [ ] 5.2 [IMPL] `application/annotation/ports.py`: extend `LinguisticAnalyzer.analyze`'s docstring with the `source_index == i` obligation and `ANNOTATION_FAILED` failure name.
- [ ] 5.3 [TEST] Enumerate every rejection branch of the application's annotation validation; assert each maps to a documented port obligation.
- [ ] 5.4 [TEST] `test_annotate_import.py` — **G3 executable acceptance**: stub analyzer swaps two same-text annotations while consistently reassigning `source_index`; assert the run is accepted and rows written, docstring citing `REQ-003H-006` as the documented bound.
- [ ] 5.5 [TEST] `test_annotate_import.py` — covered-case control: same swap WITHOUT reassigning `source_index` fails `ANNOTATION_FAILED`, zero rows written (regression guard on already-shipped behaviour).
- [ ] 5.6 [DOC] **G2 — one bounded statement, three locations, one work unit**: write the bounded `source_index` guarantee once; copy verbatim into `ports.py` (5.2), confirm it matches the spec's `REQ-003H-006` wording, and into `docs/traceability-matrix.md`'s `REQ-003H-006` row.
- [ ] 5.7 [DOC] `docs/glossary.md`: add Spanish `source_index` entry (categoría: atributo), referencing `REQ-003H-006`/`ports.py`.
- [ ] 5.8 [TEST] Guard: `docs/` searched for `source_index` returns ≥1 match.

## Phase 6 — Traceability matrix (`08f-traceability-matrix`)

Closes: REQ-003H-005 (AC-003H-05). Mandatorily last — depends on every test name from Phases 1–5 existing.

- [ ] 6.1 [TEST] `test_traceability.py` — RED: resolve every test name/node ID the whole matrix cites (not only SPEC-001 rows) against the collected suite; a row citing a nonexistent test fails.
- [ ] 6.2 [IMPL] `test_traceability.py`: implement the cited-test resolution check across all rows.
- [ ] 6.3 [DOC] Correct `docs/traceability-matrix.md`'s `REQ-003-004` row: replace "por IDENTIDAD" wording with content-equality + `source_index == position`; cite the swap regression test and the property test's shipped form.
- [ ] 6.4 [TEST] Guard: matrix searched for an identity-based pairing claim → zero matches.
- [ ] 6.5 [DOC] Add matrix rows for `REQ-003H-001`…`REQ-003H-006`, each with AC ref, test file(s), task ID(s), status.
- [ ] 6.6 [REFACTOR] Full regression: `cd apps/api && uv run pytest` (503+new, 100% coverage; domain/application ≥90%, global ≥80%), `ruff check`, `mypy`; `cd apps/web && pnpm run test && pnpm exec eslint . && pnpm exec tsc --noEmit`; confirm `import.v1.json`/`annotation.v1.json` byte-identical; 4 E2E specs green.
- [ ] 6.7 [DOC] Final traceability sweep; close out the proposal's Success Criteria checklist.

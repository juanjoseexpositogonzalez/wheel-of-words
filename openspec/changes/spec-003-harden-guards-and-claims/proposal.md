# Proposal: Harden SPEC-003 Guards and Model-Internal Claims

## Intent

Two Judgment Day rounds patched symptoms and escalated six findings (H1–H6) when the fix budget ran out. The guards that must prove the lemma-isolation and annotation-identity invariants still contain exploitable holes, and three documents assert model internals that have drifted from the pinned `en_core_web_sm`. **The method failed, not just the code**: both rounds were a bounded fix actor rewording a ledger. This cycle defines *what each guard is required to guarantee* before touching implementation, fixing the **binding granularity** of each guard/claim rather than the symptom. It lands as the final chained link before the SPEC-003 tracker merges to `main`, so 003 never reaches `main` carrying known guard holes.

## Scope

### In Scope — six findings, each with an existing reproduction

| ID | Symptom | Root-cause pattern to fix |
|----|---------|---------------------------|
| H1 | JSON lemma exemption binds to the `$defs.occurrence` **component**, and `_path_segments` splits on every dot, so renaming any sibling property (`raw_text`, `pos`, …) to `lemma` yields zero violations; helper duplicated in both guards. | **Binding-granularity mismatch across legs**: the Python leg binds symbol→file/column, the JSON leg binds path→component. Rebind the exemption to lemma-bearing **property names**; unify the helper. |
| H2 | `_DOCSTRING_OWNERS=(ast.Module,)` exempts every module docstring; a docstring `DELETE FROM manual_correction…` run via `text(__doc__)` yields zero violations. Function/class legs are correctly closed. | **Exemption scoped to a syntactic category, not the offending instance**: scope it to the one module whose explanatory prose caused the false positive — not "all module docstrings". |
| H3 | `design.md §P1` + `docs/traceability-matrix.md` claim only `UH→INTJ`/`CD→NUM` are exact, then self-contradict on `CC→CCONJ` (measured diff 0.0); AUX rule-170 count wrong. Written wrong three times. | **Hand-written assertions about model internals drift**: the claim MUST be produced by executable enumeration of the pinned model's `attribute_ruler` table + measured posteriors, or not exist in prose. Treat hand-written model-internal prose as the defect class. |
| H4 | `application/annotation/ports.py` documents only the `raw_text` obligation, but `_validate_and_assemble` rejects `source_index != position` (`ANNOTATION_FAILED`, 500). A port-conformant adapter is rejected at runtime. | State the `source_index` obligation the code enforces. |
| H5 | Traceability `REQ-003-004` row still reads "IDENTIDAD…`raw_text`" (proven content-equality), omits `source_index`, omits the new regression test, and describes the property test under its pre-fix `unique=True` form. Violates AGENTS.md §10. | Update the row to the shipped mechanism. |
| H6 | `source_index` is self-reported: swapping same-text annotations while consistently reassigning `source_index` passes validation. Shipped adapter cannot exhibit this. | **Contract hardening, not a live defect**: strengthen the mechanism OR state the real bounded guarantee accurately (open decision). |

### Out of Scope
S2 parser exclusion (ADR-0011, do not reopen); f-string/`str.join`/`%`-format isolation evasions and `_path_segments` nested-array handling (info-level, user-deferred); single-`Doc` memory, one-UPDATE-per-occurrence, registry thread-safety, `SPACE` POS tag, unit-test DB markers; everything both judges confirmed closed (SQLite chunking, model-path translation, deletion cascade, score normalization, the same-text swap main case).

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `003-lemmatization-pos`: harden isolation-guard binding (H1/H2); replace prose model-internal claims with executable enumeration or remove them (H3); document the `source_index` port obligation (H4); correct traceability `REQ-003-004` (H5); state the accurate bounded `source_index` guarantee (H6).
- `002-text-import`: amend the `AC-002-10` naming-isolation guard shared by both legs (H1/H2 touch this cross-cutting guard).

## Approach

Specification-first: for each finding the delta spec states the invariant, the mutation that MUST be caught, and the non-vacuity assertion — *before* code. Strict TDD (RED→GREEN→REFACTOR): every absence assertion gets a real mutation check whose observed output is recorded in the test docstring, plus a non-vacuity test. No guard deleted, no file/dir excluded, no regex weakened, no AST criterion reverted to text search. H3's remedy is structural — an executable enumeration binds the claim to the pinned model so it cannot drift. `domain` stays stdlib-only; per-occurrence POS (ADR-0006), local-first (ADR-0005); frontend duplicates no linguistic rules.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `apps/api/tests/unit/test_no_lemma_naming.py` | Modified | Rebind JSON exemption to property names; scope docstring exemption to the offending module; unify `_path_segments` |
| `apps/api/tests/unit/test_annotation_contract.py` | Modified | Same shared-helper fix; `source_index` guarantee coverage |
| `apps/api/src/wheel_vocabulary/application/annotation/ports.py` | Modified | Document the `source_index == position` obligation (H4) |
| new executable model-enumeration (H3) | New | Enumerates `attribute_ruler` rules + measured posteriors from the pinned `en_core_web_sm` |
| `apps/api/src/wheel_vocabulary/api/schemas/annotation.v1.json` | Inspected | Keep byte-identical unless a spec change requires otherwise |
| `openspec/changes/lemmatization-pos/specs/{002-text-import,003-lemmatization-pos}/spec.md`, `design.md` | Modified | Amend guard requirements; replace/remove §P1 prose claim |
| `docs/traceability-matrix.md` (Spanish) | Modified | Fix `REQ-003-004` row; add H1–H6 identifiers |

## Open Decisions (AGENTS.md §9 — record, do not silently resolve)

1. **Delta-spec target**: SPEC-003 (`lemmatization-pos`) is not yet archived to baseline `openspec/specs/`. This change should amend the in-flight `openspec/changes/lemmatization-pos/specs/` deltas (recommended), not baseline. Confirm in the spec phase.
2. **H6 direction**: strengthen `source_index` (needs an independent source of truth) vs. state the bounded guarantee accurately (default — the shipped adapter cannot exhibit the defect). Resolve in design.

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Guard fix reintroduces a false positive | Medium | Non-vacuity + mutation tests per leg; scope exemptions to the named instance, never a container |
| H3 enumeration couples tests to model load | Medium | Pin model; gate as integration if heavy; keep `domain` stdlib-only |
| A fourth wrong model-internal claim | Medium | Bind the claim to executable enumeration; no hand-written posteriors survive |
| Chain rebase leaks prior slices into diff | Low | Branch `feat/spec-003-08-harden-guards` off `07-judgment-fixes`; retarget until diff is clean |
| Coverage regresses below 100% backend | Low | A test for every new branch; hold ≥90% domain/application, ≥80% global |

## Rollback Plan

Revert the `feat/spec-003-08-harden-guards` slice. Guards, specs, and docs return to `07-judgment-fixes` @ `b4092c4`. No runtime schema or persisted-data change; `import.v1.json` (SHA-256 `def94cb6…554258`) and the 503/67/4 test baselines are unaffected.

## Dependencies

- Chain link off `07-judgment-fixes` @ `b4092c4` as `feat/spec-003-08-harden-guards`.
- Pinned venv (Python 3.12) + real `en_core_web_sm` for the H3 enumeration and mutation checks.
- Judgment ledger (Engram obs #4790) as established evidence — treated as fact, not re-investigated.

## Success Criteria

- [ ] H1: renaming any non-lemma property inside `$defs.occurrence` to `lemma` produces a violation; a key named `occurrence.extra` is not misclassified; the helper is unified across both guards.
- [ ] H2: a module-docstring SQL string executed via `text(__doc__)` produces a violation; the function and class legs remain closed.
- [ ] H3: the model-internal claim is generated by executable enumeration of the pinned model (or is absent from prose); no hand-written posterior remains.
- [ ] H4: `ports.py` documents the `source_index == position` obligation the code enforces.
- [ ] H5: the `REQ-003-004` row reflects `source_index`, the new regression test, and the current property-test form.
- [ ] H6: the claimed `source_index` guarantee matches exactly what is enforced.
- [ ] Every absence assertion has a mutation check with observed output in its docstring, plus a non-vacuity test.
- [ ] 503 backend / 67 frontend / 4 E2E green; 100% backend coverage held; linters clean; `import.v1.json` SHA-256 unchanged.

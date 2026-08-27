# Design: Harden SPEC-003 Guards and Model-Internal Claims

## Technical Approach

Six findings, one shape: a rule stated at a coarser grain than its subject (spec §2.1–§2.6). Three
mechanical remedies cover all six — one shared binding implementation, one instance-scoped exemption
with pinned content, one generated-only claim channel. No runtime behaviour changes; `domain` stays
stdlib-only; both pinned schemas stay byte-identical.

## Architecture Decisions

### D1 — The shared binding helper lives in `apps/api/tests/unit/_guard_binding.py`

| Option | Trade-off | Decision |
|---|---|---|
| `src/wheel_vocabulary/...` | Ships guard machinery as production code, inside the naming guard's own walk and the 100 %-coverage floor | Rejected |
| `tests/conftest.py` | Fixtures, not pure functions; forces pytest indirection | Rejected |
| `tests/unit/_guard_binding.py` | Sibling non-`test_*` module both guards import directly | **Chosen** |

Mirrors the shipped precedent `tests/integration/_bench_corpus.py`, which pytest's `prepend` import
mode already makes importable from same-directory tests. Both guards live in `tests/unit/`, so one
import path serves both (B5).

### D2 — Binding is `(name, pinned declaring definition)`, and paths are carried, never re-split

The traversal yields `(segments, kind, text)`; the rendered path is for messages only, so a key
containing a dot stays one segment (B4). An owning site is a **pinned property manifest**: a declaring
definition's segment tuple mapped to its complete declared property set plus the lemma-bearing subset.
A match is exempt only when the name is in that subset, sits at a property position of that definition,
and the definition's declared set still equals the manifest. Binding alone cannot catch B3's mutation —
a renamed sibling lands at a legitimate position under a legitimate name — but manifest equality
breaks, so the rename is reported. This is E4 content-pinning applied to the JSON and OpenAPI legs.

### D3 — Model-internal values exist only at run time; governed prose may carry none (RISK #1)

| Option | Trade-off | Decision |
|---|---|---|
| Rewrite the paragraph correctly | Exactly what failed three times (REC-1) | Forbidden |
| Commit a generated block, verify by regeneration | Verification needs the model, so the committed values ship unverified (AMB-11) | Rejected |
| Governed documents carry **zero** values plus a citation | Strictly stronger than AC-003H-03's "no un-cited claim"; guard needs no model | **Chosen** |

`§P1` keeps the predicate and cites the enumeration's pytest node ID; every value it stated is deleted.
A new unit guard, `apps/api/tests/unit/test_no_model_internal_claims.py`, scans a fixed document set for
four value-bearing signature families — high-precision decimal literals, explicit posterior notation,
rule/pattern counts, and uppercase-tag-to-UPOS mapping arrows (with Spanish variants, since `docs/` is
Spanish) — and asserts zero matches. The scanned set includes **this change's own artifacts**, making
K5 executable rather than aspirational.

Transcription becomes structurally impossible because the only surface where a value may appear is the
enumeration's run-time output: typing one into a governed document fails a model-free test on every
invocation. Non-vacuity — the guard asserts each document resolves non-empty, and a synthetic fixture
carrying each signature family must be reported.

### D4 — The enumeration is an integration test that fails loudly

`tests/integration/_attribute_ruler_enumeration.py` (pure computation over a loaded pipeline) plus
`tests/integration/test_attribute_ruler_enumeration.py`, marked `@pytest.mark.integration`. It imports
`_EXCLUDED_PIPES` from `infrastructure/nlp/spacy_analyzer.py`, so reachability (K3) has one source of
truth. Model absence raises rather than skips, following `test_spacy_analyzer.py`. Assertions cover the
output's shape and computed predicates; no expected constant exists except a mutation fixture (K2).

### D5 — H2: exemption scoped to one named module, with pinned content

`_DOCSTRING_OWNERS` is replaced by `(module path, exact docstring text)`. Every other module docstring
returns to scope; the exempted one is exempt only while its content matches the pinned reviewed prose
(E1, E2(b-ii), E4). The function and class legs are untouched.

### D6 — H4/H6: one bounded statement, three locations, one work unit

The `source_index` obligation and its bounded guarantee are written once and copied verbatim into
`ports.py`, the spec, and `docs/traceability-matrix.md` (G2). `docs/glossary.md` gains the Spanish
`source_index` term so it is discoverable outside the source file. `REQ-003H-006`'s uncovered case ships
as a passing test that records acceptance (G3).

## Data Flow

    JSON / OpenAPI document
        └─ traverse ──► (segments, kind, text) ──► _guard_binding.is_exempt
                                                        │
                          pinned property manifests ────┘   (name + definition + declared set)

    pinned model ──► _attribute_ruler_enumeration ──► values (run time only)
                                                          ▲
    governed documents ──► test_no_model_internal_claims ──┘ cite, never transcribe

## File Changes

| File | Action | Description |
|---|---|---|
| `apps/api/tests/unit/_guard_binding.py` | Create | Sole traversal + binding implementation (B1–B5) |
| `apps/api/tests/unit/test_no_lemma_naming.py` | Modify | Import the helper; manifest-bound JSON/OpenAPI legs; rename mutations |
| `apps/api/tests/unit/test_annotation_contract.py` | Modify | Delete the duplicated helpers; import the shared one |
| `apps/web/tests/contracts/no-lemma-naming.test.ts` | Modify | Per-file owning sets enumerate only declared names (B6) |
| `apps/api/tests/unit/test_annotation_write_repository_isolation.py` | Modify | Named-module exemption with pinned content (D5) |
| `apps/api/tests/integration/_attribute_ruler_enumeration.py` | Create | Enumeration over the pinned model (K2–K4) |
| `apps/api/tests/integration/test_attribute_ruler_enumeration.py` | Create | Asserts shape and computed predicates |
| `apps/api/tests/unit/test_no_model_internal_claims.py` | Create | Model-free document guard (D3) |
| `apps/api/src/.../application/annotation/ports.py` | Modify | `source_index == i` obligation, names `ANNOTATION_FAILED` |
| `apps/api/tests/unit/test_annotation_ports.py` | Modify | Obligation-sentence guard; rejection-branch enumeration |
| `apps/api/tests/unit/test_annotate_import.py` | Modify | G3 accepted-bound test and its covered-case control |
| `openspec/changes/archive/2026-08-26-lemmatization-pos/design.md` | Modify | §P1 values deleted, predicate + citation retained |
| `docs/traceability-matrix.md` | Modify | `REQ-003-004` corrected; rows for `REQ-003H-001`…`006` |
| `docs/glossary.md` | Modify | `source_index` term (Spanish) |
| `apps/api/tests/unit/test_traceability.py` | Modify | Every cited test name must resolve against the suite |

## Interfaces / Contracts

```python
# apps/api/tests/unit/_guard_binding.py
JsonMatch = tuple[tuple[str, ...], str, str]          # (segments, kind, text)

def walk_json(document: Any) -> Iterator[JsonMatch]: ...
def render(segments: tuple[str, ...], kind: str) -> str: ...

@dataclass(frozen=True)
class OwningDefinition:
    path: tuple[str, ...]                              # e.g. ("$", "$defs", "<definition>")
    declared: frozenset[str]                           # pinned complete property set
    exempt: frozenset[str]                             # lemma-bearing subset of `declared`

def is_exempt(match: JsonMatch, document: Any, owners: Sequence[OwningDefinition]) -> bool: ...
```

## Testing Strategy

| Layer | What to test | Approach |
|---|---|---|
| Unit | Binding, path decomposition, docstring instance exemption, document claim guard, port obligation, matrix integrity | pytest `@pytest.mark.unit`; every absence assertion carries an M1 mutation with verbatim observed output, an M2 non-vacuity test, and an M3 boundary control |
| Integration | `attribute_ruler` enumeration against the pinned model; accepted/covered `source_index` swap cases | `@pytest.mark.integration`; fails loudly when the model is absent |
| Frontend | Per-file owning sets; a non-declared name in an owning file still fails | Vitest over the existing `ts.createSourceFile` walk |
| E2E | Unchanged | 4 existing Playwright specs must stay green |

Strict TDD throughout: RED first with the observed failure recorded verbatim, then GREEN, then
REFACTOR. Regression budget zero — 503 backend / 67 frontend / 4 E2E, 100 % backend coverage,
`domain`+`application` ≥ 90 %, global ≥ 80 %, `import.v1.json` SHA-256 unchanged.

## Delivery Plan — 6 chained slices (feature-branch-chain, 400-line budget)

The spec phase estimated 4–6. Six is correct once the measured ~2.5:1 test:code ratio is applied;
SPEC-003 overran three times by estimating from production lines alone.

```
feat/spec-003-07-judgment-fixes
 └─ feat/spec-003-08-harden-guards  (sub-tracker, holds proposal + specs + this design)
     └─ 08a-guard-binding-helper 📍
         └─ 08b-frontend-owning-sets
             └─ 08c-docstring-instance-exemption
                 └─ 08d-model-claim-enumeration
                     └─ 08e-port-contract-bound
                         └─ 08f-traceability-matrix
```

| Slice | Scope | Est. lines | Boundary justification |
|---|---|---|---|
| 08a | `_guard_binding.py` + both Python guards rebound | ~380 | Helper and its two call sites are atomic: landing the helper alone leaves a duplicate alive, breaching B5 mid-chain |
| 08b | Frontend per-file owning sets (B6) | ~130 | Different language and toolchain, independently revertible; folding it into 08a breaches the budget |
| 08c | Docstring exemption rescope + content pinning | ~260 | Different guard module, different rule family (§2.2), zero overlap with 08a |
| 08d | Enumeration + document claim guard + §P1 rewrite | ~380 | Self-contained; the document guard depends on no earlier slice |
| 08e | Port obligation, bounded guarantee, `docs/glossary.md`, G3 tests | ~250 | G2 requires every guarantee copy in one work unit, so it cannot split further |
| 08f | Matrix corrections, `REQ-003H` rows, cited-test resolution guard | ~180 | **Last**: it asserts every cited test name resolves, so 08a–08e must already exist |

Each slice verifies with `cd apps/api && uv run pytest`, `ruff`, `mypy`, and (08b) `eslint`/`tsc`.
Rollback is a single-slice revert; no slice touches runtime behaviour or persisted data.

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or
process-integration boundary. The change adds test-side static analysis and documentation only.

## Migration / Rollout

No migration required. No schema, error-contract, port-signature, or persisted-data change.

## Open Questions

None. `DEC-1` and `DEC-2` were settled in the spec phase and are not reopened here.

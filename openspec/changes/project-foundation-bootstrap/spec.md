# Delta Spec — project-foundation-bootstrap

## 1. Metadata

| Field | Value |
|-------|-------|
| Change slug | `project-foundation-bootstrap` |
| Cycle type | First code-touching cycle. Operationalizes SPEC-001 against Constitution v2.0.0 |
| Delta-spec version | 1.0.0 |
| Governing constitution version | v2.0.0 (approved 2026-07-15; multi-language amendment 2026-07-16) |
| Target spec suite | `specs/001-project-foundation/` (SPEC-001 v1.0.0) |
| Requirement prefix (this delta) | `REQ-PFB-###` (zero-padded, 3-digit, sequential from 001) |
| Inherited requirement prefix | `REQ-001-###` (SPEC-001, unchanged by this delta) |
| Persistence mode | `openspec` (companion Engram topic `sdd/project-foundation-bootstrap/spec`) |
| Chain strategy | `feature-branch-chain` (confirmed by maintainer at session preflight) |
| Review budget | 400 authored lines per PR; lockfiles and generated Alembic scripts excluded from authored-line count |
| Source proposal | `openspec/changes/project-foundation-bootstrap/proposal.md` (Engram #2419) |
| Source exploration | `openspec/changes/project-foundation-bootstrap/explore.md` (Engram #2415) |
| Testing capabilities baseline | `sdd/wheel-of-words/testing-capabilities` (Engram #2414: `strict_tdd: false` runtime at cycle start) |
| Init report | `sdd-init-anthropic/wheel-of-words` (Engram #2413) |
| Language | English (methodology artifact per ADR-0010; SPEC-001 remains Spanish and is not translated by this delta) |
| Scope guard | This delta does NOT rewrite `specs/001-project-foundation/`; it refines contracts and adds cycle-scoped requirements only |

---

## 2. Purpose of this delta

SPEC-001 was authored on 2026-07-15 alongside Constitution v1.0.0 and ADR-0001, and left several contracts implicit — most notably the exact JSON body of `GET /api/v1/health`, the semantics of the Alembic baseline migration, the browser matrix of the Playwright suite, and the enforcement severity of coverage thresholds. During the docs-methodology-overhaul cycle (2026-07-16) the Constitution was bumped to v2.0.0 with the multi-language amendment, and ADRs 0002 through 0010 were ratified. The exploration phase for this cycle (Engram #2415) identified **zero blocking discrepancies** between SPEC-001 and the v2.0.0 normative frame, but recorded seven `minor` refresh items, one `major` documentation drift in the top-level traceability matrix, and ten open questions that the proposal (Engram #2419) reduced to ten stated assumptions.

This delta pins the implicit contracts, resolves the three assumptions the proposal explicitly deferred to the spec phase (ASSUMPTION-4, ASSUMPTION-8, ASSUMPTION-9), addresses the seven refresh items as first-class requirements, and specifies the traceability matrix correction as `REQ-PFB-TRACE-01` — a spec-level requirement — without editing the matrix here. Matrix editing lands in Slice D per proposal §5. The delta does not rewrite SPEC-001, does not renumber its requirements, does not touch its files, and does not decide component boundaries, folder layouts, or task ordering. Design and tasks phases own those.

---

## 3. Requirement inheritance from SPEC-001

Every requirement in SPEC-001 is preserved verbatim as the target for this cycle. The table below records inheritance status and points to the delta section that refines a requirement when refinement occurs. **No requirement is removed, renamed, or reworded in the source spec by this delta.**

### 3.1 Functional requirements (REQ-001-001..018)

| REQ ID | One-line intent | Inherited as-is? | Refined by |
|--------|-----------------|------------------|------------|
| REQ-001-001 | FastAPI backend startable via a documented command | Yes | — |
| REQ-001-002 | `GET /api/v1/health` returns the documented JSON payload | Refined | §5 CONTRACT-1 (JSON schema + `version`/`timestamp` semantics) |
| REQ-001-003 | React + TypeScript frontend startable via a documented command | Yes | — |
| REQ-001-004 | Frontend polls `/health` and renders loading / available / unavailable + retry | Refined | §5 CONTRACT-3 (three-state contract with accessible retry, no stack-trace leakage) |
| REQ-001-005 | Backend connects to SQLite via configurable URL | Yes | — |
| REQ-001-006 | Alembic configured with a verifiable initial migration | Refined | §5 CONTRACT-2 (single empty-schema baseline; resolves ASSUMPTION-4) |
| REQ-001-007 | Configuration read from environment variables; `.env.example` committed with no secrets | Yes (behavior); refined at documentation layer only | §4 REF-7 (matrix mis-map is documentation drift, not a behavior change) |
| REQ-001-008 | Unified command surface: `install / dev / test / lint / typecheck / format / e2e / migrate` | Yes | — |
| REQ-001-009 | ≥1 backend unit, ≥1 API, ≥1 SQLite integration test | Yes | — |
| REQ-001-010 | Frontend component tests: loading, available, unavailable, retry | Yes | — |
| REQ-001-011 | Playwright E2E validates the integrated health state | Refined | §5 CONTRACT-4 (single Chromium-only spec; Firefox/WebKit deferred) |
| REQ-001-012 | Backend passes Ruff and mypy strict | Refined | §5 CONTRACT-5 (mypy strict for `domain`/`application`, gradual for `infrastructure`/`api`) |
| REQ-001-013 | Frontend passes TypeScript strict and its linter | Yes | — |
| REQ-001-014 | GitHub Actions CI runs install, lint, types, backend tests, frontend tests, E2E, migrations on every PR | Refined | §5 CONTRACT-5 (job matrix pinned; severity of coverage gate defined in §4 REF-2 + §6 ASSUMPTION-8) |
| REQ-001-015 | Backend directory structure `domain/ application/ infrastructure/ api/` without fictitious domain logic | Refined | §4 REF-4 (no English hardcoding in the empty skeleton); §4 REF-7 (missing matrix row) |
| REQ-001-016 | README explains requirements, install, start, tests, quality, migrations, structure | Yes | — |
| REQ-001-017 | No copyrighted book text in the repository | Yes | — |
| REQ-001-018 | `.env`, local DBs, imported files, coverage, caches, secrets, and generated exports gitignored | Yes | — |

### 3.2 Non-functional requirements (REQ-001-NF-001..006)

| REQ ID | One-line intent | Inherited as-is? | Refined by |
|--------|-----------------|------------------|------------|
| REQ-001-NF-001 | Reproducible dependencies via lockfiles | Yes | — |
| REQ-001-NF-002 | Unit tests provide fast feedback on normal hardware | Yes | — |
| REQ-001-NF-003 | Tests do not depend on public network | Yes | — |
| REQ-001-NF-004 | Application works in recent Chromium | Refined | §5 CONTRACT-4 (Chromium-only for E2E; browser matrix pinned) |
| REQ-001-NF-005 | Status screen uses text and accessible regions, not only color | Yes | — |
| REQ-001-NF-006 | Configuration centralized and documented | Yes | — |

### 3.3 Inheritance summary

- **Total SPEC-001 requirements inherited**: 24 (18 functional + 6 non-functional).
- **Inherited as-is**: 17.
- **Refined by this delta**: 7 (REQ-001-002, -004, -006, -011, -012, -014, -015 and REQ-001-NF-004).
- **Removed / renamed / reworded in source**: 0.
- **New cycle-scoped requirements**: 8 (all `REQ-PFB-*`, defined in §4 and §5).

---

## 4. Refreshes to reconcile SPEC-001 with Constitution v2.0.0

Each subsection below addresses one of the seven `minor` refresh items from exploration §3 (summary table) and elevates it to a normative requirement in this delta. RFC 2119 keywords apply per `openspec/config.yaml` `rules.specs`.

### 4.1 REF-1 — TDD bootstrap exception wording

**Grounding.** Constitution Art. II.1 reads verbatim: *"Cada comportamiento nuevo debe comenzar con una prueba que falle."* Constitution Art. II.2: *"La prueba debe fallar por la ausencia del comportamiento."* AGENTS.md §3 and ADR-0003 restate this as strict RED → GREEN → REFACTOR with no implementation before a failing test. Proposal §5 codifies the bootstrap sequencing rule for this cycle.

**REQ-PFB-BOOT-01 — Bootstrap-prerequisite tag scope.** During Slice A only, tasks that install the test runner, initialize `pyproject.toml`, resolve `uv.lock`, create the empty four-layer directory structure, create `.gitignore` / `.env.example` / `Makefile` skeletons, or otherwise materialize infrastructure prerequisites required for the first RED test to become executable MUST be tagged `[BOOTSTRAP]` in the tasks phase, or equivalently tagged `[IMPL]` with an explicit inline note stating the task creates infrastructure, not behavior. From the first `[TEST]`-tagged task onward — regardless of slice — RED → GREEN → REFACTOR per Constitution Art. II.1 is inviolable: no `[IMPL]` or `[REFACTOR]` task may precede its governing failing test.

**REQ-PFB-BOOT-02 — First RED test anchor.** The first `[TEST]`-tagged task of the cycle MUST be a trivial smoke test that asserts the test runner executes. The smoke test MUST fail before creation (RED because the file does not exist) and pass after creation (GREEN because the runner discovers and runs the assertion). This smoke test is the transition point between bootstrap prerequisites and strict TDD. From this task forward, `[BOOTSTRAP]` MUST NOT be used.

**Acceptance.** See §7 AC-PFB-01 and AC-PFB-02.

### 4.2 REF-2 — Coverage thresholds and enforcement severity

**Grounding.** ADR-0003 §Consequences.Positive states coverage targets: domain/application ≥ 90%, global ≥ 80%, aligned with `openspec/config.yaml` `verify.coverage_threshold: 80`. Constitution Art. II.6 stipulates coverage is a signal, not a substitute for meaningful tests. SPEC-001 test-plan.md §9 references "umbrales de cobertura" without pinning numbers. Proposal ASSUMPTION-8 defaulted to hard-gating from Slice B onward but flagged the severity question for this phase.

**REQ-PFB-COV-01 — Coverage thresholds (cycle-initial).** For this cycle, the following thresholds MUST be configured in the CI pipeline:

| Layer | Threshold | Source |
|-------|-----------|--------|
| Backend `domain/` and `application/` line coverage | ≥ 90% | ADR-0003 |
| Backend global line coverage | ≥ 80% | ADR-0003, `openspec/config.yaml` |
| Frontend line coverage | ≥ 70% | Cycle-initial default (see rationale below) |

Frontend ≥ 70% is a **cycle-initial** cap, not a downgrade of ADR-0003: ADR-0003's numeric thresholds are stated for the Python backend layers only; the frontend threshold is not fixed in any ADR. The 70% floor is chosen as the minimum useful signal for a state-machine component with retry logic and accessibility assertions. Thresholds are revisable at cycle close via a decisions-log entry.

**REQ-PFB-COV-02 — Enforcement severity by slice.** Coverage below any REQ-PFB-COV-01 threshold MUST WARN (soft) during Slice B and Slice C, and MUST FAIL (hard) the CI pipeline starting in Slice D once the six-job workflow is fully wired. This resolves proposal ASSUMPTION-8: the proposal's default was hard-gate from Slice B; the spec revises to WARN-then-FAIL because the ADR-0003 targets apply to a full test suite, not a partial one under construction. The severity flip in Slice D coincides with the final CI wiring (T053–T054) and gives Slice B/C freedom to land minimum-viable coverage without red-lining the pipeline.

**Maintainer-revisable.** If the maintainer prefers hard-gate from Slice B (matching the proposal's original default), REQ-PFB-COV-02 flips to `FAIL from Slice B` without changing REQ-PFB-COV-01.

**Acceptance.** See §7 AC-PFB-03 and AC-PFB-04.

### 4.3 REF-3 — MWE non-goal terminology alignment

**Grounding.** ADR-0009 canonicalizes "expresiones multipalabra específicas del idioma" as the abstract MWE concept, with `mwe_kind: "phrasal_verb"` as the English instance. Constitution Art. V.6 post-amendment (v2.0.0) preserves the separate-modeling rule in language-agnostic terms. SPEC-001 §4 non-goals still list "Phrasal verbs" verbatim as a single non-goal item.

**REQ-PFB-TERM-01 — Non-goal terminology alignment (documentation-only, cycle-scoped).** This delta records the intent that any documentation authored within `openspec/changes/project-foundation-bootstrap/` (proposal, spec, design, tasks, verify-report, archive-report) that references MWE-related non-goals MUST use the canonical wording "language-specific multiword expressions (including phrasal verbs)" — the English rendering of the ADR-0009 canonical term. **This is TERMINOLOGY ONLY: no scope change.** The out-of-scope status of MWE work in this cycle is unchanged: no MWE code, no MWE data, no MWE tests. The word "phrasal verbs" alone remains valid in citations of SPEC-001 §4; the enrichment applies to new authored text.

**Explicit non-modification.** `specs/001-project-foundation/spec.md §4` is NOT edited by this cycle. Its Spanish wording ("Phrasal verbs") stays. Terminology alignment happens only in the artifacts this cycle authors.

**Acceptance.** See §7 AC-PFB-05.

### 4.4 REF-4 — Multi-language skeleton note

**Grounding.** ADR-0008 fixes multi-language scope from day one; the architecture must not hardcode English. Constitution v2.0.0 preamble is generalized. This cycle ships no linguistic code, so no domain entities are affected — but the empty skeleton must not encode English assumptions that a later cycle would have to unwind.

**REQ-PFB-LANG-01 — No English hardcoding in the empty skeleton.** The backend skeleton delivered by this cycle MUST NOT contain any of the following in `domain/` or `application/`:

- Module or package names such as `english/`, `en/`, `english_analyzer.py`, or any other name whose semantics assume a single language.
- Function signatures with default parameters like `def analyze(text: str, language: str = "en") -> ...` or `assume_english: bool = True`.
- String literals matching the regex `(?i)\b(english|en_us|en_gb|assume_english)\b` outside a single explicitly-permitted location: a language-registry stub (if any) exposed for `/health` metadata or configuration.
- ISO-639 language codes (`"en"`, `"es"`, `"de"`, etc.) as magic strings, other than in the permitted language-registry stub.

**REQ-PFB-LANG-02 — Permitted language-registry stub.** IF the design phase decides to expose a language-registry stub for future use (e.g., a `LanguageRegistry` port in `application/` returning the set of supported languages), THEN that stub MUST live in exactly one module, MUST be tested at least once (a single unit test verifying it returns an empty tuple or a documented placeholder), and MUST be documented in `README.md` or the `application/` `__init__.py` docstring. In this cycle no linguistic function depends on the registry — it is a marker of intent, not a runtime dependency.

**Design phase MAY defer.** The design phase MAY conclude that no language-registry stub is needed in this cycle; in that case REQ-PFB-LANG-02 is trivially satisfied (there is nothing to test) and REQ-PFB-LANG-01 alone governs.

**Acceptance.** See §7 AC-PFB-06 and §9 verification hook 2.

### 4.5 REF-5 — `strict_tdd` runtime vs policy documentation

**Grounding.** `openspec/config.yaml` line 31 declares `strict_tdd: true` as **policy**. Engram observation #2414 (`sdd/wheel-of-words/testing-capabilities`) records `strict_tdd: false, reason: no_test_runner_detected` as **runtime** state at cycle start. ADR-0003 references `strict_tdd: true` as the policy that unblocks strict RED-first apply mode. These are two different facts; the exploration §3 flagged the documentation drift risk.

**REQ-PFB-DOCS-01 — Explicit distinction between runtime and policy for `strict_tdd`.** All authored artifacts in this cycle (spec, design, tasks, verify-report, archive-report) that reference `strict_tdd` MUST explicitly disambiguate between the runtime cache (`sdd/wheel-of-words/testing-capabilities`, a truth about the current installation state) and the policy declaration (`openspec/config.yaml` + ADR-0003 + Constitution Art. II, a rule that binds behavior). The runtime state is a fact ("does pytest exist right now?"); the policy is a commandment ("every new behavior begins with a failing test"). The `false` runtime value at cycle start is not a policy relaxation.

**REQ-PFB-DOCS-02 — Post-cycle runtime flip.** At cycle close (archive phase), `sdd/wheel-of-words/testing-capabilities` MUST be upserted to `strict_tdd: true` with `test_runner_command: uv run pytest` and `test_runner_version` pinned to the resolved version. This is the runtime reflecting installation, not a policy amendment.

**Acceptance.** See §7 AC-PFB-07.

### 4.6 REF-6 — T024 task type re-tagging (spec-level directive to tasks phase)

**Grounding.** SPEC-001 tasks.md lists T024 as `[IMPL] Crear capas del backend`. AGENTS.md §8 pins the task tag vocabulary to: `[SPEC]`, `[TEST]`, `[IMPL]`, `[REFACTOR]`, `[DOC]`, `[MIGRATION]`, `[E2E]`, `[CI]`, `[SECURITY]`. This delta additionally introduces `[BOOTSTRAP]` as a cycle-scoped tag (REQ-PFB-BOOT-01). T024 creates empty directories with no runtime behavior; strict-TDD readers can misread `[IMPL]` as a violation.

**REQ-PFB-TASK-01 — T024 must be re-tagged in this cycle's tasks phase.** The tasks phase for this cycle MUST re-tag T024 using the AGENTS.md §8 taxonomy plus the `[BOOTSTRAP]` tag introduced by REQ-PFB-BOOT-01. The exact final tag is the tasks phase's decision; permitted options include `[BOOTSTRAP]`, `[IMPL]` with an explicit "bootstrap prerequisite" note, or `[DOC]` if paired with T025. The spec phase does NOT decide the tag here. This is a directive to the tasks phase, not a resolution.

**Non-modification of SPEC-001.** T024 in `specs/001-project-foundation/tasks.md` is NOT edited. Re-tagging happens in the cycle's own tasks artifact (`openspec/changes/project-foundation-bootstrap/tasks.md`), which is a delta over SPEC-001's task list.

**Acceptance.** See §7 AC-PFB-08.

### 4.7 REF-7 — Traceability matrix correction (as a spec-level requirement)

**Grounding.** Exploration §3 identified a `major` documentation drift in `docs/traceability-matrix.md`:

- The row for `REQ-001-007` currently reads "El dominio no contiene imports de frameworks; arquitectura hexagonal validable" and cites `AC-007` with tests `UT-BE-001, UT-BE-002` and tasks `T004–T010`. **This is wrong.** In SPEC-001, REQ-001-007 is the configuration requirement (env vars + `.env.example`); the hexagonal-structure requirement is REQ-001-015. The tests UT-BE-001 / UT-BE-002 are configuration tests, not hexagonal-structure tests.
- There is NO row for `REQ-001-015` at all.

Proposal ASSUMPTION-10 defaulted the fix to Slice D's documentation task. This delta records the fix as a first-class requirement.

**REQ-PFB-TRACE-01 — Traceability matrix correction (contents; timing is a tasks concern).** By the end of Slice D of this cycle, `docs/traceability-matrix.md` MUST correctly map every `REQ-001-<n>` from SPEC-001 to its acceptance criteria, prevented tests, and tasks. Specifically:

1. The row for `REQ-001-007` MUST reference the SPEC-001 configuration requirement (Statement: "Configuración se lee de variables de entorno; `.env.example` sin secretos"), acceptance criterion `AC-007`, tests `UT-BE-001, UT-BE-002`, and tasks `T008, T010` (with T004–T005 remaining if the maintainer prefers to keep `.env.example`/`.gitignore` scaffolding in the row's task list — this is a tasks-phase judgment).
2. A new row for `REQ-001-015` MUST exist with Statement: "Backend directory structure `domain/ application/ infrastructure/ api/` without fictitious domain logic", acceptance criterion `AC-015` (or the acceptance criterion the spec-suite maps hexagonal-structure verification to), tests: structural inspection of `apps/api/src/wheel_vocab/`, tasks: `T024, T025`.
3. All 18 functional requirements (`REQ-001-001` through `REQ-001-018`) MUST have a row in the matrix. The 6 non-functional requirements (`REQ-001-NF-001..006`) MAY also have rows; the spec-suite `specs/001-project-foundation/traceability.md` already covers a partial subset — the top-level matrix's coverage is set by tasks-phase decision.

**REQ-PFB-TRACE-02 — Mechanical verification.** The verify phase for Slice D MUST run a grep-based check against `docs/traceability-matrix.md` that:

- Returns exactly one row for each of `REQ-001-001` through `REQ-001-018` (18 rows minimum for the SPEC-001 functional set).
- Returns zero occurrences of the mis-mapping regex `REQ-001-007.*dominio no contiene imports` (case-insensitive, on the same line).
- Confirms that the `REQ-001-007` row references `AC-007` and NOT `AC-015`, and that the `REQ-001-015` row references the structural acceptance criterion.

Details of the exact grep patterns are refined by the tasks phase; the spec pins the semantic outcome, not the exact regex.

**No edit here.** This delta does NOT modify `docs/traceability-matrix.md`. The edit is a Slice D task per proposal ASSUMPTION-10.

**Acceptance.** See §7 AC-PFB-09 and §9 verification hook 3.

---

## 5. Explicit contracts pinned by this delta

Each contract below pins a semantic that SPEC-001 left implicit. Every clause is grounded in SPEC-001 or an ADR. Where a contract clause is NOT directly grounded and requires a first-time decision, it is tagged `NEW-CONTRACT-DECISION` and flagged as maintainer-revisable at proposal-review time — see the individual annotations.

### 5.1 CONTRACT-1 — Health endpoint contract

**Grounding.** REQ-001-002 verbatim payload in SPEC-001 §7:
```json
{
  "status": "ok",
  "service": "wheel-vocabulary-api",
  "version": "0.1.0"
}
```
AC-001 confirms HTTP 200 and `status: "ok"`. Plan.md §3 pins `GET /api/v1/health`. Plan.md §5 defines the frontend `HealthResponse` TypeScript interface with the same three keys plus `service` and `version`. Constitution Art. VII.4 forbids business rules in the API layer. ADR-0005 forbids third-party egress.

**REQ-PFB-CONTRACT-01 — `GET /api/v1/health` response body.** The backend MUST respond to `GET /api/v1/health` with HTTP status `200 OK` and a JSON object with exactly the following top-level keys and semantics:

| Key | Type | Value semantic | Grounding |
|-----|------|----------------|-----------|
| `status` | string | Literal `"ok"` when the server is up. No other values in this cycle. | REQ-001-002, AC-001 |
| `service` | string | Literal `"wheel-vocabulary-api"`. | REQ-001-002 verbatim payload |
| `version` | string | The backend package version, read from `pyproject.toml` at process startup and cached. MUST NOT be a hardcoded literal in the route handler. | REQ-001-002 (payload shows `"0.1.0"`); plan.md §3 (Settings carries `app_version`); Constitution Art. VI.1 (reproducibility: each execution records the application version) |
| `timestamp` | string | ISO-8601 UTC timestamp of response generation with millisecond precision (format `"YYYY-MM-DDTHH:MM:SS.sssZ"`). `NEW-CONTRACT-DECISION` — see rationale below. | Not in REQ-001-002 verbatim payload; added to satisfy observability signal per Constitution Art. X.1–2 |

**Additional constraints.**

- The response body MUST NOT contain PII, secrets, environment names, database URLs, or file paths. Constitution Art. X.2 forbids sensitive content in fault contexts; extended to success contexts here for defense-in-depth.
- The response body MUST NOT contain fields beyond the four keys enumerated above. No `git_sha`, `build_id`, `hostname`, or environment-leaking fields.
- The response body MUST validate against a JSON Schema (Draft 2020-12) shipped inside the backend package. The schema's path is a design-phase decision; requirement is that the schema exists, is versioned, and is enforceable at test time (used by CONTRACT-001 test per SPEC-001 test-plan §5).

**`NEW-CONTRACT-DECISION` — `timestamp` field.** REQ-001-002's verbatim payload does not mention `timestamp`. Adding it is a first-time decision by this delta. Rationale: `timestamp` gives the frontend an unambiguous signal that a given response is fresh (not a stale cache) without adding cache-control complexity in this cycle; it also aligns with Constitution Art. X.1 (importation and analysis have explicit states) by supplying a temporal anchor for the health state. **Maintainer-revisable at proposal review**: if the maintainer prefers strict verbatim adherence to REQ-001-002 (three keys only), `timestamp` is dropped and the frontend derives freshness from HTTP response headers instead. The design phase resolves the eventual schema.

**Impact if `NEW-CONTRACT-DECISION` reverses.** No line-count impact on the proposal's forecast. Removing `timestamp` shortens the schema, the handler, and one test by a few lines each.

**Acceptance.** See §7 AC-PFB-10.

### 5.2 CONTRACT-2 — Alembic baseline migration

**Grounding.** REQ-001-006 in SPEC-001 §7: "Alembic estará configurado y existirá una migración inicial verificable." Plan.md §3: "La migración inicial puede crear `app_metadata`; no se crearán entidades de dominio ficticias." AC-006: applying migrations against an empty database succeeds and Alembic records the applied revision. DEC-005 forbids fictitious domain entities. Proposal ASSUMPTION-4 defaulted to empty-schema baseline (SQLAlchemy 2 auto-creating only the `alembic_version` table).

**REQ-PFB-CONTRACT-02 — Alembic baseline is exactly one empty-schema revision.** This cycle MUST ship exactly ONE Alembic revision — the baseline. The revision's `upgrade()` function MUST create no user tables (no `app_metadata`, no domain entities, no linguistic tables). It MAY only ensure Alembic's own `alembic_version` bookkeeping table is created via `alembic upgrade head` against an empty database (this is Alembic's default behavior; no user code is required).

**Rationale.** DEC-005 forbids domain tables in this cycle. Plan.md §3's `app_metadata` option is a suggestion, not a requirement. An empty-schema baseline (a) satisfies REQ-001-006 (Alembic is configured; a verifiable revision exists), (b) satisfies AC-006 (`alembic upgrade head` succeeds from empty; the revision is recorded), and (c) leaves no schema surface to migrate away from in future cycles.

**Downgrade path.** The baseline's `downgrade()` MUST exist and MUST be a no-op that reverses to the pre-baseline state (no user tables, no rows in `alembic_version`). INT-BE-003 (SPEC-001 test-plan §3) tests this per REQ-001-006.

**Resolves.** Proposal ASSUMPTION-4 (Alembic baseline content).

**Acceptance.** See §7 AC-PFB-11.

### 5.3 CONTRACT-3 — Frontend health-status screen

**Grounding.** REQ-001-004: frontend consults health endpoint and shows loading / available / unavailable with retry on error. SPEC-001 §10 state machine: `idle → loading → available | unavailable`. SPEC-001 §11: on backend failure, frontend shows a comprehensible state, does not raise unhandled exceptions, offers retry, and keeps the page usable. AC-003 / AC-004 lock the visible labels ("Backend disponible" / "Backend no disponible"). REQ-001-NF-005 and Constitution Art. IX.3–4: accessible text, not color alone. ADR-0005 forbids third-party egress. Plan.md §4 pins `BackendStatus`, `RetryButton`, and the TanStack Query pattern.

**REQ-PFB-CONTRACT-03 — Status screen contract.** On mount, the frontend status screen MUST call `GET /api/v1/health` against the configured backend URL and MUST render exactly one of the following three visible states at any given time:

| State | Visible content requirements | Grounding |
|-------|------------------------------|-----------|
| **Loading** | Visible text (in Spanish per ADR-0010 product-facing policy) equivalent to "Comprobando estado" per SPEC-001 §10 and UT-FE-001. MUST be perceivable without color (text or ARIA live region). | REQ-001-004, REQ-001-NF-005, Art. IX.3 |
| **Healthy (available)** | Visible text "Backend disponible" per AC-003. MUST also render the `version` and `timestamp` from the health response (implementation may format these; requirement is that both values are present in the DOM). Product name is visible per AC-002. | REQ-001-004, AC-002, AC-003, CONTRACT-1 |
| **Error (unavailable)** | Visible text "Backend no disponible" per AC-004. MUST render a human-readable message; MUST NOT expose a stack trace, exception type, or raw error object. MUST offer a retry control (button) with an accessible name (`aria-label` or visible text) per A11Y-FE-001 and Art. IX.2. | REQ-001-004, AC-004, REQ-001-NF-005, A11Y-FE-001, Art. IX.2 |

**Retry semantics.** The retry control MUST trigger a new `GET /api/v1/health` request. On success the state transitions to Healthy; on continued failure it stays in Error. TanStack Query's retry mechanism satisfies this if configured with `retry: false` at the query level and manual invalidation on button click, or with a custom exponential-backoff retry.

**Out of scope this cycle.** No routing, no theming, no i18n, no user preferences, no session persistence, no analytics. The status screen is a single route (`/`) with one component tree.

**Acceptance.** See §7 AC-PFB-12.

### 5.4 CONTRACT-4 — E2E smoke coverage

**Grounding.** REQ-001-011: Playwright opens the app and verifies the integrated state. AC-011: with backend and frontend running, Playwright opens the app, product name is visible, "Backend disponible" is visible. SPEC-001 test-plan §7: Chromium only, artifacts only on failure. Plan.md §10 risk: no arbitrary sleeps. Proposal §4.4: Playwright `webServer` config. Proposal ASSUMPTION-7 defaulted to Chromium only.

**REQ-PFB-CONTRACT-04 — Playwright E2E scope.** This cycle MUST ship exactly ONE Playwright spec file containing E2E-001 as its sole test case. The spec MUST:

1. Use Playwright's `webServer` config option to boot both the backend (FastAPI via `uvicorn` or equivalent) and the frontend (Vite dev server or preview server) before the test runs. No `setTimeout`, no `sleep()`, no hardcoded wait durations.
2. Load the frontend root URL (from `playwright.config.ts`).
3. Wait for and assert the presence of the product name text (per AC-002 / AC-011).
4. Wait for and assert the visibility of "Backend disponible" (per AC-003 / AC-011).
5. Target `chromium` only. `firefox` and `webkit` MUST NOT be configured in `playwright.config.ts` for this cycle.
6. Capture artifacts (screenshot, video, trace) ONLY on failure per test-plan §7.

**Future browser matrix.** Adding `firefox` and `webkit` is deferred per proposal §5 R-3 and ASSUMPTION-7. Not in scope.

**Acceptance.** See §7 AC-PFB-13.

### 5.5 CONTRACT-5 — CI job matrix

**Grounding.** REQ-001-014: GitHub Actions runs install, lint, types, backend tests, frontend tests, E2E, migrations on every PR. Plan.md §7 lists six jobs by name. REQ-001-012 pins Ruff + mypy strict. REQ-001-013 pins TypeScript + linter. REQ-001-NF-003 forbids public-network dependence. Proposal ASSUMPTION-6 defaulted to `ubuntu-latest` only. ADR-0001 pins GitHub Actions.

**REQ-PFB-CONTRACT-05 — CI job matrix.** The GitHub Actions workflow(s) MUST configure at minimum the following jobs. Each job MUST fail the workflow on non-zero exit. All jobs MUST run on `ubuntu-latest` (macOS deferred per ASSUMPTION-6).

| Job | Command surface (indicative) | Grounding |
|-----|------------------------------|-----------|
| `backend-quality` | `uv run ruff check .` + `uv run ruff format --check .` | REQ-001-012 |
| `backend-typecheck` | `uv run mypy` with strict mode for `domain/` and `application/`, gradual for `infrastructure/` and `api/`. | REQ-001-012; `NEW-CONTRACT-DECISION` for the layered strictness (see below) |
| `backend-tests` | `uv run pytest` with coverage measurement per REQ-PFB-COV-01 | REQ-001-009, REQ-001-014 |
| `frontend-quality` | `pnpm run lint` (ESLint) | REQ-001-013 |
| `frontend-typecheck` | `pnpm run typecheck` (`tsc --noEmit`) | REQ-001-013 |
| `frontend-tests` | `pnpm run test` (Vitest with coverage per REQ-PFB-COV-01) | REQ-001-010, REQ-001-014 |
| `migration-check` | `alembic upgrade head` against an empty temporary SQLite | REQ-001-006, AC-006, REQ-001-014 |
| `e2e` | `pnpm exec playwright test` (Chromium only per CONTRACT-4) | REQ-001-011, REQ-001-014 |

**Consolidation permitted.** Plan.md §7 groups `backend-quality` and `backend-typecheck` into a single job. The design phase MAY consolidate to six jobs matching plan.md §7 verbatim; the requirement is that each command surface above executes at least once per PR. Coverage-threshold enforcement severity follows REQ-PFB-COV-02 (WARN in Slice B/C, FAIL in Slice D).

**`NEW-CONTRACT-DECISION` — layered mypy strictness.** SPEC-001 REQ-001-012 requires "configuración estricta acordada" (agreed strict configuration) without pinning per-layer strictness. This delta pins strict mypy for `domain/` and `application/` (aligning with Constitution Art. VII.1 domain purity and Art. VII.2 application isolation) and gradual mypy for `infrastructure/` and `api/` where framework interop with SQLAlchemy, Alembic, and FastAPI benefits from a more permissive default while the four-layer skeleton stabilizes. **Maintainer-revisable at proposal review**: if the maintainer prefers uniform strict across all four layers, the layered concession is dropped and the tasks/design phase absorbs a modest increase in initial mypy-error triage. Impact if reversed: potentially adds a small number of `# type: ignore[misc]` comments in `infrastructure/` per SQLAlchemy 2 typing quirks; no proposal-forecast impact.

**Acceptance.** See §7 AC-PFB-14 and AC-PFB-15.

---

## 6. Assumption resolutions

The proposal deferred ten assumptions across spec, design, and tasks phases. This delta resolves only the three that proposal §6 marked "re-examined in `sdd-spec`". The remaining seven remain the responsibility of design or tasks per proposal §6.

### 6.1 ASSUMPTION-4 — Alembic baseline content

**Resolution.** Empty-schema baseline. See §5 CONTRACT-2 / REQ-PFB-CONTRACT-02.

**Grounding.** DEC-005 (no fictitious domain), plan.md §3 (baseline "may create `app_metadata`" is permissive not prescriptive), REQ-001-006 (a verifiable revision exists — an empty-schema revision is verifiable via `alembic upgrade head` succeeding and `alembic_version` populating).

**Blast radius if wrong.** Small. If the maintainer prefers an `app_metadata` version-pin table, one migration script gains ~10 lines and INT-BE-002/INT-BE-003 assertions gain one table-existence check. No proposal-forecast impact.

### 6.2 ASSUMPTION-8 — Coverage-threshold enforcement severity

**Resolution.** WARN in Slice B and Slice C; FAIL from Slice D onward. See §4 REF-2 / REQ-PFB-COV-02.

**Grounding.** ADR-0003 targets a full test suite. Slice B and Slice C land partial suites en route to Slice D's fully wired CI; hard-gating during partial construction penalizes the mid-cycle state. Slice D flips the severity to FAIL, at which point the six-job workflow is complete and the ADR-0003 numeric targets apply cleanly. Constitution Art. II.6 is respected: coverage is a signal, not a substitute for meaningful tests — a WARN-then-FAIL rollout preserves the signal without inflating the coverage number with vacuous tests to appease the gate.

**Blast radius if wrong.** Small–Medium. If the maintainer prefers hard-gate from Slice B (proposal §6's original default), Slice B PRs may be blocked by coverage even if the code is otherwise correct. Reversing later is a one-line CI configuration change. **Maintainer-revisable at proposal-review time.**

### 6.3 ASSUMPTION-9 — Docker Compose scope

**Resolution.** OUT of scope for this cycle. No `docker-compose.yml` lands in Slice A, B, C, or D.

**Grounding.** ADR-0005 (local-first) does not require containerization for developer laptop workflow. DEC-006 marks Docker optional. Docker Compose would only be justified when the project depends on real infrastructure sidecars (Redis, task queue, PostgreSQL, etc.) — none of which land in this cycle. SPEC-001 §6 assumptions state "Docker opcional" without requiring it.

**Follow-up.** A future maintenance cycle MAY add `docker-compose.yml` when real infra dependencies land (proposal §9 out-of-scope follow-ups list).

**Blast radius if wrong.** Small. Adding `docker-compose.yml` in a future cycle is a self-contained addition of one file plus README section; no rework of existing bootstrap code. **Maintainer-revisable at proposal-review time.**

### 6.4 Re-forecast triggers

None of the three resolutions above materially change the proposal's aggregate line-count forecast (600–1120 authored lines). Empty-schema Alembic baseline is smaller than the `app_metadata` variant. WARN-then-FAIL coverage is a CI config toggle, not code. Docker Compose out-of-scope keeps Slice D leaner than the proposal's high bound. **No re-forecast trigger for the tasks phase.**

---

## 7. Acceptance criteria — new for this delta

Format: `AC-PFB-<n>: given <precondition>, when <action>, then <observable outcome>.` Grouped by verifying slice. Every REF and CONTRACT above has at least one AC.

### 7.1 Slice A — Repository scaffold and Python toolchain

**AC-PFB-01** (REF-1 / REQ-PFB-BOOT-01) — Given the Slice A tasks list, when a reviewer inspects task tags, then every task that lands before the first `[TEST]` task carries the `[BOOTSTRAP]` tag OR carries `[IMPL]` with an explicit "bootstrap prerequisite" note in the task description, and no `[TEST]`, `[REFACTOR]`, `[IMPL]` (without note), or `[MIGRATION]` task exists in Slice A that violates the RED-first sequence for a behavior.

**AC-PFB-02** (REF-1 / REQ-PFB-BOOT-02) — Given Slice A has landed, when the first `[TEST]` task of Slice B runs (a smoke test asserting the pytest runner executes), then the test fails before the smoke test file is created (RED because the file does not exist or pytest reports collection error) and passes after the file is committed (GREEN with a trivial assertion).

**AC-PFB-05** (REF-3 / REQ-PFB-TERM-01) — Given any artifact authored inside `openspec/changes/project-foundation-bootstrap/` (this spec, proposal, design, tasks, verify-report, archive-report), when a reader grep-searches for MWE-related non-goal wording, then no bare "phrasal verbs" mention exists outside a citation of `specs/001-project-foundation/spec.md §4`; the canonical wording "language-specific multiword expressions (including phrasal verbs)" appears wherever the concept is introduced.

**AC-PFB-07** (REF-5 / REQ-PFB-DOCS-01) — Given the cycle's artifacts, when a reader searches for the token `strict_tdd`, then every occurrence is qualified explicitly as either "runtime" (referring to `sdd/wheel-of-words/testing-capabilities`) or "policy" (referring to `openspec/config.yaml` + ADR-0003 + Constitution Art. II); no bare `strict_tdd` reference exists that leaves the distinction ambiguous.

### 7.2 Slice B — Backend TDD

**AC-PFB-03** (REF-2 / REQ-PFB-COV-01) — Given Slice B lands the backend test suite, when `uv run pytest` runs with coverage measurement, then coverage output reports domain/application line coverage ≥ 90% and global line coverage ≥ 80% at least as an emitted signal (the WARN severity per REQ-PFB-COV-02 means the pipeline does not fail if below threshold in Slice B; the coverage number is still reported).

**AC-PFB-06** (REF-4 / REQ-PFB-LANG-01) — Given Slice B has landed the backend skeleton, when the verify hook (§9 hook 2) runs a grep against `apps/api/src/wheel_vocab/domain/` and `apps/api/src/wheel_vocab/application/` for the regex `(?i)\b(english|en_us|en_gb|assume_english)\b` AND for hardcoded ISO-639 language codes as string literals, then the count is zero outside the single permitted language-registry stub location (if any) documented per REQ-PFB-LANG-02.

**AC-PFB-10** (CONTRACT-1 / REQ-PFB-CONTRACT-01) — Given the backend is running, when a test client issues `GET /api/v1/health`, then the response has HTTP status 200, the body validates against the shipped JSON Schema, the `status` field equals `"ok"`, the `service` field equals `"wheel-vocabulary-api"`, the `version` field matches the version declared in `pyproject.toml` (asserted by reading `pyproject.toml` in the test), the `timestamp` field parses as a valid ISO-8601 UTC timestamp with millisecond precision, and no additional top-level keys are present in the body.

**AC-PFB-11** (CONTRACT-2 / REQ-PFB-CONTRACT-02) — Given a fresh empty SQLite database (INT-BE-002 fixture), when `alembic upgrade head` runs, then the command exits with status 0, the `alembic_version` table exists with exactly one row corresponding to the baseline revision ID, and no user tables (no `app_metadata`, no domain entities) exist in the database.

### 7.3 Slice C — Frontend TDD

**AC-PFB-12** (CONTRACT-3 / REQ-PFB-CONTRACT-03) — Given the frontend is rendered in a test environment (Vitest + Testing Library) with the backend response mocked, when the mock returns 200 with a valid `HealthResponse`, then the DOM contains the text "Backend disponible" and both the `version` and `timestamp` values from the response are present in the accessibility tree; when the mock returns a network error, then the DOM contains "Backend no disponible", no stack trace is present, and a retry button with an accessible name is queryable via `getByRole('button')`.

### 7.4 Slice D — E2E + CI + README + traceability matrix

**AC-PFB-04** (REF-2 / REQ-PFB-COV-02) — Given Slice D wires the final CI configuration, when the CI pipeline runs against a PR where any layer's coverage falls below its REQ-PFB-COV-01 threshold, then at least one job's exit status is non-zero and the pipeline reports FAILED. Conversely, when all thresholds are met, the pipeline reports SUCCESS.

**AC-PFB-08** (REF-6 / REQ-PFB-TASK-01) — Given the tasks phase artifact `openspec/changes/project-foundation-bootstrap/tasks.md`, when a reader inspects the task corresponding to T024 ("Crear capas del backend"), then it carries a tag from the union of AGENTS.md §8 tag vocabulary + `[BOOTSTRAP]` (introduced by REQ-PFB-BOOT-01), and if the tag is `[IMPL]` a bootstrap-prerequisite note is present in the task description.

**AC-PFB-09** (REF-7 / REQ-PFB-TRACE-01) — Given `docs/traceability-matrix.md` after Slice D lands, when a reviewer scans the matrix for `REQ-001-*` rows, then:
- Exactly one row exists for each `REQ-001-<n>` where `n ∈ {001..018}` (18 rows minimum).
- The `REQ-001-007` row's Statement references configuration/env-vars, its Acceptance column references `AC-007`, and its Test column references `UT-BE-001, UT-BE-002`.
- A `REQ-001-015` row exists with Statement referencing the four-layer directory structure and Acceptance referencing `AC-015` (or the acceptance criterion the tasks phase chose).

**AC-PFB-13** (CONTRACT-4 / REQ-PFB-CONTRACT-04) — Given Slice D wires Playwright, when `pnpm exec playwright test` runs against the checked-out repository, then exactly one Playwright spec file executes, the test uses `webServer` config to boot backend and frontend without arbitrary sleeps, `chromium` is the only configured browser project in `playwright.config.ts`, and the test asserts both product name and "Backend disponible" text visibility.

**AC-PFB-14** (CONTRACT-5 / REQ-PFB-CONTRACT-05) — Given a PR against the tracker branch, when GitHub Actions runs, then at least the following command surfaces execute successfully (or per REQ-PFB-COV-02 severity flip during Slice D): backend Ruff check, backend mypy (strict for `domain`/`application`, gradual for `infrastructure`/`api`), backend pytest with coverage, frontend ESLint, frontend `tsc --noEmit`, frontend Vitest with coverage, Alembic `upgrade head` against empty SQLite, Playwright Chromium E2E. Any single failure fails the workflow.

**AC-PFB-15** (CONTRACT-5 / REQ-PFB-CONTRACT-05) — Given the CI configuration, when a reviewer inspects the runner matrix, then all jobs use `ubuntu-latest`; no `macos-latest` or `windows-latest` runner is configured for this cycle.

### 7.5 Acceptance summary by verifying slice

| Slice | AC count | AC IDs |
|-------|----------|--------|
| A | 4 | AC-PFB-01, AC-PFB-05, AC-PFB-07 (partial), and AC-PFB-02 (verified transitionally when Slice B's first test runs) |
| B | 4 | AC-PFB-03, AC-PFB-06, AC-PFB-10, AC-PFB-11 |
| C | 1 | AC-PFB-12 |
| D | 6 | AC-PFB-04, AC-PFB-08, AC-PFB-09, AC-PFB-13, AC-PFB-14, AC-PFB-15 |
| **Total** | **15** | — |

Every REF and every CONTRACT introduced by §4 and §5 is covered by at least one AC. AC-PFB-07 spans multiple slices (documentation discipline holds throughout the cycle); it is verified per artifact at its authoring slice.

---

## 8. Explicit non-additions (scope creep guard)

This delta explicitly does NOT do any of the following. Any temptation to breach these boundaries is a scope violation, not a judgment call.

1. **Does NOT add new REQs to SPEC-001.** Every requirement introduced here carries the `REQ-PFB-*` prefix and is scoped to this cycle. SPEC-001's `REQ-001-*` numbering and inventory are unchanged.
2. **Does NOT change SPEC-001's numbering or file structure.** `specs/001-project-foundation/spec.md`, `acceptance.md`, `plan.md`, `test-plan.md`, `tasks.md`, `decisions.md`, and `traceability.md` are read-only inputs to this delta.
3. **Does NOT modify the target spec suite files in `specs/001-project-foundation/`.** No SPEC-001 file is written, appended, or reformatted by this cycle. If a mismatch between SPEC-001 wording and Constitution v2.0.0 is discovered, it is refined here in `REQ-PFB-*` form, not by editing SPEC-001.
4. **Does NOT edit `docs/traceability-matrix.md`.** The correction is specified here (REF-7, REQ-PFB-TRACE-01) and the mechanical edit lands in Slice D per proposal ASSUMPTION-10.
5. **Does NOT decide component boundaries, folder layouts, or module names beyond the four-layer directory names REQ-001-015 already pins.** Design owns this. Specifically, this delta does NOT decide: `apps/api/src/wheel_vocab/` internal package layout beyond REQ-001-015's four directories; the exact filenames of Settings / HealthResponse / route handler modules; the `LanguageRegistry` stub location if any.
6. **Does NOT decide DB schema shape.** CONTRACT-2 pins empty-schema baseline; the actual schema for future cycles is future scope.
7. **Does NOT decide task ordering, task-level LOC estimates, or per-task file lists.** Tasks phase owns this. The tasks phase MUST re-tag T024 per REQ-PFB-TASK-01 and MUST introduce `[BOOTSTRAP]` per REQ-PFB-BOOT-01, but the exact task numbering and per-task descriptions are the tasks-phase artifact.
8. **Does NOT decide the sub-split of Slice B.** Proposal ASSUMPTION-1 defers this to the tasks phase.
9. **Does NOT decide Makefile vs. `uv scripts` composition.** Proposal ASSUMPTION-3 defers this to design.
10. **Does NOT decide TypeScript ESLint ruleset baseline.** Proposal ASSUMPTION-5 defers this to design.
11. **Does NOT decide the JSON Schema file path or format specifics for the health-response schema.** Design owns the path and versioning scheme; CONTRACT-1 requires that the schema exists.

---

## 9. Verification hooks

The verify phase for the cycle MUST run at minimum the following mechanical checks. Exact command syntax is refined by the tasks/verify phases; the semantic outcome is pinned here.

### Hook 1 — Forbidden domain classes
```bash
grep -RE "class\s+(Lexeme|Occurrence|Corpus|Mwe|MultiwordExpression|Lemma|SurfaceForm|WordForm|PartOfSpeech|ManualCorrection|TextExtractor)\b" apps/api/src/
```
Expected: exit code non-zero (grep found nothing). Any hit is a DEC-005 / Constitution Art. VII.6 / SPEC-001 §4 violation. Verifies proposal R-4.

### Hook 2 — Hardcoded English in domain/application
```bash
grep -REn "(?i)\b(english|en_us|en_gb|assume_english)\b" apps/api/src/wheel_vocab/domain/ apps/api/src/wheel_vocab/application/
grep -REn "['\"]en['\"]" apps/api/src/wheel_vocab/domain/ apps/api/src/wheel_vocab/application/
```
Expected: zero hits outside the permitted language-registry stub location documented per REQ-PFB-LANG-02. Verifies REQ-PFB-LANG-01 / AC-PFB-06.

### Hook 3 — Traceability matrix correctness
```bash
# Count REQ-001-<n> rows for n=001..018
for n in 001 002 003 004 005 006 007 008 009 010 011 012 013 014 015 016 017 018; do
  count=$(grep -c "^| REQ-001-${n}\b" docs/traceability-matrix.md)
  [ "$count" = "1" ] || echo "MISS: REQ-001-${n} row count = $count"
done
# Assert REQ-001-007 does NOT map to hexagonal wording
grep -Ei "REQ-001-007.*dominio no contiene imports" docs/traceability-matrix.md
# Assert REQ-001-015 row references AC-015
grep -E "^\| REQ-001-015 \|.*AC-015" docs/traceability-matrix.md
```
Expected: exactly one row per REQ-001-001..018 (18 rows minimum); the mis-mapping grep returns nothing (exit 1); the REQ-001-015 row exists and references AC-015. Verifies REQ-PFB-TRACE-01 / REQ-PFB-TRACE-02 / AC-PFB-09.

### Hook 4 — Health response JSON Schema validation
Given the backend running under a test harness, the API test that verifies `GET /api/v1/health` MUST validate the response body against the shipped JSON Schema (per CONTRACT-1). Verifies AC-PFB-10.

### Hook 5 — Coverage thresholds (severity per REF-2 + ASSUMPTION-8)
```bash
# Backend
uv run pytest --cov=apps/api/src/wheel_vocab --cov-report=term-missing --cov-fail-under=80
# Frontend
pnpm run test -- --coverage
# Coverage-threshold enforcement per REQ-PFB-COV-02 (WARN in Slice B/C via CI job set to `continue-on-error: true`; FAIL in Slice D via removing that flag).
```
Expected: In Slice B/C, coverage below threshold reports WARN but pipeline continues. In Slice D and beyond, coverage below threshold fails the pipeline. Verifies AC-PFB-03 / AC-PFB-04.

### Hook 6 — Copyrighted content sweep
Standard REQ-001-017 / AC-013 check. Reused from SPEC-001; no new hook needed. Listed here for completeness.

---

## 10. Open items deferred to design and tasks

The following decisions are intentionally left open by this delta. Each is tagged with the owning phase.

### 10.1 Design phase owns

- **Backend package internal layout.** `apps/api/src/wheel_vocab/{domain,application,infrastructure,api}/` internal file structure, module naming, and cross-layer import boundaries. Only REQ-001-015's four top-level directory names are pinned. (Proposal ASSUMPTION-2 defers `apps/api/pyproject.toml` vs. root-workspace to design.)
- **JSON Schema file path and versioning.** CONTRACT-1 requires the health-response JSON Schema exists; design decides `apps/api/src/wheel_vocab/api/schemas/health.schema.json` vs. an alternative path, and the versioning scheme (embedded `$id`, per-schema version field, or filename suffix).
- **`LanguageRegistry` stub location and shape** (if design decides to include one). Per REQ-PFB-LANG-02: one module, documented, one test.
- **Alembic env layout.** `apps/api/migrations/` structure, `env.py` content, target-metadata composition. CONTRACT-2 pins the semantic (empty-schema baseline); design picks the file organization.
- **TypeScript ESLint ruleset baseline.** Proposal ASSUMPTION-5 defers to design.
- **Makefile vs. `uv scripts` composition.** Proposal ASSUMPTION-3 defers to design.
- **`BackendStatus` component decomposition.** Plan.md §4 sketches `App`, `BackendStatus`, `RetryButton`; design decides whether to keep these three or consolidate.
- **HTTP client details.** Plan.md §4 mentions TanStack Query; design decides retry policy, cache semantics, and query invalidation on retry-button click.
- **Layered mypy strictness configuration.** Where in `pyproject.toml` the per-module strictness overrides live and their exact settings. CONTRACT-5 pins the semantic split; design picks the config surface.

### 10.2 Tasks phase owns

- **Slice B sub-split decision.** Proposal ASSUMPTION-1: split into B1 + B2 if the LOC forecast exceeds 400 authored lines; keep as one Slice B otherwise. Tasks phase performs the forecast.
- **T024 final tag.** REF-6 / REQ-PFB-TASK-01: `[BOOTSTRAP]`, `[IMPL]` with note, or `[DOC]` — tasks phase decides.
- **Traceability-matrix correction task placement.** Proposal ASSUMPTION-10 defaults to Slice D; tasks phase may split into two sub-tasks (one for the REQ-001-007 correction, one for the new REQ-001-015 row) or combine.
- **Per-task LOC estimates.** REF-2 severity flip (WARN → FAIL) depends on Slice D being the flip point; tasks phase's LOC forecast confirms slice sizing.
- **Full task inventory delta over SPEC-001.** The tasks-phase artifact is a delta over `specs/001-project-foundation/tasks.md`; the spec phase does NOT enumerate the 62 tasks here.

### 10.3 Explicitly out of this cycle

Per proposal §9 and ASSUMPTION-9: Docker Compose skeleton, macOS CI runner support, Firefox/WebKit Playwright targets, project rename ("Wheel Vocabulary" vs. `wheel-of-words`), `openspec/changes/` gitignore policy resolution, `sdd-archive-anthropic` skill move-vs-copy defect fix.

---

## Notes

- This delta is 100% English per ADR-0010 (methodology artifact). SPEC-001's Spanish wording is cited verbatim where necessary; no translation of source SPEC-001 files occurs.
- Every `REQ-PFB-*` requirement uses RFC 2119 keywords (MUST, SHALL, SHOULD, MAY) per `openspec/config.yaml` `rules.specs`.
- Every REF and CONTRACT has at least one AC in §7; every AC is verifiable by a mechanical hook in §9 or by inspection.
- Two `NEW-CONTRACT-DECISION` items exist in this delta: the `timestamp` field in CONTRACT-1 and the layered mypy strictness in CONTRACT-5. Both are maintainer-revisable at proposal-review time; neither materially changes the proposal's line-count forecast per §6.4.
- Design phase is **unblocked** by this delta: every ambiguity design needs to resolve is either pinned by CONTRACT-1..5 or explicitly listed in §10.1.

---

## References

- **This cycle's artifacts**: `openspec/changes/project-foundation-bootstrap/{explore.md, proposal.md}`.
- **Target spec suite**: `specs/001-project-foundation/{spec.md, acceptance.md, plan.md, test-plan.md, tasks.md, decisions.md, traceability.md}`.
- **Constitution**: `docs/constitution.md` (v2.0.0).
- **ADRs**: `docs/adr/README.md` and ADR-0001 through ADR-0010 (in particular ADR-0002 hexagonal, ADR-0003 TDD, ADR-0005 local-first, ADR-0008 multi-language, ADR-0009 MWE, ADR-0010 language policy).
- **Definition of Done**: `docs/definition-of-done.md`.
- **Traceability matrix (drift documented in this delta, edit deferred to Slice D)**: `docs/traceability-matrix.md`.
- **AGENTS.md** §§ 2, 3, 5, 6, 8, 10.
- **Engram anchors**: #2413 (init), #2414 (testing capabilities), #2415 (explore), #2419 (proposal).
- **Tone calibration only (not reproduced)**: `openspec/archive/2026-07-16-docs-methodology-overhaul/spec.md`.

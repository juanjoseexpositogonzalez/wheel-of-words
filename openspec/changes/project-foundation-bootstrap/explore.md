# Exploration — project-foundation-bootstrap

**Change slug**: `project-foundation-bootstrap`
**Phase**: Exploration
**Date**: 2026-07-20
**Status**: Complete — ready for proposal

---

## 1. Change Identity

- **Slug**: `project-foundation-bootstrap`
- **Target spec**: SPEC-001 — `specs/001-project-foundation/`
- **Cycle type**: First code-touching cycle. Establishes the monorepo skeleton, Python + JS toolchains, hexagonal layer structure, health endpoint, and CI so that every subsequent vertical slice has a stable scaffold to build on. No linguistic domain logic lands here.
- **Constitutional anchors**:
  - **Art. I** (SDD) — specification, numbered requirements, and verifiable acceptance criteria already exist in `specs/001-project-foundation/` before this cycle writes a line of code. All five SPEC-001 artifacts (spec, acceptance, plan, test-plan, tasks) are in place; this cycle is their operationalization, not their creation.
  - **Art. II** (TDD) — every new backend behavior begins with a RED test. The bootstrap exception (see §4 Risks) is the only case where pre-test setup is permitted; it is addressed explicitly there.
  - **Art. III** (vertical slices) — this cycle is itself the first vertical slice: backend starter → frontend starter → `/health` end-to-end. Each slice produces an observable result (running server, visible UI, CI green).
  - **Art. IV.4–5** (local-first / no egress) — the health endpoint and DB must not reach out to any third-party service; test data must be synthetic.
  - **Art. VI** (reproducibility) — lockfiles (`uv.lock`, `pnpm-lock.yaml`) and pinned tool versions must exist from commit one.
  - **Art. VII.1–4** (hexagonal architecture) — `domain/`, `application/`, `infrastructure/`, `api/` layers created; domain layer must have zero framework imports even in the empty bootstrap state.
  - **Art. VIII.1–2** (quality) — Ruff, mypy strict, TypeScript strict, ESLint, and Vitest/pytest configured and enforced in CI.
  - **Art. IX.1–6** (accessibility) — health-status screen must use text, not color alone; retry control must have an accessible name.
  - **Art. XI** (Definition of Done) — requirements updated, tests green, linter/types green, migrations verified, traceability matrix updated.
  - **ADR-0001** — exact toolchain: `uv` (not poetry), `pnpm` (not npm/yarn), pytest, Hypothesis, Ruff, mypy, React, Vite, TanStack Query, Vitest, Testing Library, Playwright, GitHub Actions.
  - **ADR-0002** — four-layer hexagonal split enforced from the first commit; `domain` depends on nothing outside stdlib.
  - **ADR-0003** — TDD mandatory with strict RED → GREEN → REFACTOR for every new behavior; CI enforces coverage thresholds (≥90% domain/application, ≥80% global).
  - **ADR-0004** — SDD + OpenSpec pre-code gate already satisfied by SPEC-001 existing; apply/verify/archive phases follow.
  - **ADR-0005** — local-first: all NLP processing (none in this cycle) and all test data remain on-device; `/health` response is purely in-memory.
  - **ADR-0006**, **ADR-0007**, **ADR-0009** — linguistic model ADRs. Not directly exercised in this cycle; their entities do NOT land here (DEC-005).
  - **ADR-0008** — multi-language scope. Not directly exercised, but the layer structure must not hard-code English-only assumptions even in the empty skeleton.
  - **ADR-0010** — methodology artifacts (this file, proposal, spec, design, tasks, ADRs) in English; product-facing (README, AGENTS.md, constitution) in Spanish.

---

## 2. Current State

### Repository baseline

As of 2026-07-20, the repository contains **zero production code**. A `glob` for `*.py` and `*.ts` returns no results. The directory tree is:

```
.atl/              ← skill registry (methodology)
.git/
.gitignore         ← pre-configured (Python + Node + .env patterns)
AGENTS.md
docs/              ← full methodology suite (constitution v2.0.0, 10 ADRs, glossary, etc.)
openspec/          ← SDD artifact store (config.yaml, archive for docs-methodology-overhaul)
  archive/         ← completed cycle archive
  changes/         ← active change spool (currently empty except README)
  config.yaml
README.md
specs/             ← SPEC-001 suite (all 7 files, status: "Lista para implementación")
templates/
```

The `.gitignore` already excludes `.env`, `node_modules/`, `.venv/`, build caches, and coverage output. It does NOT yet gitignore `openspec/changes/` (policy deferred, per archive-report §8 post-cycle decision #1).

`openspec/config.yaml` sets `stack.status: not-implemented` and warns that all test commands will error until code exists. `strict_tdd: true` is in force.

Engram #2413 confirms the testing capability state: `strict_tdd: false, reason: no_test_runner_detected` — this is the **runtime detection** result (no executable test runner found yet), which is distinct from the **policy** (`strict_tdd: true` in config). The exploration cannot run tests because no tests exist. The proposal and tasks phases must account for this bootstrapping gap explicitly (see §4 Risks).

### What SPEC-001 commits to on paper

SPEC-001 (`specs/001-project-foundation/spec.md`, version 1.0.0, status "Lista para implementación") defines **18 functional requirements** and **6 non-functional requirements**:

| REQ ID | One-line intent |
|--------|----------------|
| REQ-001-001 | FastAPI backend startable via a documented command |
| REQ-001-002 | `GET /api/v1/health` returns `{"status":"ok","service":"wheel-vocabulary-api","version":"0.1.0"}` |
| REQ-001-003 | React + TypeScript frontend startable via a documented command |
| REQ-001-004 | Frontend polls health endpoint and shows loading / available / unavailable states with retry |
| REQ-001-005 | Backend connects to SQLite via a configurable URL |
| REQ-001-006 | Alembic configured with a verifiable initial migration |
| REQ-001-007 | Configuration read from environment variables; `.env.example` committed (no secrets) |
| REQ-001-008 | Unified Makefile commands: `install`, `dev`, `test`, `lint`, `typecheck`, `format`, `e2e`, `migrate` |
| REQ-001-009 | ≥1 backend unit test, ≥1 API test, ≥1 SQLite integration test |
| REQ-001-010 | Frontend component tests for loading, available, unavailable, and retry states |
| REQ-001-011 | Playwright E2E: open app, verify integrated health state |
| REQ-001-012 | Backend passes Ruff and mypy with agreed strict configuration |
| REQ-001-013 | Frontend passes TypeScript compiler and linter |
| REQ-001-014 | GitHub Actions CI: install, lint, types, backend tests, frontend tests, E2E, migrations on every PR |
| REQ-001-015 | Backend directory structure: `domain/`, `application/`, `infrastructure/`, `api/` — no fictitious domain logic |
| REQ-001-016 | README explains requirements, install, start, tests, quality, migrations, and structure |
| REQ-001-017 | No copyrighted book text in the repository |
| REQ-001-018 | `.env`, local DBs, imported files, coverage, caches, secrets, and generated exports gitignored |
| REQ-001-NF-001 | Locked dependency files (lockfiles) |
| REQ-001-NF-002 | Unit tests provide fast feedback on normal hardware |
| REQ-001-NF-003 | Tests do not depend on public network |
| REQ-001-NF-004 | Application works in recent Chromium (MVP target) |
| REQ-001-NF-005 | Status screen uses visible text and accessible regions, not only color |
| REQ-001-NF-006 | Configuration centralized and documented |

### What is explicitly IN scope for SPEC-001 (§3)

- Monorepo skeleton
- FastAPI backend
- React + TypeScript + Vite frontend
- SQLite with SQLAlchemy and Alembic
- Health endpoint and status screen
- Minimum unit, integration, and E2E tests
- Ruff, mypy, Vitest, Testing Library, Playwright quality tooling
- Makefile
- Example environment variables
- GitHub Actions CI
- Bootstrap documentation

### What is explicitly OUT of scope (§4)

- Book import
- Tokenization or lemmatization
- Part-of-speech categories
- Phrasal verbs (any language-specific MWE)
- Anki export
- Authentication
- Production deployment
- PostgreSQL

---

## 3. Gap Analysis — SPEC-001 vs. Constitution v2.0.0 + ADRs 0001–0010

SPEC-001 was written on 2026-07-15 alongside the Constitution v1.0.0 and ADR-0001. The methodology wave (ADRs 0002–0010 and Constitution v2.0.0) landed on 2026-07-16. The gap analysis below checks every REQ, decision, task, and acceptance criterion in SPEC-001 against the current normative framework.

> **Legend**: Impact: `none` (no change needed), `minor` (refresh is beneficial but not blocking), `major` (materially affects scope or technical approach), `blocking` (must be resolved before propose).

| Item | SPEC-001 says | Constitution v2.0.0 / ADR says | Impact | Recommendation |
|------|---------------|-------------------------------|--------|----------------|
| **Package manager — Python** | T009: "Configurar Python con `uv`"; plan.md §3 uses `uv` implicitly | ADR-0001: `uv` explicitly named as the Python package manager | none | keep-as-is — aligned |
| **Package manager — JS** | spec §3/§6 assumptions: "Node.js LTS y pnpm" (§6); plan.md §7 "cachés de `uv` y pnpm" | ADR-0001: `pnpm` explicitly listed as frontend package manager | none | keep-as-is — aligned |
| **Test runner — backend** | test-plan.md uses pytest (UT-BE-*, API-BE-*, INT-BE-*, E2E framework); plan.md §7 "pytest y cobertura" | ADR-0001: pytest + Hypothesis listed; ADR-0003: pytest is the de-facto runner per `openspec/config.yaml` `unit: uv run pytest` | none | keep-as-is — aligned |
| **Test runner — frontend** | test-plan.md §4 UT-FE-* use Vitest + Testing Library; plan §6 "TypeScript, linter y Vitest" | ADR-0001: Vitest + Testing Library explicitly listed | none | keep-as-is — aligned |
| **E2E runner** | test-plan.md §6 E2E-001 uses Playwright; plan §7 "Playwright con Chromium" | ADR-0001: Playwright explicitly listed | none | keep-as-is — aligned |
| **Hexagonal layer names** | REQ-001-015: `domain/`, `application/`, `infrastructure/`, `api/` verbatim; plan.md §2 structure diagram | ADR-0002: "exactly four named layers: `domain`, `application`, `infrastructure`, and `api`" verbatim | none | keep-as-is — perfectly aligned |
| **Domain purity** | REQ-001-015: "sin introducir lógica de dominio ficticia"; DEC-005: domain entities deferred | ADR-0002: "domain has zero imports from FastAPI, SQLAlchemy, spaCy, or any third-party library" | none | keep-as-is — aligned; DEC-005 is the correct operationalization of ADR-0002 for a bootstrap |
| **TDD ordering in tasks** | tasks.md Phase B: T008 [TEST] → T010 [IMPL] → T011 [REFACTOR]; similar for T012/T013/T014/T015/T016 and frontend phases | ADR-0003: "Every new behavior MUST begin with a RED test" | none | keep-as-is — tasks already sequence [TEST] → [IMPL] → [REFACTOR] correctly |
| **TDD bootstrap exception** | T009 [IMPL] "Configurar Python con `uv`" precedes any test; T003/T004/T005/T006 are infrastructure tasks with no preceding test | ADR-0003 / Constitution Art. II.1: "cada comportamiento nuevo debe comenzar con una prueba que falle." Infrastructure scaffolding tasks (creating lockfiles, Makefile, .gitignore) are not *behaviors* in the TDD sense — they are prerequisites. However, ADR-0003 says "No implementation may precede a failing test" and specifically discusses this for config: "Aligns with `openspec/config.yaml` `strict_tdd: true` flag" | **minor** | refresh-in-spec-phase — explicitly document in spec and tasks that Phases A (repo scaffold) and the first half of B (T009 toolchain setup) are **bootstrap prerequisites**, not behaviors; the first RED test (T008 / T014) can only run once the test runner itself is installed. The Constitution does not prohibit setting up the test runner before writing the first test — it prohibits writing implementation of a *behavior* before its test. Clarifying this boundary in spec/design/tasks will prevent confusion during apply. |
| **Coverage targets** | test-plan.md §9: "se alcanzan umbrales de cobertura"; no specific numbers stated | ADR-0003: domain/application ≥90%, global ≥80%; `openspec/config.yaml` `coverage_threshold: 80` | **minor** | refresh-in-spec-phase — the test-plan should state the exact thresholds verbatim from ADR-0003 to eliminate ambiguity during verify |
| **CI provider and jobs** | plan.md §7: 6 jobs named (backend-quality, backend-tests, frontend-quality, frontend-tests, migration-check, e2e); REQ-001-014: "GitHub Actions" | ADR-0001: "GitHub Actions" explicitly | none | keep-as-is — aligned; the six-job structure is an implementation detail that does not contradict any ADR |
| **Endpoint path and contract** | REQ-001-002 / acceptance.md AC-001 / test-plan.md API-BE-001: `GET /api/v1/health` responding `{"status":"ok","service":"wheel-vocabulary-api","version":"0.1.0"}` | ADR-0001 and ADR-0002 do not prescribe an endpoint path; Constitution Art. VII.4 ("API HTTP no contiene reglas de negocio") is satisfied by a health endpoint | none | keep-as-is — path is internally consistent across spec, acceptance, test-plan, and traceability |
| **Frontend framework** | spec §3: React + TypeScript + Vite; DEC-001: "React con Vite (no SSR, no Node backend)" | ADR-0001: React + TypeScript + Vite + TanStack Query | none | keep-as-is — aligned; TanStack Query is included in plan.md §4 frontend section |
| **Migration tool** | REQ-001-006: Alembic; spec §3: "SQLite con SQLAlchemy y Alembic"; plan §3 persistence section | ADR-0001: Alembic explicitly listed | none | keep-as-is — aligned |
| **SQLAlchemy version** | plan.md §3: "SQLAlchemy 2" | ADR-0001: "SQLAlchemy 2" explicitly | none | keep-as-is — aligned |
| **DEC-002 SQLite** | decisions.md DEC-002: "Favorece local-first, instalación mínima y migración futura mediante SQLAlchemy" | ADR-0005: local-first processing; ADR-0001: SQLite as MVP persistence | none | keep-as-is — DEC-002 is the SPEC-001 echo of ADR-0005 for the persistence tier; fully consistent |
| **DEC-004 OpenAPI as contract** | decisions.md DEC-004: "El contrato backend-frontend se derivará de OpenAPI" | ADR-0002: "Frontend-backend contract remains at the `api` layer boundary"; Constitution Art. VII.4–5 | none | keep-as-is — OpenAPI is the correct mechanism for the api-layer contract |
| **REQ-001-004 health screen text** | spec §10: states loading/available/unavailable; AC-003: "ve 'Backend disponible'"; AC-004: "ve 'Backend no disponible'" | ADR-0010: UI copy follows product-facing language (ES); Constitution Art. IX.3 (loading/success/error perceptible) | none | keep-as-is — Spanish UI strings are correct per ADR-0010 §3 (product-facing); accessible text per Art. IX |
| **REQ-001-007 wording vs ADR-002 hexagonal layer check** | REQ-001-007 in traceability.md maps to AC-007 ("Configuración segura — .env.example, no credentials, .env gitignored"); but the REQ-001-007 in spec.md is about configuration (env vars + .env.example), NOT about hexagonal structure | The top-level traceability matrix (`docs/traceability-matrix.md`) row for REQ-001-007 says "El dominio no contiene imports de frameworks; arquitectura hexagonal validable" — mapping it to AC-007 — but in `specs/001-project-foundation/spec.md`, REQ-001-007 is about **configuration** (env vars), and AC-007 is about **configuration security** (not hexagonal architecture). REQ-001-015 is the actual hexagonal-structure requirement | **major** | refresh-in-spec-phase — **The top-level traceability matrix has a mis-mapped row**: it labels REQ-001-007 as the hexagonal requirement and references AC-007, but in the spec itself REQ-001-007 is the configuration requirement and AC-007 is the `.env` security criterion. The hexagonal requirement is REQ-001-015; the tests UT-BE-001/UT-BE-002 in the matrix row actually belong to configuration, not hexagonal validation (they test `Settings`). The matrix must be corrected: the REQ-001-007 row should say "Configuración se lee de variables de entorno; .env.example sin secretos" with AC-007, and a separate REQ-001-015 row should be added. This is a documentation drift, not a behavioral conflict — no ADR is violated — but it WILL cause verify-phase confusion if left uncorrected. |
| **spec §4 "Phrasal verbs" in non-goals** | spec.md §4 lists "Phrasal verbs" as explicitly out of scope | ADR-0009: phrasal verbs are `mwe_kind: "phrasal_verb"` — the English instance of "expresiones multipalabra específicas del idioma"; ADR-0008: multi-language scope from day one | **minor** | refresh-in-spec-phase — the non-goal is correct in intent (no linguistic domain logic in the bootstrap), but the phrasing should be updated to "Expresiones multipalabra específicas del idioma (incluyendo phrasal verbs)" to align with ADR-0009 canonical terminology. Failing to update this will create a terminology mismatch between SPEC-001 non-goals and future specs that use the canonical term. This is non-blocking for bootstrap itself (it's an out-of-scope item) but should be cleaned up during the spec-refresh sub-task. |
| **Multi-language scope impact on bootstrap** | SPEC-001 was written under Constitution v1.0.0 (English-only). The bootstrap creates an empty directory structure | ADR-0008: "the architecture is multi-language by design from day one; adding a new language requires only a new NLP adapter"; the hexagonal skeleton must not hard-code English assumptions | **minor** | refresh-in-spec-phase — there is no code yet, so no hard-coding has occurred. However, the spec and tasks should add a note in REQ-001-015 or plan §2 explicitly stating that the `domain/`, `application/`, etc. directories must not contain English-specific naming conventions or assumptions in their initial scaffold. This guards the apply phase from inadvertently introducing language-specific file names. |
| **ADR-0010 language policy: tasks.md language** | SPEC-001 all files are in Spanish (task names, requirement descriptions, acceptance scenarios) | ADR-0010: `AGENTS.md` classified as product-facing (ES); specs in `specs/` — no explicit ruling. The constitution and AGENTS.md are ES; methodology artifacts (ADRs, architecture-baseline, traceability-matrix) are EN. Per ADR-0010 §4: "mixed artifacts follow the scaffold language." The SPEC-001 suite uses Spanish throughout, which is consistent with being a product-facing artifact. | none | keep-as-is — SPEC-001 is a product/feature spec; Spanish is appropriate per ADR-0010 |
| **openspec/config.yaml strict_tdd flag** | ADR-0003 references `strict_tdd: true`; but Engram #2414 reports `strict_tdd: false, reason: no_test_runner_detected` at runtime | `openspec/config.yaml` line 31: `strict_tdd: true` is the policy declaration; runtime detection showing `false` is the Engram capability-cache value reflecting "no test runner is installed yet" — not a conflict with the policy | **minor** | refresh-in-spec-phase — the proposal should explicitly document this distinction: `strict_tdd: true` (policy) vs. `no_test_runner_detected` (current runtime state). Tasks must install the test runner as a prerequisite before any RED test can be written. No ADR conflict exists. |
| **Task T024 [IMPL] "Crear capas del backend"** | tasks.md T024: labeled [IMPL], creating empty directories | ADR-0003: [IMPL] tasks must follow a RED test in TDD. Empty directory creation is pure scaffolding, not a behavior. | **minor** | refresh-in-spec-phase — T024 should be typed [SPEC] or [DOC] or left as [IMPL] with an explicit note that creating empty directories is bootstrap scaffolding, not a behavior requiring a preceding test. The tasks phase can resolve this cleanly. |

### Summary by severity

| Severity | Count | Items |
|----------|-------|-------|
| `none` (no change needed) | 14 | Toolchain stack, layer names, domain purity, TDD ordering, CI jobs, endpoint path/contract, frameworks, migration tool, SQLAlchemy version, DEC-002, DEC-004, UI text language, multi-language impact on bootstrap (no code yet), ADR-0010 language |
| `minor` (refresh in spec phase) | 7 | TDD bootstrap exception wording, coverage threshold numbers in test-plan, traceability matrix — REQ-001-015 missing row, phrasal-verb non-goal wording, multi-language skeleton note, strict_tdd policy vs runtime state documentation, T024 task type |
| `major` (doc drift, no behavior conflict) | 1 | Top-level `docs/traceability-matrix.md` REQ-001-007 row mis-maps to hexagonal requirement instead of configuration requirement |
| `blocking-must-amend-first` | **0** | None |

**No blocking discrepancy was found.** SPEC-001 is substantively compatible with Constitution v2.0.0 and all ten ADRs. The one `major` finding is a documentation drift in the top-level traceability matrix (not in the spec itself) that must be corrected during the spec phase of this cycle.

---

## 4. Bootstrap Risk Landscape

### Risk 1 — The TDD chicken-and-egg (HIGH severity)

**The problem**: ADR-0003 and Constitution Art. II.1 state that "every new behavior introduced to the codebase MUST begin with a RED test." But a RED test requires a test runner. The test runner (`pytest`, `Vitest`, `Playwright`) does not exist until `uv` installs it, `pnpm` installs it, and the project scaffolding is in place. The Engram #2414 capability snapshot confirms this: `strict_tdd: false, reason: no_test_runner_detected`.

**What the Constitution actually permits**: Art. II.1 says "cada comportamiento nuevo debe comenzar con una prueba que falle." Setting up a build tool, a package manager, a virtual environment, and an empty directory structure is not a *behavior* — it is infrastructure. The Constitution does not prohibit creating the hammer before driving the first nail. ADR-0003 confirms: "The minimum sufficient implementation is written to turn the RED test GREEN." A project that has no test runner cannot write a failing test — writing the test runner installer is the first act.

**The SDD-compliant sequence**: The following tasks are **bootstrap prerequisites** (no preceding RED test required because there is nothing to test yet):

1. Create `.gitignore` additions, Makefile skeleton, `.env.example` (no behaviors, pure scaffolding).
2. `uv sync` / `pyproject.toml` setup to install `pytest`. This is prerequisite infrastructure.
3. Create the empty four-layer directory structure.
4. The first executable RED test (T008 — `Settings` configuration validation) is then the first TDD act.

Everything after the test runner is installed must follow strict RED → GREEN → REFACTOR. The spec and tasks should make this boundary explicit to avoid ambiguity during the apply phase. If the apply agent writes `Settings` code before T008's RED test runs, that is a TDD violation. If the apply agent sets up `uv` before T008, that is not a TDD violation — it is the bootstrap.

**The same logic applies to the frontend**: `pnpm install` and `vite.config.ts` scaffold are bootstrap prerequisites; the first `Vitest` RED test (T027 — loading state) is the first frontend TDD act.

### Risk 2 — Cross-ecosystem coupling (MEDIUM severity)

The cycle touches five distinct technical surfaces: Python/FastAPI backend, SQLAlchemy/Alembic, React/Vite frontend, GitHub Actions CI, and the Makefile glue. Each surface has its own failure modes. The key coupling risks are:

- **Health endpoint E2E**: Playwright (frontend) depends on both the backend server and the frontend dev server being alive during the test. This is the single most complex integration point and the one most likely to produce flaky CI behavior.
- **Migration check in CI**: Alembic's `upgrade head` from an empty database must succeed as a separate CI job. This is independent of tests but must not depend on the Python tests job having passed first (it can run in parallel with `backend-tests`).
- **`uv` cache in CI**: GitHub Actions caching for `uv` requires the `uv.lock` file to exist before the cache key is computed. If the lock file is not committed in the first bootstrap PR, CI will miss the cache on every run. The `uv.lock` file must land in the same commit as `pyproject.toml`.

**Safe split points**: Backend Python (Phases A+B), frontend JS (Phase C), and CI (Phase F) can be delivered in chained PRs. The integration point (E2E test, Phase E) should be the last PR, since it requires both servers to be running.

**Unsafe split**: Attempting to land the Alembic migration without having `uv` / `pyproject.toml` first, or landing frontend tests without a working backend contract — these pairs must always land together.

### Risk 3 — Reproducibility: `uv` vs. legacy poetry references (LOW severity)

SPEC-001 (written 2026-07-15) consistently references `uv` in tasks.md (T009: "Configurar Python con `uv`") and plan.md §7 ("cachés de `uv` y pnpm"). ADR-0001 names `uv` explicitly. No reference to `poetry` was found in any SPEC-001 file. This risk is **not realized** — SPEC-001 and ADR-0001 are in agreement on `uv`. However, if any agent or collaborator manually reaches for `poetry` (a common Python reflex), the resulting `poetry.lock` would conflict with the expected `uv.lock`. The spec phase should explicitly state that `poetry` must not be used.

### Risk 4 — Local-first compliance for the health endpoint (LOW severity)

ADR-0005 and Constitution Art. IV.4–5 require local-first processing. The `/health` endpoint does not contact any external service — it returns a static JSON payload. Risk is essentially zero. However, the initial Alembic migration creates a local SQLite file. CI must use an in-memory or temp-dir SQLite to avoid state leakage between runs. The test-plan already specifies this (INT-BE-001: "SQLite temporal"; CI item: "Alembic sobre base vacía"). No additional constraint is needed.

The health-status frontend screen calls `GET /api/v1/health` on the same host — this is not third-party egress. ADR-0005 is satisfied.

### Risk 5 — Non-goals safety: what must NOT sneak in (HIGH severity for apply)

SPEC-001 §4 non-goals are explicit. The apply phase MUST enforce these hard boundaries:

- **No domain entities**: No `Lexeme`, `Occurrence`, `WordForm`, `PartOfSpeech`, `ManualCorrection`, `MultiwordExpression` in any Python file. The `domain/` directory is created empty (or with a `__init__.py` and a `README`/`.gitkeep`).
- **No NLP imports**: No `spaCy`, `stanza`, or any NLP library in `pyproject.toml` yet.
- **No book import logic**: No `TextExtractor`, no file upload endpoint.
- **No linguistic rules in frontend**: The `BackendState` union type is a UI state machine; it must not encode linguistic concepts.

The apply agent must check against these boundaries before committing. A temptation exists to "pre-scaffold" domain entities because the architecture is known — this is the "anticipatory scaffolding" that Art. II (TDD) and Art. VII.6 (no speculative abstraction) forbid.

---

## 5. Slice Plan Proposal

The 18 functional REQs and 62 tasks in SPEC-001 are substantial for a single PR delivery (estimated 600–900+ lines of new code, config, and tests). This exceeds the 400-line review budget by a significant margin. The slice plan below decomposes the work into four coherent chained PRs.

### Slice A — Repository scaffold and Python toolchain bootstrap

**Intent**: Create the monorepo skeleton, `.gitignore` additions, Makefile, `.env.example`, `pyproject.toml`, `uv.lock`, and the empty four-layer directory structure. This is the bootstrap-prerequisite slice that makes subsequent RED tests possible.

**REQs satisfied (partial)**: REQ-001-007 (partial — `.env.example`), REQ-001-008 (partial — Makefile skeleton), REQ-001-015 (partial — empty layer directories), REQ-001-017, REQ-001-018, REQ-001-NF-001 (backend lockfile), REQ-001-NF-006.

**Tasks from SPEC-001**: T001–T007, T009, T024–T025 (partial).

**Estimated changed lines**: S (50–120 lines). Pure configuration, no behavioral code, no tests for behavior (bootstrap).

**Dependencies**: None. This is the root slice.

**Exceeds 400-line budget?** No.

**Layers touched**: Backend tooling / Infra / Docs.

---

### Slice B — Backend TDD: Settings → HealthResponse → `/health` → SQLAlchemy → Alembic

**Intent**: Full Python backend implementation in strict TDD order: Settings config → HealthResponse model → FastAPI factory + `/health` route → SQLAlchemy engine → Alembic initial migration. Includes backend unit, API, and integration tests.

**REQs satisfied**: REQ-001-001, REQ-001-002, REQ-001-005, REQ-001-006, REQ-001-007 (complete), REQ-001-009, REQ-001-012, REQ-001-NF-001 (verified), REQ-001-NF-003.

**Tasks from SPEC-001**: T008–T023, T045–T046 (Ruff/mypy config), T025 (docs for layer limits), partial T059/T062.

**Estimated changed lines**: M–L (250–450 lines). Python source + tests + Alembic migration + pyproject.toml config for Ruff/mypy.

**Dependencies**: Slice A (requires `uv`, `pyproject.toml`, and directory structure).

**Exceeds 400-line budget?** Potentially yes (upper end). If it lands at 400+ lines, it MUST be sub-split: B1 (Settings + HealthResponse + factory + route, ~200 lines) and B2 (SQLAlchemy + Alembic + integration tests, ~200 lines).

**Layers touched**: Backend (domain stub, api, infrastructure/db).

---

### Slice C — Frontend TDD: React bootstrap + BackendStatus component + contract validation

**Intent**: Initialize React + Vite + TypeScript project; implement `BackendStatus` component in TDD order (loading → available → unavailable → retry); add accessibility tests; validate `HealthResponse` contract.

**REQs satisfied**: REQ-001-003, REQ-001-004, REQ-001-010, REQ-001-013, REQ-001-NF-004, REQ-001-NF-005.

**Tasks from SPEC-001**: T026–T039, T047–T048.

**Estimated changed lines**: M–L (300–450 lines). TypeScript source + Vitest tests + Vite/TS config + `package.json` + `pnpm-lock.yaml`.

**Dependencies**: Slice A (Makefile, monorepo structure). Conceptually independent of Slice B, but the contract test (T037–T038) needs the OpenAPI spec from Slice B's `/health` endpoint. If B and C are developed in parallel, the contract test can use a pinned snapshot of the OpenAPI schema; otherwise C follows B.

**Exceeds 400-line budget?** Potentially yes (upper end). The `pnpm-lock.yaml` lockfile alone can add hundreds of lines but is typically excluded from review-line counting (generated file). If counting only authored lines (TS + test + config), estimate is M (200–350 lines). Reviewer burn-out is low risk if lockfiles are excluded.

**Layers touched**: Frontend.

---

### Slice D — E2E + CI + README

**Intent**: Configure Playwright; write the E2E health-check test; create GitHub Actions workflows (6 jobs); complete README with all documented commands; final security sweep (secrets, .gitignore audit); close traceability matrix.

**REQs satisfied**: REQ-001-008 (complete), REQ-001-011, REQ-001-014, REQ-001-016, REQ-001-NF-002 (verified in CI), remaining REQ-001-NF-*.

**Tasks from SPEC-001**: T040–T044 (E2E), T049–T054 (CI), T055–T060 (closure).

**Estimated changed lines**: S–M (100–200 lines). YAML workflows + Playwright config + README + docs updates.

**Dependencies**: Slices B and C must be complete (CI jobs must have working test commands). This is the integration slice.

**Exceeds 400-line budget?** No.

**Layers touched**: CI / Docs / Infra.

---

### Forecast vs 400-line budget

| Slice | Est. lines (authored) | Status |
|-------|----------------------|--------|
| A | 50–120 | Under budget |
| B | 250–450 | Conditional — sub-split if >400 |
| C | 200–350 (excl. lockfile) | Conditional — likely under budget |
| D | 100–200 | Under budget |
| **Total** | **600–1120** | **Exceeds 400 in aggregate** |

**The sum of the slice plan WILL trigger the `ask-on-risk` guard.** The total aggregate across all slices is estimated at 600–1120 authored lines, well above the 400-line single-PR budget. However, the plan proposes **four chained PRs** rather than one, so no individual PR is expected to exceed 400 lines. The Slice B upper bound (450 lines) is the only individual risk; it should be sub-split if it lands there.

### Recommended delivery shape

**Four chained PRs: A → B → C → D** (optionally B sub-split into B1 + B2 if backend grows beyond 400 lines).

Justification:
1. Each slice produces a directly verifiable result (A: tooling works; B: `make test` green; C: `make test` frontend green + component tests; D: `make e2e` green + CI green).
2. No single PR exceeds 400 lines under the proposed split (with the B caveat).
3. The chain strategy matches the "cortes verticales" principle of Art. III.
4. The alternative — a single PR for the entire bootstrap — would be 600–1100+ lines and would guarantee reviewer burn-out and verify-phase complexity.
5. Splitting into more than four PRs (e.g., one per phase of SPEC-001) is also possible but produces very small PRs with incomplete observable results; four is the sweet spot for this scale.

**Do NOT split across two SDD cycles.** The entire bootstrap is SPEC-001's scope; two cycles would create an incomplete spec in the middle, violating the traceability requirement (Art. XI).

---

## 6. Open Questions for the Proposal Phase

The following questions are for the human maintainer to confirm before `sdd-propose` writes the proposal. They are about product/architecture scope, not test harness mechanics.

1. **Should Slice B be split into B1 (Settings + health route) and B2 (SQLAlchemy + Alembic)?** The estimated 250–450 line range makes this a judgment call. If the maintainer prefers consistent sub-400-line PRs, B1/B2 is the right call. If slightly larger PRs are acceptable for backend-only work, B can remain one PR.

2. **`pyproject.toml` monorepo shape**: Should the backend live at `apps/api/pyproject.toml` (plan.md §2 structure) or at the repo root (`pyproject.toml` with workspace members)? ADR-0001 says monorepo but does not prescribe the `uv` workspace layout. This must be decided before Slice A, because it affects all path references in Makefile, CI, and imports.

3. **Makefile or `uv` scripts for the unified command interface (REQ-001-008)?** SPEC-001 plan.md prescribes a `Makefile`. ADR-0001 lists `Makefile` in "Automatización." Should the Makefile delegate to `uv run` commands, or should `uv` scripts in `pyproject.toml` be the primary interface with Makefile as a thin wrapper?

4. **Initial Alembic migration content**: SPEC-001 plan §3 says "La migración inicial puede crear `app_metadata`". Is `app_metadata` the desired table name, or should the initial migration be a no-op schema version pin? This determines what the migration test verifies.

5. **TypeScript + ESLint configuration level**: Strict TypeScript (`strict: true` in tsconfig) is specified in REQ-001-013. Which ESLint ruleset should be the baseline — `@typescript-eslint/recommended-type-checked`, or a lighter preset? This affects the volume of lint errors in Slice C.

6. **GitHub Actions runner OS**: `ubuntu-latest`, a specific Ubuntu version, or also `macos-latest`? SPEC-001 §6 assumptions say "Linux, macOS or WSL" but CI jobs should target a specific OS to avoid non-determinism. Ubuntu latest is the standard; should macOS be added for E2E stability?

7. **Playwright browser target**: test-plan §7 says "Chromium". Should only Chromium be configured in `playwright.config.ts`, or also Firefox/WebKit as optional? Keeping Chromium-only minimizes flakiness risk for the first E2E suite.

8. **Coverage threshold enforcement in CI**: `openspec/config.yaml` sets `coverage_threshold: 80`. Should this be enforced as a hard CI gate from Slice B (failing the build), or soft (warning) until the full suite is in place?

9. **Docker Compose scope**: DEC-006 says Docker is optional. Should Slice D include a `docker-compose.yml` skeleton, or defer entirely to a future maintenance task? Including it in Slice D keeps the bootstrap complete; excluding it keeps Slice D leaner.

10. **Traceability matrix correction timing**: The `docs/traceability-matrix.md` REQ-001-007 row must be corrected (it currently misidentifies REQ-001-007 as the hexagonal requirement). Should this correction land in a pre-cycle docs fix commit, or as part of Slice D's documentation tasks? Fixing it early avoids confusion during apply; fixing it in Slice D keeps the cycle atomic.

---

## 7. Recommendation

**Proceed to `sdd-propose`** with the four-slice delivery plan (A → B → C → D, B optionally sub-split) and the ten open questions above. No blocking discrepancy was found between SPEC-001 and the current normative framework (Constitution v2.0.0, ADRs 0001–0010). The spec is substantively correct and implementable as-is; the seven `minor` drift items and one `major` documentation drift (traceability matrix REQ-001-007 row) should be addressed in the spec-phase refresh sub-task for this cycle, not as pre-conditions to proposing. The bootstrap risk landscape is well-understood and manageable: the TDD chicken-and-egg is resolved by the bootstrap-prerequisite exception; the cross-ecosystem coupling is addressed by the chained-slice strategy; and the 400-line reviewer budget is respected by delivering four PRs instead of one. The project is in a clean state (zero production code, complete methodology documentation, no conflicts) and is structurally ready for its first code-touching cycle.

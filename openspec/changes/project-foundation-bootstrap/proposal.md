# Proposal — project-foundation-bootstrap

**Change slug:** `project-foundation-bootstrap`
**Date:** 2026-07-20
**Cycle type:** First code-touching cycle. Operationalizes SPEC-001 (`specs/001-project-foundation/`), which was already validated against Constitution v2.0.0 and ADRs 0001–0010 during exploration. No new capability is authored here; every REQ, AC, plan step, test-plan case, and task in SPEC-001 becomes deliverable code, config, tests, and CI.
**Target spec:** SPEC-001 — 18 functional REQs (REQ-001-001..018) + 6 non-functional REQs (REQ-001-NF-001..006), 15 acceptance criteria (AC-001..015), 7 test-plan sections (UT-BE-*, API-BE-*, INT-BE-*, UT-FE-*, A11Y-FE-*, CONTRACT-*, E2E-*), and 62 tasks (T001–T062) across seven phases.
**Constitution version bound:** v2.0.0.
**Persistence mode:** `openspec` (per session preflight) with Engram companion via topic `sdd/project-foundation-bootstrap/proposal`.
**Delivery strategy:** `ask-on-risk` (default; already triggered by aggregate forecast).
**Branch strategy:** `feature-branch-chain` on tracker branch `project-foundation-bootstrap`. Only the tracker branch merges to `main`, at cycle close.
**Review budget:** 400 authored lines per PR (lockfiles and generated Alembic migration scripts excluded from authored-line accounting; still included in complete-snapshot review).
**Preceded by:** `openspec/changes/project-foundation-bootstrap/explore.md` (352 lines, Engram #2415) and `sdd/wheel-of-words/testing-capabilities` (Engram #2414: `strict_tdd: false` runtime, `strict_tdd: true` policy).

---

## 1. Intent — why this cycle exists

This cycle turns the repository from a documentation-only baseline into an executable project for the first time. Every artifact required by SPEC-001 exists on paper; none of them execute. The exploration confirmed zero blocking discrepancies between SPEC-001 and Constitution v2.0.0 + ADRs 0001–0010. The cycle's single-sentence goal, phrased against Constitution Art. XI (Definition of Done) and SPEC-001 §2 (Objetivo), is: **a developer can clone, install, run, test, lint, type-check, migrate, and see a green frontend-to-backend `/health` round trip, with all quality gates enforced in CI, following only the documented commands.** Nothing linguistic lands. The domain layer is created but stays empty per DEC-005 and Constitution Art. VII.6 (no speculative abstraction).

---

## 2. Scope — what this cycle DELIVERS

Enumerated by outcome, not by file. Each bullet ties back to a SPEC-001 requirement family. Full requirement-to-task mapping is the spec-phase deliverable, not the proposal's.

- **Python project bootstrap.** `uv`-managed backend (ADR-0001), `pyproject.toml`, `uv.lock`, four-layer directory structure (`domain/`, `application/`, `infrastructure/`, `api/`) per ADR-0002 and REQ-001-015, Ruff + mypy strict configuration per REQ-001-012 and Art. VIII.1, pytest + Hypothesis test infrastructure per ADR-0001 and REQ-001-NF-002. End state: pytest is installed and runnable, unlocking the flip of `sdd/wheel-of-words/testing-capabilities` from `strict_tdd: false` (runtime) to `strict_tdd: true` (runtime) at cycle close. The policy declaration in `openspec/config.yaml` (`strict_tdd: true`) becomes actionable, not aspirational.
- **Backend health endpoint.** `GET /api/v1/health` per REQ-001-002 and AC-001. The exact JSON body is pinned by SPEC-001 §7 (REQ-001-002 quotes the payload verbatim); the proposal will not restate or renegotiate that contract. `Settings` (pydantic-settings), `HealthResponse` model, and FastAPI factory per plan.md §3 (DEC-003) satisfy REQ-001-001, REQ-001-007, REQ-001-NF-006.
- **SQLAlchemy 2 + Alembic wiring with SQLite.** Engine and session factories in `infrastructure/`, Alembic configured with an initial baseline migration per REQ-001-005, REQ-001-006, AC-005, AC-006, DEC-002, and ADR-0005. The initial migration may be an empty-schema revision or an `app_metadata` version-pin table (see §7 ASSUMPTION-4); no domain tables land — DEC-005 forbids it.
- **Frontend bootstrap.** pnpm + Vite + React + TypeScript strict (REQ-001-013, ADR-0001), `BackendStatus` state machine (`idle → loading → available | unavailable` per SPEC-001 §10) with retry (REQ-001-004, AC-004), Vitest + Testing Library test infrastructure (REQ-001-010), health-endpoint client using TanStack Query per plan.md §4. Accessibility per REQ-001-NF-005 and Art. IX.3–4 (text, not color alone; accessible retry button).
- **Playwright E2E covering the health screen round trip.** Chromium target per test-plan §7, `E2E-001` scenario per SPEC-001 §12 and AC-011. Playwright `webServer` config manages backend + frontend lifecycle to avoid arbitrary sleeps per plan.md §10 risk item.
- **GitHub Actions CI wiring the full quality gate.** Six-job structure per plan.md §7: `backend-quality`, `backend-tests`, `frontend-quality`, `frontend-tests`, `migration-check`, `e2e`. Enforces REQ-001-014, REQ-001-NF-003 (no public-network dependence per Art. VI.5 and ADR-0005). `uv` and `pnpm` cache keys anchored to `uv.lock` / `pnpm-lock.yaml` per §8 Risk 2 discussed in exploration.
- **Makefile, `.env.example`, developer bootstrap documentation.** Unified command surface `install / dev / test / lint / typecheck / format / e2e / migrate` per REQ-001-008 and AC-008. `.env.example` with no secrets per REQ-001-007 and AC-007. README covers requisitos, instalación, arranque, pruebas, calidad, migraciones y estructura per REQ-001-016 and AC-015. Spanish UI copy for the status screen per ADR-0010 (product-facing = ES) and Art. IX.3.
- **`.gitignore` audit.** `.env`, local DBs, imported files, coverage, caches, secrets, and generated exports per REQ-001-018 and AC-007/AC-013. No copyrighted texts per REQ-001-017 and Art. IV.1.
- **Traceability matrix correction (in-scope for the spec/tasks phases of THIS cycle, not for the proposal).** `docs/traceability-matrix.md` currently mis-maps REQ-001-007 to the hexagonal requirement and quotes "El dominio no contiene imports de frameworks; arquitectura hexagonal validable" against it. REQ-001-007 is actually the configuration requirement (env vars + `.env.example`); the hexagonal requirement is REQ-001-015, which has no row at all. This is a documented drift (exploration §3 `major` finding). The proposal names the drift and commits the cycle to fixing it during the spec or Slice D tasks phase — the fix does NOT happen here in the proposal, and does NOT happen silently anywhere. Timing between "fix before Slice A begins" and "fix in Slice D docs task" is ASSUMPTION-10.
- **Post-cycle capability flip.** At cycle close (archive phase), `sdd/wheel-of-words/testing-capabilities` (Engram #2414) is upserted to `strict_tdd: true` with `test_runner_command: uv run pytest` and `test_runner_version: <resolved>`. This unblocks strict RED-first apply mode for every subsequent cycle (starting with SPEC-002 `.txt` import).

---

## 3. Non-goals — what this cycle explicitly does NOT deliver

Grounded in Constitution v2.0.0 and the ADR wave. Any temptation to breach these is a violation, not a judgment call.

- **No domain entities.** No `Lexeme`, `Occurrence`, `WordForm`, `PartOfSpeech`, `ManualCorrection`, `MultiwordExpression`, `Corpus`, or any linguistic class in Python. Grounded in Constitution Art. VII.6 ("Se evitará la abstracción especulativa"), DEC-005 ("SPEC-001 solo crea capas; las entidades lingüísticas llegarán con requisitos funcionales"), ADR-0002 (domain purity), and SPEC-001 §4 non-goals. The `domain/` package holds only `__init__.py` and, at most, a `README.md` explaining the layer contract per T025.
- **No importers, exporters, or NLP.** No `TextExtractor`, no file-upload endpoint, no `.txt` / `.epub` / `.pdf` handling, no `spaCy` / `stanza` / any NLP library in `pyproject.toml`, no Anki export path. Grounded in SPEC-001 §4 and Art. IV.2 (test data synthetic only).
- **No book text.** No copyrighted or extended real prose in the repo, including fixtures. Grounded in Constitution Art. IV.1–2, REQ-001-017, AC-013.
- **No authentication, users, or sessions.** Grounded in SPEC-001 §4 and the product-vision.md §4 audience ("Personal use", per archived cycle proposal §2).
- **No production deployment or cloud infrastructure.** No Docker image push, no cloud runtime target, no PostgreSQL migration, no secret management beyond `.env.example`. Grounded in SPEC-001 §4 and ADR-0005 (local-first). Docker Compose skeleton is deferred per DEC-006 and ASSUMPTION-9.
- **No public release / no license selection.** README acknowledges "license TBD" (Wheel Vocabulary is a personal-use product per archived cycle proposal §2). This is not a violation; it is a deliberate deferral.
- **No documentation-only refactors beyond the traceability matrix correction.** No overhauls of `docs/constitution.md`, ADRs, `docs/architecture/*`, `docs/glossary.md`, `docs/decisions-log.md`, or `AGENTS.md`. The only doc file this cycle may modify outside `openspec/changes/project-foundation-bootstrap/` is `docs/traceability-matrix.md`, and only to correct the REQ-001-007 / REQ-001-015 drift.
- **No project renaming.** The provisional name "Wheel Vocabulary" (per `docs/product-vision.md` §1) versus the repo directory name `wheel-of-words` is a real inconsistency but out of scope for this cycle. Handling it (constitutional amendment or product-vision refresh) is a deferred follow-up (§10).

---

## 4. Approach — how the cycle will be delivered

The exploration already produced the 4-slice plan; the proposal confirms it, binds it to the `feature-branch-chain` PR strategy, and records the rollback boundaries. **The maintainer has already approved `feature-branch-chain` for this cycle**; the tasks phase MUST NOT re-litigate the chain shape.

### 4.1 Slice A — Repository scaffold and Python toolchain bootstrap

| Attribute | Value |
|-----------|-------|
| Intent | Land the monorepo skeleton, `pyproject.toml`, `uv.lock`, empty four-layer structure, Makefile skeleton, `.env.example`, `.gitignore` additions. |
| REQs (partial) | REQ-001-007 (`.env.example`), REQ-001-008 (Makefile), REQ-001-015 (empty layer dirs), REQ-001-017, REQ-001-018, REQ-001-NF-001 (backend lockfile), REQ-001-NF-006. |
| Tasks | T001–T007, T009, T024–T025 (partial). |
| Layers | Repo skeleton, backend tooling, infra scaffolding. Zero behavior code. |
| Est. authored lines | 50–120. Safely under 400-line budget. |
| PR target | Slice A → PR into tracker branch `project-foundation-bootstrap`. |
| Rollback boundary | Full revert removes the scaffold; nothing depends on it yet. |

### 4.2 Slice B — Backend TDD: Settings → HealthResponse → `/health` → SQLAlchemy → Alembic

| Attribute | Value |
|-----------|-------|
| Intent | Strict TDD: Settings (T008 → T010 → T011) → HealthResponse (T012 → T013) → factory + route (T014 → T015 → T016) → SQLAlchemy (T017 → T018 → T019) → Alembic initial migration (T020 → T021 → T022 → T023). Include Ruff + mypy strict config. |
| REQs | REQ-001-001, REQ-001-002, REQ-001-005, REQ-001-006, REQ-001-007 (complete), REQ-001-009, REQ-001-012, REQ-001-NF-001 (verified), REQ-001-NF-003. |
| Tasks | T008–T023, T045–T046, T025 (docs). |
| Layers | Backend: empty `domain/` (per DEC-005), `application/` (config port if needed), `infrastructure/` (SQLAlchemy engine + Alembic env), `api/` (FastAPI factory + `/health` router). |
| Est. authored lines | 250–450. Upper bound overshoots the 400-line budget. |
| Sub-split rule | If Slice B lands > 400 authored lines, split into B1 (Settings + HealthResponse + factory + route, ~200 LOC) and B2 (SQLAlchemy engine + Alembic + integration tests, ~200 LOC). Decision surfaced during `sdd-tasks` per ASSUMPTION-1. |
| PR target | Slice B → PR into Slice A's branch. If sub-split: B1 → PR into Slice A branch; B2 → PR into B1 branch. |
| Rollback boundary | Reverting Slice B leaves Slice A intact (scaffold + toolchain remain). |

### 4.3 Slice C — Frontend TDD: React bootstrap + BackendStatus + contract validation

| Attribute | Value |
|-----------|-------|
| Intent | Initialize React + TypeScript strict + Vite (T026); implement `BackendStatus` in strict TDD (T027–T036). Add contract test (T037–T038) validating `HealthResponse` schema against backend OpenAPI. Frontend accessibility test (T035 → A11Y-FE-001). |
| REQs | REQ-001-003, REQ-001-004, REQ-001-010, REQ-001-013, REQ-001-NF-004, REQ-001-NF-005. |
| Tasks | T026–T039, T047–T048. |
| Layers | Frontend only. Uses backend OpenAPI as contract source per DEC-004. |
| Est. authored lines | 200–350 excluding `pnpm-lock.yaml`. Under budget when lockfile excluded from authored count. |
| Ordering | Depends on Slice B (contract test needs backend's OpenAPI schema). If parallel development is attempted, the contract test consumes a snapshotted schema until Slice B lands. |
| PR target | Slice C → PR into Slice B's branch (or Slice B2's, if B is sub-split). |
| Rollback boundary | Reverting Slice C leaves backend + scaffold intact. `apps/web/` is deleted; backend continues to serve `/health`. |

### 4.4 Slice D — E2E + CI + README + traceability matrix correction

| Attribute | Value |
|-----------|-------|
| Intent | Playwright config + `E2E-001` test (T040–T044); six GitHub Actions jobs (T049–T054); complete README (T055–T056); final secrets/protected-content sweep (T058); traceability matrix correction (per §2 bullet 9 and ASSUMPTION-10); final SPEC-001 traceability closure (T059) and decisions log (T062). |
| REQs | REQ-001-008 (complete), REQ-001-011, REQ-001-014, REQ-001-016, REQ-001-NF-002 (verified in CI), remaining REQ-001-NF-*. |
| Tasks | T040–T044, T049–T054, T055–T060. |
| Layers | CI, docs, `.github/workflows/`, `docs/traceability-matrix.md` (correction only). |
| Est. authored lines | 100–200. Under budget. |
| PR target | Slice D → PR into Slice C's branch. |
| Rollback boundary | Reverting Slice D removes CI, E2E, README polish. Backend + frontend still work locally. |

### 4.5 Chain topology

```
main
  └─ project-foundation-bootstrap  (tracker branch; ONLY this merges to main at cycle close)
       └─ slice-a
            └─ slice-b   (or slice-b1 → slice-b2 if sub-split)
                 └─ slice-c
                      └─ slice-d
```

Each PR targets the immediately previous slice's branch. GitHub diffs must show only the current slice's authored lines; if diffs surface previous slices, rebase/retarget until clean, per §E of the shared SDD phase common protocol. Only the tracker branch merges to `main`, with `--no-ff` at archive time to preserve the atomic cycle boundary.

### 4.6 Aggregate forecast

Exploration §5 forecast: **600–1120 authored lines aggregate** across four slices; each individual slice ≤ 400 lines (with Slice B sub-split contingency). The proposal accepts this forecast unchanged — no evidence during proposal drafting revises it. Aggregate exceeds the 400-line PR budget by 1.5×–3×, which is exactly why `feature-branch-chain` is the resolution rather than a single-PR delivery. The `ask-on-risk` guard is **triggered on aggregate but not on any individual PR** under the chain plan, which is the standard mitigation shape.

### 4.7 What the proposal does NOT decide

- Backend directory layout choice: `apps/api/pyproject.toml` vs. root-level workspace (ASSUMPTION-2).
- Sub-split of Slice B into B1 + B2 (ASSUMPTION-1).
- Makefile vs. `uv scripts` as the primary command surface (ASSUMPTION-3).
- Alembic baseline table content (ASSUMPTION-4).
- TypeScript ESLint ruleset (ASSUMPTION-5).
- CI runner OS matrix (ASSUMPTION-6).
- Playwright browser matrix (ASSUMPTION-7).
- Coverage-threshold enforcement severity (ASSUMPTION-8).
- Docker Compose scope (ASSUMPTION-9).
- Traceability matrix correction timing (ASSUMPTION-10).

These are all handled in §7. The proposal defers them to the spec, design, or tasks phases with stated defaults; none is a proposal-level lock.

---

## 5. TDD bootstrap policy for this cycle

The cycle starts with `strict_tdd: false` at the runtime layer (Engram #2414: `no_test_runner_detected`) even though the policy in `openspec/config.yaml` and the intent throughout AGENTS.md §3, Constitution Art. II, and ADR-0003 is `strict_tdd: true`. A RED test cannot precede the tool that runs it: pytest does not exist until `uv sync` installs it. The apply phase MUST follow this sequencing rule, which the proposal codifies here so the spec and tasks phases can inherit it without ambiguity:

1. **Bootstrap-prerequisite tasks (Slice A only).** Installing the test runner and its minimal configuration is scaffolding, not a behavior. This includes: creating `pyproject.toml`, running `uv sync`, creating `pytest.ini` or `[tool.pytest.ini_options]` in `pyproject.toml`, creating the empty four-layer directories, creating `.gitignore` and `.env.example`, and creating the Makefile skeleton. These MUST be tagged `[BOOTSTRAP]` (per AGENTS.md §8 tag vocabulary — this cycle introduces `[BOOTSTRAP]` for the first time; the tasks phase promotes it into the shared vocabulary if the maintainer accepts) or, equivalently, `[IMPL]` with an explicit note stating that the task creates infrastructure prerequisites, not a behavior.
2. **First `[TEST]` task.** A trivial smoke test that pytest works — e.g., `tests/smoke/test_smoke.py::test_pytest_runs`, asserting `assert True` — is the first RED task. It is trivial by design: Constitution Art. II.1 says every behavior begins with a failing test, and running a test runner for the first time IS a behavior (a testable claim: "pytest is installed and can execute a test file"). The smoke test starts non-existent (RED because the file does not exist and pytest reports "no tests ran" or "collection error"), then passes once the file is created. From this task forward, every subsequent behavior in Slice B, C, D follows strict RED → GREEN → REFACTOR per ADR-0003.
3. **Everything after the smoke test.** Every `Settings`, `HealthResponse`, route handler, SQLAlchemy engine, Alembic migration behavior, frontend component, E2E scenario, and CI job that has observable behavior begins with a failing test in the appropriate layer per test-plan.md.

**Constitutional grounding.** Constitution Art. II.1 reads: *"Cada comportamiento nuevo debe comenzar con una prueba que falle."* Art. II.2: *"La prueba debe fallar por la ausencia del comportamiento."* Neither clause literally names infrastructure scaffolding as "un comportamiento nuevo". ADR-0003 §Decision paragraph 2 reads: *"The minimum sufficient implementation is written to turn the RED test GREEN. No additional abstraction, no anticipatory scaffolding, no feature branching inside the implementation."* Here, "no anticipatory scaffolding" refers to speculative production code (extra fields, extra classes, extra methods) written during GREEN — it does NOT refer to installing the test runner itself.

**Open question flagged, not papered over.** The Constitution and ADR-0003 do NOT contain a clause that literally reads "infrastructure scaffolding is permitted before the first RED test." The interpretation above is the exploration's judgment (exploration §4 Risk 1) and the proposal's judgment. If the maintainer disagrees during proposal review, the correction lands in the spec phase as an explicit refresh item (per exploration §3 `minor` finding on TDD bootstrap exception wording). This is **not** treated as blocking: the exploration explicitly judged it non-blocking, and no ADR or Constitution clause literally prohibits the bootstrap sequence proposed. If the maintainer wants an amendment to Art. II to name the exception, that is a separate cycle.

---

## 6. Assumptions — proposal-level defaults, revisable by maintainer before spec starts

Ten questions surfaced in the exploration are recorded here as **assumptions with a stated default**. Each is revisable during proposal review; unresolved items carry into the spec / design / tasks phases per the `where re-examined` column. None is invented product policy — where the exploration and this proposal lack authority to decide, the default is the conservative option.

| ID | Question | Default assumed | Re-examined in | Blast radius if default is wrong |
|----|----------|-----------------|----------------|----------------------------------|
| ASSUMPTION-1 | Should Slice B split into B1 + B2? | Keep Slice B as one PR IF the final authored count is ≤ 400 lines; otherwise auto-split into B1 (Settings + HealthResponse + factory + route) and B2 (SQLAlchemy + Alembic + integration tests). Decision made during `sdd-tasks` after task-level LOC forecast. | `sdd-tasks` | Small. Splitting is a mechanical reorganization; wrong default means one PR is either 20% oversized or one PR is redundant. |
| ASSUMPTION-2 | Backend layout: `apps/api/pyproject.toml` (monorepo workspace) vs. root-level `pyproject.toml`. | Follow plan.md §2 structure verbatim: `apps/api/pyproject.toml`, with `apps/web/package.json` as the frontend sibling. This is what SPEC-001 already documents. | `sdd-design` | Medium. Wrong default forces path rewrites in Makefile, CI job working directories, and all import statements. Correcting later is a large refactor. Decide before Slice A begins. |
| ASSUMPTION-3 | Makefile vs. `uv scripts` for the unified command surface. | Makefile is the canonical entry point per REQ-001-008 and ADR-0001 §Automatización; it delegates to `uv run` (backend) and `pnpm` (frontend) commands. `uv scripts` in `pyproject.toml` MAY exist as backend-only conveniences but are not the primary interface. | `sdd-design` | Small. Wrong default is a reorganization of Makefile targets. |
| ASSUMPTION-4 | Initial Alembic migration content. | Empty-schema baseline revision that only pins Alembic's `alembic_version` table (SQLAlchemy 2 default behavior when running `alembic upgrade head` against an empty DB with no models). No `app_metadata` domain table; DEC-005 forbids domain scaffolding. Downgrade path exists (T023) even if trivial. | `sdd-spec` | Small. Wrong default means the migration test (INT-BE-002) has a slightly different assertion. |
| ASSUMPTION-5 | TypeScript ESLint ruleset baseline. | `@typescript-eslint/recommended-type-checked` + `eslint-plugin-react-hooks` (recommended). Strict TS (`strict: true` in `tsconfig.json`) per REQ-001-013. React 19 conventions honored. | `sdd-design` | Small. Wrong default is a lint config edit. |
| ASSUMPTION-6 | GitHub Actions runner OS matrix. | `ubuntu-latest` only for all six CI jobs. `macos-latest` is NOT included in the CI matrix; local macOS validation is developer responsibility. | `sdd-design` | Small. Wrong default is adding a matrix key to the workflow. Runtime cost is real (macOS runners are 10× more expensive minutes) so opt-in is correct default. |
| ASSUMPTION-7 | Playwright browser target. | Chromium only per test-plan §7. `webkit` and `firefox` are NOT configured in `playwright.config.ts`. | `sdd-design` | Small. Wrong default is a Playwright config addition. |
| ASSUMPTION-8 | Coverage-threshold enforcement severity in CI. | Hard-gate at global 80% and domain/application 90% per ADR-0003 §Consequences and `openspec/config.yaml` `verify.coverage_threshold: 80`, starting from Slice B (backend) and Slice C (frontend). No soft-warning phase. | `sdd-spec` | Small–Medium. Wrong default means the first PR that lands red-lines below threshold is blocked by CI without prior warning. Acceptable per Art. VIII.2. |
| ASSUMPTION-9 | Docker Compose scope in this cycle. | Excluded from this cycle. DEC-006 marks Docker optional; the exploration recommended deferring to a maintenance task. No `docker-compose.yml` lands in Slice A–D. | `sdd-spec` | Small. Wrong default is a follow-up task in a future maintenance cycle. |
| ASSUMPTION-10 | Traceability matrix correction timing. | Land the `docs/traceability-matrix.md` REQ-001-007 → configuration + REQ-001-015 → hexagonal correction inside Slice D's documentation task (T059-adjacent). No pre-cycle docs commit. Rationale: keeps the cycle atomic; a mid-cycle docs commit fragments the tracker branch. Downside: apply/verify agents encounter the drift during Slice B/C and may be confused. Mitigation: this proposal explicitly flags the drift (per exploration §3 `major` finding); apply agent MUST NOT act on the mis-mapped row. | `sdd-tasks` | Medium. Wrong default causes 2–3 apply-phase confusions until Slice D lands. Fixing pre-cycle instead is a 5-line docs commit but changes the branch topology. |

These assumptions are **revisable by the maintainer before the spec phase starts.** After the spec phase begins, revisions require an updated spec artifact and an updated tasks artifact.

---

## 7. Risks and mitigations

Top risks carried from exploration §4, updated with proposal-level judgment. Ordered by severity × likelihood.

| # | Risk | Severity | Mitigation |
|---|------|----------|------------|
| R-1 | **TDD bootstrap chicken-and-egg.** RED test cannot precede the test runner; strict interpretation of Constitution Art. II.1 could stall Slice A. | HIGH | §5 sequencing rule. `[BOOTSTRAP]` tag distinguishes prerequisite infrastructure from behavior. First RED test is the trivial `test_smoke.py::test_pytest_runs`. If the maintainer rejects this interpretation, spec phase adds an explicit refresh item; the cycle does not stall. |
| R-2 | **Slice B size overshoot.** Backend TDD estimate is 250–450 lines; upper bound violates the 400-line per-PR budget. | HIGH | Pre-committed sub-split rule per ASSUMPTION-1 and §4.2. `sdd-tasks` performs the LOC forecast per task and decides sub-split before apply begins. `sdd-apply` refuses to start Slice B if forecast > 400 and sub-split is not scheduled. |
| R-3 | **E2E flakiness.** Playwright depends on both backend and frontend being alive; race conditions and arbitrary sleeps degrade CI reliability (plan.md §10, exploration §4 Risk 2). | MEDIUM–HIGH | Playwright `webServer` config manages server lifecycle deterministically (no `setTimeout` or `sleep()`). Use `expect(...).toBeVisible()` and `waitForLoadState` instead of hardcoded waits. First E2E run stays Chromium-only per ASSUMPTION-7 to minimize browser-specific flakiness. |
| R-4 | **Non-goals creep during apply.** Temptation to pre-scaffold a `Lexeme` entity because "the architecture is known" (exploration §4 Risk 5). Directly violates DEC-005 and Constitution Art. VII.6. | HIGH (severity) × LOW (likelihood with mitigation) | `sdd-apply` MUST cite DEC-005 and Art. VII.6 in its pre-apply checklist. Verify phase MUST run a static check: `grep -R "class Lexeme\|class Occurrence\|class Corpus\|class MultiwordExpression\|class Lemma" apps/api/` MUST return empty. Any hit fails Slice B verification. |
| R-5 | **Traceability drift compounds if uncorrected before verify.** REQ-001-007 mis-map + missing REQ-001-015 row will produce a Slice D verify failure OR (worse) a silent pass because the matrix is wrong. | MEDIUM | ASSUMPTION-10 default: correct in Slice D. Proposal names the drift so no phase silently accepts the mis-mapped row. Alternative pre-cycle fix is available if maintainer prefers. |

Additional lower-severity risks documented in exploration §4 (uv vs. poetry reflex, local-first compliance of `/health`) are already resolved by SPEC-001's toolchain lock-in and ADR-0005 respectively; they are not reproduced here.

---

## 8. Success criteria — cycle-close outcomes

Bulleted; each is objectively verifiable at archive time. Verify-phase-specific criteria (test-by-test) live in SPEC-001 acceptance.md and test-plan.md; the criteria below are proposal-level.

- [ ] All 18 functional REQs (REQ-001-001..018) and all 6 non-functional REQs (REQ-001-NF-001..006) map to at least one PR merged into tracker branch `project-foundation-bootstrap`.
- [ ] All 15 acceptance criteria (AC-001..015) pass in the final verify report on the tracker branch.
- [ ] All 62 tasks (T001..T062) are marked done in the tasks-phase artifact, with per-task evidence (commit SHA or verify-report reference).
- [ ] Every PR in the chain (A, B [or B1+B2], C, D) has ≤ 400 authored lines (excluding `uv.lock`, `pnpm-lock.yaml`, and generated Alembic migration script if flagged as generated).
- [ ] `main` remains at its pre-cycle HEAD until archive; only the tracker branch merges to `main` at cycle close (`--no-ff`).
- [ ] CI green on the tracker branch at cycle close: `backend-quality`, `backend-tests`, `frontend-quality`, `frontend-tests`, `migration-check`, `e2e` all pass.
- [ ] `sdd/wheel-of-words/testing-capabilities` (Engram #2414) upserted to `strict_tdd: true` with `test_runner_command: uv run pytest` and version pinned.
- [ ] `openspec/config.yaml` `strict_tdd: true` now reflects both policy AND runtime.
- [ ] `docs/traceability-matrix.md` drift corrected: REQ-001-007 row references configuration and AC-007; new REQ-001-015 row references hexagonal structure and AC-015 (or the matrix's chosen AC per spec-phase decision).
- [ ] Zero forbidden domain entities present anywhere under `apps/api/src/`. Static grep check documented in verify-report.
- [ ] Zero copyrighted book text or extended real prose fixtures anywhere in the repo (REQ-001-017, AC-013).
- [ ] `openspec/changes/project-foundation-bootstrap/` cleanly promotes to `openspec/archive/<date>-project-foundation-bootstrap/` at archive. **Known workaround:** the `sdd-archive-anthropic` skill has a documented copy-instead-of-move defect (see archived cycle post-cycle decisions). Cycle close requires a manual reconcile analogous to the previous cycle — this is captured explicitly here so it is not forgotten (§10 out-of-scope follow-ups includes the skill fix).
- [ ] Engram cycle audit trail: `sdd/project-foundation-bootstrap/{explore, proposal, spec, design, tasks, apply-progress, verify-report, archive-report}` all persisted with matching `topic_key`.

---

## 9. Out-of-scope follow-ups — deferred to future cycles

Named deliberately so they are not silently lost.

- **SPEC-002: `.txt` import + alphabetical frequency list.** First user-value slice. Depends on this cycle landing. Product-vision.md §12 roadmap step 2. Will be the first cycle to introduce domain entities (`Lexeme`, `Occurrence`) under strict TDD, with `strict_tdd: true` at runtime.
- **Constitutional amendment for the project name.** Product-vision.md §1 uses "Wheel Vocabulary" (provisional); the repo directory and Engram project key are `wheel-of-words`. Reconciliation requires either a product-vision refresh (rename to "Wheel of Words") or a repo/Engram rename. This is a coordinated multi-file change like the v2.0.0 amendment; not this cycle.
- **`sdd-archive-anthropic` skill: move-vs-copy defect.** Documented workaround at cycle close; the skill itself needs a patch so archive is atomic. Skill-registry / SDD skill patches are outside this cycle's authored code.
- **`openspec/changes/` gitignore policy.** Deferred per archived cycle post-cycle decision #1. Resolution should happen before or during archive of THIS cycle; the maintainer decides whether to gitignore `openspec/changes/` and rely on Engram + archive as the durable record, or continue tracking `changes/` in git.
- **Docker Compose skeleton.** Deferred per ASSUMPTION-9 and DEC-006.
- **macOS CI runner support.** Deferred per ASSUMPTION-6.
- **Firefox / WebKit Playwright targets.** Deferred per ASSUMPTION-7.
- **`docs/product-vision.md` §12 roadmap items 3–10.** All post-SPEC-001 cycles: tokenization, lemmatization, POS, navigator, proper nouns, MWEs, learning state, Anki export, EPUB.

---

## 10. Rollback plan

Per the chain topology, rollback granularity IS slice granularity.

- **Slice A rollback.** `git revert` the Slice A merge commit on the tracker branch (or reset the tracker branch if no downstream slice has merged into it yet). Repository returns to documentation-only baseline; no code is orphaned; Engram observations are preserved. Toolchain is not installed on developer machines, but no state escapes the repo.
- **Slice B rollback.** Revert Slice B (or B2 → B1 → nothing) on top of Slice A. Backend disappears; Slice A scaffold remains. `uv sync` still works (pyproject exists) but there are no Python source files to run. `strict_tdd` runtime flag does NOT flip back automatically — it stays `true` because pytest is still installed, but there are no tests to run.
- **Slice C rollback.** Revert Slice C on top of Slice B. Frontend disappears; backend continues to run `/health`. E2E cannot pass (no frontend), so Slice D CI cannot pass either.
- **Slice D rollback.** Revert Slice D. Removes CI, README polish, and the traceability matrix correction. Backend + frontend both work locally.
- **Full cycle rollback.** Reset the tracker branch to its pre-cycle HEAD. `sdd/wheel-of-words/testing-capabilities` in Engram must be manually re-set to `strict_tdd: false` (runtime) to match the pre-cycle state. `openspec/changes/project-foundation-bootstrap/` remains as historical planning artifact; it does NOT need to be deleted.

**No cascading rollback**: reverting Slice D does NOT force reverting Slice C. Each slice is independently revertible above its ancestors.

---

## 11. Dependencies

- **Human**: maintainer review of this proposal (assumptions, non-goals, chain topology) before `sdd-spec` begins.
- **Tooling**: `uv` CLI installed on developer machines; `pnpm` installed; Playwright's browser downloader has network access at install time (first `pnpm exec playwright install` requires internet — this is install-time only, not test-time, so REQ-001-NF-003 is preserved).
- **Prerequisite artifacts**: SPEC-001 (already complete), Constitution v2.0.0 + ADRs 0001–0010 (already ratified), `openspec/config.yaml` (already present).
- **Prerequisite state**: `sdd-init-anthropic/wheel-of-words` (Engram #2413), `sdd/wheel-of-words/testing-capabilities` (Engram #2414), `sdd/project-foundation-bootstrap/explore` (Engram #2415). All present.
- **No external dependencies**: no cloud accounts, no third-party services, no paid tooling.

---

## 12. Skill resolution

| Skill | Status | Role in this proposal |
|-------|--------|-----------------------|
| `_shared` | Loaded (support reference; not invokable) | `sdd-phase-common.md` sections A (skill loading), B (retrieval), C (persistence), D (return envelope), E (review workload guard) followed. |
| `sdd-propose` | Loaded (executor, this phase) | Governs this artifact. Structure follows the SKILL.md schema (metadata, intent, scope, non-goals, approach, TDD bootstrap policy, assumptions, risks, success criteria, out-of-scope, rollback, dependencies, skill resolution). |

**Skill resolution result:** `paths-injected` — paths supplied by orchestrator (`/Users/isildur/.claude/skills/sdd-propose/SKILL.md`, `/Users/isildur/.config/opencode/skills/_shared/SKILL.md` fallback). No registry fallback required.

---

## 13. Recommendation

**Proceed to `sdd-spec`** for the delta spec against SPEC-001, or **proceed to `sdd-design` in parallel** if the maintainer prefers to develop the technical design alongside the spec refresh. The spec phase MUST address:

1. The seven `minor` refresh items from exploration §3 (TDD bootstrap wording, coverage thresholds, phrasal-verb non-goal terminology, multi-language skeleton note, `strict_tdd` policy vs. runtime, T024 task type, and any minor drift discovered).
2. The `major` traceability drift (REQ-001-007 / REQ-001-015).
3. Assumptions marked "re-examined in sdd-spec" (ASSUMPTION-4, -8, -9).

The maintainer is asked to confirm or revise the ten assumptions in §7 before spec phase begins. If any assumption is revised, the change is captured in the proposal (revision) or in the spec phase directly, and this file is upserted to Engram accordingly.

---

## References

- Exploration: `openspec/changes/project-foundation-bootstrap/explore.md` (352 lines; Engram #2415).
- Init report: `sdd-init-anthropic/wheel-of-words` (Engram #2413).
- Testing capabilities snapshot: `sdd/wheel-of-words/testing-capabilities` (Engram #2414).
- Target spec suite: `specs/001-project-foundation/` (spec, acceptance, plan, test-plan, tasks, decisions, traceability).
- Constitution: `docs/constitution.md` (v2.0.0).
- ADRs: `docs/adr/README.md` and ADR-0001 through ADR-0010.
- Product vision: `docs/product-vision.md`.
- Architecture baseline: `docs/architecture/architecture-baseline.md`.
- Definition of Done: `docs/definition-of-done.md`.
- Top-level traceability: `docs/traceability-matrix.md` (drift documented herein).
- AGENTS.md sections 2, 3, 5, 6, 8, 10.
- Reference archived cycle: `openspec/archive/2026-07-16-docs-methodology-overhaul/proposal.md` and `archive-report.md` (tone and structural calibration only; scope and content not reproduced).

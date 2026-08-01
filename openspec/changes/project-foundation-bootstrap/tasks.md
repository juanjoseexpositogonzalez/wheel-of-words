# Tasks — project-foundation-bootstrap

## 1. Metadata

| Field | Value |
|-------|-------|
| Change slug | `project-foundation-bootstrap` |
| Cycle type | First code-touching cycle; operationalizes SPEC-001 |
| Tasks version | `1.0.0` |
| Constitution version | v2.0.0 |
| Target spec suite | `specs/001-project-foundation/` (SPEC-001 v1.0.0) |
| Chain strategy | `feature-branch-chain` on tracker branch `project-foundation-bootstrap` |
| Review budget | 400 authored lines per PR (lockfiles and generated Alembic scripts excluded) |
| **Python package name** | `wheel_vocabulary` (PyPI: `wheel-vocabulary`). This overrides `wheel_vocab` wherever it appears in design.md §4.3 and §5.2. Every import path, config reference, and file path in these tasks uses `wheel_vocabulary`. |
| Upstream inputs | design.md (898 lines), spec.md (515 lines), proposal.md (288 lines), explore.md |
| Downstream consumer | apply phase (one slice at a time, in order A → B1 → B2 → C → D) |

**Package name override note.** The maintainer has decided the Python module name is `wheel_vocabulary` (underscore) and the PyPI-convention project name is `wheel-vocabulary` (hyphen). Every occurrence of `wheel_vocab` in design.md §4.3 NDD-01, §5.2 pyproject.toml shape, §6.x call graphs, and §14 verify hooks is superseded by this override. Task TA14 corrects design.md. All subsequent tasks reference `wheel_vocabulary` exclusively.

---

## 2. Slice DAG and Forecast Summary

### 2.1 Slice overview

| Slice | Branch target | Intent | Task count | Est. authored LOC | ≤ 400? |
|-------|--------------|--------|------------|-------------------|--------|
| A | tracker (`project-foundation-bootstrap`) | Monorepo scaffold, pyproject.toml, empty layers, Makefile, .env.example, .gitignore, smoke test, stubs, design.md fix | 14 | ~370 | **Yes** |
| B1 | slice-a | Settings → Clock → Version reader → health.v1.json → HealthResponse DTO → GET /api/v1/health route + factory | 12 | ~265 | **Yes** |
| B2 | slice-b1 | SQLAlchemy engine → DeclarativeBase → Alembic init + baseline migration → integration tests | 8 | ~150 | **Yes** |
| C | slice-b2 | Frontend bootstrap, API client, StatusLoading/Healthy/Error/Page components, wiring, CSS | 13 | ~243 | **Yes** |
| D | slice-c | E2E spec + playwright.config, CI workflow, traceability regression test + matrix fix, README update, decisions log, security test, capability flip | 10 | ~235 | **Yes** |

**Aggregate: ~1263 authored LOC.** This is +13% above the proposal's high bound of 1120 LOC. The overshoot is within the ±30% re-forecast trigger threshold; no re-forecast is required. Each individual PR stays ≤ 400 authored lines.

### 2.2 Slice B sub-split decision (proposal §5 R-2 pre-committed rule)

**SPLIT TRIGGERED.** Task-level LOC forecast for Slice B as a single PR = ~415 authored lines, exceeding the 400-line budget by ~4%. The split is mandatory per proposal §4.2 sub-split rule.

**B1 boundary** (split point): after TA14 of Slice A, through TB1-12 (route + factory). B1 delivers: Settings, Clock port + SystemClock, version reader, health.v1.json schema, HealthResponse DTO, GET /api/v1/health route, FastAPI app factory, and all associated tests.

**B2 boundary**: TB2-01 through TB2-08. B2 delivers: SQLAlchemy engine + session factory, DeclarativeBase, Alembic wiring (alembic.ini, env.py, script.py.mako, 0001_baseline.py), and integration tests (INT-BE-001, INT-BE-002, INT-BE-003).

### 2.3 PR targets under feature-branch-chain

```
main (unchanged until cycle close via --no-ff)
  └─ project-foundation-bootstrap  (tracker branch)
       └─ slice-a           PR A → tracker
            └─ slice-b1     PR B1 → slice-a
                 └─ slice-b2  PR B2 → slice-b1
                      └─ slice-c   PR C → slice-b2
                           └─ slice-d  PR D → slice-c
```

Only `project-foundation-bootstrap` → `main` at archive (cycle close).

### 2.4 ask-on-risk guard

The aggregate forecast of ~1263 LOC exceeds the 400-line single-PR budget, triggering the `ask-on-risk` delivery strategy guard. However, because the maintainer has already committed to `feature-branch-chain` with the B1/B2 sub-split — meaning **no individual PR exceeds 400 authored lines** — the per-PR budget risk is **Low** for every slice. The orchestrator guard is resolved: the chain strategy IS the mitigation. `Decision needed before apply: No`.

---

## 3. Task Naming and Traceability Format

Tasks use the format `T<slice><nn>` (e.g., `TA01`, `TB101` for B1, `TB201` for B2, `TC01`, `TD01`). Slices A, C, D use `TA`, `TC`, `TD`. Slice B1 uses `TB1nn`. Slice B2 uses `TB2nn`. TDD ordering is strict from the first `[TEST]` task onward: every `[TEST]` (RED) precedes its `[IMPL]` (GREEN) which precedes any `[REFACTOR]`. `[BOOTSTRAP]` tasks are Slice A only and precede the first `[TEST]`.

---

## 4. Slice A — Scaffold

**Exit criterion:** `make bootstrap && make test-backend && make lint && make typecheck` all pass on the slice-a branch. (Coverage is not gated here; only the smoke test runs.)

---

### TA01 [BOOTSTRAP] Create monorepo directory skeleton

- **Slice**: A
- **Status**: DONE
- **Type tag**: [BOOTSTRAP]
- **Touches**: `apps/api/`, `apps/api/tests/smoke/`, `apps/api/tests/unit/`, `apps/api/tests/api/`, `apps/api/tests/integration/`, `apps/web/`, `apps/web/src/api/`, `apps/web/src/components/`, `apps/web/src/pages/`, `apps/web/src/styles/`, `apps/web/src/types/`, `apps/web/e2e/`, `.github/workflows/` (empty; CI YAML is Slice D), `pnpm-workspace.yaml`
- **Traces**: REQ-001-015, REQ-001-008, design §4.4, AGENTS.md §8 [BOOTSTRAP]
- **Prereq tasks**: none
- **Estimated LOC**: 5 (pnpm-workspace.yaml) + directory markers only
- **Description**: Create the full directory tree from design §4.4 — `apps/api/`, `apps/web/`, all `src/` subdirectories, `tests/` subdirectories, `e2e/`, `.github/workflows/`. Create `pnpm-workspace.yaml` at repo root declaring `apps/web` as the sole workspace package. No source files yet; directories only (with `.gitkeep` where needed to make directories trackable).
- **DoD**:
  - `apps/api/tests/{smoke,unit,api,integration}/` all exist
  - `apps/web/src/{api,components,pages,styles,types}/` all exist
  - `pnpm-workspace.yaml` lists `apps/web` as packages entry
  - `apps/web/e2e/` and `.github/workflows/` exist

---

### TA02 [BOOTSTRAP] Create `apps/api/pyproject.toml`

- **Slice**: A
- **Status**: DONE
- **Type tag**: [BOOTSTRAP]
- **Touches**: `apps/api/pyproject.toml`
- **Traces**: REQ-001-008, REQ-001-009, REQ-001-012, REQ-001-NF-001, design §5.2, spec CONTRACT-5, ADR-0001, ADR-0003
- **Prereq tasks**: TA01
- **Estimated LOC**: 75
- **Description**: Create `apps/api/pyproject.toml` with `[project].name = "wheel-vocabulary"`, `[project].version = "0.1.0"`, `requires-python = ">=3.12"`, runtime and optional-dependency groups (`dev`, `test`, `lint`, `type`), `[build-system]` using hatchling, `[tool.hatch.build.targets.wheel] packages = ["src/wheel_vocabulary"]`, `[tool.pytest.ini_options]` with `testpaths = ["tests"]` / `addopts = "--strict-markers -ra"` / markers (`unit`, `integration`, `e2e`, `smoke`), `[tool.coverage.run]` with `source = ["wheel_vocabulary"]` and `branch = true`, `[tool.coverage.report]`, `[tool.ruff]` with the full rule set from design §5.3 and `known-first-party = ["wheel_vocabulary"]`, `[tool.mypy]` base gradual config plus `[[tool.mypy.overrides]]` for `wheel_vocabulary.domain.*` and `wheel_vocabulary.application.*` set to `strict = true`. Use `wheel_vocabulary` (NOT `wheel_vocab`) in every identifier.
- **DoD**:
  - `[project].name = "wheel-vocabulary"` present
  - `[tool.hatch.build.targets.wheel] packages = ["src/wheel_vocabulary"]`
  - `[[tool.mypy.overrides]] module = "wheel_vocabulary.domain.*"` and `"wheel_vocabulary.application.*"` each with `strict = true`
  - `[tool.ruff.lint.isort] known-first-party = ["wheel_vocabulary"]`
  - `python -c "import tomllib; tomllib.loads(open('apps/api/pyproject.toml').read())"` exits 0

---

### TA03 [BOOTSTRAP] Generate `apps/api/uv.lock` via `uv lock`

- **Slice**: A
- **Status**: DONE
- **Type tag**: [BOOTSTRAP]
- **Touches**: `apps/api/uv.lock` (generated; excluded from authored LOC count)
- **Traces**: REQ-001-NF-001, ADR-0001 (uv)
- **Prereq tasks**: TA02
- **Estimated LOC**: 0 (generated)
- **Description**: From `apps/api/`, run `uv lock` to generate the lockfile. Then run `uv sync --extra dev` to install the virtual environment. This installs pytest and all dev dependencies. **This task is infrastructure setup — it creates the prerequisite for the first RED test.** The lockfile is committed but excluded from the 400-line authored LOC count.
- **DoD**:
  - `apps/api/uv.lock` exists
  - `apps/api/.venv/` is created (not committed; gitignored)
  - `uv run pytest --version` exits 0 from `apps/api/`

---

### TA04 [BOOTSTRAP] Create `apps/api/src/wheel_vocabulary/` package tree

- **Slice**: A
- **Status**: DONE
- **Type tag**: [BOOTSTRAP]
- **Touches**: `apps/api/src/wheel_vocabulary/__init__.py`, `apps/api/src/wheel_vocabulary/domain/__init__.py`, `apps/api/src/wheel_vocabulary/application/__init__.py`, `apps/api/src/wheel_vocabulary/infrastructure/__init__.py`, `apps/api/src/wheel_vocabulary/infrastructure/persistence/__init__.py`, `apps/api/src/wheel_vocabulary/api/__init__.py`, `apps/api/src/wheel_vocabulary/api/schemas/` (empty dir), `apps/api/src/wheel_vocabulary/api/dtos/` (empty dir), `apps/api/src/wheel_vocabulary/api/routes/` (empty dir)
- **Traces**: REQ-001-015, design §4.4, ADR-0002 (hexagonal layers), REQ-PFB-LANG-01, REQ-PFB-BOOT-01
- **Prereq tasks**: TA03
- **Estimated LOC**: 10 (minimal `__init__.py` files; `__version__` export in root only)
- **Description**: Create the four-layer package tree per design §4.4, using the package name `wheel_vocabulary`. Each layer gets an `__init__.py`. The root `__init__.py` exports `__version__ = "0.1.0"`. All other `__init__.py` files are empty (docstring only if desired). Do NOT add any domain, application, or infrastructure code. `domain/__init__.py` MUST be empty except for an optional layer-contract docstring. No English-hardcoding per REQ-PFB-LANG-01; the docstring may reference the layer role but must not encode language assumptions. Also create empty sub-directories for `api/schemas/`, `api/dtos/`, `api/routes/` with `__init__.py`.
- **DoD**:
  - `python -c "import wheel_vocabulary"` exits 0 (from `apps/api/` with venv active or `uv run`)
  - `from wheel_vocabulary.domain import *` produces no import error
  - `grep -r "english\|en_us\|en_gb\|assume_english" apps/api/src/wheel_vocabulary/domain/ apps/api/src/wheel_vocabulary/application/` returns empty (hook 2)
  - `__version__ = "0.1.0"` present in root `__init__.py`

---

### TA05 [BOOTSTRAP] Create `apps/api/tests/conftest.py`

- **Slice**: A
- **Status**: DONE
- **Type tag**: [BOOTSTRAP]
- **Touches**: `apps/api/tests/conftest.py`
- **Traces**: REQ-001-009, design §4.5, ADR-0003
- **Prereq tasks**: TA04
- **Estimated LOC**: 8
- **Description**: Create a minimal `apps/api/tests/conftest.py` that will hold shared fixtures for the cycle. At this stage it may be nearly empty (a comment block explaining fixture placement policy). Slice B adds actual fixtures (FrozenClock, TestClient) here. Do not add any fixtures in Slice A — Slice A's conftest is infrastructure scaffolding only.
- **DoD**:
  - File exists
  - `uv run pytest --collect-only` exits 0 from `apps/api/` (no errors; zero tests found is expected)

---

### TA06 [BOOTSTRAP] Create `apps/web/package.json`, `tsconfig.json`, and TypeScript config files

- **Slice**: A
- **Status**: DONE
- **Type tag**: [BOOTSTRAP]
- **Touches**: `apps/web/package.json`, `apps/web/tsconfig.json`, `apps/web/tsconfig.node.json`, `apps/web/index.html`
- **Traces**: REQ-001-003, REQ-001-013, ADR-0001, design §7.1
- **Prereq tasks**: TA01
- **Estimated LOC**: 60
- **Description**: Create `apps/web/package.json` with all frontend dependencies pinned to the versions from design §7.1 (React 19, Vite 5, TypeScript 5.4, Vitest 1.6, Testing Library 16, Playwright 1.44). Create `tsconfig.json` with `strict: true`, `target: "ES2022"`, `lib: ["ES2022", "DOM"]`, `module: "ESNext"`, `moduleResolution: "bundler"`. Create `tsconfig.node.json` for Vite config files. Create `apps/web/index.html` as the Vite entry point with `<div id="root"></div>` and `<script type="module" src="/src/main.tsx">`.
- **DoD**:
  - `package.json` contains React 19, Vite 5, TypeScript 5.4, Vitest, Testing Library, Playwright entries
  - `tsconfig.json` has `"strict": true`
  - `index.html` references `/src/main.tsx`

---

### TA07 [BOOTSTRAP] Create `apps/web/vite.config.ts` and `apps/web/vitest.config.ts`

- **Slice**: A
- **Status**: DONE
- **Type tag**: [BOOTSTRAP]
- **Touches**: `apps/web/vite.config.ts`, `apps/web/vitest.config.ts`
- **Traces**: REQ-001-003, REQ-001-010, ADR-0001, design §7.1
- **Prereq tasks**: TA06
- **Estimated LOC**: 35
- **Description**: Create `apps/web/vite.config.ts` with React plugin. Create `apps/web/vitest.config.ts` with `environment: "jsdom"`, `globals: true`, `setupFiles`, and `coverage` config (provider `v8`; threshold will be enabled in Slice D per REQ-PFB-COV-02). Coverage threshold NOT enabled here — Slice D task TD03 activates it. The `coverage.include` should already reference `src/**` so Slice D's activation is a one-line change.
- **DoD**:
  - `apps/web/vite.config.ts` imports and uses `@vitejs/plugin-react`
  - `apps/web/vitest.config.ts` has `environment: "jsdom"` and `coverage.provider: "v8"`
  - No `coverageThreshold` active yet (Slice D enables it)

---

### TA08 [BOOTSTRAP] Create `apps/web/.eslintrc.cjs` and install frontend dependencies

- **Slice**: A
- **Status**: DONE
- **Type tag**: [BOOTSTRAP]
- **Touches**: `apps/web/.eslintrc.cjs`, `apps/web/pnpm-lock.yaml` (generated; excluded from LOC)
- **Traces**: REQ-001-013, design §7.6 (NDD-10), ADR-0001
- **Prereq tasks**: TA07
- **Estimated LOC**: 25 (.eslintrc.cjs); 0 (lockfile, generated)
- **Description**: Create `apps/web/.eslintrc.cjs` with `@typescript-eslint/recommended-type-checked` parser options and `eslint-plugin-react-hooks` per design §7.6 NDD-10. From `apps/web/`, run `pnpm install` to generate `pnpm-lock.yaml`. The lockfile is committed but excluded from the 400-line authored LOC count. Verify `pnpm run lint` exits 0 (no source files yet, so lint should pass vacuously).
- **DoD**:
  - `.eslintrc.cjs` extends `@typescript-eslint/recommended-type-checked`
  - `apps/web/pnpm-lock.yaml` exists
  - `pnpm run lint` exits 0 from `apps/web/`

---

### TA09 [BOOTSTRAP] Create `apps/web/src/main.tsx` and `apps/web/src/App.tsx` stubs

- **Slice**: A
- **Status**: DONE
- **Type tag**: [BOOTSTRAP]
- **Touches**: `apps/web/src/main.tsx`, `apps/web/src/App.tsx`
- **Traces**: REQ-001-003, design §4.4 (Slice A scaffold), design §7.2
- **Prereq tasks**: TA08
- **Estimated LOC**: 15
- **Description**: Create minimal stub versions of `main.tsx` (mounts `<App />` on `#root`) and `App.tsx` (returns `<p>Loading…</p>` or similar placeholder). These stubs will be replaced in Slice C by the real `StatusPage` wiring. Purpose here is to make `pnpm run dev` bootable and TypeScript compiler happy. The stub MUST NOT import from `./pages/StatusPage` (that file does not exist yet).
- **DoD**:
  - `pnpm run typecheck` exits 0 from `apps/web/`
  - `pnpm run dev` starts Vite dev server without errors (may show placeholder UI)

---

### TA10 [BOOTSTRAP] Create root `Makefile`

- **Slice**: A
- **Status**: DONE
- **Type tag**: [BOOTSTRAP]
- **Touches**: `Makefile`
- **Traces**: REQ-001-008, ADR-0001 (Makefile as canonical surface, design §10)
- **Prereq tasks**: TA03, TA08
- **Estimated LOC**: 60
- **Description**: Create `Makefile` at repo root with all targets from design §10 as `.PHONY` entries: `bootstrap`, `install`, `dev-backend`, `dev-frontend`, `dev`, `test-backend`, `test-frontend`, `test-e2e`, `test`, `lint-backend`, `lint-frontend`, `lint`, `typecheck-backend`, `typecheck-frontend`, `typecheck`, `format`, `migrate`, `clean`. Each delegates to `uv run` (backend, working in `apps/api/`) or `pnpm` (frontend, working in `apps/web/`). `dev-backend` uses `wheel_vocabulary.api.main:create_app` (NOT `wheel_vocab`). `typecheck-backend` runs `uv run mypy src/wheel_vocabulary`.
- **DoD**:
  - `make bootstrap` exits 0 (runs `uv sync --extra dev` + `pnpm install`)
  - All target names from design §10 present as `.PHONY`
  - `dev-backend` target references `wheel_vocabulary.api.main:create_app`
  - `typecheck-backend` references `src/wheel_vocabulary`

---

### TA11 [BOOTSTRAP] Create `.env.example` at repo root

- **Slice**: A
- **Status**: DONE
- **Type tag**: [BOOTSTRAP]
- **Touches**: `.env.example`
- **Traces**: REQ-001-007, REQ-001-018, design §6.4, spec AC-007, Constitution Art. VIII.5
- **Prereq tasks**: TA01
- **Estimated LOC**: 15
- **Description**: Create `.env.example` with documented placeholder values for every field that `Settings` will use: `APP_NAME`, `APP_VERSION`, `ENVIRONMENT`, `DATABASE_URL`, `CORS_ORIGINS`, `LOG_LEVEL`, and `VITE_API_BASE_URL`. All values are safe examples (no real secrets, no real credentials). File contains a header comment stating "Copy to .env for local development; never commit .env". `DATABASE_URL` example uses `sqlite:///./data/wheel_vocabulary.db` (updated from design to match `wheel_vocabulary` package name).
- **DoD**:
  - `.env.example` exists at repo root
  - Contains all Settings field names (as env-var keys)
  - No actual secrets present
  - `DATABASE_URL` example references `wheel_vocabulary`

---

### TA12 [BOOTSTRAP] Extend `.gitignore`

- **Slice**: A
- **Status**: DONE
- **Type tag**: [BOOTSTRAP]
- **Touches**: `.gitignore`
- **Traces**: REQ-001-018, design §4.4, spec AC-013
- **Prereq tasks**: TA01
- **Estimated LOC**: 10
- **Description**: Extend the existing `.gitignore` (do not replace it) to cover: Python artifacts (`__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.coverage`, `htmlcov/`, `*.pyc`, `apps/api/.venv/`, `data/`), Node artifacts (`apps/web/node_modules/`, `apps/web/dist/`, `apps/web/coverage/`), and environment files (`.env`, `.env.local`). Alembic-generated migration files in `apps/api/migrations/versions/` are NOT gitignored (they are committed).
- **DoD**:
  - `.env` and `.env.local` entries present
  - `apps/api/.venv/` gitignored
  - `data/` gitignored (SQLite development DB location)
  - `apps/web/node_modules/` gitignored

---

### TA13 [DOC] Create `apps/api/README.md` and `apps/web/README.md` stubs

- **Slice**: A
- **Status**: DONE
- **Type tag**: [DOC]
- **Touches**: `apps/api/README.md`, `apps/web/README.md`
- **Traces**: REQ-001-016, design §4.4
- **Prereq tasks**: TA04, TA06
- **Estimated LOC**: 10
- **Description**: Create one-paragraph README stubs for both packages. `apps/api/README.md`: "Python backend for Wheel Vocabulary (`wheel_vocabulary` package). See the root README for installation instructions." `apps/web/README.md`: "React + TypeScript frontend for Wheel Vocabulary. See the root README for installation instructions." Slice D (TD06) will update the root README; these stubs satisfy the directory-level documentation expectation only.
- **DoD**:
  - Both files exist
  - Each contains at least one sentence and a reference to the root README

---

### TA14 [SPEC] Fix `wheel_vocab` → `wheel_vocabulary` in `design.md`

- **Slice**: A
- **Status**: DONE
- **Type tag**: [SPEC]
- **Touches**: `openspec/changes/project-foundation-bootstrap/design.md`
- **Traces**: REQ-PFB-TASK-01 (maintainer override: package name = `wheel_vocabulary`), spec REF-6
- **Prereq tasks**: none (can run in parallel with TA01)
- **Estimated LOC**: 0 (in-place edits only; ~20 occurrences of `wheel_vocab` replaced with `wheel_vocabulary` where they appear as Python identifiers — NOT in quoted SPEC-001 citations or NDD-01 rationale text which records the original decision)
- **Description**: Perform a targeted find-and-replace in `design.md`: replace every occurrence of the Python identifier `wheel_vocab` with `wheel_vocabulary` — specifically in code blocks, `[tool.hatch.build.targets.wheel]`, `[tool.ruff.lint.isort]`, `[[tool.mypy.overrides]] module = "wheel_vocab.*"`, the directory tree (§4.4), call graph paths (§6.1), JSON Schema `$id` (§6.3), Settings class docstring (§6.4), Alembic `env.py` import (§6.5), Clock port (§6.6), mypy command target (§10), and verify hooks (§14). Do NOT replace `wheel_vocab` in §4.3 NDD-01 rationale or in the NDD register's "Decision" column — that text records the original design's decision (it is historical record). Add a note at the top of §4.3: "**Override**: maintainer has decided the Python package name is `wheel_vocabulary`. This decision supersedes NDD-01. See tasks.md §1."
- **DoD**:
  - `grep -c "wheel_vocab[^u]" openspec/changes/project-foundation-bootstrap/design.md` returns 0 outside the §4.3 NDD-01 historical note
  - The NDD-01 entry in §12 is preserved with its original text + the override note

---

### TA15-SMOKE [TEST] Create `apps/api/tests/smoke/test_smoke.py`

- **Slice**: A
- **Status**: DONE
- **Type tag**: [TEST]
- **Touches**: `apps/api/tests/smoke/test_smoke.py`
- **Traces**: REQ-PFB-BOOT-01, REQ-PFB-BOOT-02, spec AC-PFB-01, AC-PFB-02, ADR-0003, Constitution Art. II.1
- **Prereq tasks**: TA03 (pytest installed), TA05 (conftest exists)
- **Estimated LOC**: 5
- **Description**: Create the **first RED test** of the cycle. File: `apps/api/tests/smoke/test_smoke.py`. Content: a single test `test_pytest_runs` that asserts `True`. This is intentionally trivial — its purpose is to prove the test runner executes. **TDD transition boundary**: from this task forward, `[BOOTSTRAP]` must not be used; every behavior begins with a `[TEST]` per Constitution Art. II.1 and REQ-PFB-BOOT-02. The test is RED before the file exists (pytest reports collection error) and GREEN after creation (the assertion passes). The smoke test is decorated with `@pytest.mark.smoke`.
- **DoD**:
  - `uv run pytest tests/smoke/test_smoke.py -v` exits 0 from `apps/api/`
  - Test is marked `@pytest.mark.smoke`
  - `make test-backend` exits 0

---

**Slice A integration check (not a task — exit criterion):**
`make bootstrap && make test-backend && make lint && make typecheck` all pass on the slice-a branch. Coverage is not gated; only `test_smoke.py` runs. `pnpm run typecheck` passes for the stub frontend.

---

## 5. Slice B1 — Backend TDD: Settings → Clock → Health route

**Exit criterion:** `make test-backend` passes; `uv run ruff check .` + `uv run ruff format --check .` pass; `uv run mypy src/wheel_vocabulary` passes; coverage report generated (severity: WARN per REQ-PFB-COV-02 — `CI_COVERAGE_MODE=warn`).

---

### TB101 [TEST] Settings loader tests (RED)

- **Slice**: B1
- **Status**: DONE
- **Type tag**: [TEST]
- **Touches**: `apps/api/tests/unit/test_settings.py`
- **Traces**: REQ-001-007, UT-BE-001, UT-BE-002, spec AC-PFB-03 (partial), design §6.4
- **Prereq tasks**: TA15-SMOKE
- **Estimated LOC**: 30
- **Description**: Write `apps/api/tests/unit/test_settings.py` with: (1) `test_settings_defaults` — constructs `Settings()` in a clean env and asserts `app_name == "wheel-vocabulary-api"`, `environment == "development"`, `database_url` starts with `sqlite:///`. (2) `test_settings_env_override` — patches `DATABASE_URL` env var, constructs `Settings()`, asserts the override is picked up. (3) `test_settings_log_level_default` — asserts `log_level == "INFO"`. Tests use `@pytest.mark.unit`. All three tests must be RED (import error or `ModuleNotFoundError`) before TB102 creates the module.
- **DoD**:
  - `uv run pytest tests/unit/test_settings.py` fails with `ModuleNotFoundError` or `ImportError` (RED confirmed)
  - Tests are decorated `@pytest.mark.unit`

---

### TB102 [IMPL] `Settings` in `infrastructure/settings.py` (GREEN)

- **Slice**: B1
- **Status**: DONE
- **Type tag**: [IMPL]
- **Touches**: `apps/api/src/wheel_vocabulary/infrastructure/settings.py`
- **Traces**: REQ-001-007, REQ-001-NF-006, design §6.4 (NDD-07), spec AC-PFB-03
- **Prereq tasks**: TB101
- **Estimated LOC**: 35
- **Description**: Implement `Settings(BaseSettings)` per design §6.4: fields `app_name`, `app_version` (reads from `importlib.metadata.version("wheel-vocabulary")` with fallback to `"0.1.0"`), `environment`, `database_url` (default `sqlite:///./data/wheel_vocabulary.db`), `cors_origins`, `log_level`. Include `model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")`. Add `get_settings()` factory with `@lru_cache`. Module-level `__all__` exports `Settings` and `get_settings`. All mypy annotations must pass (`infrastructure.*` is gradual, but no bare `Any` in fields). A single `# type: ignore[code]` is permitted only if a specific SQLAlchemy/pydantic interaction forces it, with a citation comment.
- **DoD**:
  - `uv run pytest tests/unit/test_settings.py -v` exits 0 (all three tests GREEN)
  - `uv run mypy src/wheel_vocabulary/infrastructure/settings.py` exits 0
  - `uv run ruff check src/wheel_vocabulary/infrastructure/settings.py` exits 0

---

### TB103 [TEST] `Clock` port and `FrozenClock` tests (RED)

- **Slice**: B1
- **Status**: DONE
- **Type tag**: [TEST]
- **Touches**: `apps/api/tests/unit/test_clock.py`
- **Traces**: REQ-PFB-CONTRACT-01 (timestamp semantics), design §6.2, design §6.6, ADR-0002 (port in application), Constitution Art. VII.1
- **Prereq tasks**: TB102
- **Estimated LOC**: 20
- **Description**: Write `apps/api/tests/unit/test_clock.py` with: (1) `test_clock_protocol_is_structural` — verifies `Clock` is a `typing.Protocol` (structural subtyping: a class with `now_utc() -> datetime` satisfies it without inheriting). (2) `test_system_clock_returns_utc` — instantiates `SystemClock`, calls `now_utc()`, asserts the result is timezone-aware and UTC. (3) `test_frozen_clock_returns_fixed_time` — instantiates `FrozenClock(fixed_dt)`, asserts `now_utc()` returns exactly `fixed_dt`. `FrozenClock` is a test double defined in the test file itself (or in `conftest.py` if shared). All tests `@pytest.mark.unit`. Tests must be RED before TB104/TB105.
- **DoD**:
  - `uv run pytest tests/unit/test_clock.py` fails (RED: import error on `wheel_vocabulary.application.clock`)

---

### TB104 [IMPL] `Clock` protocol in `application/clock.py` + `SystemClock` in `infrastructure/clock.py` (GREEN)

- **Slice**: B1
- **Status**: DONE
- **Type tag**: [IMPL]
- **Touches**: `apps/api/src/wheel_vocabulary/application/clock.py`, `apps/api/src/wheel_vocabulary/infrastructure/clock.py`
- **Traces**: design §6.2, design §6.6, ADR-0002, Constitution Art. VII.1 (domain purity — `application/` has zero framework imports)
- **Prereq tasks**: TB103
- **Estimated LOC**: 20
- **Description**: Implement `Clock` protocol in `application/clock.py` — a `typing.Protocol` with `now_utc(self) -> datetime`. No framework imports; only `typing` and `datetime`. Module MUST be `mypy --strict` clean (it is in `application.*` strict override). Implement `SystemClock` in `infrastructure/clock.py` — `def now_utc(self) -> datetime: return datetime.now(tz=timezone.utc)`. Add `FrozenClock` to `apps/api/tests/conftest.py` as a shared fixture for test injection.
- **DoD**:
  - `uv run pytest tests/unit/test_clock.py -v` exits 0 (GREEN)
  - `uv run mypy src/wheel_vocabulary/application/clock.py` exits 0 with strict mode
  - `uv run mypy src/wheel_vocabulary/infrastructure/clock.py` exits 0

---

### TB105 [TEST] Version reader tests (RED)

- **Slice**: B1
- **Status**: DONE
- **Type tag**: [TEST]
- **Touches**: `apps/api/tests/unit/test_version.py`
- **Traces**: REQ-PFB-CONTRACT-01 (`version` field must match package metadata), design §6.4 (`app_version` source)
- **Prereq tasks**: TB104
- **Estimated LOC**: 10
- **Description**: Write `apps/api/tests/unit/test_version.py` with: (1) `test_get_version_returns_string` — calls `get_package_version()`, asserts result is a non-empty string matching `^\d+\.\d+\.\d+`. (2) `test_get_version_fallback` — mocks `importlib.metadata.version` to raise `PackageNotFoundError`, asserts `get_package_version()` returns the fallback string `"0.0.0"` (or another documented fallback). Tests `@pytest.mark.unit`. Tests must be RED before TB106.
- **DoD**:
  - `uv run pytest tests/unit/test_version.py` fails (RED: import error)

---

### TB106 [IMPL] Version reader in `infrastructure/version.py` (GREEN)

- **Slice**: B1
- **Status**: DONE
- **Type tag**: [IMPL]
- **Touches**: `apps/api/src/wheel_vocabulary/infrastructure/version.py`
- **Traces**: REQ-PFB-CONTRACT-01, design §6.4
- **Prereq tasks**: TB105
- **Estimated LOC**: 10
- **Description**: Implement `get_package_version() -> str` using `importlib.metadata.version("wheel-vocabulary")` with `except PackageNotFoundError: return "0.0.0"`. Export via `__all__`. Gradual mypy applies (`infrastructure.*`); but no bare `Any` allowed.
- **DoD**:
  - `uv run pytest tests/unit/test_version.py -v` exits 0 (GREEN)

---

### TB107 [SPEC] Create `apps/api/src/wheel_vocabulary/api/schemas/health.v1.json`

- **Slice**: B1
- **Status**: DONE
- **Type tag**: [SPEC]
- **Touches**: `apps/api/src/wheel_vocabulary/api/schemas/health.v1.json`
- **Traces**: REQ-PFB-CONTRACT-01, design §6.3, spec §9 Hook 4, Constitution Art. VIII.1
- **Prereq tasks**: TB106
- **Estimated LOC**: 20
- **Description**: Create the JSON Schema file per design §6.3 verbatim: `$schema` Draft 2020-12, `$id: "urn:wheel-vocabulary:health:v1"`, `type: object`, `required: ["status","service","version","timestamp"]`, `additionalProperties: false`, properties: `status` (`const: "ok"`), `service` (`const: "wheel-vocabulary-api"`), `version` (pattern `^\d+\.\d+\.\d+`), `timestamp` (pattern for ISO-8601 UTC ms). Also create `apps/api/src/wheel_vocabulary/api/schemas/__init__.py` so the directory is importable via `importlib.resources.files("wheel_vocabulary.api.schemas")`.
- **DoD**:
  - `python -c "import json; json.load(open('apps/api/src/wheel_vocabulary/api/schemas/health.v1.json'))"` exits 0
  - `additionalProperties: false` present
  - Schema `$id` contains `wheel-vocabulary`

---

### TB108 [TEST] `HealthResponse` DTO tests (RED)

- **Slice**: B1
- **Status**: DONE
- **Type tag**: [TEST]
- **Touches**: `apps/api/tests/unit/test_health_dto.py`
- **Traces**: REQ-001-002, REQ-PFB-CONTRACT-01, design §6.3, UT-BE-003
- **Prereq tasks**: TB107
- **Estimated LOC**: 15
- **Description**: Write `apps/api/tests/unit/test_health_dto.py` with: (1) `test_health_response_valid_construction` — constructs `HealthResponse(status="ok", service="wheel-vocabulary-api", version="0.1.0", timestamp="2026-07-20T00:00:00.000Z")` and asserts field values. (2) `test_health_response_schema_validation` — loads `health.v1.json` via `importlib.resources`, validates a constructed `HealthResponse.model_dump()` against it using `jsonschema.validate`. (3) `test_health_response_rejects_extra_fields` — asserts that constructing with an extra field raises a validation error (Pydantic strict model). Tests `@pytest.mark.unit`. Tests must be RED before TB109.
- **DoD**:
  - `uv run pytest tests/unit/test_health_dto.py` fails (RED: import error on `wheel_vocabulary.api.dtos.health`)

---

### TB109 [IMPL] `HealthResponse` DTO in `api/dtos/health.py` (GREEN)

- **Slice**: B1
- **Status**: DONE
- **Type tag**: [IMPL]
- **Touches**: `apps/api/src/wheel_vocabulary/api/dtos/health.py`, `apps/api/src/wheel_vocabulary/api/dtos/__init__.py`
- **Traces**: REQ-001-002, REQ-PFB-CONTRACT-01, design §6.3
- **Prereq tasks**: TB108
- **Estimated LOC**: 15
- **Description**: Implement `HealthResponse(BaseModel)` with fields `status: Literal["ok"]`, `service: str`, `version: str`, `timestamp: str`. Use `model_config = ConfigDict(extra="forbid")` to reject extra fields. No framework imports beyond `pydantic`. Gradual mypy applies for `api.*`; no bare `Any` in field types.
- **DoD**:
  - `uv run pytest tests/unit/test_health_dto.py -v` exits 0 (GREEN)

---

### TB110 [TEST] `GET /api/v1/health` route tests (RED)

- **Slice**: B1
- **Status**: DONE
- **Type tag**: [TEST]
- **Touches**: `apps/api/tests/api/test_health.py`
- **Traces**: REQ-001-001, REQ-001-002, REQ-PFB-CONTRACT-01, AC-PFB-10, API-BE-001, spec §9 Hook 4, design §6.1
- **Prereq tasks**: TB109
- **Estimated LOC**: 40
- **Description**: Write `apps/api/tests/api/test_health.py` with a `@pytest.fixture` `client` that creates a `TestClient(create_app())` and overrides `get_clock` dependency with `FrozenClock`. Tests (all `@pytest.mark.unit`): (1) `test_health_status_200` — asserts `GET /api/v1/health` returns 200. (2) `test_health_response_body` — asserts body has keys `status`, `service`, `version`, `timestamp`. (3) `test_health_status_ok` — asserts `body["status"] == "ok"`. (4) `test_health_service_name` — asserts `body["service"] == "wheel-vocabulary-api"`. (5) `test_health_version_matches_package` — reads `pyproject.toml` and asserts `body["version"]` matches the version field. (6) `test_health_timestamp_frozen` — injects `FrozenClock` and asserts `body["timestamp"]` equals the frozen datetime formatted as ISO-8601 UTC ms. (7) `test_health_schema_validation` — loads `health.v1.json` via `importlib.resources`, calls `jsonschema.validate(body, schema)` (Hook 4). (8) `test_health_x_schema_version_header` — asserts response header `X-Schema-Version: 1`. (9) `test_health_no_extra_fields` — asserts `set(body.keys()) == {"status","service","version","timestamp"}`. Tests must be RED before TB111.
- **DoD**:
  - `uv run pytest tests/api/test_health.py` fails (RED: import error on `wheel_vocabulary.api`)

---

### TB111 [IMPL] FastAPI app factory and health route (GREEN)

- **Slice**: B1
- **Status**: DONE
- **Type tag**: [IMPL]
- **Touches**: `apps/api/src/wheel_vocabulary/api/main.py`, `apps/api/src/wheel_vocabulary/api/routes/health.py`
- **Traces**: REQ-001-001, REQ-001-002, REQ-PFB-CONTRACT-01, design §6.1, design §6.2, ADR-0002, Constitution Art. VII.4
- **Prereq tasks**: TB110
- **Estimated LOC**: 45
- **Description**: Implement `create_app() -> FastAPI` factory in `api/main.py` — creates `FastAPI(title="Wheel Vocabulary API")`, includes the health router via `app.include_router(health.router)`. Implement `get_clock()` dependency provider returning `SystemClock()`. Implement health router in `api/routes/health.py`: `APIRouter(prefix="/api/v1")`, `@router.get("/health", response_model=HealthResponse)` handler that takes `Settings` via `Depends(get_settings)` and `Clock` via `Depends(get_clock)`, returns `HealthResponse(status="ok", service=settings.app_name, version=settings.app_version, timestamp=<clock.now_utc() formatted as ISO-8601 UTC ms>)`, and adds `X-Schema-Version: 1` response header. Import path: `from wheel_vocabulary.application.clock import Clock` (port). `SystemClock` injected via `infrastructure.clock.SystemClock` from the dependency provider — route handler never imports `SystemClock` directly (ADR-0002).
- **DoD**:
  - `uv run pytest tests/api/test_health.py -v` exits 0 (all nine tests GREEN)
  - `make test-backend` exits 0
  - `uv run mypy src/wheel_vocabulary` exits 0
  - `uv run ruff check .` exits 0 from `apps/api/`

---

### TB112 [REFACTOR] Health route and factory cleanup (if needed)

- **Slice**: B1
- **Status**: DONE
- **Type tag**: [REFACTOR]
- **Touches**: `apps/api/src/wheel_vocabulary/api/main.py`, `apps/api/src/wheel_vocabulary/api/routes/health.py` (if any duplication surfaced)
- **Traces**: Constitution Art. VII.6 (no speculative abstraction), ADR-0003 §Decision (no anticipatory scaffolding)
- **Prereq tasks**: TB111
- **Estimated LOC**: 0–10 (only if real duplication exists)
- **Description**: If TB111 introduced duplication (e.g., timestamp-formatting logic duplicated between handler and test, or import block that should be a utility), address it here. Do NOT introduce new abstractions (`HealthCheckService`, `ResponseFormatter`) that have no second user per Constitution Art. VII.6 NDD-06. If no duplication exists, this task is a no-op (verified by inspection in < 5 minutes).
- **DoD**:
  - `make test-backend` still exits 0 after any refactor
  - No `HealthCheckService` or speculative class introduced
  - Coverage report generated (severity WARN)

---

## 6. Slice B2 — Backend TDD: SQLAlchemy + Alembic

**Exit criterion:** `make test-backend` passes including integration tests; `make migrate` exits 0 against a temp SQLite DB; coverage report generated (severity: WARN per REQ-PFB-COV-02).

---

### TB201 [TEST] SQLAlchemy engine + session factory tests (RED)

- **Slice**: B2
- **Type tag**: [TEST]
- **Touches**: `apps/api/tests/integration/test_engine.py`
- **Traces**: REQ-001-005, INT-BE-001, design §6.5
- **Prereq tasks**: TB112
- **Estimated LOC**: 20
- **Description**: Write `apps/api/tests/integration/test_engine.py` with `@pytest.mark.integration` tests: (1) `test_engine_creates_from_settings` — creates engine from `Settings(database_url="sqlite:///:memory:")`, asserts it is a `sqlalchemy.Engine` instance. (2) `test_session_factory_yields_session` — uses `get_session()` context manager or factory, asserts yielded object is a SQLAlchemy `Session`. (3) `test_sqlite_trivial_query` — executes `select(1)` against a `:memory:` engine, asserts the result. Tests must be RED before TB202.
- **DoD**:
  - `uv run pytest tests/integration/test_engine.py` fails (RED: import error on `wheel_vocabulary.infrastructure.persistence.engine`)

---

### TB202 [IMPL] SQLAlchemy engine + session factory in `infrastructure/persistence/engine.py` (GREEN)

- **Slice**: B2
- **Type tag**: [IMPL]
- **Touches**: `apps/api/src/wheel_vocabulary/infrastructure/persistence/engine.py`
- **Traces**: REQ-001-005, design §6.5, ADR-0001 (SQLAlchemy 2)
- **Prereq tasks**: TB201
- **Estimated LOC**: 25
- **Description**: Implement `create_engine(url: str) -> Engine` wrapper and `get_session()` context manager (or session factory) using SQLAlchemy 2 `create_engine` and `sessionmaker`. Accept `database_url` string. Integrate with `Settings` via dependency injection path (not imported directly in routes; dependency provider wraps it). `# type: ignore[assignment]` or similar is permitted ONLY if SQLAlchemy 2 ORM descriptors require it, with an inline citation comment: `# sqlalchemy 2 typing; see REQ-001-012 NDD-04`.
- **DoD**:
  - `uv run pytest tests/integration/test_engine.py -v` exits 0 (GREEN)

---

### TB203 [TEST] `DeclarativeBase` presence test (RED)

- **Slice**: B2
- **Type tag**: [TEST]
- **Touches**: `apps/api/tests/integration/test_base.py`
- **Traces**: REQ-PFB-CONTRACT-02 (empty-schema baseline), design §6.5, DEC-005
- **Prereq tasks**: TB202
- **Estimated LOC**: 5
- **Description**: Write `apps/api/tests/integration/test_base.py` with `@pytest.mark.integration test_base_metadata_is_empty` — imports `Base` from `wheel_vocabulary.infrastructure.persistence.base`, asserts `len(Base.metadata.tables) == 0`. This confirms no domain tables are pre-registered on `Base`, satisfying DEC-005 and CONTRACT-2. Test must be RED before TB204.
- **DoD**:
  - `uv run pytest tests/integration/test_base.py` fails (RED: import error)

---

### TB204 [IMPL] `DeclarativeBase` in `infrastructure/persistence/base.py` (GREEN)

- **Slice**: B2
- **Type tag**: [IMPL]
- **Touches**: `apps/api/src/wheel_vocabulary/infrastructure/persistence/base.py`
- **Traces**: REQ-PFB-CONTRACT-02, design §6.5, DEC-005, Constitution Art. VII.6
- **Prereq tasks**: TB203
- **Estimated LOC**: 10
- **Description**: Implement `Base(DeclarativeBase)` with `pass` body. No domain models registered here. Export `Base` in `__all__`. A single `# type: ignore[misc]` may be needed for `DeclarativeBase` metaclass with a citation: `# sqlalchemy 2 DeclarativeBase metaclass; see NDD-04`.
- **DoD**:
  - `uv run pytest tests/integration/test_base.py -v` exits 0 (GREEN: `Base.metadata.tables` is empty)

---

### TB205 [MIGRATION] Create Alembic scaffold: `alembic.ini`, `apps/api/migrations/env.py`, `script.py.mako`, `0001_baseline.py`

- **Slice**: B2
- **Type tag**: [MIGRATION]
- **Touches**: `apps/api/alembic.ini`, `apps/api/migrations/env.py`, `apps/api/migrations/script.py.mako`, `apps/api/migrations/versions/0001_baseline.py`
- **Traces**: REQ-001-006, REQ-PFB-CONTRACT-02, design §6.5, spec AC-PFB-11
- **Prereq tasks**: TB204
- **Estimated LOC**: 70 (alembic.ini ~15, env.py ~30, script.py.mako ~10, 0001_baseline.py ~15)
- **Description**: Create `alembic.ini` pointing `script_location = migrations`. Create `apps/api/migrations/env.py` that imports `Base` from `wheel_vocabulary.infrastructure.persistence.base`, sets `target_metadata = Base.metadata`, and configures both offline and online migration paths with `run_migrations_offline()` / `run_migrations_online()`. Create standard `script.py.mako`. Create `migrations/versions/0001_baseline.py` with `revision = "0001"`, `down_revision = None`, `upgrade()` as `pass` (empty-schema baseline per CONTRACT-2 — no `op.create_table` calls), `downgrade()` as `pass`. The revision file MUST include a comment: `# empty-schema baseline; no user tables created (CONTRACT-2, DEC-005)`. Note: generated Alembic file (0001_baseline.py) is excluded from authored LOC count per review-budget convention.
- **DoD**:
  - `uv run alembic upgrade head` exits 0 from `apps/api/` against a `:memory:` URL
  - `uv run alembic downgrade base` exits 0
  - `0001_baseline.py upgrade()` contains only `pass` (no `op.create_table`)

---

### TB206 [TEST] Alembic baseline integration tests (RED)

- **Slice**: B2
- **Type tag**: [TEST]
- **Touches**: `apps/api/tests/integration/test_alembic.py`
- **Traces**: REQ-001-006, INT-BE-002, INT-BE-003, spec AC-PFB-11, design §6.5
- **Prereq tasks**: TB205
- **Estimated LOC**: 20
- **Description**: Write `apps/api/tests/integration/test_alembic.py` with `@pytest.mark.integration` tests: (1) `test_alembic_upgrade_head_succeeds` — runs `alembic upgrade head` via `subprocess` or Alembic's Python API against a temp SQLite file, asserts exit 0, asserts `alembic_version` table exists with one row. (2) `test_alembic_no_user_tables` — after upgrade head, inspects `inspector.get_table_names()`, asserts the only table is `alembic_version`. (3) `test_alembic_downgrade_base` — runs `alembic downgrade base`, asserts exit 0. Tests must be RED before TB205 is complete (import error or runtime error).
- **DoD**:
  - Before TB205 fix: `uv run pytest tests/integration/test_alembic.py` fails
  - After TB205: `uv run pytest tests/integration/test_alembic.py -v` exits 0 (all three GREEN)
  - `make test-backend` exits 0

---

### TB207 [IMPL] Wire integration test fixtures in `conftest.py`

- **Slice**: B2
- **Type tag**: [IMPL]
- **Touches**: `apps/api/tests/conftest.py`
- **Traces**: REQ-001-009, design §4.5, ADR-0003
- **Prereq tasks**: TB206
- **Estimated LOC**: 15
- **Description**: Add integration-test fixtures to `apps/api/tests/conftest.py`: (1) `tmp_db_url` fixture (scope `function`) — creates a temp SQLite file, yields `sqlite:////<path>`, cleans up. (2) `alembic_config` fixture — returns an `alembic.config.Config` pointing at `apps/api/alembic.ini` with `sqlalchemy.url` overridden to `tmp_db_url`. These shared fixtures make `test_alembic.py` and future integration tests cleaner. Confirm TB206 still passes.
- **DoD**:
  - `make test-backend` exits 0
  - Coverage report generated (WARN mode)

---

### TB208 [REFACTOR] Persistence layer cleanup (if needed)

- **Slice**: B2
- **Type tag**: [REFACTOR]
- **Touches**: `apps/api/src/wheel_vocabulary/infrastructure/persistence/` (if duplication exists)
- **Traces**: Constitution Art. VII.6, ADR-0003
- **Prereq tasks**: TB207
- **Estimated LOC**: 0–10
- **Description**: If TB202–TB204 introduced any duplication (e.g., URL string construction logic repeated in tests vs. implementation, or `create_engine` called with divergent parameters in two places), resolve it here. Do not introduce speculative abstractions. If clean, this task is a no-op.
- **DoD**:
  - `make test-backend` exits 0
  - `uv run mypy src/wheel_vocabulary` exits 0
  - `uv run ruff check .` exits 0

---

## 7. Slice C — Frontend TDD

**Exit criterion:** `make test-frontend` passes; `pnpm run typecheck` passes; `pnpm run lint` passes; `make dev` boots both servers without errors.

---

### TC01 [TEST] `fetchHealth()` API client tests (RED)

- **Slice**: C
- **Type tag**: [TEST]
- **Touches**: `apps/web/tests/api/client.test.ts`
- **Traces**: REQ-001-004, design §7.3, ADR-0005 (local-first, no external egress)
- **Prereq tasks**: TB208
- **Estimated LOC**: 25
- **Description**: Write `apps/web/tests/api/client.test.ts` (path: `apps/web/src/` adjacent or under `apps/web/tests/` per Vitest config). Tests: (1) `fetchHealth calls correct URL` — mocks `fetch`, verifies `${VITE_API_BASE_URL}/api/v1/health` is called. (2) `fetchHealth returns parsed JSON on 200` — mocks `fetch` returning a valid `HealthResponse` JSON, asserts return value matches. (3) `fetchHealth throws on non-2xx` — mocks `fetch` returning 500, asserts thrown error contains `HTTP 500`. (4) `fetchHealth throws on network error` — mocks `fetch` to reject, asserts error propagates. Also create `apps/web/src/types/health.ts` with `HealthResponse` interface per design §7.2 as a prerequisite data contract. Tests must be RED.
- **DoD**:
  - `pnpm run test` fails (RED: module not found for `./client`)

---

### TC02 [IMPL] `apps/web/src/api/client.ts` (GREEN)

- **Slice**: C
- **Type tag**: [IMPL]
- **Touches**: `apps/web/src/api/client.ts`, `apps/web/src/types/health.ts`
- **Traces**: REQ-001-004, design §7.3, NDD-08 (no TanStack Query), Constitution Art. VII.6
- **Prereq tasks**: TC01
- **Estimated LOC**: 23
- **Description**: Implement `fetchHealth(): Promise<HealthResponse>` per design §7.3: `const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"`, `fetch()` call, non-2xx throws `Error("HTTP ${resp.status}")`, returns `resp.json() as Promise<HealthResponse>`. Also finalize `apps/web/src/types/health.ts` with `HealthResponse` interface matching CONTRACT-1 (`status: "ok"`, `service: string`, `version: string`, `timestamp: string`).
- **DoD**:
  - `pnpm run test -- tests/api/client.test.ts` exits 0 (GREEN)
  - TypeScript: `pnpm run typecheck` exits 0

---

### TC03 [TEST] `<StatusLoading>` component tests (RED)

- **Slice**: C
- **Type tag**: [TEST]
- **Touches**: `apps/web/tests/components/StatusLoading.test.tsx`
- **Traces**: REQ-001-004, REQ-001-NF-005, UT-FE-001, A11Y-FE-001 (partial), design §7.2, spec CONTRACT-3
- **Prereq tasks**: TC02
- **Estimated LOC**: 10
- **Description**: Write test: (1) `renders loading text` — renders `<StatusLoading />`, asserts `getByText("Comprobando estado")` is in the DOM. (2) `has aria-live polite` — asserts the loading element has `aria-live="polite"`. Must be RED before TC04.
- **DoD**:
  - `pnpm run test -- tests/components/StatusLoading.test.tsx` fails (RED)

---

### TC04 [IMPL] `apps/web/src/components/StatusLoading.tsx` (GREEN)

- **Slice**: C
- **Type tag**: [IMPL]
- **Touches**: `apps/web/src/components/StatusLoading.tsx`
- **Traces**: REQ-001-NF-005, design §7.2, Constitution Art. IX.3, ADR-0010 (Spanish UI copy)
- **Prereq tasks**: TC03
- **Estimated LOC**: 15
- **Description**: Implement pure presentational component: `<p aria-live="polite">Comprobando estado</p>`. No props. Spanish UI copy per ADR-0010 §2. English identifiers (component name `StatusLoading`, function name).
- **DoD**:
  - `pnpm run test -- tests/components/StatusLoading.test.tsx` exits 0 (GREEN)

---

### TC05 [TEST] `<StatusHealthy>` component tests (RED)

- **Slice**: C
- **Type tag**: [TEST]
- **Touches**: `apps/web/tests/components/StatusHealthy.test.tsx`
- **Traces**: REQ-001-004, AC-003, UT-FE-002, design §7.2, spec CONTRACT-3 (Healthy state)
- **Prereq tasks**: TC04
- **Estimated LOC**: 15
- **Description**: Tests: (1) `displays Backend disponible` — renders with props, asserts text "Backend disponible". (2) `displays version from props` — asserts `version` value visible in DOM. (3) `displays timestamp from props` — asserts `timestamp` value visible in DOM. Must be RED.
- **DoD**:
  - `pnpm run test -- tests/components/StatusHealthy.test.tsx` fails (RED)

---

### TC06 [IMPL] `apps/web/src/components/StatusHealthy.tsx` (GREEN)

- **Slice**: C
- **Type tag**: [IMPL]
- **Touches**: `apps/web/src/components/StatusHealthy.tsx`
- **Traces**: REQ-001-004, AC-003, design §7.2, spec CONTRACT-3
- **Prereq tasks**: TC05
- **Estimated LOC**: 20
- **Description**: Implement `StatusHealthy({ service, version, timestamp }: StatusHealthyProps)`. Renders: `<p>Backend disponible</p>` (per AC-003), `<p>version: {version}</p>`, `<p>timestamp: {timestamp}</p>` (or equivalent accessible elements). Props interface: `{ service: string; version: string; timestamp: string }`.
- **DoD**:
  - `pnpm run test -- tests/components/StatusHealthy.test.tsx` exits 0 (GREEN)

---

### TC07 [TEST] `<StatusError>` component tests (RED)

- **Slice**: C
- **Type tag**: [TEST]
- **Touches**: `apps/web/tests/components/StatusError.test.tsx`
- **Traces**: REQ-001-004, AC-004, UT-FE-003, UT-FE-004, A11Y-FE-001, design §7.2, spec CONTRACT-3 (Error state)
- **Prereq tasks**: TC06
- **Estimated LOC**: 15
- **Description**: Tests: (1) `displays Backend no disponible` — renders with message prop, asserts text "Backend no disponible". (2) `displays retry button with accessible name` — asserts `getByRole("button", { name: /reintentar/i })` is present. (3) `retry button calls onRetry` — clicks button, asserts `onRetry` mock was called once. (4) `no stack trace in output` — asserts error stack trace text is NOT in DOM. Must be RED.
- **DoD**:
  - `pnpm run test -- tests/components/StatusError.test.tsx` fails (RED)

---

### TC08 [IMPL] `apps/web/src/components/StatusError.tsx` (GREEN)

- **Slice**: C
- **Type tag**: [IMPL]
- **Touches**: `apps/web/src/components/StatusError.tsx`
- **Traces**: REQ-001-004, AC-004, REQ-001-NF-005, A11Y-FE-001, design §7.2, Constitution Art. IX.2
- **Prereq tasks**: TC07
- **Estimated LOC**: 20
- **Description**: Implement `StatusError({ message, onRetry }: StatusErrorProps)`. Renders: `<p>Backend no disponible</p>`, a human-readable message (from props), `<button aria-label="Reintentar" onClick={onRetry}>Reintentar</button>`. MUST NOT render stack traces or raw error objects. Props: `{ message: string; onRetry: () => void }`.
- **DoD**:
  - `pnpm run test -- tests/components/StatusError.test.tsx` exits 0 (GREEN)
  - No stack trace text exposed per spec CONTRACT-3

---

### TC09 [TEST] `<StatusPage>` orchestration tests (RED)

- **Slice**: C
- **Type tag**: [TEST]
- **Touches**: `apps/web/tests/components/StatusPage.test.tsx`
- **Traces**: REQ-001-004, UT-FE-001–004, A11Y-FE-001, spec AC-PFB-12, design §7.2 + §7.4
- **Prereq tasks**: TC08
- **Estimated LOC**: 30
- **Description**: Write tests using `vi.mock("../api/client")` to mock `fetchHealth`: (1) `shows loading state initially` — mock returns a never-resolving promise, asserts "Comprobando estado" is visible. (2) `shows healthy state on success` — mock resolves with `HealthResponse`, asserts "Backend disponible" and version/timestamp visible. (3) `shows error state on failure` — mock rejects, asserts "Backend no disponible" visible, retry button present. (4) `retry button triggers re-fetch` — after error state, clicks retry button, asserts `fetchHealth` called twice. (5) `no stack trace on error` — asserts no stack trace present. Must be RED.
- **DoD**:
  - `pnpm run test -- tests/components/StatusPage.test.tsx` fails (RED)

---

### TC10 [IMPL] `apps/web/src/pages/StatusPage.tsx` (GREEN)

- **Slice**: C
- **Type tag**: [IMPL]
- **Touches**: `apps/web/src/pages/StatusPage.tsx`
- **Traces**: REQ-001-004, design §7.2 + §7.4, Constitution Art. VII.6 (NDD-08: no TanStack Query)
- **Prereq tasks**: TC09
- **Estimated LOC**: 30
- **Description**: Implement `StatusPage` using `useState` + `useEffect` per design §7.4. Three states: `"loading"`, `"healthy"` (with `HealthResponse` payload), `"error"` (with string message). On mount, call `fetchHealth()`, transition to healthy or error. Retry handler: `setStatus("loading")` + increment `retryCount` state to re-trigger `useEffect`. Render: `{status === "loading" && <StatusLoading />}`, `{status === "healthy" && <StatusHealthy ...props />}`, `{status === "error" && <StatusError message={...} onRetry={retry} />}`. No global state, no reducer, no context.
- **DoD**:
  - `pnpm run test -- tests/components/StatusPage.test.tsx` exits 0 (all five GREEN)

---

### TC11 [IMPL] Wire `<StatusPage>` into `App.tsx` and `main.tsx`

- **Slice**: C
- **Type tag**: [IMPL]
- **Touches**: `apps/web/src/App.tsx`, `apps/web/src/main.tsx`
- **Traces**: REQ-001-003, REQ-001-004, design §4.4
- **Prereq tasks**: TC10
- **Estimated LOC**: 20
- **Description**: Replace the Slice A stub `App.tsx` with a real version that renders `<StatusPage />`. `main.tsx` mounts `<React.StrictMode><App /></React.StrictMode>` on `#root`. No routing (single-page, single route `"/"` per spec CONTRACT-3 out-of-scope note). Verify `pnpm run dev` boots both servers (Vite dev server) and the status page displays in browser.
- **DoD**:
  - `pnpm run typecheck` exits 0
  - `make dev` boots both servers without errors
  - Browser shows loading → healthy (when backend is running) or loading → error (when backend is stopped)

---

### TC12 [SPEC] Create `apps/web/src/styles/status.css`

- **Slice**: C
- **Type tag**: [SPEC]
- **Touches**: `apps/web/src/styles/status.css`, `apps/web/src/main.tsx` (import)
- **Traces**: design §7.5 (NDD-09: plain CSS), Constitution Art. VII.6
- **Prereq tasks**: TC11
- **Estimated LOC**: 20
- **Description**: Create `src/styles/status.css` with minimal three-state styling: a container class, styles for the loading state (neutral), healthy state (green-tinted or green indicator — but NOT color-only per REQ-001-NF-005; use text too), error state (red-tinted). Import in `main.tsx`. No Tailwind, no CSS Modules. Plain CSS with BEM-ish or semantic class names. The visual design is minimal; the requirement is that the three states are visually distinct and text-first accessible.
- **DoD**:
  - `src/styles/status.css` exists and is imported in `main.tsx`
  - Three state classes present
  - No Tailwind utility classes

---

### TC13 [REFACTOR] Frontend cleanup (if needed)

- **Slice**: C
- **Type tag**: [REFACTOR]
- **Touches**: `apps/web/src/` (any file with duplication)
- **Traces**: Constitution Art. VII.6
- **Prereq tasks**: TC12
- **Estimated LOC**: 0–10
- **Description**: If TC01–TC12 introduced duplication in test mocks, component prop-passing, or CSS class naming, address it. Do not introduce abstractions that don't exist yet (no `useHealthStatus` hook unless two components share the same fetch logic — they don't). If clean, no-op.
- **DoD**:
  - `make test-frontend` exits 0
  - `pnpm run typecheck` exits 0
  - `make dev` still boots cleanly

---

## 8. Slice D — E2E + CI + Docs + Traceability

**Exit criterion:** All CI jobs green on tracker branch; `make lint && make typecheck && make test && make test-e2e` local pass; traceability grep test passes; README reflects SPEC-001 IMPLEMENTED; testing-capabilities Engram cache updated.

---

### TD01 [E2E] Create `apps/web/e2e/status.spec.ts`

- **Slice**: D
- **Type tag**: [E2E]
- **Touches**: `apps/web/e2e/status.spec.ts`
- **Traces**: REQ-001-011, REQ-PFB-CONTRACT-04, E2E-001, spec AC-PFB-13, design §8.2
- **Prereq tasks**: TC13
- **Estimated LOC**: 30
- **Description**: Write the single Playwright E2E spec per design §8. Test `E2E-001 — integrated health status`: (1) Navigate to frontend root URL (`/`). (2) Wait for and assert product name or heading text is visible. (3) Wait for `"Backend disponible"` text to be visible (implicit wait via `expect(page.getByText("Backend disponible")).toBeVisible()`). (4) Assert version string is visible somewhere in the DOM. (5) Assert timestamp string is visible. No `setTimeout`, no `sleep()`, no `waitForTimeout`. Use `page.waitForLoadState("networkidle")` or Playwright's built-in retry before assertions.
- **DoD**:
  - `apps/web/e2e/status.spec.ts` exists with exactly one `test()` block
  - No hardcoded `sleep()` or `setTimeout()` calls

---

### TD02 [E2E] Update `apps/web/playwright.config.ts` with `webServer` and browser matrix

- **Slice**: D
- **Type tag**: [E2E]
- **Touches**: `apps/web/playwright.config.ts`
- **Traces**: REQ-PFB-CONTRACT-04, design §8.1 + §8.3, spec AC-PFB-13 + AC-PFB-15
- **Prereq tasks**: TD01
- **Estimated LOC**: 40
- **Description**: Create/update `apps/web/playwright.config.ts` per design §8 verbatim: two `webServer` entries (backend: `cd ../../ && make dev-backend`, polls `http://localhost:8000/api/v1/health`; frontend: `pnpm run dev`, polls `http://localhost:5173`); `reuseExistingServer: !process.env.CI`; timeout 30s each. Browser matrix: exactly one project `chromium` using `devices["Desktop Chrome"]`. Artifacts: `screenshot: "only-on-failure"`, `video: "retain-on-failure"`, `trace: "on-first-retry"`. Test dir: `e2e/`.
- **DoD**:
  - `playwright.config.ts` has exactly one `projects` entry (`chromium`)
  - Two `webServer` entries present
  - `make test-e2e` exits 0 (with both servers running, or via Playwright's `webServer` auto-start)

---

### TD03 [CI] Create `.github/workflows/ci.yml`

- **Slice**: D
- **Type tag**: [CI]
- **Touches**: `.github/workflows/ci.yml`
- **Traces**: REQ-001-014, REQ-PFB-CONTRACT-05, spec AC-PFB-14 + AC-PFB-15, design §9.2 + §9.3, ADR-0001
- **Prereq tasks**: TD02
- **Estimated LOC**: 120
- **Description**: Create `.github/workflows/ci.yml` triggered on `push` and `pull_request` (all branches). Implement the 10-job DAG from design §9.2: `setup-python`, `setup-node`, `backend-lint` (needs `setup-python`), `backend-typecheck` (needs `setup-python`), `backend-test` (needs `setup-python`; `CI_COVERAGE_MODE: fail`), `migration-check` (needs `setup-python`), `frontend-lint` (needs `setup-node`), `frontend-typecheck` (needs `setup-node`), `frontend-test` (needs `setup-node`; `CI_COVERAGE_MODE: fail`), `e2e` (needs `backend-test` AND `frontend-test`). All jobs on `ubuntu-latest`. Cache keys: `apps/api/uv.lock` (Python), `apps/web/pnpm-lock.yaml` (Node). `CI_COVERAGE_MODE: fail` activates `--cov-fail-under=80` for backend and coverage threshold in vitest per REQ-PFB-COV-02. `backend-typecheck` runs `uv run mypy src/wheel_vocabulary`. E2E job runs `pnpm exec playwright install chromium && pnpm exec playwright test`.
- **DoD**:
  - All 10 job names from design §9.2 present
  - All jobs on `ubuntu-latest`
  - `CI_COVERAGE_MODE: fail` set in `backend-test` and `frontend-test`
  - `e2e` job `needs: [backend-test, frontend-test]`
  - `uv run mypy src/wheel_vocabulary` in `backend-typecheck` (NOT `src/wheel_vocab`)

---

### TD04 [TEST] Traceability matrix regression test

- **Slice**: D
- **Type tag**: [TEST]
- **Touches**: `apps/api/tests/unit/test_traceability.py`
- **Traces**: REQ-PFB-TRACE-01, REQ-PFB-TRACE-02, spec AC-PFB-09, design §14 Hook 3
- **Prereq tasks**: TD03
- **Estimated LOC**: 20
- **Description**: Write `apps/api/tests/unit/test_traceability.py` with `@pytest.mark.unit` tests that grep `docs/traceability-matrix.md` (path relative to repo root, discovered via `pathlib.Path(__file__).parents[4] / "docs/traceability-matrix.md"`): (1) `test_all_18_reqs_have_rows` — for each `n` in `001..018`, assert exactly one line starting with `| REQ-001-{n}` exists. (2) `test_req_007_not_mis_mapped` — asserts no line matching `REQ-001-007.*dominio no contiene imports` (case-insensitive) exists. (3) `test_req_015_has_ac_015` — asserts a line matching `REQ-001-015` and `AC-015` exists. Tests must be RED before TD05 (which fixes the actual matrix).
- **DoD**:
  - `uv run pytest tests/unit/test_traceability.py` fails (RED: matrix still has old mis-mapping or missing rows)

---

### TD05 [DOC] Fix `docs/traceability-matrix.md`

- **Slice**: D
- **Type tag**: [DOC]
- **Touches**: `docs/traceability-matrix.md`
- **Traces**: REQ-PFB-TRACE-01, REQ-PFB-TRACE-02, spec AC-PFB-09, design §14 Hook 3
- **Prereq tasks**: TD04
- **Estimated LOC**: 20 (edits; this is the ONLY doc edit outside `openspec/changes/` permitted in this cycle)
- **Description**: Correct `docs/traceability-matrix.md` per REQ-PFB-TRACE-01: (1) Fix the `REQ-001-007` row: Statement = configuration/env-vars requirement; Acceptance = `AC-007`; Tests = `UT-BE-001, UT-BE-002`; Tasks = appropriate scaffold + settings tasks from this cycle. (2) Add a new `REQ-001-015` row: Statement = "Backend directory structure `domain/ application/ infrastructure/ api/` without fictitious domain logic"; Acceptance = `AC-015`; Tests = structural inspection (Hook 1 grep); Tasks = `TA01, TA04`. (3) Verify all 18 `REQ-001-001..018` rows exist (adding any missing rows as needed with appropriate citations). Run `uv run pytest tests/unit/test_traceability.py` — all three tests must now pass (GREEN).
- **DoD**:
  - `uv run pytest tests/unit/test_traceability.py -v` exits 0 (GREEN)
  - `grep -c "REQ-001-007" docs/traceability-matrix.md` returns 1
  - `grep "REQ-001-015" docs/traceability-matrix.md` returns a result containing `AC-015`

---

### TD06 [DOC] Update root `README.md` "Status" section

- **Slice**: D
- **Type tag**: [DOC]
- **Touches**: `README.md`
- **Traces**: REQ-001-016, spec AC-PFB-09 (partial), proposal §2 (success criteria)
- **Prereq tasks**: TD05
- **Estimated LOC**: 10
- **Description**: Update only the "Status" table in `README.md` (do NOT rewrite the README, do NOT change the "Repository layout" tree). Change SPEC-001's status from `Not started` or equivalent to `IMPLEMENTED`. Update the "Next planned work" entry to reference SPEC-002 (`.txt` import + alphabetical frequency list) per proposal §10. Keep this section short — ≤ 10 lines added/modified.
- **DoD**:
  - `README.md` "Status" table shows SPEC-001 as IMPLEMENTED
  - SPEC-002 mentioned as next planned work
  - No other sections of `README.md` modified

---

### TD07 [DOC] Add `docs/decisions-log.md` cycle-close entry

- **Slice**: D
- **Type tag**: [DOC]
- **Touches**: `docs/decisions-log.md`
- **Traces**: AGENTS.md §11 (final report requirement), proposal §8 (success criteria)
- **Prereq tasks**: TD06
- **Estimated LOC**: 15
- **Description**: Add a chronological entry to `docs/decisions-log.md` for the `project-foundation-bootstrap` cycle close. Entry includes: date (2026-07-20), cycle slug, key decisions made (NDD-01 override to `wheel_vocabulary`, B1/B2 split triggered, WARN→FAIL coverage flip, Clock port approved), and reference to the archive report (to be created by `sdd-archive`). This is a brief chronological record, not a full summary.
- **DoD**:
  - New entry exists in `docs/decisions-log.md` with date, cycle slug, and ≥ 3 key decisions listed

---

### TD08 [SECURITY] Health route no-PII and no-env-leak assertion

- **Slice**: D
- **Type tag**: [SECURITY]
- **Touches**: `apps/api/tests/api/test_health_security.py`
- **Traces**: REQ-PFB-CONTRACT-01 (no PII, no secrets), Constitution Art. X.2
- **Prereq tasks**: TD07
- **Estimated LOC**: 10
- **Description**: Write `apps/api/tests/api/test_health_security.py` with `@pytest.mark.unit test_health_no_pii_or_env_leakage` — calls `GET /api/v1/health`, serializes response body to a string, and asserts the string does NOT contain any of: `SECRET`, `TOKEN`, `PASSWORD`, `KEY=`, `DATABASE_URL`, `hostname`, `stack`. Asserts response body keys are exactly `{"status", "service", "version", "timestamp"}` (defense-in-depth; matches TB110 test_9 but scoped to security concern). The test description must cite `CONTRACT-1 no-PII clause`.
- **DoD**:
  - `uv run pytest tests/api/test_health_security.py -v` exits 0
  - `make test-backend` still exits 0

---

### TD09 [REFACTOR] Final sweep (if needed)

- **Slice**: D
- **Type tag**: [REFACTOR]
- **Touches**: Any file across A–D slices with residual duplication
- **Traces**: AGENTS.md §3 (REFACTOR phase of TDD cycle)
- **Prereq tasks**: TD08
- **Estimated LOC**: 0–20
- **Description**: Final cross-slice cleanup. Check for: duplicate timestamp-formatting logic in tests vs. implementation; repeated health schema loading boilerplate in multiple tests (consider a conftest fixture); ESLint/mypy warnings that slipped through. Do NOT introduce new modules. If clean, no-op. Must not break any passing tests.
- **DoD**:
  - `make lint && make typecheck && make test && make test-e2e` all pass

---

### TD10 [BOOTSTRAP] Flip `strict_tdd` runtime to `true` in Engram

- **Slice**: D
- **Type tag**: [BOOTSTRAP]
- **Touches**: Engram observation `sdd/wheel-of-words/testing-capabilities` (#2414)
- **Traces**: REQ-PFB-DOCS-02, spec AC-PFB-07, proposal §2 (post-cycle capability flip)
- **Prereq tasks**: TD09 (all CI jobs green)
- **Estimated LOC**: 0 (Engram upsert, not a file change)
- **Description**: After all CI jobs are green on the tracker branch, upsert Engram observation `sdd/wheel-of-words/testing-capabilities` (topic key `sdd/wheel-of-words/testing-capabilities`) to: `strict_tdd: true` (runtime, now reflects installation), `test_runner_command: "uv run pytest"`, `test_runner_version: <resolved from uv.lock>`. Explicitly note in the content: "This is a RUNTIME state change — pytest is now installed and verified. The POLICY (`openspec/config.yaml strict_tdd: true`) was always true; this flip makes runtime match policy per REQ-PFB-DOCS-01/02." **This flip MUST happen after CI green, not before.**
- **DoD**:
  - Engram observation #2414 upserted with `strict_tdd: true`
  - Content explicitly distinguishes runtime vs. policy per REQ-PFB-DOCS-01
  - CI green confirmed before flip

---

## 9. Review Workload Forecast

```
## Review Workload Forecast

- Estimated changed lines (authored, excl. lockfiles/generated): ~1263
- Chained PRs recommended: Yes
- 400-line budget risk (any single PR): Low (all five PRs ≤ 400)
- Aggregate 400-line budget risk: High (exceeds by design; chain mitigates)
- Decision needed before apply: No
  - Maintainer has already committed to feature-branch-chain with B1/B2 split.
    Delivery strategy = ask-on-risk; guard is resolved because NO INDIVIDUAL PR
    exceeds 400 authored lines. size:exception is NOT needed.
- Per-slice forecast:
  - Slice A: ~370 LOC — risk: Low
  - Slice B1: ~265 LOC — risk: Low
  - Slice B2: ~150 LOC — risk: Low
  - Slice C: ~243 LOC — risk: Low
  - Slice D: ~235 LOC — risk: Low
```

**B1/B2 split:** CONFIRMED TRIGGERED. Slice B as a single PR = ~415 LOC. Split at boundary after health route (TB112) into B1 (~265 LOC) and B2 (~150 LOC). Both well under budget.

**Aggregate confirmation:** ~1263 LOC is +13% above the proposal's upper bound of 1120 LOC. Within the ±30% re-forecast trigger threshold. No re-forecast required.

```
Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: Low (per PR)
```

---

## 10. Open Items Deferred to Apply

The following are intentionally left to apply-time discretion:

1. **Exact docstring wording** in `__init__.py` layer files (style, not contract).
2. **Exact fixture names** in `conftest.py` (e.g., `tmp_db_url` vs `db_url` vs `sqlite_url` — only the behavior matters per the task description).
3. **Exact error message strings** in `fetchHealth()` — "HTTP 500" format is suggested by design §7.3 but apply may choose "HTTP error: 500" as long as the test is written to match.
4. **Exact CSS class names** in `status.css` — the three states must be visually distinct and text-first; exact naming is apply discretion.
5. **HTTP status code in health handler** — design §6.1 specifies 200; apply may emit `status_code=200` explicitly or omit it (FastAPI default). The test asserts 200 regardless.
6. **Alembic revision hash** — `0001_baseline.py` filename uses a deterministic prefix; the actual revision ID hash assigned by `alembic revision` may differ from `0001`. Apply uses whatever hash `alembic revision --autogenerate` or `alembic revision` assigns, then updates the test assertion to match.
7. **`FrozenClock` placement** — either inline in `test_clock.py` or shared in `tests/conftest.py`. Tasks phase recommends `conftest.py` for reuse in `test_health.py`; apply decides.
8. **`vitest.config.ts` coverage threshold activation** — Slice D's TD03 activates `coverageThreshold`; the exact `lines: 70` value is pinned by REQ-PFB-COV-01, but the structure of the vitest config activation is apply discretion (env-var gate or direct enable).

---

## 11. Risk Delta from Design

### Design-phase risks (restated)

| # | Risk | Severity | Task-phase status |
|---|------|----------|-------------------|
| R-1 | TDD bootstrap chicken-and-egg | HIGH | **Resolved.** TA01–TA14 are `[BOOTSTRAP]`; first `[TEST]` is TA15-SMOKE; all subsequent tasks follow RED→GREEN→REFACTOR. |
| R-2 | Slice B size overshoot | HIGH | **Resolved by B1/B2 split.** B total = ~415 LOC; B1 = ~265, B2 = ~150. Both PRs under budget. |
| R-3 | E2E flakiness | MEDIUM–HIGH | **Mitigated.** TD01 bans `sleep()`; TD02 uses `webServer` with health-based readiness. Chromium-only. Risk remains in CI due to cold-start timing. |
| R-4 | Non-goals creep during apply | HIGH | **Mitigated.** TA04 `domain/__init__.py` is empty; apply MUST NOT add domain classes. Hook 1 grep is a Slice B verify requirement. |
| R-5 | Traceability drift compounds | MEDIUM | **Resolved.** TD04/TD05 add regression test + fix in Slice D. TD04 test will be RED until TD05 fixes the matrix. |

### New task-phase risks

| # | New risk | Severity | Mitigation |
|---|----------|----------|------------|
| R-6 | `wheel_vocabulary` import path inconsistency across slices | MEDIUM | TA14 fixes design.md in Slice A before apply begins. TA10 Makefile references `wheel_vocabulary`. Any `wheel_vocab` slip in apply will cause an import error immediately. |
| R-7 | `playwright.config.ts` `webServer` `cd ../../` path fragility | LOW | Pinned by design §8.1; Makefile target `dev-backend` is the stable abstraction. Rename of Makefile target triggers a 1-line config change. |
| R-8 | Alembic `env.py` import path drift | LOW | TB205 specifies `from wheel_vocabulary.infrastructure.persistence.base import Base`. Any apply that uses `wheel_vocab` will fail with `ModuleNotFoundError` immediately — self-detecting error. |
| R-9 | Coverage WARN→FAIL flip in CI (TD03 sets `CI_COVERAGE_MODE: fail`) | LOW–MEDIUM | Slice D applies coverage gates for the first time. If actual coverage misses 80% (backend) or 70% (frontend) at Slice D merge, the CI gate blocks the PR. Mitigation: coverage is reported (WARN) in B1, B2, and C, giving apply visibility before the hard gate activates. |
| R-10 | `strict_tdd` runtime flip (TD10) must happen AFTER CI green, not during apply | LOW | TD10 is the last task in Slice D and is explicitly gated on "CI green confirmed before flip". Apply phase must not flip Engram before the CI run completes. |

---

## 12. Traceability Matrix — Tasks Phase

| Task ID | Type | Slice | Traces | DoD Summary |
|---------|------|-------|--------|-------------|
| TA01 | [BOOTSTRAP] | A | REQ-001-015, REQ-001-008, design §4.4 | All directories exist |
| TA02 | [BOOTSTRAP] | A | REQ-001-008, REQ-001-009, REQ-001-012, ADR-0001, design §5.2 | `pyproject.toml` valid; `wheel_vocabulary` throughout |
| TA03 | [BOOTSTRAP] | A | REQ-001-NF-001, ADR-0001 | `uv.lock` generated; `pytest --version` exits 0 |
| TA04 | [BOOTSTRAP] | A | REQ-001-015, ADR-0002, REQ-PFB-LANG-01 | Package importable; zero English-hardcoding in domain/application |
| TA05 | [BOOTSTRAP] | A | REQ-001-009, ADR-0003 | `conftest.py` exists; `--collect-only` exits 0 |
| TA06 | [BOOTSTRAP] | A | REQ-001-003, REQ-001-013, ADR-0001, design §7.1 | `package.json` + `tsconfig.json` with strict |
| TA07 | [BOOTSTRAP] | A | REQ-001-003, REQ-001-010, ADR-0001 | Vite + Vitest config; no coverage threshold yet |
| TA08 | [BOOTSTRAP] | A | REQ-001-013, NDD-10, ADR-0001 | `.eslintrc.cjs` present; `pnpm install` done |
| TA09 | [BOOTSTRAP] | A | REQ-001-003, design §4.4 | `typecheck` exits 0; `dev` boots |
| TA10 | [BOOTSTRAP] | A | REQ-001-008, ADR-0001, design §10 | All Makefile targets present; references `wheel_vocabulary` |
| TA11 | [BOOTSTRAP] | A | REQ-001-007, REQ-001-018, Constitution Art. VIII.5 | `.env.example` has all keys; no secrets |
| TA12 | [BOOTSTRAP] | A | REQ-001-018, spec AC-013 | Python + Node + env artifacts gitignored |
| TA13 | [DOC] | A | REQ-001-016, design §4.4 | README stubs exist |
| TA14 | [SPEC] | A | REQ-PFB-TASK-01 (maintainer override) | Zero `wheel_vocab` (non-historical) in design.md |
| TA15-SMOKE | [TEST] | A | REQ-PFB-BOOT-01, REQ-PFB-BOOT-02, AC-PFB-01, AC-PFB-02, ADR-0003 | First RED→GREEN; smoke test passes |
| TB101 | [TEST] | B1 | REQ-001-007, UT-BE-001, UT-BE-002, design §6.4 | Tests fail before TB102 (RED) |
| TB102 | [IMPL] | B1 | REQ-001-007, REQ-001-NF-006, NDD-07 | Settings tests GREEN; mypy passes |
| TB103 | [TEST] | B1 | REQ-PFB-CONTRACT-01, design §6.2, design §6.6, ADR-0002 | Clock tests RED before TB104 |
| TB104 | [IMPL] | B1 | design §6.2, design §6.6, ADR-0002, Constitution Art. VII.1 | Clock tests GREEN; strict mypy on application/ |
| TB105 | [TEST] | B1 | REQ-PFB-CONTRACT-01, design §6.4 | Version tests RED before TB106 |
| TB106 | [IMPL] | B1 | REQ-PFB-CONTRACT-01, design §6.4 | Version tests GREEN |
| TB107 | [SPEC] | B1 | REQ-PFB-CONTRACT-01, design §6.3, Hook 4 | `health.v1.json` valid JSON; `additionalProperties: false` |
| TB108 | [TEST] | B1 | REQ-001-002, REQ-PFB-CONTRACT-01, UT-BE-003 | DTO tests RED before TB109 |
| TB109 | [IMPL] | B1 | REQ-001-002, REQ-PFB-CONTRACT-01, design §6.3 | DTO tests GREEN |
| TB110 | [TEST] | B1 | REQ-001-001, REQ-001-002, REQ-PFB-CONTRACT-01, AC-PFB-10, API-BE-001, Hook 4 | Route tests RED (9 assertions) before TB111 |
| TB111 | [IMPL] | B1 | REQ-001-001, REQ-001-002, REQ-PFB-CONTRACT-01, ADR-0002, Constitution Art. VII.4 | All 9 route tests GREEN; mypy passes |
| TB112 | [REFACTOR] | B1 | Constitution Art. VII.6, ADR-0003 | No duplication; all tests still GREEN |
| TB201 | [TEST] | B2 | REQ-001-005, INT-BE-001, design §6.5 | Engine tests RED before TB202 |
| TB202 | [IMPL] | B2 | REQ-001-005, design §6.5, ADR-0001 | Engine tests GREEN |
| TB203 | [TEST] | B2 | REQ-PFB-CONTRACT-02, design §6.5, DEC-005 | Base test RED before TB204 |
| TB204 | [IMPL] | B2 | REQ-PFB-CONTRACT-02, design §6.5, DEC-005 | Base test GREEN; `metadata.tables` empty |
| TB205 | [MIGRATION] | B2 | REQ-001-006, REQ-PFB-CONTRACT-02, design §6.5, AC-PFB-11 | `alembic upgrade head` exits 0; no user tables |
| TB206 | [TEST] | B2 | REQ-001-006, INT-BE-002, INT-BE-003, AC-PFB-11 | Alembic tests GREEN (3 tests) |
| TB207 | [IMPL] | B2 | REQ-001-009, design §4.5 | Shared fixtures in conftest; all tests pass |
| TB208 | [REFACTOR] | B2 | Constitution Art. VII.6 | No duplication; mypy + ruff pass |
| TC01 | [TEST] | C | REQ-001-004, design §7.3, ADR-0005 | Client tests RED before TC02 |
| TC02 | [IMPL] | C | REQ-001-004, NDD-08, Constitution Art. VII.6 | Client tests GREEN; types defined |
| TC03 | [TEST] | C | REQ-001-004, UT-FE-001, A11Y-FE-001, design §7.2 | Loading tests RED before TC04 |
| TC04 | [IMPL] | C | REQ-001-NF-005, design §7.2, Constitution Art. IX.3 | Loading tests GREEN; `aria-live="polite"` |
| TC05 | [TEST] | C | REQ-001-004, AC-003, UT-FE-002, design §7.2 | Healthy tests RED before TC06 |
| TC06 | [IMPL] | C | REQ-001-004, AC-003, design §7.2 | Healthy tests GREEN; version + timestamp visible |
| TC07 | [TEST] | C | REQ-001-004, AC-004, UT-FE-003, UT-FE-004, A11Y-FE-001 | Error tests RED (4 tests) before TC08 |
| TC08 | [IMPL] | C | REQ-001-004, AC-004, REQ-001-NF-005, Constitution Art. IX.2 | Error tests GREEN; retry button accessible |
| TC09 | [TEST] | C | REQ-001-004, UT-FE-001–004, AC-PFB-12, design §7.4 | StatusPage tests RED (5 tests) before TC10 |
| TC10 | [IMPL] | C | REQ-001-004, design §7.2, NDD-08 | StatusPage tests GREEN (5 tests) |
| TC11 | [IMPL] | C | REQ-001-003, REQ-001-004, design §4.4 | `make dev` boots; browser shows status page |
| TC12 | [SPEC] | C | design §7.5, NDD-09, Constitution Art. VII.6 | `status.css` imported; three states styled |
| TC13 | [REFACTOR] | C | Constitution Art. VII.6 | No duplication; `make test-frontend` passes |
| TD01 | [E2E] | D | REQ-001-011, REQ-PFB-CONTRACT-04, E2E-001, AC-PFB-13 | Single spec file; no `sleep()` |
| TD02 | [E2E] | D | REQ-PFB-CONTRACT-04, design §8.1+§8.3, AC-PFB-13 | Two `webServer` entries; Chromium only |
| TD03 | [CI] | D | REQ-001-014, REQ-PFB-CONTRACT-05, AC-PFB-14+AC-PFB-15 | 10 jobs; `CI_COVERAGE_MODE: fail`; all on `ubuntu-latest` |
| TD04 | [TEST] | D | REQ-PFB-TRACE-01, REQ-PFB-TRACE-02, AC-PFB-09, Hook 3 | Traceability tests RED before TD05 |
| TD05 | [DOC] | D | REQ-PFB-TRACE-01, REQ-PFB-TRACE-02, AC-PFB-09 | Matrix corrected; traceability tests GREEN |
| TD06 | [DOC] | D | REQ-001-016, proposal §2 | README Status table updated |
| TD07 | [DOC] | D | AGENTS.md §11, proposal §8 | decisions-log entry added |
| TD08 | [SECURITY] | D | REQ-PFB-CONTRACT-01, Constitution Art. X.2 | No PII/secrets in health response confirmed by test |
| TD09 | [REFACTOR] | D | AGENTS.md §3 | All tests pass; no duplication |
| TD10 | [BOOTSTRAP] | D | REQ-PFB-DOCS-02, AC-PFB-07, proposal §2 | Engram #2414 upserted to `strict_tdd: true` (runtime) post-CI-green |

**Total tasks: 47** (A:15, B1:12, B2:8, C:13, D:10; including the TA15-SMOKE transition task)

---

## References

- `openspec/changes/project-foundation-bootstrap/design.md` (898 lines)
- `openspec/changes/project-foundation-bootstrap/spec.md` (515 lines)
- `openspec/changes/project-foundation-bootstrap/proposal.md` (288 lines)
- `specs/001-project-foundation/{spec,acceptance,plan,test-plan,tasks,decisions,traceability}.md`
- `docs/constitution.md` (v2.0.0)
- `docs/adr/` (ADR-0001 through ADR-0010)
- `docs/definition-of-done.md`
- `AGENTS.md` §§ 2, 3, 5, 6, 8, 10, 11
- `docs/traceability-matrix.md` (drift documented; corrected by TD05)
- `openspec/archive/2026-07-16-docs-methodology-overhaul/tasks.md` (tone/scale calibration)
- **Engram anchors**: #2413 (init), #2414 (testing capabilities), #2415 (explore), #2419 (proposal), #2421 (spec), #2423 (design)

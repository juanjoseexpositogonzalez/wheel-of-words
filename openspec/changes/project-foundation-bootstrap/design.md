# Design — project-foundation-bootstrap

---

## 1. Metadata

| Field | Value |
|-------|-------|
| Change slug | `project-foundation-bootstrap` |
| Cycle type | First code-touching cycle; operationalizes SPEC-001 |
| Constitution version | v2.0.0 |
| Target spec suite | `specs/001-project-foundation/` (SPEC-001 v1.0.0) |
| Chain strategy | `feature-branch-chain` on tracker branch `project-foundation-bootstrap` |
| Review budget | 400 authored lines per PR (lockfiles and generated Alembic scripts excluded) |
| Design version | 1.0.0 |
| Language | English (methodology artifact per ADR-0010) |

**Upstream inputs:**

| Artifact | Location | Lines |
|----------|----------|-------|
| Delta spec v1.0.0 | `openspec/changes/project-foundation-bootstrap/spec.md` | 515 |
| Proposal | `openspec/changes/project-foundation-bootstrap/proposal.md` | 288 |
| Exploration | `openspec/changes/project-foundation-bootstrap/explore.md` | 352 |

**Downstream consumers:** `openspec/changes/project-foundation-bootstrap/tasks.md` (not yet written).

---

## 2. Purpose of this design

The spec pins WHAT ships; this design pins HOW it is organized. Every layout, module name, and integration point required for the tasks phase to write atomic RED→GREEN→REFACTOR steps is decided here. The design resolves three maintainer-cached decisions (mypy strictness, backend layout, health endpoint `timestamp` semantics), every architectural question listed in spec §10.1 (design-phase owns), and every structural decision left implicit by the proposal. The tasks phase takes this design as a blueprint and produces the ordered task list with per-task LOC estimates and TDD triads — it does not renegotiate architectural choices made here.

---

## 3. Decisions cache (from orchestrator)

The following three decisions were made by the maintainer before this design phase and are treated as resolved inputs, not open items:

1. **Health endpoint `timestamp` field — KEEP.** The response body is `{status, service, version, timestamp}` with `timestamp` as an ISO-8601 UTC string with millisecond precision. The design preserves this contract in full and pins all `timestamp` semantics. This decision is final; no further discussion of dropping `timestamp` is permitted in this cycle.

2. **mypy strictness policy — DEFERRED TO DESIGN (resolved below in §5).** The maintainer explicitly asked the design phase to choose between layered strictness (strict in `domain`/`application`, gradual in `infrastructure`/`api`) or a flat policy. This design resolves the choice; see §5 mypy config.

3. **Backend layout (proposal `ASSUMPTION-2`) — DEFERRED TO DESIGN (resolved below in §4).** The maintainer explicitly asked the design phase to decide between `apps/backend/ + apps/frontend/`, `backend/ + frontend/` at repo root, or the `apps/api/ + apps/web/` shape that plan.md §2 already sketches. This design resolves the choice; see §4 repository layout decision.

---

## 4. Repository layout decision

### 4.1 Options considered

| Option | Description | Tradeoffs |
|--------|-------------|-----------|
| A — `apps/api/ + apps/web/` (flat apps) | Backend at `apps/api/`, frontend at `apps/web/`, shared workspace root | Matches SPEC-001 plan.md §2 exactly; ADR-0001 names `apps/api` layout implicitly through SPEC-001 plan; simplest to reason about with two ecosystems |
| B — `backend/ + frontend/` at root | Roots directly in repo root | Simpler paths, but naming doesn't signal monorepo intent; harder to add a third app (docs site, CLI) without ambiguity |
| C — `services/api/ + apps/web/` | Semantic split between services and apps | Not grounded in any existing artifact; introduces a new vocabulary not in SPEC-001 or any ADR |
| D — `packages/` monorepo tool (Turborepo/Nx) | Shared JS tooling layer | JavaScript-tooling-heavy approach unsuitable for a Python-primary project; ADR-0001 does not name Turborepo |

### 4.2 Decision

**Option A — `apps/api/ + apps/web/`** is adopted.

**Justification:**
- **ADR-0001**: Names `uv` (backend) and `pnpm` (frontend) as separate toolchains within a monorepo, implying sibling app directories rather than a single root package.
- **ADR-0002**: The hexagonal split (`domain/application/infrastructure/api`) lives inside the Python package, not at repo root. A dedicated `apps/api/` subtree cleanly contains that Python package.
- **SPEC-001 plan.md §2**: Provides a concrete structure sketch with `apps/api/` and `apps/web/` already named. This is the authoritative structural signal from SPEC-001; deviation requires a documented reason.
- **Constitution Art. VII**: Architecture separates Python and JS concerns; co-locating them under a flat `backend/` root doesn't harm this, but `apps/api/` makes the boundary explicit.
- **ADR-0004**: Each cycle produces traceable artifacts; the `apps/` namespace makes CI job scoping (`--working-directory apps/api`) explicit and auditable.

### 4.3 Package name decision

> **Override**: maintainer has decided the Python package name is `wheel_vocabulary`. This decision supersedes NDD-01. See tasks.md §1.

The Python package is named `wheel_vocab` (not `wheel_vocabulary`, not `wheel_of_words`). *(NDD-01 historical record — preserved verbatim; see Override note above.)*

**Rationale:**
- `docs/product-vision.md` §1 uses "Wheel Vocabulary" as the provisional product name; the repo directory is `wheel-of-words`. A project rename is explicitly out of scope for this cycle (spec §10.3). The design must pick one name for the Python package.
- `wheel_vocabulary` is the Constitution's canonical project name (product-facing). Used as the Python package name it is the most faithful to the product identity.
- However, `wheel_vocabulary` as a Python identifier is 16 characters and makes every import verbose. SPEC-001 plan.md §2 uses `wheel_vocab` as the package name in its structure sketch (`src/wheel_vocabulary/`).
- **Design choice**: follow plan.md §2 verbatim — `wheel_vocab`. This is a `NEW-DESIGN-DECISION` (see NDD-01 in §12). It does not conflict with any ADR or Constitution clause because the Constitution does not prescribe Python identifiers.

### 4.4 Full Slice A directory tree

The tree below shows every file Slice A scaffolds. File content is the tasks phase's concern; the tree is the design.

```
wheel-of-words/                          ← repo root (already exists)
├── .github/
│   └── workflows/
│       └── ci.yml                       ← create (Slice D)
├── .gitignore                           ← already exists; Slice A extends
├── apps/
│   ├── api/                             ← Python backend root
│   │   ├── alembic.ini                  ← Alembic config
│   │   ├── migrations/
│   │   │   ├── env.py
│   │   │   ├── script.py.mako
│   │   │   └── versions/
│   │   │       └── 0001_baseline.py     ← empty-schema baseline (Slice B)
│   │   ├── pyproject.toml               ← backend package manifest
│   │   ├── src/
│   │   │   └── wheel_vocabulary/
│   │   │       ├── __init__.py
│   │   │       ├── domain/
│   │   │       │   └── __init__.py
│   │   │       ├── application/
│   │   │       │   ├── __init__.py
│   │   │       │   └── clock.py         ← Clock protocol (Slice B)
│   │   │       ├── infrastructure/
│   │   │       │   ├── __init__.py
│   │   │       │   ├── clock.py         ← SystemClock impl (Slice B)
│   │   │       │   └── persistence/
│   │   │       │       ├── __init__.py
│   │   │       │       └── base.py      ← DeclarativeBase (Slice B)
│   │   │       └── api/
│   │   │           ├── __init__.py
│   │   │           ├── main.py          ← FastAPI factory (Slice B)
│   │   │           ├── routes/
│   │   │           │   ├── __init__.py
│   │   │           │   └── health.py    ← /health route (Slice B)
│   │   │           └── schemas/
│   │   │               └── health.v1.json  ← JSON Schema (Slice B)
│   │   └── tests/
│   │       ├── conftest.py
│   │       ├── smoke/
│   │       │   └── test_smoke.py        ← first RED test (Slice B bootstrap)
│   │       ├── unit/
│   │       │   └── test_settings.py     ← UT-BE-001, UT-BE-002 (Slice B)
│   │       ├── api/
│   │       │   └── test_health.py       ← API-BE-001 (Slice B)
│   │       └── integration/
│   │           └── test_alembic.py      ← INT-BE-002, INT-BE-003 (Slice B)
│   └── web/                             ← TypeScript/React frontend root
│       ├── package.json
│       ├── pnpm-lock.yaml               ← (generated; excluded from line count)
│       ├── tsconfig.json
│       ├── tsconfig.node.json
│       ├── vite.config.ts
│       ├── vitest.config.ts
│       ├── .eslintrc.cjs                ← ESLint config
│       ├── playwright.config.ts         ← (Slice D)
│       ├── index.html
│       ├── src/
│       │   ├── main.tsx
│       │   ├── App.tsx
│       │   ├── api/
│       │   │   └── client.ts            ← thin fetch wrapper (Slice C)
│       │   ├── components/
│       │   │   ├── StatusPage.tsx       ← page component (Slice C)
│       │   │   ├── StatusLoading.tsx
│       │   │   ├── StatusHealthy.tsx
│       │   │   └── StatusError.tsx
│       │   └── types/
│       │       └── health.ts            ← HealthResponse interface (Slice C)
│       ├── tests/
│       │   └── components/
│       │       └── StatusPage.test.tsx  ← UT-FE-001..004 + A11Y-FE-001 (Slice C)
│       └── e2e/
│           └── status.spec.ts           ← E2E-001 (Slice D)
├── .env.example                         ← create (Slice A)
├── Makefile                             ← create (Slice A)
└── README.md                            ← already exists; Slice D rewrites
```

**Traceability:** REQ-001-015 (four-layer structure) → `src/wheel_vocabulary/{domain,application,infrastructure,api}/`. REQ-001-007 (`.env.example`) → `.env.example`. REQ-001-008 (Makefile) → `Makefile`. REQ-001-018 (gitignore) → `.gitignore` extension.

### 4.5 Test layout decision

Tests live **adjacent to the source package** under `apps/api/tests/` (not as package siblings under `src/`). This is the structure SPEC-001 plan.md §2 sketches. Test discovery uses the `testpaths = ["tests"]` setting in `pyproject.toml` relative to `apps/api/`.

Sub-directories within `tests/`:
- `smoke/` — infrastructure smoke tests (runner installed, import works).
- `unit/` — unit tests (no database, no network). Maps to UT-BE-* in test-plan.
- `api/` — API tests using FastAPI `TestClient`. Maps to API-BE-*.
- `integration/` — SQLite + Alembic integration tests. Maps to INT-BE-*.

**Justification:** Co-location with the package (not inside `src/`) is the `uv` / `pytest` community norm; it avoids `src/` layout complications for test imports. This is `NEW-DESIGN-DECISION` NDD-02.

---

## 5. Python packaging and tooling

### 5.1 Package manager and Python version

- **Package manager:** `uv >= 0.4` per ADR-0001. No `poetry`, no `pip` invocations in CI or Makefile. Root `uv.lock` is not used; the lockfile lives at `apps/api/uv.lock` alongside `apps/api/pyproject.toml` (single-package, not uv workspace, see §5.2).
- **Python version:** `>= 3.12` per SPEC-001 §6 assumptions ("Python 3.12 o superior") and ADR-0001 §Backend.

### 5.2 pyproject.toml shape

Single-package (not a uv workspace). The backend is one Python package; no shared `packages/` are needed this cycle. The frontend is a separate pnpm workspace under `apps/web/`.

```toml
[project]
name = "wheel-vocab"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.111",
    "uvicorn[standard]>=0.29",
    "pydantic-settings>=2.2",
    "sqlalchemy>=2.0",
    "alembic>=1.13",
    "jsonschema>=4.22",
]

[project.optional-dependencies]
dev  = ["wheel-vocab[test,lint,type]"]
test = ["pytest>=8", "pytest-cov>=5", "httpx>=0.27", "hypothesis>=6"]
lint = ["ruff>=0.4"]
type = ["mypy>=1.10"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/wheel_vocabulary"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts   = "--strict-markers -ra"
markers   = [
    "unit: pure unit test (no database, no network)",
    "integration: test with SQLite or Alembic",
    "e2e: Playwright end-to-end test",
    "smoke: infrastructure smoke test",
]

[tool.coverage.run]
source   = ["wheel_vocabulary"]
branch   = true

[tool.coverage.report]
show_missing = true
skip_empty   = true

[tool.ruff]
target-version = "py312"
line-length    = 100
select = ["E", "F", "I", "N", "UP", "B", "S", "A", "C4", "PT", "SIM", "RET", "TCH", "TID"]

[tool.ruff.lint.isort]
known-first-party = ["wheel_vocabulary"]

[tool.mypy]
python_version     = "3.12"
strict             = false          # ← base is gradual; overrides below make domain/application strict
warn_unused_configs = true

[[tool.mypy.overrides]]
module  = "wheel_vocabulary.domain.*"
strict  = true

[[tool.mypy.overrides]]
module  = "wheel_vocabulary.application.*"
strict  = true

# infrastructure.* and api.* remain at base (gradual) — no override
```

**Traceability:** REQ-001-012 (Ruff + mypy) → `[tool.ruff]`, `[tool.mypy]`. REQ-001-NF-001 (lockfiles) → `uv.lock`. REQ-001-009 (pytest) → `[tool.pytest.ini_options]`. REQ-PFB-COV-01 (coverage thresholds) → `[tool.coverage.*]`.

### 5.3 Ruff configuration rationale

- **Rule set `E, F, I, N, UP, B, S, A, C4, PT, SIM, RET, TCH, TID`**: covers style (`E/F`), imports (`I`), naming (`N`), upgrade suggestions (`UP`), bugbear (`B`), security basics (`S`), shadowing (`A`), comprehensions (`C4`), pytest (`PT`), simplifications (`SIM`), return-value patterns (`RET`), type-checking imports (`TCH`), and tidy imports (`TID`). Omits `D` (docstrings) — documenting every empty-layer `__init__` is noise; add in a future cycle.
- **Line length 100**: 88 (Black default) is too tight for function signatures with type annotations; 120 is too permissive for code review at 400-line PR budgets. 100 is the balance. `NEW-DESIGN-DECISION` NDD-03.

### 5.4 mypy strictness resolution (deferred decision from orchestrator)

**Choice: Layered strictness — strict in `domain.*` and `application.*`, gradual in `infrastructure.*` and `api.*`.**

**Rationale:** This is the design phase's resolution of the maintainer-deferred `NEW-CONTRACT-DECISION` from spec §5.5 CONTRACT-5 and the explicit orchestrator directive.

- `domain` and `application` are the innermost layers with zero framework dependencies (ADR-0002, Constitution Art. VII.1–2). They will grow to contain all linguistic invariants. Catching every untyped or implicit `Any` here prevents type-drift from propagating outward. Strict mypy at these layers costs nothing this cycle (empty layers have no code to annotate) and pays dividends in every subsequent cycle.
- `infrastructure` and `api` interact with SQLAlchemy 2 ORM descriptors, FastAPI route decorators, Alembic migration scripts, and Pydantic models — all of which are known to produce `[misc]` and `[assignment]` mypy errors even with correct usage until the ecosystem matures. Enforcing strict on these layers from day one would cause the CI pipeline to red on legitimate, correct code.
- A single `# type: ignore[<specific-code>]` comment IS permitted in `infrastructure.*` and `api.*` ONLY, and MUST be accompanied by an inline comment citing the grounding reason (e.g., `# sqlalchemy descriptor typing; see REQ-001-012`). Bare `# type: ignore` without a code is forbidden. This rule is `NEW-DESIGN-DECISION` NDD-04.
- **Flat-strict alternative rejected**: Would require dozens of `# type: ignore[misc]` annotations in SQLAlchemy and FastAPI interaction code from Slice B day one, creating noisy diffs and obscuring real type errors in future cycles.
- **Flat-gradual alternative rejected**: Defeats the purpose; `domain` and `application` layers must be strictly typed from the start per Constitution Art. VII.1 (domain purity) and ADR-0002.

**Implementation:** See pyproject.toml `[[tool.mypy.overrides]]` blocks above. No separate `mypy.ini` file is created; inline configuration is the preferred pattern when a `pyproject.toml` is present.

**Traceability:** REQ-001-012 (mypy strict) → `[[tool.mypy.overrides]]` for `domain.*` and `application.*`. REQ-PFB-CONTRACT-05 (layered) → gradual base + strict overrides. Constitution Art. VII.1–2 → strict domain/application.

### 5.5 pytest and coverage configuration

**Coverage severity per slice (resolving ASSUMPTION-8 via spec §4 REF-2):**

- **Slices B and C (WARN):** `pytest --cov=apps/api/src/wheel_vocabulary --cov-report=term-missing --cov-report=xml` runs but does NOT use `--cov-fail-under`. The CI job that runs this sets `continue-on-error: true`. The coverage number is reported and visible; the pipeline does not fail if below threshold.
- **Slice D (FAIL gate activated):** The CI job removes `continue-on-error: true` AND adds `--cov-fail-under=80` for backend global and a separate `--cov-fail-under=90` for `domain/` + `application/` paths. For the frontend, Vitest's `coverageThreshold` is activated in `vitest.config.ts` with `lines: 70`.
- **Mechanism:** A single environment variable `CI_COVERAGE_MODE` toggled in the CI workflow controls this. `CI_COVERAGE_MODE=warn` → `continue-on-error: true`, no `--cov-fail-under`. `CI_COVERAGE_MODE=fail` → no `continue-on-error`, with `--cov-fail-under`. Slice D sets `CI_COVERAGE_MODE: fail` in the workflow YAML; Slices B/C set `CI_COVERAGE_MODE: warn`. This is `NEW-DESIGN-DECISION` NDD-05.

**Traceability:** REQ-PFB-COV-01 (thresholds) → `--cov-fail-under=80` (global), `--cov-fail-under=90` (domain/application). REQ-PFB-COV-02 (WARN→FAIL) → `CI_COVERAGE_MODE` variable. ADR-0003 (coverage targets ≥ 90%/≥ 80%) → these exact thresholds. Constitution Art. II.6 (coverage is a signal) → soft-gate in Slices B/C.

---

## 6. Backend architecture

### 6.1 Health handler call graph

```
GET /api/v1/health
    │
    ▼
apps/api/src/wheel_vocabulary/api/routes/health.py
    router = APIRouter(prefix="/api/v1")
    @router.get("/health", response_model=HealthOut)
    async def health(settings: Annotated[Settings, Depends(get_settings)],
                     clock:    Annotated[Clock,    Depends(get_clock)]) -> HealthOut:
        return HealthOut(
            status="ok",
            service=settings.app_name,
            version=settings.app_version,
            timestamp=clock.now_utc(),
        )
    │
    ├─▶ wheel_vocabulary.application.clock.Clock        (port: protocol)
    │       def now_utc(self) -> datetime: ...
    │
    ├─▶ wheel_vocabulary.infrastructure.clock.SystemClock  (adapter: implements Clock)
    │       def now_utc(self) -> datetime:
    │           return datetime.now(tz=timezone.utc)
    │
    └─▶ wheel_vocabulary.api.main.get_settings()        (dependency: reads cached Settings)
            lru_cache → Settings (pydantic-settings, reads from env)
```

**Deliberate thinness of the health route:** The health handler does NOT delegate to an application-layer use case. A `HealthCheckService` use case would be speculative abstraction per Constitution Art. VII.6 — the `/health` route has no domain logic and no infrastructure dependency (other than `clock` and `settings`). The route IS the use case. This keeps Slice B small. Future cycles that add readiness probes (DB connectivity, model loaded) SHOULD introduce a `HealthProbe` port at that point. `NEW-DESIGN-DECISION` NDD-06.

**ADR-0002 compliance:** `api` depends on `application` (Clock protocol lives in `application/`), not on `infrastructure` directly. The `SystemClock` is injected via `infrastructure`'s dependency provider, not imported directly in the router. This preserves the inward dependency direction.

**Traceability:** REQ-001-001 (FastAPI startable) → `main.py` factory. REQ-001-002 (health endpoint) → `routes/health.py`. Constitution Art. VII.4 (no business rules in API) → thin handler. ADR-0002 (hexagonal) → Clock port in `application/`, adapter in `infrastructure/`.

### 6.2 Timestamp semantics

- **Source:** `datetime.now(tz=timezone.utc)` — wall-clock UTC, no local time, no external service.
- **Format:** ISO-8601 with millisecond precision: `"2026-07-20T14:32:00.123Z"`. Python format string: `dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"`.
- **Utility location:** `wheel_vocabulary/application/clock.py` defines the `Clock` protocol (a `typing.Protocol` with `now_utc() -> datetime`). `wheel_vocabulary/infrastructure/clock.py` provides `SystemClock`, the production implementation.
- **Test injection:** Tests inject a `FakeClock(fixed_dt)` that returns a deterministic `datetime`, enabling assertion of exact timestamp values without wall-clock coupling.
- **Traceability:** REQ-PFB-CONTRACT-01 (timestamp field) → `clock.now_utc()`. Constitution Art. VI.1 (record versions/timestamps per execution) → timestamp in health response. Maintainer decision: KEEP timestamp.

### 6.3 JSON schema for `/health`

- **Location:** `apps/api/src/wheel_vocabulary/api/schemas/health.v1.json`
- **Versioning scheme:** filename-based (`health.v1.json`) + response header `X-Schema-Version: 1`. No URL-path versioning for schemas at this scale. Header is added via FastAPI `Response` parameter in the route.
- **Draft:** JSON Schema Draft 2020-12 (`"$schema": "https://json-schema.org/draft/2020-12/schema"`).
- **Validation at test time:** `jsonschema` package (already in `dependencies` section above). The API test (`test_health.py`) loads the schema via `importlib.resources.files("wheel_vocabulary.api.schemas").joinpath("health.v1.json")` and validates the actual response JSON against it. This satisfies spec §9 Hook 4 and AC-PFB-10.
- **Schema shape:**
  ```json
  {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "urn:wheel-vocab:health:v1",
    "type": "object",
    "required": ["status", "service", "version", "timestamp"],
    "additionalProperties": false,
    "properties": {
      "status":    { "type": "string", "const": "ok" },
      "service":   { "type": "string", "const": "wheel-vocabulary-api" },
      "version":   { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+" },
      "timestamp": { "type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}\\.\\d{3}Z$" }
    }
  }
  ```
- **Traceability:** REQ-PFB-CONTRACT-01 (schema must exist and be versioned) → `health.v1.json`. Spec §9 Hook 4 → `jsonschema` validation in test. Constitution Art. VIII.1 (strict typing) → `additionalProperties: false`.

### 6.4 Settings and configuration

- **Library:** `pydantic-settings >= 2.2`. ADR-0001 does not mention it by name; it names Pydantic generally. `pydantic-settings` is the canonical extension for environment-variable loading and is the de-facto standard for FastAPI applications. `NEW-DESIGN-DECISION` NDD-07.
- **Fields:**

  ```python
  class Settings(BaseSettings):
      app_name:     str  = "wheel-vocabulary-api"
      app_version:  str  = "0.1.0"          # read from importlib.metadata at startup
      environment:  str  = "development"
      database_url: str  = "sqlite:///./data/wheel_vocabulary.db"
      cors_origins: list[str] = []
      log_level:    str  = "INFO"

      model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
  ```

- **`app_version` source:** `importlib.metadata.version("wheel-vocab")` called once at import time, not in the route handler. The field default `"0.1.0"` is a fallback for test environments where the package is not installed.
- **Env file:** `.env` for local dev (gitignored). `.env.example` committed with all keys and safe example values, no secrets. Per REQ-001-007, AC-007, REQ-001-018.
- **Traceability:** REQ-001-007 (env vars, `.env.example`) → `Settings.model_config`. REQ-001-NF-006 (centralized config) → single `Settings` class. Constitution Art. VIII.5 (no secrets in repo) → `.env.example` has placeholder values only.

### 6.5 SQLAlchemy and Alembic wiring

- **SQLAlchemy version:** `>= 2.0` per SPEC-001 plan.md §3 and ADR-0001 §Backend.
- **Engine URL convention:** `sqlite:///./data/wheel_vocabulary.db` for development; `sqlite:///:memory:` for integration tests. The `data/` directory is gitignored per REQ-001-018.
- **`DeclarativeBase` location:** `apps/api/src/wheel_vocabulary/infrastructure/persistence/base.py`
  ```python
  from sqlalchemy.orm import DeclarativeBase

  class Base(DeclarativeBase):
      pass
  ```
- **Alembic env.py:** imports `Base` from `wheel_vocabulary.infrastructure.persistence.base` and sets `target_metadata = Base.metadata`.
- **Alembic directory structure:**
  ```
  apps/api/
  ├── alembic.ini
  └── migrations/
      ├── env.py
      ├── script.py.mako
      └── versions/
          └── 0001_baseline.py
  ```
- **Baseline revision (CONTRACT-2):** `upgrade()` is an explicit no-op body (a comment `# empty-schema baseline`) preceded by `op.execute("")` (or simply `pass`). `alembic upgrade head` creates only the `alembic_version` table. `downgrade()` is `pass`. No user tables created.
- **Traceability:** REQ-001-005 (SQLite configurable) → `Settings.database_url`. REQ-001-006 (Alembic) → `migrations/versions/0001_baseline.py`. REQ-PFB-CONTRACT-02 (empty-schema) → `upgrade()` is no-op. AC-PFB-11 (upgrade head succeeds) → INT-BE-002 test.

### 6.6 Port definitions

Two concrete port definitions relevant to this cycle (though `domain/` is empty, establishing ports in `application/` now prevents anti-pattern drift later):

**`wheel_vocabulary/application/clock.py`:**
```python
from typing import Protocol
from datetime import datetime

class Clock(Protocol):
    def now_utc(self) -> datetime: ...
```

**Note on `HealthProbe` port:** Deferred. A `HealthProbe` protocol (checking DB connectivity, NLP model availability) is NOT introduced this cycle — no domain or infrastructure state to probe. Constitution Art. VII.6 (no speculative abstraction). This will be introduced when SPEC-002 adds real persistence queries.

**Traceability:** ADR-0002 (ports in application) → `Clock` protocol in `application/clock.py`. Constitution Art. VII.1 (domain has zero framework imports) → `Clock` is a pure `typing.Protocol`. Constitution Art. VII.6 (no speculative abstraction) → `HealthProbe` deferred.

---

## 7. Frontend architecture

### 7.1 Bootstrap stack — pinned versions

| Tool | Version | Justification |
|------|---------|---------------|
| pnpm | `>= 9.x` | ADR-0001 names pnpm; v9 is stable LTS as of mid-2026 |
| Vite | `>= 5.x` | ADR-0001; Vite 5 is the stable release; avoids Vite 6 churn |
| React | `19.x` | SPEC-001 plan.md §4 mentions React conventions; React 19 is the current stable as of 2026-07 |
| TypeScript | `>= 5.4` | REQ-001-013; TS 5.4 is stable, supports all pattern features needed |
| Vitest | `>= 1.6` | ADR-0001; compatible with Vite 5 |
| Testing Library | `>= 16.x` | ADR-0001; React 19 compatible |
| Playwright | `>= 1.44` | ADR-0001; CONTRACT-4 (Chromium-only) |

**Traceability:** REQ-001-013 (TypeScript strict) → `tsconfig.json` `strict: true`. ADR-0001 (pnpm, React, Vite, Vitest, Testing Library, Playwright). REQ-001-NF-004 (Chromium) → CONTRACT-4 compliance.

**Decision NOT to use TanStack Query:** Plan.md §4 mentions TanStack Query, and proposal §2 repeats it. However, plan.md §4 says "TanStack Query *puede* gestionar consulta y reintento" (emphasis on "can"; not "must"). CONTRACT-3 (spec §5.3) requires a retry control but does not mandate TanStack Query. Introducing TanStack Query adds a dependency for a 3-state machine that native `fetch` + `useState` + `useEffect` handles cleanly. Constitution Art. VII.6 (no speculative abstraction) applies. `NEW-DESIGN-DECISION` NDD-08 — NOT using TanStack Query in this cycle.

### 7.2 Component tree for the status screen

```
src/
└── components/
    ├── StatusPage.tsx      ← owns fetch, state, re-fetch on retry
    ├── StatusLoading.tsx   ← pure presentational; renders "Comprobando estado"
    ├── StatusHealthy.tsx   ← pure presentational; renders version + timestamp
    └── StatusError.tsx     ← pure presentational; renders message + retry button
```

**Component contracts:**

```typescript
// StatusPage.tsx
// No props. Owns all state: "loading" | "healthy" | "error"
// Uses useState + useEffect + native fetch

// StatusLoading.tsx
// No props; renders: <p aria-live="polite">Comprobando estado</p>

// StatusHealthy.tsx
interface StatusHealthyProps {
  service: string;
  version: string;
  timestamp: string;
}

// StatusError.tsx
interface StatusErrorProps {
  message: string;
  onRetry: () => void;
}
// renders: <p>Backend no disponible</p>
//          <button aria-label="Reintentar" onClick={onRetry}>Reintentar</button>
```

**HealthResponse type (in `src/types/health.ts`):**
```typescript
export interface HealthResponse {
  status: "ok";
  service: string;
  version: string;
  timestamp: string;
}
```

**Spanish UI copy rationale:** UI strings ("Comprobando estado", "Backend disponible", "Backend no disponible", "Reintentar") are in Spanish per ADR-0010 §2 (product-facing artifacts in Spanish) and SPEC-001 AC-003, AC-004. Code identifiers remain English (language-domain contract per ADR-0010 §5 and SKILL.md).

**File naming:** PascalCase files matching component names. Props interfaces co-located in the same file (no separate `types.ts` per component at this scale).

**Traceability:** REQ-001-004 (three-state screen, retry) → `StatusPage.tsx` + `StatusError.tsx`. REQ-PFB-CONTRACT-03 (state contract) → component props. REQ-001-NF-005 (accessible) → `aria-live="polite"` on loading, `aria-label` on retry button. Constitution Art. IX.2–3 → accessible labels and text.

### 7.3 API client

`src/api/client.ts` — thin wrapper:
```typescript
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function fetchHealth(): Promise<HealthResponse> {
  const resp = await fetch(`${API_BASE}/api/v1/health`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json() as Promise<HealthResponse>;
}
```

No Axios, no React Query. Constitution Art. VII.6 (no speculative abstraction). The error path throws; `StatusPage` catches and transitions to error state. `NEW-DESIGN-DECISION` NDD-08 (no TanStack Query).

### 7.4 State management

`useState` + `useEffect` at `StatusPage` level. No global state, no context, no reducer. Three local states: `"loading"`, `"healthy"` (with `HealthResponse` payload), `"error"` (with error message string). The retry handler calls `setStatus("loading")` and re-triggers `useEffect` via a `retryCount` counter. Constitution Art. VII.6 (no speculative abstraction).

### 7.5 CSS strategy

**Plain CSS (`src/index.css`).**

Tailwind rejected: adds a PostCSS pipeline, `tailwind.config.js`, JIT compilation, and 3–4 extra `devDependencies` for a 3-state screen with one button. The review budget is 400 lines; Tailwind setup alone consumes ~20 lines of config with zero behavioral value. CSS Modules rejected: adds import syntax complexity (`styles.wrapper`) for no scoping benefit when there are four leaf components. Plain CSS is zero-dependency and ships in Vite by default. `NEW-DESIGN-DECISION` NDD-09.

### 7.6 Frontend environment

- `VITE_API_BASE_URL` in `.env` (local dev, defaults to `http://localhost:8000`).
- `.env.example` includes `VITE_API_BASE_URL=http://localhost:8000` as a documented example.
- In CI E2E context, `playwright.config.ts` `webServer` config controls both servers; `VITE_API_BASE_URL` is set via the Playwright config environment to point at the CI-local backend port.

**TypeScript ESLint ruleset (resolving ASSUMPTION-5):**
`@typescript-eslint/recommended-type-checked` + `eslint-plugin-react-hooks` recommended rules. `tsconfig.json` sets `strict: true`. This matches proposal ASSUMPTION-5's stated default. `NEW-DESIGN-DECISION` NDD-10.

**Traceability:** REQ-001-013 (TypeScript strict, linter) → `tsconfig.json` + ESLint config. REQ-001-007 (`.env.example`) → `VITE_API_BASE_URL` entry. ADR-0005 (local-first) → `http://localhost:8000` default.

---

## 8. E2E topology

### 8.1 Playwright `webServer` configuration

`playwright.config.ts` declares two `webServer` entries:

```typescript
webServer: [
  {
    command: "cd ../../ && make dev-backend",
    url: "http://localhost:8000/api/v1/health",
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
  {
    command: "pnpm run dev",
    url: "http://localhost:5173",
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
],
```

Playwright polls the `url` until it responds before running tests. No `setTimeout`, no `sleep()`. Readiness is health-based. REQ-PFB-CONTRACT-04 satisfied.

### 8.2 Test file location

`apps/web/e2e/status.spec.ts` — inside the frontend package, separate from Vitest unit/component tests in `tests/`. Playwright and Vitest never share test directories (different configs, different runners).

### 8.3 Browser matrix

`playwright.config.ts` lists exactly one project:
```typescript
projects: [
  { name: "chromium", use: { ...devices["Desktop Chrome"] } },
],
```
Firefox and WebKit are NOT listed. REQ-PFB-CONTRACT-04, CONTRACT-4 compliance, ASSUMPTION-7 resolved.

### 8.4 Artifacts on failure only

```typescript
use: {
  screenshot: "only-on-failure",
  video:      "retain-on-failure",
  trace:      "on-first-retry",
},
```

SPEC-001 test-plan §7 requirement met.

**Traceability:** REQ-001-011 (Playwright E2E) → `status.spec.ts`. REQ-PFB-CONTRACT-04 (single spec, `webServer`, Chromium only) → this section. AC-PFB-13 → `webServer` + single browser project.

---

## 9. CI job DAG

### 9.1 Workflow file

`.github/workflows/ci.yml` — single workflow, triggered on `push` (all branches) and `pull_request`.

### 9.2 Job DAG

```
setup-python  ──────────────────────────────────────────────────┐
  ├── backend-lint       (ruff check + ruff format --check)      │
  ├── backend-typecheck  (mypy)                                   │
  ├── backend-test       (pytest + coverage; CI_COVERAGE_MODE)   │
  └── migration-check    (alembic upgrade head against :memory:) │
                                                                  ├──▶ e2e
setup-node    ──────────────────────────────────────────────────┘
  ├── frontend-lint      (eslint)
  ├── frontend-typecheck (tsc --noEmit)
  └── frontend-test      (vitest + coverage; CI_COVERAGE_MODE)
```

`e2e` needs `backend-test` AND `frontend-test` (ensures both test suites pass before running the integrated E2E). It does NOT need `migration-check` to succeed (Playwright tests against a running backend that handles its own DB; the CI DB is in-memory per the test settings).

### 9.3 Job definitions summary

| Job | Needs | Commands | ubuntu-latest |
|-----|-------|----------|---------------|
| `setup-python` | — | Install uv, `uv sync --extra dev`; cache on `apps/api/uv.lock` | ✓ |
| `setup-node` | — | Install pnpm, `pnpm install`; cache on `apps/web/pnpm-lock.yaml` | ✓ |
| `backend-lint` | `setup-python` | `uv run ruff check .` + `uv run ruff format --check .` | ✓ |
| `backend-typecheck` | `setup-python` | `uv run mypy src/wheel_vocabulary` | ✓ |
| `backend-test` | `setup-python` | `uv run pytest --cov ... CI_COVERAGE_MODE` | ✓ |
| `migration-check` | `setup-python` | `uv run alembic upgrade head` (temp SQLite) | ✓ |
| `frontend-lint` | `setup-node` | `pnpm run lint` | ✓ |
| `frontend-typecheck` | `setup-node` | `pnpm run typecheck` | ✓ |
| `frontend-test` | `setup-node` | `pnpm run test -- --coverage CI_COVERAGE_MODE` | ✓ |
| `e2e` | `backend-test`, `frontend-test` | `pnpm exec playwright install chromium && pnpm exec playwright test` | ✓ |

All jobs run on `ubuntu-latest` per ASSUMPTION-6 and REQ-PFB-CONTRACT-05.

### 9.4 Coverage severity in CI

- `CI_COVERAGE_MODE` is set at workflow input level or via a `vars` context:
  - Slices B and C CI YAML: `CI_COVERAGE_MODE: warn` → `continue-on-error: true` on test jobs, no `--cov-fail-under`.
  - Slice D CI YAML: `CI_COVERAGE_MODE: fail` → removes `continue-on-error`, adds `--cov-fail-under=80`.
- **Single failure fails the pipeline** per REQ-PFB-CONTRACT-05: every job uses `if: success()` implicitly; no jobs use `continue-on-error` except the coverage step during warn mode.

**Traceability:** REQ-001-014 (CI) → `ci.yml`. REQ-PFB-CONTRACT-05 (job matrix) → all eight jobs above. ADR-0001 (GitHub Actions, uv, pnpm cache) → cache keys. REQ-PFB-COV-02 (WARN→FAIL) → `CI_COVERAGE_MODE`. REQ-001-NF-003 (no public network in tests) → jobs run against local servers.

---

## 10. Makefile targets

All targets are `.PHONY`. The Makefile lives at repo root and delegates to `uv run` (backend) and `pnpm` (frontend). **Resolves ASSUMPTION-3** — Makefile is the canonical surface; `uv` scripts in `pyproject.toml` are NOT the primary interface.

| Target | Commands wrapped | Intent |
|--------|-----------------|--------|
| `bootstrap` | `uv sync --extra dev` (in `apps/api/`) + `pnpm install` (in `apps/web/`) | First-run setup; installs all deps |
| `install` | alias for `bootstrap` | REQ-001-008 `make install` |
| `dev-backend` | `cd apps/api && uv run uvicorn wheel_vocabulary.api.main:create_app --factory --reload` | Start backend dev server |
| `dev-frontend` | `cd apps/web && pnpm run dev` | Start frontend Vite dev server |
| `dev` | `make dev-backend & make dev-frontend` | Both servers (background) |
| `test-backend` | `cd apps/api && uv run pytest` | Backend test suite |
| `test-frontend` | `cd apps/web && pnpm run test` | Frontend Vitest suite |
| `test-e2e` | `cd apps/web && pnpm exec playwright test` | Playwright E2E |
| `test` | `make test-backend && make test-frontend && make test-e2e` | All tests |
| `lint-backend` | `cd apps/api && uv run ruff check .` | Backend Ruff |
| `lint-frontend` | `cd apps/web && pnpm run lint` | Frontend ESLint |
| `lint` | `make lint-backend && make lint-frontend` | All lint |
| `typecheck-backend` | `cd apps/api && uv run mypy src/wheel_vocabulary` | mypy |
| `typecheck-frontend` | `cd apps/web && pnpm run typecheck` | tsc --noEmit |
| `typecheck` | `make typecheck-backend && make typecheck-frontend` | All types |
| `format` | `cd apps/api && uv run ruff format .` | Ruff autoformat |
| `migrate` | `cd apps/api && uv run alembic upgrade head` | Apply migrations |
| `clean` | Remove `apps/api/.venv`, `apps/web/node_modules`, coverage artifacts, `__pycache__` | Reset to clean state |

**Traceability:** REQ-001-008 (`install/dev/test/lint/typecheck/format/e2e/migrate`) → all targets above. ADR-0001 (Makefile in Automatización) → Makefile as primary surface.

---

## 11. Traceability from design to spec/proposal/SPEC-001

| Design section | Decides | Traces to |
|----------------|---------|-----------|
| §4.2 Layout | `apps/api/ + apps/web/` monorepo shape | SPEC-001 plan.md §2; ADR-0001 (Makefile, monorepo); ADR-0002 (hexagonal) |
| §4.3 Package name | `wheel_vocabulary` Python package name | SPEC-001 plan.md §2 (`src/wheel_vocabulary/`); NDD-01 |
| §4.4 Directory tree | Full Slice A file tree | REQ-001-015; REQ-001-007; REQ-001-008; REQ-001-018 |
| §4.5 Test layout | `apps/api/tests/{smoke,unit,api,integration}/` | REQ-001-009; ADR-0003 (pytest); NDD-02 |
| §5.1 Package manager | `uv >= 0.4`, Python `>= 3.12` | ADR-0001; SPEC-001 §6 |
| §5.2 pyproject.toml | Single-package shape, dependency groups | REQ-001-012; REQ-001-NF-001; ADR-0001 |
| §5.3 Ruff config | Rule set, line length 100 | REQ-001-012; NDD-03 |
| §5.4 mypy strictness | Layered: strict domain/application, gradual infra/api | REQ-001-012; REQ-PFB-CONTRACT-05; Constitution Art. VII.1–2; ADR-0002; NDD-04 |
| §5.5 Coverage | Thresholds, WARN/FAIL toggle via `CI_COVERAGE_MODE` | REQ-PFB-COV-01; REQ-PFB-COV-02; ADR-0003; Constitution Art. II |
| §6.1 Health handler | Call graph, thin handler, no use case object | REQ-001-001; REQ-001-002; Constitution Art. VII.4; ADR-0002; NDD-06 |
| §6.2 Timestamp | `Clock` protocol, `SystemClock`, ISO-8601 UTC ms format | REQ-PFB-CONTRACT-01; Constitution Art. VI.1; Maintainer decision |
| §6.3 JSON schema | `health.v1.json` path, Draft 2020-12, `jsonschema` validation | REQ-PFB-CONTRACT-01; spec §9 Hook 4; Constitution Art. VIII.1 |
| §6.4 Settings | `pydantic-settings`, fields, `.env.example` | REQ-001-007; REQ-001-NF-006; Constitution Art. VIII.5; NDD-07 |
| §6.5 SQLAlchemy/Alembic | `DeclarativeBase` location, `alembic.ini`, empty baseline | REQ-001-005; REQ-001-006; REQ-PFB-CONTRACT-02; DEC-002; ADR-0001 |
| §6.6 Ports | `Clock` protocol; `HealthProbe` deferred | ADR-0002; Constitution Art. VII.1; Art. VII.6; NDD-06 |
| §7.1 Frontend stack | Versions, no TanStack Query | ADR-0001; REQ-001-013; Constitution Art. VII.6; NDD-08 |
| §7.2 Component tree | `StatusPage` + three presentational children | REQ-001-004; REQ-PFB-CONTRACT-03; REQ-001-NF-005; Constitution Art. IX.2–3 |
| §7.3 API client | `fetchHealth()` with native fetch | REQ-001-004; ADR-0005; Constitution Art. VII.6; NDD-08 |
| §7.5 CSS | Plain CSS | Constitution Art. VII.6; NDD-09 |
| §7.6 ESLint ruleset | `@typescript-eslint/recommended-type-checked` | REQ-001-013; NDD-10 |
| §8.1 E2E `webServer` | Two entries, health-based readiness | REQ-PFB-CONTRACT-04; plan.md §10 |
| §8.2 E2E file | `apps/web/e2e/status.spec.ts` | REQ-001-011; REQ-PFB-CONTRACT-04 |
| §8.3 Browser matrix | Chromium only | REQ-001-NF-004; ASSUMPTION-7; CONTRACT-4 |
| §9.2 CI DAG | 10-job DAG with `e2e` needing both test jobs | REQ-001-014; REQ-PFB-CONTRACT-05; ADR-0001 |
| §9.4 Coverage severity | `CI_COVERAGE_MODE` env var | REQ-PFB-COV-02; NDD-05 |
| §10 Makefile | All targets + `.PHONY` discipline | REQ-001-008; ADR-0001; ASSUMPTION-3 |

Every non-trivial decision has at least one trace. No design decision floats free.

---

## 12. NEW-DESIGN-DECISION register

| ID | Decision | Rationale | Maintainer-visible |
|----|----------|-----------|-------------------|
| NDD-01 | Python package named `wheel_vocab` | Follows SPEC-001 plan.md §2 exactly; avoids `wheel_vocabulary` verbosity; no ADR or Constitution clause prescribes identifiers. | Yes — if `wheel_vocabulary` is preferred, update plan.md §2 and all CI working-directory references. |
| NDD-02 | Tests in `apps/api/tests/` (not `src/`-adjacent) | Standard `uv` + `pytest` layout; avoids import complications; matches plan.md §2 sketch. No binding artifact conflicts. | Yes — low-risk, cosmetic. |
| NDD-03 | Ruff line length 100 | 88 is too tight for annotated signatures; 120 too permissive. ADR-0001 does not prescribe a line length. | Yes — pure preference; easy to change. |
| NDD-04 | `# type: ignore[code]` without adjacent comment is forbidden; citation required | Prevents silent suppression of mypy errors; enforces the spirit of REQ-001-012. Not in any ADR; Constitution Art. VIII.1 (strict typing) supports it by implication. | Yes — add to AGENTS.md §8 or design if desired. |
| NDD-05 | `CI_COVERAGE_MODE` env var toggles WARN vs FAIL coverage enforcement | Implements REQ-PFB-COV-02 mechanically. No existing artifact specifies the mechanism. Constitution Art. II.6 (coverage is a signal) supports soft-gating during construction. | Yes — alternative is two separate workflow files. |
| NDD-06 | Health handler is thin (no `HealthCheckService` use case); `HealthProbe` port deferred | Constitution Art. VII.6 (no speculative abstraction). The `/health` route has no domain logic. `HealthProbe` is introduced when real probes exist. | Yes — if maintainer wants a use-case object now, add `HealthCheckService` in `application/`. |
| NDD-07 | `pydantic-settings >= 2.2` for environment loading | ADR-0001 names Pydantic but not `pydantic-settings` by name; it is the canonical FastAPI community pattern. Alternatives (`os.environ` dict, `python-dotenv` alone) are less type-safe. | Yes — if ADR-0001 should be updated to name `pydantic-settings` explicitly, raise during tasks review. |
| NDD-08 | No TanStack Query in this cycle; native `fetch` + `useState` | plan.md §4 says TanStack Query "can" manage queries; Constitution Art. VII.6 forbids speculative abstraction. Three-state screen does not need a caching layer. | Yes — if maintainer prefers TanStack Query, it can be added in Slice C; adds ~1 devDependency and wrapper abstraction. |
| NDD-09 | Plain CSS (no CSS Modules, no Tailwind) | Constitution Art. VII.6. Tailwind adds PostCSS pipeline and build complexity for a 3-state screen. CSS Modules adds import syntax overhead. | Yes — Tailwind can be added in a future cycle when the UI grows. |
| NDD-10 | ESLint: `@typescript-eslint/recommended-type-checked` + `eslint-plugin-react-hooks` | Matches proposal ASSUMPTION-5's stated default. Provides strong TypeScript-aware lint without custom ruleset authoring. | Yes — lighter presets (e.g. `@typescript-eslint/recommended` without `-type-checked`) available if type-checking in ESLint proves slow. |

---

## 13. Rollback boundaries (per slice)

Under `feature-branch-chain`:

```
main (unchanged until cycle close)
  └── project-foundation-bootstrap  (tracker)
        └── slice-a
              └── slice-b  (or b1 → b2)
                    └── slice-c
                          └── slice-d
```

| Slice | Rollback mechanism | Cascade? | Tracker stays intact? |
|-------|------------------|----------|----------------------|
| A | `git revert <slice-a-merge-commit>` on tracker branch. Removes scaffold; nothing depends on it yet. | None — no downstream slice has merged. | Yes |
| B | `git revert <slice-b-merge-commit>` on slice-a branch. Backend disappears; scaffold (slice-a) remains. If sub-split: revert B2 first, then B1. | Does NOT force revert of A. | Yes |
| C | `git revert <slice-c-merge-commit>` on slice-b branch. `apps/web/` is removed; backend continues. E2E cannot pass without frontend. | Does NOT force revert of A or B. | Yes |
| D | `git revert <slice-d-merge-commit>` on slice-c branch. Removes CI YAML, E2E spec, README, traceability fix. Backend + frontend still work locally. | Does NOT force revert of A, B, or C. | Yes |

**Git command pattern for re-parenting after a revert (at high level):**
```bash
# If slice-b needs revert while slice-c exists:
git checkout slice-c
git rebase --onto slice-a slice-b
# Resolve any conflicts that result from slice-b being gone
```
This re-parents slice-c onto slice-a. The tracker branch is untouched until archive.

**`strict_tdd` runtime note on rollback:** If Slice B is reverted, pytest is still installed (pyproject.toml from Slice A includes it as a dev dependency), so the runtime `strict_tdd` cache in Engram #2414 does NOT automatically flip back. A manual Engram upsert is required on full cycle rollback (as stated in proposal §10).

---

## 14. Verify-hook implementations

Per spec §9. Exact regex and paths pinned.

### Hook 1 — Forbidden domain classes

```bash
grep -RE "class\s+(Lexeme|Occurrence|Corpus|Mwe|MultiwordExpression|Lemma|SurfaceForm|WordForm|PartOfSpeech|ManualCorrection|TextExtractor)\b" \
  apps/api/src/wheel_vocabulary/
```
Expected: grep exits with code 1 (no matches). Any hit fails the slice verification. **Verifies:** DEC-005, Constitution Art. VII.6, SPEC-001 §4 non-goals.

### Hook 2 — Hardcoded English in domain/application

```bash
grep -REn "(?i)\b(english|en_us|en_gb|assume_english)\b" \
  apps/api/src/wheel_vocabulary/domain/ \
  apps/api/src/wheel_vocabulary/application/
grep -REn "['\"]en['\"]" \
  apps/api/src/wheel_vocabulary/domain/ \
  apps/api/src/wheel_vocabulary/application/
```
Expected: zero hits outside the single permitted `LanguageRegistry` stub location (if any). The permitted location is `wheel_vocabulary/application/language_registry.py` if the design phase decided to include the stub — per spec REQ-PFB-LANG-02. **This design phase does NOT include the stub** (no domain code needs it in this cycle; REQ-PFB-LANG-02's "MAY defer" clause applies). Therefore zero hits anywhere is the expected outcome. **Verifies:** REQ-PFB-LANG-01, AC-PFB-06.

### Hook 3 — Traceability matrix correctness

```bash
# 18 rows check
for n in 001 002 003 004 005 006 007 008 009 010 011 012 013 014 015 016 017 018; do
  count=$(grep -cP "^\| REQ-001-${n}\b" docs/traceability-matrix.md || echo 0)
  [ "$count" = "1" ] || echo "MISS: REQ-001-${n} count=${count}"
done

# REQ-001-007 must NOT reference hexagonal wording
if grep -qiE "REQ-001-007.*dominio no contiene imports" docs/traceability-matrix.md; then
  echo "FAIL: REQ-001-007 still mis-mapped"
fi

# REQ-001-015 row with AC-015
grep -P "^\| REQ-001-015 \|" docs/traceability-matrix.md | grep -q "AC-015" \
  || echo "FAIL: REQ-001-015 row missing or lacks AC-015"
```
**Verifies:** REQ-PFB-TRACE-01, REQ-PFB-TRACE-02, AC-PFB-09. Run in Slice D verify.

### Hook 4 — Health JSON Schema validation

In `apps/api/tests/api/test_health.py`, the CONTRACT-001 test:
```python
import json
import importlib.resources
import jsonschema

def test_health_schema(client):
    schema_text = importlib.resources.files("wheel_vocabulary.api.schemas") \
        .joinpath("health.v1.json").read_text()
    schema = json.loads(schema_text)
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    jsonschema.validate(resp.json(), schema)
```
**Verifies:** AC-PFB-10, spec §9 Hook 4, CONTRACT-1.

### Hook 5 — Coverage thresholds

```bash
# Backend (global ≥ 80%)
cd apps/api && uv run pytest \
  --cov=src/wheel_vocabulary \
  --cov-report=term-missing \
  --cov-report=xml \
  ${CI_COVERAGE_MODE:+--cov-fail-under=80}

# Backend domain+application ≥ 90% (separate run or via per-module config)
cd apps/api && uv run pytest tests/unit tests/api \
  --cov=src/wheel_vocabulary/domain \
  --cov=src/wheel_vocabulary/application \
  ${CI_COVERAGE_MODE:+--cov-fail-under=90}

# Frontend (≥ 70%, controlled in vitest.config.ts)
# In Slice D: vitest.config.ts enables `coverageThreshold: { lines: 70 }`
```
WARN in B/C: `CI_COVERAGE_MODE` is unset or `warn`; the `${CI_COVERAGE_MODE:+--cov-fail-under=N}` expansion produces no flag. FAIL in D: `CI_COVERAGE_MODE=fail`; expansion adds `--cov-fail-under=N`. **Verifies:** REQ-PFB-COV-01, REQ-PFB-COV-02, AC-PFB-03, AC-PFB-04.

---

## 15. Open items deferred to tasks

The tasks phase owns:

- **Slice B sub-split (ASSUMPTION-1):** Tasks phase performs the per-task LOC forecast and decides B1/B2. Design does not pre-decide.
- **T024 re-tagging (REQ-PFB-TASK-01):** Tasks phase decides the exact tag (`[BOOTSTRAP]`, `[IMPL]` with note, or `[DOC]`).
- **Per-task LOC estimates:** Tasks phase produces these after mapping design sections to implementation tasks.
- **RED→GREEN→REFACTOR triads per task:** Each task's TDD sequence is a tasks-phase artifact.
- **Traceability matrix correction task placement (ASSUMPTION-10):** Tasks phase decides exact task ID in Slice D.
- **Slice B sub-split naming (B1/B2):** Tasks phase names and orders them.
- **Full 62-task delta inventory:** Tasks phase produces the delta over SPEC-001 tasks.md.

Design pins architecture; tasks phase pins sequence.

---

## 16. Risk update

| # | Risk from spec return envelope | Severity | Design-phase mitigation |
|---|-------------------------------|----------|------------------------|
| R-1 | TDD bootstrap chicken-and-egg | HIGH | Bootstrap sequencing rule confirmed: Slice A tasks tagged `[BOOTSTRAP]`; first RED test is `test_smoke.py::test_pytest_runs` (REQ-PFB-BOOT-01/02). Design shows the exact file path: `apps/api/tests/smoke/test_smoke.py`. |
| R-2 | Slice B size overshoot (250–450 LOC) | HIGH | Design pins exact file list and call graph for Slice B, enabling precise LOC forecasting in tasks phase. Sub-split contingency (B1: Settings + health route; B2: SQLAlchemy + Alembic) is still in place. |
| R-3 | E2E flakiness | MEDIUM–HIGH | `webServer` config with health-based readiness (not `sleep`) specified in §8.1. Chromium-only (§8.3) reduces browser-specific flakiness. |
| R-4 | Non-goals creep during apply | HIGH | Hook 1 (grep for forbidden classes) is pinned with exact regex in §14. Domain skeleton is explicit (`__init__.py` only in `domain/`). |
| R-5 | Traceability drift compounding | MEDIUM | Hook 3 pins the exact grep patterns for Slice D verify. ASSUMPTION-10 (default: fix in Slice D) is still the design's position. |

**New risk introduced by design decisions:**

| # | New risk | Severity | Mitigation |
|---|----------|----------|------------|
| R-6 | mypy strict domain/application can slow iteration if type stubs are missing for future domain dependencies | LOW (this cycle has no domain deps) | In future cycles, `# type: ignore[import-untyped]` is permitted only in `domain` with a `# see REQ-<id>` citation per NDD-04. The permission is narrow and logged. |
| R-7 | Playwright `webServer` `cd ../../` path from `apps/web/` may break if Makefile target changes | LOW | `playwright.config.ts` references the Makefile target by name; any Makefile rename triggers a single-line update in config. The design pins the Makefile target `dev-backend` explicitly (§10). |

---

## Threat matrix

N/A — this design introduces no routing-shell-subprocess boundary, no VCS/PR automation executable-file classification, and no process-integration boundary in the threat matrix sense. The design wires FastAPI to a local SQLite file and a local Vite dev server; there are no shell command injection vectors, no external egress (ADR-0005), and no executable-file classification decisions. Threat matrix not applicable to this cycle.

---

## References

- `openspec/changes/project-foundation-bootstrap/spec.md` (515 lines)
- `openspec/changes/project-foundation-bootstrap/proposal.md` (288 lines)
- `openspec/changes/project-foundation-bootstrap/explore.md` (352 lines)
- `specs/001-project-foundation/{spec, plan, test-plan, decisions}.md`
- `docs/constitution.md` v2.0.0
- `docs/adr/0001-monorepo-and-stack.md`
- `docs/adr/0002-hexagonal-split.md`
- `docs/adr/0003-tdd-mandatory.md`
- `docs/adr/0005-local-first.md`
- `docs/adr/0008-multi-language-scope.md`
- `docs/adr/0010-documentation-language-policy.md`
- `docs/architecture/architecture-baseline.md`
- `openspec/archive/2026-07-16-docs-methodology-overhaul/design.md` (structural calibration only)
- **Engram anchors:** #2413 (init), #2414 (testing capabilities), #2415 (explore), #2419 (proposal), #2421 (spec)

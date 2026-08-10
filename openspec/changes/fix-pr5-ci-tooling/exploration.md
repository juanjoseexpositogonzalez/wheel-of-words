## Exploration: PR #5 CI tooling repair

### Current State
PR #5's workflow is structurally split into setup jobs and consumer jobs, but GitHub Actions jobs do not share filesystems or virtual environments. `setup-python` runs `uv sync --extra dev`, while `backend-lint`, `backend-typecheck`, `backend-test`, and `migration-check` only install `uv` and invoke `uv run`. Because the dev extra is not installed in those jobs, `uv` resolves the runtime environment (the observed 31 packages) without `ruff`, `mypy`, or `pytest`; each command then fails because its executable is absent.

The frontend setup has a separate deterministic defect: `actions/setup-node` is configured with `cache-dependency-path: apps/web/pnpm-lock.yaml`, but the repository contains the lockfile at the workspace root (`pnpm-lock.yaml`). The setup-node job therefore fails before dependency installation, and all jobs that require it are skipped. This is a separate path/configuration failure, not the backend missing-dev-tools failure.

The E2E job repeats the invalid frontend cache path and does not explicitly prepare the backend environment. Its Playwright configuration starts the backend through `make dev-backend`, which depends on `uv run`; after the frontend setup defect is fixed, E2E should still establish the backend environment explicitly so the job is self-contained and reproducible.

### Affected Areas
- `.github/workflows/ci.yml` — CI setup, job isolation, dependency installation, lockfile cache path, and E2E preparation.
- `apps/api/pyproject.toml` — defines `dev` as the source of `pytest`, `ruff`, and `mypy`; confirms the tools are optional rather than runtime dependencies.
- `apps/api/uv.lock` — backend dependency lockfile used by `uv`.
- `pnpm-lock.yaml` — actual workspace lockfile; the workflow currently references a nonexistent path.
- `apps/web/playwright.config.ts` — starts the backend with `make dev-backend`, making E2E dependent on backend tooling being available.
- `apps/api/tests/unit/test_ci_workflow.py` — existing structural CI contract tests; the natural place for regression coverage.

### Approaches
1. **Self-contained jobs with corrected lockfile paths** — make every job that invokes tooling install its own dependencies; use the repository-root pnpm lockfile in setup-node and all frontend/E2E jobs.
   - Pros: matches GitHub Actions isolation semantics; minimal change; failures identify the exact missing setup; no hidden artifact transfer.
   - Cons: repeats setup steps and may spend more installation time without cache improvements.
   - Effort: Low

2. **Reusable setup actions or dependency artifacts** — centralize setup in composite actions, or upload/download prepared environments between jobs.
   - Pros: reduces YAML repetition or can optimize installation time.
   - Cons: artifacts/virtual environments are platform-sensitive; composite-action design adds indirection; unnecessary scope for a small repair.
   - Effort: Medium

### Recommendation
Use self-contained jobs. Correct `cache-dependency-path` to `pnpm-lock.yaml`, retain frozen installs, and add the appropriate `uv sync --extra dev` step to every backend job that runs development tools (and explicitly prepare the backend in E2E). Keep the change limited to workflow setup plus focused structural regression tests in `test_ci_workflow.py`; do not alter application dependencies or source behavior. This directly addresses both observed failure classes while keeping the review well below the 400-line budget.

Candidate requirements and acceptance criteria for proposal/spec:

- **REQ-CI-001**: Every backend CI job invoking `ruff`, `mypy`, `pytest`, or migration tooling MUST install the locked project environment with the required extras within that job before invocation.
  - **AC-001**: On a clean GitHub runner, backend lint, typecheck, test, and migration jobs locate their commands and complete successfully.
- **REQ-CI-002**: Frontend CI jobs MUST reference the committed lockfile path and install dependencies with frozen-lockfile semantics.
  - **AC-002**: setup-node and all dependent frontend jobs complete installation without a missing lockfile error.
- **REQ-CI-003**: CI jobs MUST be independently reproducible and MUST NOT rely on a setup job's filesystem state.
  - **AC-003**: Each consumer job contains the setup required for its tools; no job depends solely on `needs` for dependency availability.
- **REQ-CI-004**: The E2E job MUST prepare both frontend and backend runtime dependencies before Playwright starts its configured web servers.
  - **AC-004**: Playwright can start both configured servers and execute the Chromium E2E suite on a clean runner.

### Test and Validation Strategy
- Extend `apps/api/tests/unit/test_ci_workflow.py` with structural assertions for the root pnpm lockfile path, per-job backend sync, and E2E backend preparation; first run the focused test before implementation to establish a meaningful RED result.
- After implementation, run the focused workflow-contract tests, the backend test suite, lint, typecheck, migration check, and frontend lint/typecheck/tests locally using the repository's documented commands.
- Validate the workflow as YAML and, where available, with an action/workflow linter; inspect the resulting GitHub Actions run and confirm backend jobs execute tools rather than report spawn errors, frontend setup succeeds, and E2E reaches Playwright rather than being skipped.
- Treat the remote PR run as the authoritative integration check because local execution cannot reproduce GitHub job isolation and runner action behavior exactly.

### Risks
- Adding `uv sync --extra dev` to several jobs increases install time, although lockfile-based caching can mitigate it.
- A workflow-only fix may expose pre-existing lint, type, coverage, migration, or E2E failures that were previously masked by setup failures.
- The exact `uv` action/cache behavior should be confirmed from the failed run after the first repair; `needs` ordering must not be mistaken for state sharing.
- The current E2E workflow starts a backend process but does not declare a separate backend service; startup timing or environment-variable issues may surface once dependency setup is fixed.

### Ready for Proposal
Yes. The exploration identifies two independent root causes and a bounded CI-only repair. The proposal should explicitly keep application behavior and dependency declarations out of scope, choose self-contained jobs, and preserve the prior agreement to run adversarial/judge review after CI repair.

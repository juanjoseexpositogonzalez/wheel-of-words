# Delta for 001-project-foundation

## ADDED Requirements

### Requirement: REQ-CI-001 — Independent Backend Tool Setup

Every CI backend job that invokes development tooling MUST perform a locked
`uv sync --extra dev` in its own runner before invoking that tooling. The job
MUST remain independently reproducible; `needs` MAY enforce ordering but MUST
NOT provide an implicit environment.

Acceptance: AC-CI-001.

#### Scenario: Backend quality jobs run on clean runners

- GIVEN a clean runner with the repository checked out
- WHEN lint, typecheck, test, or migration validation runs
- THEN the job installs the locked backend development environment first
- AND the requested command executes without relying on another job's environment

### Requirement: REQ-CI-002 — Root Frontend Lockfile Installation

Frontend CI jobs MUST resolve dependency caching and frozen installation from
the committed repository-root `pnpm-lock.yaml`. They MUST NOT reference a
nonexistent application-local lockfile path.

Acceptance: AC-CI-002.

#### Scenario: Frontend setup uses the committed lockfile

- GIVEN a clean runner and the repository-root lockfile
- WHEN frontend dependencies are cached or installed
- THEN the cache key and frozen install use `pnpm-lock.yaml` at the repository root
- AND setup completes without a missing-lockfile error

### Requirement: REQ-CI-003 — Locked E2E Dependency Preparation

The E2E job MUST prepare locked frontend and backend dependencies before
starting Playwright-managed servers. A setup failure MUST be reported as a
failed job rather than silently skipping Chromium E2E execution.

Acceptance: AC-CI-003.

#### Scenario: Chromium E2E starts after dependency setup

- GIVEN a clean runner with both committed lockfiles available
- WHEN the E2E job starts its servers and invokes Playwright
- THEN frontend and backend locked environments are ready beforehand
- AND the Chromium health smoke spec is attempted

### Requirement: REQ-CI-004 — Functional E2E Failure Boundary

This change MUST be limited to CI dependency setup, cache paths, and structural
workflow guarantees. It MUST NOT alter product behavior, application dependency
declarations, or functional E2E expectations to mask failures revealed after
setup succeeds.

Acceptance: AC-CI-004.

#### Scenario: Setup repair exposes an unrelated functional failure

- GIVEN dependency preparation succeeds
- WHEN a Playwright assertion fails for an application behavior unrelated to setup
- THEN CI reports the functional E2E failure as a real failure
- AND the failure remains outside this change's implementation scope

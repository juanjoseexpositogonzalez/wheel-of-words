# Delta for 001-project-foundation

This native OpenSpec delta reconciles the archived legacy full spec at
`openspec/archive/2026-08-03-project-foundation-bootstrap/spec.md` into the
dispatcher-expected path. The archived legacy file remains the detailed audit
source; this file preserves its normative requirements and acceptance identifiers
in native shape.

## ADDED Requirements

### Requirement: REQ-PFB-BOOT-001 — Bootstrap-to-TDD Boundary

Slice A prerequisite work MUST be tagged `[BOOTSTRAP]` or explicitly documented as
non-behavior infrastructure, and every behavior after the first smoke test MUST
follow RED → GREEN → REFACTOR.

Acceptance: AC-PFB-01, AC-PFB-02.

#### Scenario: Bootstrap tasks are distinguishable

- GIVEN the Slice A task list
- WHEN a reviewer inspects tasks before the first `[TEST]`
- THEN each prerequisite task is marked `[BOOTSTRAP]` or has a bootstrap note

#### Scenario: First executable test anchors TDD

- GIVEN pytest is installed
- WHEN the smoke test is added after initially failing due to absence
- THEN the test passes and subsequent behavior tasks require RED-first tests

### Requirement: REQ-PFB-CONTRACT-001 — Health Endpoint Contract

`GET /api/v1/health` MUST return HTTP 200 with exactly `status`, `service`,
`version`, and `timestamp`, MUST validate against a shipped JSON Schema, and MUST
NOT expose secrets, paths, environment names, or extra fields.

Acceptance: AC-PFB-10.

#### Scenario: Health response is schema-valid

- GIVEN the backend is running
- WHEN a client requests `/api/v1/health`
- THEN the body validates against the shipped schema
- AND the response contains only the four approved fields

#### Scenario: Timestamp is observable and safe

- GIVEN a deterministic clock is injected in tests
- WHEN the health endpoint responds
- THEN `timestamp` is ISO-8601 UTC with millisecond precision

### Requirement: REQ-PFB-CONTRACT-002 — Empty Alembic Baseline

The cycle MUST ship exactly one Alembic baseline revision whose upgrade/downgrade
creates no user tables and records only Alembic bookkeeping.

Acceptance: AC-PFB-11.

#### Scenario: Empty database upgrades cleanly

- GIVEN a fresh SQLite database
- WHEN `alembic upgrade head` runs
- THEN the command succeeds and only `alembic_version` exists

### Requirement: REQ-PFB-CONTRACT-003 — Status Screen and E2E Scope

The frontend MUST render loading, healthy, and error states for backend health;
error state MUST include an accessible retry control and MUST NOT expose stack
traces. Playwright MUST run one Chromium-only health smoke spec via `webServer`.

Acceptance: AC-PFB-12, AC-PFB-13.

#### Scenario: Status screen handles success and failure

- GIVEN mocked backend success and failure responses
- WHEN the status screen renders and retry is activated
- THEN Spanish user-facing state text and accessible retry behavior are observable

#### Scenario: E2E uses deterministic server startup

- GIVEN Slice D Playwright config
- WHEN E2E runs
- THEN backend and frontend start via `webServer` without arbitrary sleeps

### Requirement: REQ-PFB-GOV-001 — Governance, Coverage, and Traceability

The cycle MUST preserve SPEC-001 inheritance, prevent language/domain scope creep,
WARN on coverage during construction and FAIL from Slice D, correct the
REQ-001-007/REQ-001-015 matrix drift, use ubuntu-latest CI, and keep Docker out of
scope.

Acceptance: AC-PFB-03, AC-PFB-04, AC-PFB-05, AC-PFB-06, AC-PFB-07, AC-PFB-08,
AC-PFB-09, AC-PFB-14, AC-PFB-15.

#### Scenario: Governance checks are mechanically verifiable

- GIVEN Slice D verification
- WHEN coverage, grep, CI, and traceability checks run
- THEN drift, forbidden domain classes, English hardcoding, and CI gaps fail visibly

_The CI quality-gate requirements below were synced from the `fix-pr5-ci-tooling`
change delta, archived at
`openspec/archive/2026-08-10-fix-pr5-ci-tooling/specs/001-project-foundation/spec.md`._

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

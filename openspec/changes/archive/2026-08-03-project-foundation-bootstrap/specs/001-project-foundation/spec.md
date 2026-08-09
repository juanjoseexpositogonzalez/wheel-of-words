# Delta for 001-project-foundation

This native OpenSpec delta reconciles the legacy full spec at
`openspec/changes/project-foundation-bootstrap/spec.md` into the dispatcher-expected
path. The legacy file remains the detailed audit source; this file preserves its
normative requirements and acceptance identifiers in native shape.

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

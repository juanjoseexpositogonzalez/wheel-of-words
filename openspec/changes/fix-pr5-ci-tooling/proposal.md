# Proposal: Fix PR #5 CI Tooling

## Intent

Repair PR #5 CI failures from cross-job environment assumptions and a nonexistent pnpm lockfile path. Restore quality feedback without product behavior changes.

## Goals

- Reproduce each tool-consuming job on a clean runner.
- Use the committed root lockfile for frontend and E2E setup.
- Prove the repair locally and in PR #5 Actions.

## Scope

### In Scope
- Correct workflow dependency setup and cache paths.
- Add structural regression tests in `apps/api/tests/unit/test_ci_workflow.py`.
- Validate backend, frontend, migration, and E2E paths.

### Out of Scope
- Product, API, frontend, or domain behavior changes.
- Application dependency declarations, except essential workflow quality configuration.
- Functional E2E defects exposed after setup; those need a separate change.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `001-project-foundation`: CI quality gates must be independently reproducible on clean runners.

## Candidate Requirements

- **REQ-CI-001**: Each backend job invoking development tooling MUST run locked `uv sync --extra dev` before the tool.
  - **AC-001**: Lint, typecheck, test, and migration commands run on a clean runner.
- **REQ-CI-002**: Frontend setup MUST use `pnpm-lock.yaml` and frozen installation.
  - **AC-002**: Frontend jobs no longer fail on a missing lockfile path.
- **REQ-CI-003**: E2E MUST prepare locked frontend and backend dependencies before Playwright starts servers.
  - **AC-003**: Chromium E2E runs on a clean runner instead of being skipped by setup failure.

## Proposed Approach

Use self-contained jobs: retain `needs` only for ordering, add per-job backend sync, correct every pnpm cache path to the repository root, and explicitly sync the E2E backend. Cover these invariants with structural tests.

## Validation Plan

Run focused CI tests RED then GREEN, YAML validation, affected quality suites, migration check, and E2E. PR #5 Actions is authoritative: every required job MUST be green. Run adversarial/judge review before merge.

## Sizing and Delivery

Estimate: 60–100 lines. Single PR; chained-slice need: No. 400-line budget risk: Low.

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Setup exposes unrelated E2E failure | Medium | Open a separate CI-only change. |
| Repeated sync increases duration | Medium | Use locked installs and existing caches. |

## Rollback Plan

Revert the workflow and structural-test commit, then rerun PR #5 Actions to restore the prior pipeline definition.

## Dependencies

- GitHub Actions runners, `astral-sh/setup-uv@v5`, pnpm, committed lockfiles.

## Success Criteria

- [ ] PR #5 GitHub Actions is fully green.
- [ ] Structural tests prevent invalid lockfile paths and missing per-job setup.
- [ ] No product behavior or application dependency declaration changes are introduced.

## Next Phase

Create a delta spec for `001-project-foundation`, then produce the technical design and TDD task plan.

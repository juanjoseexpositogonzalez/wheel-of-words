# Tasks: Fix PR #5 CI Tooling

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | 120–160 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR / one work-unit commit |
| Delivery strategy | single-pr |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|
| 1 | Isolate CI jobs and lock dependency setup | PR #5 | `cd apps/api && uv run pytest tests/unit/test_ci_workflow.py` | PR #5 Actions: required jobs incl. Chromium E2E | Revert `.github/workflows/ci.yml`, its structural tests, and CI traceability rows |

## Phase 1: CI Workflow Contracts

- [x] TC01 [TEST] Add failing section assertions in `apps/api/tests/unit/test_ci_workflow.py`: `backend-{lint,typecheck,test}`, `migration-check`, and `e2e` run locked `uv sync --extra dev` before consumers. REQ-CI-001/003, AC-CI-001/003; done when RED fails only for absent setup; est. 25 lines.
- [x] TC02 [TEST] Add failing assertions for root `pnpm-lock.yaml`, frozen frontend installs, retained E2E ordering, and no setup-job dependency. REQ-CI-002/004, AC-CI-002/004; done when RED identifies invalid paths/cross-job assumptions; est. 25 lines.

## Phase 2: Minimal Workflow Repair

- [x] TC03 [IMPL] Edit `.github/workflows/ci.yml`: remove `setup-python`/`setup-node` and `needs` references; add `uv sync --locked --extra dev` inside each backend and E2E job before its command. REQ-CI-001/003, AC-CI-001/003; done when TC01 is GREEN; est. 40–55 lines.
- [x] TC04 [IMPL] Change all Node cache paths to root `pnpm-lock.yaml`; retain frozen installs and `e2e` quality ordering without altering product/E2E assertions. REQ-CI-002/004, AC-CI-002/004; done when TC02 is GREEN; est. 20–30 lines.
- [x] TC05 [REFACTOR] Tighten duplicated section helpers/assertions in `apps/api/tests/unit/test_ci_workflow.py` only if behavior remains unchanged. REQ-CI-001–004; done when focused test remains GREEN; est. 10–20 lines.

## Phase 3: Verification and Traceability

- [x] TC06 [TEST] Validate YAML and run focused plus affected commands: `ruby -e 'require "yaml"; YAML.load_file(".github/workflows/ci.yml")'`, backend lint/typecheck/test/migration, frontend lint/typecheck/test, and Playwright. REQ-CI-001–004; keep unrelated E2E failures visible; est. 0 lines.
- [x] TC07 [DOC] Add REQ-CI-001–004 rows to `docs/traceability-matrix.md`, linking ACs, `test_ci_workflow.py`, TC01–TC06, and initial status `En progreso`. REQ-CI-001–004; done when all rows are traceable; est. 4–8 lines.
- [ ] TC08 [SECURITY] Push the CI-only work-unit commit, confirm all PR #5 Actions jobs are green, then complete adversarial/judge review before any merge decision. REQ-CI-001–004; done when remote evidence and review outcome are recorded; est. 0 lines.

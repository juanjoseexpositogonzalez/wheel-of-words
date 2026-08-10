# Design: Fix PR #5 CI Tooling

## Technical Approach

Repair `.github/workflows/ci.yml` so every GitHub Actions job is self-contained. Replace the cross-job setup gates with each consumer job installing its own locked dependencies, point Node caching to the committed root lockfile, and protect these invariants through the existing Python structural-test pattern. This implements REQ-CI-001 through REQ-CI-004 without changing runtime application behavior.

## Architecture Decisions

| Decision | Choice | Alternative / trade-off | Rationale |
|---|---|---|---|
| Job isolation | Remove `setup-python` and `setup-node`; add `cd apps/api && uv sync --locked --extra dev` before each backend command, including E2E. | Keep setup jobs and `needs`; jobs still cannot share their environments. | A runner is the ownership boundary. Removing redundant gates avoids duplicated frontend lint and setup-only skips. |
| Node install source | Retain `cd apps/web && pnpm install --frozen-lockfile`; change every `cache-dependency-path` to `pnpm-lock.yaml`. | Add an app-local lockfile or change dependencies. | The root workspace declares `apps/web` and owns the committed lockfile. |
| Regression coverage | Extend `test_ci_workflow.py` with text-section assertions per job. | Add a YAML parser dependency or test Actions remotely only. | Existing tests intentionally read workflow text; precise sections keep the repair dependency-free and fast. |

## Data Flow

```
checkout → tool setup → locked dependency install → quality/E2E command → GitHub status
                         │
                         └─ each job's isolated runner only
```

`e2e` retains `needs: [backend-test, frontend-test]` only as a quality ordering gate; its own `uv sync` and frontend install happen before Playwright starts the Makefile/Vite servers. A setup or application failure therefore fails its owning job; it is never masked by changing test expectations.

## File Changes

| File | Action | Description |
|---|---|---|
| `.github/workflows/ci.yml` | Modify | Remove shared setup jobs, add locked backend setup to four backend jobs and E2E, and correct four pnpm cache paths. |
| `apps/api/tests/unit/test_ci_workflow.py` | Modify | Add structural contracts for job-local setup ordering, root lockfile cache paths, frozen Node install, and E2E preparation. |
| `openspec/changes/fix-pr5-ci-tooling/design.md` | Create | This technical design. |

Estimated implementation delta: 70–110 lines; below the 400-line single-PR budget.

## Interfaces / Contracts

No product or API interface changes. Workflow contract:

```text
backend-{lint,typecheck,test}, migration-check, e2e:
  uv sync --locked --extra dev precedes uv run / Playwright server startup
frontend-{lint,typecheck,test}, e2e:
  cache-dependency-path: pnpm-lock.yaml
  pnpm install --frozen-lockfile precedes the consumer command
```

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit (RED/GREEN) | REQ-CI-001–003 workflow invariants | First add failing section assertions; then edit YAML minimally until `cd apps/api && uv run pytest tests/unit/test_ci_workflow.py` passes. |
| Local integration | Locked installs and all affected commands | Run backend lint/typecheck/test/migration, frontend lint/typecheck/test, and `pnpm exec playwright test`; failures after successful setup are reported, not fixed here. |
| Remote integration | Actual clean-runner behavior and merge gate | Push the CI-only commit to PR #5 and inspect Actions: every required job, including Chromium E2E, must be green. After CI is corrected, adversarial/judge review remains required before the merge decision. |

Validate YAML syntax before remote execution. Follow RED → minimal GREEN → refactor only if behavior is unchanged; rerun the focused structural test after refactoring.

## Threat Matrix

| Boundary | Applicability | Safe/failure behavior | Planned RED test |
|---|---|---|---|
| Documentation-like paths | N/A — no executable classification | N/A | N/A |
| Git repository selection | N/A — workflow uses checkout only | N/A | N/A |
| Commit state | N/A — no commit operation | N/A | N/A |
| Push state | N/A — no push operation | N/A | N/A |
| PR commands | N/A — no PR CLI automation | N/A | N/A |

## Migration / Rollout

No migration or feature flag required. Roll out by committing the workflow and test changes, then use PR #5 Actions as authoritative proof. After all required jobs are green, complete adversarial/judge review before deciding whether to merge. If a new failure is unrelated to dependency setup, keep it visible and open a separate change. Roll back with a revert of this CI-only commit and rerun Actions.

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Dependency setup reveals an unrelated E2E defect | Medium | Keep the failure visible and open a separate change; do not alter product behavior or E2E assertions. |
| Per-job locked sync increases CI duration | Medium | Retain pnpm caching and measure PR #5 Actions before considering later optimization. |
| Green CI is treated as sufficient for merge | Low | Enforce adversarial/judge review after CI correction and before the merge decision. |

## Open Questions

None.

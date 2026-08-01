# Tasks: project-foundation-bootstrap

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | ~1263 aggregate; each slice ≤400 |
| 400-line budget risk | Low per PR / High aggregate |
| Chained PRs recommended | Yes |
| Suggested split | A → B1 → B2 → C → D |
| Delivery strategy | ask-always |
| Chain strategy | feature-branch-chain |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|
| A | Scaffold + smoke | PR A → tracker | `make test-backend` | `make bootstrap` | scaffold only |
| B1 | Settings + health | PR B1 → slice-a | `cd apps/api && uv run pytest tests/unit tests/api` | `make dev-backend` | backend app only |
| B2 | SQLAlchemy + Alembic | PR B2 → slice-b1 | `cd apps/api && uv run pytest tests/integration` | `make migrate` | persistence wiring |
| C | Status screen | PR C → slice-b2 | `cd apps/web && pnpm run test` | `make dev` | `apps/web/` |
| D | E2E + CI + docs | PR D → slice-c | `make test-e2e` | `pnpm exec playwright test` | CI/docs/e2e only |

## Phase 1: Slice A — Scaffold

- [x] TA01 [BOOTSTRAP] Create repo/app/test/workspace skeleton under `apps/`, `.github/`, `pnpm-workspace.yaml`.
- [x] TA02 [BOOTSTRAP] Add `apps/api/pyproject.toml` for `wheel_vocabulary`, pytest, Ruff, mypy, coverage.
- [x] TA03 [BOOTSTRAP] Generate `apps/api/uv.lock` and sync dev dependencies.
- [x] TA04 [BOOTSTRAP] Create `apps/api/src/wheel_vocabulary/{domain,application,infrastructure,api}` package tree.
- [x] TA05 [BOOTSTRAP] Add minimal `apps/api/tests/conftest.py`.
- [x] TA06 [BOOTSTRAP] Add `apps/web/package.json`, `tsconfig*.json`, `index.html`.
- [x] TA07 [BOOTSTRAP] Add `apps/web/vite.config.ts` and `vitest.config.ts`.
- [x] TA08 [BOOTSTRAP] Add `apps/web/.eslintrc.cjs` and `pnpm-lock.yaml`.
- [x] TA09 [BOOTSTRAP] Add `apps/web/src/main.tsx` and `App.tsx` stubs.
- [x] TA10 [BOOTSTRAP] Add root `Makefile` targets for bootstrap/dev/test/lint/typecheck/migrate.
- [x] TA11 [BOOTSTRAP] Add repo `.env.example` with backend/frontend safe defaults.
- [x] TA12 [BOOTSTRAP] Extend `.gitignore` for venv, caches, DB, node, env files.
- [x] TA13 [DOC] Add `apps/api/README.md` and `apps/web/README.md` stubs.
- [x] TA14 [SPEC] Align `design.md` to `wheel_vocabulary` override.
- [x] TA15-SMOKE [TEST] Add `apps/api/tests/smoke/test_smoke.py` as first RED→GREEN anchor.

## Phase 2: Slice B1 — Backend health path

- [x] TB101 [TEST] RED settings tests in `apps/api/tests/unit/test_settings.py`.
- [x] TB102 [IMPL] GREEN `apps/api/src/wheel_vocabulary/infrastructure/settings.py`.
- [x] TB103 [TEST] RED clock tests in `apps/api/tests/unit/test_clock.py`.
- [x] TB104 [IMPL] GREEN `application/clock.py` and `infrastructure/clock.py`.
- [x] TB105 [TEST] RED version tests in `apps/api/tests/unit/test_version.py`.
- [x] TB106 [IMPL] GREEN `apps/api/src/wheel_vocabulary/infrastructure/version.py`.
- [x] TB107 [SPEC] Add `apps/api/src/wheel_vocabulary/api/schemas/health.v1.json`.
- [x] TB108 [TEST] RED DTO tests in `apps/api/tests/unit/test_health_dto.py`.
- [x] TB109 [IMPL] GREEN `apps/api/src/wheel_vocabulary/api/dtos/health.py`.
- [x] TB110 [TEST] RED route tests in `apps/api/tests/api/test_health.py`.
- [x] TB111 [IMPL] GREEN `apps/api/src/wheel_vocabulary/api/main.py` and `routes/health.py`.
- [x] TB112 [REFACTOR] Remove duplication without adding speculative abstractions.

## Phase 3: Slice B2 — Persistence baseline

- [x] TB201 [TEST] RED engine/session tests in `apps/api/tests/integration/test_engine.py`.
- [x] TB202 [IMPL] GREEN `apps/api/src/wheel_vocabulary/infrastructure/persistence/engine.py`.
- [x] TB203 [TEST] RED empty-metadata test in `apps/api/tests/integration/test_base.py`.
- [x] TB204 [IMPL] GREEN `apps/api/src/wheel_vocabulary/infrastructure/persistence/base.py`.
- [x] TB205 [MIGRATION] Add `apps/api/alembic.ini`, `migrations/env.py`, `script.py.mako`, `versions/0001_baseline.py`.
- [x] TB206 [TEST] RED/GREEN Alembic integration tests in `apps/api/tests/integration/test_alembic.py`.
- [x] TB207 [IMPL] Add shared Alembic/temp-DB fixtures in `apps/api/tests/conftest.py`.
- [x] TB208 [REFACTOR] Clean persistence duplication and keep tests/lint/typecheck green.

## Phase 4: Slice C — Frontend status screen

- [ ] TC01 [TEST] RED `apps/web/tests/api/client.test.ts` and `src/types/health.ts` contract.
- [ ] TC02 [IMPL] GREEN `apps/web/src/api/client.ts` and `src/types/health.ts`.
- [ ] TC03 [TEST] RED `apps/web/tests/components/StatusLoading.test.tsx`.
- [ ] TC04 [IMPL] GREEN `apps/web/src/components/StatusLoading.tsx`.
- [ ] TC05 [TEST] RED `apps/web/tests/components/StatusHealthy.test.tsx`.
- [ ] TC06 [IMPL] GREEN `apps/web/src/components/StatusHealthy.tsx`.
- [ ] TC07 [TEST] RED `apps/web/tests/components/StatusError.test.tsx`.
- [ ] TC08 [IMPL] GREEN `apps/web/src/components/StatusError.tsx`.
- [ ] TC09 [TEST] RED `apps/web/tests/components/StatusPage.test.tsx`.
- [ ] TC10 [IMPL] GREEN `apps/web/src/pages/StatusPage.tsx`.
- [ ] TC11 [IMPL] Wire `StatusPage` into `apps/web/src/App.tsx` and `main.tsx`.
- [ ] TC12 [SPEC] Add `apps/web/src/styles/status.css` and import it.
- [ ] TC13 [REFACTOR] Remove frontend duplication; keep test/lint/typecheck green.

## Phase 5: Slice D — E2E, CI, docs, traceability

- [ ] TD01 [E2E] Add `apps/web/e2e/status.spec.ts` without sleeps.
- [ ] TD02 [E2E] Add `apps/web/playwright.config.ts` `webServer` + Chromium-only config.
- [ ] TD03 [CI] Add `.github/workflows/ci.yml` with backend/frontend/migration/e2e jobs.
- [ ] TD04 [TEST] RED traceability regression tests in `apps/api/tests/unit/test_traceability.py`.
- [ ] TD05 [DOC] Fix `docs/traceability-matrix.md` for REQ-001-007 and REQ-001-015.
- [ ] TD06 [DOC] Update root `README.md` status and next-work section only.
- [ ] TD07 [DOC] Add `project-foundation-bootstrap` close-out entry to `docs/decisions-log.md`.
- [ ] TD08 [SECURITY] Add `apps/api/tests/api/test_health_security.py` no-PII/no-env-leak assertions.
- [ ] TD09 [REFACTOR] Final cleanup with `make lint && make typecheck && make test && make test-e2e`.
- [ ] TD10 [BOOTSTRAP] Upsert Engram `sdd/wheel-of-words/testing-capabilities` after CI green.

# SDD Archive Report — fix-pr5-ci-tooling

**Date**: 2026-08-10
**Artifact store**: hybrid (OpenSpec + Engram)
**Status**: archived — intentional partial archive (no verify phase; see "Verification gap")

## Final state

The CI tooling repair is implemented, merged, and live on `main`.

- Shipped commit: `61ab356` — `ci: fix PR workflow dependency setup`. Confirmed contained in
  `main` and `origin/main`. It touches `.github/workflows/ci.yml`,
  `apps/api/tests/unit/test_ci_workflow.py`, and `docs/traceability-matrix.md`
  (100 insertions, 33 deletions).
- The commit was originally authored as `adebe99` and was rewritten to `61ab356` when the
  project-foundation PR chain was split. Both hashes denote the same work unit.
- Final integration reached `main` through the project-foundation PR chain; the last
  integrating pull request was **PR #13**, merge commit `aa3042d`.
- CI was green on `main` at that point: run `31393451500`, all 8 jobs passing
  (`backend-lint`, `backend-test`, `backend-typecheck`, `migration-check`, `frontend-lint`,
  `frontend-typecheck`, `frontend-test`, `e2e`).
- Earlier, on the original PR #5 branch, run `31374547599` also passed all backend, frontend,
  migration, and E2E jobs (per Engram `#3785`). The two runs are complementary evidence at
  different points, not competing claims.
- `main` has since advanced to `aefbcf0` (PR #16, backend test-warnings cleanup) and CI remains
  green. The backend suite now reports **50 passed, zero warnings, 99% coverage**, with
  `filterwarnings` configured as an error gate in `apps/api/pyproject.toml`
  (`error::ResourceWarning`, `error::pytest.PytestUnraisableExceptionWarning`,
  `error::starlette.exceptions.StarletteDeprecationWarning`).

All four requirements are observably satisfied by the shipped workflow:

| Requirement | Shipped evidence in `.github/workflows/ci.yml` |
|---|---|
| REQ-CI-001 | `cd apps/api && uv sync --locked --extra dev` present in `backend-lint`, `backend-typecheck`, `backend-test`, and `migration-check`, each preceded by `astral-sh/setup-uv@v5`. |
| REQ-CI-002 | `cache-dependency-path: pnpm-lock.yaml` (repository root) plus `pnpm install --frozen-lockfile` in all three frontend jobs and in `e2e`. |
| REQ-CI-003 | `e2e` runs both `uv sync --locked --extra dev` and `pnpm install --frozen-lockfile` before Playwright; `needs: [backend-test, frontend-test]` is retained for ordering only. |
| REQ-CI-004 | Change is confined to workflow setup, structural tests, and traceability rows; no product, API, or E2E assertion changes appear in `61ab356`. |

## Verification gap (explicit, non-blocking)

**No formal `sdd-verify` phase ever ran for this cycle.** There is no `verify-report.md` in the
change folder and no `sdd/fix-pr5-ci-tooling/verify-report` observation in Engram. This archive
therefore proceeds as an **intentional partial archive**, explicitly authorized by the
orchestrator.

The verification evidence that does exist:

1. **Local validation (TC06)** — recorded in the `apply-progress` snapshot (Engram `#3766`,
   2026-08-10 11:02:49): YAML parse, focused workflow tests (8 passed), Ruff check and format,
   mypy (19 files, no issues), backend coverage (50 passed, 99%), `alembic upgrade head`,
   frontend lint/typecheck/coverage (12 tests, 100% lines), and Playwright Chromium (1 test).
   All exited 0.
2. **Green hosted CI** — runs `31374547599` (PR branch) and `31393451500` (on `main`, 8/8 jobs).

Green CI on `main` is the strongest verification signal available for this change, but it is
**not** a substitute for a verify phase: no one re-ran the spec's acceptance criteria against the
implementation as a distinct, recorded verification step. This gap is stated here rather than
papered over. Because no verify report exists, there are also no CRITICAL verification findings,
so nothing blocks archive under the strict archive policy.

## Task completion — TC08 remains unchecked (deliberate)

The archived `tasks.md` shows **7 of 8 tasks checked**. TC08 is still `- [ ]`:

> TC08 [SECURITY] Push the CI-only work-unit commit, confirm all PR #5 Actions jobs are green,
> then complete adversarial/judge review before any merge decision.

Every element of TC08 is in fact satisfied by later evidence:

| TC08 element | Evidence | Source |
|---|---|---|
| Push the CI-only work-unit commit | `adebe99` pushed, later `61ab356` on `main` | Engram `#3785`; `git branch --contains` |
| Confirm all Actions jobs green | PR run `31374547599` green; `main` run `31393451500`, 8/8 | Engram `#3785`; orchestrator final-state facts |
| Adversarial/judge review before merge | Native high-risk review ran, required an explicit `astral-sh/setup-uv@v5`-before-`uv sync` assertion in the E2E contract, then approved; pre-commit and pre-push gates allowed | Engram `#3785` |

The review finding is independently corroborated in the shipped tree: `test_ci_workflow.py:49`
asserts `"astral-sh/setup-uv@v5" in e2e`.

**The checkbox was nevertheless left unchecked, on purpose.** The archive skill permits archive-time
checkbox reconciliation only when the orchestrator explicitly instructs it *and* `apply-progress`
or `verify-report` prove completion. Neither precondition held: the orchestrator gave no
reconciliation instruction, and `apply-progress` (`#3766`) is precisely the artifact that records
TC08 as pending. The proof arrived afterwards, in a delivery observation (`#3785`) and in the
orchestrator's final-state facts — sources that the reconciliation rule does not accept.

Altering the archived audit trail on weaker authority than the rule requires would be a worse
outcome than an unchecked box carrying a documented explanation. Readers should treat TC08 as
**complete in substance, unchecked in the artifact**, per this section.

## Contradictions surfaced (not silently resolved)

1. **"PR #5" throughout the artifacts vs. PR #13 as the real integration point.** `proposal.md`,
   `design.md`, `tasks.md`, and `exploration.md` all name PR #5 as the authoritative Actions
   surface, because they were written before the project-foundation PR chain was split. The work
   actually merged via PR #13 (`aa3042d`), and the commit hash changed from `adebe99` to
   `61ab356`. This is rankable: the orchestrator's final-state facts outrank the point-in-time
   artifacts, so the final state above is authoritative. The artifacts are left unedited as
   historical record.
2. **`apply-progress` (`#3766`) says "Partial — 7/8, TC08 pending" vs. delivery evidence.** That
   snapshot was written at 11:02:49; delivery completed and was recorded at 11:27:42 (`#3785`).
   The snapshot's "pending" claim was valid only at its own timestamp. Reported as final state
   above; the snapshot is not echoed as current fact.
3. **`apply-progress` risk note "Remote PR #5 Actions ... has not been executed"** is likewise
   superseded — hosted Actions ran green twice afterwards.

## Spec synchronization

**Decision: synced.** The delta contributed four requirements that the canonical spec did not
carry.

- Delta: `specs/001-project-foundation/spec.md`, section `## ADDED Requirements`, containing
  REQ-CI-001 through REQ-CI-004 with one scenario each.
- Canonical: `openspec/specs/001-project-foundation/spec.md`, which before this sync contained
  only the five `REQ-PFB-*` requirements and **zero** occurrences of `REQ-CI` (verified by
  `grep -c`).
- `proposal.md` explicitly lists `001-project-foundation` under *Modified Capabilities*, and
  `openspec/config.yaml` `rules.archive` mandates: "Archive MUST sync delta specs into
  `openspec/specs/` if the change modified a capability spec."

The sync was performed as a **pure append**:

- The four requirement blocks were appended byte-for-byte from the delta via shell
  (`tail -n +5` piped to `>>`), never re-typed through the model. A `diff` of the appended region
  against the delta source returned empty.
- The canonical spec's pre-existing 99 lines were verified byte-identical to a pre-edit backup
  after the append. This matters: that file was corrected twice (PR #10 and PR #12) after
  adversarial review found stale archive references in its header. **Those corrections are
  untouched.** Nothing was overwritten, reordered, modified, or removed.
- A short provenance note was added above the appended block, pointing at this archive directory
  (a permanent path) rather than at the now-nonexistent `openspec/changes/` path — deliberately
  avoiding the stale-reference class of defect that PR #10 and PR #12 had to fix.

Result: 4 requirements added, 0 modified, 0 removed. Canonical spec grew from 99 to 165 lines and
now holds 9 requirements (5 `REQ-PFB-*`, 4 `REQ-CI-*`).

Before syncing, each REQ-CI requirement was checked against the shipped `.github/workflows/ci.yml`
rather than trusted from the artifact alone; see the requirement table under "Final state". The
canonical spec therefore describes behavior that is currently true on `main`.

## Archived artifacts

The complete change folder was moved with `git mv` (history preserved) to:

`openspec/archive/2026-08-10-fix-pr5-ci-tooling/`

Contents: `proposal.md`, `exploration.md`, `design.md`, `tasks.md`,
`specs/001-project-foundation/spec.md`, and this archive report.

The move was verified by `diff -r` against a recursive pre-move snapshot; the diff was empty, so
the archived tree is byte-identical to the source. No `verify-report.md` exists to archive.

Note on path convention: the generic skill documents `openspec/changes/archive/`, but this
repository has established `openspec/archive/` (see the 2026-07-16 and 2026-08-03 archives).
Repository precedent was followed.

## Traceability sources

### OpenSpec files

- `openspec/archive/2026-08-10-fix-pr5-ci-tooling/proposal.md`
- `openspec/archive/2026-08-10-fix-pr5-ci-tooling/exploration.md`
- `openspec/archive/2026-08-10-fix-pr5-ci-tooling/design.md`
- `openspec/archive/2026-08-10-fix-pr5-ci-tooling/tasks.md`
- `openspec/archive/2026-08-10-fix-pr5-ci-tooling/specs/001-project-foundation/spec.md`
- `openspec/specs/001-project-foundation/spec.md` (updated by this archive)

### Engram observations read

- `#3743` — `sdd/fix-pr5-ci-tooling/explore`
- `#3745` — `sdd/fix-pr5-ci-tooling/proposal`
- `#3747` — `sdd/fix-pr5-ci-tooling/spec`
- `#3749` — `sdd/fix-pr5-ci-tooling/design`
- `#3761` — `sdd/fix-pr5-ci-tooling/tasks`
- `#3766` — `sdd/fix-pr5-ci-tooling/apply-progress` (intermediate snapshot)
- `#3785` — `sdd/fix-pr5-ci-tooling/delivery` (commit, hosted CI, native review approval)
- `#3752`, `#3755`, `#3757` — design phase-contract validation and gate-drift correction
- `#3769`, `#3771`, `#3773` — apply blockage on missing `pnpm`, then local validation completion

No `sdd/fix-pr5-ci-tooling/verify-report` observation exists, consistent with the verification gap
recorded above.

### Native review gate

No `reviewGate` was present in structured status for this candidate at archive time, so archive
proceeded under ordinary repository policy. The native high-risk review recorded in `#3785`
relates to the delivery gates (pre-commit/pre-push) and is reported as delivery evidence, not as a
receipt-driven archive gate.

## Risks and follow-up

Reported for the maintainer; **not acted upon**, because these live outside the archive's scope:

1. **`docs/traceability-matrix.md` now holds stale references.** Rows 48–51 point at
   `openspec/changes/fix-pr5-ci-tooling/specs/001-project-foundation/spec.md`, a path this archive
   just removed. They should point at either
   `openspec/archive/2026-08-10-fix-pr5-ci-tooling/specs/001-project-foundation/spec.md` or, better,
   the now-canonical `openspec/specs/001-project-foundation/spec.md`. The same four rows also still
   carry status `En progreso`, which is stale for shipped and merged work. This is the same defect
   class that adversarial review caught in PR #10 and PR #12.
2. **`openspec/config.yaml` `open_issues` is stale.** Issues #14 (SQLite `ResourceWarning`) and #15
   (`StarletteDeprecationWarning`) are recorded as open, but both were resolved on `main` by
   `a2d6d88` and `d04a85e`, and the suite now runs with zero warnings behind a `filterwarnings`
   error gate.
3. **The missing verify phase** described above. If a formal record is wanted, `sdd-verify` can be
   run retroactively against the shipped implementation.

No commit, stage, push, or pull request was created by this archive.

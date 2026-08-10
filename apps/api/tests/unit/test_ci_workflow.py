"""Structural contract tests for the Slice D CI workflow (TD03)."""

from pathlib import Path

_REPOSITORY_ROOT = Path(__file__).parents[4]
_WORKFLOW = _REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml"


def _job_section(workflow: str, job_name: str, next_job_name: str | None) -> str:
    section = workflow.split(f"  {job_name}:", maxsplit=1)[1]
    if next_job_name is not None:
        section = section.split(f"  {next_job_name}:", maxsplit=1)[0]
    return section


def test_ci_workflow_defines_the_required_quality_jobs() -> None:
    workflow = _WORKFLOW.read_text(encoding="utf-8")

    for job in (
        "backend-lint:",
        "backend-typecheck:",
        "backend-test:",
        "migration-check:",
        "frontend-lint:",
        "frontend-typecheck:",
        "frontend-test:",
        "e2e:",
    ):
        assert job in workflow


def test_ci_workflow_enforces_coverage_and_chromium_e2e() -> None:
    workflow = _WORKFLOW.read_text(encoding="utf-8")

    assert "CI_COVERAGE_MODE: fail" in workflow
    assert "--cov-fail-under=80" in workflow
    assert "playwright install chromium" in workflow


def test_ci_workflow_runs_frontend_lint_and_prepares_backend_for_e2e() -> None:
    workflow = _WORKFLOW.read_text(encoding="utf-8")

    frontend_lint = workflow.split("  frontend-lint:", maxsplit=1)[1].split(
        "  frontend-typecheck:", maxsplit=1
    )[0]
    e2e = workflow.split("  e2e:", maxsplit=1)[1]

    assert "pnpm run lint" in frontend_lint
    assert "astral-sh/setup-uv@v5" in e2e


def test_ci_workflow_does_not_use_invalid_steps_alias_splicing() -> None:
    workflow = _WORKFLOW.read_text(encoding="utf-8")

    assert "*backend-setup" not in workflow
    assert "*frontend-setup" not in workflow


def test_backend_jobs_sync_locked_development_tools_before_consuming_them() -> None:
    workflow = _WORKFLOW.read_text(encoding="utf-8")
    jobs = (
        ("backend-lint", "backend-typecheck", "uv run ruff check ."),
        ("backend-typecheck", "backend-test", "uv run mypy src/wheel_vocabulary"),
        ("backend-test", "migration-check", "uv run pytest"),
        ("migration-check", "frontend-lint", "uv run alembic upgrade head"),
    )

    for job_name, next_job_name, consumer in jobs:
        job = _job_section(workflow, job_name, next_job_name)
        setup = "cd apps/api && uv sync --locked --extra dev"

        assert setup in job
        assert job.index(setup) < job.index(consumer)


def test_e2e_job_prepares_locked_backend_dependencies_before_playwright() -> None:
    workflow = _WORKFLOW.read_text(encoding="utf-8")
    e2e = _job_section(workflow, "e2e", None)
    uv_install = "uses: astral-sh/setup-uv@v5"
    backend_setup = "cd apps/api && uv sync --locked --extra dev"

    assert uv_install in e2e
    assert backend_setup in e2e
    assert e2e.index(uv_install) < e2e.index(backend_setup)
    assert e2e.index(backend_setup) < e2e.index("playwright install chromium")
    assert e2e.index(backend_setup) < e2e.index("playwright test")


def test_frontend_jobs_use_root_lockfile_and_frozen_install_before_consumers() -> None:
    workflow = _WORKFLOW.read_text(encoding="utf-8")
    jobs = (
        ("frontend-lint", "frontend-typecheck", "pnpm run lint"),
        ("frontend-typecheck", "frontend-test", "pnpm run typecheck"),
        ("frontend-test", "e2e", "pnpm run test:coverage"),
        ("e2e", None, "playwright test"),
    )

    for job_name, next_job_name, consumer in jobs:
        job = _job_section(workflow, job_name, next_job_name)
        install = "cd apps/web && pnpm install --frozen-lockfile"

        assert "cache-dependency-path: pnpm-lock.yaml" in job
        assert install in job
        assert job.index(install) < job.index(consumer)


def test_ci_jobs_do_not_depend_on_setup_jobs_and_e2e_keeps_quality_ordering() -> None:
    workflow = _WORKFLOW.read_text(encoding="utf-8")

    assert "  setup-python:" not in workflow
    assert "  setup-node:" not in workflow
    assert "needs: setup-python" not in workflow
    assert "needs: setup-node" not in workflow

    e2e = _job_section(workflow, "e2e", None)
    assert "needs: [backend-test, frontend-test]" in e2e

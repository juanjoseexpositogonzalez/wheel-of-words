"""Structural contract tests for the Slice D CI workflow (TD03)."""

from pathlib import Path

_REPOSITORY_ROOT = Path(__file__).parents[4]
_WORKFLOW = _REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml"


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

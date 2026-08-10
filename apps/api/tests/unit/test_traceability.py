"""Regression tests for the SPEC-001 traceability corrections (TD04/TD05)."""

import re
from pathlib import Path

_REPOSITORY_ROOT = Path(__file__).parents[4]
_MATRIX = _REPOSITORY_ROOT / "docs" / "traceability-matrix.md"
_README = _REPOSITORY_ROOT / "README.md"
_TASKS = (
    _REPOSITORY_ROOT
    / "openspec"
    / "archive"
    / "2026-08-03-project-foundation-bootstrap"
    / "tasks.md"
)


def test_configuration_requirement_has_its_own_traceability_row() -> None:
    matrix = _MATRIX.read_text(encoding="utf-8")

    assert "| REQ-001-007 | Configuración por entorno con valores de ejemplo seguros" in matrix
    assert "| REQ-001-007 | El dominio no contiene imports" not in matrix


def test_hexagonal_requirement_is_traced_separately() -> None:
    matrix = _MATRIX.read_text(encoding="utf-8")

    row = next(line for line in matrix.splitlines() if line.startswith("| REQ-001-015 |"))

    assert "Capas backend hexagonales con fronteras de framework" in row
    assert "docs/adr/0002-hexagonal-split.md#decision" in row
    assert "AC-015" not in row


def test_all_functional_foundation_requirements_have_exactly_one_row() -> None:
    matrix = _MATRIX.read_text(encoding="utf-8")

    for number in range(1, 19):
        requirement = f"| REQ-001-{number:03d} |"
        assert matrix.count(requirement) == 1


def test_readme_documents_the_foundation_command_surface() -> None:
    readme = _README.read_text(encoding="utf-8")

    for command in (
        "make install",
        "make dev",
        "make test",
        "make lint",
        "make typecheck",
        "make format",
        "make migrate",
    ):
        assert command in readme


def test_bootstrap_tasks_are_explicitly_tagged_before_the_smoke_anchor() -> None:
    tasks = _TASKS.read_text(encoding="utf-8")
    slice_a, _ = tasks.split("## Phase 2:", maxsplit=1)

    assert "TA15-SMOKE [TEST]" in slice_a
    prerequisites = re.findall(r"^- \[x\] (TA\d+) \[([^]]+)\]", slice_a, flags=re.MULTILINE)

    assert prerequisites
    assert all(tag == "BOOTSTRAP" for task, tag in prerequisites if task != "TA15")

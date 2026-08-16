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

_PLACEHOLDER_RE = re.compile(r"(?:^|\b)(?:N/A|TODO|TBD|NONE|PENDING)\b", re.IGNORECASE)


def _matrix_rows(matrix: str) -> list[list[str]]:
    """Return content rows from the repository traceability matrix."""
    rows: list[list[str]] = []
    for line in matrix.splitlines():
        if not line.startswith("| REQ-"):
            continue
        rows.append([cell.strip() for cell in line.strip("|").split("|")])
    return rows


def _rows_for_prefix(matrix: str, prefix: str) -> list[list[str]]:
    return [row for row in _matrix_rows(matrix) if row[0].startswith(prefix)]


def _requirement_ids(rows: list[list[str]]) -> list[str]:
    return [row[0] for row in rows]


def _is_placeholder(value: str) -> bool:
    normalized = value.strip().strip("`*_ ").strip()
    return bool(_PLACEHOLDER_RE.search(normalized))


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


def test_all_text_import_requirements_have_exactly_one_row() -> None:
    matrix = _MATRIX.read_text(encoding="utf-8")
    rows = _rows_for_prefix(matrix, "REQ-002-")

    assert sorted(_requirement_ids(rows)) == [f"REQ-002-{number:03d}" for number in range(1, 19)]


def test_text_import_traceability_rows_are_fulfilled_and_evidenced() -> None:
    matrix = _MATRIX.read_text(encoding="utf-8")
    rows = _rows_for_prefix(matrix, "REQ-002-")

    assert rows
    for req_id, _statement, acceptance, tests, tasks, status in rows:
        assert status.startswith("Cumplido"), req_id
        assert "openspec/changes/text-import/specs/002-text-import/spec.md" in acceptance
        assert not _is_placeholder(acceptance), req_id
        assert tests, req_id
        assert not _is_placeholder(tests), req_id
        assert tasks, req_id
        assert not _is_placeholder(tasks), req_id


def test_text_import_traceability_guard_rejects_missing_duplicate_or_open_rows() -> None:
    matrix = "\n".join(
        [
            "| REQ ID | Statement | Acceptance | Test file(s) | Task(s) | Status |",
            "|--------|--------------------|--------------------------|--------------|---------|--------|",
            "| REQ-002-001 | one | spec.md — AC-01 | test.py | T1 | Cumplido |",
            "| REQ-002-001 | duplicate | spec.md — AC-01 | test.py | T1 | Cumplido |",
            "| REQ-002-003 | open | spec.md — AC-03 | test.py | T3 | En progreso |",
            "| REQ-002-004 | placeholder | spec.md — AC-04 | TODO | TBD | Cumplido |",
            "| REQ-002-005 | markdown placeholder | spec.md — AC-05 | `TODO` | `TBD` | Cumplido |",
            "| REQ-002-006 | emphasized placeholder | spec.md — AC-06 "
            "| **TODO** | _TBD_ | Cumplido |",
            "| REQ-002-007 | acceptance placeholder | spec.md — TODO | test.py | T7 | Cumplido |",
        ]
    )
    rows = _rows_for_prefix(matrix, "REQ-002-")

    assert _requirement_ids(rows) != [f"REQ-002-{number:03d}" for number in range(1, 19)]
    assert any(not row[5].startswith("Cumplido") for row in rows)
    assert any(row[0] == "REQ-002-004" and _is_placeholder(row[3]) for row in rows)
    assert any(row[0] == "REQ-002-005" and _is_placeholder(row[3]) for row in rows)
    assert any(row[0] == "REQ-002-006" and _is_placeholder(row[3]) for row in rows)
    assert any(row[0] == "REQ-002-007" and _is_placeholder(row[2]) for row in rows)


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

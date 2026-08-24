"""Structural guard — the annotation write path cannot reach `ManualCorrection` (R3).

Design §P3: read and write live in **two separate modules** precisely so this
assertion is cheap and exact. `annotation_write_repository.py` MUST NOT
import, reference, or otherwise mention `ManualCorrection` anywhere in its
source — not in an import statement, not as a bare name, not as an attribute
access, not in a string literal. This is what makes R2/R3 unforgeable rather
than merely checked: the write path has no branch that could fail to check a
correction, because it cannot see the correction table at all
(REQ-003-011, AC-003-11 scenario 3).

Written RED before `infrastructure/persistence/annotation_write_repository.py`
exists — the file-not-found is the only thing that can fail at this stage.

MUTATION CHECK — this is an ABSENCE assertion. It passes on its first run over
correct code, which proves nothing on its own. Verified by temporarily adding
``from wheel_vocabulary.infrastructure.persistence.models import ManualCorrection``
to the write repository, confirming the ``AssertionError`` named the import,
then reverting.

REQ-003-011 / AC-003-11.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_WRITE_REPOSITORY_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "wheel_vocabulary"
    / "infrastructure"
    / "persistence"
    / "annotation_write_repository.py"
)


def _references_to(source: str, label: str, forbidden_name: str) -> list[str]:
    """Report every AST node in `source` that names `forbidden_name`."""
    tree = ast.parse(source, filename=label)
    violations: list[str] = []

    for node in ast.walk(tree):
        line = getattr(node, "lineno", 0)
        if isinstance(node, ast.Name) and node.id == forbidden_name:
            violations.append(f"{label}:{line} name {node.id!r}")
        elif isinstance(node, ast.Attribute) and node.attr == forbidden_name:
            violations.append(f"{label}:{line} attribute {node.attr!r}")
        elif isinstance(node, ast.alias) and forbidden_name in (node.name, node.asname):
            violations.append(f"{label}:{line} import alias {node.name!r}")
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            if node.module.endswith(forbidden_name) or node.module == forbidden_name:
                violations.append(f"{label}:{line} imported module {node.module!r}")
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value == forbidden_name
        ):
            violations.append(f"{label}:{line} string literal {node.value!r}")

    return violations


@pytest.mark.unit
def test_the_write_repository_file_exists() -> None:
    """Non-vacuity: the walk below must reach a real file, or it proves nothing."""
    assert _WRITE_REPOSITORY_PATH.is_file()


@pytest.mark.unit
def test_the_write_repository_never_references_manual_correction() -> None:
    """R3: zero references to `ManualCorrection`, in any AST position."""
    source = _WRITE_REPOSITORY_PATH.read_text(encoding="utf-8")

    violations = _references_to(source, "annotation_write_repository.py", "ManualCorrection")

    assert not violations, "the annotation write path references ManualCorrection:\n" + "\n".join(
        violations
    )


@pytest.mark.unit
def test_the_write_repository_never_references_the_persisted_table_name_either() -> None:
    """Remediation (verify-report SUGGESTION 1): the class name `ManualCorrection`
    is the ORM model; the PERSISTED table is `manual_correction` (snake_case,
    `Base.metadata`'s `__tablename__`). The check above matches only the exact
    string `ManualCorrection`, so a raw-SQL literal such as
    `text("UPDATE manual_correction ...")` would slip past it undetected —
    no such code exists today, but nothing stopped it. This closes that gap
    with the same AST criterion, scanning for the snake_case table name.

    MUTATION CHECK: temporarily added a module-level string literal
    `"manual_correction"` to the write repository, ran this test, and
    observed::

        AssertionError: the annotation write path references the manual_correction table name:
        annotation_write_repository.py:47 string literal 'manual_correction'

    then reverted.
    """
    source = _WRITE_REPOSITORY_PATH.read_text(encoding="utf-8")

    violations = _references_to(source, "annotation_write_repository.py", "manual_correction")

    assert not violations, (
        "the annotation write path references the manual_correction table name:\n"
        + "\n".join(violations)
    )


@pytest.mark.unit
def test_a_manual_correction_import_would_be_caught() -> None:
    """Direct mutation check, run synthetically so it never has to touch
    production code to prove the detector itself works."""
    source = "from wheel_vocabulary.infrastructure.persistence.models import ManualCorrection\n"

    violations = _references_to(source, "synthetic.py", "ManualCorrection")

    assert violations
    assert any("ManualCorrection" in violation for violation in violations)


@pytest.mark.unit
def test_a_bare_name_reference_would_be_caught() -> None:
    """Not only imports: a bare name use is caught too."""
    source = "def f():\n    return ManualCorrection\n"

    violations = _references_to(source, "synthetic.py", "ManualCorrection")

    assert violations

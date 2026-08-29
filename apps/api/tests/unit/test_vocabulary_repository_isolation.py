"""Structural guard — the vocabulary read path never names `AnnotationProvenance` (D4/C6).

Design §D4: the query joins `occurrence` and `manual_correction` only.
`annotation_provenance` — the sole holder of `pos_confidence`/`lemma_confidence`
— is never joined, so confidence cannot reach this endpoint at all. This is
stronger than "nothing branches on it": the module structurally cannot see
the table.

This guard is NARROWER than `test_annotation_write_repository_isolation.py`
(here: one forbidden name, one mutation check) and DISTINCT from
`test_vocabulary_write_guard.py` (there: reads of `ManualCorrection` are
permitted, only writes are forbidden — AMB-3). This guard forbids ANY
reference to `AnnotationProvenance` at all, because this capability has no
business reading provenance either.

REQ-005-007 (D4/C6), AC-005-07.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_VOCABULARY_REPOSITORY_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "wheel_vocabulary"
    / "infrastructure"
    / "persistence"
    / "vocabulary_repository.py"
)


def _folded_string(node: ast.AST) -> str | None:
    """Constant-fold a chain of string-literal `+` concatenations.

    Mirrors `test_annotation_write_repository_isolation.py::_folded_string`:
    a split literal such as ``"Annotation" + "Provenance"`` must not evade
    detection by never spelling the forbidden name as one complete Constant.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _folded_string(node.left)
        right = _folded_string(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def _references_to(source: str, label: str, forbidden_name: str) -> list[str]:
    """Report every AST node in `source` that names `forbidden_name`.

    Checks identifiers, attributes, import aliases, imported modules, and
    string literals (including `+`-concatenated chains) — the same coverage
    as `test_annotation_write_repository_isolation.py::_references_to`,
    scoped to the vocabulary repository only.
    """
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
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if forbidden_name in node.value:
                violations.append(f"{label}:{line} string literal {node.value!r}")
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            folded = _folded_string(node)
            if folded is not None and forbidden_name in folded:
                violations.append(f"{label}:{line} concatenated string literal {folded!r}")

    return violations


@pytest.mark.unit
def test_the_vocabulary_repository_file_exists() -> None:
    """Non-vacuity: the guard below must reach a real file, or it proves nothing."""
    assert _VOCABULARY_REPOSITORY_PATH.is_file(), (
        f"vocabulary repository not found at {_VOCABULARY_REPOSITORY_PATH}"
    )


@pytest.mark.unit
def test_the_vocabulary_repository_never_references_annotation_provenance() -> None:
    """D4/C6: zero references to `AnnotationProvenance`, in any AST position.

    The vocabulary read path joins `occurrence` and `manual_correction` only.
    `annotation_provenance` is the sole holder of `pos_confidence`/
    `lemma_confidence`; if this module ever names it, confidence has a path
    into the aggregate, which §2.4 K1 forbids.

    MUTATION CHECK: temporarily added
    ``from wheel_vocabulary.infrastructure.persistence.models import AnnotationProvenance``
    to `vocabulary_repository.py`, ran this test, and observed::

        AssertionError: the vocabulary read path references AnnotationProvenance:
        vocabulary_repository.py:182 import alias 'AnnotationProvenance'

    then reverted.
    """
    source = _VOCABULARY_REPOSITORY_PATH.read_text(encoding="utf-8")

    violations = _references_to(source, "vocabulary_repository.py", "AnnotationProvenance")

    assert not violations, (
        "the vocabulary read path references AnnotationProvenance:\n" + "\n".join(violations)
    )


@pytest.mark.unit
def test_an_annotation_provenance_import_would_be_caught() -> None:
    """Direct mutation check, run synthetically so it never touches production code."""
    source = "from wheel_vocabulary.infrastructure.persistence.models import AnnotationProvenance\n"

    violations = _references_to(source, "synthetic.py", "AnnotationProvenance")

    assert violations
    assert any("AnnotationProvenance" in violation for violation in violations)

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

# The module's own docstring legitimately explains, in prose, that the query
# never joins `annotation_provenance` (design D4) — that is exactly what this
# guard exists to prove, so the docstring naming the table it forbids cannot
# itself be a violation. Pinned to the REVIEWED instance, mirroring
# `test_annotation_write_repository_isolation.py::_EXEMPT_MODULE_DOCSTRINGS`:
# a changed docstring falls out of the exemption and is caught again, rather
# than the exemption silently widening to whatever prose replaces it.
_EXEMPT_MODULE_DOCSTRINGS: dict[str, str] = {
    "vocabulary_repository.py": (
        "Vocabulary aggregation read path — design §D1, §D2, §D5; spec §2.1-§2.5.\n"
        "\n"
        "Groups occurrences by their precedence-resolved effective `(lemma, POS)`\n"
        "pair. Two legs run inside ONE `Session` — one snapshot, a correctness\n"
        "obligation design D1 states explicitly, not a style preference:\n"
        "\n"
        "* **leg A** (`_raw_group_counts`): `GROUP BY` over the RAW `Occurrence`\n"
        "  columns — an index-ordered scan served by `ix_occurrence_book_lemma_pos`,\n"
        "  no temp B-tree (design D2). Counts every occurrence under its raw pair,\n"
        "  corrected ones included.\n"
        "* **leg B** (`_corrected_deltas`): one `(raw pair, effective pair)` per\n"
        "  occurrence carrying at least one `ManualCorrection` row. Bounded by the\n"
        "  correction count, never by the occurrence count.\n"
        "\n"
        "`_merge` moves each occurrence leg B names out of its raw group and into\n"
        "its effective group by calling `domain.annotation.resolve_effective` — the\n"
        "ONE place spec §2.5's precedence rule runs (design D1). A SQL `COALESCE`\n"
        "over `manual_correction` would be a second, divergent definition of that\n"
        "rule and is explicitly forbidden (spec §2.2 E3). Work is\n"
        "O(groups + corrections), never O(occurrences).\n"
        "\n"
        "The query joins `occurrence` and `manual_correction` only — never\n"
        "`annotation_provenance` — so confidence cannot reach this module at all\n"
        "(design D4, spec §2.4 K1).\n"
        "\n"
        "REQ-005-001, REQ-005-002, REQ-005-003, REQ-005-005, REQ-005-009.\n"
    ),
}


def _docstring_constant_ids(tree: ast.AST, label: str) -> frozenset[int]:
    """Identify the one reviewed module docstring, by identity and content.

    Mirrors `test_annotation_write_repository_isolation.py::_docstring_constant_ids`.
    """
    identifiers: set[int] = set()
    expected = _EXEMPT_MODULE_DOCSTRINGS.get(label)
    first = tree.body[0] if isinstance(tree, ast.Module) and tree.body else None
    if (
        expected is not None
        and isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and first.value.value == expected
    ):
        identifiers.add(id(first.value))
    return frozenset(identifiers)


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
    string literals (including `+`-concatenated chains) — the same AST
    criteria as
    `test_annotation_write_repository_isolation.py::_references_to`, scoped
    to the vocabulary repository only. That module additionally has a
    SECOND call site checking the snake_case persisted table name
    (`test_the_write_repository_never_references_the_persisted_table_name_either`);
    `test_the_vocabulary_repository_never_references_the_persisted_table_name_either`
    below mirrors it, so the two guards now share the same coverage rather
    than only the same detection function.
    """
    tree = ast.parse(source, filename=label)
    docstrings = _docstring_constant_ids(tree, label)
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
            if id(node) not in docstrings and forbidden_name in node.value:
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


# --------------------------------------------------------------------------
# JD-W3-3 remediation (Judgment Day round 1) — the guard above matches only
# the CamelCase class name `AnnotationProvenance`. `text("SELECT
# pos_confidence FROM annotation_provenance")`, reflection, and
# `Base.metadata.tables["annotation_provenance"]` all name the PERSISTED
# table by its snake_case name and slipped past undetected. This adds the
# second call site `test_annotation_write_repository_isolation.py` already
# has for its own forbidden name (`_the_write_repository_never_references_
# the_persisted_table_name_either`), so this guard now carries the SAME
# coverage the earlier docstring only claimed it had.
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_the_vocabulary_repository_never_references_the_persisted_table_name_either() -> None:
    """D4/C6: zero references to `annotation_provenance` (the persisted
    snake_case table name), in any AST position — the class name
    `AnnotationProvenance` checked above is the ORM model; the PERSISTED
    table is `annotation_provenance` (`Base.metadata`'s `__tablename__`,
    `models.py`). A raw-SQL literal, a reflected `Table(...)` construction,
    or a `Base.metadata.tables[...]` subscript would name the table this way
    without ever spelling `AnnotationProvenance`, and the check above would
    report zero violations for any of them.

    MUTATION CHECK: temporarily added a module-level string literal
    `_DEBUG_TABLE_NAME = "annotation_provenance"` to `vocabulary_repository.py`,
    ran this test, and observed::

        ['vocabulary_repository.py:46 string literal 'annotation_provenance'']

    then reverted.
    """
    source = _VOCABULARY_REPOSITORY_PATH.read_text(encoding="utf-8")

    violations = _references_to(source, "vocabulary_repository.py", "annotation_provenance")

    assert not violations, (
        "the vocabulary read path references the annotation_provenance table name:\n"
        + "\n".join(violations)
    )


@pytest.mark.unit
def test_an_annotation_provenance_table_name_string_would_be_caught() -> None:
    """Direct mutation check, run synthetically: a raw-SQL string naming the
    persisted table is caught even with no `AnnotationProvenance` in sight."""
    source = (
        'from sqlalchemy import text\ntext("SELECT pos_confidence FROM annotation_provenance")\n'
    )

    violations = _references_to(source, "synthetic.py", "annotation_provenance")

    assert violations
    assert any("annotation_provenance" in violation for violation in violations)


@pytest.mark.unit
def test_a_metadata_tables_subscript_naming_the_table_would_be_caught() -> None:
    """`Base.metadata.tables["annotation_provenance"]` — the subscript key is
    the whole literal, caught by the same exact/substring criterion."""
    source = 'Base.metadata.tables["annotation_provenance"]\n'

    violations = _references_to(source, "synthetic.py", "annotation_provenance")

    assert violations
    assert any("annotation_provenance" in violation for violation in violations)


@pytest.mark.unit
def test_only_the_reviewed_module_docstring_stays_exempt_from_the_table_name_check() -> None:
    """The docstring exemption is an exact reviewed instance, not module
    prose generally — mirrors
    `test_annotation_write_repository_isolation.py::test_only_the_reviewed_module_docstring_stays_exempt`."""
    source = '"""' + _EXEMPT_MODULE_DOCSTRINGS["vocabulary_repository.py"] + '"""\n'

    assert _references_to(source, "vocabulary_repository.py", "annotation_provenance") == []


@pytest.mark.unit
def test_a_changed_reviewed_module_docstring_would_be_caught_for_the_table_name_too() -> None:
    """A docstring that does not match the pinned reviewed text gets no exemption."""
    source = '"""Non-reviewed text naming annotation_provenance."""\n'

    violations = _references_to(source, "vocabulary_repository.py", "annotation_provenance")

    assert violations
    assert any("annotation_provenance" in violation for violation in violations)

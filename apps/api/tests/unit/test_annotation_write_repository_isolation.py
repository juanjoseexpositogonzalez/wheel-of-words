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

# Nodes that own a docstring: the docstring is body[0], never any other
# Constant. C4 remediation: switching the string-literal check below from
# exact equality to a substring search (needed to catch a raw-SQL string
# that EMBEDS the forbidden name) means the module's own docstring — which
# legitimately explains "never reading, importing, or otherwise referencing
# ManualCorrection" in prose — would otherwise trip the guard on itself.
# Mirrors `test_no_lemma_naming.py::_docstring_constant_ids` exactly.
_DOCSTRING_OWNERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def _docstring_constant_ids(tree: ast.AST) -> frozenset[int]:
    """Identify the Constant nodes that are docstrings, by identity."""
    identifiers: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, _DOCSTRING_OWNERS):
            continue
        first = node.body[0] if node.body else None
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            identifiers.add(id(first.value))
    return frozenset(identifiers)


def _folded_string(node: ast.AST) -> str | None:
    """Constant-fold a chain of string-literal `+` concatenations.

    C4 remediation: `"manual" + "_correction"` (or a longer chain such as
    `"manual" + "_" + "correction"`, which Python's own parser
    left-associates as nested `BinOp`s) never appears as one complete
    `ast.Constant`, so a check that only ever inspects one `Constant` node at
    a time cannot see the concatenated result. This is deliberately NOT a
    general expression evaluator — it recognises exactly one shape (a `+`
    chain of string constants) and returns `None` for anything else,
    including a single non-string constant or a non-`Add` `BinOp`.
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

    C4 remediation: a string literal is flagged if it CONTAINS
    `forbidden_name` (a raw-SQL string built with `text("DELETE FROM
    manual_correction ...")` embeds the table name as a substring of a
    longer literal, never the literal on its own), not only if it equals it
    exactly. A `BinOp` `+` chain of string constants is separately folded
    and checked the same way, so a split literal such as
    `"Manual" + "Correction"` cannot evade detection by never spelling the
    forbidden name as one complete `ast.Constant`. A module/class/function
    docstring is exempt from the substring check (never from the exact-name
    identifier checks above it), so legitimate prose explaining what this
    guard forbids — including this very module's own docstring — stays
    green; that exemption is scoped exactly like `test_no_lemma_naming.py`'s.
    """
    tree = ast.parse(source, filename=label)
    docstrings = _docstring_constant_ids(tree)
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


# --------------------------------------------------------------------------
# C4 remediation — the detector only matched the exact string
# `"ManualCorrection"`/`"manual_correction"` as a WHOLE Constant value, never
# as a substring or a concatenation of split literals. Every scenario below
# was confirmed to slip past undetected before this fix; each is a genuine
# way the write path could reach the table without ever spelling either
# forbidden name as one complete literal.
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_a_raw_sql_string_embedding_the_table_name_would_be_caught() -> None:
    """`text("DELETE FROM manual_correction ...")` — the table name is a
    SUBSTRING of a longer SQL string, never the whole literal, so the
    original exact-equality check missed it entirely.

    RED before C4: `_references_to(source, "x.py", "manual_correction")`
    returned `[]` for this exact source.
    """
    source = 'from sqlalchemy import text\ntext("DELETE FROM manual_correction WHERE 1=1")\n'

    violations = _references_to(source, "synthetic.py", "manual_correction")

    assert violations
    assert any("manual_correction" in violation for violation in violations)


@pytest.mark.unit
def test_a_split_string_concatenation_of_the_table_name_would_be_caught() -> None:
    """`"manual" + "_correction"` — neither half is the forbidden name by
    itself, so the original check, which only ever inspected one `Constant`
    node at a time, never saw the concatenated result.

    RED before C4: `_references_to(source, "x.py", "manual_correction")`
    returned `[]` for this exact source.
    """
    source = 'x = "manual" + "_correction"\n'

    violations = _references_to(source, "synthetic.py", "manual_correction")

    assert violations
    assert any("manual_correction" in violation for violation in violations)


@pytest.mark.unit
def test_a_split_string_concatenation_of_the_class_name_would_be_caught() -> None:
    """`getattr(models, "Manual" + "Correction")` — same evasion, applied to
    the class-name forbidden string instead of the table name.

    RED before C4: `_references_to(source, "x.py", "ManualCorrection")`
    returned `[]` for this exact source.
    """
    source = 'getattr(models, "Manual" + "Correction")\n'

    violations = _references_to(source, "synthetic.py", "ManualCorrection")

    assert violations
    assert any("ManualCorrection" in violation for violation in violations)


@pytest.mark.unit
def test_a_three_way_split_concatenation_would_also_be_caught() -> None:
    """The fold must not be limited to exactly two operands — a `BinOp`
    chain (`(("manual" + "_") + "correction")`, how Python's own parser
    left-associates three literals joined by `+`) must fold all the way
    down."""
    source = 'x = "manual" + "_" + "correction"\n'

    violations = _references_to(source, "synthetic.py", "manual_correction")

    assert violations
    assert any("manual_correction" in violation for violation in violations)


@pytest.mark.unit
def test_a_metadata_tables_subscript_naming_the_table_would_be_caught() -> None:
    """`Base.metadata.tables["manual_correction"]` — already caught by exact
    string-literal equality before C4 (the subscript key IS the whole
    literal), but pinned here explicitly as a regression guard: this is one
    of the five reachability patterns the C4 ledger entry lists, and every
    one of them gets its own test, not only the ones that needed a code
    change to pass."""
    source = 'Base.metadata.tables["manual_correction"]\n'

    violations = _references_to(source, "synthetic.py", "manual_correction")

    assert violations
    assert any("manual_correction" in violation for violation in violations)


@pytest.mark.unit
def test_a_module_docstring_naming_the_forbidden_concept_stays_exempt() -> None:
    """The substring check above must not trip on legitimate PROSE
    explaining what this guard forbids — exactly the situation this
    module's own docstring is in ("without ever reading, importing, or
    otherwise referencing `ManualCorrection`"). Non-vacuity for this
    exemption: the production file's own docstring already exercises it
    (see `test_the_write_repository_never_references_manual_correction`
    passing despite mentioning the name), this test pins the mechanism
    directly against a synthetic source."""
    source = '"""This module never references ManualCorrection or manual_correction."""\n\nx = 1\n'

    assert _references_to(source, "synthetic.py", "ManualCorrection") == []
    assert _references_to(source, "synthetic.py", "manual_correction") == []


@pytest.mark.unit
def test_a_reflected_table_construction_naming_the_table_would_be_caught() -> None:
    """`Table("manual_correction", MetaData(), autoload_with=e)` — also
    already caught by exact string-literal equality before C4 (the first
    positional argument IS the whole literal); pinned here for the same
    regression-guard reason as the subscript case above."""
    source = 'Table("manual_correction", MetaData(), autoload_with=e)\n'

    violations = _references_to(source, "synthetic.py", "manual_correction")

    assert violations
    assert any("manual_correction" in violation for violation in violations)

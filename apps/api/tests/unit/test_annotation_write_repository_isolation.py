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

# E2(b-ii): this is the one reviewed false positive, and this guard has no
# downstream leg that re-catches module docstrings. Keep this exact instance
# pinned: a module docstring remains runtime reachable through ``__doc__``.
_EXEMPT_MODULE_DOCSTRINGS: dict[str, str] = {
    "annotation_write_repository.py": """The annotation write path — design §P3/P5, spec §2.5 R2/R3.

Writes automatic `pos`/`lemma` values and provenance **unconditionally**,
without ever reading, importing, or otherwise referencing `ManualCorrection`
(R2/R3). Splitting read from write into two separate modules is what makes
that guarantee checkable by a static, structural guard rather than only a
runtime assertion that could pass by chance:
`test_annotation_write_repository_isolation.py` asserts, via AST inspection,
that this module's source never names `ManualCorrection` — not in an import,
not as a bare name, not as an attribute, not as an exact or substring string
literal, and not as a `+`-concatenated chain of split literals. The write
path cannot corrupt a correction through any of THOSE construction patterns,
because it cannot see the correction table through them at all.

**Not an exhaustive proof (R3, Judgment Day round 2).** The guard above is
bounded to the string-construction patterns it explicitly recognises. An
f-string interpolation, `str.join`, or `%`-formatted string that assembled
`"manual_correction"` at runtime would currently evade it — "structurally
provable" overstated what a finite AST pattern-matcher can guarantee against
arbitrary string construction. Closing every such route is future work, not
a claim this module makes today.

**Atomicity (REQ-003-014, AC-003-15).** `write()` is one transaction: DELETE
the occurrences' existing provenance, UPDATE each occurrence's `pos`/`lemma`,
INSERT the new provenance rows, COMMIT. A failure at any point — including
after some `UPDATE` statements have already been issued but not yet committed
— leaves every row exactly as it was before the call: the session context
manager closes without committing, which rolls back the whole transaction.
Validation of the annotations themselves (length, order, UPOS membership,
confidence range) is the caller's responsibility (`AnnotateImport`, Phase 4)
and happens entirely before this method is ever called — this repository
trusts its input and only guarantees that a *write* either lands completely
or not at all.

REQ-003-011, REQ-003-014, AC-003-15.
""",
}


def _docstring_constant_ids(tree: ast.AST, label: str) -> frozenset[int]:
    """Identify the one reviewed module docstring, by identity and content."""
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
    forbidden name as one complete `ast.Constant`. ONLY a MODULE docstring is
    exempt from the substring check (never from the exact-name identifier
    checks above it, and never a class or function docstring — R3, Judgment
    Day round 2): the guarded production module's own module-level docstring
    legitimately explains what this guard forbids in prose and stays green,
    but a class or function docstring gets no such exemption, because it is
    an ordinary runtime-reachable string (`obj.__doc__`) that could otherwise
    be used to smuggle the forbidden name past this check undetected.
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


def _write_repository_modules(directory: Path) -> tuple[Path, ...]:
    """Walk the repository package and fail closed if its target disappears."""
    modules = tuple(directory.glob("*.py"))
    assert modules, "annotation write repository module walk reached zero modules"
    assert any(path.name == "annotation_write_repository.py" for path in modules), (
        "annotation write repository module walk is missing annotation_write_repository.py"
    )
    return modules


@pytest.mark.unit
def test_the_write_repository_file_exists() -> None:
    """Non-vacuity: the walk below must reach a real file, or it proves nothing."""
    modules = _write_repository_modules(_WRITE_REPOSITORY_PATH.parent)

    assert _WRITE_REPOSITORY_PATH in modules


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
def test_a_module_docstring_holding_the_raw_forbidden_sql_would_be_caught() -> None:
    """REQ-003H-002 / AC-003H-02 M1: a module docstring is runtime reachable.

    RED before E1/E4 hardening: ``_references_to`` returned ``[]`` because
    ``_DOCSTRING_OWNERS = (ast.Module,)`` exempted every module docstring.
    """
    source = '"""DELETE FROM manual_correction WHERE 1=1"""\n'

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
def test_a_function_docstring_holding_the_raw_forbidden_sql_would_be_caught() -> None:
    """R3 (Judgment Day round 2): the C4 docstring exemption was scoped to
    EVERY docstring owner (`ast.Module`, `ast.ClassDef`, `ast.FunctionDef`,
    `ast.AsyncFunctionDef`) — but a docstring is an ordinary runtime-reachable
    string, not inert prose by construction: `q.__doc__` is a normal
    attribute access that can be passed anywhere a string can, including
    `sqlalchemy.text(q.__doc__)`. A function whose docstring IS the raw
    forbidden SQL therefore reached `manual_correction` with zero violations
    reported, purely because a docstring happened to be its home.

    The control case directly below (`test_the_same_sql_outside_a_docstring_
    is_still_caught`) proves the miss is caused SPECIFICALLY by the docstring
    exemption, not by some other gap in the substring check: identical SQL,
    not in `body[0]`, is caught.

    RED (before the fix, verified 2026-08-25): `_references_to` returned
    `[]` for this exact source — the function's docstring, `body[0]` of the
    `FunctionDef`, was exempted by `_docstring_constant_ids` exactly like a
    module docstring, even though nothing about a function's own docstring
    makes it any less runtime-reachable than a module's.
    """
    source = 'def q():\n    """DELETE FROM manual_correction WHERE 1=1"""\n    return q.__doc__\n'

    violations = _references_to(source, "synthetic.py", "manual_correction")

    assert violations
    assert any("manual_correction" in violation for violation in violations)


@pytest.mark.unit
def test_the_same_sql_outside_a_docstring_is_still_caught() -> None:
    """Control case for the test above: identical SQL, placed as an ordinary
    string literal rather than as `body[0]` of the function, is caught both
    before and after the fix — proving the miss above was caused
    specifically by the docstring exemption, not some other gap."""
    source = 'def q():\n    return "DELETE FROM manual_correction WHERE 1=1"\n'

    violations = _references_to(source, "synthetic.py", "manual_correction")

    assert violations
    assert any("manual_correction" in violation for violation in violations)


@pytest.mark.unit
def test_a_class_docstring_holding_the_raw_forbidden_sql_would_also_be_caught() -> None:
    """Same evasion, applied to a class docstring instead of a function
    docstring — `_DOCSTRING_OWNERS` exempted `ast.ClassDef` too."""
    source = 'class Q:\n    """DELETE FROM manual_correction WHERE 1=1"""\n'

    violations = _references_to(source, "synthetic.py", "manual_correction")

    assert violations
    assert any("manual_correction" in violation for violation in violations)


@pytest.mark.unit
def test_only_the_reviewed_module_docstring_stays_exempt() -> None:
    """The exemption is an exact reviewed instance, not module prose generally."""
    source = '"""' + _EXEMPT_MODULE_DOCSTRINGS["annotation_write_repository.py"] + '"""\n'

    assert _references_to(source, "annotation_write_repository.py", "ManualCorrection") == []
    assert _references_to(source, "annotation_write_repository.py", "manual_correction") == []


@pytest.mark.unit
def test_a_changed_reviewed_module_docstring_would_be_caught() -> None:
    """REQ-003H-002 / AC-003H-02 E4: the exemption pins reviewed content."""
    source = '"""Non-reviewed text naming manual_correction."""\n'

    violations = _references_to(source, "annotation_write_repository.py", "manual_correction")

    assert violations
    assert any("manual_correction" in violation for violation in violations)


@pytest.mark.unit
def test_sql_in_function_class_docstrings_and_plain_literals_remains_in_scope() -> None:
    """REQ-003H-002 / AC-003H-02 M3: only the pinned module instance is exempt."""
    sources = (
        'def query():\n    """DELETE FROM manual_correction WHERE 1=1"""\n',
        'class Query:\n    """DELETE FROM manual_correction WHERE 1=1"""\n',
        'query = "DELETE FROM manual_correction WHERE 1=1"\n',
    )

    for source in sources:
        violations = _references_to(source, "synthetic.py", "manual_correction")
        assert violations
        assert any("manual_correction" in violation for violation in violations)


@pytest.mark.unit
def test_write_repository_module_walk_fails_closed_when_empty_or_incomplete(tmp_path: Path) -> None:
    """REQ-003H-002 / AC-003H-02 M2: the guard requires its target module."""
    with pytest.raises(AssertionError, match="reached zero modules"):
        _write_repository_modules(tmp_path)

    (tmp_path / "another_module.py").write_text("x = 1\n", encoding="utf-8")

    with pytest.raises(AssertionError, match="annotation_write_repository.py"):
        _write_repository_modules(tmp_path)


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

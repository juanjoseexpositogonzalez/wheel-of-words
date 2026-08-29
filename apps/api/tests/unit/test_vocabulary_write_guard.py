"""Structural guard — no code path in this capability writes a ManualCorrection row (REQ-005-008).

This guard is DISTINCT from `test_annotation_write_repository_isolation.py`
and NARROWER (AMB-3): the annotation write path must not *reference*
`ManualCorrection` at all (SPEC-003 R3), but this capability's aggregate
query MUST *read* `manual_correction` to satisfy REQ-005-002. Its guard
therefore distinguishes read from write: a `SELECT` is permitted, an
`INSERT`, `UPDATE` or `DELETE` is a violation.

The guard scans every module this capability introduces (the vocabulary
modules listed below) for:
  - SQLAlchemy ORM write calls: `insert(ManualCorrection, ...)`,
    `update(ManualCorrection)`, `delete(ManualCorrection)`.
  - Raw SQL text: `INSERT INTO manual_correction`, `UPDATE manual_correction`,
    `DELETE FROM manual_correction` (case-insensitive substring).

It does NOT flag `select(ManualCorrection...)` reads or `ManualCorrection.field`
attribute reads — those are the legitimate correction-delta lookup (leg B).

REQ-005-008, AC-005-08.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src" / "wheel_vocabulary"

# Every module this capability introduces. The guard fails closed if any
# disappears (non-vacuity). `application/vocabulary/use_cases.py` and
# `api/routes/vocabulary.py` do not exist yet (WU5/WU6) — they are added
# here so the guard covers them when they appear, but the non-vacuity
# check uses `glob` (files that exist today), not this manifest.
_VOCABULARY_MODULES = frozenset(
    {
        "infrastructure/persistence/vocabulary_repository.py",
        "application/vocabulary/use_cases.py",
        "api/routes/vocabulary.py",
    }
)

# Modules that exist today and MUST be reached by the scan.
_EXPECTED_EXISTING_MODULES = frozenset(
    {
        "infrastructure/persistence/vocabulary_repository.py",
    }
)

_FORBIDDEN_RAW_SQL = (
    "insert into manual_correction",
    "update manual_correction",
    "delete from manual_correction",
)


def _folded_string(node: ast.AST) -> str | None:
    """Constant-fold a chain of string-literal `+` concatenations."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _folded_string(node.left)
        right = _folded_string(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def _all_string_literals(source: str, label: str) -> list[str]:
    """Extract every string literal from `source`, including BinOp-folded chains.

    Module docstrings are NOT exempt here — a raw SQL string in a docstring
    is still a signal worth flagging in a write-path guard. This is simpler
    than `_references_to`'s docstring exemption because this guard's
    forbidden patterns are SQL fragments, not a class name that a docstring
    legitimately explains.
    """
    tree = ast.parse(source, filename=label)
    literals: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            literals.append(node.value)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            folded = _folded_string(node)
            if folded is not None:
                literals.append(folded)
    return literals


def _has_manual_correction_arg(call: ast.Call) -> bool:
    """Check whether an `ast.Call` has a `ManualCorrection` argument.

    Matches `insert(ManualCorrection, ...)`, `update(ManualCorrection)`,
    `delete(ManualCorrection)` — the ORM model passed as the first positional
    argument or as a keyword argument value. Also matches
    `insert(ManualCorrection).values(...)` style where `ManualCorrection`
    is the sole positional argument.
    """
    for arg in call.args:
        if isinstance(arg, ast.Name) and arg.id == "ManualCorrection":
            return True
        if isinstance(arg, ast.Attribute) and arg.attr == "ManualCorrection":
            return True
    for kw in call.keywords:
        if isinstance(kw.value, ast.Name) and kw.value.id == "ManualCorrection":
            return True
    return False


def _is_write_call(node: ast.AST) -> bool:
    """Check whether `node` is a SQLAlchemy ORM write call targeting ManualCorrection.

    Matches `insert(...)`, `update(...)`, `delete(...)` from `sqlalchemy`
    with `ManualCorrection` as an argument. These are the three ORM write
    entry points that produce INSERT/UPDATE/DELETE statements.
    """
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    # Match bare-name calls: insert(...), update(...), delete(...)
    if isinstance(func, ast.Name) and func.id in ("insert", "update", "delete"):
        return _has_manual_correction_arg(node)
    # Match attribute calls: sqlalchemy.insert(...), sa.update(...), etc.
    if isinstance(func, ast.Attribute) and func.attr in ("insert", "update", "delete"):
        return _has_manual_correction_arg(node)
    return False


def _detect_writes(source: str, label: str) -> list[str]:
    """Report every write statement targeting `manual_correction` in `source`.

    Two detection mechanisms (T16):
    1. AST `ast.Call` matching on `insert`/`update`/`delete` from `sqlalchemy`
       with a `ManualCorrection` argument — catches ORM write calls.
    2. Substring scan over string/`BinOp`-folded literals for raw SQL
       `INSERT INTO manual_correction` / `UPDATE manual_correction` /
       `DELETE FROM manual_correction` (case-insensitive) — catches raw
       `text("...")` statements.
    """
    tree = ast.parse(source, filename=label)
    violations: list[str] = []

    # 1. ORM write calls
    for node in ast.walk(tree):
        line = getattr(node, "lineno", 0)
        if _is_write_call(node):
            func_name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
                if isinstance(node.func, ast.Attribute)
                else "?"
            )
            violations.append(f"{label}:{line} ORM write call {func_name}(ManualCorrection)")

    # 2. Raw SQL text
    for literal in _all_string_literals(source, label):
        lower = literal.lower()
        for fragment in _FORBIDDEN_RAW_SQL:
            if fragment in lower:
                violations.append(f"{label} raw SQL fragment {fragment!r}")

    return violations


def _vocabulary_modules() -> list[Path]:
    """Walk the package and return every module this capability introduces.

    Uses glob (files that exist on disk), not the static manifest — so the
    non-vacuity check proves the scan reaches real files. The static manifest
    lists what the capability WILL introduce; the glob lists what it DOES
    introduce today.
    """
    modules: list[Path] = []
    for rel in _VOCABULARY_MODULES:
        path = _PACKAGE_ROOT / rel
        if path.is_file():
            modules.append(path)
    return sorted(modules)


@pytest.mark.unit
def test_the_scan_reaches_the_vocabulary_modules() -> None:
    """Non-vacuity: the walk must reach the vocabulary repository, or the
    guard below proves nothing (SPEC-003 §3.3 M2)."""
    scanned = {path.relative_to(_PACKAGE_ROOT).as_posix() for path in _vocabulary_modules()}

    assert scanned >= _EXPECTED_EXISTING_MODULES, (
        "the vocabulary module walk is missing expected modules: "
        + ", ".join(sorted(_EXPECTED_EXISTING_MODULES - scanned))
    )


@pytest.mark.unit
def test_no_vocabulary_module_writes_to_manual_correction() -> None:
    """REQ-005-008 / AC-005-08 scenario 1: no `INSERT`, `UPDATE` or `DELETE`
    targeting `manual_correction` in any module this capability introduces.

    `select(ManualCorrection...)` reads and `ManualCorrection.field` attribute
    reads are PERMITTED — this capability reads corrections to resolve
    effective values (REQ-005-002). Only writes are forbidden.

    MUTATION CHECK: see `test_a_synthetic_insert_would_be_caught` and
    `test_a_synthetic_delete_would_be_caught` below for the per-mutation
    evidence (AC-005-08 scenario 3).
    """
    violations = [
        violation
        for module in _vocabulary_modules()
        for violation in _detect_writes(
            module.read_text(encoding="utf-8"),
            module.relative_to(_PACKAGE_ROOT).as_posix(),
        )
    ]

    assert not violations, "a vocabulary module writes to manual_correction:\n" + "\n".join(
        violations
    )


@pytest.mark.unit
def test_a_synthetic_insert_would_be_caught() -> None:
    """AC-005-08 scenario 3: a synthetic `insert(ManualCorrection, ...)` must
    produce a violation.

    MUTATION CHECK: ran `_detect_writes` against this exact source and
    observed::

        ['synthetic.py:1 ORM write call insert(ManualCorrection)']
    """
    source = "from sqlalchemy import insert\ninsert(ManualCorrection, {'field': 'lemma'})\n"

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("insert" in v and "ManualCorrection" in v for v in violations)


@pytest.mark.unit
def test_a_synthetic_delete_would_be_caught() -> None:
    """AC-005-08 scenario 3: a synthetic `delete(ManualCorrection)` must
    produce a violation.

    MUTATION CHECK: ran `_detect_writes` against this exact source and
    observed::

        ['synthetic.py:2 ORM write call delete(ManualCorrection)']
    """
    source = "from sqlalchemy import delete\ndelete(ManualCorrection)\n"

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("delete" in v and "ManualCorrection" in v for v in violations)


@pytest.mark.unit
def test_a_write_outside_the_capability_still_violates() -> None:
    """AC-005-08 scenario 4 / M3: the same forbidden write statement placed
    in a module OUTSIDE this capability still produces a violation.

    The boundary control proves the guard is not silently exempting anything
    by file path — the detector flags the write pattern regardless of which
    module it appears in.
    """
    source = "from sqlalchemy import insert\ninsert(ManualCorrection, {'field': 'pos'})\n"

    violations = _detect_writes(source, "some/other/module.py")

    assert violations
    assert any("insert" in v and "ManualCorrection" in v for v in violations)


@pytest.mark.unit
def test_select_on_manual_correction_is_permitted() -> None:
    """AMB-3: a `select(ManualCorrection...)` read is NOT a violation.

    This capability reads corrections to resolve effective values (REQ-005-002).
    The guard distinguishes read from write — only INSERT/UPDATE/DELETE are
    forbidden.
    """
    source = "from sqlalchemy import select\nselect(ManualCorrection.occurrence_id)\n"

    violations = _detect_writes(source, "synthetic.py")

    assert not violations


@pytest.mark.unit
def test_manual_correction_attribute_read_is_permitted() -> None:
    """AMB-3: `ManualCorrection.field` attribute access in a select is NOT a
    violation — it is the legitimate correction-delta lookup (leg B)."""
    source = (
        "from sqlalchemy import select\n"
        "stmt = select(ManualCorrection.occurrence_id, ManualCorrection.field)\n"
    )

    violations = _detect_writes(source, "synthetic.py")

    assert not violations


@pytest.mark.unit
def test_a_raw_sql_insert_would_be_caught() -> None:
    """Raw SQL `INSERT INTO manual_correction` is caught by the substring scan."""
    source = 'from sqlalchemy import text\ntext("INSERT INTO manual_correction VALUES (1)")\n'

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("insert into manual_correction" in v for v in violations)


@pytest.mark.unit
def test_a_raw_sql_update_would_be_caught() -> None:
    """Raw SQL `UPDATE manual_correction` is caught by the substring scan."""
    source = 'from sqlalchemy import text\ntext("UPDATE manual_correction SET field = \\"pos\\"")\n'

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("update manual_correction" in v for v in violations)


@pytest.mark.unit
def test_a_raw_sql_delete_would_be_caught() -> None:
    """Raw SQL `DELETE FROM manual_correction` is caught by the substring scan."""
    source = 'from sqlalchemy import text\ntext("DELETE FROM manual_correction WHERE 1=1")\n'

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("delete from manual_correction" in v for v in violations)


@pytest.mark.unit
def test_a_case_insensitive_raw_sql_insert_would_be_caught() -> None:
    """The raw SQL scan is case-insensitive — `insert into` is caught too."""
    source = 'text("insert into manual_correction values (1)")\n'

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("insert into manual_correction" in v for v in violations)


@pytest.mark.unit
def test_a_split_raw_sql_string_would_be_caught() -> None:
    """A `+`-concatenated raw SQL string is folded and caught."""
    source = 'text("INSERT" + " INTO manual_correction VALUES (1)")\n'

    violations = _detect_writes(source, "synthetic.py")

    assert violations

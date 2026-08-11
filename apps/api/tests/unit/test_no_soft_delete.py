"""Structural guard — hook H8: no soft delete anywhere (T217).

`REQ-002-011` forbids a soft delete outright, not merely leaves it unshipped:
Art. IV.8 requires the application to actually be able to delete a user's
imported data, and a `deleted_at`/`is_deleted`/tombstone flag would retain it
behind a filter instead. This guard scans the persisted schema — the
`0002_book_occurrence` migration and the mapped `Book`/`Occurrence` models —
for any of the three markers.

AST-based, like the AC-002-10 naming guards (`test_no_lemma_naming.py`,
`test_domain_isolation.py`): identifiers and non-docstring string literals are
checked, `#` comments and docstrings are exempt by construction. Without the
exemption this module's own docstring ("no `deleted_at` ... column anywhere")
would trip the guard it explains — the exact pathology those two guards were
already converted away from.

MUTATION CHECK — this is an ABSENCE assertion. It passes on the first run over
correct code, which proves nothing on its own. Verified by adding a real
`deleted_at` column to `0002_book_occurrence.py`, confirming an
`AssertionError` naming the revision file and the matched token, then
reverting.

REQ-002-011 / hook H8.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4]
_MIGRATION = _REPO_ROOT / "apps" / "api" / "migrations" / "versions" / "0002_book_occurrence.py"
_MODELS = (
    _REPO_ROOT
    / "apps"
    / "api"
    / "src"
    / "wheel_vocabulary"
    / "infrastructure"
    / "persistence"
    / "models.py"
)
_FORBIDDEN = re.compile(r"deleted_at|is_deleted|tombstone", re.IGNORECASE)

_DOCSTRING_OWNERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def _docstring_constant_ids(tree: ast.AST) -> frozenset[int]:
    """Identify the Constant nodes that are docstrings, by identity.

    Mirrors `test_no_lemma_naming.py::_docstring_constant_ids` exactly: a
    docstring is recognised by *position* (first statement of a module, class
    or function body), never by its text.
    """
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


def _identifier_names(node: ast.AST) -> list[str]:
    """Every identifier a node introduces — column and field names live here."""
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Attribute):
        return [node.attr]
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return [node.target.id]
    if isinstance(node, ast.arg):
        return [node.arg]
    if isinstance(node, ast.keyword) and node.arg is not None:
        return [node.arg]
    return []


def _soft_delete_violations(source: str, label: str) -> list[str]:
    """Report a forbidden marker in identifiers and non-docstring literals."""
    tree = ast.parse(source, filename=label)
    docstrings = _docstring_constant_ids(tree)
    violations: list[str] = []

    for node in ast.walk(tree):
        line = getattr(node, "lineno", 0)
        for name in _identifier_names(node):
            if _FORBIDDEN.search(name):
                violations.append(f"{label}:{line} identifier {name!r}")
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
            and _FORBIDDEN.search(node.value)
        ):
            violations.append(f"{label}:{line} string literal {node.value!r}")

    return violations


@pytest.mark.unit
def test_no_soft_delete_marker_in_the_migration_or_the_mapped_models() -> None:
    """H8: no `deleted_at` / `is_deleted` / tombstone in the persisted schema."""
    violations = [
        violation
        for path in (_MIGRATION, _MODELS)
        for violation in _soft_delete_violations(
            path.read_text(encoding="utf-8"), str(path.relative_to(_REPO_ROOT))
        )
    ]

    assert not violations, "soft-delete marker leaked into the persisted schema:\n" + "\n".join(
        violations
    )


@pytest.mark.unit
def test_docstrings_may_document_the_prohibition_they_enforce() -> None:
    """The exemption exists so this module's own docstring can say the words."""
    source = '''
"""No deleted_at, no is_deleted, no tombstone column."""


class Book:
    """Neither this class nor its migration ever carries a tombstone."""

    id: int
'''

    assert _soft_delete_violations(source, "synthetic.py") == []


@pytest.mark.unit
def test_a_column_identifier_named_deleted_at_still_fails() -> None:
    """The exemption is scoped to docstrings; it is not a hole for real columns."""
    source = '''
"""No soft delete here."""


class Occurrence:
    deleted_at: str
'''

    violations = _soft_delete_violations(source, "synthetic.py")

    assert violations
    assert any("deleted_at" in violation for violation in violations)

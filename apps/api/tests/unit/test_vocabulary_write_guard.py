"""Structural guard — no code path in this capability writes a ManualCorrection row (REQ-005-008).

This guard is DISTINCT from `test_annotation_write_repository_isolation.py`
and NARROWER (AMB-3): the annotation write path must not *reference*
`ManualCorrection` at all (SPEC-003 R3), but this capability's aggregate
query MUST *read* `manual_correction` to satisfy REQ-005-002. Its guard
therefore distinguishes read from write: a `SELECT` is permitted, an
`INSERT`, `UPDATE` or `DELETE` is a violation.

It does NOT flag `select(ManualCorrection...)` reads or `ManualCorrection.field`
attribute reads — those are the legitimate correction-delta lookup (leg B).

**Discovery (JD-W3-1, Judgment Day round 1).** The scan enumerates the
ENTIRE `wheel_vocabulary` package via `Path.rglob("*.py")`, plus every file
under `migrations/versions/`, not a fixed per-module manifest. Before this
fix, `_vocabulary_modules()` iterated a hardcoded `_VOCABULARY_MODULES`
list and returned only the subset that existed on disk — `scanned` was
therefore, BY CONSTRUCTION, always a subset of that list, so the
non-vacuity assertion `scanned >= _EXPECTED_EXISTING_MODULES` could never
fail on a module the manifest never named. A module this capability
introduces after this file was written (`application/vocabulary/ports.py`,
T26; `api/dtos/vocabulary.py`, T30; a vocabulary-specific addition to the
shared `api/dependencies.py`, T33) would never have been scanned, and
`migrations/versions/0004_vocabulary_group_index.py` was unreachable
outright, because the old walk never left `_PACKAGE_ROOT`.

**Scope, corrected during this same round.** An earlier draft of this fix
walked the ENTIRE package (`rglob("*.py")` with no filter), reasoning that
SPEC-003 §3.4 W1 permits broadening but not narrowing. That draft's own
non-vacuity/mutation-check run immediately surfaced a real false positive:
`infrastructure/persistence/book_repository.py:144`'s
`delete(ManualCorrection).where(...)` — a genuine, INTENTIONAL write. It is
`DeleteImport`'s cascade cleanup (SPEC-002/003, not this capability): when
a book is deleted, its `manual_correction` rows must go with it, or a later
import that reuses the freed `Occurrence.id` inherits a ghost correction it
never made (`book_repository.py:129-136`). REQ-005-008 forbids a write by
"a module THIS CAPABILITY introduces" — `book_repository.py` belongs to
`002-text-import`, not `005-vocabulary-browser`, so scanning it here was
never correct scope, and "broadening never narrows" is not the same claim
as "broadening never produces a false positive": SPEC-004 (the correction
WRITE capability, out of scope for this repository today) will introduce
its own legitimate `manual_correction` writer, and an unscoped whole-package
walk would flag that one too the day it lands.

The corrected scope: every `.py` path under `_PACKAGE_ROOT` whose path
contains the case-insensitive token `"vocabulary"` — which covers every
file T8, T12, T26, T27, T30, and T38 create by this capability's own
established naming convention with NO manifest entry required — **plus**
the two shared, multi-capability wiring files `api/dependencies.py` and
`api/main.py`. Those two are named explicitly, not pattern-matched, because
ADR-0002 routes every capability's dependency wiring and route registration
through them without renaming either file, and T33/T40 both add
vocabulary-specific code to them; unlike the `_VOCABULARY_MODULES` manifest
this replaces, they are already in scope TODAY, before T33/T40 ship, so no
future commit needs to add them. `book_repository.py`,
`annotation_write_repository.py`, and every other SPEC-002/003 module stay
correctly out of scope, confirmed by
`test_the_scan_does_not_reach_unrelated_capability_modules` below.

**Migrations decision.** REQ-005-008's text is "No module this capability
introduces SHALL insert, update, or delete a `manual_correction` row" —
`migrations/versions/0004_vocabulary_group_index.py` (T2) IS such a module,
literally, even though its `upgrade()`/`downgrade()` only touch an index on
`occurrence`. Migrations ARE in scope. Rather than tracking a second
manifest of "which migration belongs to which capability" — which would
reintroduce the exact hardcoded-list defect this remediation exists to
fix — every file under `migrations/versions/` is scanned unconditionally.
This is broader than strictly required (only one of today's four
migrations was introduced by this capability), which SPEC-003 §3.4 W1
permits; a `CREATE TABLE`/`op.create_index` migration for an unrelated
capability contains no `insert into manual_correction`-shaped substring or
`ManualCorrection`-referencing ORM call, so scanning them produces no false
positive (confirmed by the non-vacuity/mutation-check suite below).

**Detection (JD-W3-2, Judgment Day round 1).** The write detector resolves
`sqlalchemy` import aliases (`from sqlalchemy import delete as sa_delete`)
and verifies call origin, so a bare `.insert`/`.update`/`.delete` attribute
call is matched ONLY when it is traceable to a `sqlalchemy` import, a
`ManualCorrection.__table__` chain, or a `.query(ManualCorrection)` chain —
never by method name alone (`cache.update(ManualCorrection)` is not a
database write and is no longer flagged). Covered idioms, beyond the three
free `insert`/`update`/`delete` functions:

  - `session.add(ManualCorrection(...))` / `session.add_all([...])`,
    including via a local variable directly bound to a `ManualCorrection(...)`
    construction earlier in the same module.
  - `session.delete(...)`, same binding-tracking rule as `add`.
  - `session.query(ManualCorrection).delete()` / `.update({...})`.
  - `session.bulk_insert_mappings(ManualCorrection, ...)` /
    `.bulk_update_mappings(ManualCorrection, ...)`.
  - `ManualCorrection.__table__.insert()` / `.update()` / `.delete()`.

**Residual gaps (SPEC-003 §3.6 G1/G3) — not closed by this detector, and
each pinned by its own accepted-behaviour test below:**

  - An attribute-assignment mutation of an already-fetched row
    (`row.field = "x"`) followed by `session.commit()` names no forbidden
    identifier at the mutation site; this AST-only detector performs no
    type inference to learn that `row` is a `ManualCorrection`.
  - `session.delete(row)` where `row` was fetched by a query, or is a
    second alias of a tracked name, rather than DIRECTLY bound to a
    `ManualCorrection(...)` construction — the binding tracker follows one
    assignment hop, not an arbitrary chain.
  - A `sqlalchemy` import name reassigned after import
    (`insert = lambda *a: None`) is still flagged: the alias map is static,
    not flow-sensitive to later rebinding, so this is a documented
    over-approximation (a possible false positive), never an
    under-approximation (a missed real write).
  - The raw-SQL substring scan is unchanged by this round — `REPLACE INTO`,
    `TRUNCATE`, and whitespace/quoting variants remain out of scope
    (maintainer-deferred; unaffected by the ORM-idiom fix above, since
    none of the new idioms construct SQL text).

REQ-005-008, AC-005-08.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src" / "wheel_vocabulary"
_MIGRATIONS_ROOT = Path(__file__).resolve().parents[2] / "migrations" / "versions"

# Non-vacuity anchors (SPEC-003 §3.3 M2): files the scan MUST reach on the
# real filesystem, or the guard below proves nothing. NOT a manifest the
# scan enumerates FROM (that was the JD-W3-1 defect) — `_scanned_modules`
# walks the filesystem directly; these sets are only the checkpoints the
# non-vacuity test below asserts against.
_EXPECTED_PACKAGE_MODULES = frozenset(
    {
        "infrastructure/persistence/vocabulary_repository.py",
        "api/dependencies.py",
    }
)
_EXPECTED_MIGRATIONS = frozenset(
    {
        "0004_vocabulary_group_index.py",
    }
)

# The only two files in scope that do NOT carry "vocabulary" in their path —
# see the module docstring's "Scope, corrected during this same round"
# section for why these two, and only these two, are named explicitly.
_SHARED_WIRING_FILES = frozenset({"api/dependencies.py", "api/main.py"})

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


_SQLALCHEMY_WRITE_FUNCS = frozenset({"insert", "update", "delete"})
_SESSION_ADD_METHODS = frozenset({"add", "add_all"})
_SESSION_MAPPING_METHODS = frozenset({"bulk_insert_mappings", "bulk_update_mappings"})
_TABLE_WRITE_METHODS = frozenset({"insert", "update", "delete"})


def _collect_sqlalchemy_call_aliases(tree: ast.AST) -> dict[str, str]:
    """Map each locally-bound name to the `sqlalchemy` function it was
    imported as, resolving `as` aliases.

    `from sqlalchemy import delete as sa_delete` maps `"sa_delete" ->
    "delete"`. Only `insert`/`update`/`delete` are tracked — the three ORM
    Core write entry points this guard checks for by name. This is what
    lets `_core_write_call` verify origin instead of matching a bare `Name`
    with no idea where it came from (JD-W3-2).
    """
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "sqlalchemy":
            for alias in node.names:
                if alias.name in _SQLALCHEMY_WRITE_FUNCS:
                    aliases[alias.asname or alias.name] = alias.name
    return aliases


def _collect_sqlalchemy_module_aliases(tree: ast.AST) -> frozenset[str]:
    """Local names bound to the `sqlalchemy` module itself via `import
    sqlalchemy` / `import sqlalchemy as sa`, so `sa.insert(...)` resolves to
    the same origin as a bare `insert(...)`."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "sqlalchemy":
                    names.add(alias.asname or alias.name)
    return frozenset(names)


def _constructs_manual_correction(node: ast.AST) -> bool:
    """True if `node` is a call constructing `ManualCorrection(...)` directly."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name) and func.id == "ManualCorrection":
        return True
    return isinstance(func, ast.Attribute) and func.attr == "ManualCorrection"


def _names_manual_correction(node: ast.AST) -> bool:
    """True if `node` is a bare reference to `ManualCorrection` (a `Name` or
    an attribute access ending in it), never a call."""
    if isinstance(node, ast.Name):
        return node.id == "ManualCorrection"
    return isinstance(node, ast.Attribute) and node.attr == "ManualCorrection"


def _manual_correction_bindings(tree: ast.AST) -> frozenset[str]:
    """Names directly bound to a `ManualCorrection(...)` construction
    anywhere in the module (module-scope, flow-insensitive), so
    `correction = ManualCorrection(...)` followed by
    `session.add(correction)` on a LATER, non-adjacent line is recognised
    (JD-W3-2) — exactly the shape `test_vocabulary_read_scenario.py:128-134`
    uses.

    Deliberately simple: only a DIRECT `Name = ManualCorrection(...)`
    binding is tracked, one assignment hop. A binding threaded through a
    second alias, a function argument, or a query result is NOT tracked —
    see the module docstring's "Residual gaps" section and
    `test_a_delete_of_an_opaquely_fetched_row_is_a_known_residual_gap`.
    """
    bindings: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and _constructs_manual_correction(node.value):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    bindings.add(target.id)
    return frozenset(bindings)


def _references_manual_correction(node: ast.AST, bindings: frozenset[str]) -> bool:
    """True if `node` constructs, names, or (via a tracked local binding)
    resolves to `ManualCorrection`."""
    if _constructs_manual_correction(node) or _names_manual_correction(node):
        return True
    return isinstance(node, ast.Name) and node.id in bindings


def _core_write_call(
    node: ast.Call, call_aliases: dict[str, str], module_aliases: frozenset[str]
) -> str | None:
    """`insert(ManualCorrection, ...)` / `update(...)` / `delete(...)`,
    resolved through import aliases, or `sqlalchemy.insert(...)` /
    `sa.update(...)` via a tracked module alias.

    Origin-checked (JD-W3-2): a bare `.update()`/`.insert()`/`.delete()`
    attribute call is NOT matched here unless its base is a name the module
    actually imported `sqlalchemy` (or `sqlalchemy as ...`) under — so
    `cache.update(ManualCorrection)` is never mistaken for a database write.
    """
    func = node.func
    if isinstance(func, ast.Name) and func.id in call_aliases:
        canonical = call_aliases[func.id]
        if _has_manual_correction_arg(node):
            return canonical
    if (
        isinstance(func, ast.Attribute)
        and isinstance(func.value, ast.Name)
        and func.value.id in module_aliases
        and func.attr in _SQLALCHEMY_WRITE_FUNCS
        and _has_manual_correction_arg(node)
    ):
        return func.attr
    return None


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


def _instance_add_call(node: ast.Call, bindings: frozenset[str]) -> str | None:
    """`session.add(ManualCorrection(...))` / `session.add_all([...])`,
    including via a locally bound variable (JD-W3-2)."""
    func = node.func
    if not isinstance(func, ast.Attribute) or func.attr not in _SESSION_ADD_METHODS:
        return None
    if not node.args:
        return None
    arg = node.args[0]
    if func.attr == "add_all":
        if isinstance(arg, ast.List) and any(
            _references_manual_correction(element, bindings) for element in arg.elts
        ):
            return func.attr
        return None
    if _references_manual_correction(arg, bindings):
        return func.attr
    return None


def _instance_delete_call(node: ast.Call, bindings: frozenset[str]) -> str | None:
    """`session.delete(row)` where `row` constructs, names, or is bound to
    `ManualCorrection` (JD-W3-2). Requires an argument, which is what tells
    this apart from the zero-arg `.query(ManualCorrection).delete()` form
    `_query_write_call` handles instead."""
    func = node.func
    if not isinstance(func, ast.Attribute) or func.attr != "delete" or not node.args:
        return None
    if _references_manual_correction(node.args[0], bindings):
        return "delete"
    return None


def _query_write_call(node: ast.Call) -> str | None:
    """`<session>.query(ManualCorrection).delete()` / `.update({...})` —
    the legacy `Query` API's bulk write methods (JD-W3-2)."""
    func = node.func
    if not isinstance(func, ast.Attribute) or func.attr not in ("delete", "update"):
        return None
    base = func.value
    if not isinstance(base, ast.Call) or not isinstance(base.func, ast.Attribute):
        return None
    if base.func.attr != "query" or not base.args:
        return None
    if _names_manual_correction(base.args[0]):
        return func.attr
    return None


def _bulk_mapping_call(node: ast.Call) -> str | None:
    """`session.bulk_insert_mappings(ManualCorrection, rows)` /
    `.bulk_update_mappings(ManualCorrection, rows)` (JD-W3-2)."""
    func = node.func
    if not isinstance(func, ast.Attribute) or func.attr not in _SESSION_MAPPING_METHODS:
        return None
    if not node.args or not _names_manual_correction(node.args[0]):
        return None
    return func.attr


def _table_write_call(node: ast.Call) -> str | None:
    """`ManualCorrection.__table__.insert()` / `.update()` / `.delete()` —
    a Core write issued directly against the mapped table (JD-W3-2)."""
    func = node.func
    if not isinstance(func, ast.Attribute) or func.attr not in _TABLE_WRITE_METHODS:
        return None
    table_attr = func.value
    if not isinstance(table_attr, ast.Attribute) or table_attr.attr != "__table__":
        return None
    if _names_manual_correction(table_attr.value):
        return func.attr
    return None


def _classify_write_call(
    node: ast.Call,
    call_aliases: dict[str, str],
    module_aliases: frozenset[str],
    bindings: frozenset[str],
) -> str | None:
    """Dispatch `node` through every known write idiom in turn, returning a
    human-readable description of the first match, or `None`."""
    canonical = _core_write_call(node, call_aliases, module_aliases)
    if canonical is not None:
        return f"ORM write call {canonical}(ManualCorrection)"
    method = _instance_add_call(node, bindings)
    if method is not None:
        return f"ORM instance write session.{method}(ManualCorrection)"
    if _instance_delete_call(node, bindings) is not None:
        return "ORM instance write session.delete(ManualCorrection)"
    query_method = _query_write_call(node)
    if query_method is not None:
        return f"ORM Query write .query(ManualCorrection).{query_method}(...)"
    mapping_method = _bulk_mapping_call(node)
    if mapping_method is not None:
        return f"ORM bulk write {mapping_method}(ManualCorrection, ...)"
    table_method = _table_write_call(node)
    if table_method is not None:
        return f"ORM Core write ManualCorrection.__table__.{table_method}()"
    return None


def _detect_writes(source: str, label: str) -> list[str]:
    """Report every write statement targeting `manual_correction` in `source`.

    Two detection mechanisms:
    1. AST `ast.Call` matching against every write idiom `_classify_write_call`
       dispatches through — origin-checked free `insert`/`update`/`delete`
       functions (with alias resolution), `session.add`/`add_all`/`delete`
       (with local-binding tracking), `Query.delete`/`Query.update`,
       `bulk_insert_mappings`/`bulk_update_mappings`, and
       `ManualCorrection.__table__` writes. See the module docstring's
       "Detection" section for the full list and its "Residual gaps"
       section for what remains uncovered.
    2. Substring scan over string/`BinOp`-folded literals for raw SQL
       `INSERT INTO manual_correction` / `UPDATE manual_correction` /
       `DELETE FROM manual_correction` (case-insensitive) — catches raw
       `text("...")` statements.
    """
    tree = ast.parse(source, filename=label)
    call_aliases = _collect_sqlalchemy_call_aliases(tree)
    module_aliases = _collect_sqlalchemy_module_aliases(tree)
    bindings = _manual_correction_bindings(tree)
    violations: list[str] = []

    # 1. ORM write calls
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        description = _classify_write_call(node, call_aliases, module_aliases, bindings)
        if description is not None:
            line = getattr(node, "lineno", 0)
            violations.append(f"{label}:{line} {description}")

    # 2. Raw SQL text
    for literal in _all_string_literals(source, label):
        lower = literal.lower()
        for fragment in _FORBIDDEN_RAW_SQL:
            if fragment in lower:
                violations.append(f"{label} raw SQL fragment {fragment!r}")

    return violations


def _scanned_modules(
    package_root: Path = _PACKAGE_ROOT, migrations_root: Path = _MIGRATIONS_ROOT
) -> list[tuple[Path, str]]:
    """Enumerate every module this write guard scans: `(path, label)` pairs
    for every "vocabulary"-named module under the package, the two shared
    wiring files, and every Alembic migration.

    See the module docstring's "Discovery", "Scope, corrected during this
    same round", and "Migrations decision" sections for the reasoning.
    `package_root`/`migrations_root` are overridable so the non-vacuity
    tests below can exercise an empty, partial, or unrelated tree without
    touching the real one.
    """
    modules = [
        (path, label)
        for path in sorted(package_root.rglob("*.py"))
        for label in (path.relative_to(package_root).as_posix(),)
        if "vocabulary" in label.lower() or label in _SHARED_WIRING_FILES
    ]
    modules += [
        (path, f"migrations/versions/{path.name}") for path in sorted(migrations_root.glob("*.py"))
    ]
    return modules


@pytest.mark.unit
def test_the_scan_reaches_the_vocabulary_modules() -> None:
    """Non-vacuity: the walk must reach the vocabulary repository and the
    vocabulary migration, or the guard below proves nothing (SPEC-003 §3.3 M2)."""
    scanned = {label for _, label in _scanned_modules()}

    missing_package = _EXPECTED_PACKAGE_MODULES - scanned
    missing_migrations = {f"migrations/versions/{name}" for name in _EXPECTED_MIGRATIONS} - scanned
    missing = missing_package | missing_migrations

    assert not missing, "the vocabulary module walk is missing expected modules: " + ", ".join(
        sorted(missing)
    )


@pytest.mark.unit
def test_the_scan_fails_closed_when_the_roots_are_empty(tmp_path: Path) -> None:
    """SPEC-003 §3.3 M2: an empty package root and an empty migrations root
    must fail the non-vacuity assertion above — proving it CAN fail, not
    only that it happens to pass today."""
    empty_package = tmp_path / "empty_package"
    empty_package.mkdir()
    empty_migrations = tmp_path / "empty_migrations"
    empty_migrations.mkdir()

    scanned = {label for _, label in _scanned_modules(empty_package, empty_migrations)}

    assert not (scanned >= _EXPECTED_PACKAGE_MODULES)
    assert not any(label.startswith("migrations/versions/") for label in scanned)


@pytest.mark.unit
def test_the_scan_reaches_a_module_the_manifest_never_listed(tmp_path: Path) -> None:
    """JD-W3-1: the walk is not bounded by any hardcoded list — a module
    dropped ANYWHERE under the package root is scanned on the next run,
    with no second commit required to register its path here first.

    Mirrors the shape of T26's `application/vocabulary/ports.py`, a module
    this capability introduces after this guard was written.

    RED before the fix: the old `_vocabulary_modules()` iterated a fixed
    `_VOCABULARY_MODULES` manifest and returned an empty scan for a file
    not on that list, regardless of what was on disk.
    """
    package_root = tmp_path / "wheel_vocabulary"
    (package_root / "application" / "vocabulary").mkdir(parents=True)
    (package_root / "application" / "vocabulary" / "ports.py").write_text(
        "x = 1\n", encoding="utf-8"
    )
    migrations_root = tmp_path / "migrations"
    migrations_root.mkdir()

    scanned = {label for _, label in _scanned_modules(package_root, migrations_root)}

    assert "application/vocabulary/ports.py" in scanned


@pytest.mark.unit
def test_the_scan_reaches_migrations_outside_the_package_root(tmp_path: Path) -> None:
    """The migrations root is a SEPARATE directory tree from the package
    root (`apps/api/migrations/versions/` vs. `apps/api/src/wheel_vocabulary/`)
    — the old walk could never leave `_PACKAGE_ROOT`, so
    `0004_vocabulary_group_index.py` was unreachable regardless of the
    manifest's content."""
    package_root = tmp_path / "wheel_vocabulary"
    package_root.mkdir()
    migrations_root = tmp_path / "migrations"
    migrations_root.mkdir()
    (migrations_root / "0004_vocabulary_group_index.py").write_text("x = 1\n", encoding="utf-8")

    scanned = {label for _, label in _scanned_modules(package_root, migrations_root)}

    assert "migrations/versions/0004_vocabulary_group_index.py" in scanned


@pytest.mark.unit
def test_the_scan_does_not_reach_unrelated_capability_modules(tmp_path: Path) -> None:
    """A module belonging to a DIFFERENT capability — no `"vocabulary"` in
    its path, not a shared wiring file — is correctly excluded, even one
    that contains a LEGITIMATE `ManualCorrection` write that is none of
    this guard's business.

    `book_repository.py`'s `DeleteImport` cascade delete of
    `manual_correction` rows is exactly this case (see the module
    docstring's "Scope, corrected during this same round"): real,
    intentional, and outside REQ-005-008's scope, because
    `book_repository.py` is a `002-text-import` module, not one this
    capability introduces. An earlier draft of this fix scanned the whole
    package and flagged it as a false positive; this test pins the
    corrected scope as a regression guard.
    """
    package_root = tmp_path / "wheel_vocabulary"
    (package_root / "infrastructure" / "persistence").mkdir(parents=True)
    (package_root / "infrastructure" / "persistence" / "book_repository.py").write_text(
        "from sqlalchemy import delete\n"
        "delete(ManualCorrection).where(ManualCorrection.occurrence_id.in_(ids))\n",
        encoding="utf-8",
    )
    migrations_root = tmp_path / "migrations"
    migrations_root.mkdir()

    scanned = {label for _, label in _scanned_modules(package_root, migrations_root)}

    assert "infrastructure/persistence/book_repository.py" not in scanned


@pytest.mark.unit
def test_no_vocabulary_module_writes_to_manual_correction() -> None:
    """REQ-005-008 / AC-005-08 scenario 1: no `INSERT`, `UPDATE` or `DELETE`
    targeting `manual_correction` in any module the scan reaches — the
    entire `wheel_vocabulary` package plus every Alembic migration (see the
    module docstring's "Discovery" and "Migrations decision" sections).

    `select(ManualCorrection...)` reads and `ManualCorrection.field` attribute
    reads are PERMITTED — this capability reads corrections to resolve
    effective values (REQ-005-002). Only writes are forbidden.

    MUTATION CHECK: see `test_a_synthetic_insert_would_be_caught` and
    `test_a_synthetic_delete_would_be_caught` below for the per-mutation
    evidence (AC-005-08 scenario 3).
    """
    violations = [
        violation
        for path, label in _scanned_modules()
        for violation in _detect_writes(path.read_text(encoding="utf-8"), label)
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

        ['synthetic.py:2 ORM write call insert(ManualCorrection)']

    (JD-W3-6, Judgment Day round 1: the call is the source's SECOND line —
    the import statement is the first — so `:2` is what a verbatim run
    produces; an earlier version of this docstring recorded `:1`, which
    this file's own `_detect_writes` never actually outputs for this source.)
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


# --------------------------------------------------------------------------
# JD-W3-2 remediation (Judgment Day round 1) — pre-fix RED capture. Every
# test below is run FIRST against the ORIGINAL detector (no import-alias
# resolution, no origin check, no ORM-instance idioms) to record the exact
# miss or false positive, then again after the fix to prove it is closed.
# See the module docstring for the final list of idioms covered and the
# residual gaps documented as accepted, per SPEC-003 §3.6 G3.
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_an_aliased_core_write_import_would_be_caught() -> None:
    """`from sqlalchemy import delete as sa_delete` then `sa_delete(...)` —
    no import-origin check meant an aliased import evaded the old detector
    entirely, because it only ever matched the bare names `insert`/`update`/
    `delete`.

    RED before the fix: `_detect_writes` returned `[]` for this exact source.
    """
    source = "from sqlalchemy import delete as sa_delete\nsa_delete(ManualCorrection)\n"

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("ManualCorrection" in v for v in violations)


@pytest.mark.unit
def test_a_non_sqlalchemy_update_call_is_not_a_false_positive() -> None:
    """`cache.update(ManualCorrection)` — a dict-like `.update()` call that
    happens to take `ManualCorrection` as an argument. The old detector
    matched ANY `.insert`/`.update`/`.delete` attribute call with a
    `ManualCorrection` argument, with no check that the call actually
    originates from `sqlalchemy` — a false positive on ordinary code that
    has nothing to do with the database.

    RED before the fix: `_detect_writes` reported a violation for this
    exact source, which performs no database write at all.
    """
    source = "cache.update(ManualCorrection)\n"

    violations = _detect_writes(source, "synthetic.py")

    assert violations == []


@pytest.mark.unit
def test_a_session_add_call_constructing_manual_correction_would_be_caught() -> None:
    """`session.add(ManualCorrection(...))` is the live production write
    idiom this codebase actually uses (`book_repository.py:63`'s
    `session.add(book)`, and `test_vocabulary_read_scenario.py`'s own
    correction-seeding fixture) — and the old detector, which recognised
    only the three free `insert`/`update`/`delete` functions, had no branch
    for it at all.

    RED before the fix: `_detect_writes` returned `[]` for this exact source.
    """
    source = (
        "session.add(ManualCorrection(occurrence_id=1, field='lemma', "
        "corrected_value='x', corrected_at=None))\n"
    )

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("ManualCorrection" in v for v in violations)


@pytest.mark.unit
def test_a_session_add_all_call_constructing_manual_correction_would_be_caught() -> None:
    """`session.add_all([ManualCorrection(...), ...])` — the batched sibling
    of `session.add`, used by `book_repository.py` for the occurrence write.

    RED before the fix: `_detect_writes` returned `[]` for this exact source.
    """
    source = (
        "session.add_all([ManualCorrection(occurrence_id=1, field='lemma', "
        "corrected_value='x', corrected_at=None)])\n"
    )

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("ManualCorrection" in v for v in violations)


@pytest.mark.unit
def test_a_session_add_call_via_a_locally_bound_variable_would_be_caught() -> None:
    """`correction = ManualCorrection(...)` followed by
    `session.add(correction)` on a LATER line — exactly the shape
    `test_vocabulary_read_scenario.py:128-134` uses in this same commit.
    The construction and the write are two separate statements, so a
    detector that only inspects one `ast.Call`'s own arguments cannot see
    the connection without tracking the local binding.

    RED before the fix: `_detect_writes` returned `[]` for this exact source.
    """
    source = (
        "correction = ManualCorrection(occurrence_id=1, field='lemma', "
        "corrected_value='x', corrected_at=None)\n"
        "session.add(correction)\n"
    )

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("ManualCorrection" in v for v in violations)


@pytest.mark.unit
def test_a_session_delete_call_via_a_locally_bound_variable_would_be_caught() -> None:
    """`row = ManualCorrection(...)` followed by `session.delete(row)` — the
    delete-side mirror of the add-via-binding case above.

    RED before the fix: `_detect_writes` returned `[]` for this exact source.
    """
    source = (
        "row = ManualCorrection(occurrence_id=1, field='lemma', "
        "corrected_value='x', corrected_at=None)\n"
        "session.delete(row)\n"
    )

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("ManualCorrection" in v for v in violations)


@pytest.mark.unit
def test_a_query_delete_call_would_be_caught() -> None:
    """`session.query(ManualCorrection).delete()` — the legacy `Query` API's
    bulk-delete, which never mentions `insert`/`update`/`delete` as a free
    function and was invisible to the old detector's only branch.

    RED before the fix: `_detect_writes` returned `[]` for this exact source.
    """
    source = "session.query(ManualCorrection).delete()\n"

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("ManualCorrection" in v for v in violations)


@pytest.mark.unit
def test_a_query_update_call_would_be_caught() -> None:
    """`session.query(ManualCorrection).update({...})` — the `Query` API's
    bulk-update.

    RED before the fix: `_detect_writes` returned `[]` for this exact source.
    """
    source = "session.query(ManualCorrection).update({'field': 'pos'})\n"

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("ManualCorrection" in v for v in violations)


@pytest.mark.unit
def test_a_bulk_insert_mappings_call_would_be_caught() -> None:
    """`session.bulk_insert_mappings(ManualCorrection, rows)` — a bulk write
    entry point that bypasses the unit-of-work identity map entirely and
    never calls the free `insert()` function.

    RED before the fix: `_detect_writes` returned `[]` for this exact source.
    """
    source = "session.bulk_insert_mappings(ManualCorrection, rows)\n"

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("ManualCorrection" in v for v in violations)


@pytest.mark.unit
def test_a_bulk_update_mappings_call_would_be_caught() -> None:
    """`session.bulk_update_mappings(ManualCorrection, rows)` — the update
    sibling of the bulk-insert idiom above."""
    source = "session.bulk_update_mappings(ManualCorrection, rows)\n"

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("ManualCorrection" in v for v in violations)


@pytest.mark.unit
def test_a_table_insert_call_would_be_caught() -> None:
    """`ManualCorrection.__table__.insert()` — a Core write issued directly
    against the mapped table, bypassing both the free `insert()` function
    and the ORM session entirely.

    RED before the fix: `_detect_writes` returned `[]` for this exact source.
    """
    source = "ManualCorrection.__table__.insert()\n"

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("ManualCorrection" in v for v in violations)


@pytest.mark.unit
def test_a_table_delete_call_would_be_caught() -> None:
    """`ManualCorrection.__table__.delete()` — the delete sibling of the
    Core table-write idiom above."""
    source = "ManualCorrection.__table__.delete()\n"

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("ManualCorrection" in v for v in violations)


# --------------------------------------------------------------------------
# G3 — accepted residual gaps. Each test below EXERCISES a case this
# AST-only detector does NOT cover and records that as specified, accepted
# behaviour, so a future change to this detector has something to flip
# rather than an unnoticed hole. See the module docstring's "Residual gaps"
# section for the full list.
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_an_attribute_mutation_followed_by_commit_is_a_known_residual_gap() -> None:
    """`row.field = 'corrected'` then `session.commit()` mutates an
    already-fetched ORM object with no syntax naming `ManualCorrection`
    anywhere in the mutating statement itself. `row`'s runtime type is
    whatever query produced it; this is a static, per-file AST guard, not a
    type checker, and performs no such inference.

    ACCEPTED (SPEC-003 §3.6 G3): closing this would require tracking a
    variable's runtime type across arbitrary prior statements, which this
    guard does not attempt.
    """
    source = "row.field = 'corrected'\nsession.commit()\n"

    violations = _detect_writes(source, "synthetic.py")

    assert violations == []


@pytest.mark.unit
def test_a_delete_of_an_opaquely_fetched_row_is_a_known_residual_gap() -> None:
    """`session.delete(row)` where `row` was fetched by a query (or aliased
    from one) rather than directly bound to a `ManualCorrection(...)`
    construction. The binding tracker above only follows a DIRECT
    `name = ManualCorrection(...)` assignment; a query result, a function
    return value, or a second alias of an already-tracked name all evade it.

    ACCEPTED (SPEC-003 §3.6 G3): this is the same limitation
    `test_annotation_write_repository_isolation.py`'s docstring accepts for
    string construction, applied here to object provenance instead.
    """
    source = (
        "row = session.query(ManualCorrection).filter_by(id=1).first()\n"
        "other = row\n"
        "session.delete(other)\n"
    )

    violations = _detect_writes(source, "synthetic.py")

    assert violations == []


@pytest.mark.unit
def test_a_reassigned_sqlalchemy_import_name_is_flagged_conservatively() -> None:
    """`from sqlalchemy import insert` then a LATER reassignment
    `insert = some_other_callable` shadows the tracked alias. The alias map
    is built once, statically, from the module's import statements — it is
    NOT flow-sensitive to a later rebinding of the same name, so this call
    is STILL reported even though it may no longer reach `sqlalchemy` at
    runtime.

    ACCEPTED (SPEC-003 §3.6 G3), and deliberately on the safe side: this is
    an over-approximation (a call that MIGHT be a false positive still gets
    flagged), never an under-approximation (a real write silently passing).
    A write-safety guard failing towards "flag it" on an ambiguous case is
    the correct default; failing towards "let it through" would not be.
    """
    source = "from sqlalchemy import insert\ninsert = lambda *a: None\ninsert(ManualCorrection)\n"

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("insert" in v and "ManualCorrection" in v for v in violations)

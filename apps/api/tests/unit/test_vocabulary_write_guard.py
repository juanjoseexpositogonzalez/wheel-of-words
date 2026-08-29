"""Structural guard — no code path in this capability writes a `ManualCorrection` row (REQ-005-008).

This guard is DISTINCT from `test_annotation_write_repository_isolation.py`
and narrower: that guard forbids the annotation write path from referencing
`ManualCorrection` at all (SPEC-003 R3). This capability's aggregate query
must *read* `manual_correction` to resolve effective values (REQ-005-002),
so this guard distinguishes read from write instead: a `SELECT` is
permitted, an `INSERT`, `UPDATE` or `DELETE` is a violation. It never flags
`select(ManualCorrection...)` or a `ManualCorrection.field` attribute read.

**Scope.** `_scanned_modules()` walks the entire `wheel_vocabulary` package
(`Path.rglob("*.py")`, no filter) plus every file under
`migrations/versions/`. There is no naming convention and no manifest: a
module dropped anywhere under either root is scanned on its next run, with
no second commit required to register its path first. This is what makes
AC-005-08's "every module this capability introduces" literally true —
the scanned set is a superset of what this capability ships, not a
convention this capability's modules have followed so far.

**Exemptions.** REQ-005-008 forbids a write by "a module this capability
introduces". A module this walk reaches that belongs to a DIFFERENT,
already-shipped capability, and that legitimately writes to
`manual_correction`, is exempted by exact path in `_EXEMPT_WRITE_MODULES`,
with its reason recorded next to it. The walk still reaches an exempted
module — `test_the_only_exemption_is_book_repository_and_it_is_scanned`
pins this — and only the violation is suppressed, at the aggregation step
in `_write_violations`, never by removing the module from
`_scanned_modules`. Excluding an exempted module from the walk itself would
be the exact remedy SPEC-003 §3.4 W1 forbids.

`book_repository.py` is the one exemption today: `DeleteImport`'s cascade
delete removes `manual_correction` rows for a deleted book's occurrences,
so a later import that reuses the freed `Occurrence.id` does not inherit a
ghost correction it never made — that is `002-text-import`'s concern, not
this capability's. Two tests prove the exemption is load-bearing rather
than decorative: `test_the_exempted_write_is_real_not_inert` shows the
write it hides is genuine, and `test_removing_the_exemption_fails_the_scan`
shows deleting the entry fails the guard. No module whose path carries the
case-insensitive token `"vocabulary"` may ever be exempted — enforced by
`test_no_exempt_module_carries_the_vocabulary_naming_token`.

**Migrations carry no exemption.** Every file under `migrations/versions/`
is scanned with no capability scoping and no exemption mechanism at all,
unlike the package walk above. A migration belonging to any OTHER
capability that legitimately writes to `manual_correction` — a future
data-cleanup migration, for instance — would be flagged here with no way
to exempt it. This is an accepted, currently-live over-approximation
(SPEC-003 §3.6 G3), pinned by
`test_a_migration_write_is_flagged_with_no_exemption_mechanism`, which
calls the detector end to end against a synthetic migration rather than
only checking scan membership.

**Detection.** The write detector resolves `sqlalchemy` import aliases
(`from sqlalchemy import delete as sa_delete`) and verifies call origin for
the three free `insert`/`update`/`delete` functions — a bare
`insert`/`update`/`delete` `Name` is matched only when traceable to a
`sqlalchemy` import; `cache.update(ManualCorrection)`, an ordinary
dict-like call, is not flagged this way.

The remaining idioms are matched by method name and argument shape alone,
with no check on the receiver's origin: `cache.add(ManualCorrection())` and
`cache.delete(ManualCorrection)` are indistinguishable, to this AST walk,
from a real `session.add`/`session.delete`, and ARE flagged — a deliberate
over-approximation, never the reverse. The violation message names the
actual receiver expression (`_receiver_name`) and marks these idioms
`[receiver origin unverified]`, rather than asserting `session.` regardless
of what the source says. Covered idioms, beyond the three free functions:

  - `<receiver>.add(ManualCorrection(...))` / `<receiver>.add_all([...])`,
    including via a local variable directly bound to a `ManualCorrection(...)`
    construction earlier in the same module. No receiver-origin check.
  - `<receiver>.delete(...)`, same binding-tracking rule as `add`, same no
    receiver-origin check.
  - `<receiver>.query(ManualCorrection).delete()` / `.update({...})` — no
    verified `Session`/`Query` origin either.
  - `<receiver>.bulk_insert_mappings(ManualCorrection, ...)` /
    `.bulk_update_mappings(ManualCorrection, ...)` — method names are
    SQLAlchemy-specific, not origin-verified.
  - `ManualCorrection.__table__.insert()` / `.update()` / `.delete()` — the
    one idiom with a genuine origin check: the receiver chain must resolve
    to a `Name` or an `Attribute` spelled `ManualCorrection`.

**Binding tracker.** Three binding shapes let the detector follow a
`ManualCorrection` construction to a later write on a different line, one
assignment hop: `name = ManualCorrection(...)` (`ast.Assign`),
`name: ManualCorrection = ManualCorrection(...)` (`ast.AnnAssign`), and
`(name := ManualCorrection(...))` (`ast.NamedExpr`, walrus). The binding
set is built once from the whole module body and is flow-insensitive — see
the known-gaps list below.

**Known gaps.** The list below is not exhaustive — an AST-only detector
over untyped Python always has more gaps than any one docstring enumerates.
Each gap here is pinned by a test that calls the detector against the
uncovered case, never a test that only asserts a label.

Under-approximations (a real write passes silently):

  - `from sqlalchemy.sql import delete` / `from sqlalchemy.sql.expression
    import insert` — the alias collector requires `node.module ==
    "sqlalchemy"` exactly.
    `test_a_sqlalchemy_submodule_import_evades_alias_resolution`.
  - `session.merge(ManualCorrection(...))` — a real INSERT-or-UPDATE with
    no branch for it at all. `test_a_session_merge_call_is_a_known_residual_gap`.
  - `session.add_all` with a tuple or a generator expression — the matcher
    requires `isinstance(arg, ast.List)`.
    `test_add_all_with_a_non_list_argument_is_a_known_residual_gap`.
  - Tuple-unpacking (`a, b = ManualCorrection(x=1), 2`) and `for`-target
    bindings (`for c in [...]: session.add(c)`) — neither binding shape is
    tracked. `test_tuple_and_for_target_bindings_are_known_residual_gaps`.
  - An attribute-assignment mutation of an already-fetched row
    (`row.field = "x"`) followed by `session.commit()` names no forbidden
    identifier at the mutation site; this is a static, per-file AST guard,
    not a type checker, and performs no type inference.
    `test_an_attribute_mutation_followed_by_commit_is_a_known_residual_gap`.
  - `session.delete(row)` where `row` was fetched by a query, or aliased
    from one, rather than directly bound to a construction — the tracker
    follows one hop from a construction, never into a query result.
    `test_a_delete_of_an_opaquely_fetched_row_is_a_known_residual_gap`.
  - A second alias of an already-tracked name (`y = x` after `x =
    ManualCorrection(...)`) — `y`'s value is a bare `Name`, not a
    construction, so `y` never enters the binding set.
    `test_a_second_alias_of_a_tracked_binding_is_a_known_residual_gap`.
  - Raw-SQL adjacency: `REPLACE INTO`, `TRUNCATE`, whitespace variants
    (a double space, a newline splitting the fragment), a quoted or
    schema-qualified table name, and runtime string assembly
    (`str.join`, `%`-formatting, an f-string) all reach `manual_correction`
    without ever containing one of the three tracked fragments verbatim.
    `test_raw_sql_adjacency_gaps_evade_the_substring_scan`.

Over-approximations (a call gets flagged that is not a database write):

  - `<receiver>.add`/`.add_all`/`.delete`,
    `<receiver>.query(...).delete()`/`.update()`, and
    `<receiver>.bulk_insert_mappings`/`.bulk_update_mappings` verify no
    receiver origin at all — see the "Detection" section above.
    `test_a_non_session_add_call_is_a_known_false_positive`,
    `test_a_non_session_delete_call_is_a_known_false_positive`.
  - The binding set is flow-insensitive: a name reassigned away from a
    `ManualCorrection(...)` construction stays "bound" for the rest of the
    module. `test_a_rebound_tracked_name_is_a_known_false_positive_residual_gap`.
  - A `sqlalchemy` import name reassigned after import
    (`insert = lambda *a: None`) is still flagged; the alias map is built
    once from imports and is never updated on a later rebinding.
    `test_a_reassigned_sqlalchemy_import_name_is_flagged_conservatively`.

REQ-005-008, AC-005-08.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src" / "wheel_vocabulary"
_MIGRATIONS_ROOT = Path(__file__).resolve().parents[2] / "migrations" / "versions"

# Non-vacuity anchors (SPEC-003 §3.3 M2): real files the scan MUST reach, or
# the guard below proves nothing. Not a manifest the scan enumerates FROM —
# `_scanned_modules` walks the filesystem unconditionally; these sets are
# only the checkpoints the non-vacuity tests assert against.
_EXPECTED_PACKAGE_MODULES = frozenset(
    {
        "infrastructure/persistence/vocabulary_repository.py",
        # The one exempted module (see the module docstring's "Exemptions"
        # section). Anchored here too, so a silent removal of this file
        # from the walk — as opposed to a legitimate change to the
        # exemption reason — would fail non-vacuity like any other anchor.
        "infrastructure/persistence/book_repository.py",
        "api/dependencies.py",
        "api/main.py",
    }
)
_EXPECTED_MIGRATIONS = frozenset({"0004_vocabulary_group_index.py"})

# The one documented exemption. See the module docstring's "Exemptions"
# section for the mechanism and the tests that prove it is load-bearing.
_EXEMPT_WRITE_MODULES: dict[str, str] = {
    "infrastructure/persistence/book_repository.py": (
        "002-text-import: DeleteImport's cascade delete removes "
        "manual_correction rows for a deleted book's occurrences, so a "
        "later import that reuses the freed Occurrence.id never inherits "
        "a ghost correction it never made."
    ),
}

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

    No docstring exemption here — a raw SQL string in a docstring is still
    a signal worth flagging in a write-path guard. This is simpler than a
    reference guard's docstring exemption because this guard's forbidden
    patterns are SQL fragments, not a class name a docstring might
    legitimately explain.
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
    "delete"`. Only `insert`/`update`/`delete` are tracked. This is what
    lets `_core_write_call` verify origin instead of matching a bare `Name`
    with no idea where it came from.
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
    """True if `node` is a call constructing `ManualCorrection(...)` directly,
    unwrapping one `NamedExpr` (walrus) layer first.

    `session.add(c := ManualCorrection(...))` puts the `NamedExpr` itself,
    not its inner `Call`, in the argument position, so this looks one level
    through it to find the construction.
    """
    if isinstance(node, ast.NamedExpr):
        return _constructs_manual_correction(node.value)
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


def _single_construction_target(node: ast.AST) -> ast.Name | None:
    """Return the `Name` target of an `ast.AnnAssign` or `ast.NamedExpr`
    binding that directly constructs `ManualCorrection(...)`, else `None`."""
    if not isinstance(node, ast.AnnAssign | ast.NamedExpr):
        return None
    value = node.value
    if value is None or not _constructs_manual_correction(value):
        return None
    return node.target if isinstance(node.target, ast.Name) else None


def _manual_correction_bindings(tree: ast.AST) -> frozenset[str]:
    """Names directly bound to a `ManualCorrection(...)` construction
    anywhere in the module (module-scope, flow-insensitive), so
    `correction = ManualCorrection(...)` followed by
    `session.add(correction)` on a later, non-adjacent line is recognised.

    Three binding shapes are tracked, each exactly one assignment hop from
    a direct `ManualCorrection(...)` construction: `ast.Assign`,
    `ast.AnnAssign`, and `ast.NamedExpr`. A binding threaded through a
    second alias of an already-tracked name, a function argument, or a
    query result is not tracked — only a direct construction counts as the
    one hop. See the module docstring's "Known gaps" section.
    """
    bindings: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and _constructs_manual_correction(node.value):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    bindings.add(target.id)
            continue
        single_target = _single_construction_target(node)
        if single_target is not None:
            bindings.add(single_target.id)
    return frozenset(bindings)


def _references_manual_correction(node: ast.AST, bindings: frozenset[str]) -> bool:
    """True if `node` constructs, names, or (via a tracked local binding)
    resolves to `ManualCorrection`."""
    if _constructs_manual_correction(node) or _names_manual_correction(node):
        return True
    return isinstance(node, ast.Name) and node.id in bindings


def _has_manual_correction_arg(call: ast.Call) -> bool:
    """True if `call` names `ManualCorrection` as a positional or keyword
    argument — matches `insert(ManualCorrection, ...)`,
    `update(ManualCorrection)`, `delete(ManualCorrection)`."""
    for arg in call.args:
        if isinstance(arg, ast.Name) and arg.id == "ManualCorrection":
            return True
        if isinstance(arg, ast.Attribute) and arg.attr == "ManualCorrection":
            return True
    for kw in call.keywords:
        if isinstance(kw.value, ast.Name) and kw.value.id == "ManualCorrection":
            return True
    return False


def _core_write_call(
    node: ast.Call, call_aliases: dict[str, str], module_aliases: frozenset[str]
) -> str | None:
    """`insert(ManualCorrection, ...)` / `update(...)` / `delete(...)`,
    resolved through import aliases, or `sqlalchemy.insert(...)` via a
    tracked module alias.

    Origin-checked: a bare `.update()`/`.insert()`/`.delete()` attribute
    call is not matched here unless its base is a name the module actually
    imported `sqlalchemy` (or `sqlalchemy as ...`) under — so
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


def _instance_add_call(node: ast.Call, bindings: frozenset[str]) -> str | None:
    """`<receiver>.add(ManualCorrection(...))` / `<receiver>.add_all([...])`,
    including via a locally bound variable.

    No receiver-origin check: `<receiver>` can be any expression — this
    matches the method name and argument shape alone. See the module
    docstring's "Detection" section.
    """
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
    """`<receiver>.delete(row)` where `row` constructs, names, or is bound
    to `ManualCorrection`. Requires an argument, which is what tells this
    apart from the zero-arg `.query(ManualCorrection).delete()` form
    `_query_write_call` handles instead.

    No receiver-origin check: same caveat as `_instance_add_call` above.
    """
    func = node.func
    if not isinstance(func, ast.Attribute) or func.attr != "delete" or not node.args:
        return None
    if _references_manual_correction(node.args[0], bindings):
        return "delete"
    return None


def _receiver_name(node: ast.expr) -> str:
    """Best-effort source-level rendering of a call's receiver expression,
    for the violation MESSAGE text only — never for detection.

    Renders a plain dotted name (`session`, `self.session`) as written; a
    receiver this walk cannot flatten to one falls back to a generic
    placeholder rather than guessing.
    """
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_receiver_name(node.value)}.{node.attr}"
    return "<expr>"


def _query_write_call(node: ast.Call) -> str | None:
    """`<session>.query(ManualCorrection).delete()` / `.update({...})` —
    the legacy `Query` API's bulk write methods."""
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
    `.bulk_update_mappings(ManualCorrection, rows)`."""
    func = node.func
    if not isinstance(func, ast.Attribute) or func.attr not in _SESSION_MAPPING_METHODS:
        return None
    if not node.args or not _names_manual_correction(node.args[0]):
        return None
    return func.attr


def _table_write_call(node: ast.Call) -> str | None:
    """`ManualCorrection.__table__.insert()` / `.update()` / `.delete()` —
    a Core write issued directly against the mapped table. The receiver
    chain is checked with `_names_manual_correction`, so a module-qualified
    reference (`models.ManualCorrection.__table__.insert()`) is caught the
    same way the bare form is."""
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
    human-readable description of the first match, or `None`.

    The instance-write branches (`add`/`add_all`/`delete`) name the
    RECEIVER as written in source (`_receiver_name`), never a hardcoded
    `session.` — those idioms verify no receiver origin, so the message
    must not assert a `Session` origin the detector never checked.
    """
    canonical = _core_write_call(node, call_aliases, module_aliases)
    if canonical is not None:
        return f"ORM write call {canonical}(ManualCorrection)"
    func = node.func
    receiver = _receiver_name(func.value) if isinstance(func, ast.Attribute) else "<expr>"
    unverified = "[receiver origin unverified]"
    method = _instance_add_call(node, bindings)
    if method is not None:
        return f"ORM instance write {receiver}.{method}(ManualCorrection) {unverified}"
    if _instance_delete_call(node, bindings) is not None:
        return f"ORM instance write {receiver}.delete(ManualCorrection) {unverified}"
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
       dispatches through — see the module docstring's "Detection" section
       for the full list and "Known gaps" for what remains uncovered.
    2. Substring scan over string/`BinOp`-folded literals for raw SQL
       `INSERT INTO manual_correction` / `UPDATE manual_correction` /
       `DELETE FROM manual_correction` (case-insensitive).
    """
    tree = ast.parse(source, filename=label)
    call_aliases = _collect_sqlalchemy_call_aliases(tree)
    module_aliases = _collect_sqlalchemy_module_aliases(tree)
    bindings = _manual_correction_bindings(tree)
    violations: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        description = _classify_write_call(node, call_aliases, module_aliases, bindings)
        if description is not None:
            line = getattr(node, "lineno", 0)
            violations.append(f"{label}:{line} {description}")

    for literal in _all_string_literals(source, label):
        lower = literal.lower()
        for fragment in _FORBIDDEN_RAW_SQL:
            if fragment in lower:
                violations.append(f"{label} raw SQL fragment {fragment!r}")

    return violations


def _scanned_modules(
    package_root: Path = _PACKAGE_ROOT, migrations_root: Path = _MIGRATIONS_ROOT
) -> list[tuple[Path, str]]:
    """Enumerate every module this write guard scans: `(path, label)` for
    every `.py` file under `package_root`, unconditionally, plus every
    Alembic migration under `migrations_root`.

    No naming convention and no manifest — a module's presence here depends
    only on where it lives on disk. `package_root`/`migrations_root` are
    overridable so the tests below can exercise an empty, partial, or
    unrelated tree without touching the real one.
    """
    modules = [
        (path, path.relative_to(package_root).as_posix())
        for path in sorted(package_root.rglob("*.py"))
    ]
    modules += [
        (path, f"migrations/versions/{path.name}") for path in sorted(migrations_root.glob("*.py"))
    ]
    return modules


def _write_violations(
    modules: list[tuple[Path, str]] | None = None,
    exempt: dict[str, str] | None = None,
) -> list[str]:
    """Run `_detect_writes` over every scanned module except those named in
    `exempt`.

    `exempt` defaults to `_EXEMPT_WRITE_MODULES`, the real documented
    exemption set. Tests below pass `exempt={}` to prove the exemption is
    load-bearing rather than decorative — see
    `test_removing_the_exemption_fails_the_scan`.
    """
    scan = _scanned_modules() if modules is None else modules
    active_exemptions = _EXEMPT_WRITE_MODULES if exempt is None else exempt
    return [
        violation
        for path, label in scan
        if label not in active_exemptions
        for violation in _detect_writes(path.read_text(encoding="utf-8"), label)
    ]


# --------------------------------------------------------------------------
# Non-vacuity and the unconditional walk.
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_the_scan_reaches_every_expected_module() -> None:
    """Non-vacuity (SPEC-003 §3.3 M2): the walk must reach the vocabulary
    repository, the exempted book repository, both shared wiring files, and
    the vocabulary migration on the real filesystem, or the guard below
    proves nothing."""
    scanned = {label for _, label in _scanned_modules()}

    missing_package = _EXPECTED_PACKAGE_MODULES - scanned
    missing_migrations = {f"migrations/versions/{name}" for name in _EXPECTED_MIGRATIONS} - scanned
    missing = missing_package | missing_migrations

    assert not missing, "the module walk is missing expected modules: " + ", ".join(sorted(missing))


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
def test_the_scan_fails_closed_when_any_anchor_is_missing(tmp_path: Path) -> None:
    """SPEC-003 §3.3 M2, verified by construction for every named anchor: a
    package tree missing exactly one of `_EXPECTED_PACKAGE_MODULES` must
    fail `scanned >= _EXPECTED_PACKAGE_MODULES` — proving the assertion can
    fail on each anchor individually, not only when the whole tree is
    empty."""
    migrations_root = tmp_path / "migrations"
    migrations_root.mkdir()
    (migrations_root / "0004_vocabulary_group_index.py").write_text("x = 1\n", encoding="utf-8")

    for missing in sorted(_EXPECTED_PACKAGE_MODULES):
        package_root = tmp_path / f"pkg_missing_{missing.replace('/', '_')}"
        for present in _EXPECTED_PACKAGE_MODULES - {missing}:
            target = package_root / present
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("x = 1\n", encoding="utf-8")

        scanned = {label for _, label in _scanned_modules(package_root, migrations_root)}

        assert not (scanned >= _EXPECTED_PACKAGE_MODULES), (
            f"a tree missing only {missing!r} did not fail non-vacuity"
        )


@pytest.mark.unit
def test_the_scan_reaches_a_module_with_no_vocabulary_token_in_its_path(tmp_path: Path) -> None:
    """The walk carries no naming convention: a module whose path contains
    no `"vocabulary"` token anywhere is still scanned, because
    `_scanned_modules` filters on nothing but `.py`. This is what makes
    AC-005-08's "every module this capability introduces" true by
    construction rather than by an assumed convention."""
    package_root = tmp_path / "wheel_vocabulary"
    (package_root / "api" / "dtos").mkdir(parents=True)
    (package_root / "api" / "dtos" / "groups.py").write_text("x = 1\n", encoding="utf-8")
    migrations_root = tmp_path / "migrations"
    migrations_root.mkdir()

    scanned = {label for _, label in _scanned_modules(package_root, migrations_root)}

    assert "api/dtos/groups.py" in scanned


@pytest.mark.unit
def test_the_scan_reaches_migrations_outside_the_package_root(tmp_path: Path) -> None:
    """The migrations root is a SEPARATE directory tree from the package
    root (`apps/api/migrations/versions/` vs. `apps/api/src/wheel_vocabulary/`)
    — a walk bounded to the package root alone could never reach
    `0004_vocabulary_group_index.py` regardless of anything else."""
    package_root = tmp_path / "wheel_vocabulary"
    package_root.mkdir()
    migrations_root = tmp_path / "migrations"
    migrations_root.mkdir()
    (migrations_root / "0004_vocabulary_group_index.py").write_text("x = 1\n", encoding="utf-8")

    scanned = {label for _, label in _scanned_modules(package_root, migrations_root)}

    assert "migrations/versions/0004_vocabulary_group_index.py" in scanned


# --------------------------------------------------------------------------
# The exemption mechanism.
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_the_only_exemption_is_book_repository_and_it_is_scanned() -> None:
    """The exemption set names exactly one module today, and the walk still
    reaches it — the exemption suppresses a violation at the aggregation
    step, it never removes the module from `_scanned_modules`."""
    assert set(_EXEMPT_WRITE_MODULES) == {"infrastructure/persistence/book_repository.py"}

    scanned = {label for _, label in _scanned_modules()}

    assert "infrastructure/persistence/book_repository.py" in scanned


@pytest.mark.unit
def test_no_exempt_module_carries_the_vocabulary_naming_token() -> None:
    """Invariant: this capability never exempts one of its own modules. A
    future exemption whose path contains the case-insensitive token
    `"vocabulary"` fails this test immediately, rather than surviving until
    a human reviewer notices."""
    offending = [label for label in _EXEMPT_WRITE_MODULES if "vocabulary" in label.lower()]

    assert not offending, f"a vocabulary module is exempted: {offending}"


@pytest.mark.unit
def test_the_exempted_write_is_real_not_inert() -> None:
    """The exemption hides a GENUINE write, not a hypothetical one — proved
    by calling the detector directly against `book_repository.py`'s actual
    source, bypassing `_write_violations`'s exemption filter entirely.

    MUTATION CHECK: ran `_detect_writes` against the real file and observed::

      ['infrastructure/persistence/book_repository.py:144 ORM write call delete(ManualCorrection)']

    That line is `delete(ManualCorrection).where(...)` inside
    `SqlAlchemyBookRepository.delete()` — a real, origin-checked
    `sqlalchemy.delete()` call, not a synthetic fixture.
    """
    path, label = next(
        (p, lbl)
        for p, lbl in _scanned_modules()
        if lbl == "infrastructure/persistence/book_repository.py"
    )

    violations = _detect_writes(path.read_text(encoding="utf-8"), label)

    assert violations
    assert any("ManualCorrection" in v for v in violations)


@pytest.mark.unit
def test_removing_the_exemption_fails_the_scan() -> None:
    """M3, made meaningful by a real exemption: dropping `book_repository.py`
    from the exempt set must fail the main guard, proving the earlier
    passing state is the exemption's doing and not an accident of scope.

    MUTATION CHECK: ran `_write_violations(exempt={})` and observed a
    violation naming `book_repository.py` — see the assertion below,
    verified by execution.
    """
    violations = _write_violations(exempt={})

    assert violations
    assert any("book_repository.py" in v for v in violations)


@pytest.mark.unit
def test_the_exemption_boundary_holds() -> None:
    """AC-005-08 scenario 4 / M3: the same forbidden write statement placed
    in a module that carries no exemption still produces a violation — the
    detector itself grants no blanket safety; only the two exemption tests
    above do, and only for the one named module."""
    source = "from sqlalchemy import insert\ninsert(ManualCorrection, {'field': 'pos'})\n"

    violations = _detect_writes(source, "some/other/module.py")

    assert violations
    assert any("insert" in v and "ManualCorrection" in v for v in violations)


# --------------------------------------------------------------------------
# Migrations: scanned unconditionally, with no exemption mechanism.
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_a_migration_write_is_flagged_with_no_exemption_mechanism(tmp_path: Path) -> None:
    """Migrations are not scoped by capability the way the package walk is,
    and carry no exemption mechanism at all: a migration belonging to ANY
    capability — including a hypothetical future data-cleanup migration
    with a legitimate `manual_correction` write — is flagged here.

    This calls `_write_violations` end to end against a real synthetic
    migration, so a detector stubbed to return `[]` would fail this test —
    unlike a test that only checks scan membership.

    ACCEPTED (SPEC-003 §3.6 G3): tracking which migration belongs to which
    capability would reintroduce a manifest, the exact shape the package
    walk's exemption mechanism above exists to avoid for THIS capability's
    own scope.
    """
    package_root = tmp_path / "wheel_vocabulary"
    package_root.mkdir()
    migrations_root = tmp_path / "migrations"
    migrations_root.mkdir()
    (migrations_root / "9999_unrelated_cleanup.py").write_text(
        "from sqlalchemy import delete\ndelete(ManualCorrection).where(ManualCorrection.id > 0)\n",
        encoding="utf-8",
    )

    violations = _write_violations(_scanned_modules(package_root, migrations_root))

    assert violations
    assert any("9999_unrelated_cleanup.py" in v for v in violations)


# --------------------------------------------------------------------------
# The main guard and its mutation checks.
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_no_module_writes_to_manual_correction() -> None:
    """REQ-005-008 / AC-005-08 scenario 1: no `INSERT`, `UPDATE` or `DELETE`
    targeting `manual_correction` in any module this guard scans, after the
    one documented exemption is applied.

    `select(ManualCorrection...)` reads and `ManualCorrection.field`
    attribute reads are permitted — this capability reads corrections to
    resolve effective values (REQ-005-002). Only writes are forbidden.
    """
    violations = _write_violations()

    assert not violations, "a module writes to manual_correction:\n" + "\n".join(violations)


@pytest.mark.unit
def test_a_synthetic_insert_would_be_caught() -> None:
    """AC-005-08 scenario 3: a synthetic `insert(ManualCorrection, ...)`
    must produce a violation.

    MUTATION CHECK: ran `_detect_writes` against this exact source and
    observed::

        ['synthetic.py:2 ORM write call insert(ManualCorrection)']
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
def test_a_write_placed_in_the_vocabulary_repository_would_be_caught() -> None:
    """AC-005-08 scenario 3, using its literal wording: an insert against
    `ManualCorrection`, then a delete against it, each added in turn to the
    real `vocabulary_repository.py` source.
    """
    path = _PACKAGE_ROOT / "infrastructure" / "persistence" / "vocabulary_repository.py"
    original = path.read_text(encoding="utf-8")
    label = "infrastructure/persistence/vocabulary_repository.py"
    with_insert = (
        original + "\nfrom sqlalchemy import insert\ninsert(ManualCorrection, {'field': 'lemma'})\n"
    )
    with_delete = original + "\nfrom sqlalchemy import delete\ndelete(ManualCorrection)\n"

    insert_violations = _detect_writes(with_insert, label)
    delete_violations = _detect_writes(with_delete, label)

    assert insert_violations
    assert any("insert" in v and "ManualCorrection" in v for v in insert_violations)
    assert delete_violations
    assert any("delete" in v and "ManualCorrection" in v for v in delete_violations)


@pytest.mark.unit
def test_select_on_manual_correction_is_permitted() -> None:
    """AMB-3: a `select(ManualCorrection...)` read is NOT a violation. This
    capability reads corrections to resolve effective values (REQ-005-002).
    The guard distinguishes read from write — only INSERT/UPDATE/DELETE are
    forbidden."""
    source = "from sqlalchemy import select\nselect(ManualCorrection.occurrence_id)\n"

    violations = _detect_writes(source, "synthetic.py")

    assert not violations


@pytest.mark.unit
def test_manual_correction_attribute_read_is_permitted() -> None:
    """AMB-3: `ManualCorrection.field` attribute access in a select is NOT a
    violation — it is the legitimate correction-delta lookup."""
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
# ORM write idiom coverage — every idiom the detector recognises.
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_an_aliased_core_write_import_would_be_caught() -> None:
    """`from sqlalchemy import delete as sa_delete` then `sa_delete(...)` —
    resolved through the import-alias map."""
    source = "from sqlalchemy import delete as sa_delete\nsa_delete(ManualCorrection)\n"

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("ManualCorrection" in v for v in violations)


@pytest.mark.unit
def test_a_non_session_add_call_is_a_known_false_positive() -> None:
    """`cache.add(ManualCorrection())` — `cache` is not a `Session`, but
    `_instance_add_call` performs no receiver-origin check: it matches ANY
    receiver's `.add(...)` call whose argument shape names
    `ManualCorrection`, exactly like it would for a real `session.add(...)`.

    ACCEPTED (SPEC-003 §3.6 G3), deliberately on the safe side: a call that
    might not be a database write still gets flagged, never the reverse.
    The violation message names the actual receiver (`cache`, not
    `session`) and marks the origin unverified.
    """
    source = (
        "cache.add(ManualCorrection(occurrence_id=1, field='lemma', "
        "corrected_value='x', corrected_at=None))\n"
    )

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("cache.add" in v and "unverified" in v for v in violations)


@pytest.mark.unit
def test_a_non_session_delete_call_is_a_known_false_positive() -> None:
    """`cache.delete(ManualCorrection)` — the delete-side mirror of the
    `add` case above; same no receiver-origin check, same accepted
    over-approximation (SPEC-003 §3.6 G3)."""
    source = "cache.delete(ManualCorrection)\n"

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("cache.delete" in v and "unverified" in v for v in violations)


@pytest.mark.unit
def test_a_non_sqlalchemy_update_call_is_not_a_false_positive() -> None:
    """`cache.update(ManualCorrection)` — a dict-like `.update()` call that
    happens to take `ManualCorrection` as an argument, with no `sqlalchemy`
    import anywhere in the module. The origin check on the three free
    functions keeps this from being flagged."""
    source = "cache.update(ManualCorrection)\n"

    violations = _detect_writes(source, "synthetic.py")

    assert violations == []


@pytest.mark.unit
def test_a_session_add_call_constructing_manual_correction_would_be_caught() -> None:
    """`session.add(ManualCorrection(...))` — the production write idiom
    this codebase actually uses."""
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
    of `session.add`."""
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
    `session.add(correction)` on a LATER line — the construction and the
    write are two separate statements, so this requires tracking the local
    binding."""
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
    delete-side mirror of the add-via-binding case above."""
    source = (
        "row = ManualCorrection(occurrence_id=1, field='lemma', "
        "corrected_value='x', corrected_at=None)\n"
        "session.delete(row)\n"
    )

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("ManualCorrection" in v for v in violations)


@pytest.mark.unit
def test_an_annotated_assignment_binding_would_be_caught() -> None:
    """`correction: ManualCorrection = ManualCorrection(...)` followed by
    `session.add(correction)` — the idiomatic binding form in this
    mypy-strict repository."""
    source = (
        "correction: ManualCorrection = ManualCorrection(occurrence_id=1, field='lemma', "
        "corrected_value='x', corrected_at=None)\n"
        "session.add(correction)\n"
    )

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("ManualCorrection" in v for v in violations)


@pytest.mark.unit
def test_a_walrus_binding_would_be_caught() -> None:
    """`session.add(c := ManualCorrection(...))` — the walrus operator binds
    and passes the construction in one expression."""
    source = (
        "session.add(c := ManualCorrection(occurrence_id=1, field='lemma', "
        "corrected_value='x', corrected_at=None))\n"
    )

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("ManualCorrection" in v for v in violations)


@pytest.mark.unit
def test_a_query_delete_call_would_be_caught() -> None:
    """`session.query(ManualCorrection).delete()` — the legacy `Query` API's
    bulk-delete."""
    source = "session.query(ManualCorrection).delete()\n"

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("ManualCorrection" in v for v in violations)


@pytest.mark.unit
def test_a_query_update_call_would_be_caught() -> None:
    """`session.query(ManualCorrection).update({...})` — the `Query` API's
    bulk-update."""
    source = "session.query(ManualCorrection).update({'field': 'pos'})\n"

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("ManualCorrection" in v for v in violations)


@pytest.mark.unit
def test_a_bulk_insert_mappings_call_would_be_caught() -> None:
    """`session.bulk_insert_mappings(ManualCorrection, rows)` — a bulk write
    entry point that bypasses the unit-of-work identity map entirely."""
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
    and the ORM session."""
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


@pytest.mark.unit
def test_a_qualified_table_write_would_also_be_caught() -> None:
    """`_names_manual_correction` matches an `ast.Attribute` ending in
    `ManualCorrection`, not only a bare `ast.Name` — so a module-qualified
    reference is caught by the same branch as the bare form above."""
    source = "models.ManualCorrection.__table__.insert()\n"

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("ManualCorrection" in v for v in violations)


# --------------------------------------------------------------------------
# G3 — accepted residual gaps. Each test EXERCISES a case this AST-only
# detector does NOT cover and records that as specified, accepted behaviour.
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_an_attribute_mutation_followed_by_commit_is_a_known_residual_gap() -> None:
    """`row.field = 'corrected'` then `session.commit()` mutates an
    already-fetched ORM object with no syntax naming `ManualCorrection`
    anywhere in the mutating statement itself. `row`'s runtime type is
    whatever query produced it; this is a static AST guard, not a type
    checker, and performs no such inference.

    ACCEPTED (SPEC-003 §3.6 G3): closing this would require tracking a
    variable's runtime type across arbitrary prior statements.
    """
    source = "row.field = 'corrected'\nsession.commit()\n"

    violations = _detect_writes(source, "synthetic.py")

    assert violations == []


@pytest.mark.unit
def test_a_delete_of_an_opaquely_fetched_row_is_a_known_residual_gap() -> None:
    """`session.delete(row)` where `row` was fetched by a query, then
    aliased, rather than directly bound to a `ManualCorrection(...)`
    construction. The binding tracker only follows a DIRECT
    `name = ManualCorrection(...)` assignment; a query result evades it.

    ACCEPTED (SPEC-003 §3.6 G3).
    """
    source = (
        "row = session.query(ManualCorrection).filter_by(id=1).first()\n"
        "other = row\n"
        "session.delete(other)\n"
    )

    violations = _detect_writes(source, "synthetic.py")

    assert violations == []


@pytest.mark.unit
def test_a_second_alias_of_a_tracked_binding_is_a_known_residual_gap() -> None:
    """`x = ManualCorrection(...)` followed by `y = x` then
    `session.delete(y)` — `y = x` is not itself a `ManualCorrection(...)`
    construction (its value is a bare `Name`), so `y` is never added to the
    binding set even though it is, at runtime, the same object `x` names.

    ACCEPTED (SPEC-003 §3.6 G3): closing this would require following an
    arbitrary chain of aliases, which this deliberately single-hop tracker
    does not attempt.
    """
    source = (
        "x = ManualCorrection(occurrence_id=1, field='lemma', corrected_value='x', "
        "corrected_at=None)\n"
        "y = x\n"
        "session.delete(y)\n"
    )

    violations = _detect_writes(source, "synthetic.py")

    assert violations == []


@pytest.mark.unit
def test_a_rebound_tracked_name_is_a_known_false_positive_residual_gap() -> None:
    """`x = ManualCorrection(...)` then `x = object()` (reassigning `x`
    entirely) then `cache.add(x)` — the binding set is built once from the
    whole module body and never narrowed by later control flow, so `x`
    stays "bound" even though it no longer holds a `ManualCorrection` at
    the call site.

    ACCEPTED (SPEC-003 §3.6 G3), on the safe side: an over-approximation,
    never an under-approximation.
    """
    source = (
        "x = ManualCorrection(occurrence_id=1, field='lemma', corrected_value='x', "
        "corrected_at=None)\n"
        "x = object()\n"
        "cache.add(x)\n"
    )

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("ManualCorrection" in v for v in violations)


@pytest.mark.unit
def test_a_reassigned_sqlalchemy_import_name_is_flagged_conservatively() -> None:
    """`from sqlalchemy import insert` then a LATER reassignment
    `insert = some_other_callable` shadows the tracked alias. The alias map
    is static, not flow-sensitive to a later rebinding, so this call is
    still reported even though it may no longer reach `sqlalchemy` at
    runtime.

    ACCEPTED (SPEC-003 §3.6 G3), on the safe side: a write-safety guard
    failing towards "flag it" on an ambiguous case is the correct default.
    """
    source = "from sqlalchemy import insert\ninsert = lambda *a: None\ninsert(ManualCorrection)\n"

    violations = _detect_writes(source, "synthetic.py")

    assert violations
    assert any("insert" in v and "ManualCorrection" in v for v in violations)


# --------------------------------------------------------------------------
# Known gaps introduced or clarified by this rewrite. Each test below calls
# the detector against the uncovered case rather than only asserting a
# label.
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_a_sqlalchemy_submodule_import_evades_alias_resolution() -> None:
    """KNOWN GAP: `_collect_sqlalchemy_call_aliases` requires
    `node.module == "sqlalchemy"` exactly. `from sqlalchemy.sql import
    delete` and `from sqlalchemy.sql.expression import insert` are both
    documented SQLAlchemy import paths and both evade alias resolution.

    ACCEPTED (SPEC-003 §3.6 G3): matching any module path with a
    `sqlalchemy.` prefix risks matching an unrelated package sharing it.
    """
    sources = (
        "from sqlalchemy.sql import delete\ndelete(ManualCorrection)\n",
        "from sqlalchemy.sql.expression import insert\n"
        "insert(ManualCorrection, {'field': 'pos'})\n",
    )

    for source in sources:
        assert _detect_writes(source, "synthetic.py") == [], source


@pytest.mark.unit
def test_a_session_merge_call_is_a_known_residual_gap() -> None:
    """KNOWN GAP: `session.merge(ManualCorrection(...))` is a real
    INSERT-or-UPDATE, and no branch in `_classify_write_call` recognises
    the method name `merge` at all.

    ACCEPTED (SPEC-003 §3.6 G3): not closed by this rewrite.
    """
    source = (
        "session.merge(ManualCorrection(occurrence_id=1, field='lemma', "
        "corrected_value='x', corrected_at=None))\n"
    )

    assert _detect_writes(source, "synthetic.py") == []


@pytest.mark.unit
def test_add_all_with_a_non_list_argument_is_a_known_residual_gap() -> None:
    """KNOWN GAP: `_instance_add_call`'s `add_all` branch requires
    `isinstance(arg, ast.List)`. A tuple or a generator expression carries
    the same meaning to SQLAlchemy and evades it.

    ACCEPTED (SPEC-003 §3.6 G3): every non-list iterable shape was not
    closed in this rewrite.
    """
    sources = (
        "session.add_all((ManualCorrection(occurrence_id=1, field='lemma', "
        "corrected_value='x', corrected_at=None),))\n",
        "session.add_all(c for c in corrections)\n",
    )

    for source in sources:
        assert _detect_writes(source, "synthetic.py") == [], source


@pytest.mark.unit
def test_tuple_and_for_target_bindings_are_known_residual_gaps() -> None:
    """KNOWN GAP: `_manual_correction_bindings` only recognises `Assign`,
    `AnnAssign`, and `NamedExpr` targets that are a single plain `Name`. A
    tuple-unpacking assignment and a `for`-loop target both bind a name to
    a `ManualCorrection` value through a different AST shape and are not
    tracked.

    ACCEPTED (SPEC-003 §3.6 G3): the binding tracker is deliberately a
    single-hop, single-shape tracker.
    """
    sources = (
        "a, b = ManualCorrection(occurrence_id=1, field='lemma', "
        "corrected_value='x', corrected_at=None), 2\nsession.add(a)\n",
        "for c in [ManualCorrection(occurrence_id=1, field='lemma', "
        "corrected_value='x', corrected_at=None)]:\n    session.add(c)\n",
    )

    for source in sources:
        assert _detect_writes(source, "synthetic.py") == [], source


@pytest.mark.unit
def test_raw_sql_adjacency_gaps_evade_the_substring_scan() -> None:
    """KNOWN GAP: `_FORBIDDEN_RAW_SQL` matches exactly three fixed
    fragments. `REPLACE INTO`, `TRUNCATE`, whitespace variants, a quoted or
    schema-qualified table name, and runtime string assembly all reach
    `manual_correction` without ever containing one of the three tracked
    fragments verbatim.

    ACCEPTED (SPEC-003 §3.6 G3): the scan is a fixed substring match, not a
    SQL parser; each case below is a distinct way to spell a write the
    substring match does not recognise.
    """
    sources = (
        'text("REPLACE INTO manual_correction VALUES (1)")\n',
        'text("TRUNCATE manual_correction")\n',
        'text("INSERT  INTO manual_correction VALUES (1)")\n',
        'text("INSERT INTO\\nmanual_correction VALUES (1)")\n',
        "text('DELETE FROM \"manual_correction\" WHERE 1=1')\n",
        'text("DELETE FROM main.manual_correction WHERE 1=1")\n',
        'text("".join(["DELETE FROM ", "manual_correction"]))\n',
        'text("DELETE FROM %s" % "manual_correction")\n',
        "query = f'DELETE FROM {\"manual_correction\"}'\n",
    )

    for source in sources:
        assert _detect_writes(source, "synthetic.py") == [], source

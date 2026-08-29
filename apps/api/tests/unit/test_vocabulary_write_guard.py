"""Structural guard — no module in this capability writes a `ManualCorrection` row (REQ-005-008).

A call is a write when its callee names a write verb — `insert`, `update`,
`delete`, `add`, `add_all`, `merge`, `bulk_insert_mappings`,
`bulk_update_mappings`, matched either on the callee's own bare identifier
or, since round 8, through `_WRITE_VERB_ALIASES` (a write verb imported
under any local name, from any module: `from anywhere import delete as d`
makes `d` resolve to the canonical verb `delete`) — and `ManualCorrection`
(its bare name, a module-local `from ... import ManualCorrection as X`
alias, or, since round 8, a name bound in exactly one assignment hop to a
fresh `ManualCorrection(...)` construction) appears anywhere in that call
expression: an argument, a keyword argument, or the receiver chain. The
receiver's identity, type, or import origin is never inspected —
`delete(...)`, `sa.delete(...)`, `session.delete(...)`,
`anything.delete(...)` all match on the callee's bare name or final
attribute alone
(`test_a_write_call_is_caught_regardless_of_receiver_name`). Walking the
whole call, not just its own argument list, is what catches
`session.query(ManualCorrection).delete()`: the outer callee is `delete`,
and `ManualCorrection` sits in the receiver's nested `query()` call, not
in `delete()`'s own arguments. This closes every ORM-instance idiom a
receiver-type check previously excluded — `session.add`/`.merge`/`.delete`,
`Query.delete`/`.update`, bulk mappings
(`test_session_receiver_idioms_are_now_caught`), and
`ManualCorrection.__table__.delete()`
(`test_table_attribute_write_is_now_caught`) — because none of them
requires knowing what the receiver is, only more AST. `select(...)` reads
stay permitted because `select` is not a write verb (REQ-005-002,
`test_select_and_attribute_reads_are_permitted`).

Also flags raw SQL text matching `insert into`/`update`/`delete
from`/`replace into`/`truncate table manual_correction` (case-insensitive,
`+`-folded, deduplicated so a folded chain is not also counted through its
own sub-expressions), in EVERY string literal including module, class, and
function docstrings — a docstring is runtime-reachable through `__doc__`
(SPEC-003 §3.2 E3; `session.execute(text(__doc__))` would otherwise read
past a prose exemption), so no position is exempt from the scan
(`test_a_docstring_containing_the_forbidden_fragment_is_flagged`). Since
round 8, each of the five verb-forms above is matched by a whitespace-
tolerant regex, not a fixed substring: any run of whitespace between the
verb keyword and the table name (double space, a newline) is accepted, and
an optional surrounding quote character (`"`, `'`, backtick) plus an
optional `schema.` prefix between the verb and `manual_correction` is
accepted too, so `DELETE  FROM manual_correction`, `DELETE\\nFROM
manual_correction`, `DELETE FROM "manual_correction"` and `DELETE FROM
main.manual_correction` are all caught
(`test_the_raw_sql_adjacency_gaps_named_in_the_brief_are_now_closed`).
Dynamic SQL-text assembly — `%`-format substitution, `str.join`, and an
f-string with an interpolated `{...}` placeholder — stays a documented,
unclosed gap: none of these resolve to a literal string in the AST alone
(`test_dynamic_sql_assembly_is_a_documented_gap`). A literal-only f-string
(no `{...}` placeholder) was never actually a gap — Python's own parser
folds it to a plain string constant that the existing literal walk already
finds, with no round-8 change required
(`test_a_placeholder_free_f_string_was_already_caught_before_round_8`).

Scans every `.py` file under `wheel_vocabulary` and every migration (both
`rglob`, no naming convention), exempting `book_repository.py`'s
`DeleteImport` cascade delete (002-text-import) at aggregation, never by
excluding the module from the walk.

Known accepted over-approximations, not narrowed — the callee name and
the `ManualCorrection` name are both matched textually, never resolved to
what they actually refer to:

* Any callable literally named a write verb (bare, or resolved through
  `_WRITE_VERB_ALIASES`) is flagged regardless of what it is — a `cache`
  object's `add`/`delete` methods, or a locally-defined function literally
  named `delete`, all match identically to a real ORM call
  (`test_no_receiver_or_origin_is_verified_a_known_over_approximation`).
  Renaming an UNRELATED import to a write-verb name (`from module import
  unrelated_func as delete`) is flagged the same way, through this same
  bare-identifier path, not through the alias map — `unrelated_func` is
  not a write verb, so it never enters `_WRITE_VERB_ALIASES` at all
  (`test_renaming_an_unrelated_import_to_a_write_verb_name_is_an_over_approximation`).
* A class literally named `ManualCorrection`, imported from ANY module,
  matches identically to the tracked model — its import path is never
  checked (`test_an_unrelated_class_genuinely_named_manual_correction_is_flagged`).
  The same holds for a DIFFERENT class aliased to that exact spelling
  (`from anywhere import Occurrence as ManualCorrection`): the bare
  string `"ManualCorrection"` is always in the matched-name set
  unconditionally, so this import is flagged too, identically
  (`test_an_import_aliasing_a_different_class_to_the_exact_name_is_flagged`).
  Contrast with a DIFFERENT class aliased to a similar-LOOKING but
  non-identical name, which stays unflagged
  (`test_an_unrelated_class_aliased_to_a_similar_name_is_not_flagged`).
* Class-alias resolution is not flow-sensitive: an alias, once imported,
  is treated as `ManualCorrection` even after being rebound to something
  else (`test_a_rebound_class_alias_is_still_treated_as_manual_correction`).
* The one-hop binding tracker (below) inherits the same non-flow-
  sensitivity and the same textual-only class-alias matching; it adds no
  new precision to either.

Known gaps, not closed this round:

* Dynamic SQL-text assembly — `%`-format, `str.join`, and interpolated
  f-strings — is not resolved to a literal string, so a raw-SQL write
  assembled through any of them evades the scan
  (`test_dynamic_sql_assembly_is_a_documented_gap`).
* A write verb imported under a renamed binding is CLOSED as of round 8
  (see above); what remains open is the SAME class of gap one level
  deeper — a write verb reached through a REBOUND local name
  (`d = delete` after `from sqlalchemy import delete`, then `d(...)`) is
  not resolved, because `_WRITE_VERB_ALIASES` reads only `ast.ImportFrom`
  nodes, never a plain `ast.Assign` the way the ManualCorrection-name
  tracker does. Not pinned by a test this round — recorded here only.
* The one-hop binding tracker (`_one_hop_bindings`) follows EXACTLY ONE
  assignment hop from a fresh `ManualCorrection(...)` construction to a
  plain `ast.Name` target, and no further: `correction =
  ManualCorrection(...)` then `alias = correction` then
  `session.add(alias)` evades detection, because `alias`'s own right-hand
  side is a plain `Name`, not a fresh construction — the SECOND hop is
  never walked
  (`test_a_second_assignment_hop_is_the_documented_uncovered_boundary`).
* Tuple/list unpacking assignment targets (`a, b = ManualCorrection(...),
  None`) and `for` loop targets are never tracked by the one-hop binding
  tracker, even where a per-element or per-iteration match with the
  right-hand side would be structurally possible — a deliberate scope
  decision, not an oversight
  (`test_tuple_unpacking_targets_are_a_documented_uncovered_boundary`,
  `test_a_for_loop_target_is_a_documented_uncovered_boundary`).

REQ-005-008, AC-005-08.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

_PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src" / "wheel_vocabulary"
_MIGRATIONS_ROOT = Path(__file__).resolve().parents[2] / "migrations" / "versions"

# Non-vacuity anchors (SPEC-003 §3.3 M2): real files the scan MUST reach, or
# the guard below proves nothing. Not a manifest the scan enumerates FROM —
# `_scanned_modules` walks the filesystem unconditionally.
_EXPECTED_PACKAGE_MODULES = frozenset(
    {
        "infrastructure/persistence/vocabulary_repository.py",
        "infrastructure/persistence/book_repository.py",
        "api/dependencies.py",
        "api/main.py",
    }
)
_EXPECTED_MIGRATIONS = frozenset({"0004_vocabulary_group_index.py"})

# The one documented exemption.
_EXEMPT_WRITE_MODULES: dict[str, str] = {
    "infrastructure/persistence/book_repository.py": (
        "002-text-import: DeleteImport's cascade delete removes "
        "manual_correction rows for a deleted book's occurrences, so a "
        "later import that reuses the freed Occurrence.id never inherits "
        "a ghost correction it never made."
    ),
}

_WRITE_VERBS = frozenset(
    {
        "insert",
        "update",
        "delete",
        "add",
        "add_all",
        "merge",
        "bulk_insert_mappings",
        "bulk_update_mappings",
    }
)
_FORBIDDEN_RAW_SQL = (
    "insert into manual_correction",
    "update manual_correction",
    "delete from manual_correction",
    "replace into manual_correction",
    "truncate table manual_correction",
)

# One whitespace-tolerant, quote-tolerant, schema-prefix-tolerant regex per
# forbidden fragment above, keyed identically so `_FORBIDDEN_RAW_SQL` stays
# the single list a mutation drops an element from. `\s+` accepts a double
# space or a newline between the verb keyword and the object reference;
# `["'`]?` accepts an optional surrounding quote character; `(?:\w+\.)?`
# accepts an optional `schema.` prefix. No trailing boundary is required
# after `manual_correction` — like the substring match it replaces, a
# longer table name that merely starts with `manual_correction` (e.g. a
# hypothetical `manual_correction_backup`) still matches; this widening is
# unchanged from before round 8, not a new over-approximation. Dynamic
# assembly — `%`-format, `str.join`, an interpolated f-string — is NOT
# resolved by this regex or by anything else in this module; see the
# module docstring's Known-gaps section.
_RAW_SQL_PATTERNS: dict[str, re.Pattern[str]] = {
    "insert into manual_correction": re.compile(
        r"insert\s+into\s+[\"'`]?(?:\w+\.)?[\"'`]?manual_correction", re.IGNORECASE
    ),
    "update manual_correction": re.compile(
        r"update\s+[\"'`]?(?:\w+\.)?[\"'`]?manual_correction", re.IGNORECASE
    ),
    "delete from manual_correction": re.compile(
        r"delete\s+from\s+[\"'`]?(?:\w+\.)?[\"'`]?manual_correction", re.IGNORECASE
    ),
    "replace into manual_correction": re.compile(
        r"replace\s+into\s+[\"'`]?(?:\w+\.)?[\"'`]?manual_correction", re.IGNORECASE
    ),
    "truncate table manual_correction": re.compile(
        r"truncate\s+table\s+[\"'`]?(?:\w+\.)?[\"'`]?manual_correction", re.IGNORECASE
    ),
}


def _folded_string(node: ast.AST) -> str | None:
    """Constant-fold a chain of string-literal `+` concatenations."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _folded_string(node.left), _folded_string(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def _string_literals(tree: ast.AST) -> list[str]:
    """Every string literal in `tree`, including `+`-folded chains. A
    folded chain is collected once, at its outermost `BinOp`; its
    constituent sub-expressions are then skipped so the same source text
    is never counted a second time through its own parts. No position is
    exempt — a module, class or function docstring is scanned exactly
    like any other string constant (see the module docstring)."""
    literals: list[str] = []
    consumed: set[int] = set()
    for node in ast.walk(tree):
        if id(node) in consumed:
            continue
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            literals.append(node.value)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            folded = _folded_string(node)
            if folded is not None:
                literals.append(folded)
                consumed.update(id(child) for child in ast.walk(node) if child is not node)
    return literals


def _write_verb_aliases(tree: ast.AST) -> dict[str, str]:
    """Local names bound to a write verb through `from ... import X as Y`
    (or the bare `from ... import X`, where `Y` is `X` itself), keyed on
    the imported symbol's ORIGINAL name being a write verb — the module
    the import comes from is never inspected. `from sqlalchemy import
    delete as sa_delete` maps `sa_delete` to the canonical verb `delete`;
    `from anywhere import delete as d` maps `d` to `delete` identically,
    because only `alias.name` (the name as written at the import site) is
    checked against `_WRITE_VERBS`, never `node.module`. An import whose
    ORIGINAL name is NOT a write verb never enters this map, even if its
    local alias happens to spell one (`from module import unrelated_func
    as delete`) — that call is still flagged, but through the existing
    bare-identifier path in `_call_write_verb`, not through this map."""
    return {
        alias.asname or alias.name: alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
        if alias.name in _WRITE_VERBS
    }


def _manual_correction_aliases(tree: ast.AST) -> frozenset[str]:
    """Names treated as naming the `ManualCorrection` class. ALWAYS
    includes the bare string `"ManualCorrection"` unconditionally,
    regardless of what that name actually resolves to in `tree` — a
    completely UNRELATED class imported under that exact spelling
    (`from anywhere import Occurrence as ManualCorrection`) is an
    `ImportFrom` whose local name is spelled `ManualCorrection`, and it
    is flagged identically to the real model, because this function never
    inspects what a name is bound to, only its literal spelling (a known
    over-approximation, pinned by
    `test_an_import_aliasing_a_different_class_to_the_exact_name_is_flagged`).
    Contrast with `from anywhere import Occurrence as ManualCorrectionLike`:
    the LOCAL spelling there is `ManualCorrectionLike`, not
    `ManualCorrection`, so it stays unmatched
    (`test_an_unrelated_class_aliased_to_a_similar_name_is_not_flagged`).
    Also includes every local name the real `ManualCorrection` symbol
    (imported from ANY module, origin never checked) is itself aliased
    to, via `from ... import ManualCorrection as X` — this is a SEPARATE
    addition to the set, not a gate on the bare string above, which is
    seeded regardless of whether this second form of import exists at
    all."""
    aliases = {
        alias.asname
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
        if alias.name == "ManualCorrection" and alias.asname is not None
    }
    return frozenset({"ManualCorrection", *aliases})


def _one_hop_bindings(tree: ast.AST, class_aliases: frozenset[str]) -> frozenset[str]:
    """Names bound, in EXACTLY ONE assignment hop, to a fresh
    `ManualCorrection(...)` construction — `ast.Assign`, `ast.AnnAssign`
    and `ast.NamedExpr` targets whose right-hand side is directly a call
    naming `ManualCorrection` (bare or import-aliased). Only a single,
    plain `ast.Name` target is tracked: `a = b = ManualCorrection(...)`
    binds both `a` and `b`, because each is its own plain-`Name` target
    on the SAME one-hop assignment, not a second hop off the other.
    Tuple/list unpacking targets (`a, b = ManualCorrection(...), None`)
    and `for` loop targets are NEVER tracked, even where a per-element or
    per-iteration match would be structurally possible — a deliberate
    scope decision to avoid a partial pairwise resolver
    (`test_tuple_unpacking_targets_are_a_documented_uncovered_boundary`,
    `test_a_for_loop_target_is_a_documented_uncovered_boundary`). A
    SECOND hop — `alias = correction`, where `correction` is already
    one-hop bound — is never followed: only the assignment's own
    right-hand side is inspected, never a name looked up transitively
    through this same map
    (`test_a_second_assignment_hop_is_the_documented_uncovered_boundary`)."""
    bindings: set[str] = set()

    def _register(target: ast.expr, value: ast.expr) -> None:
        if (
            isinstance(target, ast.Name)
            and isinstance(value, ast.Call)
            and _names_manual_correction(value.func, class_aliases)
        ):
            bindings.add(target.id)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for assign_target in node.targets:
                _register(assign_target, node.value)
        elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)) and node.value is not None:
            _register(node.target, node.value)

    return frozenset(bindings)


def _names_manual_correction(node: ast.AST, resolved_names: frozenset[str]) -> bool:
    """True for a `Name` whose identifier is in `resolved_names` — a set
    that may be import-derived class aliases alone, or that plus one-hop
    binding names, depending on what the caller passes — or an
    `Attribute` access ending in the bare class name."""
    if isinstance(node, ast.Name):
        return node.id in resolved_names
    return isinstance(node, ast.Attribute) and node.attr == "ManualCorrection"


def _call_write_verb(call: ast.Call, verb_aliases: dict[str, str]) -> str | None:
    """The write verb `call`'s callee names, or `None`. A bare `Name`
    callee matches its own literal identifier (`delete(...)`) directly
    against `_WRITE_VERBS`, or, failing that, resolves through
    `verb_aliases` (`sa_delete(...)` after `from sqlalchemy import delete
    as sa_delete`) to the canonical verb it was imported as. An
    `Attribute` callee matches its final attribute regardless of the
    receiver (`session.delete(...)`, `sa.delete(...)`, `anything.delete(...)`
    all match on `.attr` alone) — the receiver's identity, type or origin
    is never inspected, and `verb_aliases` is never consulted for an
    `Attribute` callee, because an attribute access cannot itself be the
    target of an import alias."""
    func = call.func
    if isinstance(func, ast.Name):
        if func.id in _WRITE_VERBS:
            return func.id
        return verb_aliases.get(func.id)
    if isinstance(func, ast.Attribute):
        return func.attr if func.attr in _WRITE_VERBS else None
    return None


def _call_names_manual_correction(call: ast.Call, resolved_names: frozenset[str]) -> bool:
    """True if a name in `resolved_names` (class aliases, one-hop
    bindings, or both — the caller decides which set to pass) appears
    anywhere inside `call` — positional/keyword arguments, or the
    receiver chain. Walking the whole call, not just its argument list,
    is what makes `session.query(ManualCorrection).delete()` match: the
    outer callee is `delete`, and `ManualCorrection` is an argument of
    the nested `query()` call inside the receiver, not of `delete()`
    itself."""
    return any(_names_manual_correction(node, resolved_names) for node in ast.walk(call))


def _detect_writes(source: str, label: str) -> list[str]:
    """Every write targeting `manual_correction` in `source`: a call whose
    callee names a write verb (bare, or resolved through
    `_write_verb_aliases`) and whose call expression names
    `ManualCorrection` anywhere (argument, keyword, receiver chain, or a
    name one-hop bound to a fresh `ManualCorrection(...)` construction),
    or raw SQL text naming the table after an
    INSERT/UPDATE/DELETE/REPLACE/TRUNCATE keyword (case-insensitive,
    whitespace-, quote- and schema-prefix-tolerant, `+`-folded, no
    position exempt)."""
    tree = ast.parse(source, filename=label)
    class_aliases = _manual_correction_aliases(tree)
    resolved_names = class_aliases | _one_hop_bindings(tree, class_aliases)
    verb_aliases = _write_verb_aliases(tree)
    violations: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            verb = _call_write_verb(node, verb_aliases)
            if verb is not None and _call_names_manual_correction(node, resolved_names):
                violations.append(f"{label}:{node.lineno} {verb}(ManualCorrection)")

    for literal in _string_literals(tree):
        for fragment in _FORBIDDEN_RAW_SQL:
            if _RAW_SQL_PATTERNS[fragment].search(literal):
                violations.append(f"{label} raw SQL fragment {fragment!r}")

    return violations


def _scanned_modules(
    package_root: Path = _PACKAGE_ROOT, migrations_root: Path = _MIGRATIONS_ROOT
) -> list[tuple[Path, str]]:
    """Every `.py` file under `package_root` and `migrations_root`, both
    walked recursively (`rglob`), unconditionally: no naming convention."""
    modules = [
        (path, path.relative_to(package_root).as_posix())
        for path in sorted(package_root.rglob("*.py"))
    ]
    modules += [
        (path, f"migrations/versions/{path.relative_to(migrations_root).as_posix()}")
        for path in sorted(migrations_root.rglob("*.py"))
    ]
    return modules


def _write_violations(
    modules: list[tuple[Path, str]] | None = None,
    exempt: dict[str, str] | None = None,
) -> list[str]:
    """Run `_detect_writes` over every scanned module except those named in
    `exempt` (default: the real `_EXEMPT_WRITE_MODULES`)."""
    scan = _scanned_modules() if modules is None else modules
    active_exempt = _EXEMPT_WRITE_MODULES if exempt is None else exempt
    return [
        violation
        for path, label in scan
        if label not in active_exempt
        for violation in _detect_writes(path.read_text(encoding="utf-8"), label)
    ]


# --------------------------------------------------------------------------
# Non-vacuity and the unconditional walk.
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_the_scan_reaches_every_expected_module() -> None:
    """Non-vacuity (SPEC-003 §3.3 M2): the real walk reaches every anchor."""
    scanned = {label for _, label in _scanned_modules()}
    missing_migrations = {f"migrations/versions/{name}" for name in _EXPECTED_MIGRATIONS}

    assert not (_EXPECTED_PACKAGE_MODULES - scanned)
    assert not (missing_migrations - scanned)


@pytest.mark.unit
@pytest.mark.parametrize("missing", sorted(_EXPECTED_PACKAGE_MODULES))
def test_the_scan_fails_closed_when_an_anchor_is_missing(tmp_path: Path, missing: str) -> None:
    """SPEC-003 §3.3 M2, per anchor: a tree missing exactly one named anchor
    must fail `scanned >= _EXPECTED_PACKAGE_MODULES`."""
    package_root = tmp_path / "pkg"
    migrations_root = tmp_path / "migrations"
    migrations_root.mkdir()
    for present in _EXPECTED_PACKAGE_MODULES - {missing}:
        target = package_root / present
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("x = 1\n", encoding="utf-8")

    scanned = {label for _, label in _scanned_modules(package_root, migrations_root)}

    assert not (scanned >= _EXPECTED_PACKAGE_MODULES)


@pytest.mark.unit
def test_the_scan_reaches_a_module_with_no_vocabulary_token_in_its_path(tmp_path: Path) -> None:
    """No naming convention: a module with no `"vocabulary"` token in its
    path is still scanned."""
    package_root = tmp_path / "wheel_vocabulary"
    (package_root / "api" / "dtos").mkdir(parents=True)
    (package_root / "api" / "dtos" / "groups.py").write_text("x = 1\n", encoding="utf-8")
    migrations_root = tmp_path / "migrations"
    migrations_root.mkdir()

    scanned = {label for _, label in _scanned_modules(package_root, migrations_root)}

    assert "api/dtos/groups.py" in scanned


@pytest.mark.unit
def test_the_scan_reaches_a_nested_migration(tmp_path: Path) -> None:
    """The migrations root is walked with `rglob`, not `glob`: a migration
    one directory deeper than today's flat layout is still reached."""
    package_root = tmp_path / "wheel_vocabulary"
    package_root.mkdir()
    migrations_root = tmp_path / "migrations"
    (migrations_root / "archived").mkdir(parents=True)
    (migrations_root / "archived" / "0000_old.py").write_text("x = 1\n", encoding="utf-8")

    scanned = {label for _, label in _scanned_modules(package_root, migrations_root)}

    assert "migrations/versions/archived/0000_old.py" in scanned


# --------------------------------------------------------------------------
# The exemption mechanism.
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_the_exempt_set_is_exactly_book_repository() -> None:
    """The exempt set names exactly one module. This does not prove it is
    impossible to exempt another — it proves any addition requires
    deliberately editing this assertion, which forces review."""
    assert set(_EXEMPT_WRITE_MODULES) == {"infrastructure/persistence/book_repository.py"}


@pytest.mark.unit
def test_the_exemption_hides_a_genuine_write() -> None:
    """MUTATION CHECK: ran `_detect_writes` against the real
    `book_repository.py` source and observed::

        ['infrastructure/persistence/book_repository.py:144 delete(ManualCorrection)']
    """
    path, label = next(
        (p, lbl)
        for p, lbl in _scanned_modules()
        if lbl == "infrastructure/persistence/book_repository.py"
    )

    violations = _detect_writes(path.read_text(encoding="utf-8"), label)

    assert violations == [
        "infrastructure/persistence/book_repository.py:144 delete(ManualCorrection)"
    ]


@pytest.mark.unit
def test_emptying_the_exempt_set_fails_through_write_violations() -> None:
    """M3, through aggregation, not a direct `_detect_writes` call — a prior
    round's control bypassed aggregation and passed against a mutant that
    suppressed the whole default scan.

    MUTATION CHECK: ran `_write_violations(exempt={})` and observed::

        ['infrastructure/persistence/book_repository.py:144 delete(ManualCorrection)']
    """
    violations = _write_violations(exempt={})

    assert violations == [
        "infrastructure/persistence/book_repository.py:144 delete(ManualCorrection)"
    ]


@pytest.mark.unit
def test_the_exemption_boundary_holds_through_write_violations(tmp_path: Path) -> None:
    """M3 boundary: the same write placed outside the exempt set still
    violates, through `_write_violations`'s aggregation path."""
    outside = tmp_path / "other_module.py"
    outside.write_text("delete(ManualCorrection)\n", encoding="utf-8")

    violations = _write_violations(modules=[(outside, "some/other/module.py")])

    assert violations
    assert any("some/other/module.py" in v for v in violations)


# --------------------------------------------------------------------------
# The main guard and its mutation checks.
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_no_module_writes_to_manual_correction() -> None:
    """REQ-005-008 / AC-005-08 scenario 1, exemption applied."""
    violations = _write_violations()

    assert not violations, "a module writes to manual_correction:\n" + "\n".join(violations)


@pytest.mark.unit
def test_writes_appended_to_the_vocabulary_repository_are_caught() -> None:
    """AC-005-08 scenario 3, literal wording: an insert against
    `ManualCorrection`, then a delete against it, each appended in turn to
    the real `vocabulary_repository.py` source.

    MUTATION CHECK: ran `_detect_writes` against each mutated source.
    `vocabulary_repository.py` is 181 lines and ends with a trailing
    newline, so the appended `"\\n" + statement + "\\n"` lands the
    statement on line 183 (one blank line from the append, then the
    statement) — re-derived by execution against THIS round's file, not
    copied from a prior round's recorded output, which had drifted to
    :184 without the file ever changing length.

    insert::

    ['infrastructure/persistence/vocabulary_repository.py:183 insert(ManualCorrection)']

    delete::

    ['infrastructure/persistence/vocabulary_repository.py:183 delete(ManualCorrection)']
    """
    path = _PACKAGE_ROOT / "infrastructure" / "persistence" / "vocabulary_repository.py"
    original = path.read_text(encoding="utf-8")
    label = "infrastructure/persistence/vocabulary_repository.py"
    with_insert = original + "\ninsert(ManualCorrection, {'field': 'lemma'})\n"
    with_delete = original + "\ndelete(ManualCorrection)\n"

    insert_violations = _detect_writes(with_insert, label)
    delete_violations = _detect_writes(with_delete, label)

    assert insert_violations == [f"{label}:183 insert(ManualCorrection)"]
    assert delete_violations == [f"{label}:183 delete(ManualCorrection)"]


@pytest.mark.unit
def test_select_and_attribute_reads_are_permitted() -> None:
    """AMB-3 / REQ-005-002: `select(ManualCorrection...)` and a
    `ManualCorrection.field` attribute read are not violations — `select`
    is not in `_WRITE_VERBS`."""
    source = (
        "from sqlalchemy import select\n"
        "stmt = select(ManualCorrection.occurrence_id, ManualCorrection.field)\n"
    )

    assert _detect_writes(source, "synthetic.py") == []


@pytest.mark.unit
@pytest.mark.parametrize(
    "source",
    [
        "delete(ManualCorrection)\n",
        "sa.delete(ManualCorrection)\n",
        "session.delete(ManualCorrection)\n",
        "anything.delete(ManualCorrection)\n",
    ],
    ids=["bare name", "sa.delete", "session.delete", "anything.delete"],
)
def test_a_write_call_is_caught_regardless_of_receiver_name(source: str) -> None:
    """The receiver is never inspected: a bare callee and three different
    attribute receivers all resolve to the same write, `delete`, because
    only the callee's own final name is matched."""
    assert _detect_writes(source, "synthetic.py") == ["synthetic.py:1 delete(ManualCorrection)"]


@pytest.mark.unit
def test_a_renamed_write_verb_import_is_now_caught() -> None:
    """CLOSED (round 8): `_write_verb_aliases` is keyed on the imported
    symbol's ORIGINAL name being a write verb, never on which module it
    came from — `from sqlalchemy import delete as sa_delete` maps
    `sa_delete` to the canonical verb `delete`, so
    `sa_delete(ManualCorrection)` is now caught, reported under its
    canonical name."""
    source = "from sqlalchemy import delete as sa_delete\nsa_delete(ManualCorrection)\n"

    assert _detect_writes(source, "synthetic.py") == ["synthetic.py:2 delete(ManualCorrection)"]


@pytest.mark.unit
@pytest.mark.parametrize(
    # Hardcoded, not `sorted(_WRITE_VERBS)`: the parametrize list must stay
    # fixed independently of the constant under test (see
    # `test_every_write_verb_is_caught_bare`'s identical rationale).
    "verb",
    [
        "add",
        "add_all",
        "bulk_insert_mappings",
        "bulk_update_mappings",
        "delete",
        "insert",
        "merge",
        "update",
    ],
)
def test_every_write_verb_is_caught_under_a_renamed_import(verb: str) -> None:
    """MUTATION CHECK: each of the 8 write verbs, imported under an
    unrelated local alias from an arbitrary (non-`sqlalchemy`) module, is
    still caught — origin is never checked, only the imported symbol's
    original spelling. Dropping any single element from `_WRITE_VERBS`
    makes exactly its own parametrized case here return `[]`, the same as
    it does for the bare-name mutation matrix."""
    source = f"from anywhere import {verb} as renamed_verb\nrenamed_verb(ManualCorrection)\n"

    assert _detect_writes(source, "synthetic.py") == [f"synthetic.py:2 {verb}(ManualCorrection)"]


@pytest.mark.unit
def test_renaming_an_unrelated_import_to_a_write_verb_name_is_an_over_approximation() -> None:
    """The alias map is keyed on the ORIGINAL imported name, not the
    local alias: `from module import unrelated_func as delete` does NOT
    enter `_write_verb_aliases` — `unrelated_func` is not a write verb —
    but the call is still flagged, because the local name `delete`
    matches `_WRITE_VERBS` directly through the pre-existing bare-name
    path, the same over-approximation `cache.delete(...)` and a
    locally-defined `delete` function already exercise."""
    source = "from module import unrelated_func as delete\ndelete(ManualCorrection)\n"

    assert _detect_writes(source, "synthetic.py") == ["synthetic.py:2 delete(ManualCorrection)"]


@pytest.mark.unit
@pytest.mark.parametrize(
    "verb",
    # Hardcoded, not `sorted(_WRITE_VERBS)`: the parametrize list must stay
    # fixed independently of the constant under test, or dropping an
    # element from `_WRITE_VERBS` would also drop its own parametrized
    # case from collection instead of failing it.
    [
        "add",
        "add_all",
        "bulk_insert_mappings",
        "bulk_update_mappings",
        "delete",
        "insert",
        "merge",
        "update",
    ],
)
def test_every_write_verb_is_caught_bare(verb: str) -> None:
    """MUTATION CHECK: `_WRITE_VERBS` has 8 elements; dropping any single
    one makes exactly its own parametrized case return `[]` instead of a
    violation. Ran the matrix with each element removed in turn and
    confirmed only that element's case failed, the other 7 stayed green."""
    violations = _detect_writes(f"{verb}(ManualCorrection)\n", "synthetic.py")

    assert violations == [f"synthetic.py:1 {verb}(ManualCorrection)"]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            "session.add(ManualCorrection(occurrence_id=1))\n",
            "synthetic.py:1 add(ManualCorrection)",
        ),
        (
            "session.merge(ManualCorrection(occurrence_id=1))\n",
            "synthetic.py:1 merge(ManualCorrection)",
        ),
        (
            "session.query(ManualCorrection).delete()\n",
            "synthetic.py:1 delete(ManualCorrection)",
        ),
        (
            "session.bulk_insert_mappings(ManualCorrection, rows)\n",
            "synthetic.py:1 bulk_insert_mappings(ManualCorrection)",
        ),
    ],
    ids=["session.add", "session.merge", "Query.delete", "bulk_insert_mappings"],
)
def test_session_receiver_idioms_are_now_caught(source: str, expected: str) -> None:
    """Rounds 1-4 excluded these four idioms because verifying the
    receiver is a `Session` requires type inference an AST pass cannot
    do. This rule never asks: the outer callee names a write verb, and
    `ManualCorrection` is in the call expression (directly, or through
    the nested `query()` call in `Query.delete`'s receiver chain)."""
    assert _detect_writes(source, "synthetic.py") == [expected]


@pytest.mark.unit
def test_table_attribute_write_is_now_caught() -> None:
    """`ManualCorrection.__table__.delete()` closes the same way
    `Query.delete` does: the outer callee is `delete`, and
    `ManualCorrection` sits in the receiver's attribute chain."""
    assert _detect_writes("ManualCorrection.__table__.delete()\n", "synthetic.py") == [
        "synthetic.py:1 delete(ManualCorrection)"
    ]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("fragment", "sql"),
    [
        ("insert into manual_correction", "INSERT INTO manual_correction VALUES (1)"),
        ("update manual_correction", "UPDATE manual_correction SET field=1"),
        ("delete from manual_correction", "DELETE FROM manual_correction WHERE 1=1"),
        ("replace into manual_correction", "REPLACE INTO manual_correction VALUES (1)"),
        ("truncate table manual_correction", "TRUNCATE TABLE manual_correction"),
    ],
    # Hardcoded, not derived from `_FORBIDDEN_RAW_SQL`: the parametrize list
    # must stay fixed independently of the constant under test, or dropping
    # an element from `_FORBIDDEN_RAW_SQL` would also drop its own
    # parametrized case from collection instead of failing it.
    ids=["insert", "update", "delete", "replace", "truncate"],
)
def test_every_raw_sql_fragment_is_caught(fragment: str, sql: str) -> None:
    """MUTATION CHECK: `_FORBIDDEN_RAW_SQL` has 5 elements; dropping any
    single one makes exactly its own parametrized case return `[]`. Ran
    the matrix with each element removed in turn and confirmed only that
    element's case failed, the other 4 stayed green."""
    violations = _detect_writes(f'text("{sql}")\n', "synthetic.py")

    assert violations == [f"synthetic.py raw SQL fragment {fragment!r}"]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("fragment", "source"),
    [
        ("delete from manual_correction", 'text("DELETE  FROM manual_correction VALUES (1)")\n'),
        ("delete from manual_correction", 'text("DELETE\\nFROM manual_correction")\n'),
        (
            "delete from manual_correction",
            "text('DELETE FROM \"manual_correction\" WHERE 1=1')\n",
        ),
        ("delete from manual_correction", 'text("DELETE FROM main.manual_correction")\n'),
        (
            "replace into manual_correction",
            'text("REPLACE INTO manual_correction VALUES (1)")\n',
        ),
        ("truncate table manual_correction", 'text("TRUNCATE TABLE manual_correction")\n'),
    ],
    ids=["double space", "newline", "quoted", "schema-qualified", "replace into", "truncate table"],
)
def test_the_raw_sql_adjacency_gaps_named_in_the_brief_are_now_closed(
    fragment: str, source: str
) -> None:
    """CLOSED (round 8): all six variants named in the round-8 brief —
    double space, a newline, a quoted table name, a `main.`-qualified
    table name, `REPLACE INTO`, and `TRUNCATE TABLE` — were verified by
    execution to return `[]` against the pre-round-8 detector; each now
    produces exactly one violation against the shipped
    `_RAW_SQL_PATTERNS` regex."""
    assert _detect_writes(source, "synthetic.py") == [f"synthetic.py raw SQL fragment {fragment!r}"]


@pytest.mark.unit
@pytest.mark.parametrize(
    "source",
    [
        'text("DELETE FROM %s" % "manual_correction")\n',
        'text(" ".join(["DELETE", "FROM", "manual_correction"]))\n',
        'text(f"DELETE FROM {table_name}")\n',
    ],
    ids=["percent-format", "str.join", "interpolated f-string"],
)
def test_dynamic_sql_assembly_is_a_documented_gap(source: str) -> None:
    """KNOWN GAP, not closed this round: none of `%`-format substitution,
    `str.join`, or an f-string with an interpolated `{...}` placeholder
    resolves to a literal string constant in the AST — closing any of
    them would require simulating runtime string semantics, the same
    category of complexity this module's docstring already declines for
    the binding tracker and the write-verb alias map."""
    assert _detect_writes(source, "synthetic.py") == []


@pytest.mark.unit
def test_a_placeholder_free_f_string_was_already_caught_before_round_8() -> None:
    """NOT a round-8 change: an f-string with no `{...}` placeholder
    compiles to a plain `ast.Constant` string value inside the
    `ast.JoinedStr` wrapper (verified against this project's Python
    version), and `_string_literals`'s `ast.walk` already finds that
    inner constant regardless of the wrapper — confirmed against the
    pre-round-8 detector before this round began, unchanged since."""
    assert _detect_writes('text(f"DELETE FROM manual_correction")\n', "synthetic.py") == [
        "synthetic.py raw SQL fragment 'delete from manual_correction'"
    ]


# --------------------------------------------------------------------------
# Round 5 (Judgment Day): class aliasing and a folded-chain deduplication
# fix. Both mechanisms are unchanged by the round-6 rule rewrite below.
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_a_write_call_through_a_class_alias_is_caught() -> None:
    """JD-A4: `from ... import ManualCorrection as MC` then `delete(MC)`
    used to evade detection entirely — `_names_manual_correction` matched
    only the literal identifier `ManualCorrection`. Class aliases resolve
    through `_manual_correction_aliases`."""
    source = (
        "from wheel_vocabulary.infrastructure.persistence.models import ManualCorrection as MC\n"
        "delete(MC)\n"
    )

    assert _detect_writes(source, "synthetic.py") == ["synthetic.py:2 delete(ManualCorrection)"]


@pytest.mark.unit
def test_an_unrelated_class_aliased_to_a_similar_name_is_not_flagged() -> None:
    """False-positive control for the class-alias mechanism: importing a
    DIFFERENT class under a name that merely LOOKS related (a different
    spelling, `ManualCorrectionLike`) is never mistaken for
    `ManualCorrection` — the bare-string seed only matches the EXACT
    spelling `ManualCorrection`, and this import's local name is spelled
    differently."""
    source = (
        "from wheel_vocabulary.infrastructure.persistence.models "
        "import Occurrence as ManualCorrectionLike\n"
        "delete(ManualCorrectionLike)\n"
    )

    assert _detect_writes(source, "synthetic.py") == []


@pytest.mark.unit
def test_an_import_aliasing_a_different_class_to_the_exact_name_is_flagged() -> None:
    """KNOWN ACCEPTED OVER-APPROXIMATION, corrects a prior docstring claim
    that this could not happen: `from elsewhere import Occurrence as
    ManualCorrection` is an `ImportFrom` whose LOCAL name is spelled
    exactly `ManualCorrection`. `_manual_correction_aliases` never checks
    what that name resolves to — it seeds its returned set with the bare
    string `"ManualCorrection"` unconditionally — so this import is
    flagged identically to a real `ManualCorrection` reference, contrary
    to what an earlier revision of this module's docstring asserted."""
    source = "from elsewhere import Occurrence as ManualCorrection\ndelete(ManualCorrection)\n"

    assert _detect_writes(source, "synthetic.py") == ["synthetic.py:2 delete(ManualCorrection)"]


@pytest.mark.unit
def test_a_folded_chain_is_reported_once_not_once_per_sub_expression() -> None:
    """JD-A5 (Judge A): `"a" + "insert into manual_correction" + "b"` used
    to report three times for one write statement — the outer fold, the
    inner fold, and the bare inner constant were each collected
    independently by `_string_literals`. The outermost fold is now the
    only literal collected from a chain; its sub-expressions are
    consumed, not re-walked."""
    source = 'x = "a" + "insert into manual_correction" + "b"\n'

    assert _detect_writes(source, "synthetic.py") == [
        "synthetic.py raw SQL fragment 'insert into manual_correction'"
    ]


# --------------------------------------------------------------------------
# Round 6 (Judgment Day): the callee-name/receiver-chain rule replaces the
# receiver-origin checks; the docstring exclusion from the raw-SQL scan is
# removed.
# --------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize(
    "source",
    [
        '"""DELETE FROM manual_correction WHERE id=1"""\n',
        'class Payload:\n    """DELETE FROM manual_correction WHERE id=1"""\n',
        'def f() -> None:\n    """DELETE FROM manual_correction WHERE id=1"""\n',
    ],
    ids=["module docstring", "class docstring", "function docstring"],
)
def test_a_docstring_containing_the_forbidden_fragment_is_flagged(source: str) -> None:
    """Round 5 excluded module/class/function docstrings from the raw-SQL
    scan to stop prose being flagged. That created a false negative:
    `session.execute(text(__doc__))` reads a docstring at runtime, so
    excluding docstrings from the scan let a real DELETE statement hide
    as documentation (SPEC-003 §3.2 E3). The exclusion is removed — a
    docstring is scanned exactly like any other string literal.

    MUTATION CHECK: ran `_detect_writes` against each variant and
    observed, for all three::

        ["synthetic.py raw SQL fragment 'delete from manual_correction'"]
    """
    violations = _detect_writes(source, "synthetic.py")

    assert violations == ["synthetic.py raw SQL fragment 'delete from manual_correction'"]


@pytest.mark.unit
def test_a_docstring_mentioning_manual_correction_stays_permitted_without_the_fragment() -> None:
    """The scan is a substring match, not a semantic one: prose that names
    `manual_correction` without the exact `verb + table` fragment stays
    permitted."""
    source = '"""We document manual_correction rows here."""\n'

    assert _detect_writes(source, "synthetic.py") == []


@pytest.mark.unit
@pytest.mark.parametrize(
    "source",
    [
        "cache.add(ManualCorrection())\n",
        "cache.delete(ManualCorrection)\n",
        "def delete(x):\n    return x\n\n\ndelete(ManualCorrection)\n",
    ],
    ids=["cache.add", "cache.delete", "locally-defined delete"],
)
def test_no_receiver_or_origin_is_verified_a_known_over_approximation(source: str) -> None:
    """KNOWN ACCEPTED OVER-APPROXIMATION: the callee name is matched
    textually, never resolved to what it refers to. A `cache` object with
    `add`/`delete` methods, or a locally-defined function literally named
    `delete`, is flagged identically to a real ORM/`sqlalchemy` call —
    this is the deliberate cost of dropping the receiver-origin checks
    three Judgment Day rounds falsified."""
    assert _detect_writes(source, "synthetic.py") != []


@pytest.mark.unit
def test_an_unrelated_class_genuinely_named_manual_correction_is_flagged() -> None:
    """KNOWN ACCEPTED OVER-APPROXIMATION: `ManualCorrection`'s import path
    is never checked — a class of the same name imported from a
    completely unrelated module matches identically to the tracked model.
    Contrast with `test_an_unrelated_class_aliased_to_a_similar_name_is_not_flagged`,
    where a DIFFERENT class is merely aliased to a similar-looking name
    and correctly stays unflagged."""
    source = "from some_other_package.models import ManualCorrection\ndelete(ManualCorrection)\n"

    assert _detect_writes(source, "synthetic.py") == ["synthetic.py:2 delete(ManualCorrection)"]


@pytest.mark.unit
def test_a_rebound_class_alias_is_still_treated_as_manual_correction() -> None:
    """KNOWN ACCEPTED OVER-APPROXIMATION: class-alias resolution is not
    flow-sensitive. `_manual_correction_aliases` collects the import
    statement alone; `MC` being rebound to an unrelated object afterward
    is invisible to it, so `delete(MC)` is still reported."""
    source = (
        "from wheel_vocabulary.infrastructure.persistence.models import ManualCorrection as MC\n"
        "MC = object()\n"
        "delete(MC)\n"
    )

    assert _detect_writes(source, "synthetic.py") != []


@pytest.mark.unit
def test_a_binding_constructed_elsewhere_then_passed_is_now_caught() -> None:
    """CLOSED (round 8): the one-hop binding tracker resolves
    `correction = ManualCorrection(...)` followed by
    `session.add(correction)` on a later line — `correction`'s own
    right-hand side is a direct `ManualCorrection` construction, so it
    enters the resolved-name set exactly like a class alias."""
    source = "correction = ManualCorrection(occurrence_id=1)\nsession.add(correction)\n"

    assert _detect_writes(source, "synthetic.py") == ["synthetic.py:2 add(ManualCorrection)"]


@pytest.mark.unit
def test_an_annotated_assignment_binding_is_caught() -> None:
    """`ast.AnnAssign` is tracked the same way as `ast.Assign`."""
    source = "correction: object = ManualCorrection(occurrence_id=1)\nsession.add(correction)\n"

    assert _detect_writes(source, "synthetic.py") == ["synthetic.py:2 add(ManualCorrection)"]


@pytest.mark.unit
def test_a_walrus_binding_is_caught() -> None:
    """`ast.NamedExpr` (`:=`) is tracked the same way as `ast.Assign`."""
    source = "if (correction := ManualCorrection(occurrence_id=1)):\n    session.add(correction)\n"

    assert _detect_writes(source, "synthetic.py") == ["synthetic.py:2 add(ManualCorrection)"]


@pytest.mark.unit
def test_a_chained_assignment_binds_every_plain_name_target() -> None:
    """`a = b = ManualCorrection(...)` is ONE assignment with two plain
    `Name` targets sharing the same one-hop right-hand side; both enter
    the resolved-name set, not just the first."""
    source = "a = b = ManualCorrection(occurrence_id=1)\nsession.add(b)\n"

    assert _detect_writes(source, "synthetic.py") == ["synthetic.py:2 add(ManualCorrection)"]


@pytest.mark.unit
def test_a_second_assignment_hop_is_the_documented_uncovered_boundary() -> None:
    """KNOWN GAP, pinned boundary: the tracker follows EXACTLY ONE
    assignment hop. `alias = correction`, where `correction` is already
    one-hop bound to a `ManualCorrection(...)` construction, is a SECOND
    hop — `alias`'s own right-hand side is a plain `Name`, not a fresh
    construction — and evades detection, exactly as the module docstring
    and `_one_hop_bindings`'s own docstring state."""
    source = (
        "correction = ManualCorrection(occurrence_id=1)\nalias = correction\nsession.add(alias)\n"
    )

    assert _detect_writes(source, "synthetic.py") == []


@pytest.mark.unit
def test_tuple_unpacking_targets_are_a_documented_uncovered_boundary() -> None:
    """Deliberate scope decision, not an oversight: a tuple/list unpacking
    assignment target is never tracked, even where a per-element match
    with the right-hand side would be structurally possible."""
    source = "a, b = ManualCorrection(occurrence_id=1), None\nsession.add(a)\n"

    assert _detect_writes(source, "synthetic.py") == []


@pytest.mark.unit
def test_a_for_loop_target_is_a_documented_uncovered_boundary() -> None:
    """Deliberate scope decision: a `for` loop target is never tracked,
    even when the iterable is a literal list of `ManualCorrection`
    constructions visible in the same expression."""
    source = "for correction in [ManualCorrection(occurrence_id=1)]:\n    session.add(correction)\n"

    assert _detect_writes(source, "synthetic.py") == []

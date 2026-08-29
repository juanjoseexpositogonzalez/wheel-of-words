"""Structural guard — no module in this capability writes a `ManualCorrection` row (REQ-005-008).

Detects two write forms naming `manual_correction`: a `sqlalchemy`
`insert`/`update`/`delete` call resolved through import/module aliases,
carrying `ManualCorrection` as an argument; and raw SQL text matching
`insert into`/`update`/`delete from manual_correction` (case-insensitive,
`+`-folded). `select(...)` reads are permitted (REQ-005-002).

Scans every `.py` file under `wheel_vocabulary` and every migration (both
`rglob`, no naming convention), exempting `book_repository.py`'s
`DeleteImport` cascade delete (002-text-import) at aggregation, never by
excluding the module from the walk.

ORM-instance idioms (`session.add`, `.merge`, bulk mappings, `__table__`)
are out of scope — this AST pass cannot verify a receiver's runtime type;
the read-scenario integration test verifies the table at runtime instead.

AC-005-08's "ORM class or SQL text" reads as: the class as a call argument
versus the table name in a string — both covered. REQ-005-008, AC-005-08.
"""

from __future__ import annotations

import ast
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

_WRITE_FUNCS = frozenset({"insert", "update", "delete"})
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
        left, right = _folded_string(node.left), _folded_string(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def _string_literals(tree: ast.AST) -> list[str]:
    """Every string literal in `tree`, including `+`-folded chains."""
    literals: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            literals.append(node.value)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            folded = _folded_string(node)
            if folded is not None:
                literals.append(folded)
    return literals


def _sqlalchemy_call_aliases(tree: ast.AST) -> dict[str, str]:
    """Map a locally-bound name to the `sqlalchemy` write function it was
    imported as: `from sqlalchemy import delete as sa_delete` maps
    `"sa_delete" -> "delete"`."""
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "sqlalchemy":
            for alias in node.names:
                if alias.name in _WRITE_FUNCS:
                    aliases[alias.asname or alias.name] = alias.name
    return aliases


def _sqlalchemy_module_aliases(tree: ast.AST) -> frozenset[str]:
    """Names bound to the `sqlalchemy` module itself (`import sqlalchemy`,
    `import sqlalchemy as sa`), so `sa.insert(...)` resolves the same as a
    bare `insert(...)`."""
    return frozenset(
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
        if alias.name == "sqlalchemy"
    )


def _names_manual_correction(node: ast.AST) -> bool:
    """True for a bare `ManualCorrection` `Name`, or an `Attribute` access
    ending in it."""
    if isinstance(node, ast.Name):
        return node.id == "ManualCorrection"
    return isinstance(node, ast.Attribute) and node.attr == "ManualCorrection"


def _has_manual_correction_arg(call: ast.Call) -> bool:
    """True if `call` names `ManualCorrection` as a positional or keyword
    argument."""
    args = [*call.args, *(kw.value for kw in call.keywords)]
    return any(_names_manual_correction(arg) for arg in args)


def _sqlalchemy_write_call(
    node: ast.Call, call_aliases: dict[str, str], module_aliases: frozenset[str]
) -> str | None:
    """`insert(ManualCorrection, ...)` / `update(...)` / `delete(...)`
    resolved to a `sqlalchemy` import, carrying `ManualCorrection` as an
    argument. Origin-checked: a bare `.update()`/`.insert()`/`.delete()`
    attribute call only matches when its base names a tracked `sqlalchemy`
    module alias, so `cache.update(ManualCorrection)` is never mistaken for
    a database write — this is the one thing this AST walk can verify.
    """
    func = node.func
    if isinstance(func, ast.Name) and func.id in call_aliases:
        return call_aliases[func.id] if _has_manual_correction_arg(node) else None
    if (
        isinstance(func, ast.Attribute)
        and isinstance(func.value, ast.Name)
        and func.value.id in module_aliases
        and func.attr in _WRITE_FUNCS
        and _has_manual_correction_arg(node)
    ):
        return func.attr
    return None


def _detect_writes(source: str, label: str) -> list[str]:
    """Every write targeting `manual_correction` in `source`: a
    `sqlalchemy` write call carrying `ManualCorrection`, or raw SQL text
    naming it after an INSERT/UPDATE/DELETE keyword (case-insensitive,
    `+`-folded)."""
    tree = ast.parse(source, filename=label)
    call_aliases = _sqlalchemy_call_aliases(tree)
    module_aliases = _sqlalchemy_module_aliases(tree)
    violations: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            canonical = _sqlalchemy_write_call(node, call_aliases, module_aliases)
            if canonical is not None:
                violations.append(f"{label}:{node.lineno} sqlalchemy {canonical}(ManualCorrection)")

    for literal in _string_literals(tree):
        lower = literal.lower()
        for fragment in _FORBIDDEN_RAW_SQL:
            if fragment in lower:
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

        ['infrastructure/persistence/book_repository.py:144 sqlalchemy delete(ManualCorrection)']
    """
    path, label = next(
        (p, lbl)
        for p, lbl in _scanned_modules()
        if lbl == "infrastructure/persistence/book_repository.py"
    )

    violations = _detect_writes(path.read_text(encoding="utf-8"), label)

    assert violations == [
        "infrastructure/persistence/book_repository.py:144 sqlalchemy delete(ManualCorrection)"
    ]


@pytest.mark.unit
def test_emptying_the_exempt_set_fails_through_write_violations() -> None:
    """M3, through aggregation, not a direct `_detect_writes` call — a prior
    round's control bypassed aggregation and passed against a mutant that
    suppressed the whole default scan.

    MUTATION CHECK: ran `_write_violations(exempt={})` and observed a
    violation naming `book_repository.py`.
    """
    violations = _write_violations(exempt={})

    assert violations
    assert any("book_repository.py" in v for v in violations)


@pytest.mark.unit
def test_the_exemption_boundary_holds_through_write_violations(tmp_path: Path) -> None:
    """M3 boundary: the same write placed outside the exempt set still
    violates, through `_write_violations`'s aggregation path."""
    outside = tmp_path / "other_module.py"
    outside.write_text(
        "from sqlalchemy import delete\ndelete(ManualCorrection)\n", encoding="utf-8"
    )

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

    insert::

    ['infrastructure/persistence/vocabulary_repository.py:184 sqlalchemy insert(ManualCorrection)']

    delete::

    ['infrastructure/persistence/vocabulary_repository.py:184 sqlalchemy delete(ManualCorrection)']
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

    assert insert_violations == [f"{label}:184 sqlalchemy insert(ManualCorrection)"]
    assert delete_violations == [f"{label}:184 sqlalchemy delete(ManualCorrection)"]


@pytest.mark.unit
def test_select_and_attribute_reads_are_permitted() -> None:
    """AMB-3 / REQ-005-002: `select(ManualCorrection...)` and a
    `ManualCorrection.field` attribute read are not violations."""
    source = (
        "from sqlalchemy import select\n"
        "stmt = select(ManualCorrection.occurrence_id, ManualCorrection.field)\n"
    )

    assert _detect_writes(source, "synthetic.py") == []


@pytest.mark.unit
@pytest.mark.parametrize(
    "source",
    [
        "from sqlalchemy import delete as sa_delete\nsa_delete(ManualCorrection)\n",
        "import sqlalchemy as sa\nsa.delete(ManualCorrection)\n",
    ],
    ids=["from-import alias", "module alias"],
)
def test_a_write_call_resolved_through_either_alias_form_is_caught(source: str) -> None:
    """Both alias forms — `from sqlalchemy import delete as X` and `import
    sqlalchemy as X` — resolve to the same canonical write."""
    violations = _detect_writes(source, "synthetic.py")

    assert violations == ["synthetic.py:2 sqlalchemy delete(ManualCorrection)"]


@pytest.mark.unit
def test_a_non_sqlalchemy_call_with_the_same_method_name_is_not_flagged() -> None:
    """Origin check: `cache.update(ManualCorrection)`, with no `sqlalchemy`
    import anywhere in the module, is not a violation."""
    assert _detect_writes("cache.update(ManualCorrection)\n", "synthetic.py") == []


@pytest.mark.unit
@pytest.mark.parametrize(
    "source",
    [
        "session.add(ManualCorrection(occurrence_id=1))\n",
        "session.merge(ManualCorrection(occurrence_id=1))\n",
        "session.query(ManualCorrection).delete()\n",
        "session.bulk_insert_mappings(ManualCorrection, rows)\n",
        "ManualCorrection.__table__.delete()\n",
    ],
    ids=["session.add", "session.merge", "Query.delete", "bulk_insert_mappings", "__table__"],
)
def test_orm_instance_idioms_are_out_of_scope(source: str) -> None:
    """Pins the docstring's scope claim: none of these ORM-instance idioms
    are detected here — this AST pass cannot verify a receiver's runtime
    type."""
    assert _detect_writes(source, "synthetic.py") == []


@pytest.mark.unit
@pytest.mark.parametrize(
    ("source", "expected_fragment"),
    [
        ('text("DELETE FROM manual_correction WHERE 1=1")\n', "delete from manual_correction"),
        (
            'text("INSERT" + " INTO manual_correction VALUES (1)")\n',
            "insert into manual_correction",
        ),
    ],
    ids=["plain literal", "folded concatenation"],
)
def test_raw_sql_targeting_manual_correction_is_caught(source: str, expected_fragment: str) -> None:
    """The substring scan runs over plain and `+`-folded string literals."""
    violations = _detect_writes(source, "synthetic.py")

    assert violations == [f"synthetic.py raw SQL fragment {expected_fragment!r}"]


@pytest.mark.unit
def test_raw_sql_adjacency_gaps_are_not_exhaustive() -> None:
    """KNOWN GAP, not exhaustive: `REPLACE INTO`, extra whitespace, and a
    quoted table name all reach `manual_correction` without matching one of
    the three tracked fragments verbatim."""
    sources = (
        'text("REPLACE INTO manual_correction VALUES (1)")\n',
        'text("INSERT  INTO manual_correction VALUES (1)")\n',
        "text('DELETE FROM \"manual_correction\" WHERE 1=1')\n",
    )

    for source in sources:
        assert _detect_writes(source, "synthetic.py") == [], source

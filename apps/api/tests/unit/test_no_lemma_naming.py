"""Naming guard — hook H1, AC-002-10 (T1B20), backend leg.

This capability groups by *normalized form*. It does not lemmatize, and it must
not imply that it does. A display form is the most frequent inflected spelling in
its group; calling it a lemma would tell the user that `corro`, `corres` and
`corría` had been merged into one dictionary headword when they are in fact three
separate rows (Art. V.1, REQ-002-007).

**The guard is structural, not textual, and MUST NOT be reverted to a grep.**
AC-002-10 originally mandated a literal case-insensitive search for
`lemma|lemas|lexeme|lexema` over the source tree. That guard forbade the word
inside the very sentence explaining why the word is forbidden: cut 1a shipped
`domain/models.py` reading "neither is a lemma or a lexeme (REQ-002-007)" and
cut 1b had to reword it to "canonical dictionary headword" purely to get green,
making the docstring *less* clear to satisfy a check never aimed at docstrings.
`tests/unit/test_domain_isolation.py` had already resolved the identical dilemma
in the opposite direction — it is AST-based because domain docstrings
legitimately contain "FastAPI", "SQLAlchemy" and "Pydantic" while explaining that
those imports are prohibited. The two guards are unified on the AST criterion.

What is checked, and what is not:

- Python: every identifier, and every string literal that is **not** a docstring.
  The exemption is *the first statement of a module, class or function body* —
  never "any string constant", which would remove response keys and user-facing
  messages from the guard and leave nothing behind. `#` comments never reach the
  AST, so they are out of scope by construction.
- `import.v1.json`: every object key and every string value. JSON has no
  docstring, so nothing in it is exempt.
- The served OpenAPI document: every string. This leg is what keeps the docstring
  exemption *scoped*, because FastAPI publishes a Pydantic model docstring as
  ``components.schemas.*.description``. At that point a docstring has stopped
  being prose and become contract, and the guard catches it again.

MUTATION CHECK — these are ABSENCE assertions. They pass on their first run over
correct code, which proves nothing, so they are trusted only after being seen
failing. Verified by introducing one real violation of each kind and reverting:

1. Field identifier — renamed ``FormFrequencyResponse.display_form`` to
   ``lemma_form`` in ``api/dtos/imports.py``::

       AssertionError: lemma naming leaked into the backend sources:
       api/dtos/imports.py:44 annotated name 'lemma_form'
       api/dtos/imports.py:44 name 'lemma_form'

2. Response-key string literal — the row keys are Pydantic field names, so the
   only literal wire key in the sources is the response header in
   ``api/routes/imports.py``; changed ``"X-Schema-Version"`` to
   ``"X-Lemma-Version"``::

       AssertionError: lemma naming leaked into the backend sources:
       api/routes/imports.py:44 string literal 'X-Lemma-Version'

3. JSON Schema property name — renamed the ``normalized_form`` property of
   ``$defs.form`` in ``api/schemas/import.v1.json`` to ``lemma_form``::

       AssertionError: lemma naming leaked into the pinned JSON Schema:
       $.$defs.form.required[0] (value) -> 'lemma_form'
       $.$defs.form.properties.lemma_form (key) -> 'lemma_form'

4. Published Pydantic docstring — restored "Neither form is a lemma or a lexeme"
   to the ``FormFrequencyResponse`` class docstring. The Python leg passed, as
   designed, and the OpenAPI leg caught it (body elided at ``[...]``)::

       AssertionError: lemma naming leaked into the served OpenAPI document:
       $.components.schemas.FormFrequencyResponse.description (value) -> 'One row
       of the frequency table.\n\n[...]\n\nNeither form is a lemma or a lexeme,
       and neither may be labelled as one\n(REQ-002-007).'

   That run is also why ``api/dtos/imports.py`` keeps its reworded docstring
   while ``domain/models.py`` gets the plainer wording back: the domain
   dataclass docstring is prose and reaches no user, the DTO docstring is
   published at ``/openapi.json``. Restoring the DTO one would be a real
   REQ-002-007 violation, not a false positive.

The non-vacuity test below closes the other half of the same problem, because a
file walk that resolved to zero files would make every assertion here trivially
true.

**Frontend leg lives elsewhere.** AC-002-10's own wording lists "Python
sources (``apps/api/src/wheel_vocabulary/``, ``apps/web/src/``), parsed as an
AST" as one bullet. Cut 1c originally shipped the ``apps/web/src/`` leg here
as a plain case-insensitive text search, because Python's ``ast`` module
cannot parse TypeScript/TSX and no TS parser was named in the design. That
deviation reintroduced the exact pathology this module's AST criterion exists
to avoid: a plain text search forbids the word inside a comment explaining
why the word is forbidden — the same regression the backend leg above was
converted away from in cut 1b. A maintainer remediation moved the frontend
leg to a genuine TypeScript AST walk using the ``typescript`` package's own
compiler API (already an ``apps/web`` devDependency — no new dependency was
added), in
``apps/web/tests/contracts/no-lemma-naming.test.ts::test_frontend_sources_contain_no_lemma_naming``.
That guard checks identifiers and non-comment string literals (including JSX
text and template literals) and is now unified on the same AST criterion as
the backend leg above, satisfying AC-002-10's "parsed as an AST" wording for
the frontend rather than deviating from it.

REQ-002-007 / AC-002-10.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from wheel_vocabulary.api.main import create_app

if TYPE_CHECKING:
    from collections.abc import Iterator

    from fastapi.testclient import TestClient

_PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src" / "wheel_vocabulary"
_SCHEMA_PATH = _PACKAGE_ROOT / "api" / "schemas" / "import.v1.json"
_FORBIDDEN_PATTERN = "lemma|lemas|lexeme|lexema"
_FORBIDDEN = re.compile(_FORBIDDEN_PATTERN, re.IGNORECASE)

# Nodes that own a docstring: the docstring is body[0], never any other Constant.
_DOCSTRING_OWNERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)

# Files that make the scan meaningful. If the walk ever stops reaching these,
# the guard has silently stopped guarding anything.
_EXPECTED_FILES = frozenset(
    {
        "api/routes/imports.py",
        "api/dtos/imports.py",
        "application/imports/use_cases.py",
        "domain/models.py",
        "infrastructure/persistence/models.py",
    }
)

# The migration lives outside `_PACKAGE_ROOT` (`apps/api/migrations/`, not
# `apps/api/src/wheel_vocabulary/`), so the walk above never reaches it. Its
# `sa.Column("...", ...)` names are string literals, not identifiers — the
# persisted-column leg below checks both files.
_MIGRATION_PATH = _PACKAGE_ROOT.parents[1] / "migrations" / "versions" / "0002_book_occurrence.py"

_ROW_KEYS = {"normalized_form", "display_form", "frequency"}


def _python_modules() -> list[Path]:
    return sorted(_PACKAGE_ROOT.rglob("*.py"))


def _relative(path: Path) -> str:
    return path.relative_to(_PACKAGE_ROOT).as_posix()


def _docstring_constant_ids(tree: ast.AST) -> frozenset[int]:
    """Identify the Constant nodes that are docstrings, by identity.

    A docstring is an ``ast.Constant`` exactly like any other string literal, so
    it cannot be recognised by its value or its type. It is recognised by its
    *position*: the first statement of a module, class or function body, wrapped
    in an ``ast.Expr``. Identity (``id``) is safe here only because the caller
    keeps ``tree`` alive for the whole walk; the ids would otherwise be free to
    be reused by later objects.
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


def _declared_names(node: ast.AST) -> list[tuple[str, str]]:
    """Return every identifier a node introduces, tagged with what it is."""
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
        return [("function", node.name)]
    if isinstance(node, ast.ClassDef):
        return [("class", node.name)]
    if isinstance(node, ast.arg):
        return [("parameter", node.arg)]
    if isinstance(node, ast.Name):
        return [("name", node.id)]
    if isinstance(node, ast.Attribute):
        return [("attribute", node.attr)]
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        # Dataclass and Pydantic field declarations.
        return [("annotated name", node.target.id)]
    if isinstance(node, ast.keyword) and node.arg is not None:
        return [("keyword argument", node.arg)]
    if isinstance(node, ast.alias):
        return [("import alias", name) for name in (node.name, node.asname) if name is not None]
    if isinstance(node, ast.ImportFrom) and node.module is not None:
        return [("imported module", node.module)]
    if isinstance(node, ast.ExceptHandler) and node.name is not None:
        return [("exception name", node.name)]
    if isinstance(node, ast.Global | ast.Nonlocal):
        return [("declared global", name) for name in node.names]
    return []


def _python_violations(source: str, label: str) -> list[str]:
    """Report forbidden naming in identifiers and non-docstring string literals."""
    tree = ast.parse(source, filename=label)
    docstrings = _docstring_constant_ids(tree)
    violations: list[str] = []

    for node in ast.walk(tree):
        line = getattr(node, "lineno", 0)
        violations.extend(
            f"{label}:{line} {kind} {name!r}"
            for kind, name in _declared_names(node)
            if _FORBIDDEN.search(name)
        )
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
            and _FORBIDDEN.search(node.value)
        ):
            violations.append(f"{label}:{line} string literal {node.value!r}")

    return violations


def _json_strings(node: Any, path: str) -> Iterator[tuple[str, str]]:
    """Yield every object key and every string value, with its JSON path."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield f"{path}.{key} (key)", key
            yield from _json_strings(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, item in enumerate(node):
            yield from _json_strings(item, f"{path}[{index}]")
    elif isinstance(node, str):
        yield f"{path} (value)", node


def _json_violations(document: Any) -> list[str]:
    return [
        f"{where} -> {text!r}"
        for where, text in _json_strings(document, "$")
        if _FORBIDDEN.search(text)
    ]


@pytest.fixture
def imported_body(imports_client: TestClient) -> dict[str, Any]:
    """`imports_client` (`tests/conftest.py`) wires an isolated, schema-ready
    SQLite database — persistence landed in cut 2 (REQ-002-008)."""
    response = imports_client.post(
        "/api/v1/imports",
        files={"file": ("sample.txt", "corro corres corr\u00eda corro".encode(), "text/plain")},
    )
    assert response.status_code == 201
    body: dict[str, Any] = response.json()
    return body


@pytest.mark.unit
def test_the_scan_reaches_the_shipped_backend_sources() -> None:
    """Without this, an empty walk would make the guard below vacuously green."""
    scanned = {_relative(path) for path in _python_modules()}

    assert scanned >= _EXPECTED_FILES
    assert _SCHEMA_PATH.is_file()


@pytest.mark.unit
def test_no_backend_identifier_or_literal_names_a_lemma_or_a_lexeme() -> None:
    """AC-002-10: zero matches in identifiers and non-docstring literals."""
    violations = [
        violation
        for module in _python_modules()
        for violation in _python_violations(module.read_text(encoding="utf-8"), _relative(module))
    ]

    assert not violations, "lemma naming leaked into the backend sources:\n" + "\n".join(violations)


@pytest.mark.unit
def test_persisted_columns_contain_no_lemma_naming() -> None:
    """AC-002-10 closing leg (T217): persisted schema, not just source identifiers.

    Two checks, because the migration lives outside `_PACKAGE_ROOT` and so is
    never reached by `test_no_backend_identifier_or_literal_names_a_lemma_or_a_lexeme`:

    1. The AST walk (identifiers + non-docstring literals) over
       `infrastructure/persistence/models.py` AND the `0002_book_occurrence`
       migration, so a `sa.Column("...")` string literal is caught even though
       it is a literal, not an identifier.
    2. The ACTUAL mapped column names read back from `Base.metadata`, which
       catches a rename regardless of how the source spells it (SQLAlchemy
       infers the DB column name from the attribute unless overridden).

    MUTATION CHECK — an absence assertion. Verified by renaming
    `Occurrence.normalized_text` to `lemma_text` in `persistence/models.py`,
    confirming an `AssertionError` naming `persistence/models.py` and the
    matched token `lemma_text`, then reverting.
    """
    from wheel_vocabulary.infrastructure.persistence.base import Base

    models_path = _PACKAGE_ROOT / "infrastructure" / "persistence" / "models.py"
    violations = [
        *_python_violations(models_path.read_text(encoding="utf-8"), _relative(models_path)),
        *_python_violations(
            _MIGRATION_PATH.read_text(encoding="utf-8"),
            f"migrations/versions/{_MIGRATION_PATH.name}",
        ),
    ]
    assert not violations, "lemma naming leaked into the persisted schema source:\n" + "\n".join(
        violations
    )

    column_names = [
        column.name
        for table in ("book", "occurrence")
        for column in Base.metadata.tables[table].columns
    ]
    reflected_violations = [name for name in column_names if _FORBIDDEN.search(name)]
    assert not reflected_violations, (
        "lemma naming leaked into a persisted column name: " + ", ".join(reflected_violations)
    )


@pytest.mark.unit
def test_the_pinned_json_schema_names_no_lemma_or_lexeme() -> None:
    """AC-002-10: the schema is not Python, so it gets its own key-and-value check."""
    violations = _json_violations(json.loads(_SCHEMA_PATH.read_text(encoding="utf-8")))

    assert not violations, "lemma naming leaked into the pinned JSON Schema:\n" + "\n".join(
        violations
    )


@pytest.mark.unit
def test_the_served_openapi_document_names_no_lemma_or_lexeme() -> None:
    """AC-002-10: FastAPI publishes model docstrings, so published prose is contract."""
    violations = _json_violations(create_app().openapi())

    assert not violations, "lemma naming leaked into the served OpenAPI document:\n" + "\n".join(
        violations
    )


@pytest.mark.unit
def test_docstrings_and_comments_may_name_the_concept_they_rule_out() -> None:
    """The exemption exists so documentation can be plain about what this is not."""
    source = '''
"""Groups by normalized form; it is not a lemma and not a lexeme."""


class FormFrequency:
    """Neither value is a lemma or a lexeme (REQ-002-007)."""

    normalized_form: str

    def describe(self) -> str:
        """A lexeme would merge inflected forms; this does not."""
        # Calling this a lemma would misdescribe the grouping.
        return "normalized form"
'''

    assert _python_violations(source, "synthetic.py") == []


@pytest.mark.unit
def test_a_field_identifier_named_lemma_still_fails() -> None:
    """The exemption is scoped to docstrings; it is not a hole for identifiers."""
    source = '''
"""Neither value is a lemma or a lexeme (REQ-002-007)."""


class FormFrequency:
    lemma_form: str
'''

    violations = _python_violations(source, "synthetic.py")

    assert violations
    assert any("lemma_form" in violation for violation in violations)


@pytest.mark.unit
def test_a_response_key_string_literal_named_lemma_still_fails() -> None:
    """A response key is an ordinary Constant, and stays inside the guard."""
    source = '''
"""Neither value is a lemma or a lexeme (REQ-002-007)."""

ROW_KEYS = ("lemma_form", "display_form")
'''

    violations = _python_violations(source, "synthetic.py")

    assert violations
    assert any("string literal 'lemma_form'" in violation for violation in violations)


@pytest.mark.unit
def test_a_docstring_published_by_fastapi_is_not_exempt() -> None:
    """A model docstring is prose in the source and contract on the wire."""
    published = {"components": {"schemas": {"Row": {"description": "This is a lemma."}}}}

    assert _json_violations(published)


@pytest.mark.unit
def test_each_response_row_uses_the_specified_key_names(
    imported_body: dict[str, Any],
) -> None:
    """AC-002-10: the grouping key is `normalized_form`, the display value `display_form`."""
    assert imported_body["forms"]
    for row in imported_body["forms"]:
        assert set(row) == _ROW_KEYS


@pytest.mark.unit
def test_the_response_envelope_introduces_no_lemma_naming(
    imported_body: dict[str, Any],
) -> None:
    """Every key on the wire, not only the row keys."""
    keys = set(imported_body) | {key for row in imported_body["forms"] for key in row}

    assert not [key for key in keys if _FORBIDDEN.search(key)]


@pytest.mark.unit
def test_inflected_forms_stay_separate_rows(imported_body: dict[str, Any]) -> None:
    """The naming is honest because the behaviour is: nothing is merged (Art. V.1)."""
    assert [row["normalized_form"] for row in imported_body["forms"]] == [
        "corres",
        "corr\u00eda",
        "corro",
    ]

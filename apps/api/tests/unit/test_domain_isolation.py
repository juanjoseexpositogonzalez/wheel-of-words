"""Structural guard over ``domain/`` — hook H2, AC-002-06 (T1A10).

These are ABSENCE assertions. They pass on their first run over correct code,
which is evidence of nothing, so the guard is only trusted once it has been seen
failing: add ``import sqlalchemy`` to ``domain/frequency.py``, observe the
``AssertionError`` naming the file and the matched pattern, then revert. The
non-vacuity test below closes the other half of the same problem — a file walk
that silently resolves to zero files would make every assertion here trivially
true.

REQ-002-005 / AC-002-06, Art. VII.1, ADR-0002.

**Task 1.4/1.5 — REQ-003-002.** `_FORBIDDEN_IMPORT_PATTERN` grew to cover
`thinc` (spaCy's own ML backend) and `stanza` (ADR-0001/0002's alternative
adapter), so the domain cannot bypass `LinguisticAnalyzer` by importing
either directly. Mutation check: inserted ``import thinc`` into
``domain/frequency.py``, observed and reverted::

    AssertionError: domain isolation violated:
    frequency.py imports 'thinc' (pattern: fastapi|sqlalchemy|pydantic|spacy|thinc|stanza)
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

_DOMAIN_ROOT = Path(__file__).resolve().parents[2] / "src" / "wheel_vocabulary" / "domain"
_FORBIDDEN_IMPORT_PATTERN = "fastapi|sqlalchemy|pydantic|spacy|thinc|stanza"
_FORBIDDEN_IMPORT = re.compile(rf"^({_FORBIDDEN_IMPORT_PATTERN})$")

# A bare lowercase two- or three-letter literal, optionally with a region
# subtag, is the shape of an ISO-639 language tag. REQ-PFB-LANG-01 forbids the
# domain from carrying one, so the shape itself is refused rather than a
# hand-maintained list of codes that would inevitably fall behind.
_ISO_639_SHAPE = re.compile(r"^[a-z]{2,3}([-_][A-Za-z]{2,4})?$")
_LANGUAGE_PARAMETER_NAMES = frozenset({"language", "lang", "locale", "language_code"})

_EXPECTED_MODULES = frozenset(
    {
        "__init__.py",
        "models.py",
        "frequency.py",
        "text/__init__.py",
        "text/tokenizer.py",
        "text/normalizer.py",
    }
)


def _domain_modules() -> list[Path]:
    return sorted(_DOMAIN_ROOT.rglob("*.py"))


def _relative(path: Path) -> str:
    return path.relative_to(_DOMAIN_ROOT).as_posix()


@pytest.mark.unit
def test_domain_package_scan_is_not_vacuous() -> None:
    """The walk must actually reach the shipped modules, or every guard is empty."""
    modules = _domain_modules()

    assert modules, f"no domain modules found under {_DOMAIN_ROOT}"
    assert {_relative(path) for path in modules} >= _EXPECTED_MODULES


@pytest.mark.unit
def test_forbidden_import_pattern_includes_thinc_and_stanza() -> None:
    """REQ-003-002 gap (task 1.4): the pattern covered `spacy` but not
    `thinc` (spaCy's own ML backend) or `stanza` (ADR-0001/0002's
    alternative adapter) — a domain module could import either directly."""
    forbidden = _FORBIDDEN_IMPORT_PATTERN.split("|")

    assert "thinc" in forbidden
    assert "stanza" in forbidden


@pytest.mark.unit
def test_a_domain_module_importing_thinc_or_stanza_fails_the_guard() -> None:
    """Direct mutation check: RED before task 1.5's pattern extension (both
    matched no branch), GREEN after."""
    thinc_source = "import thinc\n"
    stanza_source = "from stanza import Pipeline\n"

    assert _forbidden_import_violations(thinc_source, "synthetic.py")
    assert _forbidden_import_violations(stanza_source, "synthetic.py")


@pytest.mark.unit
def test_domain_has_no_framework_imports_or_iso639_literals() -> None:
    """AC-002-06 / AC-003-02: the domain is standard-library only and
    language-agnostic; the forbidden-import check now also covers `thinc`
    and `stanza` (REQ-003-002)."""
    violations: list[str] = []

    for module in _domain_modules():
        source = module.read_text(encoding="utf-8")
        violations.extend(_forbidden_import_violations(source, _relative(module)))
        tree = ast.parse(source, filename=str(module))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and _ISO_639_SHAPE.match(node.value)
            ):
                violations.append(
                    f"{_relative(module)} carries the ISO-639-shaped literal {node.value!r}"
                )

    assert not violations, "domain isolation violated:\n" + "\n".join(violations)


@pytest.mark.unit
def test_domain_functions_expose_no_language_parameter() -> None:
    """AC-002-06: no function may take a language, so no rule can be language-specific."""
    violations: list[str] = []

    for module in _domain_modules():
        tree = ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            arguments = node.args
            named = [
                *arguments.posonlyargs,
                *arguments.args,
                *arguments.kwonlyargs,
            ]
            violations.extend(
                f"{_relative(module)}::{node.name} exposes the parameter {argument.arg!r}"
                for argument in named
                if argument.arg in _LANGUAGE_PARAMETER_NAMES
            )

    assert not violations, "language parameter leaked into the domain:\n" + "\n".join(violations)


def _imported_roots(node: ast.AST) -> list[str]:
    """Return the root package name of every module an import node pulls in."""
    if isinstance(node, ast.Import):
        return [alias.name.split(".")[0] for alias in node.names]
    if isinstance(node, ast.ImportFrom) and node.module is not None and node.level == 0:
        return [node.module.split(".")[0]]
    return []


def _forbidden_import_violations(source: str, label: str) -> list[str]:
    """Report every forbidden-framework/NLP-library import in `source`."""
    tree = ast.parse(source, filename=label)
    return [
        f"{label} imports {root!r} (pattern: {_FORBIDDEN_IMPORT_PATTERN})"
        for node in ast.walk(tree)
        for root in _imported_roots(node)
        if _FORBIDDEN_IMPORT.match(root)
    ]

"""Structural guard over ``domain/`` — hook H2, AC-002-06 (T1A10).

These are ABSENCE assertions. They pass on their first run over correct code,
which is evidence of nothing, so the guard is only trusted once it has been seen
failing: add ``import sqlalchemy`` to ``domain/frequency.py``, observe the
``AssertionError`` naming the file and the matched pattern, then revert. The
non-vacuity test below closes the other half of the same problem — a file walk
that silently resolves to zero files would make every assertion here trivially
true.

REQ-002-005 / AC-002-06, Art. VII.1, ADR-0002.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

_DOMAIN_ROOT = Path(__file__).resolve().parents[2] / "src" / "wheel_vocabulary" / "domain"
_FORBIDDEN_IMPORT_PATTERN = "fastapi|sqlalchemy|pydantic|spacy"
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
def test_domain_has_no_framework_imports_or_iso639_literals() -> None:
    """AC-002-06: the domain is standard-library only and language-agnostic."""
    violations: list[str] = []

    for module in _domain_modules():
        tree = ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
        for node in ast.walk(tree):
            for root in _imported_roots(node):
                if _FORBIDDEN_IMPORT.match(root):
                    violations.append(
                        f"{_relative(module)} imports {root!r} "
                        f"(pattern: {_FORBIDDEN_IMPORT_PATTERN})"
                    )
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

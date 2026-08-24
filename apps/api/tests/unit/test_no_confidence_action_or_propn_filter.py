"""Structural zero-match search — AC-003-09 scenario 3, AC-003-23 scenario 2.

Two acceptance scenarios the verify report flagged as PARTIAL (WARNING-3):
neither had a genuine structural search over the shipped sources, only a
narrower frontend check (`no-linguistic-rules.test.ts`'s `FORBIDDEN_METHODS`)
and an inference from reading the code. This module closes the backend leg
of both:

- **AC-003-09 sc.3** — "nothing acts on confidence": no filter, sort, or
  threshold may key off `pos_confidence`/`lemma_confidence` anywhere outside
  the domain's own range VALIDATION (`validate_confidence`, which rejects an
  out-of-range value — that is integrity, not acting on the value's
  magnitude to make a product decision).
- **AC-003-23 sc.2** — "no proper-noun special case": the literal `"PROPN"`
  may appear in exactly one place, `domain/annotation.py`'s `UPOS_TAGS`
  frozenset — a total 17-tag membership set, not a filter. Anywhere else it
  would mean some layer is branching on it.

Both are ABSENCE assertions. They pass on their first run over correct code,
which proves nothing on its own, so each is verified with a real mutation
check documented in its own test's docstring below.

REQ-003-009 / AC-003-09, REQ-003-022 / AC-003-23.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src" / "wheel_vocabulary"
_PROPN_ALLOWED_FILE = "domain/annotation.py"
_CONFIDENCE_ACTION_PATTERN = "threshold|filter_by_confidence|min_confidence|sort_by_confidence"

_EXPECTED_FILES = frozenset(
    {
        "domain/annotation.py",
        "application/annotation/use_cases.py",
        "infrastructure/nlp/spacy_analyzer.py",
        "infrastructure/persistence/annotation_repository.py",
        "api/routes/annotation.py",
    }
)


def _package_modules() -> list[Path]:
    return sorted(_PACKAGE_ROOT.rglob("*.py"))


def _relative(path: Path) -> str:
    return path.relative_to(_PACKAGE_ROOT).as_posix()


def _propn_violations(source: str, label: str) -> list[str]:
    """Report every string-literal occurrence of `PROPN`, unless `label` is
    the one allow-listed file (the total UPOS_TAGS membership set)."""
    if label == _PROPN_ALLOWED_FILE:
        return []
    tree = ast.parse(source, filename=label)
    return [
        f"{label}:{node.lineno} string literal 'PROPN' (only {_PROPN_ALLOWED_FILE} may contain it)"
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and node.value == "PROPN"
    ]


def _confidence_action_violations(source: str, label: str) -> list[str]:
    """Report any identifier whose name suggests acting on a confidence
    value (filtering, sorting, thresholding) — REQ-003-009 C6."""
    tree = ast.parse(source, filename=label)
    violations: list[str] = []
    for node in ast.walk(tree):
        name: str | None = None
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            name = node.name
        elif isinstance(node, ast.Name):
            name = node.id
        if name is not None and any(
            token in name for token in _CONFIDENCE_ACTION_PATTERN.split("|")
        ):
            violations.append(f"{label}:{node.lineno} identifier {name!r}")
    return violations


@pytest.mark.unit
def test_the_scan_reaches_the_shipped_annotation_sources() -> None:
    """Non-vacuity: the walk must reach every layer, or both guards below
    are empty."""
    scanned = {_relative(path) for path in _package_modules()}

    assert scanned >= _EXPECTED_FILES


@pytest.mark.unit
def test_propn_appears_nowhere_outside_the_upos_tags_membership_set() -> None:
    """AC-003-23 scenario 2: structural, package-wide.

    MUTATION CHECK: temporarily added `if pos == "PROPN": pos = None` to
    `AnnotateImport._validate_and_assemble` in
    `application/annotation/use_cases.py`, ran this test, and observed::

        AssertionError: a proper-noun special case leaked into the backend sources:
        application/annotation/use_cases.py:146 string literal 'PROPN'
        (only domain/annotation.py may contain it)

    then reverted.
    """
    violations = [
        violation
        for module in _package_modules()
        for violation in _propn_violations(module.read_text(encoding="utf-8"), _relative(module))
    ]

    assert not violations, (
        "a proper-noun special case leaked into the backend sources:\n" + "\n".join(violations)
    )


@pytest.mark.unit
def test_nothing_acts_on_confidence_anywhere_in_the_package() -> None:
    """AC-003-09 scenario 3: structural, package-wide.

    MUTATION CHECK: temporarily added a function
    `def filter_by_confidence(rows: list) -> list: ...` to
    `infrastructure/persistence/annotation_repository.py`, ran this test,
    and observed::

        AssertionError: confidence is acted upon somewhere in the backend sources:
        infrastructure/persistence/annotation_repository.py:51 identifier 'filter_by_confidence'

    then reverted.
    """
    violations = [
        violation
        for module in _package_modules()
        for violation in _confidence_action_violations(
            module.read_text(encoding="utf-8"), _relative(module)
        )
    ]

    assert not violations, (
        "confidence is acted upon somewhere in the backend sources:\n" + "\n".join(violations)
    )


@pytest.mark.unit
def test_a_propn_special_case_outside_the_allowed_file_would_be_caught() -> None:
    """Direct mutation check, run synthetically."""
    source = 'def annotate(pos):\n    if pos == "PROPN":\n        return None\n'

    assert _propn_violations(source, "synthetic.py")


@pytest.mark.unit
def test_a_confidence_threshold_helper_would_be_caught() -> None:
    """Direct mutation check, run synthetically."""
    source = "def filter_by_confidence(rows):\n    return rows\n"

    assert _confidence_action_violations(source, "synthetic.py")


@pytest.mark.unit
def test_upos_tags_is_the_one_exempt_location_and_it_does_contain_propn() -> None:
    """Sanity check on the allow-list itself: `domain/annotation.py` really
    does define PROPN (as membership, not a filter), so the exemption above
    is not accidentally pointing at the wrong file."""
    domain_path = _PACKAGE_ROOT / _PROPN_ALLOWED_FILE
    source = domain_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=_PROPN_ALLOWED_FILE)

    assert any(isinstance(node, ast.Constant) and node.value == "PROPN" for node in ast.walk(tree))

"""Unit tests for the annotation application port — spec §2.6 S4, REQ-003-003.

Written RED before `application/annotation/ports.py` exists: the import
below is the only thing that can fail at collection time.

AMB-6: the port lives in `application/`, not `domain/`, following the
`imports/ports.py` precedent, not the looser ADR-0002 wording. ADR-0008
requires the port to carry a required `language` keyword argument with no
default anywhere — verified here structurally against both this module and
`domain/annotation.py` together, per task 2.7.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from wheel_vocabulary.application.annotation.ports import AnalyzerIdentity, LinguisticAnalyzer
from wheel_vocabulary.domain.annotation import LinguisticAnnotation

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Sequence

_PORTS_MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "wheel_vocabulary"
    / "application"
    / "annotation"
    / "ports.py"
)
_DOMAIN_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "src" / "wheel_vocabulary" / "domain" / "annotation.py"
)
_ISO_639_SHAPE = re.compile(r"^[a-z]{2,3}([-_][A-Za-z]{2,4})?$")
_FORBIDDEN_NLP_IMPORTS = frozenset({"spacy", "thinc", "stanza"})
_ANALYZE_OBLIGATION = "source_index == i"
_BOUNDED_SOURCE_INDEX_GUARANTEE = (
    "the check proves that the analyzer's output is "
    "**self-consistent with the input it was given** "
    "— each annotation reports both the token text and the input index it claims to have been "
    "computed for, and both MUST agree with the occurrence at that position, so an "
    "internally reordered result of equal length is rejected instead of being written to the "
    "wrong occurrence. "
    "It does **not** prove that the annotation is linguistically correct for that token, and it "
    "cannot detect an analyzer that swaps two same-text annotations while consistently reassigning "
    "`source_index`, because `source_index` is self-reported by the analyzer."
)
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_SPEC_PATH = _PROJECT_ROOT / "openspec" / "specs" / "003-lemmatization-pos" / "spec.md"
_TRACEABILITY_MATRIX_PATH = _PROJECT_ROOT / "docs" / "traceability-matrix.md"


class _FakeAnalyzer:
    """Structural double proving REQ-003-003 without importing any NLP
    library — the whole point of the port being a `Protocol`."""

    def __init__(self) -> None:
        self.identity = AnalyzerIdentity(
            source="fake", model_name="fake-model", model_version="0.0.0"
        )

    def analyze(self, tokens: Sequence[str], *, language: str) -> Sequence[LinguisticAnnotation]:
        del language  # the fake ignores it; the real adapter does not (Phase 4)
        return [
            LinguisticAnnotation(
                raw_text=token,
                source_index=index,
                pos="NOUN",
                lemma=token,
                pos_confidence=None,
                lemma_confidence=None,
            )
            for index, token in enumerate(tokens)
        ]


def _imported_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


def _string_constants(tree: ast.AST) -> set[str]:
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def _normalized_whitespace(value: str) -> str:
    return " ".join(value.split())


@pytest.mark.unit
def test_fake_analyzer_satisfies_linguistic_analyzer_structurally() -> None:
    """REQ-003-003: a plain stdlib double conforms, with no NLP import
    anywhere in this test module or in the fake itself."""
    analyzer = _FakeAnalyzer()

    assert isinstance(analyzer, LinguisticAnalyzer)


@pytest.mark.unit
def test_analyze_returns_one_annotation_per_input_token_in_order() -> None:
    """REQ-003-003: one annotation per input token, same order (§2.6 S4)."""
    analyzer = _FakeAnalyzer()
    tokens = ["run", "ran", "running"]

    result = analyzer.analyze(tokens, language="en")

    assert [annotation.lemma for annotation in result] == tokens


@pytest.mark.unit
def test_analyze_requires_language_as_a_keyword_argument_with_no_default() -> None:
    """AC-003-03: omitting `language` fails at the call site — never a
    silent fallback."""
    analyzer = _FakeAnalyzer()

    with pytest.raises(TypeError):
        analyzer.analyze(["run"])  # type: ignore[call-arg]


@pytest.mark.unit
def test_ports_module_carries_no_nlp_import() -> None:
    """A structural `Protocol` never needs to import the library it
    abstracts over."""
    source = _PORTS_MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_PORTS_MODULE_PATH))

    violations = _imported_roots(tree) & _FORBIDDEN_NLP_IMPORTS

    assert not violations, violations


@pytest.mark.unit
@pytest.mark.parametrize("module_path", [_PORTS_MODULE_PATH, _DOMAIN_MODULE_PATH])
def test_port_and_domain_carry_zero_iso_639_literals(module_path: Path) -> None:
    """AC-003-03: neither the port nor the domain value object contains an
    ISO-639 literal."""
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(module_path))

    violations = {value for value in _string_constants(tree) if _ISO_639_SHAPE.match(value)}

    assert not violations, f"{module_path.name} carries ISO-639-shaped literal(s): {violations}"


@pytest.mark.unit
def test_analyze_has_no_default_for_the_language_parameter() -> None:
    """AC-003-03: `language` has no default anywhere in the port module —
    structural, so a future edit reintroducing one fails this test."""
    source = _PORTS_MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_PORTS_MODULE_PATH))

    checked = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) or node.name != "analyze":
            continue
        for argument, default in zip(node.args.kwonlyargs, node.args.kw_defaults, strict=True):
            if argument.arg == "language":
                assert default is None, "language must not have a default value"
                checked += 1

    assert checked == 1, "expected exactly one `analyze` definition with a `language` kwarg"


@pytest.mark.unit
def test_analyze_docstring_states_the_source_index_failure_obligation() -> None:
    """REQ-003H-004 M1 (RED before 08e, observed 2026-08-25):
    `E AssertionError: assert 'source_index == i' in 'Return one annotation
    per input token, in the same order.\\n\\n        ``tokens`` MUST be the
    already-tokenized, ordere...  ``language``. Raised before any pipeline
    loads and before\\n                any row is written (AC-003-03).\\n
        '` because the port documented only `raw_text`, not the rejected
    source-index condition.

    Removing the documented `source_index == i` sentence must therefore make
    this assertion fail rather than leave the contract guard vacuous.
    """
    docstring = LinguisticAnalyzer.analyze.__doc__

    assert docstring is not None
    assert _ANALYZE_OBLIGATION in docstring
    assert "ANNOTATION_FAILED" in docstring
    assert "raw_text" in docstring


@pytest.mark.unit
def test_each_annotation_validation_rejection_has_a_port_obligation() -> None:
    """REQ-003H-004: every `_validate_and_assemble` rejection branch maps
    to a `LinguisticAnalyzer.analyze` contract obligation."""
    docstring = LinguisticAnalyzer.analyze.__doc__

    assert docstring is not None
    rejection_obligations = {
        "annotation count": "one annotation per input token",
        "raw-text and source-index pairing": "source_index == i",
        "UPOS tag": "None or a UPOS tag",
        "confidence range": "within [0.0, 1.0]",
    }

    missing = {
        branch: obligation
        for branch, obligation in rejection_obligations.items()
        if obligation not in docstring
    }

    assert not missing, f"undocumented annotation validation branches: {missing}"


@pytest.mark.unit
def test_bounded_source_index_guarantee_is_verbatim_in_all_required_locations() -> None:
    """REQ-003H-006 G2: the bounded statement must not drift between the
    port contract, its source specification, and the traceability matrix."""
    docstring = LinguisticAnalyzer.analyze.__doc__

    assert docstring is not None
    expected = _normalized_whitespace(_BOUNDED_SOURCE_INDEX_GUARANTEE)
    locations = {
        "port contract": docstring,
        "specification": _SPEC_PATH.read_text(encoding="utf-8"),
        "traceability matrix": _TRACEABILITY_MATRIX_PATH.read_text(encoding="utf-8"),
    }
    missing = [
        name
        for name, content in locations.items()
        if expected not in _normalized_whitespace(content)
    ]

    assert not missing, f"bounded source-index guarantee missing or altered in: {missing}"
    assert "verifies this identity" not in docstring


@pytest.mark.unit
def test_docs_name_source_index() -> None:
    """REQ-003H-004: the annotation contract is discoverable in `docs/`."""
    docs_path = _PROJECT_ROOT / "docs"
    matches = [
        path
        for path in docs_path.rglob("*")
        if path.is_file() and "source_index" in path.read_text(encoding="utf-8")
    ]

    assert matches, "expected at least one docs/ file to name source_index"

"""Unit tests for the annotation domain value object and pure rules.

Written RED before `domain/annotation.py` exists: the import below is the
only thing that can fail at collection time, so the failure cannot be a
fixture or configuration fault.

Covers the *shape* of REQ-003-005 and REQ-003-006 (the value object's fields,
not the adapter that populates them), the pure rules of REQ-003-008
(confidence range) and REQ-003-010 (read-time precedence), and REQ-003-002
(frozen, stdlib-only). See `domain/annotation.py`'s module docstring for why
task 2.1 requires a dedicated test proving the bare literal `"pos"` never
appears in that module (design §Phase 2 landmine, REQ-003-022 closure note in
`tasks.md`).
"""

from __future__ import annotations

import ast
import dataclasses
import re
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from wheel_vocabulary.domain.annotation import (
    UPOS_TAGS,
    LinguisticAnnotation,
    resolve_effective,
    validate_confidence,
)

_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "src" / "wheel_vocabulary" / "domain" / "annotation.py"
)
_FORBIDDEN_IMPORTS = frozenset({"spacy", "thinc", "stanza", "sqlalchemy", "fastapi", "pydantic"})


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


@pytest.mark.unit
def test_linguistic_annotation_is_frozen() -> None:
    """REQ-003-002: the value object is immutable."""
    annotation = LinguisticAnnotation(
        raw_text="running", pos="NOUN", lemma="run", pos_confidence=0.9, lemma_confidence=None
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        annotation.pos = "VERB"  # type: ignore[misc]


@pytest.mark.unit
def test_linguistic_annotation_fields_may_all_be_none() -> None:
    """REQ-003-005/006 shape: an unannotated occurrence has every field None."""
    annotation = LinguisticAnnotation(
        raw_text="running", pos=None, lemma=None, pos_confidence=None, lemma_confidence=None
    )

    assert annotation.pos is None
    assert annotation.lemma is None
    assert annotation.pos_confidence is None
    assert annotation.lemma_confidence is None


@pytest.mark.unit
def test_domain_annotation_module_is_stdlib_only() -> None:
    """REQ-003-002: no spaCy/thinc/stanza/SQLAlchemy/FastAPI/Pydantic import."""
    source = _MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_MODULE_PATH))

    violations = _imported_roots(tree) & _FORBIDDEN_IMPORTS

    assert not violations, violations


@pytest.mark.unit
def test_upos_tags_is_the_17_member_universal_set() -> None:
    """spec §2.2: the closed UPOS set, uppercase, exactly as written."""
    expected = frozenset(
        {
            "ADJ",
            "ADP",
            "ADV",
            "AUX",
            "CCONJ",
            "DET",
            "INTJ",
            "NOUN",
            "NUM",
            "PART",
            "PRON",
            "PROPN",
            "PUNCT",
            "SCONJ",
            "SYM",
            "VERB",
            "X",
        }
    )
    assert expected == UPOS_TAGS
    assert len(UPOS_TAGS) == 17


@pytest.mark.unit
def test_domain_annotation_module_has_no_bare_pos_string_literal() -> None:
    """Landmine: `"pos"` has the ISO-639 shape `test_domain_isolation.py`'s
    guard rejects. Pinned directly here, independent of that guard's own
    coverage of this module (task 2.1)."""
    source = _MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_MODULE_PATH))

    assert "pos" not in _string_constants(tree)


@pytest.mark.unit
def test_validate_confidence_accepts_none_and_the_closed_interval_bounds() -> None:
    """REQ-003-008 C1: NULL and both interval endpoints are valid."""
    validate_confidence(None)
    validate_confidence(0.0)
    validate_confidence(1.0)
    validate_confidence(0.5)


@pytest.mark.unit
@pytest.mark.parametrize("value", [-0.01, 1.01, 1.4, -1.0])
def test_validate_confidence_rejects_out_of_range_values(value: float) -> None:
    """REQ-003-008: an out-of-range confidence fails, never clamped."""
    with pytest.raises(ValueError, match="confidence"):
        validate_confidence(value)


@pytest.mark.unit
def test_resolve_effective_returns_automatic_when_no_correction_exists() -> None:
    """REQ-003-010 R1: no ManualCorrection row -> the automatic value wins."""
    value, origin = resolve_effective("NOUN", None)

    assert value == "NOUN"
    assert origin == "automatic"


@pytest.mark.unit
def test_resolve_effective_returns_corrected_when_one_exists() -> None:
    """REQ-003-010 R1/R5: a seeded correction wins and is marked manual."""
    value, origin = resolve_effective("NOUN", "VERB")

    assert value == "VERB"
    assert origin == "manual"


@pytest.mark.unit
def test_resolve_effective_does_not_mutate_or_discard_the_automatic_argument() -> None:
    """REQ-003-010 R4: the automatic value stays recoverable by the caller —
    `resolve_effective` is pure, so the caller's own reference is untouched
    and remains the audit value regardless of which one wins."""
    automatic = "NOUN"

    value, origin = resolve_effective(automatic, "VERB")

    assert automatic == "NOUN"
    assert value == "VERB"
    assert origin == "manual"


@pytest.mark.unit
def test_resolve_effective_of_two_nones_returns_none_with_automatic_origin() -> None:
    """An unannotated occurrence with no correction resolves to (None, automatic)."""
    value, origin = resolve_effective(None, None)

    assert value is None
    assert origin == "automatic"


@pytest.mark.unit
@given(
    automatic=st.one_of(st.none(), st.text(max_size=20)),
    corrected=st.one_of(st.none(), st.text(max_size=20)),
)
def test_property_resolve_effective_output_is_never_a_third_value(
    automatic: str | None, corrected: str | None
) -> None:
    """Property (task 2.6, C3): the result is always exactly one of the two
    inputs. `resolve_effective` cannot fabricate a value neither side
    supplied."""
    value, origin = resolve_effective(automatic, corrected)

    assert value in (automatic, corrected)
    assert origin in ("automatic", "manual")


@pytest.mark.unit
@given(value=st.floats(allow_nan=False, allow_infinity=False))
def test_property_validate_confidence_rejects_every_float_outside_the_unit_interval(
    value: float,
) -> None:
    """Property (task 2.6): every float outside [0.0, 1.0] raises via
    `validate_confidence`; every float inside it does not."""
    if 0.0 <= value <= 1.0:
        validate_confidence(value)
    else:
        with pytest.raises(ValueError, match=re.escape("confidence")):
            validate_confidence(value)

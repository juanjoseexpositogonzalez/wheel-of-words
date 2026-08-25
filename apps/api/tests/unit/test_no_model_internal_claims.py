"""Document guard for model-internal claims (REQ-003H-003)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
_PRIMARY_DOCUMENTS = (
    _REPOSITORY_ROOT / "openspec/changes/lemmatization-pos/design.md",
    _REPOSITORY_ROOT / "docs/traceability-matrix.md",
)
_BOUNDARY_DOCUMENTS = (
    _REPOSITORY_ROOT / "docs/constitution.md",
    _REPOSITORY_ROOT / "openspec/changes/spec-003-harden-guards-and-claims/tasks.md",
    _REPOSITORY_ROOT / "openspec/changes/spec-003-harden-guards-and-claims/design.md",
)

_SIGNATURE_FAMILIES = {
    "high_precision_or_scientific_decimal": re.compile(
        r"(?<![\w.])(?:\d+(?:\.\d+)?[eE][+-]?\d+|\d+\.\d{3,})(?![\w%]|\.\d)"
    ),
    "posterior": re.compile(
        r"\b(?:posterior|probabilidad posterior)\b|\bP\((?!\s*\.\.\.\s*\))[^)\n]+\)\s*=",
        re.IGNORECASE,
    ),
    "rule_count": re.compile(
        r"\b(?:\d+[\s-]+(?:rules?|reglas?)|(?:rule|regla)[\s-]+\d+)\b",
        re.IGNORECASE,
    ),
    "tag_to_upos": re.compile(
        r"\b[A-Z]{2,5}\s*(?:→|->|=>)\s*[A-Z]{2,6}\b|\bmapea(?:n)?\s+a\b",
        re.IGNORECASE,
    ),
}


def _find_matches(document: Path) -> dict[str, tuple[str, ...]]:
    text = document.read_text(encoding="utf-8")
    return {
        family: tuple(match.group(0) for match in pattern.finditer(text))
        for family, pattern in _SIGNATURE_FAMILIES.items()
    }


def _matches(text: str) -> dict[str, tuple[str, ...]]:
    return {
        family: tuple(match.group(0) for match in pattern.finditer(text))
        for family, pattern in _SIGNATURE_FAMILIES.items()
    }


@pytest.mark.unit
def test_primary_governed_documents_contain_no_model_internal_claim_signatures() -> None:
    """M1 RED output records the original matching prose before its removal."""
    matches = {document: _find_matches(document) for document in _PRIMARY_DOCUMENTS}

    assert all(
        not match_values
        for document_matches in matches.values()
        for match_values in document_matches.values()
    ), matches


@pytest.mark.unit
@pytest.mark.parametrize(
    ("family", "fixture"),
    [
        ("high_precision_or_scientific_decimal", "The measurement is 0.123."),
        ("posterior", "posterior"),
        ("rule_count", "12 rules"),
        ("tag_to_upos", "TAG -> UPOS"),
    ],
)
def test_each_signature_family_reports_its_synthetic_fixture(family: str, fixture: str) -> None:
    """M2: each signature family has a non-empty positive control."""
    assert _matches(fixture)[family]


@pytest.mark.unit
def test_boundary_content_does_not_match_model_internal_claim_signatures() -> None:
    """M3: ordinary documentation syntax remains outside the four signatures."""
    boundary_text = "\n".join(
        document.read_text(encoding="utf-8") for document in _BOUNDARY_DOCUMENTS
    )
    legitimate_literals = (
        "test:code ≈2.5:1",
        "100%",
        "§2.1",
        "sha256:83e3b47ef0173b50a8f07dac41ba26a3e61734d83481995a25a97c3e5e3e79de",
        "2.0.0",
        "2026-08-25",
        "[A-Z]{2,5}",
        "(→|->|=>)",
    )

    assert all(document.is_file() for document in _BOUNDARY_DOCUMENTS)
    assert "[A-Z]{2,5}" in boundary_text
    assert "(→|->|=>)" in boundary_text
    assert not any(
        match_values
        for literal in legitimate_literals
        for match_values in _matches(literal).values()
    )

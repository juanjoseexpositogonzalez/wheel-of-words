"""Document guard for model-internal claims (REQ-003H-003)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
_PRIMARY_DOCUMENTS = (
    _REPOSITORY_ROOT / "openspec/specs/003-lemmatization-pos/spec.md",
    _REPOSITORY_ROOT / "docs/traceability-matrix.md",
)
_DOCS_DIRECTORY = _REPOSITORY_ROOT / "docs"
_ARCHIVED_CHANGE = (
    _REPOSITORY_ROOT / "openspec/changes/archive/2026-08-26-spec-003-harden-guards-and-claims"
)
_GOVERNED_DOCUMENTS = (
    *_PRIMARY_DOCUMENTS,
    _ARCHIVED_CHANGE / "design.md",
    _ARCHIVED_CHANGE / "proposal.md",
    _ARCHIVED_CHANGE / "tasks.md",
    _ARCHIVED_CHANGE / "specs/002-text-import/spec.md",
    _ARCHIVED_CHANGE / "specs/003-lemmatization-pos/spec.md",
)

_SIGNATURE_FAMILIES = {
    "high_precision_or_scientific_decimal": re.compile(
        r"(?<![\w.])(?:\d+(?:\.\d+)?[eE][+-]?\d+|\d+\.\d{3,})(?![\w%]|\.\d)"
    ),
    "posterior": re.compile(
        r"\b(?:posterior\s*(?:=|:)|probabilidad posterior\s*(?:=|:))|"
        r"\bP\((?!\s*\.\.\.\s*\))[^)\n]+\)\s*=",
        re.IGNORECASE,
    ),
    "rule_count": re.compile(
        r"\b(?:\d+[\s-]+(?:rules?|reglas?)|(?:rule|regla)[\s-]+\d+)\b",
        re.IGNORECASE,
    ),
    "tag_to_upos": re.compile(
        r"\b(?!(?:RED|GREEN)\s*(?:→|->|=>)\s*(?:RED|GREEN)\b)"
        r"[A-Z]{2,5}\s*(?:→|->|=>)\s*[A-Z]{2,6}\b|\bmapea(?:n)?\s+a\b"
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


def _governed_documents() -> tuple[Path, ...]:
    return _GOVERNED_DOCUMENTS


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
        ("posterior", "posterior = 1"),
        ("rule_count", "12 rules"),
        ("tag_to_upos", "TAG -> UPOS"),
    ],
)
def test_each_signature_family_reports_its_synthetic_fixture(family: str, fixture: str) -> None:
    """M2: each signature family has a non-empty positive control."""
    assert _matches(fixture)[family]


@pytest.mark.unit
def test_governed_document_set_excludes_legitimate_documentation_syntax() -> None:
    """M3: the full docs tree and this change's artifacts remain false-positive free."""
    documents = _governed_documents()
    matches = {
        document.relative_to(_REPOSITORY_ROOT): _find_matches(document) for document in documents
    }
    documentation_text = "\n".join(
        document.read_text(encoding="utf-8")
        for document in (*_DOCS_DIRECTORY.rglob("*.md"), *documents)
    )
    legitimate_literals = (
        "503 backend",
        "100%",
        "90%",
        "80%",
        "test:code ≈2.5:1",
        "§2.1",
        "SHA-256",
        "2.0.0",
        "2026-08-25",
        "[A-Z]{2,5}",
        "(→|->|=>)",
    )

    assert all(document.is_file() for document in documents)
    assert all(literal in documentation_text for literal in legitimate_literals)
    assert not any(
        match_values
        for literal in legitimate_literals
        for match_values in _matches(literal).values()
    )
    assert not any(
        match_values
        for document_matches in matches.values()
        for match_values in document_matches.values()
    ), matches

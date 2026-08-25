"""Unit tests for the shared JSON guard-binding implementation.

REQ-003H-001 / AC-003H-01. The manifest-pinning mutation observed these exact
results after GREEN: ``_positional_only_is_exempt(...) is True`` and
``is_exempt(...) is False``. A name-and-position predicate alone cannot detect
the renamed sibling because the renamed key occupies a legitimate property
position; the pinned declared-property manifest detects that the definition
changed.
"""

from __future__ import annotations

import importlib.resources
import json
from pathlib import Path
from typing import Any

import pytest
from _guard_binding import OwningDefinition, is_exempt, render, walk_json

_OCCURRENCE_PATH = ("$", "$defs", "occurrence")
_OCCURRENCE_EXEMPT = frozenset(
    {"lemma", "lemma_confidence", "lemma_origin", "automatic_lemma"}
)


def _annotation_schema() -> dict[str, Any]:
    path = importlib.resources.files("wheel_vocabulary.api.schemas").joinpath("annotation.v1.json")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _occurrence_owner(document: dict[str, Any]) -> OwningDefinition:
    properties = document["$defs"]["occurrence"]["properties"]
    return OwningDefinition(
        path=_OCCURRENCE_PATH,
        declared=frozenset(properties),
        exempt=_OCCURRENCE_EXEMPT,
    )


def _property_key_match(document: dict[str, Any], name: str) -> tuple[tuple[str, ...], str, str]:
    return next(
        match
        for match in walk_json(document)
        if match == (_OCCURRENCE_PATH + ("properties", name), "key", name)
    )


def _positional_only_is_exempt(
    match: tuple[tuple[str, ...], str, str], owner: OwningDefinition
) -> bool:
    """Control predicate deliberately omitting the declared-manifest check."""
    segments, kind, text = match
    return (
        kind == "key"
        and text in owner.exempt
        and segments[:-2] == owner.path
        and segments[-2] == "properties"
    )


@pytest.mark.unit
def test_walk_json_preserves_dotted_keys_as_single_segments() -> None:
    document = {"occurrence.extra": {"lemma": "run"}}

    matches = list(walk_json(document))

    assert (("$", "occurrence.extra"), "key", "occurrence.extra") in matches
    assert (("$", "occurrence.extra", "lemma"), "key", "lemma") in matches
    assert render(("$", "occurrence.extra", "lemma"), "key") == "$.occurrence.extra.lemma (key)"


@pytest.mark.unit
def test_is_exempt_requires_an_exact_name_at_an_intact_owning_property_position() -> None:
    document = _annotation_schema()
    owner = _occurrence_owner(document)

    assert is_exempt(_property_key_match(document, "lemma"), document, [owner])
    assert not is_exempt(_property_key_match(document, "position"), document, [owner])


@pytest.mark.unit
def test_is_exempt_rejects_an_allow_listed_name_outside_the_declared_property_set() -> None:
    document = _annotation_schema()
    actual_owner = _occurrence_owner(document)
    owner = OwningDefinition(
        path=actual_owner.path,
        declared=actual_owner.declared - {"lemma"},
        exempt=actual_owner.exempt,
    )

    assert not is_exempt(_property_key_match(document, "lemma"), document, [owner])


@pytest.mark.unit
def test_manifest_pinning_catches_sibling_property_renamed_into_owning_definition() -> None:
    """Mandate 2 observed outputs: positional-only control ``True``; manifest guard ``False``."""
    document = _annotation_schema()
    owner = _occurrence_owner(document)
    properties = document["$defs"]["occurrence"]["properties"]
    properties["lemma"] = properties.pop("raw_text")
    match = _property_key_match(document, "lemma")

    assert _positional_only_is_exempt(match, owner) is True
    assert is_exempt(match, document, [owner]) is False


@pytest.mark.unit
def test_the_binding_helper_exists_once() -> None:
    """AC-003H-01 M2: both JSON guards import the one shared helper module."""
    tests_dir = Path(__file__).parent
    helper_modules = list(tests_dir.glob("_guard_binding.py"))
    guard_sources = {
        guard: (tests_dir / guard).read_text(encoding="utf-8")
        for guard in ("test_no_lemma_naming.py", "test_annotation_contract.py")
    }

    assert helper_modules == [tests_dir / "_guard_binding.py"]
    assert all("from _guard_binding import" in source for source in guard_sources.values())

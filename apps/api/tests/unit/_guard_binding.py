"""Shared structural binding for JSON and OpenAPI naming guards."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

type JsonMatch = tuple[tuple[str, ...], str, str]


@dataclass(frozen=True)
class OwningDefinition:
    """A definition's pinned properties and its genuine lemma-bearing subset."""

    path: tuple[str, ...]
    declared: frozenset[str]
    exempt: frozenset[str]


def walk_json(document: Any, segments: tuple[str, ...] = ("$",)) -> Iterator[JsonMatch]:
    """Yield every JSON key and string value with traversal-produced segments."""
    if isinstance(document, dict):
        for key, value in document.items():
            key_segments = segments + (key,)
            yield key_segments, "key", key
            yield from walk_json(value, key_segments)
    elif isinstance(document, list):
        for index, item in enumerate(document):
            yield from walk_json(item, segments + (f"[{index}]",))
    elif isinstance(document, str):
        yield segments, "value", document


def render(segments: tuple[str, ...], kind: str) -> str:
    """Render a traversal path for diagnostics without reconstructing segments."""
    path = ""
    for segment in segments:
        path += segment if segment.startswith("[") else ("" if not path else ".") + segment
    return f"{path} ({kind})"


def _declared_properties(document: Any, owner: OwningDefinition) -> frozenset[str] | None:
    definition = document
    try:
        for segment in owner.path[1:]:
            definition = definition[segment]
        properties = definition["properties"]
    except (KeyError, TypeError):
        return None
    return frozenset(properties) if isinstance(properties, dict) else None


def _is_owner_position(match: JsonMatch, owner: OwningDefinition) -> bool:
    segments, kind, text = match
    if kind == "key" and segments == owner.path + ("properties", text):
        return True
    if kind != "value":
        return False
    if segments[:-1] == owner.path + ("required",):
        return True
    return segments == owner.path + ("properties", text, "title")


def is_exempt(match: JsonMatch, document: Any, owners: Sequence[OwningDefinition]) -> bool:
    """Return whether a match is a manifest-pinned exempt property key."""
    _, _, text = match
    for owner in owners:
        if (
            _is_owner_position(match, owner)
        ) and (
            text in owner.exempt
            and owner.exempt <= owner.declared
            and _declared_properties(document, owner) == owner.declared
        ):
            return True
    return False

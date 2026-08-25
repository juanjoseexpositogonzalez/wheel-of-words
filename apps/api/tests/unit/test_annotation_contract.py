"""Wire-contract tests for the annotation endpoint — design "API contract",
spec §2.1-2.5, §4 (task 5.2, SPEC-003 slice 5).

A contract distinct from `import.v1.json` v1 (REQ-003-017): grouped by
occurrence, not by normalized form, and `import.v1.json` MUST stay
byte-identical (pinned separately in `test_import_contract.py`).

Three things are pinned here:

1. Both confidence keys are ALWAYS present on every occurrence, `null`
   included — the key is never omitted (§2.3 C5, REQ-003-009).
2. `provenance` is `null` when the import has never been annotated, and an
   object with five non-null fields once it has (REQ-003-007).
3. The error envelope gains three new codes on top of the reused
   `IMPORT_NOT_FOUND` (spec §4): `UNSUPPORTED_LANGUAGE`, `ANALYZER_
   UNAVAILABLE`, `ANNOTATION_FAILED`.

REQ-003-007, REQ-003-009, REQ-003-010, REQ-003-017, REQ-003-018 (AC-003-09,
AC-003-18).
"""

from __future__ import annotations

import importlib.resources
import json
import re
from typing import Any

import jsonschema
import pytest
from pydantic import ValidationError

from wheel_vocabulary.api.dtos.annotation import (
    AnnotationOccurrenceResponse,
    AnnotationProvenanceResponse,
    AnnotationResultResponse,
)

_FORBIDDEN_LEMMA_PATTERN = re.compile("lemma|lemas|lexeme|lexema", re.IGNORECASE)
_ALLOWED_LEMMA_SYMBOLS = frozenset(
    {"lemma", "lemma_confidence", "lemma_origin", "automatic_lemma", "lemmatizer"}
)

_SUCCESS_OCCURRENCE: dict[str, Any] = {
    "position": 3,
    "raw_text": "ran",
    "pos": "VERB",
    "pos_origin": "automatic",
    "automatic_pos": "VERB",
    "pos_confidence": 0.98,
    "lemma": "run",
    "lemma_origin": "automatic",
    "automatic_lemma": "run",
    "lemma_confidence": None,
}

_SUCCESS_BODY: dict[str, Any] = {
    "id": 7,
    "provenance": {
        "source": "spacy",
        "model_name": "en_core_web_sm",
        "model_version": "3.8.0",
        "language": "en",
        "processed_at": "2026-08-23T16:00:00Z",
    },
    "occurrences": [_SUCCESS_OCCURRENCE],
}

_UNANNOTATED_BODY: dict[str, Any] = {"id": 7, "provenance": None, "occurrences": []}


def _schema() -> dict[str, Any]:
    path = importlib.resources.files("wheel_vocabulary.api.schemas").joinpath("annotation.v1.json")
    loaded: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return loaded


def _json_strings(node: Any, path: str) -> list[tuple[str, str]]:
    """Every JSON object key and string value, with its path — mirrors
    `test_no_lemma_naming.py::_json_strings` for the schema file itself,
    which that guard does not scan directly (it only scans `import.v1.json`
    and the served OpenAPI document)."""
    found: list[tuple[str, str]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            found.append((f"{path}.{key} (key)", key))
            found.extend(_json_strings(value, f"{path}.{key}"))
    elif isinstance(node, list):
        for index, item in enumerate(node):
            found.extend(_json_strings(item, f"{path}[{index}]"))
    elif isinstance(node, str):
        found.append((f"{path} (value)", node))
    return found


@pytest.mark.unit
def test_schema_is_draft_2020_12_and_versioned() -> None:
    """Mirrors import.v1.json so the contract surface stays uniform."""
    schema = _schema()

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == "urn:wheel-vocabulary:annotation:v1"


@pytest.mark.unit
def test_schema_requires_id_provenance_and_occurrences() -> None:
    schema = _schema()

    assert set(schema["required"]) == {"id", "provenance", "occurrences"}
    assert schema["additionalProperties"] is False


@pytest.mark.unit
def test_schema_accepts_an_annotated_occurrence() -> None:
    jsonschema.validate(_SUCCESS_BODY, _schema())


@pytest.mark.unit
def test_schema_accepts_a_never_annotated_import() -> None:
    """`provenance` is `null`, `occurrences` is an empty list — not an error."""
    jsonschema.validate(_UNANNOTATED_BODY, _schema())


@pytest.mark.unit
def test_schema_rejects_an_occurrence_missing_the_lemma_confidence_key() -> None:
    """C5: the key MUST be present even when the value would be `null`."""
    broken_occurrence = {k: v for k, v in _SUCCESS_OCCURRENCE.items() if k != "lemma_confidence"}
    broken = {**_SUCCESS_BODY, "occurrences": [broken_occurrence]}

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(broken, _schema())


@pytest.mark.unit
def test_schema_rejects_an_out_of_range_confidence() -> None:
    broken_occurrence = {**_SUCCESS_OCCURRENCE, "pos_confidence": 1.4}
    broken = {**_SUCCESS_BODY, "occurrences": [broken_occurrence]}

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(broken, _schema())


@pytest.mark.unit
def test_schema_rejects_a_pos_origin_outside_automatic_or_manual() -> None:
    broken_occurrence = {**_SUCCESS_OCCURRENCE, "pos_origin": "guessed"}
    broken = {**_SUCCESS_BODY, "occurrences": [broken_occurrence]}

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(broken, _schema())


@pytest.mark.unit
def test_schema_accepts_the_error_envelope_for_every_annotation_code() -> None:
    for code in (
        "IMPORT_NOT_FOUND",
        "UNSUPPORTED_LANGUAGE",
        "ANALYZER_UNAVAILABLE",
        "ANNOTATION_FAILED",
    ):
        envelope = {"error": {"code": code, "message": "m"}}
        jsonschema.validate(envelope, _schema()["$defs"]["error"])


@pytest.mark.unit
def test_schema_rejects_an_unknown_error_code() -> None:
    envelope = {"error": {"code": "SOMETHING_ELSE", "message": "m"}}

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(envelope, _schema()["$defs"]["error"])


def _path_segments(where: str) -> list[str]:
    """Mirrors `test_no_lemma_naming.py::_path_segments` (R2, Judgment Day
    round 2) for the same reason `_json_strings` above already mirrors its
    sibling: this file has no import dependency on that test module, and
    duplicating the small pure helper keeps that independence."""
    bare = where.split(" (", 1)[0]
    return [re.sub(r"\[\d+\]$", "", part) for part in bare.split(".")]


# The one `$defs` component in `annotation.v1.json` that genuinely declares
# `lemma`/`lemma_confidence` — mirrors
# `test_no_lemma_naming.py::_SCHEMA_OWNING_PATH_SEGMENTS["annotation.v1.json"]`
# (R2 remediation: that binding used to be the empty string, matching every
# path unconditionally; it is now this exact owning segment).
_OWNING_PATH_SEGMENT = "occurrence"


@pytest.mark.unit
def test_the_pinned_json_schema_names_no_lemma_or_lexeme_outside_the_allow_list() -> None:
    """AC-003-24: the versioned schema is in scope for the narrowed guard
    the same way `import.v1.json` is (task 1.7); this file is the schema's
    own leg since `test_no_lemma_naming.py::_SCHEMA_PATH` only covers
    `import.v1.json`.

    R2 (Judgment Day round 2): the predicate here used to be the UNBOUND
    pre-C1 shape — `text not in _ALLOWED_LEMMA_SYMBOLS` alone, with no
    binding to WHERE in the document the match occurs — even though C1
    bound every other leg (`_LEMMA_OWNING_FILES`, `_LEMMA_OWNING_COLUMNS`,
    `_OPENAPI_LEMMA_OWNING_SCHEMA`) to its owning declaration site. This test
    was not touched by the C1 fix round despite
    `docs/traceability-matrix.md` citing it as C1 evidence. Now bound to
    `_OWNING_PATH_SEGMENT` via the same exact-segment-match predicate
    `test_no_lemma_naming.py::_json_violations` uses.
    """
    violations = [
        f"{where} -> {text!r}"
        for where, text in _json_strings(_schema(), "$")
        if _FORBIDDEN_LEMMA_PATTERN.search(text)
        and not (text in _ALLOWED_LEMMA_SYMBOLS and _OWNING_PATH_SEGMENT in _path_segments(where))
    ]

    assert not violations, "lemma naming leaked into annotation.v1.json:\n" + "\n".join(violations)


@pytest.mark.unit
def test_renaming_a_non_owning_property_to_lemma_still_fails_outside_the_allow_list() -> None:
    """R2: proves the predicate above is genuinely BOUND to
    `_OWNING_PATH_SEGMENT`, not merely `text not in _ALLOWED_LEMMA_SYMBOLS`
    on its own — a rename that lands the bare allow-listed name `lemma` on
    `$defs.provenance.properties.source` (a field `provenance` does not
    legitimately own) must still be reported.

    RED (before the fix, verified 2026-08-25): the unbound predicate
    `text not in _ALLOWED_LEMMA_SYMBOLS` alone found zero violations for
    this exact mutation — `lemma` IS in `_ALLOWED_LEMMA_SYMBOLS`, and the old
    check never looked at WHERE the match occurred at all.
    """
    mutated = _schema()
    provenance_properties = mutated["$defs"]["provenance"]["properties"]
    provenance_properties["lemma"] = provenance_properties.pop("source")

    violations = [
        f"{where} -> {text!r}"
        for where, text in _json_strings(mutated, "$")
        if _FORBIDDEN_LEMMA_PATTERN.search(text)
        and not (text in _ALLOWED_LEMMA_SYMBOLS and _OWNING_PATH_SEGMENT in _path_segments(where))
    ]

    assert violations
    assert any("lemma" in violation for violation in violations)


# --------------------------------------------------------------------------
# DTOs
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_occurrence_dto_declares_every_wire_field() -> None:
    assert set(AnnotationOccurrenceResponse.model_fields) == {
        "position",
        "raw_text",
        "pos",
        "pos_origin",
        "automatic_pos",
        "pos_confidence",
        "lemma",
        "lemma_origin",
        "automatic_lemma",
        "lemma_confidence",
    }


@pytest.mark.unit
def test_occurrence_dto_serialises_a_null_confidence_as_json_null() -> None:
    dumped = AnnotationOccurrenceResponse(**_SUCCESS_OCCURRENCE).model_dump()

    assert "lemma_confidence" in dumped
    assert dumped["lemma_confidence"] is None
    assert dumped["pos_confidence"] == 0.98


@pytest.mark.unit
def test_result_dto_allows_a_null_provenance() -> None:
    dumped = AnnotationResultResponse(id=7, provenance=None, occurrences=[]).model_dump()

    assert dumped == _UNANNOTATED_BODY


@pytest.mark.unit
def test_result_dto_round_trips_an_annotated_import_through_the_schema() -> None:
    dumped = AnnotationResultResponse(
        id=7,
        provenance=AnnotationProvenanceResponse(
            source="spacy",
            model_name="en_core_web_sm",
            model_version="3.8.0",
            language="en",
            processed_at="2026-08-23T16:00:00Z",
        ),
        occurrences=[AnnotationOccurrenceResponse(**_SUCCESS_OCCURRENCE)],
    ).model_dump(mode="json")

    jsonschema.validate(dumped, _schema())


@pytest.mark.unit
def test_dtos_forbid_extra_fields() -> None:
    with pytest.raises(ValidationError):
        AnnotationOccurrenceResponse(**_SUCCESS_OCCURRENCE, unexpected="x")

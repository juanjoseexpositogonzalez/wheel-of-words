"""Wire-contract tests for the import endpoint — design §9.2-9.3 (T1B04, T212).

Three things are pinned here, all of them decisions rather than details:

1. Cut 2 adds ``id`` to the success body **additively** (T1B13's completion).
   Cut 1b omitted the field entirely because no ``Book`` row existed yet;
   ``null`` was never correct either, because it would have asserted the
   concept existed with an unknown value. A body carrying ``"id": null`` must
   still FAIL validation now, for a different reason: `id` is a required
   integer, and `null` does not satisfy `type: integer`.
2. Every failure on this route shares one envelope, ``{"error": {code, message}}``.
   Without the ``INVALID_REQUEST`` handler, FastAPI's native ``{"detail": [...]}``
   would give the capability two different 422 shapes (spec §4).
3. No error body carries imported text, a byte offset, a path, or a stack trace.

**AC-003-12 / AC-003-18 (SPEC-003 slice 5, task 5.1).** `import.v1.json` MUST
stay byte-identical while `003-lemmatization-pos` ships its own, separate
`annotation.v1.json` contract. `test_the_schema_stays_byte_identical_to_the_
pre_annotation_baseline` pins the file's SHA-256 digest and byte length
computed BEFORE any SPEC-003 slice-5 code was written, so any accidental
schema drift — even a single reordered key or trailing newline — fails this
test rather than passing silently. This is an approval test: it PASSES
immediately (baseline == baseline), not a RED-then-GREEN test — its job is to
stay green across every following change in this slice (safety net).

REQ-002-001, REQ-002-006, REQ-002-008, REQ-002-012, REQ-002-018, spec §4,
design §9.2-9.3, REQ-003-012, REQ-003-017 (AC-003-12, AC-003-18).
"""

from __future__ import annotations

import hashlib
import importlib.resources
import json
from typing import Any

import jsonschema
import pytest
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from wheel_vocabulary.api.dtos.imports import (
    FormFrequencyResponse,
    ImportErrorBody,
    ImportErrorResponse,
    ImportResultResponse,
)
from wheel_vocabulary.api.errors import (
    request_validation_error_handler,
    text_import_error_handler,
)
from wheel_vocabulary.application.imports.errors import (
    FileTooLargeError,
    ImportNotFoundError,
    InvalidEncodingError,
    InvalidFileTypeError,
    PersistenceFailedError,
    TextImportError,
)

_SUCCESS_BODY: dict[str, Any] = {
    "id": 1,
    "import_status": "succeeded",
    "distinct_form_count": 2,
    "total_token_count": 3,
    "forms": [
        {"normalized_form": "strasse", "display_form": "Straße", "frequency": 2},
        {"normalized_form": "zebra", "display_form": "zebra", "frequency": 1},
    ],
}


def _schema() -> dict[str, Any]:
    path = importlib.resources.files("wheel_vocabulary.api.schemas").joinpath("import.v1.json")
    loaded: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return loaded


def _request() -> Request:
    return Request({"type": "http", "method": "POST", "path": "/api/v1/imports", "headers": []})


def _body_of(response: object) -> dict[str, Any]:
    decoded: dict[str, Any] = json.loads(response.body)  # type: ignore[attr-defined]
    return decoded


@pytest.mark.unit
def test_success_dto_declares_an_id_field() -> None:
    """T212: additive over cut 1b, which had no `Book` row to report."""
    assert "id" in ImportResultResponse.model_fields
    assert set(ImportResultResponse.model_fields) == {
        "id",
        "import_status",
        "distinct_form_count",
        "total_token_count",
        "forms",
    }


@pytest.mark.unit
def test_success_dto_serialises_with_the_id_key() -> None:
    """The persisted import's identity is now a required part of the shape."""
    dumped = ImportResultResponse(
        id=7,
        import_status="succeeded",
        distinct_form_count=1,
        total_token_count=1,
        forms=[FormFrequencyResponse(normalized_form="a", display_form="A", frequency=1)],
    ).model_dump()

    assert dumped["id"] == 7
    assert dumped["forms"][0]["display_form"] == "A"


@pytest.mark.unit
def test_success_dto_requires_the_id_field() -> None:
    """A missing `id` must fail loudly, not silently default to something."""
    with pytest.raises(ValidationError):
        ImportResultResponse(
            import_status="succeeded",
            distinct_form_count=0,
            total_token_count=0,
            forms=[],
        )


@pytest.mark.unit
@pytest.mark.parametrize(
    ("model", "payload"),
    [
        (ImportErrorBody, {"code": "X", "message": "m", "detail": "leak"}),
        (
            FormFrequencyResponse,
            {"normalized_form": "a", "display_form": "A", "frequency": 1, "lemma": "a"},
        ),
    ],
)
def test_dtos_forbid_extra_fields(model: type, payload: dict[str, Any]) -> None:
    """`extra="forbid"` mirrors dtos/health.py and keeps the schema authoritative."""
    with pytest.raises(ValidationError):
        model(**payload)


@pytest.mark.unit
def test_schema_is_draft_2020_12_and_versioned() -> None:
    """Mirrors health.v1.json so the contract surface stays uniform."""
    schema = _schema()

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == "urn:wheel-vocabulary:import:v1"


@pytest.mark.unit
def test_schema_declares_and_requires_the_id_property() -> None:
    """T212: `id` is added additively and is required — every row has one now."""
    schema = _schema()

    assert schema["properties"]["id"]["type"] == "integer"
    assert "id" in schema["required"]
    assert schema["additionalProperties"] is False


@pytest.mark.unit
def test_schema_accepts_the_documented_success_body() -> None:
    """The positive leg — without it the rejection below could be vacuous."""
    jsonschema.validate(_SUCCESS_BODY, _schema())


@pytest.mark.unit
def test_schema_rejects_a_body_carrying_a_null_id() -> None:
    """The load-bearing assertion: `"id": null` is a contract violation, not a value."""
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({**_SUCCESS_BODY, "id": None}, _schema())


@pytest.mark.unit
def test_schema_rejects_a_zero_frequency_row() -> None:
    """REQ-002-017: no listed form may carry a frequency below 1."""
    broken = {
        **_SUCCESS_BODY,
        "forms": [{"normalized_form": "a", "display_form": "A", "frequency": 0}],
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(broken, _schema())


@pytest.mark.unit
def test_schema_accepts_the_error_envelope() -> None:
    """Every failure shares one shape (spec §4)."""
    envelope = {"error": {"code": "FILE_TOO_LARGE", "message": "El archivo supera el límite."}}

    jsonschema.validate(envelope, _schema()["$defs"]["error"])


@pytest.mark.unit
@pytest.mark.parametrize(
    ("error", "expected_status", "expected_code"),
    [
        (InvalidFileTypeError(), 422, "INVALID_FILE_TYPE"),
        (FileTooLargeError(limit=64), 413, "FILE_TOO_LARGE"),
        (InvalidEncodingError(), 422, "INVALID_ENCODING"),
        (ImportNotFoundError(), 404, "IMPORT_NOT_FOUND"),
        (PersistenceFailedError(), 500, "PERSISTENCE_FAILURE"),
    ],
)
def test_handler_maps_each_error_to_its_status_and_envelope(
    error: TextImportError, expected_status: int, expected_code: str
) -> None:
    """Design §9.2: one handler, one envelope, the status carried by the type."""
    response = text_import_error_handler(_request(), error)

    assert response.status_code == expected_status
    assert _body_of(response) == {"error": {"code": expected_code, "message": error.message}}


@pytest.mark.unit
def test_request_validation_is_reported_in_the_same_envelope() -> None:
    """AC-002-01: a JSON body instead of a file part must not leak FastAPI's shape."""
    response = request_validation_error_handler(
        _request(), RequestValidationError([{"loc": ("body", "file"), "msg": "Field required"}])
    )

    assert response.status_code == 422
    assert _body_of(response)["error"]["code"] == "INVALID_REQUEST"


@pytest.mark.unit
def test_validation_envelope_never_echoes_the_rejected_input() -> None:
    """Art. X.2: FastAPI's native detail carries the submitted value; ours must not."""
    response = request_validation_error_handler(
        _request(),
        RequestValidationError(
            [{"loc": ("body", "path"), "msg": "x", "input": "/etc/zzqxsentinel.txt"}]
        ),
    )

    assert "zzqxsentinel" not in response.body.decode()
    assert set(_body_of(response)["error"]) == {"code", "message"}


@pytest.mark.unit
def test_error_dto_round_trips_through_the_schema() -> None:
    """The Pydantic model and the pinned schema describe the same envelope."""
    dumped = ImportErrorResponse(
        error=ImportErrorBody(code="INVALID_ENCODING", message="UTF-8")
    ).model_dump()

    jsonschema.validate(dumped, _schema()["$defs"]["error"])


# --------------------------------------------------------------------------
# SPEC-003 slice 5 (task 5.1) — AC-003-12, AC-003-18: the SPEC-002 contract
# is untouched by the annotation capability.
# --------------------------------------------------------------------------

_PRE_ANNOTATION_SHA256 = "def94cb6361531b21f382c862120914419b867b6601aa58d763d49d65a554258"
_PRE_ANNOTATION_BYTE_LENGTH = 1852


@pytest.mark.unit
def test_the_schema_stays_byte_identical_to_the_pre_annotation_baseline() -> None:
    """AC-003-18: `import.v1.json` MUST NOT gain a property or otherwise change.

    The digest and length were computed from `import.v1.json` on the
    `lemmatization-pos` tracker branch, immediately before slice 5 (API +
    frontend) touched any file — the last commit to modify this schema was
    cut 2 of `002-text-import` (T212). Approval test: passes on this first
    run and must keep passing through every following change in this slice.
    """
    path = importlib.resources.files("wheel_vocabulary.api.schemas").joinpath("import.v1.json")
    raw = path.read_bytes()

    assert len(raw) == _PRE_ANNOTATION_BYTE_LENGTH
    assert hashlib.sha256(raw).hexdigest() == _PRE_ANNOTATION_SHA256

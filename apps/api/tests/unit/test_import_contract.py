"""Wire-contract tests for the import endpoint — design §9.2-9.3 (T1B04).

Three things are pinned here, all of them decisions rather than details:

1. The cut-1b success body OMITS ``id`` entirely — it is not ``"id": null``.
   There is no ``Book`` row in this cut, so there is no identity to report, and
   ``null`` would assert that the concept exists with an unknown value. The
   schema enforces this mechanically through ``additionalProperties: false``,
   which is why a body carrying ``"id": null`` must FAIL validation.
2. Every failure on this route shares one envelope, ``{"error": {code, message}}``.
   Without the ``INVALID_REQUEST`` handler, FastAPI's native ``{"detail": [...]}``
   would give the capability two different 422 shapes (spec §4).
3. No error body carries imported text, a byte offset, a path, or a stack trace.

REQ-002-001, REQ-002-012, REQ-002-018, spec §4, design §9.2-9.3.
"""

from __future__ import annotations

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
    TextImportError,
)

_SUCCESS_BODY: dict[str, Any] = {
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
def test_success_dto_declares_no_id_field_at_all() -> None:
    """T1B13: omission says the true thing — this cut has no import identity."""
    assert "id" not in ImportResultResponse.model_fields
    assert set(ImportResultResponse.model_fields) == {
        "import_status",
        "distinct_form_count",
        "total_token_count",
        "forms",
    }


@pytest.mark.unit
def test_success_dto_serialises_without_an_id_key() -> None:
    """A declared-but-None field would serialise as `"id": null`. There is none."""
    dumped = ImportResultResponse(
        import_status="succeeded",
        distinct_form_count=1,
        total_token_count=1,
        forms=[FormFrequencyResponse(normalized_form="a", display_form="A", frequency=1)],
    ).model_dump()

    assert "id" not in dumped
    assert dumped["forms"][0]["display_form"] == "A"


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
def test_schema_declares_no_id_property_and_does_not_require_it() -> None:
    """Cut 2 adds `id` additively; cut 1b must not pre-declare it as nullable."""
    schema = _schema()

    assert "id" not in schema["properties"]
    assert "id" not in schema["required"]
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

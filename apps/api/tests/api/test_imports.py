"""API-layer tests for POST /api/v1/imports (T1B15).

The endpoint contract, end to end through the real FastAPI stack: the ordered
gate, the shared error envelope, and the ordered frequency table computed by the
cut-1a domain.

The `id` assertions are load-bearing. This cut writes no ``Book`` row, so the
success body omits ``id`` entirely rather than reporting ``"id": null``. A null
would assert that the concept exists with an unknown value, which is false, and
would make cut 2 a semantic change to a field clients already read instead of a
purely additive one. ``"id" in body`` must therefore fail whether the value is an
integer or ``None``.

REQ-002-001, REQ-002-002, REQ-002-003, REQ-002-004, REQ-002-006 (response half),
REQ-002-012, REQ-002-018 (response half).
"""

from __future__ import annotations

import importlib.resources
import json
from typing import Any

import jsonschema
import pytest
from fastapi.testclient import TestClient

from wheel_vocabulary.api.dependencies import get_import_text
from wheel_vocabulary.api.main import create_app
from wheel_vocabulary.application.imports.use_cases import ImportText
from wheel_vocabulary.infrastructure.text_extraction import PlainTextExtractor

_ENDPOINT = "/api/v1/imports"
_SCHEMA: dict[str, Any] = json.loads(
    importlib.resources.files("wheel_vocabulary.api.schemas")
    .joinpath("import.v1.json")
    .read_text(encoding="utf-8")
)


@pytest.fixture
def client() -> TestClient:
    """A client whose import limit is the production default."""
    return TestClient(create_app())


def _client_with_limit(limit: int) -> TestClient:
    """A client whose import limit is overridden, mirroring the health fixtures."""
    app = create_app()
    app.dependency_overrides[get_import_text] = lambda: ImportText(
        extractor=PlainTextExtractor(), max_size_bytes=limit
    )
    return TestClient(app)


def _upload(
    client: TestClient,
    body: bytes,
    *,
    filename: str = "sample.txt",
    content_type: str = "text/plain",
) -> Any:
    return client.post(_ENDPOINT, files={"file": (filename, body, content_type)})


@pytest.mark.unit
def test_a_synthetic_txt_upload_is_created(client: TestClient) -> None:
    """AC-002-01 success leg: a multipart `.txt` yields 201 with the table."""
    response = _upload(client, b"uno dos dos")

    assert response.status_code == 201
    assert response.json()["import_status"] == "succeeded"


@pytest.mark.unit
def test_the_success_body_omits_the_id_field_entirely(client: TestClient) -> None:
    """T1B13: omission, not `"id": null` — there is no import identity in this cut."""
    body = _upload(client, b"uno dos").json()

    assert "id" not in body
    assert set(body) == {"import_status", "distinct_form_count", "total_token_count", "forms"}


@pytest.mark.unit
def test_the_success_body_validates_against_the_pinned_schema(client: TestClient) -> None:
    """The schema forbids additional properties, so a stray `id` fails here too."""
    jsonschema.validate(_upload(client, b"uno dos dos tres").json(), _SCHEMA)


@pytest.mark.unit
def test_the_response_carries_the_schema_version_header(client: TestClient) -> None:
    """Mirrors GET /api/v1/health, so contract versioning stays uniform."""
    assert _upload(client, b"hola").headers.get("x-schema-version") == "1"


@pytest.mark.unit
def test_each_row_carries_both_the_grouping_key_and_the_display_form(
    client: TestClient,
) -> None:
    """AC-002-23/24: `Straße straße STRASSE Straße` is one row displayed `Straße`."""
    body = _upload(client, "Stra\u00dfe stra\u00dfe STRASSE Stra\u00dfe".encode()).json()

    assert body["forms"] == [
        {"normalized_form": "strasse", "display_form": "Stra\u00dfe", "frequency": 4}
    ]
    assert body["distinct_form_count"] == 1
    assert body["total_token_count"] == 4


@pytest.mark.unit
def test_rows_arrive_already_ordered_by_the_grouping_key(client: TestClient) -> None:
    """AC-002-09: the API orders; the frontend must never re-sort."""
    body = _upload(client, "zebra \u00e1baco abandonar".encode()).json()

    assert [row["normalized_form"] for row in body["forms"]] == [
        "\u00e1baco",
        "abandonar",
        "zebra",
    ]


@pytest.mark.unit
def test_the_token_count_equals_the_sum_of_the_returned_frequencies(
    client: TestClient,
) -> None:
    """AC-002-08: both numbers describe the same occurrences."""
    body = _upload(client, b"uno dos dos tres tres tres").json()

    assert body["total_token_count"] == sum(row["frequency"] for row in body["forms"])


@pytest.mark.unit
def test_a_json_filesystem_path_is_refused_and_nothing_is_computed(
    client: TestClient,
) -> None:
    """AC-002-01 rejection leg: upload-only intake, in the shared envelope."""
    response = client.post(_ENDPOINT, json={"path": "/tmp/book.txt"})  # noqa: S108

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "INVALID_REQUEST",
            "message": "La petición no incluye un archivo .txt válido.",
        }
    }


@pytest.mark.unit
def test_a_wrong_extension_is_refused_naming_the_accepted_one(client: TestClient) -> None:
    """AC-002-02: `notes.pdf` is a 422 whose message tells the user what is accepted."""
    response = _upload(client, b"hola", filename="notes.pdf", content_type="application/pdf")
    body = response.json()

    assert response.status_code == 422
    assert body["error"]["code"] == "INVALID_FILE_TYPE"
    assert ".txt" in body["error"]["message"]
    assert "forms" not in body


@pytest.mark.unit
def test_an_uppercase_extension_is_accepted(client: TestClient) -> None:
    """AC-002-02: `SAMPLE.TXT` imports."""
    response = _upload(client, b"hola", filename="SAMPLE.TXT")

    assert response.status_code == 201
    assert response.json()["distinct_form_count"] == 1


@pytest.mark.unit
def test_non_utf8_bytes_are_refused_with_conversion_guidance(client: TestClient) -> None:
    """AC-002-05: the message names UTF-8 and tells the user how to convert."""
    response = _upload(client, b"hola\xffmundo")
    body = response.json()

    assert response.status_code == 422
    assert body["error"]["code"] == "INVALID_ENCODING"
    assert "UTF-8" in body["error"]["message"]


@pytest.mark.unit
def test_the_rejection_body_never_carries_a_byte_offset(client: TestClient) -> None:
    """Art. X.2: `UnicodeDecodeError` knows the offset into the user's text; we do not."""
    response = _upload(client, b"zzqxsentinel\xff")
    rendered = response.text

    assert "zzqxsentinel" not in rendered
    assert "12" not in rendered
    assert "0xff" not in rendered.casefold()


@pytest.mark.unit
def test_a_bom_prefixed_upload_is_accepted_without_the_bom_entering_a_form(
    client: TestClient,
) -> None:
    """AC-002-05: the BOM is stripped, not rejected and not imported."""
    body = _upload(client, b"\xef\xbb\xbfhola mundo").json()

    assert [row["normalized_form"] for row in body["forms"]] == ["hola", "mundo"]


@pytest.mark.unit
@pytest.mark.parametrize("payload", [b"", b" \n\t"])
def test_a_content_free_upload_is_a_success_with_a_zero_state(payload: bytes) -> None:
    """AC-002-17: 201 with an empty list and a count of 0, never an error."""
    response = _upload(_client_with_limit(64), payload)
    body = response.json()

    assert response.status_code == 201
    assert body["import_status"] == "succeeded"
    assert body["forms"] == []
    assert body["distinct_form_count"] == 0


@pytest.mark.unit
def test_an_oversized_upload_is_refused_with_the_limit_surfaced() -> None:
    """AC-002-04: 413 and the message names the configured limit."""
    response = _upload(_client_with_limit(64), b"a" * 65)
    body = response.json()

    assert response.status_code == 413
    assert body["error"]["code"] == "FILE_TOO_LARGE"
    assert "64" in body["error"]["message"]


@pytest.mark.unit
def test_an_upload_exactly_at_the_limit_is_accepted() -> None:
    """AC-002-04: the comparison is `>`, so 64 bytes against a 64-byte limit imports."""
    response = _upload(_client_with_limit(64), b"a" * 64)

    assert response.status_code == 201
    assert response.json()["forms"][0]["display_form"] == "a" * 64


@pytest.mark.unit
def test_every_error_shares_one_envelope_shape(client: TestClient) -> None:
    """Spec §4: one shape for every failure, so no client needs two parsers."""
    responses = [
        _upload(client, b"hola", filename="notes.pdf", content_type="application/pdf"),
        _upload(client, b"\xff"),
        client.post(_ENDPOINT, json={"path": "/tmp/book.txt"}),  # noqa: S108
    ]

    for response in responses:
        jsonschema.validate(response.json(), _SCHEMA["$defs"]["error"])

"""Log-egress tests for the import path — design §15, §9.4 (T1B18).

Two legs, and they are not equally strong.

The **failure leg** is a genuine assertion: a decode failure must produce a
record naming the error code and the import id, and nothing else. Before the
handler logs, that assertion finds zero matching records and fails.

The **success leg** is an absence assertion. It passes on the first run over code
that logs nothing at all, which proves nothing whatsoever. It is only trusted
after being seen failing: temporarily log the decoded text, confirm the sentinel
assertion fires, revert. That mutation check is recorded in the change report.

The sentinel is `zzqxsentinel` — a token that cannot occur by accident, so any
match is a real leak rather than a coincidence.

REQ-002-013 / AC-002-18, Art. X.2.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterable

    from fastapi.testclient import TestClient

_ENDPOINT = "/api/v1/imports"
_SENTINEL = "zzqxsentinel"
_OFFSET_OF_THE_BAD_BYTE = str(len(_SENTINEL))


@pytest.fixture
def client(imports_client: TestClient) -> TestClient:
    """Persistence landed in cut 2 (REQ-002-008); see `tests/conftest.py`."""
    return imports_client


def _upload(client: TestClient, body: bytes) -> Any:
    return client.post(_ENDPOINT, files={"file": ("sample.txt", body, "text/plain")})


def _rendered(records: Iterable[logging.LogRecord]) -> str:
    """Everything a handler could conceivably emit from each record."""
    return "\n".join(
        f"{record.name} {record.levelname} {record.msg!r} {record.args!r} "
        f"{record.getMessage()} {record.exc_text or ''}"
        for record in records
    )


@pytest.mark.unit
def test_a_successful_import_logs_no_imported_text(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    """AC-002-18: the sentinel is processed into a row and still never logged."""
    caplog.set_level(logging.DEBUG)

    response = _upload(client, f"{_SENTINEL} {_SENTINEL} hola".encode())

    # Non-vacuity: the sentinel really did travel through tokenize/normalize/
    # build_table. Without this the assertion below could pass on a rejected
    # upload that never touched the text at all.
    assert response.status_code == 201
    assert response.json()["forms"][0] == {
        "normalized_form": "hola",
        "display_form": "hola",
        "frequency": 1,
    }
    assert response.json()["forms"][1]["frequency"] == 2

    assert _SENTINEL not in _rendered(caplog.records)


@pytest.mark.unit
def test_a_decode_failure_logs_the_error_code_and_the_import_id(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    """AC-002-18: a failure is identified by code and id, so it stays diagnosable."""
    caplog.set_level(logging.DEBUG)

    response = _upload(client, _SENTINEL.encode() + b"\xff")

    assert response.status_code == 422
    messages = [record.getMessage() for record in caplog.records]
    assert any("code=INVALID_ENCODING" in message for message in messages)
    assert any("import_id=-" in message for message in messages)


@pytest.mark.unit
def test_a_decode_failure_logs_neither_the_text_nor_the_byte_offset(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    """`UnicodeDecodeError` carries an index into the user's content. It must not ship."""
    caplog.set_level(logging.DEBUG)

    _upload(client, _SENTINEL.encode() + b"\xff")
    rendered = _rendered(caplog.records)

    assert _SENTINEL not in rendered
    assert "0xff" not in rendered.casefold()
    assert all(
        _OFFSET_OF_THE_BAD_BYTE not in message
        for message in [record.getMessage() for record in caplog.records]
    )


@pytest.mark.unit
def test_no_decode_failure_is_logged_with_a_traceback(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    """`logger.exception()` would render `UnicodeDecodeError.__str__`, offset included."""
    caplog.set_level(logging.DEBUG)

    _upload(client, _SENTINEL.encode() + b"\xff")

    assert caplog.records
    assert all(record.exc_info is None for record in caplog.records)


@pytest.mark.unit
def test_a_type_rejection_is_traceable_by_its_code_and_carries_no_filename(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    """Triangulation: a second failure code, and the filename is content too."""
    caplog.set_level(logging.DEBUG)

    client.post(_ENDPOINT, files={"file": (f"{_SENTINEL}.pdf", b"hola", "application/pdf")})
    rendered = _rendered(caplog.records)

    assert "code=INVALID_FILE_TYPE" in rendered
    assert _SENTINEL not in rendered

"""Unit tests for the import error taxonomy — design §9.1 (T1B03).

The taxonomy exists to keep the user's text out of the failure path. Every
assertion here is about what an exception is allowed to *carry*, because an
exception that holds a slice of the imported text, a byte offset into it, or a
filesystem path leaks that content into logs, tracebacks and error bodies
(Art. X.2, REQ-002-013).

REQ-002-002, REQ-002-003, REQ-002-004, REQ-002-011, spec §4, design §9.1-9.2.
"""

from __future__ import annotations

import pytest

from wheel_vocabulary.application.imports.errors import (
    FileTooLargeError,
    ImportNotFoundError,
    InvalidEncodingError,
    InvalidFileTypeError,
    TextImportError,
)

# Every attribute an import exception is permitted to hold. The point of the
# allowlist is that it is a *closed* set: a field added later without a
# deliberate decision fails the test rather than silently shipping.
_SAFE_ATTRIBUTES = frozenset({"limit"})

_SENTINEL = "zzqxsentinel"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("factory", "expected_code", "expected_status"),
    [
        (InvalidFileTypeError, "INVALID_FILE_TYPE", 422),
        (lambda: FileTooLargeError(limit=64), "FILE_TOO_LARGE", 413),
        (InvalidEncodingError, "INVALID_ENCODING", 422),
        (ImportNotFoundError, "IMPORT_NOT_FOUND", 404),
    ],
)
def test_each_error_carries_its_wire_code_and_status(
    factory: object, expected_code: str, expected_status: int
) -> None:
    """Spec §4: each failure maps to one distinct code and one HTTP status."""
    error = factory()  # type: ignore[operator]

    assert isinstance(error, TextImportError)
    assert error.code == expected_code
    assert error.http_status == expected_status


@pytest.mark.unit
def test_base_error_declares_the_code_contract_without_a_value() -> None:
    """The base is never raised directly, so it must not answer to a code."""
    assert issubclass(TextImportError, Exception)
    assert "code" in TextImportError.__annotations__
    assert not hasattr(TextImportError, "code")


@pytest.mark.unit
def test_file_too_large_reports_the_configured_limit() -> None:
    """AC-002-04: the message must name the limit so the user can act on it."""
    error = FileTooLargeError(limit=64)

    assert error.limit == 64
    assert "64" in error.message


@pytest.mark.unit
def test_invalid_file_type_names_the_accepted_extension() -> None:
    """AC-002-02: the message must name `.txt`."""
    assert ".txt" in InvalidFileTypeError().message


@pytest.mark.unit
def test_invalid_encoding_names_utf8_and_how_to_convert() -> None:
    """AC-002-05: naming the encoding is not enough; the user needs a next step."""
    message = InvalidEncodingError().message

    assert "UTF-8" in message
    assert "Convi" in message  # "Conviértelo…" — actionable conversion guidance


@pytest.mark.unit
@pytest.mark.parametrize(
    "factory",
    [
        InvalidFileTypeError,
        lambda: FileTooLargeError(limit=64),
        InvalidEncodingError,
        ImportNotFoundError,
    ],
)
def test_no_error_carries_text_offset_or_path(factory: object) -> None:
    """Art. X.2: the only instance state permitted is the safe allowlist."""
    error = factory()  # type: ignore[operator]

    assert set(vars(error)) <= _SAFE_ATTRIBUTES


@pytest.mark.unit
def test_invalid_encoding_accepts_nothing_that_could_carry_user_text() -> None:
    """A constructor that takes no payload cannot be handed the user's bytes."""
    with pytest.raises(UnicodeDecodeError) as decode_failure:
        (_SENTINEL.encode() + b"\xff").decode("utf-8")

    original = decode_failure.value
    assert str(original.object, "utf-8", "replace").startswith(_SENTINEL)

    with pytest.raises(TypeError):
        InvalidEncodingError(original)  # type: ignore[call-arg]


@pytest.mark.unit
def test_error_string_never_renders_the_offending_bytes() -> None:
    """`str(exc)` reaches logs and tracebacks, so it must stay content-free."""
    rendered = [str(error) for error in (InvalidEncodingError(), FileTooLargeError(limit=64))]

    assert all(_SENTINEL not in text for text in rendered)
    assert rendered[0] == InvalidEncodingError().message

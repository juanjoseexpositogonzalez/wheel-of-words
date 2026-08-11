"""Unit tests for the ImportText ordered gate — design §8, §15 (T1B10-T1B12).

The gate is ordered for a reason and the order is what these tests protect:

- Gate 1 classifies the upload before a single byte is read, so an unsupported
  file never reaches the decoder or the tokenizer (design §15, row 1).
- Gate 3 bounds the read, so a body larger than the limit is refused *while*
  arriving rather than after it has been accumulated in full. Checking
  ``len(body) > limit`` after an unbounded read defeats the purpose of having a
  limit at all (design §15, unbounded intake).
- An empty or whitespace-only upload is a success with zero forms, not an error
  (REQ-002-012).

REQ-002-001, REQ-002-002, REQ-002-003, REQ-002-004, REQ-002-012.
"""

from __future__ import annotations

import builtins
import io

import pytest

from wheel_vocabulary.application.imports.errors import (
    FileTooLargeError,
    InvalidEncodingError,
    InvalidFileTypeError,
)
from wheel_vocabulary.application.imports.use_cases import ImportText
from wheel_vocabulary.infrastructure.text_extraction import PlainTextExtractor

_CHUNK_BOUND = 65_536


class _CountingStream:
    """A ByteStream that records exactly how many bytes the gate pulled from it."""

    def __init__(self, data: bytes) -> None:
        self._buffer = io.BytesIO(data)
        self.bytes_read = 0

    def read(self, size: int, /) -> bytes:
        chunk = self._buffer.read(size)
        self.bytes_read += len(chunk)
        return chunk


class _ExplodingStream:
    """Reading from this is a test failure — gate 1 must reject before gate 3."""

    def __init__(self) -> None:
        self.bytes_read = 0

    def read(self, size: int, /) -> bytes:
        del size
        message = "gate 1 must reject before any byte is read"
        raise AssertionError(message)


class _FakeRepository:
    """An in-memory `BookRepository` double — no real database (AGENTS.md §6).

    These are unit tests for the ordered gate; cut-2 persistence is covered by
    the real `SqlAlchemyBookRepository` in `tests/integration/`. This double
    only has to hand back an incrementing id.
    """

    def __init__(self) -> None:
        self._next_id = 1

    def create(self, **kwargs: object) -> int:
        del kwargs
        book_id = self._next_id
        self._next_id += 1
        return book_id

    def frequency_pairs(self, book_id: int) -> list[tuple[str, str, int]] | None:
        del book_id
        return []

    def exists(self, book_id: int) -> bool:
        del book_id
        return True

    def delete(self, book_id: int) -> bool:
        del book_id
        return True


class _FakeClock:
    """A fixed-time `Clock` double — no wall-clock coupling in a unit test."""

    def now_utc(self):  # noqa: ANN201 - returns datetime; inferred to keep the helper terse
        from datetime import UTC, datetime

        return datetime(2026, 8, 11, tzinfo=UTC)


def _use_case(*, max_size_bytes: int = 4_194_304) -> ImportText:
    return ImportText(
        extractor=PlainTextExtractor(),
        max_size_bytes=max_size_bytes,
        repository=_FakeRepository(),
        clock=_FakeClock(),
    )


def _import(
    use_case: ImportText,
    *,
    filename: str | None = "sample.txt",
    content_type: str | None = "text/plain",
    stream: object | None = None,
    declared_size: int | None = None,
):  # noqa: ANN202 - returns ImportResult; inferred to keep the helper terse
    return use_case.execute(
        filename=filename,
        content_type=content_type,
        stream=stream if stream is not None else _CountingStream(b""),
        declared_size=declared_size,
    )


# --------------------------------------------------------------------------
# T1B10 — threat matrix row 1: filename and content-type classification
# --------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize(
    "filename",
    ["notes.pdf", "report.txt.exe", "archive.tar.gz", "notes", "", None, ".txt"],
)
def test_unsupported_filename_is_rejected_before_any_byte_is_read(
    filename: str | None,
) -> None:
    """AC-002-02: gate 1 runs first, so the stream must stay untouched."""
    stream = _ExplodingStream()

    with pytest.raises(InvalidFileTypeError):
        _import(_use_case(), filename=filename, stream=stream)

    assert stream.bytes_read == 0


@pytest.mark.unit
@pytest.mark.parametrize("content_type", ["text/html", "application/pdf", "", None])
def test_unsupported_content_type_is_rejected_before_any_byte_is_read(
    content_type: str | None,
) -> None:
    """A `.txt` suffix is not enough — the declared type is checked too."""
    stream = _ExplodingStream()

    with pytest.raises(InvalidFileTypeError):
        _import(_use_case(), content_type=content_type, stream=stream)

    assert stream.bytes_read == 0


@pytest.mark.unit
@pytest.mark.parametrize("filename", ["SAMPLE.TXT", "Sample.Txt", "sample.txt"])
def test_extension_matching_is_case_insensitive(filename: str) -> None:
    """AC-002-02: `SAMPLE.TXT` is accepted."""
    result = _import(_use_case(), filename=filename, stream=_CountingStream(b"hola"))

    assert result.distinct_form_count == 1


@pytest.mark.unit
@pytest.mark.parametrize(
    "content_type",
    ["text/plain", "text/plain; charset=utf-8", "application/octet-stream", "TEXT/PLAIN"],
)
def test_accepted_content_types_including_parameters(content_type: str) -> None:
    """Browsers append `; charset=…`; the parameter is not part of the media type."""
    result = _import(_use_case(), content_type=content_type, stream=_CountingStream(b"hola"))

    assert result.total_token_count == 1


@pytest.mark.unit
def test_traversal_shaped_filename_is_judged_on_its_suffix_alone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Design §15: the filename is classified, never resolved into a path."""

    def _forbidden(*args: object, **kwargs: object) -> object:
        del args, kwargs
        message = "the import path must never open a file derived from the filename"
        raise AssertionError(message)

    monkeypatch.setattr(builtins, "open", _forbidden)

    result = _import(
        _use_case(),
        filename="../../etc/passwd.txt",
        stream=_CountingStream(b"zebra zebra"),
    )

    assert result.distinct_form_count == 1
    assert result.forms[0].normalized_form == "zebra"
    assert result.forms[0].frequency == 2


# --------------------------------------------------------------------------
# T1B11 — adjacent boundary: unbounded resource intake
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_body_one_byte_over_the_limit_is_rejected() -> None:
    """AC-002-04: the comparison is `>`, so 65 bytes against 64 is a rejection."""
    with pytest.raises(FileTooLargeError) as failure:
        _import(_use_case(max_size_bytes=64), stream=_CountingStream(b"a" * 65))

    assert failure.value.limit == 64
    assert "64" in failure.value.message


@pytest.mark.unit
def test_body_exactly_at_the_limit_is_accepted() -> None:
    """AC-002-04: `>` and not `>=` — a file exactly at the limit imports."""
    result = _import(_use_case(max_size_bytes=64), stream=_CountingStream(b"a" * 64))

    assert result.total_token_count == 1
    assert result.forms[0].display_form == "a" * 64


@pytest.mark.unit
def test_an_oversized_body_is_abandoned_mid_stream_not_after_the_fact() -> None:
    """The gate must abort while the body arrives; reading it all first is the defect."""
    body = b"a" * (1024 * 1024)
    stream = _CountingStream(body)

    with pytest.raises(FileTooLargeError):
        _import(_use_case(max_size_bytes=64), stream=stream)

    assert stream.bytes_read <= _CHUNK_BOUND
    assert stream.bytes_read < len(body)


@pytest.mark.unit
def test_an_absent_declared_size_is_still_rejected_at_the_streaming_gate() -> None:
    """`Content-Length` is client-supplied and may be absent; gate 3 is the enforcement."""
    with pytest.raises(FileTooLargeError):
        _import(_use_case(max_size_bytes=64), stream=_CountingStream(b"a" * 65), declared_size=None)


@pytest.mark.unit
def test_a_declared_oversize_is_rejected_without_reading_the_body() -> None:
    """Gate 2 is the fast path: when the size is already known, read nothing."""
    stream = _ExplodingStream()

    with pytest.raises(FileTooLargeError):
        _import(_use_case(max_size_bytes=64), stream=stream, declared_size=65)

    assert stream.bytes_read == 0


@pytest.mark.unit
def test_a_lying_declared_size_does_not_bypass_the_streaming_gate() -> None:
    """Gate 2 is an optimisation only — an understated size must not let a body through."""
    with pytest.raises(FileTooLargeError):
        _import(_use_case(max_size_bytes=64), stream=_CountingStream(b"a" * 500), declared_size=1)


# --------------------------------------------------------------------------
# T1B12 — REQ-002-012: empty and whitespace-only uploads succeed
# --------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize("body", [b"", b" \n\t", b"   ", "\u00a0\u2028".encode(), b"\r\n\r\n"])
def test_a_content_free_upload_succeeds_with_zero_forms(body: bytes) -> None:
    """AC-002-17: this is a success with an empty table, never an error."""
    result = _import(_use_case(), stream=_CountingStream(body))

    assert result.forms == ()
    assert result.distinct_form_count == 0
    assert result.total_token_count == 0


@pytest.mark.unit
def test_a_digits_only_upload_succeeds_with_zero_forms() -> None:
    """T6: a token with no letter is discarded, so `2026 1914` yields nothing."""
    result = _import(_use_case(), stream=_CountingStream(b"2026 1914-1918"))

    assert result.distinct_form_count == 0


# --------------------------------------------------------------------------
# Gate 4 and gate 5 — decoding and aggregation reach the shipped domain
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_invalid_bytes_are_rejected_after_the_size_gate() -> None:
    """AC-002-05: an in-limit body that is not UTF-8 fails at gate 4."""
    with pytest.raises(InvalidEncodingError):
        _import(_use_case(), stream=_CountingStream(b"hola\xffmundo"))


@pytest.mark.unit
def test_aggregation_uses_the_shipped_domain_rules() -> None:
    """AC-002-23: `Straße straße STRASSE Straße` is one row keyed `strasse`."""
    body = "Stra\u00dfe stra\u00dfe STRASSE Stra\u00dfe".encode()

    result = _import(_use_case(), stream=_CountingStream(body))

    assert result.distinct_form_count == 1
    assert result.total_token_count == 4
    assert result.forms[0].normalized_form == "strasse"
    assert result.forms[0].display_form == "Stra\u00dfe"
    assert result.forms[0].frequency == 4


@pytest.mark.unit
def test_rows_arrive_ordered_by_the_grouping_key() -> None:
    """AC-002-09: ordering is diacritic-insensitive and computed server-side."""
    result = _import(_use_case(), stream=_CountingStream("zebra \u00e1baco abandonar".encode()))

    assert [row.normalized_form for row in result.forms] == ["\u00e1baco", "abandonar", "zebra"]


@pytest.mark.unit
def test_reported_token_count_equals_the_sum_of_frequencies() -> None:
    """AC-002-08: the two numbers describe the same occurrences and must agree."""
    result = _import(_use_case(), stream=_CountingStream(b"uno dos dos tres tres tres"))

    assert result.total_token_count == sum(row.frequency for row in result.forms)
    assert result.distinct_form_count == 3


@pytest.mark.unit
def test_a_leading_bom_does_not_enter_the_first_form() -> None:
    """AC-002-05: the BOM is stripped before tokenization, not after."""
    result = _import(_use_case(), stream=_CountingStream(b"\xef\xbb\xbfhola"))

    assert result.forms[0].normalized_form == "hola"

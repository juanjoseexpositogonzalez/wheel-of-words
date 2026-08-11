"""Unit tests for the import ports — design §7.2 (T1B08).

The ports are structural on purpose. ``starlette``'s ``UploadFile.file`` and a
``SpooledTemporaryFile`` satisfy ``ByteStream`` as they are, with no adapter class
and no inheritance, which is what keeps ``application`` free of any import from
``infrastructure`` or ``api`` (Art. VII.2-3, ADR-0002).

Structural satisfaction is only worth asserting if non-satisfaction is asserted
too: ``isinstance`` against a ``runtime_checkable`` Protocol checks method
presence, so a test that only ever shows conforming stubs cannot distinguish a
real Protocol from an empty one.

REQ-002-001, REQ-002-004, REQ-002-008 (port declaration).
"""

from __future__ import annotations

import io
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from wheel_vocabulary.application.imports.ports import (
    BookRepository,
    ByteStream,
    TextExtractor,
)
from wheel_vocabulary.infrastructure.text_extraction import PlainTextExtractor

if TYPE_CHECKING:
    from collections.abc import Sequence


class _PlainStream:
    """No base class, no registration — presence of ``read`` is the whole contract."""

    def read(self, size: int, /) -> bytes:
        return b"x" * size


class _PlainExtractor:
    def extract(self, data: bytes) -> str:
        return data.decode("utf-8")


class _PlainRepository:
    def create(
        self,
        *,
        content_hash: str,
        token_count: int,
        created_at: datetime,
        occurrences: Sequence[tuple[str, str, int]],
    ) -> int:
        del content_hash, token_count, created_at, occurrences
        return 1

    def frequency_pairs(self, book_id: int) -> list[tuple[str, str, int]] | None:
        return [] if book_id == 1 else None


class _NotAStream:
    """Satisfies nothing — the negative control for every assertion below."""

    def readlines(self) -> list[bytes]:
        return []


@pytest.mark.unit
@pytest.mark.parametrize(
    ("protocol", "stub"),
    [
        (ByteStream, _PlainStream()),
        (TextExtractor, _PlainExtractor()),
        (BookRepository, _PlainRepository()),
    ],
)
def test_a_plain_stub_satisfies_the_port_without_inheriting(protocol: type, stub: object) -> None:
    """Structural typing: no subclassing, no registration, no adapter class."""
    assert isinstance(stub, protocol)
    assert type(stub).__mro__ == (type(stub), object)


@pytest.mark.unit
@pytest.mark.parametrize("protocol", [ByteStream, TextExtractor, BookRepository])
def test_an_object_missing_the_methods_does_not_satisfy_the_port(protocol: type) -> None:
    """The negative control — without it the checks above could be vacuous."""
    assert not isinstance(_NotAStream(), protocol)


@pytest.mark.unit
def test_a_binary_file_object_satisfies_bytestream_as_is() -> None:
    """The production stream is a spooled file; no wrapper may be required."""
    stream = io.BytesIO(b"hola mundo")

    assert isinstance(stream, ByteStream)
    assert stream.read(4) == b"hola"


@pytest.mark.unit
def test_the_shipped_extractor_satisfies_textextractor_without_inheriting() -> None:
    """The real adapter conforms structurally, so no ABC registration is needed."""
    assert isinstance(PlainTextExtractor(), TextExtractor)
    assert TextExtractor not in PlainTextExtractor.__mro__


@pytest.mark.unit
def test_repository_distinguishes_unknown_import_from_empty_import() -> None:
    """Design §7.2: `None` means unknown id (404); `[]` means an empty import (201)."""
    repository = _PlainRepository()

    assert repository.frequency_pairs(1) == []
    assert repository.frequency_pairs(999) is None


@pytest.mark.unit
def test_repository_create_returns_an_identifier() -> None:
    """The port is declared now; cut 2 supplies the SQLAlchemy implementation."""
    book_id = _PlainRepository().create(
        content_hash="0" * 64,
        token_count=0,
        created_at=datetime(2026, 8, 11, tzinfo=UTC),
        occurrences=[],
    )

    assert book_id == 1

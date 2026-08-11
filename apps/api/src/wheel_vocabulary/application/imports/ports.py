"""Ports the import use cases depend on — design §7.2.

All three are structural ``Protocol`` types, not abstract base classes. Starlette's
``UploadFile.file`` satisfies ``ByteStream`` exactly as it is, so no adapter class
has to exist purely to declare a conformance the object already has (Art. VII.6),
and ``application`` never imports ``infrastructure`` or ``api`` to obtain one.

They are ``runtime_checkable`` so the structural contract itself is assertable.

REQ-002-001, REQ-002-004, REQ-002-008.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Sequence
    from datetime import datetime

__all__ = ["BookRepository", "ByteStream", "TextExtractor"]


@runtime_checkable
class ByteStream(Protocol):
    """Structural view of an inbound upload body.

    Synchronous on purpose: the route is a plain ``def`` that FastAPI runs in the
    threadpool, which is what keeps ``application`` async-free (design §8).
    """

    def read(self, size: int, /) -> bytes:
        """Return at most ``size`` bytes; an empty result means end of stream."""
        ...


@runtime_checkable
class TextExtractor(Protocol):
    """Decodes uploaded bytes into text."""

    def extract(self, data: bytes) -> str:
        """Return the decoded text, raising ``InvalidEncodingError`` on bad bytes."""
        ...


@runtime_checkable
class BookRepository(Protocol):
    """Persistence port for imported corpora. Implemented in cut 2."""

    def create(
        self,
        *,
        content_hash: str,
        token_count: int,
        created_at: datetime,
        occurrences: Sequence[tuple[str, str, int]],
    ) -> int:
        """Persist a corpus and its occurrences; return the new import id."""
        ...

    def frequency_pairs(self, book_id: int) -> list[tuple[str, str, int]] | None:
        """Return ``(raw_text, normalized_text, count)`` triples for an import.

        ``None`` means the id is unknown, which is a 404. An empty list means the
        import exists and contains no forms, which is a success (REQ-002-012).
        The two MUST NOT be conflated.
        """
        ...

    def exists(self, book_id: int) -> bool:
        """Return whether an import with this id is present."""
        ...

    def delete(self, book_id: int) -> bool:
        """Delete an import and every occurrence derived from it."""
        ...

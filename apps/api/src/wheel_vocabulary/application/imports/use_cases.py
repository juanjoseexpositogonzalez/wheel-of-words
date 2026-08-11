"""Import use cases — the ordered validation gate of design §8.

The order is the security property, not a stylistic preference. Classifying the
upload first means an unsupported file never reaches the decoder or the
tokenizer; bounding the read next means a body larger than the limit is refused
*while* it arrives. An unbounded ``read()`` followed by ``len(body) > limit``
would give the same status code while doing exactly the thing the limit exists to
prevent (design §8, §15).

The policy lives here rather than in the route because it is application
behaviour: ``api`` owns the plumbing, ``application`` owns the decision. The
method is synchronous so the route can be a plain ``def`` that FastAPI runs in
the threadpool, which keeps this layer async-free.

No ``BookRepository.create()`` call is made: this cut computes and returns the
frequency table, and persistence lands in cut 2.

REQ-002-001, REQ-002-002, REQ-002-003, REQ-002-004, REQ-002-006 (response half),
REQ-002-012, REQ-002-018 (response half).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from wheel_vocabulary.application.imports.errors import (
    FileTooLargeError,
    InvalidFileTypeError,
)
from wheel_vocabulary.domain.frequency import build_table
from wheel_vocabulary.domain.text.normalizer import normalize
from wheel_vocabulary.domain.text.tokenizer import tokenize

if TYPE_CHECKING:  # pragma: no cover - typing only
    from wheel_vocabulary.application.imports.ports import ByteStream, TextExtractor
    from wheel_vocabulary.domain.models import FormFrequency

__all__ = ["ImportResult", "ImportText"]

_ACCEPTED_SUFFIX = ".txt"
_ACCEPTED_MEDIA_TYPES = frozenset({"text/plain", "application/octet-stream"})
_CHUNK_SIZE = 65_536


@dataclass(frozen=True, slots=True)
class ImportResult:
    """The outcome of a successful import.

    ``total_token_count`` counts the occurrences that entered the table, so it
    equals the sum of every row's ``frequency`` by construction (AC-002-08).
    """

    forms: tuple[FormFrequency, ...]
    distinct_form_count: int
    total_token_count: int


class ImportText:
    """Import an uploaded text and return its ordered frequency table."""

    def __init__(self, *, extractor: TextExtractor, max_size_bytes: int) -> None:
        self._extractor = extractor
        self._max_size_bytes = max_size_bytes

    def execute(
        self,
        *,
        filename: str | None,
        content_type: str | None,
        stream: ByteStream,
        declared_size: int | None = None,
    ) -> ImportResult:
        """Run the five gates in order, rejecting at the first one that fails."""
        self._gate_1_classify(filename, content_type)
        self._gate_2_reject_declared_oversize(declared_size)
        data = self._gate_3_read_within_limit(stream)
        text = self._gate_4_decode(data)
        return self._gate_5_aggregate(text)

    def _gate_1_classify(self, filename: str | None, content_type: str | None) -> None:
        """Reject an unsupported upload before a single byte is read.

        The filename is *classified*, never resolved: no path is constructed from
        it, nothing is joined to it, and it is never opened or written. A
        traversal-shaped name is therefore judged on its suffix like any other
        (design §15, row 1).
        """
        if _suffix_of(filename) != _ACCEPTED_SUFFIX:
            raise InvalidFileTypeError
        if _media_type_of(content_type) not in _ACCEPTED_MEDIA_TYPES:
            raise InvalidFileTypeError

    def _gate_2_reject_declared_oversize(self, declared_size: int | None) -> None:
        """Fast path only: reject a size the client already declared.

        Never the enforcement. The declared size is client-supplied and may be
        absent or understated, so gate 3 has to hold on its own.
        """
        if declared_size is not None and declared_size > self._max_size_bytes:
            raise FileTooLargeError(limit=self._max_size_bytes)

    def _gate_3_read_within_limit(self, stream: ByteStream) -> bytes:
        """Accumulate the body, abandoning the read one byte past the limit.

        Reading one byte beyond is what distinguishes "at the limit" from "over
        it" without ever holding more: the comparison is ``>`` and not ``>=``, so
        a file of exactly ``max_import_size_bytes`` imports (AC-002-04).
        """
        ceiling = self._max_size_bytes + 1
        buffer = bytearray()
        while len(buffer) < ceiling:
            chunk = stream.read(min(_CHUNK_SIZE, ceiling - len(buffer)))
            if not chunk:
                break
            buffer.extend(chunk)
        if len(buffer) > self._max_size_bytes:
            raise FileTooLargeError(limit=self._max_size_bytes)
        return bytes(buffer)

    def _gate_4_decode(self, data: bytes) -> str:
        """Decode strictly as UTF-8. Raises ``InvalidEncodingError`` on bad bytes."""
        return self._extractor.extract(data)

    def _gate_5_aggregate(self, text: str) -> ImportResult:
        """Tokenize, normalize and aggregate through the shipped domain rules.

        A token whose normalized form is empty is dropped rather than counted, so
        no row can carry an empty grouping key.
        """
        pairs = [
            (token.raw_text, normalized, 1)
            for token in tokenize(text)
            if (normalized := normalize(token.raw_text))
        ]
        forms = build_table(pairs)
        return ImportResult(
            forms=forms,
            distinct_form_count=len(forms),
            total_token_count=len(pairs),
        )


def _suffix_of(filename: str | None) -> str:
    """Return the casefolded final suffix, or ``""`` when there is none.

    Pure string handling — deliberately not ``pathlib``, so no path object is
    ever built from user-supplied input.
    """
    if not filename:
        return ""
    stem, dot, extension = filename.rpartition(".")
    return f".{extension}".casefold() if dot and stem else ""


def _media_type_of(content_type: str | None) -> str:
    """Return the casefolded media type without its parameters.

    Browsers append ``; charset=…``; the parameter is not part of the type.
    """
    if not content_type:
        return ""
    return content_type.split(";", 1)[0].strip().casefold()

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

Cut 2 adds the persistence branch: gate 6 calls ``BookRepository.create()`` and
the response now carries a real ``id`` for the first time (T1B13's additive
completion). ``ReadImport`` is the GET-side counterpart — it calls the SAME
``domain.frequency.build_table()`` this file already used, so the display-form
and ordering rules stay a single implementation for both write and read paths
(design §1, REQ-002-006 full closure).

REQ-002-001, REQ-002-002, REQ-002-003, REQ-002-004, REQ-002-006, REQ-002-008,
REQ-002-009, REQ-002-012, REQ-002-013, REQ-002-018.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

from wheel_vocabulary.application.imports.errors import (
    FileTooLargeError,
    ImportNotFoundError,
    InvalidFileTypeError,
    PersistenceFailedError,
)
from wheel_vocabulary.domain.frequency import build_table
from wheel_vocabulary.domain.text.normalizer import normalize
from wheel_vocabulary.domain.text.tokenizer import tokenize

if TYPE_CHECKING:  # pragma: no cover - typing only
    from wheel_vocabulary.application.clock import Clock
    from wheel_vocabulary.application.imports.ports import (
        BookRepository,
        ByteStream,
        TextExtractor,
    )
    from wheel_vocabulary.domain.models import FormFrequency

__all__ = ["DeleteImport", "ImportResult", "ImportText", "ReadImport", "read_bounded_and_hash"]

_ACCEPTED_SUFFIX = ".txt"
_ACCEPTED_MEDIA_TYPES = frozenset({"text/plain", "application/octet-stream"})
_CHUNK_SIZE = 65_536


@dataclass(frozen=True, slots=True)
class ImportResult:
    """The outcome of a successful import, read fresh or from persistence.

    ``total_token_count`` counts the occurrences that entered the table, so it
    equals the sum of every row's ``frequency`` by construction (AC-002-08).
    ``id`` is the persisted import's identity (cut 2) — always populated, since
    every ``ImportResult`` now comes either from a successful `ImportText`
    write or a successful `ReadImport` read, and both require a `Book` row to
    exist.
    """

    id: int
    forms: tuple[FormFrequency, ...]
    distinct_form_count: int
    total_token_count: int


def read_bounded_and_hash(stream: ByteStream, ceiling: int) -> tuple[bytes, str]:
    """Read at most ``ceiling`` bytes from ``stream``, hashing every byte pulled.

    One pass serves both jobs: the loop that bounds the read is the loop that
    feeds ``hashlib.sha256`` incrementally, so the returned bytes and digest can
    never diverge (design §8, §3.3). Shared by ``ImportText`` gate 3 and the
    T-BENCH synthetic-corpus generator (T216), so both hash identically.
    """
    buffer = bytearray()
    digest = hashlib.sha256()
    while len(buffer) < ceiling:
        chunk = stream.read(min(_CHUNK_SIZE, ceiling - len(buffer)))
        if not chunk:
            break
        buffer.extend(chunk)
        digest.update(chunk)
    return bytes(buffer), digest.hexdigest()


class ImportText:
    """Import an uploaded text, persist it, and return its ordered frequency table."""

    def __init__(
        self,
        *,
        extractor: TextExtractor,
        max_size_bytes: int,
        repository: BookRepository,
        clock: Clock,
    ) -> None:
        self._extractor = extractor
        self._max_size_bytes = max_size_bytes
        self._repository = repository
        self._clock = clock

    def execute(
        self,
        *,
        filename: str | None,
        content_type: str | None,
        stream: ByteStream,
        declared_size: int | None = None,
    ) -> ImportResult:
        """Run the ordered gate, rejecting at the first one that fails."""
        self._gate_1_classify(filename, content_type)
        self._gate_2_reject_declared_oversize(declared_size)
        data, content_hash = self._gate_3_read_within_limit(stream)
        text = self._gate_4_decode(data)
        forms, occurrences = self._gate_5_aggregate(text)
        return self._gate_6_persist(forms, occurrences, content_hash)

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

    def _gate_3_read_within_limit(self, stream: ByteStream) -> tuple[bytes, str]:
        """Accumulate the body and its SHA-256 hash, abandoning the read one byte
        past the limit.

        Reading one byte beyond is what distinguishes "at the limit" from "over
        it" without ever holding more: the comparison is ``>`` and not ``>=``, so
        a file of exactly ``max_import_size_bytes`` imports (AC-002-04). The hash
        covers the raw uploaded bytes, computed before decoding (Art. VI.3,
        REQ-002-009) — even a rejected upload's hash is discarded, never stored.
        """
        data, content_hash = read_bounded_and_hash(stream, self._max_size_bytes + 1)
        if len(data) > self._max_size_bytes:
            raise FileTooLargeError(limit=self._max_size_bytes)
        return data, content_hash

    def _gate_4_decode(self, data: bytes) -> str:
        """Decode strictly as UTF-8. Raises ``InvalidEncodingError`` on bad bytes."""
        return self._extractor.extract(data)

    def _gate_5_aggregate(
        self, text: str
    ) -> tuple[tuple[FormFrequency, ...], tuple[tuple[str, str, int], ...]]:
        """Tokenize and normalize once, feeding both the table and persistence.

        A token whose normalized form is empty is dropped rather than counted, so
        no row can carry an empty grouping key and no `Occurrence` is written for
        it either — the two never diverge, because both are derived from the
        same filtered sequence.
        """
        occurrences = tuple(
            (token.raw_text, normalized, token.position)
            for token in tokenize(text)
            if (normalized := normalize(token.raw_text))
        )
        pairs = [(raw_text, normalized_text, 1) for raw_text, normalized_text, _ in occurrences]
        forms = build_table(pairs)
        return forms, occurrences

    def _gate_6_persist(
        self,
        forms: tuple[FormFrequency, ...],
        occurrences: tuple[tuple[str, str, int], ...],
        content_hash: str,
    ) -> ImportResult:
        """Persist the `Book` and its `Occurrence` rows; return the full result.

        A repository failure is never re-raised as-is: the underlying driver
        exception could in principle render bound parameters into its message,
        so it is replaced with a content-free `PersistenceFailedError` before it
        can reach a log or a traceback (Art. X.2, REQ-002-013).
        """
        total_token_count = len(occurrences)
        try:
            book_id = self._repository.create(
                content_hash=content_hash,
                token_count=total_token_count,
                created_at=self._clock.now_utc(),
                occurrences=occurrences,
            )
        except Exception:
            raise PersistenceFailedError() from None
        return ImportResult(
            id=book_id,
            forms=forms,
            distinct_form_count=len(forms),
            total_token_count=total_token_count,
        )


class ReadImport:
    """Read a persisted import's ordered frequency table — the GET use case.

    Calls the SAME ``domain.frequency.build_table()`` the import path uses, so
    the display-form and ordering rules have one implementation for both write
    and read (design §1, REQ-002-006 full closure — the `GET` leg of AC-002-08
    and AC-002-09).
    """

    def __init__(self, *, repository: BookRepository) -> None:
        self._repository = repository

    def execute(self, book_id: int) -> ImportResult | None:
        """Return the ordered table, or `None` if `book_id` is unknown."""
        pairs = self._repository.frequency_pairs(book_id)
        if pairs is None:
            return None
        forms = build_table(pairs)
        return ImportResult(
            id=book_id,
            forms=forms,
            distinct_form_count=len(forms),
            total_token_count=sum(row.frequency for row in forms),
        )


class DeleteImport:
    """Delete a persisted import and its derived data — the DELETE use case.

    Permanent, not reversible (REQ-002-011): a soft delete is forbidden by
    spec (Art. IV.8 vs Art. IX.5's confirmation-or-reversible disjunction), so
    this calls the repository's hard delete directly with no intermediate
    status flag.
    """

    def __init__(self, *, repository: BookRepository) -> None:
        self._repository = repository

    def execute(self, book_id: int) -> None:
        """Delete the import, or raise `ImportNotFoundError` if unknown."""
        if not self._repository.delete(book_id):
            raise ImportNotFoundError(import_id=book_id)


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

"""The annotation port — design §7.2/P4, spec §2.6 S4, REQ-003-003.

A structural ``Protocol``, following `application/imports/ports.py`'s
shipped precedent (AMB-6): the port lives in `application/`, the pure value
object it returns lives in `domain/`. `application` never imports
`infrastructure` to obtain a conformant type — a plain stdlib double is
enough, as `test_annotation_ports.py` proves.

**Multi-language by design (ADR-0008).** `language` is a REQUIRED
keyword-only argument with NO default anywhere in this module. A second
language is a configuration and adapter concern (`Settings`, Phase 4); it
changes neither this port's signature nor the persisted schema.

**§2.6 S4.** `analyze` accepts only an already-tokenized sequence, never raw
document text — the persisted token stream is the single source of truth
for token boundaries (spec §2.6, three consequences).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Sequence
    from datetime import datetime

    from wheel_vocabulary.domain.annotation import LinguisticAnnotation

__all__ = [
    "AnalyzerIdentity",
    "AnalyzerRegistry",
    "AnnotatedToken",
    "AnnotationReader",
    "AnnotationRecord",
    "AnnotationWriter",
    "LinguisticAnalyzer",
]


@dataclass(frozen=True, slots=True)
class AnalyzerIdentity:
    """Provenance identity an analyzer reports about itself — spec §2.4.

    One call to ``analyze`` produces one identity for every row it covers:
    ``source``, ``model_name`` and ``model_version`` never vary within a
    single run. ``language`` is deliberately excluded — it is supplied by
    the caller to ``analyze``, not reported by the analyzer, so it cannot
    drift from what was actually requested.
    """

    source: str
    model_name: str
    model_version: str


@runtime_checkable
class LinguisticAnalyzer(Protocol):
    """Port for the NLP adapter that produces per-occurrence annotations.

    Any object exposing an ``identity`` attribute and a matching ``analyze``
    method satisfies this port — no base class, no import of the adapter's
    own NLP library required to write a test double (REQ-003-003).
    """

    identity: AnalyzerIdentity

    def analyze(self, tokens: Sequence[str], *, language: str) -> Sequence[LinguisticAnnotation]:
        """Return one annotation per input token, in the same order.

        ``tokens`` MUST be the already-tokenized, ordered textual forms of
        one import — never raw document text (§2.6 S4). ``language`` MUST be
        supplied explicitly; it has no default here or anywhere upstream.

        Each returned ``LinguisticAnnotation.raw_text`` MUST equal the input
        token it was computed for, at the same list position (REQ-003-004,
        C6). At output list index ``i``, ``source_index == i`` MUST also
        hold; violating either pairing obligation is rejected as
        ``ANNOTATION_FAILED``. The caller verifies these pairing conditions, not bare
        position, before pairing an annotation with an occurrence — a
        conforming implementation costs nothing extra here since the token
        text is already in hand while producing each annotation.

        Each annotation's ``pos`` MUST be None or a UPOS tag. Its
        ``pos_confidence`` and ``lemma_confidence`` MUST each be ``None`` or
        within [0.0, 1.0]. Violating either value obligation is rejected as
        ``ANNOTATION_FAILED``.

        Bounded guarantee (REQ-003H-006): the check proves that the analyzer's
        output is **self-consistent with the input it was given** — each
        annotation reports both the token text and the input index it claims to
        have been computed for, and both MUST agree with the occurrence at that
        position, so an internally reordered result of equal length is rejected
        instead of being written to the wrong occurrence. It does **not** prove
        that the annotation is linguistically correct for that token, and it
        cannot detect an analyzer that swaps two same-text annotations while
        consistently reassigning `source_index`, because `source_index` is
        self-reported by the analyzer.

        Raises:
            UnsupportedLanguageError: no analyzer is installed for
                ``language``. Raised before any pipeline loads and before
                any row is written (AC-003-03).
        """
        ...


@runtime_checkable
class AnalyzerRegistry(Protocol):
    """Port `AnnotateImport` depends on to resolve a language to an analyzer.

    Satisfied structurally by `infrastructure/nlp/registry.py::
    AnalyzerRegistry` (design §P4) — `application` never imports that
    module, only this shape.
    """

    def resolve(self, language: str) -> LinguisticAnalyzer:
        """Return the analyzer for ``language``.

        Raises:
            UnsupportedLanguageError: no analyzer is configured for
                ``language``, raised before any pipeline loads (AC-003-03).
        """
        ...


@runtime_checkable
class AnnotatedToken(Protocol):
    """The shape `AnnotateImport` needs from one persisted occurrence.

    Structural, deliberately narrower than
    `infrastructure/persistence/annotation_repository.py::AnnotatedOccurrence`
    (design §P3's read model): `application` never imports that
    `infrastructure` type (Art. VII.2-3), it only declares the two attributes
    it actually reads. `AnnotatedOccurrence` happens to expose both, so it
    satisfies this protocol without either module knowing about the other.

    Declared with read-only ``@property`` members, not plain attribute
    annotations: `AnnotatedOccurrence` and `AnnotateImport`'s own
    ``_ValidatedAnnotation`` are both frozen dataclasses, and a plain
    attribute annotation on a `Protocol` requires a *settable* attribute —
    mypy rejects a frozen dataclass against that shape even though the
    values are structurally identical.
    """

    @property
    def occurrence_id(self) -> int: ...
    @property
    def raw_text(self) -> str: ...


@runtime_checkable
class AnnotationReader(Protocol):
    """Port for reading the ordered token stream `AnnotateImport` annotates.

    Reuses the SAME read path the future `GET` endpoint uses (design's data
    flow diagram names `AnnotationReadRepository` for both) — the caller
    only reads `occurrence_id`/`raw_text` off each returned item and ignores
    the rest.
    """

    def read(self, book_id: int) -> Sequence[AnnotatedToken] | None:
        """Return every occurrence of `book_id`, ordered by `position`.

        `None` means `book_id` is unknown (REQ-003-013's "no book found"
        case) — mirroring `BookRepository.frequency_pairs`'s established
        None-vs-empty-list distinction, never conflated.
        """
        ...


@runtime_checkable
class AnnotationRecord(Protocol):
    """The shape `AnnotateImport` hands to `AnnotationWriter.write()`.

    Matches `infrastructure/persistence/annotation_write_repository.py::
    OccurrenceAnnotation`'s five fields exactly, without importing that
    `infrastructure` type — any object with these five attributes conforms.
    Read-only ``@property`` members for the same reason as `AnnotatedToken`:
    both the real `OccurrenceAnnotation` and `AnnotateImport`'s own
    ``_ValidatedAnnotation`` are frozen dataclasses.
    """

    @property
    def occurrence_id(self) -> int: ...
    @property
    def pos(self) -> str | None: ...
    @property
    def lemma(self) -> str | None: ...
    @property
    def pos_confidence(self) -> float | None: ...
    @property
    def lemma_confidence(self) -> float | None: ...


@runtime_checkable
class AnnotationWriter(Protocol):
    """Port for the unconditional, atomic annotation write — spec §2.5 R2/R3.

    Satisfied structurally by `infrastructure/persistence/
    annotation_write_repository.py::SqlAlchemyAnnotationWriteRepository`.
    """

    def write(
        self,
        *,
        annotations: Sequence[AnnotationRecord],
        identity: AnalyzerIdentity,
        language: str,
        processed_at: datetime,
    ) -> None:
        """Persist every annotation in one transaction (REQ-003-014)."""
        ...

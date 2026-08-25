"""`AnnotateImport` — the annotation use case, design §P5, spec §2.5/§2.6/§4.

Runs strictly as a second pass over already-persisted data (§2.6 S1-S4):
read the ordered token stream, resolve the requested language to an
analyzer, hand the analyzer the WHOLE sequence as one call (REQ-003-021 — a
hard constraint, never chunked), validate every returned annotation, THEN
open the one write transaction. Every step before `writer.write()` runs
outside any transaction (design §P5); a failure at any point means
`writer.write()` is never called at all, so a partially annotated import is
not a state this use case can produce (REQ-003-014).

Privacy (REQ-003-019, AC-003-20): every failure is logged with its error
code, the import id, and — where the failure is attributable to one
token — its zero-based position. Never the token's text, never a lemma,
never a stack trace (`logger.warning`, never `logger.exception`).

REQ-003-004 (length/order), REQ-003-005 (UPOS membership), REQ-003-006
(whitespace lemma -> NULL), REQ-003-008 (confidence range), REQ-003-013
(pre-existing imports are annotatable via the same code path — no special
casing for "already annotated"), REQ-003-014 (atomicity by ordering),
REQ-003-021 (whole-import analyzer call).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from wheel_vocabulary.application.annotation.errors import (
    AnalyzerUnavailableError,
    AnnotationFailedError,
    UnsupportedLanguageError,
)
from wheel_vocabulary.application.imports.errors import ImportNotFoundError
from wheel_vocabulary.domain.annotation import UPOS_TAGS, validate_confidence

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Sequence

    from wheel_vocabulary.application.annotation.ports import (
        AnalyzerRegistry,
        AnnotatedToken,
        AnnotationReader,
        AnnotationWriter,
    )
    from wheel_vocabulary.application.clock import Clock
    from wheel_vocabulary.domain.annotation import LinguisticAnnotation

__all__ = ["AnnotateImport"]

_LOGGER = logging.getLogger(__name__)
_NO_POSITION = "-"


@dataclass(frozen=True, slots=True)
class _ValidatedAnnotation:
    """Satisfies `AnnotationRecord` structurally — the exact five fields
    `AnnotationWriter.write()` reads off each item."""

    occurrence_id: int
    pos: str | None
    lemma: str | None
    pos_confidence: float | None
    lemma_confidence: float | None


class AnnotateImport:
    """Annotate one already-persisted import — the `POST …/annotation` use case."""

    def __init__(
        self,
        *,
        reader: AnnotationReader,
        registry: AnalyzerRegistry,
        writer: AnnotationWriter,
        clock: Clock,
    ) -> None:
        self._reader = reader
        self._registry = registry
        self._writer = writer
        self._clock = clock

    def execute(self, book_id: int, *, language: str) -> None:
        """Run the full annotate-and-write flow for `book_id`.

        Raises:
            ImportNotFoundError: `book_id` is unknown.
            UnsupportedLanguageError: no analyzer is configured for
                `language`; no pipeline loads, nothing is written. Also
                raised if the resolved analyzer's own `analyze()` rejects
                `language` internally (ADR-0008) — never downgraded.
            AnalyzerUnavailableError: the configured model failed to load
                (C5) — missing files, a malformed pipeline, or any other
                load-time defect. The raw exception never escapes: it may
                carry a model name or a filesystem path (REQ-003-019).
            AnnotationFailedError: the analyzer's result is malformed in any
                way (§4) — nothing is written.
        """
        tokens = self._reader.read(book_id)
        if tokens is None:
            self._log_failure(ImportNotFoundError.code, book_id)
            raise ImportNotFoundError(import_id=book_id)

        try:
            analyzer = self._registry.resolve(language)
        except UnsupportedLanguageError:
            self._log_failure(UnsupportedLanguageError.code, book_id)
            raise
        except Exception:
            # C5: a configured model that fails to load — missing files, a
            # malformed pipeline (e.g. a missing pipe raising KeyError), any
            # load-time defect — is a processing/availability problem (503),
            # never a user input problem, and the raw exception (which may
            # carry a model name or a filesystem path, REQ-003-019) must
            # never escape as-is.
            self._log_failure(AnalyzerUnavailableError.code, book_id)
            raise AnalyzerUnavailableError() from None

        raw_texts = [token.raw_text for token in tokens]
        try:
            annotations = analyzer.analyze(raw_texts, language=language)
        except AnnotationFailedError:
            self._log_failure(AnnotationFailedError.code, book_id)
            raise
        except UnsupportedLanguageError:
            # ports.py::LinguisticAnalyzer.analyze documents this as a
            # legitimate raise from inside analyze() itself (a
            # multi-language adapter dispatching internally, ADR-0008) — it
            # is a real 422, and must propagate as one, never be caught by
            # the blanket branch below and downgraded to a 500.
            self._log_failure(UnsupportedLanguageError.code, book_id)
            raise
        except Exception:
            # spec §4: every ANNOTATION_FAILED trigger is an adapter or
            # model defect, never something the user supplied — a crash
            # mid-analysis is classified the same way, content-free.
            self._log_failure(AnnotationFailedError.code, book_id)
            raise AnnotationFailedError() from None

        records = self._validate_and_assemble(tokens, annotations, book_id=book_id)

        self._writer.write(
            annotations=records,
            identity=analyzer.identity,
            language=language,
            processed_at=self._clock.now_utc(),
        )

    def _validate_and_assemble(
        self,
        tokens: Sequence[AnnotatedToken],
        annotations: Sequence[LinguisticAnnotation],
        *,
        book_id: int,
    ) -> list[_ValidatedAnnotation]:
        """REQ-003-004/005/006/008: every check runs before any write.

        `AnnotationFailedError` is raised on the FIRST violation found — the
        exact position is logged when the violation is attributable to one
        token, matching AC-003-20's "where applicable" qualifier.
        """
        if len(annotations) != len(tokens):
            self._log_failure(AnnotationFailedError.code, book_id)
            raise AnnotationFailedError()

        records: list[_ValidatedAnnotation] = []
        for position, (token, annotation) in enumerate(zip(tokens, annotations, strict=True)):
            # C6 + R1 (Judgment Day round 2): verify the pairing by identity,
            # not bare list position, and not content alone. A same-length
            # but internally reordered analyzer result would otherwise be
            # silently written to the wrong occurrence — this is what
            # REQ-003-004's "ordering mismatch" clause requires to fail
            # loudly instead. `raw_text` equality alone is NOT identity: two
            # occurrences sharing the same surface form (a homograph, or any
            # repeated token) can have correct-but-swapped annotations pass
            # a bare content comparison, because both annotations' text
            # matches both tokens' text. `source_index` closes that gap —
            # each annotation must echo the exact position it was produced
            # for, verified against the position the caller is currently
            # pairing it against.
            if annotation.raw_text != token.raw_text or annotation.source_index != position:
                self._log_failure(AnnotationFailedError.code, book_id, position=position)
                raise AnnotationFailedError()

            pos = annotation.pos
            if pos is not None and pos not in UPOS_TAGS:
                self._log_failure(AnnotationFailedError.code, book_id, position=position)
                raise AnnotationFailedError()
            try:
                validate_confidence(annotation.pos_confidence)
                validate_confidence(annotation.lemma_confidence)
            except ValueError:
                self._log_failure(AnnotationFailedError.code, book_id, position=position)
                raise AnnotationFailedError() from None

            records.append(
                _ValidatedAnnotation(
                    occurrence_id=token.occurrence_id,
                    pos=pos,
                    lemma=_null_if_blank(annotation.lemma),
                    pos_confidence=annotation.pos_confidence,
                    lemma_confidence=annotation.lemma_confidence,
                )
            )
        return records

    def _log_failure(self, code: str, book_id: int, *, position: int | None = None) -> None:
        """REQ-003-019/AC-003-20: code, import id, position — never text."""
        logged_position = position if position is not None else _NO_POSITION
        _LOGGER.warning("code=%s import_id=%s position=%s", code, book_id, logged_position)


def _null_if_blank(value: str | None) -> str | None:
    """§2.1 L4: a whitespace-only value persists as `NULL`, never `""`."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None

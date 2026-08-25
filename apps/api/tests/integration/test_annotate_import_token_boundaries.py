"""AC-003-04 scenario 3 — SPEC-002 token boundaries survive annotation.

`state-of-the-art` and `don't` are SPEC-002's own hardest tokenization
fixtures (`tests/unit/test_tokenizer.py::T2`/`T3` — a hyphen chain and an
apostrophe-internal contraction that must stay ONE token each, never split
on the hyphen or the apostrophe). Every existing test proving that lives
entirely inside SPEC-002's own suite (`test_tokenizer.py`, `test_normalizer.py`)
and never runs those fixtures through the annotation path at all — nothing
proved that `AnnotateImport`, which reads back already-persisted occurrences
and writes `pos`/`lemma` in place, leaves the *token itself* — its `raw_text`,
its `position`, and the fact that it is exactly one `Occurrence` row — intact.

This module closes that gap by running the REAL pipeline end to end: the
REAL `ImportText` use case (SPEC-002) persists the text through the REAL
`SqlAlchemyBookRepository`, then the REAL `AnnotateImport` use case (SPEC-003)
runs over the SAME database through the REAL annotation repositories. Only
the analyzer is a deterministic stdlib fake — what is under test here is
token-boundary preservation across the SPEC-002/SPEC-003 boundary, not the
real model's linguistic output (that is `test_spacy_analyzer.py`'s job).

REQ-003-004, REQ-003-013, AC-003-04 scenario 3.
"""

from __future__ import annotations

import io
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from wheel_vocabulary.application.annotation.ports import AnalyzerIdentity
from wheel_vocabulary.application.annotation.use_cases import AnnotateImport
from wheel_vocabulary.application.imports.use_cases import ImportText
from wheel_vocabulary.domain.annotation import LinguisticAnnotation
from wheel_vocabulary.infrastructure.persistence.annotation_repository import (
    SqlAlchemyAnnotationReadRepository,
)
from wheel_vocabulary.infrastructure.persistence.annotation_write_repository import (
    SqlAlchemyAnnotationWriteRepository,
)
from wheel_vocabulary.infrastructure.persistence.book_repository import SqlAlchemyBookRepository
from wheel_vocabulary.infrastructure.text_extraction import PlainTextExtractor

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.orm import Session, sessionmaker

_IMPORT_TIME = datetime(2026, 8, 24, 12, 0, 0, tzinfo=UTC)
_ANNOTATE_TIME = datetime(2026, 8, 24, 13, 0, 0, tzinfo=UTC)
_IDENTITY = AnalyzerIdentity(source="fake", model_name="fake-model", model_version="1.0")
# The exact SPEC-002 hardest-case fixtures (test_tokenizer.py T2/T3): a
# hyphen chain and an apostrophe-internal contraction, each ONE token.
_TEXT = "state-of-the-art don't"


class _FixedClock:
    def __init__(self, times: Sequence[datetime]) -> None:
        self._times = iter(times)

    def now_utc(self) -> datetime:
        return next(self._times)


class _TaggingAnalyzer:
    """A deterministic stdlib fake — proves boundary preservation, not
    linguistic accuracy (the real adapter's job is `test_spacy_analyzer.py`)."""

    identity = _IDENTITY

    def analyze(self, tokens: Sequence[str], *, language: str) -> Sequence[LinguisticAnnotation]:
        del language
        return [
            LinguisticAnnotation(
                raw_text=token,
                source_index=index,
                pos="NOUN",
                lemma=token,
                pos_confidence=None,
                lemma_confidence=None,
            )
            for index, token in enumerate(tokens)
        ]


class _SingleLanguageRegistry:
    def __init__(self, analyzer: _TaggingAnalyzer) -> None:
        self._analyzer = analyzer

    def resolve(self, language: str) -> _TaggingAnalyzer:
        del language
        return self._analyzer


@pytest.mark.integration
def test_hyphenated_and_apostrophe_tokens_stay_one_occurrence_each_after_annotation(
    annotation_session_factory: sessionmaker[Session],
) -> None:
    """AC-003-04 scenario 3: after a real annotation run, `state-of-the-art`
    and `don't` are each still exactly one occurrence, at their original
    position, with `raw_text` byte-identical to what SPEC-002 tokenized —
    annotation never re-splits, re-merges, or rewrites a token boundary."""
    book_repository = SqlAlchemyBookRepository(annotation_session_factory)
    import_use_case = ImportText(
        extractor=PlainTextExtractor(),
        max_size_bytes=4 * 1024 * 1024,
        repository=book_repository,
        clock=_FixedClock([_IMPORT_TIME]),
    )

    import_result = import_use_case.execute(
        filename="sample.txt",
        content_type="text/plain",
        stream=io.BytesIO(_TEXT.encode("utf-8")),
    )

    read_repository = SqlAlchemyAnnotationReadRepository(annotation_session_factory)
    write_repository = SqlAlchemyAnnotationWriteRepository(annotation_session_factory)
    before = read_repository.read(import_result.id)
    assert before is not None
    assert [row.raw_text for row in before] == ["state-of-the-art", "don't"]
    assert [row.position for row in before] == [0, 1]

    AnnotateImport(
        reader=read_repository,
        registry=_SingleLanguageRegistry(_TaggingAnalyzer()),
        writer=write_repository,
        clock=_FixedClock([_ANNOTATE_TIME]),
    ).execute(import_result.id, language="en")

    after = read_repository.read(import_result.id)
    assert after is not None
    assert len(after) == 2, "annotation must not split or merge a token"
    assert [row.raw_text for row in after] == ["state-of-the-art", "don't"]
    assert [row.position for row in after] == [0, 1]
    # Confirms the run actually annotated (not a no-op that would trivially
    # preserve boundaries by never touching the rows).
    assert [row.effective_pos for row in after] == ["NOUN", "NOUN"]
    assert [row.lemma for row in after] == ["state-of-the-art", "don't"]

"""Unit tests for `AnnotateImport` — design §P5, spec §2.6/§4, REQ-003-004.

Written RED before `application/annotation/use_cases.py` exists: the import
below is the only thing that can fail at collection time.

Every dependency is a plain stdlib fake satisfying the structural ports in
`application/annotation/ports.py` — no database, no spaCy, mirroring
`application/imports/use_cases.py`'s own test precedent (this module has no
direct precedent test file yet, but the pattern is the same one
`test_annotation_ports.py` already established for the port itself).

**Full validation before the transaction opens (design §P5).** Every
failure-mode test below asserts `writer.calls == []` — not merely that the
right exception was raised. That is the literal claim task 4.9 makes:
`writer.write()` must never be reached when any input is invalid, so a
partially-annotated import is not a state this use case can produce.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from wheel_vocabulary.application.annotation.errors import (
    AnnotationFailedError,
    UnsupportedLanguageError,
)
from wheel_vocabulary.application.annotation.ports import AnalyzerIdentity
from wheel_vocabulary.application.annotation.use_cases import AnnotateImport
from wheel_vocabulary.application.imports.errors import ImportNotFoundError
from wheel_vocabulary.domain.annotation import LinguisticAnnotation

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

_NOW = datetime(2026, 8, 24, 12, 0, 0, tzinfo=UTC)
_IDENTITY = AnalyzerIdentity(source="stub", model_name="stub-model", model_version="0.0")


@dataclass(frozen=True, slots=True)
class _Token:
    """Satisfies `AnnotatedToken` structurally."""

    occurrence_id: int
    raw_text: str


class _FakeReader:
    """Satisfies `AnnotationReader` structurally."""

    def __init__(self, tokens_by_book: Mapping[int, list[tuple[int, str]]]) -> None:
        self._tokens_by_book = tokens_by_book

    def read(self, book_id: int) -> list[_Token] | None:
        rows = self._tokens_by_book.get(book_id)
        if rows is None:
            return None
        return [_Token(occurrence_id=occurrence_id, raw_text=text) for occurrence_id, text in rows]


@dataclass
class _WriteCall:
    annotations: list[object]
    identity: AnalyzerIdentity
    language: str
    processed_at: datetime


class _FakeWriter:
    """Satisfies `AnnotationWriter` structurally; records every call."""

    def __init__(self) -> None:
        self.calls: list[_WriteCall] = []

    def write(
        self,
        *,
        annotations: Sequence[object],
        identity: AnalyzerIdentity,
        language: str,
        processed_at: datetime,
    ) -> None:
        self.calls.append(
            _WriteCall(
                annotations=list(annotations),
                identity=identity,
                language=language,
                processed_at=processed_at,
            )
        )


class _FakeRegistry:
    """Satisfies `AnalyzerRegistry` structurally."""

    def __init__(self, analyzers: Mapping[str, object]) -> None:
        self._analyzers = analyzers

    def resolve(self, language: str) -> object:
        analyzer = self._analyzers.get(language)
        if analyzer is None:
            raise UnsupportedLanguageError(language=language)
        return analyzer


class _StubAnalyzer:
    """Satisfies `LinguisticAnalyzer` structurally; `produce` decides output."""

    def __init__(
        self, *, produce: Callable[[Sequence[str]], Sequence[LinguisticAnnotation]]
    ) -> None:
        self.identity = _IDENTITY
        self._produce = produce

    def analyze(self, tokens: Sequence[str], *, language: str) -> Sequence[LinguisticAnnotation]:
        del language
        return self._produce(tokens)


class _FakeClock:
    """Returns each queued time in order — proves `processed_at` provenance."""

    def __init__(self, times: Sequence[datetime]) -> None:
        self._times = iter(times)

    def now_utc(self) -> datetime:
        return next(self._times)


def _use_case(
    *,
    tokens_by_book: Mapping[int, list[tuple[int, str]]],
    analyzers: Mapping[str, object],
    times: Sequence[datetime] = (_NOW,),
) -> tuple[AnnotateImport, _FakeWriter]:
    writer = _FakeWriter()
    use_case = AnnotateImport(
        reader=_FakeReader(tokens_by_book),
        registry=_FakeRegistry(analyzers),
        writer=writer,
        clock=_FakeClock(times),
    )
    return use_case, writer


def _annotation(
    pos: str | None, lemma: str | None, pos_confidence: float | None = None
) -> LinguisticAnnotation:
    return LinguisticAnnotation(
        pos=pos, lemma=lemma, pos_confidence=pos_confidence, lemma_confidence=None
    )


# --------------------------------------------------------------------------
# Success path.
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_execute_writes_one_validated_record_per_token_in_order() -> None:
    analyzer = _StubAnalyzer(
        produce=lambda tokens: [
            _annotation("VERB", "run", 0.9),
            _annotation("NOUN", "dog"),
        ]
    )
    use_case, writer = _use_case(
        tokens_by_book={1: [(10, "run"), (11, "dog")]}, analyzers={"en": analyzer}
    )

    use_case.execute(1, language="en")

    assert len(writer.calls) == 1
    call = writer.calls[0]
    assert call.identity is _IDENTITY
    assert call.language == "en"
    assert call.processed_at == _NOW
    records = call.annotations
    assert [(r.occurrence_id, r.pos, r.lemma) for r in records] == [  # type: ignore[attr-defined]
        (10, "VERB", "run"),
        (11, "NOUN", "dog"),
    ]


@pytest.mark.unit
def test_execute_of_a_book_with_zero_occurrences_writes_an_empty_sequence() -> None:
    """REQ-002-012's zero-occurrence state, re-verified for annotation."""
    analyzer = _StubAnalyzer(produce=lambda tokens: [])
    use_case, writer = _use_case(tokens_by_book={1: []}, analyzers={"en": analyzer})

    use_case.execute(1, language="en")

    assert writer.calls[0].annotations == []


@pytest.mark.unit
def test_a_none_pos_passes_validation_as_not_yet_annotated() -> None:
    """REQ-003-005: `None` means unannotated, distinct from an invalid tag."""
    analyzer = _StubAnalyzer(produce=lambda tokens: [_annotation(None, None)])
    use_case, writer = _use_case(tokens_by_book={1: [(10, "x")]}, analyzers={"en": analyzer})

    use_case.execute(1, language="en")

    assert writer.calls[0].annotations[0].pos is None  # type: ignore[attr-defined]


@pytest.mark.unit
def test_a_whitespace_only_lemma_is_normalized_to_none_not_rejected() -> None:
    """AC-003-06: whitespace-only lemma persists as NULL, not an empty
    string, and this is a success — not one of the failure modes below."""
    analyzer = _StubAnalyzer(produce=lambda tokens: [_annotation("X", "   ")])
    use_case, writer = _use_case(tokens_by_book={1: [(10, "x")]}, analyzers={"en": analyzer})

    use_case.execute(1, language="en")

    assert writer.calls[0].annotations[0].lemma is None  # type: ignore[attr-defined]


# --------------------------------------------------------------------------
# Unknown book / unsupported language.
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_execute_raises_import_not_found_for_an_unknown_book() -> None:
    use_case, writer = _use_case(tokens_by_book={}, analyzers={})

    with pytest.raises(ImportNotFoundError):
        use_case.execute(999, language="en")

    assert writer.calls == []


@pytest.mark.unit
def test_execute_propagates_unsupported_language_and_writes_nothing() -> None:
    """AC-003-03: no fallback, no partial write."""
    use_case, writer = _use_case(tokens_by_book={1: [(10, "run")]}, analyzers={})

    with pytest.raises(UnsupportedLanguageError):
        use_case.execute(1, language="fr")

    assert writer.calls == []


# --------------------------------------------------------------------------
# The 6 stub failure modes (task 4.9) — every one writes nothing.
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_a_short_return_fails_annotation_failed_and_writes_nothing() -> None:
    """AC-003-04: one fewer annotation than tokens fails the run."""
    analyzer = _StubAnalyzer(produce=lambda tokens: [_annotation("VERB", "run")])
    use_case, writer = _use_case(
        tokens_by_book={1: [(10, "run"), (11, "dog")]}, analyzers={"en": analyzer}
    )

    with pytest.raises(AnnotationFailedError):
        use_case.execute(1, language="en")

    assert writer.calls == []


@pytest.mark.unit
def test_a_non_upos_tag_fails_annotation_failed_and_writes_nothing() -> None:
    """AC-003-05: `NN` (Penn Treebank, not UPOS) is rejected, never coerced."""
    analyzer = _StubAnalyzer(produce=lambda tokens: [_annotation("NN", "run")])
    use_case, writer = _use_case(tokens_by_book={1: [(10, "run")]}, analyzers={"en": analyzer})

    with pytest.raises(AnnotationFailedError):
        use_case.execute(1, language="en")

    assert writer.calls == []


@pytest.mark.unit
def test_an_out_of_range_confidence_fails_annotation_failed_and_writes_nothing() -> None:
    """AC-003-08: `1.4` fails, never clamped to `1.0`."""
    analyzer = _StubAnalyzer(produce=lambda tokens: [_annotation("VERB", "run", 1.4)])
    use_case, writer = _use_case(tokens_by_book={1: [(10, "run")]}, analyzers={"en": analyzer})

    with pytest.raises(AnnotationFailedError):
        use_case.execute(1, language="en")

    assert writer.calls == []


@pytest.mark.unit
def test_an_analyzer_raising_annotation_failed_directly_is_not_double_wrapped() -> None:
    """If an analyzer ever raises `AnnotationFailedError` itself, it
    propagates as-is rather than being caught by the generic-exception
    branch and wrapped a second time."""

    def _raise_annotation_failed(tokens: Sequence[str]) -> Sequence[LinguisticAnnotation]:
        del tokens
        raise AnnotationFailedError

    analyzer = _StubAnalyzer(produce=_raise_annotation_failed)
    use_case, writer = _use_case(tokens_by_book={1: [(10, "run")]}, analyzers={"en": analyzer})

    with pytest.raises(AnnotationFailedError):
        use_case.execute(1, language="en")

    assert writer.calls == []


@pytest.mark.unit
def test_a_crash_mid_analysis_fails_annotation_failed_and_writes_nothing() -> None:
    """The analyzer raising an arbitrary exception is still an adapter
    defect (spec §4's closing note) — translated, never left to propagate
    as some other unclassified exception type."""

    def _boom(tokens: Sequence[str]) -> Sequence[LinguisticAnnotation]:
        del tokens
        message = "simulated crash"
        raise RuntimeError(message)

    analyzer = _StubAnalyzer(produce=_boom)
    use_case, writer = _use_case(tokens_by_book={1: [(10, "run")]}, analyzers={"en": analyzer})

    with pytest.raises(AnnotationFailedError):
        use_case.execute(1, language="en")

    assert writer.calls == []


@pytest.mark.unit
def test_a_second_token_failure_still_writes_nothing_for_the_whole_batch() -> None:
    """design §P5: validation covers the WHOLE batch before any write — a
    valid first token does not get written while a later one fails."""
    analyzer = _StubAnalyzer(
        produce=lambda tokens: [_annotation("VERB", "run"), _annotation("NN", "dog")]
    )
    use_case, writer = _use_case(
        tokens_by_book={1: [(10, "run"), (11, "dog")]}, analyzers={"en": analyzer}
    )

    with pytest.raises(AnnotationFailedError):
        use_case.execute(1, language="en")

    assert writer.calls == []


@pytest.mark.unit
def test_execute_of_an_unsupported_language_never_writes_even_with_valid_tokens() -> None:
    """The sixth stub mode restated with a non-empty book, matching the
    exact AC-003-03 scenario shape (some tokens exist, language is still
    rejected)."""
    use_case, writer = _use_case(
        tokens_by_book={1: [(10, "run"), (11, "dog")]},
        analyzers={"en": _StubAnalyzer(produce=lambda t: [])},
    )

    with pytest.raises(UnsupportedLanguageError):
        use_case.execute(1, language="de")

    assert writer.calls == []

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
    AnalyzerUnavailableError,
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
    pos: str | None,
    lemma: str | None,
    pos_confidence: float | None = None,
    *,
    raw_text: str,
    source_index: int = 0,
) -> LinguisticAnnotation:
    return LinguisticAnnotation(
        raw_text=raw_text,
        source_index=source_index,
        pos=pos,
        lemma=lemma,
        pos_confidence=pos_confidence,
        lemma_confidence=None,
    )


# --------------------------------------------------------------------------
# Success path.
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_execute_writes_one_validated_record_per_token_in_order() -> None:
    analyzer = _StubAnalyzer(
        produce=lambda tokens: [
            _annotation("VERB", "run", 0.9, raw_text="run", source_index=0),
            _annotation("NOUN", "dog", raw_text="dog", source_index=1),
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
def test_same_text_swap_with_consistently_reassigned_source_index_is_accepted() -> None:
    """REQ-003H-006 G3: this accepted result is the documented bound.

    `source_index` is self-reported by the analyzer, so a same-text swap that
    also reassigns its indexes is self-consistent with the inputs it claims.
    The port contract deliberately does not claim to detect this case.
    """
    analyzer = _StubAnalyzer(
        produce=lambda tokens: [
            _annotation("NOUN", "saw", raw_text="saw", source_index=0),
            _annotation("VERB", "see", raw_text="saw", source_index=1),
        ]
    )
    use_case, writer = _use_case(
        tokens_by_book={1: [(10, "saw"), (11, "saw")]}, analyzers={"en": analyzer}
    )

    use_case.execute(1, language="en")

    assert len(writer.calls) == 1
    records = writer.calls[0].annotations
    assert [(record.occurrence_id, record.pos, record.lemma) for record in records] == [  # type: ignore[attr-defined]
        (10, "NOUN", "saw"),
        (11, "VERB", "see"),
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
    analyzer = _StubAnalyzer(produce=lambda tokens: [_annotation(None, None, raw_text="x")])
    use_case, writer = _use_case(tokens_by_book={1: [(10, "x")]}, analyzers={"en": analyzer})

    use_case.execute(1, language="en")

    assert writer.calls[0].annotations[0].pos is None  # type: ignore[attr-defined]


@pytest.mark.unit
def test_a_whitespace_only_lemma_is_normalized_to_none_not_rejected() -> None:
    """AC-003-06: whitespace-only lemma persists as NULL, not an empty
    string, and this is a success — not one of the failure modes below."""
    analyzer = _StubAnalyzer(produce=lambda tokens: [_annotation("X", "   ", raw_text="x")])
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
# C5 — a model load failure must never escape raw or leak a filesystem path.
# --------------------------------------------------------------------------


class _ExplodingRegistry:
    """Raises an arbitrary exception from `resolve()` — simulating a real
    `spacy.load()`/pipeline-assembly failure surfacing through
    `AnalyzerRegistry.resolve()` (`infrastructure/nlp/registry.py`)."""

    def __init__(self, exc: BaseException) -> None:
        self._exc = exc

    def resolve(self, language: str) -> object:
        del language
        raise self._exc


@pytest.mark.unit
def test_a_missing_model_os_error_becomes_analyzer_unavailable_and_writes_nothing() -> None:
    """C5: `spacy.load()` raises a raw `OSError` for a missing/unloadable
    model, and that error's own message routinely carries the model name or
    a filesystem path (spaCy's real `E050` message does exactly this) — a
    string `application/annotation/errors.py` explicitly forbids leaking
    (REQ-003-019). It must be translated to `AnalyzerUnavailableError` (503),
    never left to propagate as-is."""
    path_leaking_error = OSError(
        "[E050] Can't find model '/home/user/.venv/models/en_core_web_sm-3.8.0'"
    )
    use_case = AnnotateImport(
        reader=_FakeReader({1: [(10, "run")]}),
        registry=_ExplodingRegistry(path_leaking_error),
        writer=_FakeWriter(),
        clock=_FakeClock([_NOW]),
    )

    with pytest.raises(AnalyzerUnavailableError) as excinfo:
        use_case.execute(1, language="en")

    assert "/home/user" not in excinfo.value.message
    assert "en_core_web_sm" not in excinfo.value.message


@pytest.mark.unit
def test_a_missing_model_os_error_writes_nothing() -> None:
    """C5: the writer is never reached when the model fails to load."""
    writer = _FakeWriter()
    use_case = AnnotateImport(
        reader=_FakeReader({1: [(10, "run")]}),
        registry=_ExplodingRegistry(OSError("model not found")),
        writer=writer,
        clock=_FakeClock([_NOW]),
    )

    with pytest.raises(AnalyzerUnavailableError):
        use_case.execute(1, language="en")

    assert writer.calls == []


@pytest.mark.unit
def test_a_malformed_pipeline_key_error_becomes_analyzer_unavailable() -> None:
    """C5: a `KeyError` (e.g. `get_pipe` on a missing pipe) is equally a
    load-time adapter defect, not a user input problem — same translation
    applies regardless of the raw exception TYPE the loader happens to
    raise."""
    use_case = AnnotateImport(
        reader=_FakeReader({1: [(10, "run")]}),
        registry=_ExplodingRegistry(KeyError("tagger")),
        writer=_FakeWriter(),
        clock=_FakeClock([_NOW]),
    )

    with pytest.raises(AnalyzerUnavailableError):
        use_case.execute(1, language="en")


@pytest.mark.unit
def test_an_analyzer_raising_unsupported_language_from_analyze_is_not_downgraded() -> None:
    """C5: `ports.py::LinguisticAnalyzer.analyze` documents
    `UnsupportedLanguageError` as a legitimate raise from inside `analyze()`
    itself (a multi-language adapter dispatching internally, ADR-0008). The
    blanket `except Exception` around that call must not catch and downgrade
    it to a 500 `ANNOTATION_FAILED`, discarding the real 422 cause."""

    def _raise_unsupported(tokens: Sequence[str]) -> Sequence[LinguisticAnnotation]:
        del tokens
        raise UnsupportedLanguageError(language="xx")

    analyzer = _StubAnalyzer(produce=_raise_unsupported)
    use_case, writer = _use_case(tokens_by_book={1: [(10, "run")]}, analyzers={"en": analyzer})

    with pytest.raises(UnsupportedLanguageError):
        use_case.execute(1, language="en")

    assert writer.calls == []


# --------------------------------------------------------------------------
# The 6 stub failure modes (task 4.9) plus C6's identity-mismatch mode —
# every one writes nothing.
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_a_reordered_same_length_output_fails_annotation_failed_and_writes_nothing() -> None:
    """C6: pairing is verified by identity (`raw_text`), not bare list
    position. Same length as the token stream, but the two annotations are
    swapped relative to what each token actually is — a buggy or malicious
    analyzer violating its own "same order" contract. Before the fix, this
    was silently written: occurrence 10 ("run") would receive the "dog"
    annotation and vice versa, with no error and no log entry."""
    analyzer = _StubAnalyzer(
        produce=lambda tokens: [
            _annotation("NOUN", "dog", raw_text="dog"),  # belongs to token 11, placed first
            _annotation("VERB", "run", raw_text="run"),  # belongs to token 10, placed second
        ]
    )
    use_case, writer = _use_case(
        tokens_by_book={1: [(10, "run"), (11, "dog")]}, analyzers={"en": analyzer}
    )

    with pytest.raises(AnnotationFailedError):
        use_case.execute(1, language="en")

    assert writer.calls == []


@pytest.mark.unit
def test_same_text_swap_without_reassigning_source_index_fails_and_writes_nothing() -> None:
    """REQ-003H-006 covered-case control: `raw_text` content equality alone cannot
    catch a swap between two occurrences that share the SAME surface form —
    homographs such as "saw" (VERB "see" vs. NOUN "saw") are pervasive in
    real prose. Occurrence 10 ("saw", the verb) and occurrence 11 ("saw",
    the noun) both have `raw_text == "saw"`; the stub analyzer returns the
    two CORRECT annotations but at SWAPPED positions. Every prior C6 test
    used tokens with different `raw_text` ("run"/"dog"), so this exact
    same-surface-form swap was never exercised — this is the residual gap
    both judges reproduced.

    RED (before the fix, verified 2026-08-25): the assertion
    `pytest.raises(AnnotationFailedError)` fails with
    `Failed: DID NOT RAISE <class '...AnnotationFailedError'>` — the old
    `annotation.raw_text != token.raw_text` check passes for both swapped
    positions (content is identical), so occurrence 10 silently receives the
    NOUN/"saw" tag and occurrence 11 silently receives the VERB/"see" tag,
    with no error and no `_log_failure` record.
    """
    analyzer = _StubAnalyzer(
        produce=lambda tokens: [
            # Correctly computed for input index 1 (`source_index=1`), but
            # placed at output position 0 — belongs to occurrence 11.
            _annotation("NOUN", "saw", raw_text="saw", source_index=1),
            # Correctly computed for input index 0 (`source_index=0`), but
            # placed at output position 1 — belongs to occurrence 10.
            _annotation("VERB", "see", raw_text="saw", source_index=0),
        ]
    )
    use_case, writer = _use_case(
        tokens_by_book={1: [(10, "saw"), (11, "saw")]}, analyzers={"en": analyzer}
    )

    with pytest.raises(AnnotationFailedError):
        use_case.execute(1, language="en")

    assert writer.calls == []


@pytest.mark.unit
def test_a_short_return_fails_annotation_failed_and_writes_nothing() -> None:
    """AC-003-04: one fewer annotation than tokens fails the run."""
    analyzer = _StubAnalyzer(produce=lambda tokens: [_annotation("VERB", "run", raw_text="run")])
    use_case, writer = _use_case(
        tokens_by_book={1: [(10, "run"), (11, "dog")]}, analyzers={"en": analyzer}
    )

    with pytest.raises(AnnotationFailedError):
        use_case.execute(1, language="en")

    assert writer.calls == []


@pytest.mark.unit
def test_a_non_upos_tag_fails_annotation_failed_and_writes_nothing() -> None:
    """AC-003-05: `NN` (Penn Treebank, not UPOS) is rejected, never coerced."""
    analyzer = _StubAnalyzer(produce=lambda tokens: [_annotation("NN", "run", raw_text="run")])
    use_case, writer = _use_case(tokens_by_book={1: [(10, "run")]}, analyzers={"en": analyzer})

    with pytest.raises(AnnotationFailedError):
        use_case.execute(1, language="en")

    assert writer.calls == []


@pytest.mark.unit
def test_an_out_of_range_confidence_fails_annotation_failed_and_writes_nothing() -> None:
    """AC-003-08: `1.4` fails, never clamped to `1.0`."""
    analyzer = _StubAnalyzer(
        produce=lambda tokens: [_annotation("VERB", "run", 1.4, raw_text="run")]
    )
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
        produce=lambda tokens: [
            _annotation("VERB", "run", raw_text="run", source_index=0),
            _annotation("NN", "dog", raw_text="dog", source_index=1),
        ]
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

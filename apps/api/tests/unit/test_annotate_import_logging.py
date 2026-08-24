"""Log-egress tests for `AnnotateImport` — REQ-003-019, AC-003-20.

Task 4.13. Two legs, and they are not equally strong — mirroring
`tests/api/test_imports_logging.py`'s own documented split.

The **failure leg** is a genuine assertion: a failure must produce a record
naming the error code, the import id, and — where applicable — the token
position, and nothing else. Before the use case logs, that assertion finds
zero matching records and fails.

The **success leg** is an absence assertion. It passes on the first run over
code that logs nothing at all, which proves nothing whatsoever. It is only
trusted after being seen failing: temporarily logged the raw token list at
`INFO`, confirmed the sentinel assertion fired, reverted.

The sentinel is `zzqxsentinel` — a token that cannot occur by accident, so
any match is a real leak rather than a coincidence, mirroring the SPEC-002
precedent's own sentinel choice.
"""

from __future__ import annotations

import logging
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
    from collections.abc import Callable, Iterable, Mapping, Sequence

_SENTINEL = "zzqxsentinel"
_NOW = datetime(2026, 8, 24, 12, 0, 0, tzinfo=UTC)
_IDENTITY = AnalyzerIdentity(source="stub", model_name="stub-model", model_version="0.0")


@dataclass(frozen=True, slots=True)
class _Token:
    occurrence_id: int
    raw_text: str


class _FakeReader:
    def __init__(self, tokens_by_book: Mapping[int, list[tuple[int, str]]]) -> None:
        self._tokens_by_book = tokens_by_book

    def read(self, book_id: int) -> list[_Token] | None:
        rows = self._tokens_by_book.get(book_id)
        if rows is None:
            return None
        return [_Token(occurrence_id=occurrence_id, raw_text=text) for occurrence_id, text in rows]


class _FakeWriter:
    def __init__(self) -> None:
        self.calls = 0

    def write(self, **_kwargs: object) -> None:
        self.calls += 1


class _FakeRegistry:
    def __init__(self, analyzers: Mapping[str, object]) -> None:
        self._analyzers = analyzers

    def resolve(self, language: str) -> object:
        analyzer = self._analyzers.get(language)
        if analyzer is None:
            raise UnsupportedLanguageError(language=language)
        return analyzer


class _StubAnalyzer:
    def __init__(
        self, *, produce: Callable[[Sequence[str]], Sequence[LinguisticAnnotation]]
    ) -> None:
        self.identity = _IDENTITY
        self._produce = produce

    def analyze(self, tokens: Sequence[str], *, language: str) -> Sequence[LinguisticAnnotation]:
        del language
        return self._produce(tokens)


class _FixedClock:
    def now_utc(self) -> datetime:
        return _NOW


def _use_case(
    *, tokens_by_book: Mapping[int, list[tuple[int, str]]], analyzers: Mapping[str, object]
) -> AnnotateImport:
    return AnnotateImport(
        reader=_FakeReader(tokens_by_book),
        registry=_FakeRegistry(analyzers),
        writer=_FakeWriter(),
        clock=_FixedClock(),
    )


def _rendered(records: Iterable[logging.LogRecord]) -> str:
    """Everything a handler could conceivably emit from each record."""
    return "\n".join(
        f"{record.name} {record.levelname} {record.msg!r} {record.args!r} "
        f"{record.getMessage()} {record.exc_text or ''}"
        for record in records
    )


@pytest.mark.unit
def test_a_successful_run_logs_no_sentinel_token(caplog: pytest.LogCaptureFixture) -> None:
    """AC-003-20: the sentinel travels through the whole use case and is
    still never logged."""
    caplog.set_level(logging.DEBUG)
    analyzer = _StubAnalyzer(
        produce=lambda tokens: [
            LinguisticAnnotation(pos="NOUN", lemma=t, pos_confidence=None, lemma_confidence=None)
            for t in tokens
        ]
    )
    use_case = _use_case(tokens_by_book={1: [(10, _SENTINEL)]}, analyzers={"en": analyzer})

    use_case.execute(1, language="en")

    assert _SENTINEL not in _rendered(caplog.records)


@pytest.mark.unit
def test_an_unknown_import_logs_the_code_and_the_import_id(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    use_case = _use_case(tokens_by_book={}, analyzers={})

    with pytest.raises(ImportNotFoundError):
        use_case.execute(404, language="en")

    messages = [record.getMessage() for record in caplog.records]
    assert any(f"code={ImportNotFoundError.code}" in message for message in messages)
    assert any("import_id=404" in message for message in messages)


@pytest.mark.unit
def test_an_unsupported_language_logs_the_code_and_the_import_id_not_the_language(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    use_case = _use_case(tokens_by_book={1: [(10, _SENTINEL)]}, analyzers={})

    with pytest.raises(UnsupportedLanguageError):
        use_case.execute(1, language="de")

    messages = [record.getMessage() for record in caplog.records]
    assert any(f"code={UnsupportedLanguageError.code}" in message for message in messages)
    assert any("import_id=1" in message for message in messages)
    assert _SENTINEL not in _rendered(caplog.records)


@pytest.mark.unit
def test_a_non_upos_tag_failure_logs_the_code_the_import_id_and_the_position(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-003-20: the failure IS attributable to one token, so its position
    is logged — its TEXT (the sentinel) never is."""
    caplog.set_level(logging.DEBUG)
    analyzer = _StubAnalyzer(
        produce=lambda tokens: [
            LinguisticAnnotation(
                pos="NOUN", lemma="ok", pos_confidence=None, lemma_confidence=None
            ),
            LinguisticAnnotation(
                pos="NN", lemma=_SENTINEL, pos_confidence=None, lemma_confidence=None
            ),
        ]
    )
    use_case = _use_case(
        tokens_by_book={1: [(10, "ok"), (11, _SENTINEL)]}, analyzers={"en": analyzer}
    )

    with pytest.raises(AnnotationFailedError):
        use_case.execute(1, language="en")

    messages = [record.getMessage() for record in caplog.records]
    assert any(f"code={AnnotationFailedError.code}" in message for message in messages)
    assert any("import_id=1" in message for message in messages)
    assert any("position=1" in message for message in messages)
    assert _SENTINEL not in _rendered(caplog.records)


@pytest.mark.unit
def test_a_length_mismatch_failure_logs_no_position_since_none_is_attributable(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-003-20's "where applicable" qualifier: a length mismatch is not
    attributable to any single token, so the placeholder is logged, never a
    fabricated index."""
    caplog.set_level(logging.DEBUG)
    analyzer = _StubAnalyzer(produce=lambda tokens: [])
    use_case = _use_case(tokens_by_book={1: [(10, _SENTINEL)]}, analyzers={"en": analyzer})

    with pytest.raises(AnnotationFailedError):
        use_case.execute(1, language="en")

    messages = [record.getMessage() for record in caplog.records]
    assert any("position=-" in message for message in messages)


@pytest.mark.unit
def test_a_crash_mid_analysis_logs_no_traceback(caplog: pytest.LogCaptureFixture) -> None:
    """`logger.exception()` would render the crash's own `__str__`, which
    could embed anything the stub chose to raise — never used here."""
    caplog.set_level(logging.DEBUG)

    def _boom(tokens: Sequence[str]) -> Sequence[LinguisticAnnotation]:
        del tokens
        raise RuntimeError(_SENTINEL)

    analyzer = _StubAnalyzer(produce=_boom)
    use_case = _use_case(tokens_by_book={1: [(10, "x")]}, analyzers={"en": analyzer})

    with pytest.raises(AnnotationFailedError):
        use_case.execute(1, language="en")

    assert caplog.records
    assert all(record.exc_info is None for record in caplog.records)
    assert _SENTINEL not in _rendered(caplog.records)

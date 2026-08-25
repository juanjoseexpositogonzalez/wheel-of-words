"""Hypothesis properties for `AnnotateImport` — REQ-003-020, REQ-003-021.

Tasks 4.11 and 4.12. Both properties run against the REAL Phase 3
repositories (`SqlAlchemyAnnotationReadRepository`,
`SqlAlchemyAnnotationWriteRepository`) over a real SQLite database, through
the `annotation_session_factory` fixture — the same pattern
`test_annotation_read_repository.py`'s own Hypothesis property test already
established. The analyzer is a deterministic stdlib fake: real spaCy would
make these properties depend on the model's own behaviour, when what is
under test here is `AnnotateImport`'s and the repositories' independence
from batching, read order and inter-import order — properties that hold for
ANY analyzer, not a claim about spaCy specifically.

**Two invariants this file deliberately does NOT assert (§5 AMB-1, AMB-3):**

1. Naive lemma-of-lemma idempotence ("lemmatizing a lemma returns that
   lemma") — false for a contextual tagger; `REQ-003-020` scopes the real
   invariant to stability under RE-RUN with a pinned model, not to any
   claim about a lemma's own repeated annotation.
2. Token-permutation invariance — POS and lemma are contextual (ADR-0006),
   so permuting a document's tokens legitimately changes them.
   `REQ-003-021` scopes order-independence to batch size, read order, write
   order and inter-import order — never token order.

REQ-003-020, REQ-003-021, AC-003-21, AC-003-22.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import select

from wheel_vocabulary.application.annotation.errors import AnnotationFailedError
from wheel_vocabulary.application.annotation.ports import AnalyzerIdentity
from wheel_vocabulary.application.annotation.ports import LinguisticAnalyzer as _AnalyzerPort
from wheel_vocabulary.application.annotation.use_cases import AnnotateImport
from wheel_vocabulary.domain.annotation import UPOS_TAGS, LinguisticAnnotation
from wheel_vocabulary.infrastructure.persistence.annotation_repository import (
    AnnotatedOccurrence,
    SqlAlchemyAnnotationReadRepository,
)
from wheel_vocabulary.infrastructure.persistence.annotation_write_repository import (
    OccurrenceAnnotation,
    SqlAlchemyAnnotationWriteRepository,
)
from wheel_vocabulary.infrastructure.persistence.models import Book, Occurrence

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.orm import Session, sessionmaker

_UPOS_LIST = sorted(UPOS_TAGS)
_IDENTITY = AnalyzerIdentity(source="fake", model_name="fake-model", model_version="1.0")
_FIRST_RUN = datetime(2026, 8, 24, 12, 0, 0, tzinfo=UTC)
_SECOND_RUN = datetime(2026, 8, 24, 13, 0, 0, tzinfo=UTC)

_token_lists = st.lists(
    st.text(alphabet=st.characters(categories=["Ll"]), min_size=1, max_size=8),
    min_size=1,
    max_size=6,
)


def _deterministic_annotation(token: str) -> LinguisticAnnotation:
    """A pure function of the token TEXT alone — never its position or its
    neighbours. This is what makes the properties below meaningful: any
    difference in the recorded mapping can only come from `AnnotateImport`
    or the repositories mis-handling order/batching, never from the
    analyzer being contextual."""
    index = sum(ord(character) for character in token) % len(_UPOS_LIST)
    return LinguisticAnnotation(
        raw_text=token,
        pos=_UPOS_LIST[index],
        lemma=token,
        pos_confidence=None,
        lemma_confidence=None,
    )


class _DeterministicAnalyzer:
    identity = _IDENTITY

    def analyze(self, tokens: Sequence[str], *, language: str) -> Sequence[LinguisticAnnotation]:
        del language
        return [_deterministic_annotation(token) for token in tokens]


class _RotatingScramblingAnalyzer:
    """A deliberately non-conforming analyzer — C6 regression fixture.

    Computes the exact same correct `LinguisticAnnotation` per token as
    `_DeterministicAnalyzer`, then returns them ROTATED by one position
    relative to the input it received: index 0 of the result is what index 1
    of the input asked for, and so on. Same length as the input, so the
    length check alone cannot catch it — this simulates precisely the C6
    defect class: an analyzer violating its own "same order" port contract
    (`ports.py::LinguisticAnalyzer.analyze`).
    """

    identity = _IDENTITY

    def analyze(self, tokens: Sequence[str], *, language: str) -> Sequence[LinguisticAnnotation]:
        del language
        correct = [_deterministic_annotation(token) for token in tokens]
        return correct[1:] + correct[:1]


class _FakeRegistry:
    def __init__(self, analyzer: _AnalyzerPort) -> None:
        self._analyzer = analyzer

    def resolve(self, language: str) -> _AnalyzerPort:
        del language
        return self._analyzer


class _SequentialClock:
    def __init__(self, times: Sequence[datetime]) -> None:
        self._times = iter(times)

    def now_utc(self) -> datetime:
        return next(self._times)


class _ReversingReader:
    """Wraps a real `AnnotationReader`, returning its rows in REVERSE order.

    Proves READ-order independence: reversing which order the reader hands
    `AnnotateImport` its occurrences must not scramble the final mapping.

    **What this does NOT prove (C6).** `AnnotateImport` builds `raw_texts`
    directly from whatever `tokens` this reader returns, then feeds that
    exact sequence to the analyzer — `_DeterministicAnalyzer` computes each
    annotation purely from token content, so its output is reversed in
    lockstep with `tokens` no matter what order they arrive in. A PURELY
    POSITIONAL `zip(tokens, annotations)` therefore pairs correctly here
    every time, by construction, regardless of whether the implementation
    actually checks identity — this property alone cannot distinguish a
    correct implementation from a buggy one that trusts position blindly.
    `test_property_a_scrambled_analyzer_output_fails_annotation_failed_and_
    writes_nothing` (below) closes that gap with `_RotatingScramblingAnalyzer`,
    which reorders its OUTPUT independently of its input order — the one
    case a positional implementation cannot get right by accident.
    """

    def __init__(self, real_reader: SqlAlchemyAnnotationReadRepository) -> None:
        self._real_reader = real_reader

    def read(self, book_id: int) -> list[AnnotatedOccurrence] | None:
        rows = self._real_reader.read(book_id)
        if rows is None:
            return None
        return list(reversed(rows))


def _seed_book(session_factory: sessionmaker[Session], *, tokens: list[str]) -> int:
    with session_factory() as session:
        book = Book(
            content_hash="0" * 64,
            import_status="succeeded",
            token_count=len(tokens),
            created_at=_FIRST_RUN,
        )
        session.add(book)
        session.flush()
        session.add_all(
            Occurrence(book_id=book.id, raw_text=token, normalized_text=token, position=position)
            for position, token in enumerate(tokens)
        )
        session.commit()
        return book.id


def _mapping(
    read_repository: SqlAlchemyAnnotationReadRepository, book_id: int
) -> dict[int, tuple[str | None, str | None]]:
    rows = read_repository.read(book_id)
    assert rows is not None
    return {row.position: (row.effective_pos, row.lemma) for row in rows}


def _seed_book_with_distinct_normalized(
    session_factory: sessionmaker[Session], *, tokens: list[str]
) -> int:
    """Like `_seed_book`, but `normalized_text` is deliberately DIFFERENT
    from `raw_text` for every row (`f"{token}_norm"`), so the property below
    can prove `normalized_text` specifically survives an annotation run
    untouched — not merely that it happens to equal `raw_text` and a bug
    that mixed the two columns up would go unnoticed. `AnnotatedOccurrence`
    (the read model) never surfaces `normalized_text` at all (design §P3),
    so the read-back below queries `Occurrence` directly instead of going
    through `SqlAlchemyAnnotationReadRepository`.
    """
    with session_factory() as session:
        book = Book(
            content_hash="0" * 64,
            import_status="succeeded",
            token_count=len(tokens),
            created_at=_FIRST_RUN,
        )
        session.add(book)
        session.flush()
        session.add_all(
            Occurrence(
                book_id=book.id,
                raw_text=token,
                normalized_text=f"{token}_norm",
                position=position,
            )
            for position, token in enumerate(tokens)
        )
        session.commit()
        return book.id


def _occurrence_snapshot(
    session_factory: sessionmaker[Session], book_id: int
) -> dict[int, tuple[str, str, int]]:
    """`(raw_text, normalized_text, position)` per occurrence id — the exact
    three fields spec hook H10 requires annotation never mutate."""
    with session_factory() as session:
        rows = session.execute(
            select(
                Occurrence.id, Occurrence.raw_text, Occurrence.normalized_text, Occurrence.position
            ).where(Occurrence.book_id == book_id)
        ).all()
    return {row.id: (row.raw_text, row.normalized_text, row.position) for row in rows}


# --------------------------------------------------------------------------
# Task 4.11 — stability under re-run with a pinned model (AC-003-21).
# --------------------------------------------------------------------------


@pytest.mark.integration
@settings(
    max_examples=15, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(tokens=_token_lists)
def test_property_two_runs_produce_identical_pos_and_lemma_only_processed_at_differs(
    annotation_session_factory: sessionmaker[Session], tokens: list[str]
) -> None:
    """AC-003-21: re-running annotation over an unchanged import with a
    pinned model changes nothing but `processed_at`. Each example seeds its
    own book so examples never interfere on the shared fixture database."""
    book_id = _seed_book(annotation_session_factory, tokens=tokens)
    read_repository = SqlAlchemyAnnotationReadRepository(annotation_session_factory)
    write_repository = SqlAlchemyAnnotationWriteRepository(annotation_session_factory)
    registry = _FakeRegistry(_DeterministicAnalyzer())
    use_case = AnnotateImport(
        reader=read_repository,
        registry=registry,
        writer=write_repository,
        clock=_SequentialClock([_FIRST_RUN, _SECOND_RUN]),
    )

    use_case.execute(book_id, language="en")
    first_mapping = _mapping(read_repository, book_id)
    first_processed_at = {row.position: row.processed_at for row in read_repository.read(book_id)}  # type: ignore[union-attr]

    use_case.execute(book_id, language="en")
    second_mapping = _mapping(read_repository, book_id)
    second_processed_at = {row.position: row.processed_at for row in read_repository.read(book_id)}  # type: ignore[union-attr]

    assert first_mapping == second_mapping
    assert set(second_processed_at.values()) == {_SECOND_RUN.replace(tzinfo=None)}
    assert first_processed_at != second_processed_at


# --------------------------------------------------------------------------
# Task 4.12 — batch size / read order / cross-import independence (AC-003-22).
# --------------------------------------------------------------------------


@pytest.mark.integration
@settings(
    max_examples=15, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(tokens=_token_lists)
def test_property_reversing_the_reader_row_order_does_not_change_the_mapping(
    annotation_session_factory: sessionmaker[Session], tokens: list[str]
) -> None:
    """AC-003-22 scenario 1 (read order reversed). Two freshly seeded books
    with the SAME token content at the SAME positions; one is annotated
    through the real position-ordered reader, the other through a reader
    that hands `AnnotateImport` the same rows in reverse. Read back through
    the real (always position-ordered) reader afterwards, both must produce
    an identical `position -> (pos, lemma)` mapping."""
    forward_book_id = _seed_book(annotation_session_factory, tokens=tokens)
    reversed_book_id = _seed_book(annotation_session_factory, tokens=tokens)
    read_repository = SqlAlchemyAnnotationReadRepository(annotation_session_factory)
    write_repository = SqlAlchemyAnnotationWriteRepository(annotation_session_factory)
    registry = _FakeRegistry(_DeterministicAnalyzer())

    AnnotateImport(
        reader=read_repository,
        registry=registry,
        writer=write_repository,
        clock=_SequentialClock([_FIRST_RUN]),
    ).execute(forward_book_id, language="en")

    AnnotateImport(
        reader=_ReversingReader(read_repository),
        registry=registry,
        writer=write_repository,
        clock=_SequentialClock([_FIRST_RUN]),
    ).execute(reversed_book_id, language="en")

    assert _mapping(read_repository, forward_book_id) == _mapping(read_repository, reversed_book_id)


# --------------------------------------------------------------------------
# C6 remediation — the property `_ReversingReader` above cannot exercise.
# --------------------------------------------------------------------------

_distinct_token_lists = st.lists(
    st.text(alphabet=st.characters(categories=["Ll"]), min_size=1, max_size=8),
    min_size=2,
    max_size=6,
    unique=True,
)


@pytest.mark.integration
@settings(
    max_examples=15, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(tokens=_distinct_token_lists)
def test_property_a_scrambled_analyzer_output_fails_annotation_failed_and_writes_nothing(
    annotation_session_factory: sessionmaker[Session], tokens: list[str]
) -> None:
    """C6: for ANY generated token sequence of at least two DISTINCT tokens,
    an analyzer that returns a same-length but rotated result
    (`_RotatingScramblingAnalyzer`) must make the whole run fail with
    `ANNOTATION_FAILED` and write nothing — never silently persist pos/lemma
    values under the wrong occurrence. Tokens are constrained `unique=True`
    so the rotation is always content-detectable: with a repeated token the
    rotated output could coincide with the correct one by chance.

    RED (before the fix): raised `TypeError: LinguisticAnnotation.__init__()
    got an unexpected keyword argument 'raw_text'` — there was no field to
    carry identity through `_RotatingScramblingAnalyzer` at all, which is
    itself the shape of the defect: nothing could verify a same-length
    reordering.
    """
    book_id = _seed_book(annotation_session_factory, tokens=tokens)
    read_repository = SqlAlchemyAnnotationReadRepository(annotation_session_factory)
    write_repository = SqlAlchemyAnnotationWriteRepository(annotation_session_factory)
    registry = _FakeRegistry(_RotatingScramblingAnalyzer())
    use_case = AnnotateImport(
        reader=read_repository,
        registry=registry,
        writer=write_repository,
        clock=_SequentialClock([_FIRST_RUN]),
    )

    with pytest.raises(AnnotationFailedError):
        use_case.execute(book_id, language="en")

    rows = read_repository.read(book_id)
    assert rows is not None
    assert all(row.effective_pos is None for row in rows), "a failed run must write nothing"
    assert all(row.pos_origin == "automatic" for row in rows)


@pytest.mark.integration
@settings(
    max_examples=15, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(tokens=_token_lists)
def test_property_splitting_the_write_into_two_batches_does_not_change_the_mapping(
    annotation_session_factory: sessionmaker[Session], tokens: list[str]
) -> None:
    """AC-003-22 scenario 1 (batch size). REQ-003-021 forbids chunking the
    ANALYZER call, so batching can only ever apply to the write repository's
    own chunking (design §P5's trap) — re-verified directly against it here,
    per §5 AMB-3's "re-verified" instruction. One book is written in a
    single `write()` call; an identically seeded second book is written in
    two half-sized calls. Both must read back identically."""
    single_batch_book_id = _seed_book(annotation_session_factory, tokens=tokens)
    two_batch_book_id = _seed_book(annotation_session_factory, tokens=tokens)
    read_repository = SqlAlchemyAnnotationReadRepository(annotation_session_factory)
    write_repository = SqlAlchemyAnnotationWriteRepository(annotation_session_factory)
    annotations = [_deterministic_annotation(token) for token in tokens]

    def _record_for(
        book_id: int, occurrence_id: int, annotation: LinguisticAnnotation
    ) -> OccurrenceAnnotation:
        del book_id
        return OccurrenceAnnotation(
            occurrence_id=occurrence_id,
            pos=annotation.pos,
            lemma=annotation.lemma,
            pos_confidence=annotation.pos_confidence,
            lemma_confidence=annotation.lemma_confidence,
        )

    single_batch_rows = read_repository.read(single_batch_book_id)
    two_batch_rows = read_repository.read(two_batch_book_id)
    assert single_batch_rows is not None
    assert two_batch_rows is not None

    single_records = [
        _record_for(single_batch_book_id, row.occurrence_id, annotation)
        for row, annotation in zip(single_batch_rows, annotations, strict=True)
    ]
    write_repository.write(
        annotations=single_records, identity=_IDENTITY, language="en", processed_at=_FIRST_RUN
    )

    two_batch_records = [
        _record_for(two_batch_book_id, row.occurrence_id, annotation)
        for row, annotation in zip(two_batch_rows, annotations, strict=True)
    ]
    midpoint = len(two_batch_records) // 2 or len(two_batch_records)
    write_repository.write(
        annotations=two_batch_records[:midpoint],
        identity=_IDENTITY,
        language="en",
        processed_at=_FIRST_RUN,
    )
    write_repository.write(
        annotations=two_batch_records[midpoint:],
        identity=_IDENTITY,
        language="en",
        processed_at=_FIRST_RUN,
    )

    assert _mapping(read_repository, single_batch_book_id) == _mapping(
        read_repository, two_batch_book_id
    )


@pytest.mark.integration
@settings(
    max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(tokens_a=_token_lists, tokens_b=_token_lists)
def test_property_annotating_two_imports_in_either_order_does_not_cross_contaminate(
    annotation_session_factory: sessionmaker[Session], tokens_a: list[str], tokens_b: list[str]
) -> None:
    """AC-003-22 scenario 2: each import's mapping is unaffected by the
    other. Book A/B are annotated A-then-B; a freshly seeded A2/B2 pair with
    the SAME content is annotated B2-then-A2. A's mapping must equal A2's,
    and B's must equal B2's, regardless of order."""
    book_a = _seed_book(annotation_session_factory, tokens=tokens_a)
    book_b = _seed_book(annotation_session_factory, tokens=tokens_b)
    book_a2 = _seed_book(annotation_session_factory, tokens=tokens_a)
    book_b2 = _seed_book(annotation_session_factory, tokens=tokens_b)
    read_repository = SqlAlchemyAnnotationReadRepository(annotation_session_factory)
    write_repository = SqlAlchemyAnnotationWriteRepository(annotation_session_factory)
    registry = _FakeRegistry(_DeterministicAnalyzer())

    def _annotate(book_id: int) -> None:
        AnnotateImport(
            reader=read_repository,
            registry=registry,
            writer=write_repository,
            clock=_SequentialClock([_FIRST_RUN]),
        ).execute(book_id, language="en")

    _annotate(book_a)
    _annotate(book_b)
    _annotate(book_b2)
    _annotate(book_a2)

    assert _mapping(read_repository, book_a) == _mapping(read_repository, book_a2)
    assert _mapping(read_repository, book_b) == _mapping(read_repository, book_b2)


# --------------------------------------------------------------------------
# Remediation — spec hook H10's missing property (verify-report CRITICAL-4).
#
# H10 enumerates five Hypothesis properties that must exist; this file
# shipped only four. This is the fifth: "annotation never mutates
# raw_text/normalized_text/position". `SqlAlchemyAnnotationWriteRepository.
# _update_occurrences` sets only `pos`/`lemma` by construction today, so the
# guarantee held BY ACCIDENT of the current implementation — nothing failed
# a test if a future edit widened that UPDATE. This property closes that gap
# directly, at the `AnnotateImport` boundary (AC-003-14 scenario 2).
# --------------------------------------------------------------------------


@pytest.mark.integration
@settings(
    max_examples=15, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(tokens=_token_lists)
def test_property_annotation_never_mutates_raw_text_normalized_text_or_position(
    annotation_session_factory: sessionmaker[Session], tokens: list[str]
) -> None:
    """AC-003-14 scenario 2 / spec hook H10: for ANY generated token
    sequence, `raw_text`, `normalized_text` and `position` are byte-identical
    before and after a real `AnnotateImport.execute()` run. Each example
    seeds its own book with a `normalized_text` deliberately distinct from
    `raw_text`, so this proves both columns individually, not just one
    standing in for the other.

    MUTATION CHECK — this is an absence-style property; it passes on its
    first run over correct code, which proves nothing on its own. Verified
    by temporarily adding `raw_text="MUTATION_CHECK"` to `_update_occurrences`'s
    `UPDATE` values in `annotation_write_repository.py`, running this test,
    and observing Hypothesis shrink to the minimal failing example::

        AssertionError: assert {383: ('MUTATION_CHECK', 'a_norm', 0)} == {383: ('a', 'a_norm', 0)}
        Falsifying example: ...(tokens=['a'])

    then reverting and confirming green again.
    """
    book_id = _seed_book_with_distinct_normalized(annotation_session_factory, tokens=tokens)
    before = _occurrence_snapshot(annotation_session_factory, book_id)
    read_repository = SqlAlchemyAnnotationReadRepository(annotation_session_factory)
    write_repository = SqlAlchemyAnnotationWriteRepository(annotation_session_factory)
    registry = _FakeRegistry(_DeterministicAnalyzer())

    AnnotateImport(
        reader=read_repository,
        registry=registry,
        writer=write_repository,
        clock=_SequentialClock([_FIRST_RUN]),
    ).execute(book_id, language="en")

    after = _occurrence_snapshot(annotation_session_factory, book_id)
    assert after == before

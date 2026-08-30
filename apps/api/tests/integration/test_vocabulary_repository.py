"""Repository integration coverage for the vocabulary aggregate read."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from wheel_vocabulary.infrastructure.persistence.base import Base
from wheel_vocabulary.infrastructure.persistence.engine import (
    create_engine_from_url,
    create_session_factory,
)
from wheel_vocabulary.infrastructure.persistence.models import Book, ManualCorrection, Occurrence
from wheel_vocabulary.infrastructure.persistence.vocabulary_repository import (
    SqlAlchemyVocabularyReadRepository,
    VocabularyGroup,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.orm import Session, sessionmaker


_NOW = datetime(2026, 8, 30, 12, 0, 0, tzinfo=UTC)
_Pair = tuple[str | None, str | None]


@pytest.fixture
def session_factory(tmp_path):  # noqa: ANN001, ANN201
    engine = create_engine_from_url(f"sqlite:///{tmp_path / 'vocabulary_repository.db'}")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    yield factory
    engine.dispose()


def _seed_book(
    session_factory: sessionmaker[Session], pairs: Sequence[_Pair]
) -> tuple[int, list[int]]:
    with session_factory() as session:
        book = Book(
            content_hash="0" * 64,
            import_status="succeeded",
            token_count=len(pairs),
            created_at=_NOW,
        )
        session.add(book)
        session.flush()
        occurrences = [
            Occurrence(
                book_id=book.id,
                raw_text=f"token-{position}",
                normalized_text=f"token-{position}",
                position=position,
                lemma=lemma,
                pos=pos,
            )
            for position, (lemma, pos) in enumerate(pairs)
        ]
        session.add_all(occurrences)
        session.flush()
        session.commit()
        return book.id, [occurrence.id for occurrence in occurrences]


def _repository(session_factory: sessionmaker[Session]) -> SqlAlchemyVocabularyReadRepository:
    return SqlAlchemyVocabularyReadRepository(session_factory)


@pytest.mark.integration
def test_homograph_is_returned_as_two_pos_groups_with_occurrence_counts(
    session_factory: sessionmaker[Session],
) -> None:
    """AC-005-01: a lemma occurring under two tags remains two study units."""
    book_id, _ = _seed_book(session_factory, [("run", "VERB"), ("run", "VERB"), ("run", "NOUN")])

    groups = _repository(session_factory).groups(book_id)

    assert groups == [
        VocabularyGroup(lemma="run", pos="VERB", occurrence_count=2),
        VocabularyGroup(lemma="run", pos="NOUN", occurrence_count=1),
    ]


@pytest.mark.integration
def test_corrections_move_groups_vacate_raw_group_and_resolve_each_field(
    session_factory: sessionmaker[Session],
) -> None:
    """AC-005-02: direct ORM corrections win without a correction writer."""
    book_id, occurrence_ids = _seed_book(session_factory, [("saw", "NOUN"), ("walked", "VERB")])
    with session_factory() as session:
        session.add_all(
            [
                ManualCorrection(
                    occurrence_id=occurrence_ids[0],
                    field="lemma",
                    corrected_value="see",
                    corrected_at=_NOW,
                ),
                ManualCorrection(
                    occurrence_id=occurrence_ids[0],
                    field="pos",
                    corrected_value="VERB",
                    corrected_at=_NOW,
                ),
                ManualCorrection(
                    occurrence_id=occurrence_ids[1],
                    field="lemma",
                    corrected_value="walk",
                    corrected_at=_NOW,
                ),
            ]
        )
        session.commit()

    groups = _repository(session_factory).groups(book_id)

    assert groups == [
        VocabularyGroup(lemma="see", pos="VERB", occurrence_count=1),
        VocabularyGroup(lemma="walk", pos="VERB", occurrence_count=1),
    ]
    assert VocabularyGroup(lemma="saw", pos="NOUN", occurrence_count=1) not in groups


@pytest.mark.integration
def test_unannotated_and_missing_pos_occurrences_remain_visible_buckets(
    session_factory: sessionmaker[Session],
) -> None:
    """AC-005-03: absent key halves stay as actual ``None`` values."""
    unannotated_id, _ = _seed_book(session_factory, [(None, None), (None, None), (None, None)])
    missing_pos_id, _ = _seed_book(session_factory, [("correr", None)])

    unannotated_groups = _repository(session_factory).groups(unannotated_id)
    missing_pos_groups = _repository(session_factory).groups(missing_pos_id)

    assert unannotated_groups == [VocabularyGroup(lemma=None, pos=None, occurrence_count=3)]
    assert missing_pos_groups == [VocabularyGroup(lemma="correr", pos=None, occurrence_count=1)]


@pytest.mark.integration
def test_unknown_book_and_existing_empty_book_are_distinct_states(
    session_factory: sessionmaker[Session],
) -> None:
    """AC-005-05: aggregate emptiness never stands in for existence."""
    empty_book_id, _ = _seed_book(session_factory, [])
    repository = _repository(session_factory)

    assert repository.groups(999_999) is None
    assert repository.groups(empty_book_id) == []


@pytest.mark.integration
def test_groups_follow_literal_design_order_and_are_stable_between_reads(
    session_factory: sessionmaker[Session],
) -> None:
    """AC-005-01/D5: count desc, then NULL-first lemma/POS ties, is stable.

    This positional literal rejects a stable but wrong insertion or ascending-count order.
    """
    pairs = [
        ("zeta", "NOUN"),
        ("zeta", "NOUN"),
        ("zeta", "NOUN"),
        (None, None),
        (None, None),
        (None, "VERB"),
        (None, "VERB"),
        ("alpha", None),
        ("alpha", None),
        ("alpha", "NOUN"),
        ("alpha", "NOUN"),
        ("beta", None),
        ("beta", None),
    ]
    book_id, _ = _seed_book(session_factory, pairs)
    repository = _repository(session_factory)
    expected = [
        VocabularyGroup(lemma="zeta", pos="NOUN", occurrence_count=3),
        VocabularyGroup(lemma=None, pos=None, occurrence_count=2),
        VocabularyGroup(lemma=None, pos="VERB", occurrence_count=2),
        VocabularyGroup(lemma="alpha", pos=None, occurrence_count=2),
        VocabularyGroup(lemma="alpha", pos="NOUN", occurrence_count=2),
        VocabularyGroup(lemma="beta", pos=None, occurrence_count=2),
    ]

    first_read = repository.groups(book_id)
    second_read = repository.groups(book_id)

    assert first_read == expected
    assert second_read == expected
    assert second_read == first_read

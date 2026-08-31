"""Snapshot-isolation regression coverage for the vocabulary aggregate read."""

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
    from collections.abc import Callable

    from sqlalchemy.orm import Session, sessionmaker


_NOW = datetime(2026, 8, 31, 12, 0, 0, tzinfo=UTC)


class _InterleavingVocabularyReadRepository(SqlAlchemyVocabularyReadRepository):
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        after_raw_counts: Callable[[], None],
    ) -> None:
        super().__init__(session_factory)
        self._after_raw_counts = after_raw_counts

    def _raw_group_counts(
        self, session: Session, book_id: int
    ) -> dict[tuple[str | None, str | None], int]:
        counts = super()._raw_group_counts(session, book_id)
        self._after_raw_counts()
        return counts


@pytest.fixture
def session_factory(tmp_path):  # noqa: ANN001, ANN201
    engine = create_engine_from_url(f"sqlite:///{tmp_path / 'vocabulary_snapshot.db'}")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    yield factory
    engine.dispose()


def _seed_corrected_book(session_factory: sessionmaker[Session]) -> tuple[int, int, int]:
    with session_factory() as session:
        book = Book(
            content_hash="0" * 64,
            import_status="succeeded",
            token_count=2,
            created_at=_NOW,
        )
        unrelated_book = Book(
            content_hash="1" * 64,
            import_status="succeeded",
            token_count=1,
            created_at=_NOW,
        )
        session.add_all([book, unrelated_book])
        session.flush()
        first = Occurrence(
            book_id=book.id,
            raw_text="alpha-token",
            normalized_text="alpha-token",
            position=0,
            lemma="alpha",
            pos="NOUN",
        )
        corrected = Occurrence(
            book_id=book.id,
            raw_text="beta-token",
            normalized_text="beta-token",
            position=1,
            lemma="beta",
            pos="NOUN",
        )
        unrelated = Occurrence(
            book_id=unrelated_book.id,
            raw_text="unrelated-token",
            normalized_text="unrelated-token",
            position=0,
            lemma="unrelated",
            pos="NOUN",
        )
        session.add_all([first, corrected, unrelated])
        session.flush()
        session.add(
            ManualCorrection(
                occurrence_id=corrected.id,
                field="lemma",
                corrected_value="gamma",
                corrected_at=_NOW,
            )
        )
        session.commit()
        return book.id, corrected.id, unrelated.id


@pytest.mark.integration
def test_groups_observes_one_snapshot_while_an_unrelated_writer_commits(
    session_factory: sessionmaker[Session],
) -> None:
    """WU2b: leg A and leg B share one snapshot, while a writer commits.

    Without an explicit read transaction, leg A sees raw ``beta`` while leg B sees
    the committed raw ``delta`` for the same corrected occurrence. The merge then
    returns the impossible ``beta`` group. The RED is therefore the returned group
    comparison, not a writer lock timeout.
    """
    book_id, corrected_occurrence_id, unrelated_occurrence_id = _seed_corrected_book(
        session_factory
    )

    def commit_interleaved_writes() -> None:
        with session_factory() as unrelated_writer:
            occurrence = unrelated_writer.get(Occurrence, unrelated_occurrence_id)
            assert occurrence is not None
            occurrence.lemma = "omega"
            unrelated_writer.commit()

        with session_factory() as writer:
            occurrence = writer.get(Occurrence, corrected_occurrence_id)
            assert occurrence is not None
            occurrence.lemma = "delta"
            writer.commit()

    repository = _InterleavingVocabularyReadRepository(session_factory, commit_interleaved_writes)

    groups = repository.groups(book_id)

    assert groups == [
        VocabularyGroup(lemma="alpha", pos="NOUN", occurrence_count=1),
        VocabularyGroup(lemma="gamma", pos="NOUN", occurrence_count=1),
    ]
    with session_factory() as session:
        committed = session.get(Occurrence, corrected_occurrence_id)
        unrelated_committed = session.get(Occurrence, unrelated_occurrence_id)
        assert committed is not None
        assert unrelated_committed is not None
        assert committed.lemma == "delta"
        assert unrelated_committed.lemma == "omega"

"""`Occurrence.pos` reserved and unpopulated; textual/normalized forms stay
distinct — design §6.1, ADR-0006 (T205).

REQ-002-010 / AC-002-14.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from wheel_vocabulary.infrastructure.persistence.models import Occurrence

if TYPE_CHECKING:
    from wheel_vocabulary.infrastructure.persistence.book_repository import (
        SqlAlchemyBookRepository,
    )

_NOW = datetime(2026, 8, 11, 12, 0, 0, tzinfo=UTC)


@pytest.mark.integration
def test_every_persisted_occurrence_has_pos_none(
    book_repository: SqlAlchemyBookRepository,
) -> None:
    """AC-002-14: no row written by this capability ever sets `pos`."""
    occurrences = [("uno", "uno", 0), ("dos", "dos", 1), ("dos", "dos", 2)]
    book_id = book_repository.create(
        content_hash="0" * 64, token_count=3, created_at=_NOW, occurrences=occurrences
    )

    with book_repository._session_factory() as session:  # noqa: SLF001 - test-only introspection
        rows = session.query(Occurrence).filter_by(book_id=book_id).all()

    assert rows
    assert all(row.pos is None for row in rows)


@pytest.mark.integration
def test_raw_text_and_normalized_text_stay_separate_values(
    book_repository: SqlAlchemyBookRepository,
) -> None:
    """AC-002-14: `Straße`/`strasse` must never collapse into one column value."""
    book_id = book_repository.create(
        content_hash="0" * 64,
        token_count=1,
        created_at=_NOW,
        occurrences=[("Stra\u00dfe", "strasse", 0)],
    )

    with book_repository._session_factory() as session:  # noqa: SLF001 - test-only introspection
        row = session.query(Occurrence).filter_by(book_id=book_id).one()

    assert row.raw_text == "Stra\u00dfe"
    assert row.normalized_text == "strasse"
    assert row.raw_text != row.normalized_text

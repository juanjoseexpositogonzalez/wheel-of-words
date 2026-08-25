"""SQLAlchemy implementation of the `BookRepository` port — design §7.3.

`create()` MUST use a batched Core `insert()` for the occurrence write, never
`Session.add_all()`: the ORM identity map and per-object instrumentation run
roughly 20x slower on this stage at the 4 MiB ceiling (design §3.3). The `Book`
row itself is a single object, so the ORM `Session.add()` is fine for it — the
prohibition is specific to the per-token occurrence write.

REQ-002-008, REQ-002-009, REQ-002-012.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import delete, func, insert, select

from wheel_vocabulary.infrastructure.persistence.models import (
    AnnotationProvenance,
    Book,
    ManualCorrection,
    Occurrence,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from sqlalchemy.orm import Session, sessionmaker

__all__ = ["SqlAlchemyBookRepository"]


class SqlAlchemyBookRepository:
    """Implements `application.imports.ports.BookRepository`."""

    _INSERT_BATCH = 10_000

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create(
        self,
        *,
        content_hash: str,
        token_count: int,
        created_at: datetime,
        occurrences: Sequence[tuple[str, str, int]],
    ) -> int:
        """Persist a `Book` row and one `Occurrence` row per emitted token.

        One transaction: the `Book` row is inserted first (its id is needed as
        the occurrence rows' foreign key), then the occurrences are written in
        batches of `_INSERT_BATCH` through a Core `insert()`.
        """
        with self._session_factory() as session:
            book = Book(
                content_hash=content_hash,
                import_status="succeeded",
                token_count=token_count,
                created_at=created_at,
            )
            session.add(book)
            session.flush()
            book_id = book.id
            self._insert_occurrences(session, book_id=book_id, occurrences=occurrences)
            session.commit()
            return book_id

    def _insert_occurrences(
        self,
        session: Session,
        *,
        book_id: int,
        occurrences: Sequence[tuple[str, str, int]],
    ) -> None:
        """Write every occurrence in fixed-size batches (design §3.3)."""
        for start in range(0, len(occurrences), self._INSERT_BATCH):
            batch = occurrences[start : start + self._INSERT_BATCH]
            session.execute(
                insert(Occurrence),
                [
                    {
                        "book_id": book_id,
                        "raw_text": raw_text,
                        "normalized_text": normalized_text,
                        "position": position,
                        "pos": None,
                    }
                    for raw_text, normalized_text, position in batch
                ],
            )

    def frequency_pairs(self, book_id: int) -> list[tuple[str, str, int]] | None:
        """Return `(raw_text, normalized_text, count)` triples, or `None`.

        `None` means the id is unknown (404). `[]` means the import exists and
        has zero occurrences (REQ-002-012's zero state). The two are never
        conflated: existence is checked with its own query, independent of
        whether the aggregation query below returns any row.
        """
        with self._session_factory() as session:
            if session.get(Book, book_id) is None:
                return None

            statement = (
                select(Occurrence.raw_text, Occurrence.normalized_text, func.count())
                .where(Occurrence.book_id == book_id)
                .group_by(Occurrence.raw_text, Occurrence.normalized_text)
            )
            return [
                (raw_text, normalized_text, count)
                for raw_text, normalized_text, count in session.execute(statement)
            ]

    def delete(self, book_id: int) -> bool:
        """Delete a `Book` and every row derived from it — design §6.2, S1.

        Existence is checked first with its own query, mirroring
        `frequency_pairs`'s unknown-vs-empty pattern above, so the `False`
        return does not depend on a driver-specific `rowcount` value. Once
        existence is confirmed, four explicit `DELETE` statements run in one
        transaction — `manual_correction`, `annotation_provenance`,
        `occurrence`, `book`, always in that order — never `ON DELETE
        CASCADE`: SQLite ships with `PRAGMA foreign_keys = OFF` by default,
        and this engine (`infrastructure/persistence/engine.py`) never turns
        it on, so the FK's declared cascade would silently do nothing.

        The two annotation child tables MUST be deleted alongside
        `occurrence`, not just `occurrence` and `book` alone (as an earlier
        revision of this method did): `Occurrence.id` is a plain SQLite
        ROWID, freed and eligible for reuse the moment its row is gone. A
        `manual_correction`/`annotation_provenance` row left behind, keyed
        to that now-reusable id, would silently attach to whatever LATER,
        unrelated import's occurrence happens to reuse it — a ghost
        correction the user never made on the new import at all.
        """
        with self._session_factory() as session:
            if session.get(Book, book_id) is None:
                return False

            occurrence_ids = select(Occurrence.id).where(Occurrence.book_id == book_id)
            session.execute(
                delete(ManualCorrection).where(ManualCorrection.occurrence_id.in_(occurrence_ids))
            )
            session.execute(
                delete(AnnotationProvenance).where(
                    AnnotationProvenance.occurrence_id.in_(occurrence_ids)
                )
            )
            session.execute(delete(Occurrence).where(Occurrence.book_id == book_id))
            session.execute(delete(Book).where(Book.id == book_id))
            session.commit()
            return True

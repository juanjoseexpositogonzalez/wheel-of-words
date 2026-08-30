"""`ReadVocabulary` forwards a grouped read to its persistence port."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Sequence

    from wheel_vocabulary.application.vocabulary.ports import VocabularyReader
    from wheel_vocabulary.infrastructure.persistence.vocabulary_repository import VocabularyGroup

__all__ = ["ReadVocabulary"]


class ReadVocabulary:
    """Read the pre-aggregated vocabulary groups for one import."""

    def __init__(self, *, repository: VocabularyReader) -> None:
        self._repository = repository

    def execute(self, book_id: int) -> Sequence[VocabularyGroup] | None:
        """Return grouped vocabulary, preserving the unknown-import result."""
        return self._repository.groups(book_id)

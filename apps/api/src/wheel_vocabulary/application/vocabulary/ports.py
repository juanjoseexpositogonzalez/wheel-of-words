"""Port for reading grouped vocabulary from one import."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Sequence

    from wheel_vocabulary.infrastructure.persistence.vocabulary_repository import VocabularyGroup

__all__ = ["VocabularyReader"]


@runtime_checkable
class VocabularyReader(Protocol):
    """Structural port for the grouped vocabulary read."""

    def groups(self, book_id: int) -> Sequence[VocabularyGroup] | None:
        """Return groups for an import, or ``None`` when it does not exist."""
        ...

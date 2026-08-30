"""Unit tests for the vocabulary application port and use case."""

from __future__ import annotations

from wheel_vocabulary.application.vocabulary.ports import VocabularyReader
from wheel_vocabulary.application.vocabulary.use_cases import ReadVocabulary
from wheel_vocabulary.infrastructure.persistence.vocabulary_repository import VocabularyGroup


class _FakeVocabularyReader:
    def __init__(self, result: list[VocabularyGroup] | None) -> None:
        self.result = result
        self.book_ids: list[int] = []

    def groups(self, book_id: int) -> list[VocabularyGroup] | None:
        self.book_ids.append(book_id)
        return self.result


def test_stdlib_double_satisfies_vocabulary_reader_structurally() -> None:
    reader = _FakeVocabularyReader([VocabularyGroup(lemma="run", pos="VERB", occurrence_count=2)])

    assert isinstance(reader, VocabularyReader)


def test_read_vocabulary_returns_the_repository_groups_unchanged() -> None:
    groups = [VocabularyGroup(lemma="run", pos="VERB", occurrence_count=2)]
    reader = _FakeVocabularyReader(groups)

    result = ReadVocabulary(repository=reader).execute(7)

    assert result is groups
    assert reader.book_ids == [7]


def test_read_vocabulary_preserves_the_unknown_book_result() -> None:
    reader = _FakeVocabularyReader(None)

    result = ReadVocabulary(repository=reader).execute(404)

    assert result is None
    assert reader.book_ids == [404]

"""Unit tests for vocabulary response DTO strictness."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from wheel_vocabulary.api.dtos.vocabulary import VocabularyGroupResponse, VocabularyResponse


def test_vocabulary_group_response_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError, match="extra_forbidden"):
        VocabularyGroupResponse(lemma="run", pos="VERB", occurrence_count=2, confidence=0.9)


def test_vocabulary_response_rejects_unknown_fields() -> None:
    group = VocabularyGroupResponse(lemma=None, pos=None, occurrence_count=3)

    with pytest.raises(ValidationError, match="extra_forbidden"):
        VocabularyResponse(
            id=1,
            group_count=1,
            total_occurrence_count=3,
            groups=[group],
            next_page="unused",
        )

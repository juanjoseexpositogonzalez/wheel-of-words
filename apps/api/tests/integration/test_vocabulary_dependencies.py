"""Integration tests for vocabulary dependency providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from wheel_vocabulary.api.dependencies import (
    get_read_vocabulary,
    get_vocabulary_repository,
)
from wheel_vocabulary.application.vocabulary.use_cases import ReadVocabulary
from wheel_vocabulary.infrastructure.persistence.base import Base
from wheel_vocabulary.infrastructure.persistence.engine import create_engine_from_url
from wheel_vocabulary.infrastructure.persistence.vocabulary_repository import (
    SqlAlchemyVocabularyReadRepository,
)
from wheel_vocabulary.infrastructure.settings import Settings

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.integration
def test_get_vocabulary_repository_builds_a_repository_from_settings(tmp_path: Path) -> None:
    settings = Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'vocabulary.db'}")

    repository = get_vocabulary_repository(settings)

    assert isinstance(repository, SqlAlchemyVocabularyReadRepository)


@pytest.mark.integration
def test_get_read_vocabulary_assembles_the_use_case_from_a_real_repository(tmp_path: Path) -> None:
    settings = Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'vocabulary.db'}")
    engine = create_engine_from_url(settings.database_url)
    Base.metadata.create_all(engine)
    repository = get_vocabulary_repository(settings)

    use_case = get_read_vocabulary(repository)

    assert isinstance(use_case, ReadVocabulary)
    assert use_case.execute(1) is None

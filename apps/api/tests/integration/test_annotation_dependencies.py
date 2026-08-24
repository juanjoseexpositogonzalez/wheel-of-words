"""Coverage/DoD completeness for the annotation dependency providers
(AGENTS.md §10) — task 5.10's coverage-gate check surfaced these as the only
uncovered lines in `api/dependencies.py`: `get_annotation_read_repository`,
`get_annotation_write_repository`, and `get_analyzer_registry` are never
called directly in `test_annotation_route.py` (every test there overrides
them via `app.dependency_overrides`), mirroring the exact gap
`test_book_repository.py::test_get_book_repository_builds_a_repository_
from_settings` already closes for `get_book_repository`.

REQ-003-003 (registry assembly), design §P3/P4.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from wheel_vocabulary.api.dependencies import (
    get_analyzer_registry,
    get_annotation_read_repository,
    get_annotation_write_repository,
)
from wheel_vocabulary.infrastructure.nlp.registry import AnalyzerRegistry
from wheel_vocabulary.infrastructure.persistence.annotation_repository import (
    SqlAlchemyAnnotationReadRepository,
)
from wheel_vocabulary.infrastructure.persistence.annotation_write_repository import (
    SqlAlchemyAnnotationWriteRepository,
)
from wheel_vocabulary.infrastructure.settings import Settings

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.integration
def test_get_annotation_read_repository_builds_a_repository_from_settings(
    tmp_path: Path,
) -> None:
    """The default read-side dependency provider, exercised directly."""
    settings = Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'read.db'}")

    repository = get_annotation_read_repository(settings)

    assert isinstance(repository, SqlAlchemyAnnotationReadRepository)


@pytest.mark.integration
def test_get_annotation_write_repository_builds_a_repository_from_settings(
    tmp_path: Path,
) -> None:
    """The default write-side dependency provider, exercised directly."""
    settings = Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / 'write.db'}")

    repository = get_annotation_write_repository(settings)

    assert isinstance(repository, SqlAlchemyAnnotationWriteRepository)


@pytest.mark.integration
def test_get_analyzer_registry_builds_a_registry_from_settings(tmp_path: Path) -> None:
    """The default registry provider, exercised directly — never loads a
    pipeline itself (design §P4: `resolve()` is lazy), so this stays fast."""
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'registry.db'}",
        analyzer_models={"en": "en_core_web_sm"},
    )

    registry = get_analyzer_registry(settings)

    assert isinstance(registry, AnalyzerRegistry)

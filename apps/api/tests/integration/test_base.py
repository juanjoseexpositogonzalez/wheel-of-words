"""Integration tests for the SQLAlchemy declarative base.

REQ-001-006, REQ-PFB-CONTRACT-002, design §6.5, TB203.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlalchemy import inspect

from wheel_vocabulary.infrastructure.persistence.base import Base
from wheel_vocabulary.infrastructure.persistence.engine import create_engine_from_url

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy import Engine


@pytest.mark.integration
def test_base_metadata_declares_exactly_the_shipped_capability_tables() -> None:
    """No speculative tables: every table on `Base` maps to a shipped migration.

    SPEC-001's baseline shipped no tables (`Base.metadata.tables == []`).
    SPEC-002 cut 2 (`0002_book_occurrence`) was the first capability to add
    mapped models; `lemmatization-pos` slice 3 (`0003_annotation`) added
    `annotation_provenance` and `manual_correction`.
    """
    assert set(Base.metadata.tables) == {
        "book",
        "occurrence",
        "annotation_provenance",
        "manual_correction",
    }


@pytest.mark.integration
def test_base_create_all_creates_exactly_the_mapped_tables(
    managed_engine: Callable[[Engine], Engine],
) -> None:
    """`create_all` on a fresh database creates exactly `Base`'s mapped tables.

    Pinned against the current mapped set rather than emptiness — see
    `test_base_metadata_declares_exactly_the_shipped_capability_tables`.
    """
    engine = managed_engine(create_engine_from_url("sqlite:///:memory:"))

    Base.metadata.create_all(engine)

    assert set(inspect(engine).get_table_names()) == {
        "book",
        "occurrence",
        "annotation_provenance",
        "manual_correction",
    }

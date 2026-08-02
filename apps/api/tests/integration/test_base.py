"""Integration tests for the SQLAlchemy declarative base.

REQ-001-006, REQ-PFB-CONTRACT-002, design §6.5, TB203.
"""

from __future__ import annotations

import pytest
from sqlalchemy import inspect

from wheel_vocabulary.infrastructure.persistence.base import Base
from wheel_vocabulary.infrastructure.persistence.engine import create_engine_from_url


@pytest.mark.integration
def test_base_metadata_starts_empty() -> None:
    """The baseline must not introduce speculative user/domain tables."""
    assert list(Base.metadata.tables) == []


@pytest.mark.integration
def test_base_create_all_creates_no_user_tables() -> None:
    """Creating metadata in SPEC-001 leaves the database with no user tables."""
    engine = create_engine_from_url("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    assert inspect(engine).get_table_names() == []

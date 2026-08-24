"""Alembic integration tests for revision 0002 — Book/Occurrence (T201).

AC-002-11, H3. `alembic upgrade 0002_book_occurrence` must create `book` and
`occurrence`; `alembic downgrade 0001_baseline` must remove both and return to
the empty-schema baseline.

Pinned against the named revision, not `head`/`-1`, since `lemmatization-pos`
slice 3 added `0003_annotation` on top: `head` now legitimately creates
`annotation_provenance`/`manual_correction` too, and `-1` from `head` lands on
`0002_book_occurrence` rather than `0001_baseline`. `test_alembic_0003.py`
covers the newer revision; this file stays scoped to exactly the one it names,
mirroring `test_alembic.py`'s existing pinning convention.

REQ-002-008.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import command
from sqlalchemy import create_engine, inspect, text

if TYPE_CHECKING:
    from collections.abc import Callable

    from alembic.config import Config
    from sqlalchemy import Engine


def test_upgrade_and_downgrade_book_occurrence(
    alembic_config: Config,
    managed_engine: Callable[[Engine], Engine],
) -> None:
    """AC-002-11: upgrade creates both tables; downgrade removes them cleanly."""
    command.upgrade(alembic_config, "0002_book_occurrence")

    engine = managed_engine(
        create_engine(alembic_config.get_main_option("sqlalchemy.url"), future=True)
    )
    inspector = inspect(engine)
    assert "book" in inspector.get_table_names()
    assert "occurrence" in inspector.get_table_names()

    command.downgrade(alembic_config, "0001_baseline")

    inspector = inspect(engine)
    assert "book" not in inspector.get_table_names()
    assert "occurrence" not in inspector.get_table_names()
    with engine.connect() as connection:
        version = connection.execute(text("select version_num from alembic_version")).scalar_one()
    assert version == "0001_baseline"


def test_upgrade_adds_no_display_form_column(
    alembic_config: Config,
    managed_engine: Callable[[Engine], Engine],
) -> None:
    """AC-002-24: no `display_form` column exists on `book` or `occurrence`."""
    command.upgrade(alembic_config, "0002_book_occurrence")

    engine = managed_engine(
        create_engine(alembic_config.get_main_option("sqlalchemy.url"), future=True)
    )
    inspector = inspect(engine)
    book_columns = {column["name"] for column in inspector.get_columns("book")}
    occurrence_columns = {column["name"] for column in inspector.get_columns("occurrence")}
    assert "display_form" not in book_columns
    assert "display_form" not in occurrence_columns

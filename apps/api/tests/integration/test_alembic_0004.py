"""Alembic integration tests for revision `0004_vocabulary_group_index` — design §Migration/Rollout.

`alembic upgrade head` must add a covering index `ix_occurrence_book_lemma_pos`
on `occurrence(book_id, lemma, pos)`; `alembic downgrade -1` must remove it and
return `alembic_version` to the `0003_annotation` baseline exactly — no column
or table this capability touches, additive only (design §Migration/Rollout).

REQ-005-009 / AC-005-09 scenario 3.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import command
from sqlalchemy import create_engine, text

if TYPE_CHECKING:
    from collections.abc import Callable

    from alembic.config import Config
    from sqlalchemy import Engine


def test_upgrade_adds_the_group_index_downgrade_removes_it(
    alembic_config: Config,
    managed_engine: Callable[[Engine], Engine],
) -> None:
    """AC-005-09 scenario 3: upgrade creates the index, downgrade removes it
    and returns `alembic_version` to `0003_annotation`."""
    command.upgrade(alembic_config, "head")

    engine = managed_engine(
        create_engine(alembic_config.get_main_option("sqlalchemy.url"), future=True)
    )
    with engine.connect() as connection:
        index_names = {
            row.name for row in connection.execute(text("PRAGMA index_list('occurrence')"))
        }
    assert "ix_occurrence_book_lemma_pos" in index_names

    command.downgrade(alembic_config, "-1")

    with engine.connect() as connection:
        index_names = {
            row.name for row in connection.execute(text("PRAGMA index_list('occurrence')"))
        }
        version = connection.execute(text("select version_num from alembic_version")).scalar_one()
    assert "ix_occurrence_book_lemma_pos" not in index_names
    assert version == "0003_annotation"


def test_downgrade_touches_no_other_schema_object(
    alembic_config: Config,
    managed_engine: Callable[[Engine], Engine],
) -> None:
    """The migration is additive-only: downgrade must not drop or retype any
    column or table `0003_annotation` created (design §Migration/Rollout)."""
    command.upgrade(alembic_config, "0003_annotation")
    engine = managed_engine(
        create_engine(alembic_config.get_main_option("sqlalchemy.url"), future=True)
    )
    from sqlalchemy import inspect

    inspector = inspect(engine)
    baseline_tables = set(inspector.get_table_names())
    baseline_occurrence = {
        (c["name"], c["type"].__class__.__name__, c["nullable"])
        for c in inspector.get_columns("occurrence")
    }

    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "0003_annotation")

    inspector = inspect(engine)
    after_tables = set(inspector.get_table_names())
    after_occurrence = {
        (c["name"], c["type"].__class__.__name__, c["nullable"])
        for c in inspector.get_columns("occurrence")
    }
    assert after_tables == baseline_tables
    assert after_occurrence == baseline_occurrence

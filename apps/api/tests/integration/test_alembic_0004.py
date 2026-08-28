"""Alembic integration tests for revision `0004_vocabulary_group_index` — design §Migration/Rollout.

Upgrading to `0004_vocabulary_group_index` must add a covering index
`ix_occurrence_book_lemma_pos` on `occurrence(book_id, lemma, pos)`; downgrading
to `0003_annotation` must remove it and return `alembic_version` to that
baseline exactly. The migration is additive only: it touches no column and no
table (design §Migration/Rollout).

REQ-005-009 / AC-005-09 scenario 3.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import command
from sqlalchemy import create_engine, inspect, text

from wheel_vocabulary.infrastructure.persistence.models import Occurrence

if TYPE_CHECKING:
    from collections.abc import Callable

    from alembic.config import Config
    from sqlalchemy import Engine


def test_upgrade_adds_the_group_index_downgrade_removes_it(
    alembic_config: Config,
    managed_engine: Callable[[Engine], Engine],
) -> None:
    """AC-005-09 scenario 3: upgrade creates the index, downgrade removes it
    and returns `alembic_version` to `0003_annotation`.

    Pinned to explicit revisions, not `head`/`-1`: this test asserts what THIS
    revision does. The moment a `0005` lands, `head` resolves past `0004` and a
    relative downgrade stops at `0004` instead of `0003_annotation`, so both
    post-downgrade assertions below would fail without the migration changing.
    That is the same defect this change repairs in `test_alembic_0003.py`.
    """
    command.upgrade(alembic_config, "0004_vocabulary_group_index")

    engine = managed_engine(
        create_engine(alembic_config.get_main_option("sqlalchemy.url"), future=True)
    )
    with engine.connect() as connection:
        index_names = {
            row.name for row in connection.execute(text("PRAGMA index_list('occurrence')"))
        }
        # `PRAGMA index_list` returns `(seq, name, unique, origin, partial)` —
        # no columns. Column order is the entire point of this index (design
        # §D2's ordered GROUP BY scan), so it must be checked separately, as a
        # list, never a set: `PRAGMA index_info` rows carry `seqno`, `cid`,
        # `name`, ordered by `seqno` to recover the declared column sequence.
        # A migration that swapped the column order would still pass every
        # assertion above without this check.
        index_info_rows = connection.execute(
            text("PRAGMA index_info('ix_occurrence_book_lemma_pos')")
        ).all()
    ordered_columns = [row.name for row in sorted(index_info_rows, key=lambda row: row.seqno)]
    assert "ix_occurrence_book_lemma_pos" in index_names
    assert ordered_columns == ["book_id", "lemma", "pos"]

    command.downgrade(alembic_config, "0003_annotation")

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

    inspector = inspect(engine)
    baseline_tables = set(inspector.get_table_names())
    baseline_occurrence = {
        (c["name"], c["type"].__class__.__name__, c["nullable"])
        for c in inspector.get_columns("occurrence")
    }
    baseline_indexes = {index["name"] for index in inspector.get_indexes("occurrence")}

    command.upgrade(alembic_config, "0004_vocabulary_group_index")
    command.downgrade(alembic_config, "0003_annotation")

    inspector = inspect(engine)
    after_tables = set(inspector.get_table_names())
    after_occurrence = {
        (c["name"], c["type"].__class__.__name__, c["nullable"])
        for c in inspector.get_columns("occurrence")
    }
    after_indexes = {index["name"] for index in inspector.get_indexes("occurrence")}

    assert after_tables == baseline_tables
    assert after_occurrence == baseline_occurrence
    # Index names too: without this, a downgrade that also dropped the
    # pre-existing `ix_occurrence_book_norm_raw` would pass every other
    # assertion in this file.
    assert after_indexes == baseline_indexes


def test_migrated_index_matches_the_declarative_model(
    alembic_config: Config,
    managed_engine: Callable[[Engine], Engine],
) -> None:
    """A migrated database and a fresh `Base.metadata.create_all()` must
    produce the same index: `Occurrence.__table_args__` in `models.py` and
    this migration must declare `ix_occurrence_book_lemma_pos` with the exact
    same ordered columns. Drift in either direction — the migration changing
    without the model, or the model changing without the migration — must
    fail here, not surface later as a silent scan-order regression between a
    fresh install and an upgraded one.
    """
    command.upgrade(alembic_config, "0004_vocabulary_group_index")

    engine = managed_engine(
        create_engine(alembic_config.get_main_option("sqlalchemy.url"), future=True)
    )
    migrated_index = next(
        index
        for index in inspect(engine).get_indexes("occurrence")
        if index["name"] == "ix_occurrence_book_lemma_pos"
    )

    declared_index = next(
        index
        for index in Occurrence.__table__.indexes
        if index.name == "ix_occurrence_book_lemma_pos"
    )

    assert migrated_index["column_names"] == ["book_id", "lemma", "pos"]
    assert list(declared_index.columns.keys()) == ["book_id", "lemma", "pos"]
    assert migrated_index["column_names"] == list(declared_index.columns.keys())

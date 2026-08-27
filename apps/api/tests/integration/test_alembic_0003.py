"""Alembic integration tests for revision `0003_annotation` — design §P5.

`alembic upgrade head` must add `occurrence.lemma`, the `annotation_provenance`
table and the `manual_correction` table; `alembic downgrade -1` must remove all
three and return the schema to the `0002_book_occurrence` baseline exactly —
nothing SPEC-002 created may be dropped, renamed, retyped, or made
non-nullable (REQ-003-015). A database already holding SPEC-002 imports must
survive the upgrade with every occurrence row unchanged (AC-003-16).

REQ-003-015 / AC-003-16.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from alembic import command
from sqlalchemy import create_engine, inspect, text

if TYPE_CHECKING:
    from collections.abc import Callable

    from alembic.config import Config
    from sqlalchemy import Engine


def test_upgrade_adds_lemma_provenance_and_correction(
    alembic_config: Config,
    managed_engine: Callable[[Engine], Engine],
) -> None:
    """AC-003-16: upgrade creates the three new objects, downgrade removes them.

    Pinned to the explicit revision `0003_annotation`, not `head`/`-1`: this
    test asserts what THIS revision does, and `head` has moved past it since
    `0004_vocabulary_group_index` landed (vocabulary-browser design
    §Migration/Rollout) — relative navigation would silently test the wrong
    revision boundary once another migration lands on top.
    """
    command.upgrade(alembic_config, "0003_annotation")

    engine = managed_engine(
        create_engine(alembic_config.get_main_option("sqlalchemy.url"), future=True)
    )
    inspector = inspect(engine)
    assert "annotation_provenance" in inspector.get_table_names()
    assert "manual_correction" in inspector.get_table_names()
    occurrence_columns = {column["name"] for column in inspector.get_columns("occurrence")}
    assert "lemma" in occurrence_columns

    command.downgrade(alembic_config, "0002_book_occurrence")

    inspector = inspect(engine)
    assert "annotation_provenance" not in inspector.get_table_names()
    assert "manual_correction" not in inspector.get_table_names()
    occurrence_columns = {column["name"] for column in inspector.get_columns("occurrence")}
    assert "lemma" not in occurrence_columns
    with engine.connect() as connection:
        version = connection.execute(text("select version_num from alembic_version")).scalar_one()
    assert version == "0002_book_occurrence"


def test_downgrade_leaves_the_spec_002_tables_structurally_identical(
    alembic_config: Config,
    managed_engine: Callable[[Engine], Engine],
) -> None:
    """REQ-003-015: `downgrade()` MUST NOT drop, rename, retype, or make
    non-nullable any column `002-text-import` created."""
    command.upgrade(alembic_config, "0002_book_occurrence")
    engine = managed_engine(
        create_engine(alembic_config.get_main_option("sqlalchemy.url"), future=True)
    )
    inspector = inspect(engine)
    baseline_book = {
        (c["name"], c["type"].__class__.__name__, c["nullable"])
        for c in inspector.get_columns("book")
    }
    baseline_occurrence = {
        (c["name"], c["type"].__class__.__name__, c["nullable"])
        for c in inspector.get_columns("occurrence")
        if c["name"] != "lemma"
    }

    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "0002_book_occurrence")

    inspector = inspect(engine)
    after_book = {
        (c["name"], c["type"].__class__.__name__, c["nullable"])
        for c in inspector.get_columns("book")
    }
    after_occurrence = {
        (c["name"], c["type"].__class__.__name__, c["nullable"])
        for c in inspector.get_columns("occurrence")
    }
    assert after_book == baseline_book
    assert after_occurrence == baseline_occurrence


def test_upgrade_preserves_pre_existing_spec_002_rows(
    alembic_config: Config,
    managed_engine: Callable[[Engine], Engine],
) -> None:
    """AC-003-16: an occurrence written before this capability shipped keeps
    its `raw_text`, `normalized_text` and `position` unchanged after upgrade."""
    command.upgrade(alembic_config, "0002_book_occurrence")
    engine = managed_engine(
        create_engine(alembic_config.get_main_option("sqlalchemy.url"), future=True)
    )
    book_table = text(
        "insert into book (language, content_hash, import_status, token_count, created_at)"
        " values (null, :content_hash, 'succeeded', 1, :created_at)"
    )
    with engine.begin() as connection:
        connection.execute(
            book_table,
            # Bound as an ISO string, not a raw `datetime`: this is a bare
            # `text()` insert with no SQLAlchemy column type attached, so the
            # parameter reaches sqlite3's DBAPI layer as-is. Python 3.12
            # deprecated sqlite3's own default datetime adapter
            # (`DeprecationWarning`, caught as an error by this project's
            # `filterwarnings` gate) — binding a plain string sidesteps that
            # adapter entirely. `created_at` is never asserted on below; only
            # `raw_text`/`normalized_text`/`position`/`lemma` are (AC-003-16).
            {
                "content_hash": "0" * 64,
                "created_at": datetime(2026, 8, 1, tzinfo=UTC).isoformat(sep=" "),
            },
        )
        book_id = connection.execute(text("select id from book")).scalar_one()
        connection.execute(
            text(
                "insert into occurrence (book_id, raw_text, normalized_text, position, pos)"
                " values (:book_id, 'run', 'run', 0, null)"
            ),
            {"book_id": book_id},
        )

    command.upgrade(alembic_config, "head")

    with engine.connect() as connection:
        row = connection.execute(
            text(
                "select raw_text, normalized_text, position, lemma"
                " from occurrence where book_id = :book_id"
            ),
            {"book_id": book_id},
        ).one()
    assert row.raw_text == "run"
    assert row.normalized_text == "run"
    assert row.position == 0
    assert row.lemma is None

"""Hypothesis properties for `SqlAlchemyVocabularyReadRepository` — design §D1.

Both properties run against the REAL repository over a real SQLite database,
through a locally defined `session_factory` fixture — the same pattern
`test_annotation_models.py` and `test_annotate_import_properties.py` already
established for repository-level tests. `resolve_effective`
(`domain/annotation.py:132`) is the ONLY place §2.5's precedence rule runs
(design D1); these properties prove the repository's V3 hybrid — a raw
`GROUP BY` (leg A) plus a bounded correction delta (leg B), merged in Python
— agrees with it on every generated case, never a second definition of the
rule in SQL.

`manual_correction` has no writer yet (SPEC-004): every seeded correction
below is inserted directly through the ORM, which is what `REQ-005-002`
means by "testable now".

REQ-005-001, REQ-005-002, REQ-005-003, REQ-005-005, AC-005-01, AC-005-02.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from wheel_vocabulary.domain.annotation import resolve_effective
from wheel_vocabulary.infrastructure.persistence.base import Base
from wheel_vocabulary.infrastructure.persistence.engine import (
    create_engine_from_url,
    create_session_factory,
)
from wheel_vocabulary.infrastructure.persistence.models import Book, ManualCorrection, Occurrence
from wheel_vocabulary.infrastructure.persistence.vocabulary_repository import (
    SqlAlchemyVocabularyReadRepository,
    VocabularyGroup,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.orm import Session, sessionmaker

_NOW = datetime(2026, 8, 27, 12, 0, 0, tzinfo=UTC)

# `(automatic, corrected)` for one field: `None` for `corrected` means no
# `ManualCorrection` row is seeded for that field at all — matching
# `resolve_effective`'s own signature (`corrected: str | None`).
_optional_text = st.one_of(
    st.none(), st.text(alphabet=st.characters(categories=["Ll"]), min_size=1, max_size=5)
)

# One occurrence's full spec: `(automatic_lemma, automatic_pos, corrected_lemma, corrected_pos)`.
_occurrence_spec = st.tuples(_optional_text, _optional_text, _optional_text, _optional_text)

Spec = tuple[str | None, str | None, str | None, str | None]


@pytest.fixture
def session_factory(tmp_path):  # noqa: ANN001, ANN201
    engine = create_engine_from_url(f"sqlite:///{tmp_path / 'vocabulary_repository.db'}")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    yield factory
    engine.dispose()


def _seed_occurrences(session_factory: sessionmaker[Session], specs: Sequence[Spec]) -> int:
    """Seed one `Book` with one `Occurrence` per spec, plus a `ManualCorrection`
    row for every non-`None` corrected value — direct ORM writes, mirroring
    `test_annotation_models.py::test_manual_correction_maps_field_and_
    corrected_value`'s precedent for seeding a table with no writer yet."""
    with session_factory() as session:
        book = Book(
            content_hash="0" * 64,
            import_status="succeeded",
            token_count=len(specs),
            created_at=_NOW,
        )
        session.add(book)
        session.flush()
        for position, (automatic, tag, corrected_word, corrected_tag) in enumerate(specs):
            occurrence = Occurrence(
                book_id=book.id,
                raw_text=f"tok{position}",
                normalized_text=f"tok{position}",
                position=position,
                lemma=automatic,
                pos=tag,
            )
            session.add(occurrence)
            session.flush()
            if corrected_word is not None:
                session.add(
                    ManualCorrection(
                        occurrence_id=occurrence.id,
                        field="lemma",
                        corrected_value=corrected_word,
                        corrected_at=_NOW,
                    )
                )
            if corrected_tag is not None:
                session.add(
                    ManualCorrection(
                        occurrence_id=occurrence.id,
                        field="pos",
                        corrected_value=corrected_tag,
                        corrected_at=_NOW,
                    )
                )
        session.commit()
        return book.id


def _naive_groups(specs: Sequence[Spec]) -> dict[tuple[str | None, str | None], int]:
    """Reference implementation T7 checks V3 against: resolve every
    occurrence's effective pair independently via `resolve_effective` and
    count it — never a second, divergent precedence rule (design D1).
    Shared with T6 (a one-spec call), extracted per task T11 once both
    properties below needed the identical computation."""
    expected: dict[tuple[str | None, str | None], int] = {}
    for automatic, tag, corrected_word, corrected_tag in specs:
        expected_word, _ = resolve_effective(automatic, corrected_word)
        expected_tag, _ = resolve_effective(tag, corrected_tag)
        key = (expected_word, expected_tag)
        expected[key] = expected.get(key, 0) + 1
    return expected


# --------------------------------------------------------------------------
# T6 — per-occurrence effective resolution agrees with `resolve_effective`.
# --------------------------------------------------------------------------


@pytest.mark.unit
@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(spec=_occurrence_spec)
def test_property_the_repositorys_effective_resolution_agrees_with_resolve_effective(
    session_factory: sessionmaker[Session], spec: Spec
) -> None:
    """AC-005-02 scenario 4: for every generated `(automatic, corrected)`
    pair, the single group the repository returns for one seeded occurrence
    matches `resolve_effective` applied to each field independently — never
    a second, divergent precedence rule (design D1, E3)."""
    book_id = _seed_occurrences(session_factory, [spec])
    repository = SqlAlchemyVocabularyReadRepository(session_factory)

    groups = repository.groups(book_id)

    expected = _naive_groups([spec])
    assert groups is not None
    assert {(group.lemma, group.pos): group.occurrence_count for group in groups} == expected


# --------------------------------------------------------------------------
# T7 — V3's group-by-group counts equal a naive Python groupby.
# --------------------------------------------------------------------------


@pytest.mark.unit
@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(specs=st.lists(_occurrence_spec, min_size=1, max_size=8))
def test_property_v3_group_counts_equal_a_naive_python_groupby_over_resolve_effective(
    session_factory: sessionmaker[Session], specs: list[Spec]
) -> None:
    """Design D1's RED-first equivalence requirement: V3 (leg A `GROUP BY`
    plus the leg B correction delta, merged via `resolve_effective`) must
    equal, group for group and count for count, a naive Python groupby that
    resolves every occurrence's effective pair independently and counts
    them — for arbitrary seeded corrections, never just the happy path."""
    book_id = _seed_occurrences(session_factory, specs)
    repository = SqlAlchemyVocabularyReadRepository(session_factory)

    groups = repository.groups(book_id)

    expected = _naive_groups(specs)
    assert groups is not None
    actual = {(group.lemma, group.pos): group.occurrence_count for group in groups}
    assert actual == expected


# --------------------------------------------------------------------------
# Result ordering — design D5, and the None-comparison landmine it flags.
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_the_returned_sequence_is_ordered_by_count_desc_then_lemma_then_pos_with_null_first(
    session_factory: sessionmaker[Session],
) -> None:
    """Design D5: `occurrence_count DESC, lemma, pos`, applied AFTER the
    leg-A/leg-B merge, `NULL` sorting before any string in both key halves.

    A naive `sorted(groups, key=lambda g: (-g.occurrence_count, g.lemma,
    g.pos))` would raise `TypeError` the moment it compares a `None` lemma
    against a string lemma at the same count tier — which this fixture
    deliberately creates (two count=1 groups, one keyed `None`, one keyed
    `"aa"`). Asserted positionally against a literal list, never as a set or
    a sorted copy, so a stable-but-wrong order (e.g. insertion order) cannot
    pass it either.
    """
    book_id = _seed_occurrences(
        session_factory,
        [
            ("bb", "NOUN", None, None),
            ("bb", "NOUN", None, None),  # ("bb", "NOUN") count 2 — sorts first
            (None, None, None, None),  # (None, None) count 1
            (None, "VERB", None, None),  # (None, "VERB") count 1
            ("aa", None, None, None),  # ("aa", None) count 1
        ],
    )
    repository = SqlAlchemyVocabularyReadRepository(session_factory)

    groups = repository.groups(book_id)

    assert groups == [
        VocabularyGroup(lemma="bb", pos="NOUN", occurrence_count=2),
        VocabularyGroup(lemma=None, pos=None, occurrence_count=1),
        VocabularyGroup(lemma=None, pos="VERB", occurrence_count=1),
        VocabularyGroup(lemma="aa", pos=None, occurrence_count=1),
    ]


# --------------------------------------------------------------------------
# Existence check — mirrors `annotation_repository.py::read`'s pattern.
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_groups_returns_none_for_an_unknown_book_id(
    session_factory: sessionmaker[Session],
) -> None:
    """`None` means the id is unknown — a 404, never conflated with a
    genuinely empty result (§2.3, AC-005-05)."""
    repository = SqlAlchemyVocabularyReadRepository(session_factory)

    assert repository.groups(999) is None


@pytest.mark.unit
def test_groups_returns_an_empty_list_for_an_existing_import_with_zero_occurrences(
    session_factory: sessionmaker[Session],
) -> None:
    """An import that exists with zero occurrences is a success carrying an
    empty group set, never a `None` body (AC-005-05 scenario 3)."""
    with session_factory() as session:
        book = Book(
            content_hash="0" * 64, import_status="succeeded", token_count=0, created_at=_NOW
        )
        session.add(book)
        session.commit()
        book_id = book.id
    repository = SqlAlchemyVocabularyReadRepository(session_factory)

    groups = repository.groups(book_id)

    assert groups == []

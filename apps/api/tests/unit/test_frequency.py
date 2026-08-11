"""Unit tests for §2.4 ordering and §2.5 display-form selection (T1A07).

Written RED before ``domain/frequency.py`` exists: the import below is the only
thing that can fail at collection time, so the failure cannot be a fixture or
configuration fault.

REQ-002-006 (domain leg) / AC-002-08, REQ-002-016 / AC-002-21,
REQ-002-017 / AC-002-22, REQ-002-018 / AC-002-23, AC-002-24.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from wheel_vocabulary.domain.frequency import build_table, sort_key
from wheel_vocabulary.domain.text.normalizer import normalize
from wheel_vocabulary.domain.text.tokenizer import tokenize

# Letters in both cases plus the joiners and the sharp-s family, so generated
# groups actually collide under casefolding instead of staying singletons.
_SURFACE_ALPHABET = "aAbB\u00df\u1e9e\u00e1\u00c1'\u2019-"


def _pairs_from_text(text: str) -> list[tuple[str, str, int]]:
    """Build the import-path triples: every occurrence counts once."""
    return [(token.raw_text, normalize(token.raw_text), 1) for token in tokenize(text)]


def _pairs_from_raw_forms(raw_forms: list[str]) -> list[tuple[str, str, int]]:
    """Build triples straight from generated surface forms, dropping empty keys."""
    return [(raw, normalize(raw), 1) for raw in raw_forms if normalize(raw)]


@pytest.mark.unit
def test_repeated_forms_collapse_with_frequency_and_sum() -> None:
    """AC-002-08 domain leg: one row per normalized form, frequencies sum to tokens."""
    text = "corre Corre CORRE zebra"

    table = build_table(_pairs_from_text(text))

    by_key = {row.normalized_form: row for row in table}
    assert set(by_key) == {"corre", "zebra"}
    assert by_key["corre"].frequency == 3
    assert by_key["zebra"].frequency == 1
    assert sum(row.frequency for row in table) == len(tokenize(text))


@pytest.mark.unit
def test_majority_and_tie_break_display_form() -> None:
    """AC-002-23: both worked examples from spec §2.5."""
    majority = build_table(_pairs_from_text("Stra\u00dfe stra\u00dfe STRASSE Stra\u00dfe"))

    assert len(majority) == 1
    assert majority[0].normalized_form == "strasse"
    assert majority[0].display_form == "Stra\u00dfe"
    assert majority[0].frequency == 4

    tied = build_table(_pairs_from_text("Stra\u00dfe stra\u00dfe STRASSE"))

    assert len(tied) == 1
    assert tied[0].normalized_form == "strasse"
    assert tied[0].display_form == "STRASSE"
    assert tied[0].frequency == 3


@pytest.mark.unit
def test_display_form_is_substring_of_source() -> None:
    """AC-002-24 domain leg: the displayed value literally occurs in the text."""
    text = "Stra\u00dfe stra\u00dfe cafe\u0301 caf\u00e9 state-of-the-art"

    table = build_table(_pairs_from_text(text))

    assert table
    for row in table:
        assert row.display_form in text


@pytest.mark.unit
def test_rows_are_ordered_diacritic_insensitively_by_the_grouping_key() -> None:
    """AC-002-09 domain leg: §2.4 sorts on the key, never on the display form."""
    table = build_table(_pairs_from_text("zebra \u00e1baco abandonar"))

    assert [row.normalized_form for row in table] == ["\u00e1baco", "abandonar", "zebra"]


@pytest.mark.unit
def test_ordering_uses_the_grouping_key_not_the_display_form() -> None:
    """§2.4: a row keyed ``strasse`` and displayed ``Straße`` still sorts under ``s``."""
    table = build_table(_pairs_from_text("Stra\u00dfe Stra\u00dfe sun tea"))

    assert [row.normalized_form for row in table] == ["strasse", "sun", "tea"]
    assert table[0].display_form == "Stra\u00dfe"


@pytest.mark.unit
def test_sort_key_strips_diacritics_and_stays_total() -> None:
    """§2.4: (NFD minus M*, normalized form). The second component makes it total."""
    assert sort_key("\u00e1baco") == ("abaco", "\u00e1baco")
    assert sort_key("abandonar") == ("abandonar", "abandonar")
    assert sort_key("\u00e1baco") < sort_key("abandonar")
    # Same stripped component, different keys: the tie is broken, not arbitrary.
    assert sort_key("abaco") < sort_key("\u00e1baco")


@pytest.mark.unit
def test_counts_from_the_read_path_are_summed_not_recounted() -> None:
    """The read path supplies SQL counts, so build_table must add them."""
    table = build_table([("Stra\u00dfe", "strasse", 5), ("STRASSE", "strasse", 2)])

    assert len(table) == 1
    assert table[0].frequency == 7
    assert table[0].display_form == "Stra\u00dfe"


@pytest.mark.unit
def test_empty_input_produces_no_rows() -> None:
    """REQ-002-012 domain leg: nothing to aggregate is a valid, empty result."""
    assert build_table([]) == ()
    assert build_table(_pairs_from_text(" \n\t")) == ()


@pytest.mark.unit
@pytest.mark.parametrize("count", [0, -1])
def test_non_positive_counts_are_rejected(count: int) -> None:
    """REQ-002-017: a zero or negative frequency can never enter the aggregate."""
    with pytest.raises(ValueError, match="frequency"):
        build_table([("word", "word", count)])


@pytest.mark.unit
@given(st.data(), st.lists(st.text(alphabet=_SURFACE_ALPHABET, min_size=1), max_size=40))
def test_aggregation_is_order_independent_hypothesis(
    data: st.DataObject, raw_forms: list[str]
) -> None:
    """AC-002-21: keys, frequencies AND display forms survive any permutation.

    NOTE (AMB-4): AGENTS.md §6 phrases this invariant over *lemmas*, which do not
    exist in this slice. It is verified here over normalized forms and MUST be
    re-verified against real lemmas when lemmatization ships.
    """
    pairs = _pairs_from_raw_forms(raw_forms)
    permuted = data.draw(st.permutations(pairs))

    table = build_table(pairs)
    permuted_table = build_table(permuted)

    assert {row.normalized_form for row in table} == {row.normalized_form for row in permuted_table}
    assert {row.normalized_form: row.frequency for row in table} == {
        row.normalized_form: row.frequency for row in permuted_table
    }
    assert {row.normalized_form: row.display_form for row in table} == {
        row.normalized_form: row.display_form for row in permuted_table
    }
    assert table == permuted_table


@pytest.mark.unit
def test_permuting_a_tied_group_does_not_change_the_display_form() -> None:
    """AC-002-21 worked case: a positional tie-break would fail this."""
    raw_forms = ["Stra\u00dfe", "stra\u00dfe", "STRASSE"]

    for rotation in range(len(raw_forms)):
        rotated = raw_forms[rotation:] + raw_forms[:rotation]
        table = build_table(_pairs_from_raw_forms(rotated))

        assert table[0].display_form == "STRASSE"


@pytest.mark.unit
@given(st.lists(st.text(alphabet=_SURFACE_ALPHABET, min_size=1), max_size=40))
def test_frequencies_are_never_negative_hypothesis(raw_forms: list[str]) -> None:
    """AC-002-22: every listed form carries an integer frequency >= 1."""
    pairs = _pairs_from_raw_forms(raw_forms)

    table = build_table(pairs)

    assert sum(row.frequency for row in table) == len(pairs)
    for row in table:
        assert isinstance(row.frequency, int)
        assert row.frequency >= 1
        assert row.normalized_form
        assert row.display_form

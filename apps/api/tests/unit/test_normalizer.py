"""Unit tests for the §2.3 normalization pipeline N1-N5 (T1A04).

Written RED before ``domain/text/normalizer.py`` exists: the import below is the
only thing that can fail at collection time, so the failure cannot be a fixture
or configuration fault.

REQ-002-005 / AC-002-07, REQ-002-015 / AC-002-20, spec §2.3.
"""

from __future__ import annotations

import unicodedata

import pytest
from hypothesis import given
from hypothesis import strategies as st

from wheel_vocabulary.domain.text.normalizer import normalize

_SHY = "\u00ad"

# Code points that historically break a naive pipeline. ``ŉ`` (U+0149) is the
# load-bearing one: it casefolds to U+02BC + ``n``, so folding apostrophes
# before casefolding makes the pipeline non-idempotent (§2.3, REQ-002-015).
_ADVERSARIAL = (
    "\u0149",  # ŉ LATIN SMALL LETTER N PRECEDED BY APOSTROPHE
    "a\u0149b",  # the same expansion, internal — N5 cannot mask a wrong order here
    "Stra\u00dfe",  # ß -> ss only under casefold()
    "\u1e9e",  # ẞ LATIN CAPITAL LETTER SHARP S
    "\u0130",  # İ LATIN CAPITAL LETTER I WITH DOT ABOVE
    "\u03a3\u038a\u03a3\u03a5\u03a6\u039f\u03a3",  # ΣΊΣΥΦΟΣ — final sigma
    "cafe\u0301",  # decomposed
    "caf\u00e9",  # precomposed
    "don\u2019t",
    "state\u2010of\u2010the\u2010art",
    f"inter{_SHY}national",
)

# (rule id, input, expected output)
_RULE_CASES: list[tuple[str, str, str]] = [
    # N1: canonical composition unifies the two encodings of one character.
    ("N1", "cafe\u0301", "caf\u00e9"),
    ("N1", "caf\u00e9", "caf\u00e9"),
    # N2: casefold(), not lower() — ß and final sigma must fold.
    ("N2", "Stra\u00dfe", "strasse"),
    ("N2", "STRASSE", "strasse"),
    ("N2", "\u1e9e", "ss"),
    (
        "N2",
        "\u03a3\u038a\u03a3\u03a5\u03a6\u039f\u03a3",
        "\u03c3\u03af\u03c3\u03c5\u03c6\u03bf\u03c3",
    ),
    # N3: recomposition after casefolding; İ has no precomposed lowercase form,
    # so it legitimately stays as i + COMBINING DOT ABOVE.
    ("N3", "\u0130", "i\u0307"),
    # N4: every apostrophe variant folds to U+0027, every hyphen to U+002D.
    ("N4", "don\u2019t", "don't"),
    ("N4", "l\u02bchomme", "l'homme"),
    ("N4", "\u2018tis", "tis"),
    ("N4", "a\u2010b", "a-b"),
    # N4 must run AFTER N2/N3: the U+02BC exposed by casefolding U+0149 has to
    # be folded in the same pass, or a second pass would change the result.
    #
    # LOAD-BEARING — do not simplify this row to the standalone `ŉ` the spec
    # uses as its N5 example. Standing alone the exposed U+02BC sits on an edge,
    # so N5 strips it under either order and `normalize("ŉ")` is `n` and
    # idempotent even with N4 misordered. Only an INTERNAL occurrence escapes
    # N5 and exposes the bug: misordered, this input gives `aʼnb` on the first
    # pass and `a'nb` on the second. Delete this row and a non-idempotent
    # pipeline ships green (spec §2.3, REQ-002-015).
    ("N4", "a\u0149b", "a'nb"),
    # N5: strip leading and trailing joiners; discard when nothing remains.
    ("N5", "\u0149", "n"),
    ("N5", "-word-", "word"),
    ("N5", "'word'", "word"),
    ("N5", "'", ""),
    ("N5", "-", ""),
    # T1 leg (design §5): the soft hyphen is stripped here, never by a
    # document pre-pass, so raw_text keeps it and AC-002-24 survives.
    ("T1", f"inter{_SHY}national", "international"),
]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("rule", "text", "expected"),
    _RULE_CASES,
    ids=[f"{rule}-{index}" for index, (rule, _, _) in enumerate(_RULE_CASES)],
)
def test_normalization_rules(rule: str, text: str, expected: str) -> None:
    """Each §2.3 rule row produces its documented output exactly."""
    produced = normalize(text)

    assert produced == expected, f"rule {rule} produced {produced!r}, expected {expected!r}"


@pytest.mark.unit
def test_diacritics_are_preserved() -> None:
    """§2.3: NFKC/NFKD are rejected as lossy, so accents are meaning-bearing."""
    assert normalize("s\u00ed") != normalize("si")
    assert normalize("sch\u00f6n") != normalize("schon")


@pytest.mark.unit
@pytest.mark.parametrize("text", _ADVERSARIAL)
def test_known_adversarial_code_points_are_idempotent(text: str) -> None:
    """AC-002-20: the documented adversarial set is a fixed point after one pass."""
    once = normalize(text)

    assert normalize(once) == once


@pytest.mark.unit
@pytest.mark.parametrize("text", _ADVERSARIAL)
def test_output_is_nfc_stable(text: str) -> None:
    """N3: the result is canonically composed, so no downstream NFC pass can move it."""
    once = normalize(text)

    assert unicodedata.normalize("NFC", once) == once


@pytest.mark.unit
@given(st.text())
def test_normalize_is_idempotent(text: str) -> None:
    """REQ-002-015 / AC-002-20: normalize(normalize(x)) == normalize(x) for all x.

    NOTE (AMB-4): AGENTS.md §6 phrases this invariant over *lemmas*, which do not
    exist in this slice. It is verified here over normalized forms and MUST be
    re-verified against real lemmas when lemmatization ships.
    """
    once = normalize(text)

    assert normalize(once) == once


@pytest.mark.unit
@given(st.text(alphabet=st.sampled_from("aA\u0149\u00df\u1e9e\u0130'\u2019\u02bc-\u2010 \u00ad")))
def test_normalize_is_idempotent_over_adversarial_alphabet(text: str) -> None:
    """Same invariant, biased toward the code points that break a wrong N4 order."""
    once = normalize(text)

    assert normalize(once) == once


@pytest.mark.unit
@given(st.text())
def test_output_never_starts_or_ends_with_a_joiner(text: str) -> None:
    """N5 is total: no generated input can leave a dangling joiner."""
    joiners = "\u0027\u2019\u02bc\u2018\u002d\u2010"
    once = normalize(text)

    if once:
        assert once[0] not in joiners
        assert once[-1] not in joiners

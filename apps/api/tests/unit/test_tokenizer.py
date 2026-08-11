"""Unit tests for the §2.2 tokenization rules T1-T10 (T1A01).

Written RED before ``domain/text/tokenizer.py`` exists: the import below is the
only thing that can fail at collection time, which is what proves the failure is
absent production code rather than a broken fixture.

REQ-002-005 / AC-002-07, spec §2.1 (character classes) and §2.2 (T1-T10).
"""

from __future__ import annotations

import pytest

from wheel_vocabulary.domain.text.tokenizer import tokenize

_SHY = "\u00ad"  # U+00AD SOFT HYPHEN — invisible formatting (T1)

# (rule id, input text, expected raw_text sequence)
_RULE_CASES: list[tuple[str, str, tuple[str, ...]]] = [
    # T1: a soft hyphen never breaks a token. It stays inside ``raw_text`` so
    # the textual form remains a verbatim slice of the source (design §5).
    ("T1", f"inter{_SHY}national text", (f"inter{_SHY}national", "text")),
    # T2: hyphenated compounds are a single lexical unit.
    ("T2", "state-of-the-art", ("state-of-the-art",)),
    ("T2", "a\u2010b", ("a\u2010b",)),
    # T3: an apostrophe between word characters is internal.
    ("T3", "don't l'homme O'Neill", ("don't", "l'homme", "O'Neill")),
    ("T3", "don\u2019t l\u02bchomme \u2018tis", ("don\u2019t", "l\u02bchomme", "tis")),
    # T4: a joiner that is not between two word characters is a separator.
    ("T4", "inter-\nnational", ("inter", "national")),
    ("T4", "-dash-", ("dash",)),
    ("T4", "a--b", ("a", "b")),
    # T5: en dash, em dash and minus sign are separators, never joiners.
    ("T5", "word\u2014word", ("word", "word")),
    ("T5", "word\u2013word word\u2212word", ("word", "word", "word", "word")),
    # T6: a token must contain at least one L* character.
    ("T6", "2026 covid19 3rd 1914\u20131918", ("covid19", "3rd")),
    ("T6", "42", ()),
    # T7: underscore is a separator.
    ("T7", "snake_case", ("snake", "case")),
    # T8: all Unicode whitespace separates equally.
    (
        "T8",
        "line1\r\nline2\tline3\u00a0line4\u200bline5\u2028line6",
        ("line1", "line2", "line3", "line4", "line5", "line6"),
    ),
    ("T8", "line1\r\nline2", ("line1", "line2")),
    # T9: hyphenation across a line break is NOT rejoined.
    ("T9", "well-\nknown", ("well", "known")),
    # Combining marks are word characters (§2.1), so decomposed spellings survive.
    ("M*", "cafe\u0301 na\u0308ive", ("cafe\u0301", "na\u0308ive")),
]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("rule", "text", "expected"),
    _RULE_CASES,
    ids=[f"{rule}-{index}" for index, (rule, _, _) in enumerate(_RULE_CASES)],
)
def test_tokenization_rules(rule: str, text: str, expected: tuple[str, ...]) -> None:
    """Each §2.2 rule row produces its documented token sequence exactly."""
    produced = tuple(token.raw_text for token in tokenize(text))

    assert produced == expected, f"rule {rule} produced {produced!r}, expected {expected!r}"


@pytest.mark.unit
def test_spec_scenario_synthetic_sentence() -> None:
    """The §3 REQ-002-005 scenario sentence tokenizes exactly as documented."""
    text = "state-of-the-art don't 2026 covid19 word\u2014word snake_case"

    produced = tuple(token.raw_text for token in tokenize(text))

    assert produced == ("state-of-the-art", "don't", "covid19", "word", "word", "snake", "case")


@pytest.mark.unit
def test_positions_are_contiguous_zero_based_token_indices() -> None:
    """T10: ``position`` is the index in the emitted sequence, not a byte offset."""
    tokens = tokenize("alpha 2026 beta\u2014gamma")

    assert [token.raw_text for token in tokens] == ["alpha", "beta", "gamma"]
    assert [token.position for token in tokens] == [0, 1, 2]


@pytest.mark.unit
def test_raw_text_is_a_verbatim_slice_of_the_source() -> None:
    """Design §5: no document-level transformation, so every raw_text occurs literally."""
    text = f"Stra\u00dfe cafe\u0301 inter{_SHY}national state-of-the-art"

    tokens = tokenize(text)

    assert tokens
    for token in tokens:
        assert token.raw_text in text


@pytest.mark.unit
def test_empty_and_separator_only_text_emit_no_tokens() -> None:
    """A whitespace-only source is a valid input that yields nothing (REQ-002-012 domain leg)."""
    assert tokenize("") == ()
    assert tokenize(" \n\t\u00a0") == ()

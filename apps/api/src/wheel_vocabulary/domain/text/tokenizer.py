"""Language-generic tokenization implementing spec §2.2 rules T1-T10.

Character classes come from the Unicode general category (§2.1), never from a
regex ``\\w`` shorthand: ``\\w`` drops combining marks, which would silently
truncate Devanagari, Thai, Hebrew and Arabic and would break the decomposed
spelling of accented Latin words (ADR-0008).

The soft hyphen is treated as a *transparent* character rather than removed by a
document pre-pass: a pre-pass would make ``raw_text`` a string that does not
occur in the file, breaking AC-002-24 (design §5, CONTRA-2).

REQ-002-005 / AC-002-07.
"""

from __future__ import annotations

import unicodedata

from wheel_vocabulary.domain.models import Token

__all__ = ["tokenize"]

_SOFT_HYPHEN = "\u00ad"

# §2.1 joiners: apostrophes and hyphens only. En dash, em dash and minus sign
# are deliberately absent — they punctuate clauses and never join words (T5).
_JOINERS = frozenset(
    {
        "\u0027",  # APOSTROPHE
        "\u2019",  # RIGHT SINGLE QUOTATION MARK
        "\u02bc",  # MODIFIER LETTER APOSTROPHE
        "\u2018",  # LEFT SINGLE QUOTATION MARK
        "\u002d",  # HYPHEN-MINUS
        "\u2010",  # HYPHEN
    }
)


def tokenize(text: str) -> tuple[Token, ...]:
    """Split ``text`` into tokens per §2.2.

    A token is a maximal run of word characters, optionally joined by single
    internal joiners between word characters (T2/T3/T4). Tokens carrying no
    letter are discarded (T6), so positions are contiguous over what is emitted.
    """
    stream = [(index, char) for index, char in enumerate(text) if char != _SOFT_HYPHEN]
    tokens: list[Token] = []
    cursor = 0

    while cursor < len(stream):
        if not _is_word_char(stream[cursor][1]):
            cursor += 1
            continue

        first = cursor
        last, cursor = _scan_token_span(stream, first)
        raw_text = text[stream[first][0] : stream[last][0] + 1]
        if _contains_letter(raw_text):
            tokens.append(Token(raw_text=raw_text, position=len(tokens)))

    return tuple(tokens)


def _scan_token_span(stream: list[tuple[int, str]], first: int) -> tuple[int, int]:
    """Return ``(last, next_cursor)`` for the token starting at ``first``.

    ``last`` is the index of the token's final word character; a joiner is
    absorbed only when a word character follows it (T4), which is also what
    makes runs of two or more joiners split the token.
    """
    last = first
    cursor = first + 1
    while cursor < len(stream):
        if _is_word_char(stream[cursor][1]):
            last = cursor
            cursor += 1
        elif (
            _is_joiner(stream[cursor][1])
            and cursor + 1 < len(stream)
            and _is_word_char(stream[cursor + 1][1])
        ):
            last = cursor + 1
            cursor += 2
        else:
            break
    return last, cursor


def _is_word_char(char: str) -> bool:
    """§2.1: general category ``L*`` (letter), ``M*`` (mark) or ``Nd`` (digit)."""
    category = unicodedata.category(char)
    return category[0] in {"L", "M"} or category == "Nd"


def _is_joiner(char: str) -> bool:
    """§2.1: an apostrophe or hyphen that may sit between two word characters."""
    return char in _JOINERS


def _contains_letter(text: str) -> bool:
    """T6: a token without a single ``L*`` character is not vocabulary."""
    return any(unicodedata.category(char)[0] == "L" for char in text)

"""Character classes of spec §2.1, shared by tokenization and normalization.

``tokenizer`` and ``normalizer`` are two readings of the same §2.1 vocabulary:
the tokenizer asks whether a character *may join* two word characters (T4),
the normalizer asks what that character *folds to* (N4) and which characters may
dangle at an edge (N5). Both answers must be drawn from one list, so the list
lives here rather than in either consumer.

This module is package-private on purpose. Its names are public so that a
consumer never has to import a private name across module boundaries, which is
what makes the dependency legible instead of incidental.

No rule lives here — only the classes the rules are written against.

REQ-002-005 / AC-002-07, spec §2.1.
"""

from __future__ import annotations

__all__ = ["APOSTROPHES", "HYPHENS", "JOINERS", "SOFT_HYPHEN"]

SOFT_HYPHEN = "\u00ad"

# §2.1 apostrophes. Folded to U+0027 by N4; the U+02BC entry is load-bearing
# because casefolding U+0149 emits it (see normalizer's module docstring).
APOSTROPHES = frozenset(
    {
        "\u0027",  # APOSTROPHE
        "\u2019",  # RIGHT SINGLE QUOTATION MARK
        "\u02bc",  # MODIFIER LETTER APOSTROPHE
        "\u2018",  # LEFT SINGLE QUOTATION MARK
    }
)

# §2.1 hyphens. Folded to U+002D by N4. En dash, em dash and minus sign are
# deliberately absent — they punctuate clauses and never join words (T5).
HYPHENS = frozenset(
    {
        "\u002d",  # HYPHEN-MINUS
        "\u2010",  # HYPHEN
    }
)

# The joiners of T2/T3/T4 and the strip set of N5 are the same class by
# definition, so it is derived rather than restated.
JOINERS = APOSTROPHES | HYPHENS

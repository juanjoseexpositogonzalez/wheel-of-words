"""Normalization pipeline implementing spec §2.3 steps N1-N5.

The step order is NORMATIVE. ``N4`` (joiner folding) MUST run after ``N2``/``N3``
(casefold + recompose): ``U+0149 ŉ`` casefolds to ``U+02BC`` + ``n``, so folding
apostrophes first leaves that expansion untouched on the first pass and folds it
on the second, making ``normalize(normalize(x)) != normalize(x)`` and failing
REQ-002-015.

``casefold()`` is used rather than ``lower()``: ``lower()`` leaves ``ß`` and the
Greek final sigma unmatched, which an ADR-0008 multi-language project cannot
accept. NFKC/NFKD are rejected as lossy — diacritics are preserved, so ``sí`` is
not ``si``.

REQ-002-005 / AC-002-07, REQ-002-015 / AC-002-20.
"""

from __future__ import annotations

import unicodedata

from wheel_vocabulary.domain.text.tokenizer import _JOINERS, _SOFT_HYPHEN

__all__ = ["normalize"]

_APOSTROPHES = frozenset({"\u0027", "\u2019", "\u02bc", "\u2018"})
_HYPHENS = frozenset({"\u002d", "\u2010"})
_JOINER_FOLD = {ord(char): "\u0027" for char in _APOSTROPHES} | {
    ord(char): "\u002d" for char in _HYPHENS
}
_JOINER_CHARS = "".join(sorted(_JOINERS))


def normalize(text: str) -> str:
    """Return the grouping key for ``text`` per §2.3.

    Returns the empty string when nothing survives ``N5`` — the caller decides
    whether that token is discarded.
    """
    result = _strip_soft_hyphens(text)
    result = _n1_compose(result)
    result = _n2_casefold(result)
    result = _n3_compose(result)
    result = _n4_fold_joiners(result)
    return _n5_strip_edge_joiners(result)


def _strip_soft_hyphens(text: str) -> str:
    """T1 leg: invisible formatting is never part of the grouping key (design §5)."""
    return text.replace(_SOFT_HYPHEN, "")


def _n1_compose(text: str) -> str:
    """N1: canonical composition, so the two encodings of ``café`` group as one."""
    return unicodedata.normalize("NFC", text)


def _n2_casefold(text: str) -> str:
    """N2: Unicode-full caseless matching — ``Straße`` and ``STRASSE`` collapse."""
    return text.casefold()


def _n3_compose(text: str) -> str:
    """N3: casefolding can emit decomposed sequences; recompose them."""
    return unicodedata.normalize("NFC", text)


def _n4_fold_joiners(text: str) -> str:
    """N4: apostrophe and hyphen variants are authoring-tool artifacts, not words.

    MUST run after N2/N3 — see the module docstring.
    """
    return text.translate(_JOINER_FOLD)


def _n5_strip_edge_joiners(text: str) -> str:
    """N5: drop dangling joiners, e.g. the one casefolding ``ŉ`` exposes."""
    return text.strip(_JOINER_CHARS)

"""Aggregation into the ordered frequency table — spec §2.4 and §2.5.

This is the SINGLE implementation of the display-form and ordering rules. The
import path calls it with every occurrence counted once; the read path calls it
with counts already aggregated by SQL. Both must produce the same table, so the
rule cannot be duplicated anywhere else.

Selection is a function of the *multiset* of textual forms only. No positional
input reaches this module, which is what mechanically forbids the first-occurrence
tie-break that REQ-002-018 rules out.

REQ-002-006 (domain leg), REQ-002-016, REQ-002-017, REQ-002-018.
"""

from __future__ import annotations

import unicodedata
from collections import Counter
from typing import TYPE_CHECKING

from wheel_vocabulary.domain.models import FormFrequency

if TYPE_CHECKING:
    from collections.abc import Iterable

__all__ = ["build_table", "sort_key"]


def build_table(pairs: Iterable[tuple[str, str, int]]) -> tuple[FormFrequency, ...]:
    """Aggregate ``(raw_text, normalized_text, count)`` triples into ordered rows.

    Raises:
        ValueError: if any ``count`` is below ``1``. REQ-002-017 forbids a row
            with a non-positive frequency, so a caller that produced one has a
            defect that must surface here rather than reach the user.
    """
    groups = _d1_count_surface_forms(pairs)
    rows = [
        FormFrequency(
            normalized_form=normalized_form,
            display_form=_select_display_form(surface_counts),
            frequency=sum(surface_counts.values()),
        )
        for normalized_form, surface_counts in groups.items()
    ]
    return tuple(sorted(rows, key=lambda row: sort_key(row.normalized_form)))


def sort_key(normalized_form: str) -> tuple[str, str]:
    """Return the §2.4 ordering key: (diacritic-stripped form, normalized form).

    Computed for ordering only and never stored. Locale collation is rejected: it
    needs a known language and varies across platforms, which would break Art.
    VI.2 reproducibility.
    """
    decomposed = unicodedata.normalize("NFD", normalized_form)
    stripped = "".join(char for char in decomposed if unicodedata.category(char)[0] != "M")
    return (stripped, normalized_form)


def _d1_count_surface_forms(pairs: Iterable[tuple[str, str, int]]) -> dict[str, Counter[str]]:
    """D1: count each distinct ``raw_text`` inside each group."""
    groups: dict[str, Counter[str]] = {}
    for raw_text, normalized_text, count in pairs:
        if count < 1:
            message = f"frequency must be >= 1, got {count}"
            raise ValueError(message)
        groups.setdefault(normalized_text, Counter())[raw_text] += count
    return groups


def _d2_highest_count(surface_counts: Counter[str]) -> int:
    """D2: the winning occurrence count inside the group."""
    return max(surface_counts.values())


def _d3_lowest_code_point(surface_counts: Counter[str], highest: int) -> str:
    """D3: break ties by ascending Unicode code-point order, never by position."""
    return min(raw_text for raw_text, count in surface_counts.items() if count == highest)


def _select_display_form(surface_counts: Counter[str]) -> str:
    """§2.5 D1-D3: most frequent textual form, ties by ascending code point."""
    return _d3_lowest_code_point(surface_counts, _d2_highest_count(surface_counts))

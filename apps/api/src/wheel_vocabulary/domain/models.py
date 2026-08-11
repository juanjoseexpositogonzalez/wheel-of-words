"""Domain value objects for the text-import capability.

Pure data carriers. Standard library only: no FastAPI, SQLAlchemy, Pydantic or
NLP dependency may ever reach this package (Art. VII.1, ADR-0002, AC-002-06).

REQ-002-005, REQ-002-018, design §7.1.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["FormFrequency", "Token"]


@dataclass(frozen=True, slots=True)
class Token:
    """One emitted token.

    ``raw_text`` is the *textual form*: a verbatim slice of the imported source,
    never transformed (design §5, AC-002-24). ``position`` is the zero-based
    index in the emitted token sequence, not a byte or character offset (T10).
    """

    raw_text: str
    position: int


@dataclass(frozen=True, slots=True)
class FormFrequency:
    """One row of the frequency table.

    ``normalized_form`` is the grouping key from §2.3 — synthetic, and possibly a
    spelling that appears nowhere in the text. ``display_form`` is the textual
    form the user reads, selected per §2.5 D1-D3. The two are distinct concepts
    and MUST NOT be conflated: a display form is the most frequent inflected
    spelling in its group, never a canonical dictionary headword (REQ-002-007).
    """

    normalized_form: str
    display_form: str
    frequency: int

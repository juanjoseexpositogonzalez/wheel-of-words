"""Domain value objects for the text-import capability.

Pure data carriers. Standard library only: no FastAPI, SQLAlchemy, Pydantic or
NLP dependency may ever reach this package (Art. VII.1, ADR-0002, AC-002-06).

REQ-002-005, REQ-002-018, design §7.1.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Token"]


@dataclass(frozen=True, slots=True)
class Token:
    """One emitted token.

    ``raw_text`` is the *textual form*: a verbatim slice of the imported source,
    never transformed (design §5, AC-002-24). ``position`` is the zero-based
    index in the emitted token sequence, not a byte or character offset (T10).
    """

    raw_text: str
    position: int

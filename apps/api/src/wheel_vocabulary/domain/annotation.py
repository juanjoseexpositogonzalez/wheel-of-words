"""Domain value object and pure rules for per-occurrence annotation.

Pure data and pure functions only. Standard library only: no spaCy, thinc,
stanza, SQLAlchemy, FastAPI or Pydantic may ever reach this module (Art.
VII.1, ADR-0002, REQ-003-002).

**Landmine (design §Phase 2, `tasks.md` task 2.1).** The bare string literal
`"pos"` has the exact shape `test_domain_isolation.py`'s ISO-639 guard
rejects — two-or-three lowercase letters. This module therefore never spells
`"pos"` as a string constant: `resolve_effective` distinguishes its two
fields by POSITION in the return tuple, never by a field-name string, and the
`Literal["pos", "lemma"]` field discriminator that names a corrected field
lives in `application/annotation/`, not here (AMB-6, REQ-003-023).

REQ-003-002 (shape and isolation), REQ-003-005 (shape), REQ-003-006 (shape),
REQ-003-008 (pure confidence rule), REQ-003-010 (pure precedence rule),
REQ-003-022 (no PROPN special case — this module has no filtering logic of
any kind, so there is nothing here that could special-case a tag).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

__all__ = [
    "LinguisticAnnotation",
    "Origin",
    "UPOS_TAGS",
    "resolve_effective",
    "validate_confidence",
]

# spec §2.2 — the closed 17-value Universal POS set, and no other. Uppercase,
# exactly as written; the domain-isolation ISO-639 guard only matches
# lowercase literals, so these are safe by construction.
UPOS_TAGS: frozenset[str] = frozenset(
    {
        "ADJ",
        "ADP",
        "ADV",
        "AUX",
        "CCONJ",
        "DET",
        "INTJ",
        "NOUN",
        "NUM",
        "PART",
        "PRON",
        "PROPN",
        "PUNCT",
        "SCONJ",
        "SYM",
        "VERB",
        "X",
    }
)


@dataclass(frozen=True, slots=True)
class LinguisticAnnotation:
    """One occurrence's automatic annotation — spec §2.1, §2.2, §2.3.

    ``pos`` and ``lemma`` MAY both be ``None`` for an occurrence that has not
    been annotated yet (REQ-003-005, REQ-003-006 shape). ``pos_confidence``
    and ``lemma_confidence`` are independent of one another (§2.3 C2) — each
    MAY be ``None`` while the other carries a value.

    This object performs no validation itself: a caller assembling one from
    an analyzer result MUST validate a POS against ``UPOS_TAGS`` and each
    confidence against ``validate_confidence`` before construction, and MUST
    fail the run rather than clamp or coerce an invalid value (§2.3 C3,
    REQ-003-008). Keeping validation outside the constructor keeps this
    module a plain data carrier with no branch of its own to get wrong.
    """

    pos: str | None
    lemma: str | None
    pos_confidence: float | None
    lemma_confidence: float | None


def validate_confidence(value: float | None) -> None:
    """Reject a confidence outside the closed interval [0.0, 1.0] — §2.3 C1.

    ``None`` means the analyzer reported no confidence and is always valid
    (C2, C4); it is not treated as ``0.0`` or as an error.

    Raises:
        ValueError: ``value`` is not ``None`` and falls outside
            ``[0.0, 1.0]``. REQ-003-008 forbids clamping an out-of-range
            value — the caller must fail the annotation run instead.
    """
    if value is None:
        return
    if not 0.0 <= value <= 1.0:
        message = f"confidence must be within [0.0, 1.0], got {value!r}"
        raise ValueError(message)


# The per-field origin marker of REQ-003-010 R5, distinguishing an effective
# value produced by the analyzer from one produced by a manual correction.
# Both strings are far longer than the 2-3 lowercase letters the ISO-639
# guard matches, so neither trips it.
Origin = Literal["automatic", "manual"]


def resolve_effective(automatic: str | None, corrected: str | None) -> tuple[str | None, Origin]:
    """Apply spec §2.5's read-time precedence rule — the ONLY place it runs.

    Returns ``corrected`` with origin ``"manual"`` when a correction exists
    (``corrected is not None``), otherwise ``automatic`` with origin
    ``"automatic"``. The automatic value MAY itself be ``None`` for an
    unannotated occurrence with no correction.

    This function is pure and never fabricates a third value (REQ-003-010
    R1, R4): the result is always exactly one of the two inputs, unchanged.
    Building an unforgeable read model is then a matter of calling this
    inside a constructor rather than branching at every read site — a
    missing precedence check stops being a bug one can write.
    """
    if corrected is not None:
        return corrected, "manual"
    return automatic, "automatic"

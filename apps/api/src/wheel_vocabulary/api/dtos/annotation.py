"""Response DTOs for /api/v1/imports/{id}/annotation.

Strict Pydantic models corresponding one-to-one with ``annotation.v1.json``.
Extra fields are forbidden, mirroring ``dtos/imports.py``, so the schema
stays the authority on the wire shape. A contract distinct from
``import.v1.json`` (REQ-003-017): grouped by occurrence, not by normalized
form, and ``import.v1.json`` is untouched by this module.

**Naming note.** These class docstrings deliberately avoid the word this
capability's canonical dictionary headword field is named after in prose,
using the same paraphrase ``dtos/imports.py::FormFrequencyResponse`` already
established (REQ-002-007/REQ-003-023). FastAPI publishes every Pydantic
model docstring as ``components.schemas.*.description`` in the served
OpenAPI document, and ``test_no_lemma_naming.py``'s OpenAPI leg has no
docstring exemption — only the field name itself is on the allow-list, never
a sentence that merely mentions it.

REQ-003-007, REQ-003-009, REQ-003-010, REQ-003-017, REQ-003-018.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 – Pydantic resolves this at class-creation time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AnnotationOccurrenceResponse",
    "AnnotationProvenanceResponse",
    "AnnotationResultResponse",
]


class AnnotationProvenanceResponse(BaseModel):
    """Identity shared by every occurrence produced in one run (spec §2.4).

    ``None`` on the envelope when the import has never been annotated.
    Every field here is non-null once a run has completed (REQ-003-007):
    ``source``, ``model_name``, ``model_version``, ``language`` and
    ``processed_at``.
    """

    model_config = ConfigDict(extra="forbid")

    source: str
    model_name: str
    model_version: str
    language: str
    processed_at: datetime


class AnnotationOccurrenceResponse(BaseModel):
    """One occurrence's precedence-resolved annotation record (design §P3).

    ``pos``/the canonical-dictionary-headword field are the effective,
    precedence-resolved values (REQ-003-010 R1); ``automatic_pos``/its
    counterpart are the retained audit values (R4); ``pos_origin``/its
    counterpart distinguish ``automatic`` from ``manual`` per field (R5).
    Both confidence fields are always present, ``None`` included (§2.3 C5)
    — reported by the analyzer or ``None``, never fabricated (C3).
    """

    model_config = ConfigDict(extra="forbid")

    position: int
    raw_text: str
    pos: str | None
    pos_origin: Literal["automatic", "manual"]
    automatic_pos: str | None
    pos_confidence: float | None
    # Pydantic auto-titles each field by title-casing its name (e.g. "Lemma"
    # for `lemma`), and FastAPI publishes that title into the served OpenAPI
    # document — `test_no_lemma_naming.py`'s OpenAPI leg then sees a string
    # value that fails the guard's EXACT-match allow-list check ("Lemma" !=
    # "lemma"). An explicit lowercase `title=` keeps every published string
    # equal to its own allow-listed field name (REQ-003-023, design §P6).
    lemma: str | None = Field(title="lemma")
    lemma_origin: Literal["automatic", "manual"] = Field(title="lemma_origin")
    automatic_lemma: str | None = Field(title="automatic_lemma")
    lemma_confidence: float | None = Field(title="lemma_confidence")


class AnnotationResultResponse(BaseModel):
    """Response body for POST and GET /api/v1/imports/{id}/annotation."""

    model_config = ConfigDict(extra="forbid")

    id: int
    provenance: AnnotationProvenanceResponse | None
    occurrences: list[AnnotationOccurrenceResponse]

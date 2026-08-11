"""Response DTOs for /api/v1/imports.

Strict Pydantic models corresponding one-to-one with ``import.v1.json``. Extra
fields are forbidden, mirroring ``dtos/health.py``, so the schema stays the
authority on the wire shape.

``ImportResultResponse`` now declares ``id`` (cut 2, T212). Cut 1b's body
omitted it entirely — never ``"id": null`` — because no ``Book`` row existed
yet. Adding the field here is purely additive under the versioned JSON Schema
(``X-Schema-Version`` stays ``1``): a new property, not a changed one
(T1B13's resolution, completed at T209/T212). The same response shape is now
returned by both ``POST`` (creation) and ``GET`` (read) — one DTO for the
capability's one row shape.

REQ-002-001, REQ-002-006, REQ-002-008, REQ-002-012, REQ-002-018, design §9.3.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

__all__ = [
    "FormFrequencyResponse",
    "ImportErrorBody",
    "ImportErrorResponse",
    "ImportResultResponse",
]


class FormFrequencyResponse(BaseModel):
    """One row of the frequency table.

    - ``normalized_form``: the grouping key (spec §2.3). Synthetic; it may be a
      spelling that appears nowhere in the text.
    - ``display_form``: the textual form the user reads, selected per §2.5.
    - ``frequency``: occurrences in the group, always ``>= 1`` (REQ-002-017).

    Neither value is a canonical dictionary headword, and no label attached to
    either may describe it as one (REQ-002-007).
    """

    model_config = ConfigDict(extra="forbid")

    normalized_form: str
    display_form: str
    frequency: int


class ImportResultResponse(BaseModel):
    """Response body for POST /api/v1/imports and GET /api/v1/imports/{id}.

    - ``id``: the persisted import's identity (cut 2). Additive over cut 1b,
      which had no `Book` row and therefore omitted this field entirely.
    - ``import_status``: terminal only — this capability ships no intermediate
      state (REQ-002-013).
    - ``distinct_form_count``: number of rows; ``0`` is a success, not an error
      (REQ-002-012).
    - ``total_token_count``: occurrences counted; equals the sum of all
      ``frequency`` values (AC-002-08).
    - ``forms``: already ordered per §2.4. The frontend MUST NOT re-sort.
    """

    model_config = ConfigDict(extra="forbid")

    id: int
    import_status: Literal["succeeded"]
    distinct_form_count: int
    total_token_count: int
    forms: list[FormFrequencyResponse]


class ImportErrorBody(BaseModel):
    """The inner object of the error envelope.

    ``message`` is user-facing and content-free: it never carries imported text,
    a byte offset, a filesystem path, a stack trace, or an environment value
    (Art. X.2, REQ-002-013).
    """

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str


class ImportErrorResponse(BaseModel):
    """The single error envelope shared by every failure on this route."""

    model_config = ConfigDict(extra="forbid")

    error: ImportErrorBody

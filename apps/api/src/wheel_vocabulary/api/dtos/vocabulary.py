"""Strict response DTOs for the vocabulary endpoint."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["VocabularyGroupResponse", "VocabularyResponse"]


class VocabularyGroupResponse(BaseModel):
    """One grouped vocabulary entry."""

    model_config = ConfigDict(extra="forbid")

    lemma: str | None = Field(title="lemma")
    pos: str | None
    occurrence_count: int


class VocabularyResponse(BaseModel):
    """Response body for a grouped vocabulary read."""

    model_config = ConfigDict(extra="forbid")

    id: int
    group_count: int
    total_occurrence_count: int
    groups: list[VocabularyGroupResponse]

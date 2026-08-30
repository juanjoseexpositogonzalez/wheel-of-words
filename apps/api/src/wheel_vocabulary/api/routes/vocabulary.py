"""Read-only vocabulary route."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response

from wheel_vocabulary.api.dependencies import get_read_vocabulary
from wheel_vocabulary.api.dtos.vocabulary import VocabularyGroupResponse, VocabularyResponse
from wheel_vocabulary.application.imports.errors import ImportNotFoundError
from wheel_vocabulary.application.vocabulary.use_cases import (
    ReadVocabulary,  # noqa: TC001 – FastAPI resolves at runtime
)

__all__ = ["router"]

router = APIRouter(prefix="/api/v1")


@router.get("/imports/{import_id}/vocabulary", response_model=VocabularyResponse)
def read_vocabulary(
    import_id: int,
    response: Response,
    use_case: Annotated[ReadVocabulary, Depends(get_read_vocabulary)],
) -> VocabularyResponse:
    """Return the stable grouped vocabulary view for one import."""
    response.headers["X-Schema-Version"] = "1"
    groups = use_case.execute(import_id)
    if groups is None:
        raise ImportNotFoundError(import_id=import_id)
    return VocabularyResponse(
        id=import_id,
        group_count=len(groups),
        total_occurrence_count=sum(group.occurrence_count for group in groups),
        groups=[
            VocabularyGroupResponse(
                lemma=group.lemma,
                pos=group.pos,
                occurrence_count=group.occurrence_count,
            )
            for group in groups
        ],
    )

"""Read-only vocabulary route."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from wheel_vocabulary.api.dependencies import get_read_vocabulary
from wheel_vocabulary.api.dtos.vocabulary import VocabularyResponse
from wheel_vocabulary.application.imports.errors import ImportNotFoundError
from wheel_vocabulary.application.vocabulary.use_cases import (
    ReadVocabulary,  # noqa: TC001 – FastAPI resolves at runtime
)
from wheel_vocabulary.domain.annotation import UPOS_TAGS

__all__ = ["router"]

router = APIRouter(prefix="/api/v1")
_NULL_POS_SELECTOR = "null"
_POS_SELECTOR_PATTERN = rf"^(?:{'|'.join(sorted(UPOS_TAGS))}|{_NULL_POS_SELECTOR})$"


@router.get("/imports/{import_id}/vocabulary", response_model=VocabularyResponse)
def read_vocabulary(
    import_id: int,
    use_case: Annotated[ReadVocabulary, Depends(get_read_vocabulary)],
    pos: Annotated[str | None, Query(pattern=_POS_SELECTOR_PATTERN)] = None,
) -> JSONResponse:
    """Return the stable grouped vocabulary view for one import."""
    groups = use_case.execute(import_id)
    if groups is None:
        raise ImportNotFoundError(import_id=import_id)
    if pos is not None:
        selected_pos = None if pos == _NULL_POS_SELECTOR else pos
        groups = [group for group in groups if group.pos == selected_pos]
    return JSONResponse(
        content={
            "id": import_id,
            "group_count": len(groups),
            "total_occurrence_count": sum(group.occurrence_count for group in groups),
            "groups": [
                {
                    "lemma": group.lemma,
                    "pos": group.pos,
                    "occurrence_count": group.occurrence_count,
                }
                for group in groups
            ],
        },
        headers={"X-Schema-Version": "1"},
    )

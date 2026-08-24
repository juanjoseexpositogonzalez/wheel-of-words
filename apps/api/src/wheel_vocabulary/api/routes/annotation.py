"""Annotation routes — POST/GET /api/v1/imports/{id}/annotation.

Deliberately thin, mirroring `api/routes/imports.py`: each handler adapts its
plumbing to a use case or a read repository and nothing else. POST writes
via `AnnotateImport`, then reads the result back through the SAME
`AnnotationReadRepository` GET uses, so both routes always describe the
persisted state through one code path (design's data-flow diagram).

REQ-003-003 (explicit language, no default reaching this layer besides the
configured fallback), REQ-003-009 (both confidence keys always present),
REQ-003-012 (annotation is its own operation), REQ-003-017 (own contract).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, Response

from wheel_vocabulary.api.dependencies import (
    get_annotate_import,
    get_annotation_read_repository,
    get_settings,
)
from wheel_vocabulary.api.dtos.annotation import (
    AnnotationOccurrenceResponse,
    AnnotationProvenanceResponse,
    AnnotationResultResponse,
)
from wheel_vocabulary.application.annotation.use_cases import (
    AnnotateImport,  # noqa: TC001 – FastAPI resolves at runtime
)
from wheel_vocabulary.application.imports.errors import ImportNotFoundError
from wheel_vocabulary.infrastructure.persistence.annotation_repository import (
    SqlAlchemyAnnotationReadRepository,  # noqa: TC001 – FastAPI resolves at runtime
)
from wheel_vocabulary.infrastructure.settings import (
    Settings,  # noqa: TC001 – FastAPI resolves at runtime
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from wheel_vocabulary.infrastructure.persistence.annotation_repository import (
        AnnotatedOccurrence,
    )

__all__ = ["router"]

router = APIRouter(prefix="/api/v1")


def _response_body(
    book_id: int, occurrences: list[AnnotatedOccurrence]
) -> AnnotationResultResponse:
    """Build the shared response shape from a read repository result.

    `provenance` is hoisted to the envelope because one run writes one
    identity for every row it covers (design "API contract"). Read off the
    first occurrence's provenance fields when present; `None` when the
    import has never been annotated (or has zero occurrences) — the read
    repository's per-occurrence provenance columns are all `NULL` in that
    case, never fabricated as an empty-string identity.
    """
    provenance = None
    if occurrences and occurrences[0].source is not None:
        first = occurrences[0]
        provenance = AnnotationProvenanceResponse(
            source=first.source,  # type: ignore[arg-type]
            model_name=first.model_name,  # type: ignore[arg-type]
            model_version=first.model_version,  # type: ignore[arg-type]
            language=first.language,  # type: ignore[arg-type]
            processed_at=first.processed_at,  # type: ignore[arg-type]
        )
    return AnnotationResultResponse(
        id=book_id,
        provenance=provenance,
        occurrences=[
            AnnotationOccurrenceResponse(
                position=o.position,
                raw_text=o.raw_text,
                pos=o.effective_pos,
                pos_origin=o.pos_origin,
                automatic_pos=o.automatic_pos,
                pos_confidence=o.pos_confidence,
                lemma=o.lemma,
                lemma_origin=o.lemma_origin,
                automatic_lemma=o.automatic_lemma,
                lemma_confidence=o.lemma_confidence,
            )
            for o in occurrences
        ],
    )


@router.post(
    "/imports/{import_id}/annotation", status_code=201, response_model=AnnotationResultResponse
)
def create_annotation(
    import_id: int,
    response: Response,
    use_case: Annotated[AnnotateImport, Depends(get_annotate_import)],
    reader: Annotated[SqlAlchemyAnnotationReadRepository, Depends(get_annotation_read_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
    language: str | None = None,
) -> AnnotationResultResponse:
    """Annotate a previously persisted import, then return its full record.

    `language` defaults to `Settings.annotation_language` when the query
    parameter is omitted — the ONE place a language default lives
    (REQ-003-003, design §P4); the port and the use case never default it
    themselves.
    """
    response.headers["X-Schema-Version"] = "1"
    use_case.execute(import_id, language=language or settings.annotation_language)
    occurrences = reader.read(import_id)
    if occurrences is None:
        raise ImportNotFoundError(import_id=import_id)  # pragma: no cover - see note below
    return _response_body(import_id, occurrences)


@router.get("/imports/{import_id}/annotation", response_model=AnnotationResultResponse)
def read_annotation(
    import_id: int,
    response: Response,
    reader: Annotated[SqlAlchemyAnnotationReadRepository, Depends(get_annotation_read_repository)],
) -> AnnotationResultResponse:
    """Read the precedence-resolved annotation record for one import.

    Valid before any POST has ever run: every occurrence is returned with a
    `null` automatic value, origin `automatic`, and `provenance: null`
    (REQ-003-012 — annotation is its own explicit step).
    """
    response.headers["X-Schema-Version"] = "1"
    occurrences = reader.read(import_id)
    if occurrences is None:
        raise ImportNotFoundError(import_id=import_id)
    return _response_body(import_id, occurrences)

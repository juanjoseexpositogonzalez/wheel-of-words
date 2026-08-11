"""Imports routes — POST /api/v1/imports, GET+DELETE /api/v1/imports/{id}.

Deliberately thin: each adapts its plumbing to a use case and nothing else.
The ordered validation gate is application policy and lives in ``ImportText``
(Art. VII.4, design §8); the read path is `ReadImport`, which calls the SAME
`domain.frequency.build_table()` (design §1, REQ-002-006 full closure); the
delete path is `DeleteImport`, permanent and not undoable (REQ-002-011).

All handlers are plain ``def`` rather than ``async def`` so FastAPI runs them
in the threadpool. That is what lets the ``ByteStream`` port stay synchronous
and keeps the application layer free of async plumbing.

REQ-002-001, REQ-002-006, REQ-002-008, REQ-002-011, REQ-002-012, REQ-002-018.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Response, UploadFile

from wheel_vocabulary.api.dependencies import (
    get_delete_import,
    get_import_text,
    get_read_import,
)
from wheel_vocabulary.api.dtos.imports import FormFrequencyResponse, ImportResultResponse
from wheel_vocabulary.application.imports.errors import ImportNotFoundError
from wheel_vocabulary.application.imports.use_cases import (
    DeleteImport,  # noqa: TC001 – FastAPI resolves at runtime
    ImportResult,  # noqa: TC001 – used as a plain parameter type below
    ImportText,  # noqa: TC001 – FastAPI resolves at runtime
    ReadImport,  # noqa: TC001 – FastAPI resolves at runtime
)

__all__ = ["router"]

router = APIRouter(prefix="/api/v1")


def _response_body(result: ImportResult) -> ImportResultResponse:
    """Build the shared response shape from either use case's result."""
    return ImportResultResponse(
        id=result.id,
        import_status="succeeded",
        distinct_form_count=result.distinct_form_count,
        total_token_count=result.total_token_count,
        forms=[
            FormFrequencyResponse(
                normalized_form=row.normalized_form,
                display_form=row.display_form,
                frequency=row.frequency,
            )
            for row in result.forms
        ],
    )


@router.post("/imports", status_code=201, response_model=ImportResultResponse)
def create_import(
    response: Response,
    file: Annotated[UploadFile, File()],
    use_case: Annotated[ImportText, Depends(get_import_text)],
) -> ImportResultResponse:
    """Import an uploaded `.txt`, persist it, and return its ordered table.

    ``file.size`` is the byte length of the *file part*, which is exact. The
    request ``Content-Length`` is not used for this: it measures the whole
    multipart envelope, so comparing it against the limit would reject a file
    that is genuinely under it (see the deviation note in the change report).
    """
    response.headers["X-Schema-Version"] = "1"
    result = use_case.execute(
        filename=file.filename,
        content_type=file.content_type,
        stream=file.file,
        declared_size=file.size,
    )
    return _response_body(result)


@router.get("/imports/{import_id}", response_model=ImportResultResponse)
def read_import(
    import_id: int,
    response: Response,
    use_case: Annotated[ReadImport, Depends(get_read_import)],
) -> ImportResultResponse:
    """Read a previously persisted import's ordered frequency table."""
    response.headers["X-Schema-Version"] = "1"
    result = use_case.execute(import_id)
    if result is None:
        raise ImportNotFoundError(import_id=import_id)
    return _response_body(result)


@router.delete("/imports/{import_id}", status_code=204)
def delete_import(
    import_id: int,
    use_case: Annotated[DeleteImport, Depends(get_delete_import)],
) -> None:
    """Permanently delete an import and every row derived from it (REQ-002-011).

    204 with no body on success. Deleting an unknown or already-deleted id
    raises `ImportNotFoundError`, translated to the shared 404 envelope by
    `api/errors.py` — the same handler `read_import` above already uses.
    """
    use_case.execute(import_id)

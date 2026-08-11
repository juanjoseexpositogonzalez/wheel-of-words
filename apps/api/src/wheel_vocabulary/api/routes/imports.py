"""Imports route — POST /api/v1/imports.

Deliberately thin: it adapts multipart plumbing to the use case and nothing else.
The ordered validation gate is application policy and lives in ``ImportText``
(Art. VII.4, design §8).

The handler is a plain ``def`` rather than ``async def`` so FastAPI runs it in the
threadpool. That is what lets the ``ByteStream`` port stay synchronous and keeps
the application layer free of async plumbing.

REQ-002-001, REQ-002-006 (response half), REQ-002-012, REQ-002-018 (response half).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Response, UploadFile

from wheel_vocabulary.api.dependencies import get_import_text
from wheel_vocabulary.api.dtos.imports import FormFrequencyResponse, ImportResultResponse
from wheel_vocabulary.application.imports.use_cases import (
    ImportText,  # noqa: TC001 – FastAPI resolves at runtime
)

__all__ = ["router"]

router = APIRouter(prefix="/api/v1")


@router.post("/imports", status_code=201, response_model=ImportResultResponse)
def create_import(
    response: Response,
    file: Annotated[UploadFile, File()],
    use_case: Annotated[ImportText, Depends(get_import_text)],
) -> ImportResultResponse:
    """Import an uploaded `.txt` and return its ordered frequency table.

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
    return ImportResultResponse(
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

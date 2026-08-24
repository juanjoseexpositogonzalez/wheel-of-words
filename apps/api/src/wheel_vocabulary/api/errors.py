"""Exception handlers that translate import failures into the wire envelope.

Design §9.2 specifies one handler per exception class. A single handler
registered against the base class is used instead: Starlette resolves handlers
by walking ``type(exc).__mro__``, so the base catches all four subclasses, and
each subclass already carries its own ``code`` and ``http_status``. That keeps
the status mapping on the exception — one source of truth — instead of
duplicating it in a parallel table that could drift.

``INVALID_REQUEST`` is registered so that FastAPI's native ``{"detail": [...]}``
never reaches a client of this capability. That native body echoes the rejected
input, which on this route is the user's own upload metadata (Art. X.2).

**SPEC-003 task 5.5.** `AnnotationError` (`application/annotation/errors.py`)
is a SEPARATE base from `TextImportError` — `AnnotateImport` also raises
`ImportNotFoundError` (a `TextImportError`) for an unknown `book_id`, so that
case reuses `text_import_error_handler` unchanged; the three annotation-only
codes (`UNSUPPORTED_LANGUAGE`, `ANALYZER_UNAVAILABLE`, `ANNOTATION_FAILED`)
get their own handler, sharing the same `_envelope` helper and the same
`ImportErrorBody`/`ImportErrorResponse` shape — the envelope itself is
unchanged across both contracts (spec §4, design "API contract").

REQ-002-002, REQ-002-003, REQ-002-004, REQ-002-013, spec §4, design §9.2-9.3,
REQ-003-003, REQ-003-019.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from wheel_vocabulary.api.dtos.imports import ImportErrorBody, ImportErrorResponse
from wheel_vocabulary.application.annotation.errors import AnnotationError
from wheel_vocabulary.application.imports.errors import TextImportError

if TYPE_CHECKING:  # pragma: no cover - typing only
    from fastapi import FastAPI, Request

__all__ = [
    "annotation_error_handler",
    "register_error_handlers",
    "request_validation_error_handler",
    "text_import_error_handler",
]

INVALID_REQUEST_CODE = "INVALID_REQUEST"
_INVALID_REQUEST_MESSAGE = "La petición no incluye un archivo .txt válido."

# One module logger, and it emits exactly two fields. No `extra={"filename": …}`,
# no interpolated message, no `logger.exception()`: `UnicodeDecodeError.__str__`
# embeds the offending byte and its offset into the user's text, so rendering a
# traceback on the decode path would write imported content to the log
# (design §9.4, REQ-002-013). Until persistence lands in cut 2 there is no import
# id to report, so the placeholder is emitted rather than a fabricated value.
_LOGGER = logging.getLogger(__name__)
_UNKNOWN_IMPORT_ID = "-"


def _envelope(
    *, code: str, message: str, status_code: int, import_id: int | None = None
) -> JSONResponse:
    """Build the single error envelope shared by every failure on this route."""
    logged_id = import_id if import_id is not None else _UNKNOWN_IMPORT_ID
    _LOGGER.warning("code=%s import_id=%s", code, logged_id)
    body = ImportErrorResponse(error=ImportErrorBody(code=code, message=message))
    return JSONResponse(status_code=status_code, content=body.model_dump())


def text_import_error_handler(_request: Request, exc: TextImportError) -> JSONResponse:
    """Render any import failure using the code and status carried by its type.

    `import_id` (cut 2, T213/T214) is read via `getattr` because only
    `ImportNotFoundError` carries one; every other subclass fails before an
    import ever exists to have an id.
    """
    import_id = getattr(exc, "import_id", None)
    return _envelope(
        code=exc.code, message=exc.message, status_code=exc.http_status, import_id=import_id
    )


def request_validation_error_handler(
    _request: Request, _exc: RequestValidationError
) -> JSONResponse:
    """Render a malformed request without echoing anything the client submitted."""
    return _envelope(code=INVALID_REQUEST_CODE, message=_INVALID_REQUEST_MESSAGE, status_code=422)


def annotation_error_handler(_request: Request, exc: AnnotationError) -> JSONResponse:
    """Render an annotation failure using the code and status carried by its type.

    `import_id` is not read off `exc` here: none of the three subclasses
    (`UnsupportedLanguageError`, `AnalyzerUnavailableError`,
    `AnnotationFailedError`) carry one — `AnnotateImport` already logs the
    import id itself, content-free, at the point of failure (REQ-003-019).
    """
    return _envelope(code=exc.code, message=exc.message, status_code=exc.http_status)


def register_error_handlers(app: FastAPI) -> None:
    """Wire every handler onto the application, mirroring router inclusion."""
    app.add_exception_handler(TextImportError, text_import_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(AnnotationError, annotation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(
        RequestValidationError,
        request_validation_error_handler,  # type: ignore[arg-type]
    )

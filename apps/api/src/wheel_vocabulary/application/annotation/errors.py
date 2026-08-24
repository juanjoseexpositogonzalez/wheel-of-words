"""Failure taxonomy for the annotation path — spec §4.

Declared beside the port so `infrastructure` may raise these types without
`application` ever importing `infrastructure` (Art. VII.2-3), mirroring
`application/imports/errors.py`'s shape.

Messages are Spanish because they are user-visible strings (Art. VIII.4),
matching the `imports` package precedent regardless of whether the
triggering class is `User` or `Processing` (spec §4 error table). No message
here interpolates imported text, a textual form, a lemma, a corrected value,
a stack trace, a filesystem path, a model file location, or an environment
value (REQ-003-019).

REQ-003-003, REQ-003-005, REQ-003-008.
"""

from __future__ import annotations

from typing import ClassVar

__all__ = [
    "AnalyzerUnavailableError",
    "AnnotationError",
    "AnnotationFailedError",
    "UnsupportedLanguageError",
]


class AnnotationError(Exception):
    """Base for every annotation failure. Never raised directly."""

    code: ClassVar[str]
    http_status: ClassVar[int]

    @property
    def message(self) -> str:
        """Return the user-facing message. Content-free by construction."""
        return str(self)


class UnsupportedLanguageError(AnnotationError):
    """spec §4: the requested language has no installed analyzer (422, User).

    MUST be raised before any pipeline loads and before any row is written
    (REQ-003-003, AC-003-03) — never a silent fallback to English.
    """

    code: ClassVar[str] = "UNSUPPORTED_LANGUAGE"
    http_status: ClassVar[int] = 422

    def __init__(self, *, language: str) -> None:
        super().__init__(f"No hay un analizador instalado para el idioma «{language}».")
        self.language = language


class AnalyzerUnavailableError(AnnotationError):
    """spec §4: the configured model is installed but cannot be loaded (503, Processing).

    Raised by the Phase 4 adapter's mandatory load-time self-check (design
    §P1) when the loaded pipeline does not behave as expected — never
    surfaced as a user input problem.
    """

    code: ClassVar[str] = "ANALYZER_UNAVAILABLE"
    http_status: ClassVar[int] = 503

    def __init__(self) -> None:
        super().__init__("El analizador lingüístico no está disponible en este momento.")


class AnnotationFailedError(AnnotationError):
    """spec §4: the analyzer returned a malformed result (500, Processing).

    Deliberately a 500, never a 422 (spec §4): every trigger — wrong length,
    wrong order, a tag outside the UPOS set, or a confidence outside
    ``[0.0, 1.0]`` — is an adapter or model defect, never something the user
    supplied.
    """

    code: ClassVar[str] = "ANNOTATION_FAILED"
    http_status: ClassVar[int] = 500

    def __init__(self) -> None:
        super().__init__("La anotación automática produjo un resultado inválido.")

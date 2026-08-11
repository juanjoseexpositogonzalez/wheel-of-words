"""Failure taxonomy for the import path — design §9.1, spec §4.

Declared beside the ports so ``infrastructure`` may raise these types without
``application`` ever importing ``infrastructure`` (Art. VII.2-3).

Every exception here carries only safe, non-textual interpolation values: the
configured limit, the accepted extension, the expected encoding. None may ever
hold a slice of the user's text, a byte offset into it, or a filesystem path —
those reach logs and tracebacks and would leak imported content (Art. X.2,
REQ-002-013). ``InvalidEncodingError`` in particular takes no constructor
argument at all, so a ``UnicodeDecodeError`` cannot be handed to it.

Messages are Spanish because they are user-visible strings (Art. VIII.4).

REQ-002-002, REQ-002-003, REQ-002-004, REQ-002-011.
"""

from __future__ import annotations

from typing import ClassVar

__all__ = [
    "FileTooLargeError",
    "ImportNotFoundError",
    "InvalidEncodingError",
    "InvalidFileTypeError",
    "TextImportError",
]


class TextImportError(Exception):
    """Base for every import failure. Never raised directly.

    ``code`` and ``http_status`` are declared but deliberately left unset here,
    so the base cannot answer to a wire contract it does not have. The design
    named this class ``ImportError_``; that spelling violates ruff N801 and N818
    under this repository's lint configuration, and ``TextImportError`` avoids
    shadowing the builtin ``ImportError`` just as well.
    """

    code: ClassVar[str]
    http_status: ClassVar[int]

    @property
    def message(self) -> str:
        """Return the user-facing message. Content-free by construction."""
        return str(self)


class InvalidFileTypeError(TextImportError):
    """Gate 1: the filename suffix or the declared content type is unsupported."""

    code: ClassVar[str] = "INVALID_FILE_TYPE"
    http_status: ClassVar[int] = 422

    def __init__(self) -> None:
        super().__init__("Solo se admiten archivos .txt.")


class FileTooLargeError(TextImportError):
    """Gates 2 and 3: the upload exceeds ``max_import_size_bytes``."""

    code: ClassVar[str] = "FILE_TOO_LARGE"
    http_status: ClassVar[int] = 413

    def __init__(self, *, limit: int) -> None:
        super().__init__(f"El archivo supera el límite de {limit} bytes.")
        self.limit = limit


class InvalidEncodingError(TextImportError):
    """Gate 4: the bytes are not valid UTF-8.

    Takes no argument. The ``UnicodeDecodeError`` that triggers it embeds the
    offending byte and its offset into the user's text, so it must not be
    attached, chained, or interpolated (design §9.4).
    """

    code: ClassVar[str] = "INVALID_ENCODING"
    http_status: ClassVar[int] = 422

    def __init__(self) -> None:
        super().__init__(
            "El archivo debe estar codificado en UTF-8. "
            "Conviértelo a UTF-8 con tu editor de texto y vuelve a subirlo."
        )


class ImportNotFoundError(TextImportError):
    """The requested import id is unknown or already deleted."""

    code: ClassVar[str] = "IMPORT_NOT_FOUND"
    http_status: ClassVar[int] = 404

    def __init__(self) -> None:
        super().__init__("La importación solicitada no existe.")

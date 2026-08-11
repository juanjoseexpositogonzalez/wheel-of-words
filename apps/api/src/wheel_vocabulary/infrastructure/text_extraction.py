"""Strict UTF-8 extraction — design §7.3.

Adapter satisfying the ``TextExtractor`` port. Standard library only: no charset
detection dependency is added, and none is wanted. Guessing an encoding turns a
loud, fixable failure into silent mojibake that would then be tokenized,
normalized and shown to the user as vocabulary (REQ-002-004).

REQ-002-004 / AC-002-05.
"""

from __future__ import annotations

from wheel_vocabulary.application.imports.errors import InvalidEncodingError

__all__ = ["PlainTextExtractor"]

_BOM = "\ufeff"


class PlainTextExtractor:
    """Decode uploaded bytes as UTF-8, tolerating a single leading BOM."""

    def extract(self, data: bytes) -> str:
        """Return the decoded text.

        Raises:
            InvalidEncodingError: if ``data`` is not valid UTF-8. Raised with
                ``from None`` deliberately: ``UnicodeDecodeError`` embeds the
                offending byte and its offset into the user's content, and a
                chained exception renders both into every traceback and log
                record that touches it (Art. X.2, design §9.4).
        """
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            raise InvalidEncodingError() from None
        return text.removeprefix(_BOM)

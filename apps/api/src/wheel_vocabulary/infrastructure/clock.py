"""SystemClock — production implementation of the Clock port.

Wraps datetime.now(tz=datetime.UTC) so the application layer never calls the
standard library directly. This adapter lives in infrastructure because it is an
I/O boundary (wall-clock time), even though it has no side effects in the usual
sense.

REQ-PFB-CONTRACT-01 (timestamp semantics), design §6.6.
"""

from __future__ import annotations

from datetime import UTC, datetime

__all__ = ["SystemClock"]


class SystemClock:
    """Returns the current wall-clock time in UTC."""

    def now_utc(self) -> datetime:
        """Return datetime.now(tz=UTC)."""
        return datetime.now(tz=UTC)

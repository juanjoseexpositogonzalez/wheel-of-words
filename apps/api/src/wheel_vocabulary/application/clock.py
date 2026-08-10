"""Clock port — temporal abstraction for the application layer.

Defines the Clock protocol so infrastructure and API layers depend on an
abstraction, not on datetime.now() directly. This satisfies ADR-0002 (ports in
application/) and Constitution Art. VII.1 (no framework imports in application).

REQ-PFB-CONTRACT-01 (timestamp semantics), design §6.2, §6.6.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import datetime

__all__ = ["Clock"]


class Clock(Protocol):
    """Structural protocol for time sources.

    Any class that implements ``now_utc(self) -> datetime`` satisfies this
    protocol without requiring explicit inheritance.
    """

    def now_utc(self) -> datetime:
        """Return the current UTC time as a timezone-aware datetime."""
        ...

"""Application layer for the text-import capability.

Owns the import policy — the ordered validation gate, the failure taxonomy and
the ports the infrastructure adapters satisfy. Depends on ``domain`` and on the
standard library only; it never imports ``infrastructure`` or ``api``
(Art. VII.2-3, ADR-0002).
"""

from __future__ import annotations

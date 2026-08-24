"""Application layer for the annotation capability (SPEC-003).

Owns the annotation policy — the port the NLP adapter satisfies and the
failure taxonomy raised at this layer. Depends on ``domain`` and the
standard library only; it never imports ``infrastructure`` or ``api``
(Art. VII.2-3, ADR-0002).
"""

from __future__ import annotations

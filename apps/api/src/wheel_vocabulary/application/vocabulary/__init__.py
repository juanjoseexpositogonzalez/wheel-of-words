"""Application layer for the vocabulary read capability (SPEC-005).

Declares the persistence port and the use case that forwards grouped reads to
it. This package depends on the domain-facing result shape and the standard
library only; it does not import API or persistence adapters.
"""

from __future__ import annotations

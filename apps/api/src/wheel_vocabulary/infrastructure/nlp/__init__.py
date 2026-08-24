"""The NLP adapter package — spaCy lives here and nowhere else.

`domain/` and `application/` never import spaCy, thinc, or any spaCy type
(REQ-003-002, design §P6). This package is the one place that boundary is
crossed.
"""

from __future__ import annotations

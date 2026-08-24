"""The annotation port — design §7.2/P4, spec §2.6 S4, REQ-003-003.

A structural ``Protocol``, following `application/imports/ports.py`'s
shipped precedent (AMB-6): the port lives in `application/`, the pure value
object it returns lives in `domain/`. `application` never imports
`infrastructure` to obtain a conformant type — a plain stdlib double is
enough, as `test_annotation_ports.py` proves.

**Multi-language by design (ADR-0008).** `language` is a REQUIRED
keyword-only argument with NO default anywhere in this module. A second
language is a configuration and adapter concern (`Settings`, Phase 4); it
changes neither this port's signature nor the persisted schema.

**§2.6 S4.** `analyze` accepts only an already-tokenized sequence, never raw
document text — the persisted token stream is the single source of truth
for token boundaries (spec §2.6, three consequences).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Sequence

    from wheel_vocabulary.domain.annotation import LinguisticAnnotation

__all__ = ["AnalyzerIdentity", "LinguisticAnalyzer"]


@dataclass(frozen=True, slots=True)
class AnalyzerIdentity:
    """Provenance identity an analyzer reports about itself — spec §2.4.

    One call to ``analyze`` produces one identity for every row it covers:
    ``source``, ``model_name`` and ``model_version`` never vary within a
    single run. ``language`` is deliberately excluded — it is supplied by
    the caller to ``analyze``, not reported by the analyzer, so it cannot
    drift from what was actually requested.
    """

    source: str
    model_name: str
    model_version: str


@runtime_checkable
class LinguisticAnalyzer(Protocol):
    """Port for the NLP adapter that produces per-occurrence annotations.

    Any object exposing an ``identity`` attribute and a matching ``analyze``
    method satisfies this port — no base class, no import of the adapter's
    own NLP library required to write a test double (REQ-003-003).
    """

    identity: AnalyzerIdentity

    def analyze(self, tokens: Sequence[str], *, language: str) -> Sequence[LinguisticAnnotation]:
        """Return one annotation per input token, in the same order.

        ``tokens`` MUST be the already-tokenized, ordered textual forms of
        one import — never raw document text (§2.6 S4). ``language`` MUST be
        supplied explicitly; it has no default here or anywhere upstream.

        Raises:
            UnsupportedLanguageError: no analyzer is installed for
                ``language``. Raised before any pipeline loads and before
                any row is written (AC-003-03).
        """
        ...

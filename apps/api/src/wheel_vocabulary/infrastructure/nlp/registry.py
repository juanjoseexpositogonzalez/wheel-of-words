"""Language-to-adapter registry — design §P4, REQ-003-003, AC-003-03.

Adding a second language is a `Settings.analyzer_models` entry plus an
installed model — no migration, no domain or port change (design §P4). This
module is what turns that config entry into a loaded, cached
`LinguisticAnalyzer`.

**The unsupported-language check runs BEFORE anything else.** `resolve()`
looks the language up in `analyzer_models` first; only a hit ever reaches
the loader. A miss raises `UnsupportedLanguageError` without invoking the
loader at all, which is what makes "no pipeline loads and no row is written"
(AC-003-03) true by construction rather than by a downstream check that a
future edit could reorder past.

REQ-003-002 (isolation — this module imports the concrete adapter, but
nothing in `domain/` or `application/` ever imports this module: the port,
`AnalyzerRegistry` in `application/annotation/ports.py`, is what
`AnnotateImport` depends on instead).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from wheel_vocabulary.application.annotation.errors import UnsupportedLanguageError
from wheel_vocabulary.infrastructure.nlp.spacy_analyzer import SpacyLinguisticAnalyzer

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Callable, Mapping

    from wheel_vocabulary.application.annotation.ports import LinguisticAnalyzer

__all__ = ["AnalyzerRegistry"]


class AnalyzerRegistry:
    """Satisfies `application/annotation/ports.py::AnalyzerRegistry`.

    `loader` defaults to `SpacyLinguisticAnalyzer` itself (the production
    path) and is injectable so tests can prove the "never loads for an
    unsupported language" guarantee without touching spaCy at all.
    """

    def __init__(
        self,
        *,
        analyzer_models: Mapping[str, str],
        loader: Callable[[str], LinguisticAnalyzer] = SpacyLinguisticAnalyzer,
    ) -> None:
        self._analyzer_models = analyzer_models
        self._loader = loader
        self._cache: dict[str, LinguisticAnalyzer] = {}

    def resolve(self, language: str) -> LinguisticAnalyzer:
        """Return the cached or newly loaded analyzer for `language`.

        Raises:
            UnsupportedLanguageError: `language` has no entry in
                `analyzer_models`. Raised before the loader is ever called.
        """
        if language in self._cache:
            return self._cache[language]
        model_name = self._analyzer_models.get(language)
        if model_name is None:
            raise UnsupportedLanguageError(language=language)
        analyzer = self._loader(model_name)
        self._cache[language] = analyzer
        return analyzer

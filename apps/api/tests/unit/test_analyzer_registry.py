"""Unit tests for `AnalyzerRegistry` — design §P4, REQ-003-003, AC-003-03.

Written RED before `infrastructure/nlp/registry.py` exists: the import below
is the only thing that can fail at collection time.

A fake loader (never spaCy) proves the "before pipeline load" half of
AC-003-03 precisely: an unsupported language must never even call the
loader, not merely fail before a caller-visible side effect.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from wheel_vocabulary.application.annotation.errors import UnsupportedLanguageError
from wheel_vocabulary.application.annotation.ports import AnalyzerIdentity
from wheel_vocabulary.infrastructure.nlp.registry import AnalyzerRegistry

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wheel_vocabulary.domain.annotation import LinguisticAnnotation


class _FakeAnalyzer:
    """A minimal `LinguisticAnalyzer` double — no NLP import anywhere here."""

    def __init__(self, model_name: str) -> None:
        self.identity = AnalyzerIdentity(source="fake", model_name=model_name, model_version="0.0")

    def analyze(self, tokens: Sequence[str], *, language: str) -> Sequence[LinguisticAnnotation]:
        del tokens, language
        return []


class _RecordingLoader:
    """Spy standing in for `SpacyLinguisticAnalyzer` — counts every call."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def __call__(self, model_name: str) -> _FakeAnalyzer:
        self.calls.append(model_name)
        return _FakeAnalyzer(model_name)


@pytest.mark.unit
def test_resolve_returns_an_analyzer_for_a_configured_language() -> None:
    loader = _RecordingLoader()
    registry = AnalyzerRegistry(analyzer_models={"en": "en_core_web_sm"}, loader=loader)

    analyzer = registry.resolve("en")

    assert analyzer.identity.model_name == "en_core_web_sm"
    assert loader.calls == ["en_core_web_sm"]


@pytest.mark.unit
def test_resolve_caches_the_loaded_analyzer_per_language() -> None:
    """design §P4: lazy-loads AND caches — a second call must not reload."""
    loader = _RecordingLoader()
    registry = AnalyzerRegistry(analyzer_models={"en": "en_core_web_sm"}, loader=loader)

    first = registry.resolve("en")
    second = registry.resolve("en")

    assert first is second
    assert loader.calls == ["en_core_web_sm"], "the second resolve() must not reload the pipeline"


@pytest.mark.unit
def test_resolve_loads_a_distinct_pipeline_per_language() -> None:
    loader = _RecordingLoader()
    registry = AnalyzerRegistry(
        analyzer_models={"en": "en_core_web_sm", "fr": "fr_core_news_sm"}, loader=loader
    )

    en_analyzer = registry.resolve("en")
    fr_analyzer = registry.resolve("fr")

    assert en_analyzer.identity.model_name == "en_core_web_sm"
    assert fr_analyzer.identity.model_name == "fr_core_news_sm"
    assert loader.calls == ["en_core_web_sm", "fr_core_news_sm"]


@pytest.mark.unit
def test_resolve_of_an_unconfigured_language_raises_before_any_pipeline_loads() -> None:
    """AC-003-03: `UNSUPPORTED_LANGUAGE`, no fallback, and — the precise
    claim — the loader is never even invoked, so no pipeline load is
    attempted for the unsupported code."""
    loader = _RecordingLoader()
    registry = AnalyzerRegistry(analyzer_models={"en": "en_core_web_sm"}, loader=loader)

    with pytest.raises(UnsupportedLanguageError):
        registry.resolve("xx")

    assert loader.calls == [], "an unsupported language must never reach the loader"


@pytest.mark.unit
def test_resolve_of_an_unconfigured_language_carries_the_requested_language() -> None:
    registry = AnalyzerRegistry(analyzer_models={"en": "en_core_web_sm"}, loader=_RecordingLoader())

    with pytest.raises(UnsupportedLanguageError) as excinfo:
        registry.resolve("xx")

    assert excinfo.value.language == "xx"


@pytest.mark.unit
def test_resolve_never_falls_back_to_a_configured_language() -> None:
    """AC-003-03: no silent fallback to English or any other configured code."""
    loader = _RecordingLoader()
    registry = AnalyzerRegistry(analyzer_models={"en": "en_core_web_sm"}, loader=loader)

    with pytest.raises(UnsupportedLanguageError):
        registry.resolve("fr")

    assert loader.calls == []


@pytest.mark.unit
def test_registry_defaults_to_the_real_spacy_analyzer_as_its_loader() -> None:
    """The production constructor path — `SpacyLinguisticAnalyzer` itself —
    without actually loading a model (an unsupported language short-circuits
    before the default loader is ever called)."""
    registry = AnalyzerRegistry(analyzer_models={"en": "en_core_web_sm"})

    with pytest.raises(UnsupportedLanguageError):
        registry.resolve("xx")

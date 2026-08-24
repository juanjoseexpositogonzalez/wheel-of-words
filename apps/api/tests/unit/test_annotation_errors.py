"""Unit tests for the annotation error taxonomy — spec §4.

Mirrors `test_import_errors.py`'s shape: assertions are about what each
exception is allowed to *carry* (REQ-003-019 — no imported text, textual
form, lemma, corrected value, stack trace, filesystem path, model file
location, or environment value may leak through an error body), and that
each maps to its distinct wire code and HTTP status (spec §4 table).
"""

from __future__ import annotations

import pytest

from wheel_vocabulary.application.annotation.errors import (
    AnalyzerUnavailableError,
    AnnotationError,
    AnnotationFailedError,
    UnsupportedLanguageError,
)

# Closed allowlist of instance state an annotation exception may carry.
# `language` (UnsupportedLanguageError) is a bare requested-language string,
# never imported text — exactly the kind of thing this allowlist permits.
_SAFE_ATTRIBUTES = frozenset({"language"})


@pytest.mark.unit
@pytest.mark.parametrize(
    ("factory", "expected_code", "expected_status"),
    [
        (lambda: UnsupportedLanguageError(language="xx"), "UNSUPPORTED_LANGUAGE", 422),
        (AnalyzerUnavailableError, "ANALYZER_UNAVAILABLE", 503),
        (AnnotationFailedError, "ANNOTATION_FAILED", 500),
    ],
)
def test_each_error_carries_its_wire_code_and_status(
    factory: object, expected_code: str, expected_status: int
) -> None:
    """Spec §4: each failure maps to one distinct code and one HTTP status."""
    error = factory()  # type: ignore[operator]

    assert isinstance(error, AnnotationError)
    assert error.code == expected_code
    assert error.http_status == expected_status


@pytest.mark.unit
def test_base_error_declares_the_code_contract_without_a_value() -> None:
    """The base is never raised directly, so it must not answer to a code."""
    assert issubclass(AnnotationError, Exception)
    assert "code" in AnnotationError.__annotations__
    assert not hasattr(AnnotationError, "code")


@pytest.mark.unit
def test_annotation_failed_is_a_500_not_a_422() -> None:
    """Spec §4: deliberately a 500 — every trigger is an adapter/model
    defect, never something the user supplied."""
    assert AnnotationFailedError().http_status == 500


@pytest.mark.unit
def test_unsupported_language_names_the_requested_language() -> None:
    """AC-003-03: the message must be actionable, not just "invalid"."""
    error = UnsupportedLanguageError(language="xx")

    assert error.language == "xx"
    assert "xx" in error.message


@pytest.mark.unit
@pytest.mark.parametrize(
    "factory",
    [
        lambda: UnsupportedLanguageError(language="xx"),
        AnalyzerUnavailableError,
        AnnotationFailedError,
    ],
)
def test_no_error_carries_more_than_the_safe_allowlist(factory: object) -> None:
    """REQ-003-019: the only instance state permitted is the safe allowlist —
    never imported text, a lemma, a corrected value, or a filesystem path."""
    error = factory()  # type: ignore[operator]

    assert set(vars(error)) <= _SAFE_ATTRIBUTES


@pytest.mark.unit
def test_analyzer_unavailable_and_annotation_failed_carry_no_state() -> None:
    """Neither trigger has anything safe to report beyond its fixed message —
    REQ-003-019 forbids attaching the underlying adapter/model exception."""
    assert vars(AnalyzerUnavailableError()) == {}
    assert vars(AnnotationFailedError()) == {}


@pytest.mark.unit
def test_error_string_matches_the_message_property() -> None:
    """`str(exc)` reaches logs and tracebacks; `message` must be the same
    content-free text, not a separate, possibly leakier representation."""
    error = AnnotationFailedError()

    assert str(error) == error.message

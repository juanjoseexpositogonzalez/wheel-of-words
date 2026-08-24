"""Tests for `SpacyLinguisticAnalyzer` — design §P1/P2, REQ-003-003/004/016.

Written RED before `infrastructure/nlp/spacy_analyzer.py` exists: the import
below is the only thing that can fail at collection time.

**Scope note (tasks.md task 4.3, apply-phase discovery).** Task 4.3's text
bundles three things into "same file": a `1.4` confidence / `NN` tag / length
mismatch failing `ANNOTATION_FAILED` with zero rows written, and an offline
run succeeding with zero socket connections. The first three are
untestable *against the real adapter* — `en_core_web_sm`'s tagger cannot
mathematically emit a confidence outside `[0.0, 1.0]` (softmax-normalized by
construction), cannot emit a non-UPOS `pos` (`attribute_ruler` only ever
maps to the 17-tag set), and `analyze()` always returns one annotation per
input token by its own zip-based construction. Task 4.9's
`test_annotate_import.py` already re-lists these exact three failure modes
against a *stub* analyzer, which is the only place they can be genuinely
exercised — `ANNOTATION_FAILED` is raised by the caller validating the
analyzer's result (spec §4: "the analyzer returned a malformed result"),
never self-raised by the adapter. Duplicating an unreachable assertion here
would be a vacuous test, so this file implements task 4.3's third clause
(offline/network) only; the other three are covered properly in
`test_annotate_import.py` (task 4.9). Recorded per AGENTS.md §9 rather than
silently dropped or silently duplicated.

Self-check (task 4.1) is tested at two levels: the two pure predicate
functions (`_assert_scores_are_normalized`,
`_assert_decomposed_path_agrees_with_the_plain_pipeline`) are exercised
directly with synthetic arrays — fast, and precise about which condition
fails — and one real-model integration test proves the self-check actually
runs and passes at construction time, and that a genuinely corrupted model
still fails construction end to end.

REQ-003-003, REQ-003-004, REQ-003-005, REQ-003-006, REQ-003-007, REQ-003-016.
"""

from __future__ import annotations

import socket

import numpy as np
import pytest
import spacy

from wheel_vocabulary.application.annotation.errors import AnalyzerUnavailableError
from wheel_vocabulary.domain.annotation import UPOS_TAGS
from wheel_vocabulary.infrastructure.nlp.spacy_analyzer import (
    SpacyLinguisticAnalyzer,
    _assert_decomposed_path_agrees_with_the_plain_pipeline,
    _assert_scores_are_normalized,
)

_MODEL_NAME = "en_core_web_sm"


class _BlockedConnectionError(Exception):
    """Raised by the monkeypatched socket when a connection is attempted."""


@pytest.fixture
def block_outbound_sockets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fail any outbound connection attempt — AC-003-17 scenario 2."""

    def _blocked(_self: socket.socket, address: object) -> None:
        message = f"blocked outbound connection attempt to {address!r}"
        raise _BlockedConnectionError(message)

    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", _blocked)


# --------------------------------------------------------------------------
# Task 4.1 — self-check predicates, tested directly (unit, no model load).
# --------------------------------------------------------------------------


@pytest.mark.unit
def test_scores_summing_to_one_within_tolerance_pass_the_check() -> None:
    """1.0 ± 1e-4, per design §P1's mandatory self-check tolerance."""
    scores = np.array([[0.5, 0.5], [0.30000001, 0.69999999]])

    _assert_scores_are_normalized(scores)  # must not raise


@pytest.mark.unit
def test_scores_that_do_not_sum_to_one_fail_the_check() -> None:
    """Raw, un-normalized logits (design §P1's exact failure scenario)."""
    scores = np.array([[1.2, 3.4], [0.1, 0.2]])

    with pytest.raises(AnalyzerUnavailableError):
        _assert_scores_are_normalized(scores)


@pytest.mark.unit
def test_agreeing_decomposed_and_reference_pos_pass_the_check() -> None:
    _assert_decomposed_path_agrees_with_the_plain_pipeline(
        ["NOUN", "VERB"], ["NOUN", "VERB"]
    )  # must not raise


@pytest.mark.unit
def test_disagreeing_decomposed_and_reference_pos_fail_the_check() -> None:
    """A single differing tag between the two paths is enough to fail."""
    with pytest.raises(AnalyzerUnavailableError):
        _assert_decomposed_path_agrees_with_the_plain_pipeline(["NOUN", "VERB"], ["NOUN", "AUX"])


@pytest.mark.integration
def test_construction_runs_the_self_check_and_succeeds_with_the_real_model() -> None:
    """The mandatory load-time self-check (design §P1) passes for real."""
    analyzer = SpacyLinguisticAnalyzer(_MODEL_NAME)

    assert analyzer.identity.source == "spacy"
    assert analyzer.identity.model_name == _MODEL_NAME


@pytest.mark.integration
def test_a_broken_softmax_normalization_fails_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end proof the self-check is actually wired into `__init__`:
    a model whose scores never sum to 1 (simulating the `softmax_normalize`
    flip silently not taking effect) fails construction with
    `ANALYZER_UNAVAILABLE`, never a downstream range-check surprise."""
    nlp = spacy.load(_MODEL_NAME, exclude=["parser", "ner", "senter"])
    tagger = nlp.get_pipe("tagger")
    original_predict = type(tagger.model).predict

    def _unnormalized_predict(self: object, docs: object) -> list[np.ndarray]:
        return [scores * 10.0 for scores in original_predict(self, docs)]

    # `thinc.model.Model.predict` rejects instance-level assignment
    # (read-only attribute), so the class itself is patched instead.
    monkeypatch.setattr(type(tagger.model), "predict", _unnormalized_predict)

    with pytest.raises(AnalyzerUnavailableError):
        SpacyLinguisticAnalyzer(_MODEL_NAME, nlp=nlp)


# --------------------------------------------------------------------------
# Task 4.2 — pre-tokenized input, lemma grouping, PROPN, lemma_confidence.
# --------------------------------------------------------------------------


@pytest.mark.integration
def test_analyze_builds_the_doc_directly_and_never_calls_the_pipeline_as_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """§2.6 S4: `Doc(vocab, words=tokens)` only — `nlp(text)` must never run."""
    analyzer = SpacyLinguisticAnalyzer(_MODEL_NAME)

    def _forbidden_call(*_args: object, **_kwargs: object) -> None:
        message = "nlp(text) must never be called — §2.6 S4"
        raise AssertionError(message)

    monkeypatch.setattr(
        type(analyzer._nlp),  # noqa: SLF001 - test-only introspection
        "__call__",
        _forbidden_call,
    )

    result = analyzer.analyze(["run", "ran", "running"], language="en")

    assert [annotation.lemma for annotation in result] == ["run", "run", "run"]


@pytest.mark.integration
def test_inflected_forms_share_one_lemma_while_keeping_distinct_forms() -> None:
    """AC-003-06: `run`/`ran`/`running` all lemmatize to `run`."""
    analyzer = SpacyLinguisticAnalyzer(_MODEL_NAME)

    result = analyzer.analyze(["run", "ran", "running"], language="en")

    assert [annotation.lemma for annotation in result] == ["run", "run", "run"]
    for annotation in result:
        assert annotation.pos in UPOS_TAGS


@pytest.mark.integration
def test_a_proper_noun_is_persisted_as_propn_unfiltered() -> None:
    """AC-003-23: no filter, no suppression — PROPN comes through like any tag."""
    analyzer = SpacyLinguisticAnalyzer(_MODEL_NAME)

    result = analyzer.analyze(["Alice", "went", "home"], language="en")

    assert result[0].pos == "PROPN"


@pytest.mark.integration
def test_lemma_confidence_is_always_null_never_derived_from_pos_confidence() -> None:
    """design §P1: `EnglishLemmatizer` is rule-based and exposes no probability."""
    analyzer = SpacyLinguisticAnalyzer(_MODEL_NAME)

    result = analyzer.analyze(["run", "ran", "running", "Alice"], language="en")

    assert all(annotation.lemma_confidence is None for annotation in result)
    assert any(annotation.pos_confidence is not None for annotation in result)


@pytest.mark.integration
def test_analyze_of_an_empty_token_sequence_returns_an_empty_sequence() -> None:
    """REQ-003-004: zero input tokens is a valid, degenerate case — a book
    with zero occurrences must not crash the pipeline (the empty `scores`
    array from `tagger.model.predict` skips both `argmax` and
    `set_annotations`, which would otherwise raise on a `(0, n_labels)`
    array)."""
    analyzer = SpacyLinguisticAnalyzer(_MODEL_NAME)

    assert analyzer.analyze([], language="en") == []


@pytest.mark.unit
def test_the_normalization_check_is_a_no_op_for_an_empty_score_array() -> None:
    """The self-check's own predicate must not divide-by-zero or crash on
    the same degenerate empty-book case."""
    _assert_scores_are_normalized(np.empty((0, 50)))  # must not raise


@pytest.mark.integration
def test_the_same_surface_form_takes_different_tags_in_different_contexts() -> None:
    """AC-003-05 scenario 2 / ADR-0006, design §2.1 L6, §2.2 P5: this is the
    scenario that actually proves POS is per-occurrence and contextual,
    driven through the REAL adapter — not a hand-seeded storage fixture like
    the `saw` rows in `test_annotation_read_repository.py`, which only prove
    the storage/precedence layer honours whatever `pos` it is given, never
    that the analyzer itself is contextual.

    `saw` is the exact word design §2.1 L6/REQ-003-020's own docstring names
    as the canonical example: the past tense of "see" (VERB) in one context,
    a cutting tool (NOUN) in another. Both sentences fit inside the tagger's
    own ±4-token receptive field (design §P2), so no sentence-boundary
    recovery is needed for either tag to be assigned correctly."""
    analyzer = SpacyLinguisticAnalyzer(_MODEL_NAME)

    verb_result = analyzer.analyze(["I", "saw", "him", "yesterday"], language="en")
    noun_result = analyzer.analyze(["I", "cut", "wood", "with", "a", "saw"], language="en")

    assert verb_result[1].pos == "VERB"
    assert noun_result[5].pos == "NOUN"


@pytest.mark.integration
def test_every_pos_confidence_is_within_the_closed_unit_interval() -> None:
    """§2.3 C1: bounded by construction, never a raw logit."""
    analyzer = SpacyLinguisticAnalyzer(_MODEL_NAME)

    result = analyzer.analyze(["The", "quick", "brown", "fox", "jumped"], language="en")

    for annotation in result:
        assert annotation.pos_confidence is not None
        assert 0.0 <= annotation.pos_confidence <= 1.0


# --------------------------------------------------------------------------
# Task 4.3 (third clause) — offline, zero network connections.
# --------------------------------------------------------------------------


@pytest.mark.integration
def test_construction_and_analysis_succeed_with_outbound_network_disabled(
    block_outbound_sockets: None,
) -> None:
    """AC-003-17: model load and analysis both complete with zero socket
    connection attempts. Any attempt would raise `_BlockedConnectionError`
    from the monkeypatched `socket.socket`, failing this test."""
    del block_outbound_sockets
    analyzer = SpacyLinguisticAnalyzer(_MODEL_NAME)

    result = analyzer.analyze(["run"], language="en")

    assert result[0].lemma == "run"

"""The spaCy adapter — design §P1/P2, REQ-003-003/004/005/006/007/016.

This is the ONLY module in the tree that imports spaCy or a spaCy type
(REQ-003-002, design §P6). It satisfies `LinguisticAnalyzer`
(`application/annotation/ports.py`) structurally — no inheritance.

**P1 — confidence.** `en_core_web_sm`'s tagger emits raw affine logits at
inference (`build_tagger_model(..., normalize=False)` is thinc's default;
`thinc/layers/softmax.py::forward` only normalizes when
`softmax_normalize or is_train`). At construction this adapter flips
`tagger.model.get_ref("softmax").attrs["softmax_normalize"] = True` and then
runs ONE tok2vec pass feeding both the scores and the tag assignment, so
`pos_confidence` is provably the posterior of the tag actually assigned —
never a value read from a separate, potentially diverging forward pass.
`lemma_confidence` is always `None`: `en_core_web_sm`'s lemmatizer factory is
registered with `default_config={"mode": "rule"}`
(`spacy/lang/en/__init__.py`), a deterministic rule+lookup component that
exposes no probability of any kind. Deriving one from `pos_confidence` would
be fabrication (§2.3 C3) and this module does not do it.

**Mandatory load-time self-check (§P1).** `softmax_normalize` is a thinc
attribute name, not a spaCy API guarantee, so `__init__` probes one synthetic
doc and asserts (a) every score row sums to `1.0 ± 1e-4` and (b) the
decomposed path assigns the same `pos_` as a plain `nlp(doc)` run on the same
tokens. Either failure raises `AnalyzerUnavailableError`, converting a silent
semantic corruption (logits published as probabilities) into a loud, testable
failure. The two predicates are standalone functions so they can be unit
tested with synthetic arrays, independent of loading a real model.

**P2 — pre-tokenized input.** `analyze()` builds `Doc(nlp.vocab,
words=tokens, spaces=[True] * n)` directly and never calls `nlp(text)`
(§2.6 S4) — spaCy's own tokenizer never runs, so the persisted token
boundaries (`REQ-002-005`) stay the single source of truth. `parser`, `ner`
and `senter` are excluded at load: none of them are needed (the tagger's
`HashEmbedCNN.v2` window is fixed at ±4 tokens with no sentence-boundary
feature, and the rule lemmatizer reads `text`/`pos_` only), and excluding
them means annotating a punctuation-free stream (SPEC-002 T6) never trips a
missing-sentence-boundary code path that does not exist here.

REQ-003-002 (isolation), REQ-003-003 (port conformance), REQ-003-004
(1:1 length/order — `analyze` zips tokens to annotations by construction),
REQ-003-005 (UPOS via `attribute_ruler`, never a fine-grained tag),
REQ-003-006 (lemma verbatim as the analyzer emits it — L3), REQ-003-007
(provenance identity), REQ-003-016 (offline — `spacy.load` reads only
installed site-packages, no download path).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import numpy as np
import spacy
from spacy.tokens import Doc

from wheel_vocabulary.application.annotation.errors import AnalyzerUnavailableError
from wheel_vocabulary.application.annotation.ports import AnalyzerIdentity
from wheel_vocabulary.domain.annotation import LinguisticAnnotation

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Sequence

    from spacy.language import Language
    from spacy.tokens import Token


__all__ = ["SpacyLinguisticAnalyzer"]

# A handful of ordinary tokens is enough to probe the tagger's own labels —
# the self-check only needs the model to disagree with itself, not a
# representative corpus.
_SELF_CHECK_TOKENS: tuple[str, ...] = ("The", "quick", "brown", "fox", "jumps")
_SCORE_SUM_TOLERANCE = 1e-4
_EXCLUDED_PIPES = ("parser", "ner", "senter")


def _assert_scores_are_normalized(scores: np.ndarray) -> None:
    """§P1 self-check leg 1: every row of `scores` sums to `1.0 ± 1e-4`.

    Raises `AnalyzerUnavailableError` — never a bare assertion — because a
    failed check here means the deployed model cannot be trusted to report a
    real posterior, which is a runtime availability problem (503), not a
    programming error.
    """
    if scores.size == 0:
        return
    if not bool(np.allclose(scores.sum(axis=1), 1.0, atol=_SCORE_SUM_TOLERANCE)):
        raise AnalyzerUnavailableError()


def _assert_decomposed_path_agrees_with_the_plain_pipeline(
    decomposed_pos: Sequence[str], reference_pos: Sequence[str]
) -> None:
    """§P1 self-check leg 2: the manually decomposed forward pass must assign
    the exact same `pos_` as calling every pipe in sequence would."""
    if list(decomposed_pos) != list(reference_pos):
        raise AnalyzerUnavailableError()


class SpacyLinguisticAnalyzer:
    """Satisfies `LinguisticAnalyzer` (`application/annotation/ports.py`).

    `nlp` may be injected for tests that need to tamper with an already
    -loaded pipeline (e.g. corrupting `tagger.model.predict` to prove the
    self-check actually fails end to end) without paying for a second real
    model load.
    """

    def __init__(self, model_name: str, *, nlp: Language | None = None) -> None:
        self._nlp = nlp if nlp is not None else spacy.load(model_name, exclude=_EXCLUDED_PIPES)
        # spaCy's own type stubs declare `Language.get_pipe` as
        # `Callable[[Doc], Doc]` regardless of the actual pipe class, which is
        # too narrow for the tagger-specific `.model` access below. `cast` is
        # a deliberate, narrow escape from that stub gap — this module is the
        # sole place spaCy is imported at all (REQ-003-002), so the
        # imprecision cannot leak into `domain/` or `application/`.
        self._tok2vec = cast("Any", self._nlp.get_pipe("tok2vec"))
        self._tagger = cast("Any", self._nlp.get_pipe("tagger"))
        self._attribute_ruler = cast("Any", self._nlp.get_pipe("attribute_ruler"))
        # No leading underscore: "lemmatizer" is the exact allow-listed
        # symbol (REQ-003-023, `_ALLOWED_LEMMA_SYMBOLS`) — "_lemmatizer"
        # is not, since the guard matches identifiers by exact equality,
        # never a substring or prefix/suffix variant.
        self.lemmatizer = cast("Any", self._nlp.get_pipe("lemmatizer"))
        # design §P1: flip the tagger's own output layer back to the
        # normalized form it was trained with. `softmax_normalize=False` is
        # purely an inference shortcut (argmax is softmax-invariant); this
        # does not invent a number, it completes the model's own forward pass.
        self._tagger.model.get_ref("softmax").attrs["softmax_normalize"] = True
        self.identity = AnalyzerIdentity(
            source="spacy", model_name=model_name, model_version=str(self._nlp.meta["version"])
        )
        self._run_self_check()

    def analyze(self, tokens: Sequence[str], *, language: str) -> Sequence[LinguisticAnnotation]:
        """Return one annotation per input token, in the same order.

        `language` is accepted but unused by this single-pipeline adapter —
        `infrastructure/nlp/registry.py` is what maps a language code to the
        correct `SpacyLinguisticAnalyzer` instance (design §P4); by the time
        this method runs, the caller has already resolved the right pipeline.
        """
        del language
        doc, scores = self._annotate(tokens)
        return [
            LinguisticAnnotation(
                pos=token.pos_ or None,
                # `token.lemma` (the vocab-hash form, not the `_`-suffixed
                # string form) is the allow-listed exact symbol "lemma"
                # (REQ-003-023); the string is recovered through
                # `vocab.strings`, spaCy's own hash-to-text table.
                lemma=doc.vocab.strings[token.lemma] or None,
                pos_confidence=float(scores[index].max()) if scores.size else None,
                lemma_confidence=None,  # design §P1: rule-based lemmatizer, no probability
            )
            for index, token in enumerate(doc)
        ]

    def _annotate(self, tokens: Sequence[str]) -> tuple[Doc, np.ndarray]:
        """The one decomposed forward pass — shared by `analyze()` and the
        self-check, so they can never drift apart (design §P1)."""
        doc = self._build_doc(tokens)
        self._tok2vec(doc)
        scores: np.ndarray = self._tagger.model.predict([doc])[0]
        if scores.size:
            tag_ids = scores.argmax(axis=1)
            self._tagger.set_annotations([doc], np.asarray([tag_ids]))
        self._attribute_ruler(doc)
        self.lemmatizer(doc)
        return doc, scores

    def _build_doc(self, tokens: Sequence[str]) -> Doc:
        """§2.6 S4: pre-tokenized input only — `nlp(text)` never runs."""
        return Doc(self._nlp.vocab, words=list(tokens), spaces=[True] * len(tokens))

    def _run_self_check(self) -> None:
        """design §P1: mandatory at load. Both legs use `_SELF_CHECK_TOKENS`
        through the same `_annotate` path `analyze()` uses, so a pass here is
        evidence about the real code path, not a separate one."""
        doc, scores = self._annotate(_SELF_CHECK_TOKENS)
        _assert_scores_are_normalized(scores)

        reference_doc = self._build_doc(_SELF_CHECK_TOKENS)
        for _name, pipe in self._nlp.pipeline:
            reference_doc = pipe(reference_doc)
        _assert_decomposed_path_agrees_with_the_plain_pipeline(
            [_pos_of(token) for token in doc], [_pos_of(token) for token in reference_doc]
        )


def _pos_of(token: Token) -> str:
    return token.pos_

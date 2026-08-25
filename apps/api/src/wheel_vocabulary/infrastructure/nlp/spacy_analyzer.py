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
doc and asserts (a) every score row is finite, non-negative, and sums to
`1.0 ± 1e-4` (S5 — a real probability distribution, not merely a value that
happens to sum to `1.0`) and (b) the decomposed path assigns the same `pos_`
as running THIS SAME already-loaded, already-`_EXCLUDED_PIPES`-reduced
`Language` object's own `pipeline` would (never spaCy's full default
pipeline — see `_assert_decomposed_path_agrees_with_the_plain_pipeline`'s
docstring for exactly what leg (b) can and cannot catch, S2). Either failure
raises `AnalyzerUnavailableError`, converting a silent semantic corruption
(logits published as probabilities) into a loud, testable failure. The two
predicates are standalone functions so they can be unit tested with
synthetic arrays, independent of loading a real model.

**P2 — pre-tokenized input.** `analyze()` builds `Doc(nlp.vocab,
words=tokens, spaces=[True] * n)` directly and never calls `nlp(text)`
(§2.6 S4) — spaCy's own tokenizer never runs, so the persisted token
boundaries (`REQ-002-005`) stay the single source of truth. `ner` and
`senter` are excluded at load: neither is needed (`REQ-003-005` never
persists a named-entity label, and the tagger's `HashEmbedCNN.v2` window is
fixed at ±4 tokens with no sentence-boundary feature), and excluding them
means annotating a punctuation-free stream (SPEC-002 T6) never trips a
missing-sentence-boundary code path that does not exist here.

**`parser` is ALSO excluded — known, measured, deliberately deferred
defect (S2, `judgment-day` remediation, `docs/decisions-log.md` 2026-08-25
entry).** An earlier revision of this docstring justified excluding
`parser` the same way as `ner`/`senter` ("none of them are needed"). That
was factually wrong: `attribute_ruler` (which this adapter DOES run) reads
the `DEP` label — the syntactic dependency relation `parser` is the only
pipe that ever populates — for several rules, including the exact ones that
distinguish a main-verb `be`/`have`/`do` (`VERB`, when `DEP` is `ROOT` or a
handful of clausal relations) from an auxiliary (`AUX`, the DEP-agnostic
fallback). Without `parser`, `DEP` is always unset, so those rules can
never fire: `"She has a cat"`'s `has` is tagged `AUX` here, where the same
model's full pipeline tags it `VERB`. Measured on 3 short declarative
sentences: 3/15 tokens differ, each at `pos_confidence` 0.998–0.9999 —
high-confidence WRONG UPOS tags, not low-confidence uncertainty. Measured
cost of re-including `parser` (median of 5 runs, 10,000-token synthetic
`Doc`): wall time +30%, peak RSS +19% at 30,000 tokens — a real
product/architecture tradeoff on top of the already-tracked ~2.3 GB/300k
token memory footprint, not a free fix, which is why it is recorded as a
deferred decision rather than applied silently.

REQ-003-002 (isolation), REQ-003-003 (port conformance), REQ-003-004
(1:1 length/order — `analyze` zips tokens to annotations by construction),
REQ-003-005 (UPOS via `attribute_ruler`, never a fine-grained tag — known
exception: main-verb `be`/`have`/`do` publish `AUX` instead of `VERB`, see
S2 above), REQ-003-006 (lemma verbatim as the analyzer emits it — L3),
REQ-003-007 (provenance identity), REQ-003-016 (offline — `spacy.load`
reads only installed site-packages, no download path).
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
    """§P1 self-check leg 1: every row of `scores` is a real probability
    distribution — finite, non-negative, and summing to `1.0 ± 1e-4`.

    Raises `AnalyzerUnavailableError` — never a bare assertion — because a
    failed check here means the deployed model cannot be trusted to report a
    real posterior, which is a runtime availability problem (503), not a
    programming error.

    S5 remediation: the sum-tolerance check alone accepts a non-probability
    such as `[1.0, -1.0, 1.0]`, which sums to exactly `1.0` while containing
    a negative entry no real softmax output could ever produce — publishing
    it as `pos_confidence` would be a silent semantic corruption identical
    in kind to the un-normalized-logits case this self-check already exists
    to catch. Finiteness and non-negativity are checked FIRST, before the
    sum is computed: this also means a NaN/Inf row (already indirectly
    rejected by the sum check, since `nan`/`inf` taints `.sum()` and
    `np.allclose` treats NaN as never close) is now caught by its own
    explicit, warning-free assertion instead of relying on that incidental
    floating-point behaviour.
    """
    if scores.size == 0:
        return
    if not bool(np.all(np.isfinite(scores))):
        raise AnalyzerUnavailableError()
    if not bool(np.all(scores >= 0.0)):
        raise AnalyzerUnavailableError()
    if not bool(np.allclose(scores.sum(axis=1), 1.0, atol=_SCORE_SUM_TOLERANCE)):
        raise AnalyzerUnavailableError()


def _assert_decomposed_path_agrees_with_the_plain_pipeline(
    decomposed_pos: Sequence[str], reference_pos: Sequence[str]
) -> None:
    """§P1 self-check leg 2: the manually decomposed forward pass
    (`_annotate`, called directly by `analyze()`) must assign the exact same
    `pos_` as running the pipeline through spaCy's own `pipe(doc)` calling
    convention would, for the SAME loaded `Language` object.

    **What this does NOT verify (S2, `judgment-day` remediation).**
    `reference_pos` is produced by iterating `self._nlp.pipeline` (see
    `_run_self_check` below) — `self._nlp` is ALREADY the reduced pipeline
    `_EXCLUDED_PIPES` produced, so both sides of this comparison run the
    identical set of pipes. This leg proves the manual decomposition is
    self-consistent with the loaded `Language` object's own iteration order;
    it CANNOT catch a pipe being wrongly excluded in the first place (e.g.
    `parser`, and the main-verb `be`/`have`/`do` mistagging that causes,
    `docs/decisions-log.md` 2026-08-25) — that would require a SEPARATE
    reference built from the model's UNREDUCED pipeline, which this function
    is never given.
    """
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
                # C6 + R1: echoes the exact token this annotation was
                # computed for, at its own position in `doc` — never the
                # caller's input list — so a caller can verify the pairing
                # by identity rather than trusting bare position or content
                # alone. `source_index` is `index` itself: `doc`'s own
                # iteration order IS the position each token occupied in the
                # `tokens` sequence this method received (`_build_doc`
                # constructs `doc` directly from that sequence, in order).
                raw_text=token.text,
                source_index=index,
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
        evidence about the real code path, not a separate one.

        Leg 2's `reference_doc` is built from `self._nlp.pipeline` — the
        SAME already-`_EXCLUDED_PIPES`-reduced `Language` object `_annotate`
        itself uses, not a second, unreduced pipeline. This makes leg 2
        tautological with respect to which pipes were excluded at load: see
        `_assert_decomposed_path_agrees_with_the_plain_pipeline`'s own
        docstring for exactly what it does and does not verify (S2).
        """
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

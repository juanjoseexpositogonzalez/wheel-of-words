# Design: SPEC-003 — Lemmatization and per-occurrence POS

Capability `003-lemmatization-pos`. Satisfies `REQ-003-001` … `REQ-003-023` and the `AC-002-10` delta.

> **Size note.** This document exceeds the usual 800-word design budget. The orchestrator's mandate
> enumerates six problems (P1–P6) that must be resolved explicitly, and P1 in particular cannot be
> answered honestly in a sentence. Hand-waving any of them to hit a word count would be the worse
> failure. Decisions are tabulated; prose is reserved for the non-obvious.

## Technical Approach

Annotation is a **second pass over persisted data**, never part of import (§2.6). `AnnotateImport`
reads `Occurrence.raw_text` ordered by `position`, hands the whole sequence to a `LinguisticAnalyzer`
port, validates the result in memory, then writes it in **one transaction**. A spaCy adapter builds
`Doc(vocab, words=tokens)` directly — spaCy's tokenizer never runs. Manual corrections win **at read
time** because the read model has no unresolved field to forget to check.

---

## P1 (RESOLVED) — Where confidence actually comes from

This was the highest-risk open question. The orchestrator's framing is correct: `token.prob` is
useless here (`en_core_web_sm-3.8.0` ships `"vectors": {"width": 0, "vectors": 0, "keys": 0}`, so
`prob` is `0.0` for every token). Below is what the pipeline *does* expose, verified against source.

### `pos_confidence` — a real model posterior, obtainable

Verified facts:

| Fact | Evidence |
|---|---|
| `spacy.Tagger.v2` = `chain(tok2vec, Softmax_v2)`, with `model.set_ref("softmax", output_layer)` | `spacy/ml/models/tagger.py` |
| The tagger is trained with `SequenceCategoricalCrossentropy` — it *is* a softmax classifier | `spacy/pipeline/tagger.pyx::get_loss` |
| **`build_tagger_model(..., normalize=False)` by default**, and thinc's forward is `normalize = attrs["softmax_normalize"] or is_train` | `thinc/layers/softmax.py::forward` |
| ⇒ **at inference the tagger emits raw affine logits, NOT probabilities** | same — `is_train=False`, attr `False` |
| `Tagger.predict()` argmaxes and discards the scores | `tagger.pyx::_scores2guesses` |

So the naive "take the softmax max of `tagger.model.predict()`" is **wrong as written** — it would
read logits as if they were probabilities and could emit values outside `[0.0, 1.0]`, tripping
`REQ-003-008`'s own range check.

**Decision.** At adapter load, flip the tagger's own output layer back to its trained, normalized
form and read the posterior from the same forward pass that assigns the tag:

```python
tagger = nlp.get_pipe("tagger")
tagger.model.get_ref("softmax").attrs["softmax_normalize"] = True   # emit the trained distribution

# One tok2vec pass feeds BOTH the scores and the assignment — they cannot diverge.
nlp.get_pipe("tok2vec")(doc)                     # populates the tagger's listener for this batch
scores = tagger.model.predict([doc])[0]          # (n_tokens, n_labels), rows sum to 1.0
tag_ids = scores.argmax(axis=1)
tagger.set_annotations([doc], [tag_ids])         # public API, mirrors Tagger.__call__
nlp.get_pipe("attribute_ruler")(doc)             # tag_ -> pos_ (UPOS)
nlp.get_pipe("lemmatizer")(doc)                  # rule-based, consumes pos_
pos_confidence = float(scores[i].max())
```

**Precise semantics — this is what the number means, and it is testable.**
`pos_confidence` is the tagger's posterior probability for the **fine-grained (Penn Treebank) tag it
assigned**, in `[0.0, 1.0]` by construction. `en_core_web_sm` tags 50 fine labels (`NN`, `VBD`, …)
and `attribute_ruler` maps the assigned fine tag to the UPOS we persist. Because ≥1 fine tag maps to
each UPOS, this value is a **lower bound on P(UPOS | context), not necessarily a strict one** — it
never overstates confidence, and where more than one fine tag maps to the same UPOS it systematically
*understates* it (`NN` vs `NNS`, `VBD` vs `VBN` both mean `NOUN`/`VERB`). **The bound is not strict
for every UPOS category, though.**

**Correction (R4, Judgment Day round 2).** An earlier revision of this section claimed `MD → AUX`,
`UH → INTJ`, `CD → NUM` and `WRB → SCONJ` each had "exactly one POS-setting rule" and were therefore
all exact. That reasoning checked the wrong direction: showing that `MD` maps *only* to `AUX` says
nothing about whether `AUX` is reachable from *other* fine tags too — exactness requires the reverse,
that `AUX` (the target) is reachable from *only* `MD` (the source), globally, across the whole rule
table. Enumerating `en_core_web_sm`'s pinned `attribute_ruler.patterns` directly (179 rules total)
settles it:

| Target UPOS | Rules | Distinct fine tags feeding it | Exact? |
|---|---|---|---|
| `AUX` | 20 | `MD`, `VB`, `VBP`, `VBN`, `VBG`, `VBZ`, `VBD` (7 tags) | **No** |
| `SCONJ` | 3 | `WRB`, `IN` (2 tags) | **No** |
| `INTJ` | 1 | `UH` (1 tag) | **Yes** |
| `NUM` | 1 | `CD` (1 tag) | **Yes** |

Only `UH → INTJ` and `CD → NUM` are genuine singletons — for those two, and only those two,
`pos_confidence` **equals** `P(UPOS | context)` exactly. `MD → AUX` and `WRB → SCONJ` are two of
several tags feeding a shared target, so `pos_confidence` still *understates* `P(AUX | context)` and
`P(SCONJ | context)` respectively, exactly like the general `NN`/`NNS` case above — verified through
the real adapter (`SpacyLinguisticAnalyzer._annotate`), summing the softmax row over every fine-tag
column that `attribute_ruler` would resolve to the same target UPOS for the actual word encountered:
`"is"` → `AUX`, tag `VBZ`, `pos_confidence=0.999807` vs measured `P(AUX)=0.999810` (diff `3e-6`, from
residual `MD` probability mass); `"since"` → `SCONJ`, tag `IN`, `pos_confidence=0.987158` vs measured
`P(SCONJ)=0.988532` (diff `1.4e-3`, from residual `WRB` mass) — while `"Wow"` → `INTJ` and a bare `"3"`
→ `NUM` both measured `diff=0.0` exactly, confirming the two genuine singletons.

`CC → CCONJ` remains a separate, ALSO-exact case, by a different mechanism than "only one rule
targets it": it has one narrow lexical exception — `LOWER: "but", DEP: "advmod"` → `ADV` — but that
rule can never fire in THIS adapter's actual runtime, since `parser` is excluded and `DEP` is
therefore always unset (§P2 above); `CC` is effectively exact here too, though its exactness comes
from an unreachable exception rather than the rule table simply having no exception at all.

That understatement — where it exists (`AUX`, `SCONJ`, and every other non-singleton UPOS) — is a
known property, not a defect, and MUST be stated in the release notes and reflected in the UI label.
Reporting the exact UPOS posterior would require marginalising over a `tag → UPOS` table for every
category, not only the two genuine singletons; deferred (OQ-1) because it buys accuracy in a place
that does not change which tag is shown.

**Nothing is fabricated.** Setting `softmax_normalize = True` does not invent a number: it asks the
model to complete its own trained forward pass. `normalize_outputs=False` is purely an inference
shortcut (argmax is invariant under softmax). Satisfies `C1`, `C3`.

**Mandatory load-time self-check.** `softmax_normalize` is a thinc attribute name, not a spaCy API
guarantee. The adapter MUST probe one synthetic doc at load and assert every score row sums to
`1.0 ± 1e-4` **and** that the decomposed path assigns the same `pos_` as a plain `nlp(doc)` run on
the same tokens. Failure raises `ANALYZER_UNAVAILABLE` (503). This converts a silent semantic
corruption — logits published as probabilities — into a loud, testable failure.

### `lemma_confidence` — honestly `NULL`, and I am not inventing one

`spacy/lang/en/__init__.py` registers the `lemmatizer` factory with `default_config={"mode": "rule"}`
→ `EnglishLemmatizer` is a deterministic rule + lookup-table component. It exposes **no probability
of any kind**. `en_core_web_sm`'s pipeline contains no `trainable_lemmatizer`.

Therefore `lemma_confidence` is **`NULL` for every occurrence** produced by the English pipeline.
This is exactly the case `C2` (independence), `C3` (never fabricate) and `C4` (`NULL` ≠ `0.0`) were
written for. Deriving it from `pos_confidence` — tempting, since the rule lemmatizer consumes
`pos_` — would be fabrication under `C3` and is forbidden. If a pipeline carrying
`trainable_lemmatizer` (an `EditTreeLemmatizer`, a softmax classifier) is ever installed, the adapter
reports its posterior the same way. **That is an adapter capability, not a schema change.**

Product consequence, stated plainly: for one cycle every row shows a real POS confidence and an
explicit "not reported" lemma marker. `REQ-003-009`'s AC-003-09 scenario ("one row with both
confidences null") is exercised with a stub analyzer, since the real English adapter never emits a
null POS confidence.

---

## P2 (RESOLVED) — Pre-tokenized input and the sentence-boundary question

`Doc(nlp.vocab, words=[o.raw_text for o in occurrences], spaces=[True] * n)`. Never `nlp(text)`.
Constructing `Doc` directly also sidesteps `Language.max_length`, which only guards `nlp(text)`.

**Sentence boundaries do not need to be recovered, and this is verifiable, not a hope.**
`en_core_web_sm`'s tagger sits on `spacy.HashEmbedCNN.v2` with `window_size=1, depth=4` — a
fixed-window CNN with a ±4-token receptive field, **no recurrence and no sentence-boundary feature**.
The components that consume or produce sentence boundaries are `parser` and `senter`; both are
excluded (`spacy.load(..., exclude=["parser", "ner", "senter"])`). The rule lemmatizer reads
`token.text` and `token.pos_` only. Pinned by a test: setting `sent_start` on the doc changes no
`tag_`.

**The real tradeoff is different, worse, and irreversible — and I accept it explicitly.**
SPEC-002's tokenizer discards every token without an `L*` character (`tokenizer.py::_contains_letter`,
rule T6). **The persisted stream contains no punctuation at all.** The tagger therefore sees prose
with no sentence-final period, no comma, no quote. The model card's `tag_acc: 0.973` was measured on
OntoNotes *with* punctuation; accuracy on this stream will be measurably lower, concentrated at
sentence junctions where a clause-final verb abuts a following capitalised subject.

| Option | Verdict |
|---|---|
| Re-tokenize from source text | Impossible — `Book` stores only `content_hash`; and forbidden by §2.6 S3 |
| Inject synthetic punctuation | Forbidden — breaks `REQ-003-004`'s 1:1 length/order contract |
| Accept the degraded signal | **Chosen.** `REQ-002-005` boundaries are normative; `REQ-003-013` requires annotating from persisted data alone |

This is the accepted cost of `REQ-003-013`. It must be recorded in the release notes. It is also
coherent with PV-2: `pos_confidence` is precisely the channel through which the missing punctuation
becomes visible to the user.

---

## P3 (RESOLVED) — Read-time precedence, by construction

Two repositories in **two modules**, because that is what makes `R3` checkable by a static AST
guard rather than only a runtime assertion. That guard is bounded to the string-construction
patterns it recognises (exact match, substring, `+`-concatenated literal chains) — an f-string,
`str.join`, or `%`-formatted string assembling the forbidden name would currently evade it
(Judgment Day round 2, R3). "Structurally provable" is a stronger claim than a finite AST
pattern-matcher can make against arbitrary string construction; see
`infrastructure/persistence/annotation_write_repository.py`'s own module docstring for the
corrected, bounded claim.

`infrastructure/persistence/annotation_repository.py` (read) issues one query per import:

```sql
SELECT o.position, o.raw_text, o.pos, o.lemma,
       cp.corrected_value, cl.corrected_value,
       a.source, a.model_name, a.model_version, a.language,
       a.processed_at, a.pos_confidence, a.lemma_confidence
FROM occurrence o
LEFT JOIN annotation_provenance a ON a.occurrence_id = o.id
LEFT JOIN manual_correction cp ON cp.occurrence_id = o.id AND cp.field = 'pos'
LEFT JOIN manual_correction cl ON cl.occurrence_id = o.id AND cl.field = 'lemma'
WHERE o.book_id = :book_id
ORDER BY o.position
```

Precedence is **not** resolved in SQL (untestable without a DB) but in one pure domain function:

```python
# domain/annotation.py — stdlib only
def resolve_effective(automatic: str | None, corrected: str | None) -> tuple[str | None, str]:
    """R1/R4/R5: the correction wins; the automatic value stays recoverable."""
    return (corrected, "manual") if corrected is not None else (automatic, "automatic")
```

**Why no branch can be forgotten (R1).** The read model `AnnotatedOccurrence` has **no field holding
an unresolved value**. It exposes `effective_pos` / `pos_origin` / `automatic_pos` — there is no
`pos` attribute a caller could return by accident. Resolution happens in `__post_init__`, so
constructing the object *is* applying precedence. A missing check is not a bug you can write; it is
a field that does not exist.

**Why the write path cannot corrupt a correction (R2/R3).**
`annotation_write_repository.py` never imports `ManualCorrection`. An AST test asserts that module's
import set and attribute references exclude it — the literal `AC-003-11` third scenario. Splitting
read from write into separate modules is what makes that assertion cheap and exact.

---

## P4 (RESOLVED) — Multi-language port, zero English hardcoded

Port lives in `application/`, per the shipped precedent (`application/imports/ports.py` holds
`runtime_checkable Protocol`s) and §5 AMB-6 — not in `domain/`.

```python
# application/annotation/ports.py
@runtime_checkable
class LinguisticAnalyzer(Protocol):
    def identity(self) -> AnalyzerIdentity: ...
    def analyze(self, tokens: Sequence[str], *, language: str) -> Sequence[LinguisticAnnotation]: ...
```

`language` is a required keyword argument with **no default** — `AC-003-03`'s "no language default".
The domain-isolation guard's language-parameter ban is scoped to `domain/` and does not bind this.

Adding a second language is a **configuration + adapter** change with **no migration**:

| Layer | Multi-language mechanism |
|---|---|
| `Settings` | `annotation_language: str = "en"`, `analyzer_models: dict[str, str] = {"en": "en_core_web_sm"}`. `REQ-003-003` explicitly requires the default to live here |
| `infrastructure/nlp/registry.py` | `resolve(language) -> LinguisticAnalyzer`; lazy-loads and caches one pipeline per code. Miss ⇒ `UnsupportedLanguageError` **before** any pipeline loads and before any write |
| Schema | `annotation_provenance.language` is a plain `String` column, not an enum, not a table |

`Settings` is neither the port, the value object, nor the schema, so `AC-003-03`'s ISO-639 ban does
not reach it — and `REQ-003-003` mandates the default live there. No contradiction.

---

## P5 (RESOLVED) — Migration, backfill, atomicity

**One additive revision** `0003_annotation` (`down_revision = "0002_book_occurrence"`):

| Object | Definition |
|---|---|
| `occurrence.lemma` | `sa.Text()`, nullable. Added via `op.batch_alter_table` |
| `annotation_provenance` | `id` PK; `occurrence_id` FK **UNIQUE**; `source`, `model_name`, `model_version`, `language` `String` NOT NULL; `processed_at` `DateTime` NOT NULL; `pos_confidence`, `lemma_confidence` `Float` NULL |
| `manual_correction` | `id` PK; `occurrence_id` FK; `field` `String(16)`; `corrected_value` `Text`; `corrected_at` `DateTime`; **UNIQUE(`occurrence_id`, `field`)**. Schema only (R6) |

`batch_alter_table` for both add and drop: bare `ALTER TABLE … DROP COLUMN` needs SQLite ≥ 3.35, and
`downgrade()` must work unconditionally (`AC-003-16`). Nothing SPEC-002 created is dropped, renamed,
retyped, or made non-nullable.

**Atomicity (`REQ-003-014`) — ordering first, rollback second.**

```
read occurrences  →  analyze WHOLE sequence  →  validate ALL  →  ┌ BEGIN ────────────┐
(no transaction)     (no transaction)          (no transaction)  │ DELETE provenance │
                                                                 │ UPDATE occurrence │
                                                                 │ INSERT provenance │
                                                                 └ COMMIT ───────────┘
```

The analyzer runs and every annotation is validated (length, order, UPOS membership, confidence
range) **before the transaction opens**. A stub that fails after the first token (`AC-003-15`) fails
while zero rows have been touched — atomicity holds by ordering, and the transaction is the second
line of defence, not the only one. Cost: one 150k-token import holds ~150k small frozen dataclasses
in memory (tens of MB). Accepted; streaming with incremental commits would violate `REQ-003-014`.

**Batch-size independence (`REQ-003-021`) — a trap that must not be sprung.** Batching may govern
the occurrence **read** and the `executemany` **write** chunks. It MUST NOT chunk the analyzer call:
the tagger's ±4-token window would be cut at chunk boundaries and two batch sizes would produce
different tags, failing `AC-003-22` for a correct reason. **The analyzer receives the entire import
as one `Doc`.** This is a hard constraint, not a preference.

**Backfill.** No data migration. `REQ-003-013` is satisfied by the same code path: `POST` the
annotation endpoint for a pre-existing `book_id`; the ordered `raw_text` stream is already complete.

---

## P6 (RESOLVED) — Naming under the five-leg guard

Two module-naming decisions shrink the allow-list rather than expand it (§7 leaves module names to
`sdd-design`):

- Package is **`application/annotation/`**, not `application/lemmatization/`. The Python guard reports
  `ast.ImportFrom` as `("imported module", "<full dotted path>")`, so `…application.lemmatization.ports`
  would need one brittle allow-list entry **per module**. `annotation` matches nothing.
- Adapter is `infrastructure/nlp/spacy_analyzer.py` — no match.

**Landmine (would otherwise fail CI on cut 2).** `test_domain_isolation.py` flags any 2–3 lowercase
string literal as ISO-639-shaped. The literal `"pos"` matches. Therefore `domain/annotation.py` MUST
NOT contain the bare literal `"pos"`: the `field` discriminator (`Literal["pos", "lemma"]`) lives in
`application/annotation/`, and `resolve_effective` takes values, not field names. The 17 UPOS tags are
uppercase and match nothing.

### Allow-list content (exact names, case-sensitive equality — not `in`, not `startswith`)

```python
# tests/unit/test_no_lemma_naming.py — REQ-003-023
_ALLOWED_LEMMA_SYMBOLS = frozenset({
    "lemma",             # Occurrence.lemma; LinguisticAnnotation.lemma; effective wire key
    "lemma_confidence",  # provenance column, value-object field, wire key
    "lemma_origin",      # automatic|manual marker (R5)
    "automatic_lemma",   # retained audit value (R4)
    "lemmatizer",        # spaCy pipe name, string literal in the adapter
})
```

```ts
// apps/web/tests/contracts/no-lemma-naming.test.ts — same exact-match rule
const ALLOWED_LEMMA_SYMBOLS = new Set(["lemma", "lemma_confidence", "lemma_origin", "automatic_lemma"]);
```

Every entry denotes a genuine lemma produced by a real lemmatizer. `lemma_form` is still caught;
`normalized_form` renamed to `lemma_text` is still caught; a message string `"lemma missing"` is
still caught. No path exclusion, no directory exclusion, no pattern relaxation, still AST-based.

### Two coverage gaps the narrowing MUST close, not inherit

| Gap | Fix |
|---|---|
| `_MIGRATION_PATH` is hardcoded to `0002_book_occurrence.py`, so `sa.Column("lemma", …)` in `0003` escapes the guard | Glob `migrations/versions/*.py` |
| The reflected-column leg iterates only tables `("book", "occurrence")`, so `annotation_provenance.lemma_confidence` escapes | Iterate every table in `Base.metadata` |

Narrowing the guard while silently shrinking its reach would violate `AC-003-24`'s "still covers
every previously covered file" in spirit. Both fixes ship **with** the allow-list.

UI note: the Spanish singular label `"Lema"` matches none of `lemma|lemas|lexeme|lexema` and passes
naturally; the plural `"Lemas"` **does** match and would need an allow-list entry. Prefer the
singular column header.

---

## Data Flow

```
POST /api/v1/imports/{id}/annotation
        │
        ▼
  AnnotateImport (application)
        │  1. read raw_text ORDER BY position        ──→ AnnotationReadRepository
        │  2. registry.resolve(language)             ──→ UNSUPPORTED_LANGUAGE (422) if absent
        │  3. analyze(tokens, language=…)  [whole import, one Doc]
        │        └─ SpacyLinguisticAnalyzer ─ Doc(vocab, words) → tok2vec → tagger(scores)
        │                                     → attribute_ruler → lemmatizer   [no network]
        │  4. validate all (length/order, UPOS ∈ 17, confidence ∈ [0,1])
        │        └─ any failure ⇒ ANNOTATION_FAILED (500), zero rows touched
        │  5. ┌ ONE TRANSACTION ┐  DELETE provenance → UPDATE occurrence → INSERT provenance
        ▼
GET /api/v1/imports/{id}/annotation
        │
        ▼  AnnotationReadRepository — one LEFT JOIN query
           → resolve_effective(automatic, corrected) per field   [domain, pure]
           → AnnotatedOccurrence(effective_*, *_origin, automatic_*)
```

## File Changes

| File | Action | Description |
|---|---|---|
| `apps/api/pyproject.toml`, `apps/api/.python-version` | Modify / Create | `requires-python = ">=3.12,<3.14"`; add `spacy`, `en_core_web_sm` |
| `.github/workflows/*` | Modify | Pin CI to 3.12 |
| `domain/annotation.py` | Create | `LinguisticAnnotation`, `UPOS_TAGS`, `resolve_effective`. Stdlib only, no `"pos"` literal |
| `application/annotation/{ports,errors,use_cases}.py` | Create | `LinguisticAnalyzer`, `AnalyzerIdentity`; 3 new errors; `AnnotateImport` |
| `infrastructure/nlp/{registry,spacy_analyzer}.py` | Create | Language→adapter registry; spaCy adapter. No spaCy type escapes |
| `infrastructure/persistence/models.py` | Modify | `Occurrence.lemma`; `AnnotationProvenance`; `ManualCorrection` |
| `infrastructure/persistence/annotation_write_repository.py` | Create | Transactional write. **Never imports `ManualCorrection`** |
| `infrastructure/persistence/annotation_repository.py` | Create | Read model + precedence join |
| `migrations/versions/0003_annotation.py` | Create | Additive, reversible |
| `infrastructure/settings.py` | Modify | `annotation_language`, `analyzer_models` |
| `api/routes/annotation.py`, `api/dtos/annotation.py`, `api/schemas/annotation.v1.json` | Create | New contract; `import.v1.json` untouched |
| `api/{dependencies,errors,main}.py` | Modify | Wiring + 3 error codes |
| `tests/unit/test_no_lemma_naming.py` | Modify | Allow-list + 2 coverage-gap fixes |
| `tests/unit/test_domain_isolation.py` | Modify | Forbidden imports += `thinc`, `stanza` |
| `apps/web/src/types/annotation.ts`, `api/annotation.ts`, `components/AnnotationTable.tsx` | Create | Render verbatim; total UPOS label map |
| `apps/web/tests/contracts/no-lemma-naming.test.ts`, `no-linguistic-rules.test.ts` | Modify | Allow-list; extend module manifest |

## Interfaces / Contracts

```python
# domain/annotation.py — frozen, stdlib only (REQ-003-002)
@dataclass(frozen=True, slots=True)
class LinguisticAnnotation:
    raw_text: str  # C6 remediation — the token this annotation was computed for
    pos: str | None
    lemma: str | None
    pos_confidence: float | None
    lemma_confidence: float | None
```

**C6 remediation (post-implementation correction).** The original shape above
omitted `raw_text`, so `AnnotateImport._validate_and_assemble` paired tokens to
annotations with `zip(tokens, annotations, strict=True)` — verified only by
list position and length, never by content. A same-length analyzer result
that violated its own "same order" contract (`ports.py::LinguisticAnalyzer.
analyze`) would be silently written to the wrong occurrence, with no error and
no log entry — a real-corpus-breaking defect REQ-003-004's "ordering
mismatch… MUST fail the run with `ANNOTATION_FAILED`" clause already required
to be caught but nothing implemented. `raw_text` lets the caller compare the
token it asked about against the one the analyzer says it answered for, at
each position, and fail loudly on a mismatch instead of trusting position
alone.

`GET /api/v1/imports/{id}/annotation` (`X-Schema-Version: 1`, `annotation.v1.json`):

```json
{
  "id": 7,
  "provenance": { "source": "spacy", "model_name": "en_core_web_sm",
                  "model_version": "3.8.0", "language": "en", "processed_at": "..." },
  "occurrences": [
    { "position": 3, "raw_text": "ran",
      "pos": "VERB", "pos_origin": "automatic", "automatic_pos": "VERB",
      "lemma": "run", "lemma_origin": "automatic", "automatic_lemma": "run",
      "pos_confidence": 0.98, "lemma_confidence": null }
  ]
}
```

Provenance **identity** is hoisted to the envelope because one run writes one identity for every row
by construction, so per-occurrence recoverability is preserved while 150k rows do not repeat four
strings. **Storage stays per-occurrence** as §2.4 mandates. Confidences stay per row — they are
per-token. Both confidence keys are always present, `null` included (`C5`).

## Testing Strategy

| Layer | What | How |
|---|---|---|
| Unit (pure) | `resolve_effective` precedence, UPOS membership, `""`→`NULL`, range checks | pytest + Hypothesis; no DB, no model |
| Unit (structural) | Domain isolation (+`thinc`/`stanza`); write path never references corrections; narrowed naming guard both legs; no `PROPN` special case; no confidence thresholding | AST walks, extending existing guards |
| Unit (use case) | 6 stub-analyzer failure modes: short return, `NN`, `1.4`, whitespace lemma, mid-run raise, unsupported language | Fake analyzer + fake repo |
| Integration (DB) | `0003` upgrade/downgrade over SPEC-002 data; atomicity; batch/read-order independence; re-run stability; seeded correction survives reprocessing | pytest `integration`, real SQLite |
| Integration (model) | **Softmax self-check**: rows sum to 1.0; decomposed path `pos_` == plain `nlp(doc)` `pos_`; `run/ran/running` → `run`; `PROPN` persisted; offline with sockets blocked; no source build | `@pytest.mark.integration`, real `en_core_web_sm` |
| Contract | `import.v1.json` byte-identical; full SPEC-002 suite green; annotation body validates | jsonschema + existing suite |
| Frontend | Verbatim render, unmapped tag degrades to raw tag, null vs numeric distinguishable without colour, keyboard-navigable | Vitest + Testing Library |

Coverage: `domain/` and `application/` ≥ 90% (both are pure and stub-driven), global ≥ 80%.

## Threat Matrix

No shell, subprocess, VCS/PR automation, executable-file classification, or process-integration
boundary is introduced. The one new HTTP route is covered by the spec's own error contract (§4) and
`REQ-003-019`.

| Boundary | Applicability |
|---|---|
| Documentation-like paths | **N/A** — no file classification; annotation takes an integer `book_id`, never a path or upload |
| Git repository selection | **N/A** — no VCS interaction |
| Commit state | **N/A** — no VCS interaction |
| Push state | **N/A** — no VCS interaction |
| PR commands | **N/A** — no subprocess or command composition |

Model loading reads only from installed `site-packages` via `spacy.load`, with no download path and
no network (`REQ-003-016`, pinned by a socket-blocking test).

## Migration / Rollout

One additive revision; `downgrade()` returns to the SPEC-002 baseline. Rollback = revert child PRs
newest-first to the tracker branch, `alembic downgrade -1`, drop `spacy`, unpin the interpreter.
No feature flag: annotation is a new endpoint, so not calling it *is* the off state.

## Delivery — the proposed 3-cut shape is broken; re-cut to 5

**Ordering defect, must be fixed before `sdd-tasks` plans.** Proposed cut 1 ("pin + domain/port
foundation") introduces `LinguisticAnnotation.lemma` inside `_PACKAGE_ROOT.rglob("*.py")`, but the
`AC-002-10` guard narrowing (`REQ-003-023`) is assigned to cut 2. **Cut 1 lands red.** The guard
narrowing MUST precede the first `lemma` symbol.

Honest estimate of the proposed cut 2 (adapter + migration + use case + write repo + atomicity +
guard narrowing), at this repo's actual test-to-code ratio: **~1,400 lines, ≈3.5× the 400 budget.**

Recommended chain (feature-branch-chain onto the SPEC-003 tracker branch):

| # | Slice | Est. | Rationale |
|---|---|---|---|
| 1 | Python 3.12 pin + **guard narrowing** (allow-list, both legs, 2 coverage-gap fixes) + domain-isolation extension | ~250 | Pure infra/test. Lands the guard **before** any `lemma` symbol, so every later slice is green on arrival |
| 2 | `domain/annotation.py` + `application/annotation/{ports,errors}.py` + property tests | ~300 | Pure, stdlib-only, no DB, no model |
| 3 | Migration `0003` + persistence models + write repo + read repo | ~400 | Schema and both repositories; write/read module split proves R3 |
| 4 | spaCy adapter + registry + `Settings` + `AnnotateImport` | ~400 | Carries the P1 softmax self-check and the atomicity tests |
| 5 | API route + DTOs + `annotation.v1.json` + frontend | ~400 | Only slice touching `apps/web` |

**Decision needed before apply: Yes** (3 cuts → 5).
**Chained PRs recommended: Yes.**
**400-line budget risk: High** — slice 4 is the tightest; if it exceeds budget, split the adapter
from the use case along the port boundary.

## Open Questions

- [ ] **OQ-1** — Should `pos_confidence` marginalise over the `tag → UPOS` map to report the exact
      UPOS posterior instead of the fine-tag lower bound? Deferred: it needs an `attribute_ruler`
      probe table, some of whose patterns are context-dependent, and it never changes the tag shown.
      Revisit if users report the value reads as implausibly low.
- [ ] **OQ-2** — `GET …/annotation` returns every occurrence and §7 defers pagination, so a
      150k-token novel produces a very large body. The read model is written streaming-capable so
      pagination is additive later, but the first real novel will expose this. Flag for SPEC-004.
- [x] **OQ-3** — Confirmed during slice 1 that `uv python pin 3.12` installs `spacy 3.8.15` and its
      resolved `thinc 8.3.13` from cp312 wheels with **zero** source compilation, per `AC-003-01`'s
      third scenario. `requires-python` is bounded at `<3.14` (spaCy's own wheel ceiling, not
      thinc's — see spec.md §5 FACT-1); `.python-version` stays pinned to exactly `3.12` as the
      tested interpreter.

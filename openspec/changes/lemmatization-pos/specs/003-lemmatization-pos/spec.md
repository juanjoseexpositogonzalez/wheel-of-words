# Capability 003-lemmatization-pos

This is the specification for capability `003-lemmatization-pos`: per-occurrence lemma and
part-of-speech annotation, its provenance and confidence, and the read-time precedence mechanism
that makes reprocessing safe.

It is a **new capability**, so this document is a full specification, not a delta. One separate
delta accompanies it — `../002-text-import/spec.md` — and it modifies exactly one requirement of
`002-text-import`. See §5 `CONTRA-1` for why that delta is unavoidable and why it is the *only*
change made to SPEC-002.

Section numbers `§2`, `§2.x`, `§4`, `§5` referenced inside the requirements refer to the sections
of this document. References of the form `§2.x` prefixed with `SPEC-002` refer to
`openspec/specs/002-text-import/spec.md`.

## 1. Metadata

| Field | Value |
|-------|-------|
| Capability | `003-lemmatization-pos` |
| Requirement prefix | `REQ-003-###` |
| Acceptance prefix | `AC-003-##` |
| Roadmap item | 4 — Lematización y POS (`docs/product-vision.md` §12) |
| Governing constitution | v2.0.0 (2026-07-15, multi-language amendment 2026-07-16) |
| Governing ADRs | 0001, 0002, 0003, 0005, 0006, 0007, 0008, 0009 |
| Language | English (methodology artifact, ADR-0010). Product docs stay Spanish. |
| Test runner | `cd apps/api && uv run pytest` — strict TDD, zero-warning `filterwarnings` gate |
| Depends on | `002-text-import` (archived, 23 requirements) |

### 1.1 Glossary alignment (ADR-0010: `docs/glossary.md` is Spanish)

English terms used here for the canonical Spanish glossary entries, cited once and not renamed
thereafter: **lema** = *lemma*; **categoría gramatical contextual** = *contextual part of speech*;
**aparición** = *occurrence*; **procedencia** = *provenance*; **puntuación de confianza** =
*confidence score*; **corrección manual** = *manual correction*; **reprocesamiento** =
*reprocessing*; **forma textual** = *textual form*; **forma normalizada** = *normalized form*.

**On the word `lemma`.** `REQ-002-007` forbids the tokens `lemma|lemas|lexeme|lexema` in naming and
contract surface. That prohibition is scoped by its own opening sentence to values *"introduced by
this capability"* — meaning capability `002-text-import`. It exists because a **normalized form is
not a lemma** and must not be mislabelled as one. This capability introduces a **genuine lemma**,
computed by a real lemmatizer. Naming it `lemma` is therefore the *honest* name, and is precisely
what `REQ-002-007` was protecting: it keeps the two concepts distinguishable rather than collapsing
them. `normalized_form` and `display_form` are untouched, keep their names, and keep their meaning.

The `002-text-import` **guard implementation** does not know about capability boundaries, so it must
be narrowed. That is a real, resolvable conflict, not a naming argument — see §5 `CONTRA-1` and
`REQ-003-023`.

---

## 2. Annotation contract (normative)

`REQ-002-005` pinned tokenization and normalization here because they change what the user sees and
Art. I.4 forbids resolving ambiguity in code. The same standard applies to annotation. Everything in
this section is normative and binding on the domain, the port, the adapter, the schema, and the API.

### 2.1 Three distinct values, never conflated

Each `Occurrence` carries three separately named, separately stored, non-interchangeable values.

| Value | Column | Definition | Computed by | Language-dependent |
|-------|--------|------------|-------------|--------------------|
| Textual form | `raw_text` | The verbatim source slice, per SPEC-002 §2.2 T1–T10 | `domain/text/tokenizer.py` (stdlib) | No |
| Normalized form | `normalized_text` | The synthetic grouping key of SPEC-002 §2.3 N1–N5 | `domain/text/normalizer.py` (stdlib) | No |
| **Lemma** | `lemma` | The canonical dictionary headword for this occurrence's **contextual reading**, as produced by the active `LinguisticAnalyzer` for the corpus language | NLP adapter | **Yes** |

Consequences, all binding:

| # | Rule | Reason |
|---|------|--------|
| L1 | The lemma MUST NOT be produced by `normalize()`, nor derived from `normalized_text`, nor stored in either existing column | They answer different questions. `normalize()` is a deterministic stdlib grouping key; a lemma is a model-produced linguistic claim. Conflating them would make provenance meaningless — there would be nothing to attribute |
| L2 | Annotation MUST NOT modify `raw_text`, `normalized_text`, or `position` on any row | Those are `REQ-002-005`'s output and the contract SPEC-002 already ships. Rewriting them would break `AC-002-24` (display forms must be verbatim source slices) |
| L3 | The lemma MUST be stored **verbatim as the analyzer emits it** — no casefolding, no NFC pass, no joiner folding, no trimming beyond L4 | Applying SPEC-002's normalization to a lemma would silently mix two pipelines. It would also destroy `PROPN` capitalization, which is data item 6 needs |
| L4 | An empty or whitespace-only lemma MUST be stored as `NULL`, never as `""` | `NULL` means "no lemma available". `""` is a value that claims a lemma exists and is empty. The two must stay distinguishable |
| L5 | A lemma MAY be a string that occurs nowhere in the imported text (`ran` → `run`), and MAY equal the textual form | This is what a lemma *is*. It is the opposite of `display_form`, which `REQ-002-018` requires to occur verbatim in the source. The two are not comparable and MUST NOT be validated against each other |
| L6 | The lemma is recorded **per occurrence**, never per normalized form and never per book | `saw` is `see` (VERB) in one sentence and `saw` (NOUN) in another. A lemma attached to the normalized form `saw` would have to pick one and lose the other — the same information loss ADR-0006 rejects for POS |

### 2.2 The POS tag set — Universal POS (UPOS)

`Occurrence.pos` MUST hold a **Universal POS (UPOS) tag**, drawn from this fixed 17-value set and
from no other:

```
ADJ  ADP  ADV  AUX  CCONJ  DET  INTJ  NOUN  NUM
PART PRON PROPN PUNCT SCONJ SYM  VERB  X
```

| # | Rule | Reason |
|---|------|--------|
| P1 | The persisted value MUST be one of the 17 tags above, uppercase, exactly as written | A closed, enumerable set is verifiable. An open string column is not |
| P2 | A language- or model-specific fine-grained tagset (Penn Treebank, spaCy `tag_`, STTS) MUST NOT be persisted in `pos` | Penn Treebank is English-specific. Persisting it would hardcode English into the schema and break ADR-0008's "multi-language by design" the first time a second language is added. UPOS is cross-linguistic and shared by spaCy and Stanza, which is exactly what keeps the adapter swappable (ADR-0001/0002) |
| P3 | A value outside the 17-tag set MUST be rejected at the application boundary and MUST fail the annotation run with `ANNOTATION_FAILED`. It MUST NOT be silently stored, silently dropped, or silently coerced to `X` | `X` already means "the model could not classify this". Coercing an out-of-set value to `X` would hide an adapter defect behind a legitimate-looking tag. Art. VIII.3 forbids swallowing it |
| P4 | `PROPN` MUST be persisted like every other tag. No filter, no suppression, no special case ships in this capability | Decision: proper-noun handling is roadmap item 6. Filtering here would pre-empt that capability's design with an unreviewed heuristic. See §6 PV-4 and §7 |
| P5 | POS is recorded **per occurrence**. No entity introduced by this capability MAY carry a global or aggregate POS field, and `pos` MUST NOT appear on `Book` or on any lemma-level entity | ADR-0006 and Art. V.2–3. Aggregate POS distributions are derived on query, never stored |
| P6 | `PUNCT`, `SYM` and `SPACE`-like tags are unreachable in practice — SPEC-002 T6 discards any token without an `L*` character — but MUST NOT be rejected if the analyzer emits them for a letter-bearing token | Forbidding a legal UPOS tag would be a rule invented here with no linguistic basis |

### 2.3 Confidence — derivation, range, and meaning

| # | Rule | Reason |
|---|------|--------|
| C1 | `pos_confidence` and `lemma_confidence` are each a `float` in the **closed interval `[0.0, 1.0]`**, or `NULL` | A bounded, dimensionless score is comparable across models. An unbounded logit is not |
| C2 | The two are **independent**. Either MAY be `NULL` while the other carries a value | The tagger and the lemmatizer are separate pipeline components with different observability. A rule-based lemmatizer exposes no probability while a statistical tagger does |
| C3 | Confidence MUST be **reported by the analyzer or be `NULL`**. The domain, the application, the API, and the frontend MUST NOT compute, estimate, smooth, default, or otherwise fabricate a confidence value | Art. V.7 says automatic results store confidence *"cuando proceda"* — when applicable. A fabricated number is worse than no number: it looks like evidence and is not |
| C4 | `NULL` confidence means **"the pipeline reported none"**. It MUST NOT be read, rendered, or documented as `0.0`, as low confidence, or as an error | These are three different facts. Collapsing them destroys the one signal the value exists to carry |
| C5 | Confidence MUST be present on **every** annotated occurrence returned by the API, including when `NULL`. The response key MUST be present with a JSON `null`; it MUST NOT be omitted | Decision 2: confidence is always visible. An absent key is indistinguishable from an unannotated occurrence |
| C6 | In this capability confidence is **informational only**. No filter, sort, threshold, warning, block, or automatic re-run MAY key off it | Acting on low confidence requires a correction path, which is SPEC-004. See §5 `AMB-2` — this is a knowingly accepted tradeoff with a recorded consequence, not an oversight |

### 2.4 Provenance

Every automatic annotation MUST carry provenance (Art. V.7, ADR-0007 point 3, glossary
*Procedencia*). Provenance is recorded **per occurrence**, not per field: one analyzer pass produces
both `pos` and `lemma` under one model identity, so a per-`(occurrence, field)` record would
duplicate identical data and invite the two copies to drift apart.

Normative content — the *storage layout* (dedicated table, shared run row, or inline columns) is
`sdd-design`'s decision, but every field below MUST be recoverable for any annotated occurrence:

| Field | Meaning | Nullable |
|-------|---------|----------|
| `source` | Stable adapter identifier, e.g. `spacy` | No |
| `model_name` | Loaded pipeline identifier, e.g. `en_core_web_sm` | No |
| `model_version` | The pipeline's own version string | No |
| `language` | The language code of the pipeline that produced this annotation | No |
| `processed_at` | UTC timestamp of the annotation run | No |
| `pos_confidence` | §2.3 | Yes |
| `lemma_confidence` | §2.3 | Yes |

**`language` is stored per annotation, never assumed.** This is the single mechanism that keeps the
schema multi-language under ADR-0008. `Book.language` remains unset in this capability (detection is
deferred, OQ-2), so the annotation record is the only place that states which language pipeline
actually ran. Storing it makes a future mixed-language corpus representable without a migration.

Reproducibility (Art. VI.1–2): the same token sequence, the same `source`, `model_name`,
`model_version` and `language` MUST produce the same `pos` and `lemma`.

### 2.5 Read-time precedence — the mechanism that makes reprocessing safe

Art. V.8–9 and ADR-0007 require that a manual correction wins and that reprocessing never silently
overwrites one. This capability satisfies both **by construction rather than by a conditional
check**, and that distinction is the whole point of this section.

The effective value of a field is defined as:

```
effective(occurrence, field) =
    ManualCorrection[occurrence, field].corrected_value   if such a row exists
    Occurrence.<field>                                    otherwise   (MAY be NULL)
```

where `field ∈ {pos, lemma}`.

| # | Rule | Reason |
|---|------|--------|
| R1 | Precedence MUST be applied on **every read** of an effective value, without exception | This is what makes the correction win permanently rather than until the next write |
| R2 | Precedence MUST NOT be applied at write time. The annotation write path MUST write automatic values **unconditionally** | A write-time check is a branch, and a branch can be forgotten, mis-ordered, or bypassed by a bulk update. The read-time rule has no branch to get wrong |
| R3 | The annotation write path MUST NOT insert, update, delete, or read any `ManualCorrection` row | Anything it cannot touch, it cannot corrupt |
| R4 | The automatic value MUST be retained after a correction exists, as the audit/shadow value | ADR-0007 point 1: retained for auditability, not applied as the effective value |
| R5 | Every read that exposes an effective value MUST also expose a per-field **origin marker** distinguishing `automatic` from `manual` | Without it a user cannot tell why a value differs from the pipeline output — the deficiency ADR-0007 flags in its Negative consequences |
| R6 | No code path in this capability writes a `ManualCorrection` row. The table ships with schema only | The write path and its UX are SPEC-004 (ADR-0007 OQ-1 is still open) |

**Why R6 is deliberate and not a half-measure.** Shipping the precedence mechanism one cycle before
the write path means the invariant is *proved working* against seeded corrections before any user can
create one. SPEC-004 then builds on a mechanism with passing tests instead of introducing the
mechanism and its first consumer simultaneously — which is exactly the situation in which the
"reprocessing overwrote my work" defect ADR-0007 exists to prevent gets shipped.

### 2.6 Annotation is a separate step from import

**Resolved contract boundary. Binding.**

| # | Rule |
|---|------|
| S1 | `POST /api/v1/imports` MUST NOT run annotation. Its request handling, response body, error behaviour, timing characteristics, and persisted rows are unchanged by this capability |
| S2 | Annotation MUST run as its own explicit operation over an already-persisted import |
| S3 | Annotation MUST consume the persisted token stream as-is: `Occurrence.raw_text` ordered by `Occurrence.position`, filtered to one `book_id`. It MUST NOT re-tokenize, and MUST NOT call `tokenize()` or `normalize()` |
| S4 | The analyzer MUST receive **pre-tokenized** input and MUST NOT be given raw document text |

**Three consequences, all load-bearing:**

1. **`REQ-002-010` stays literally true for capability `002-text-import`.** That requirement says
   `Occurrence.pos` is `None` "for every row written by this capability". Import still writes `None`.
   Annotation is a different capability writing later. **No MODIFIED delta is emitted against
   `REQ-002-010`.**
2. **Already-imported corpora are annotatable without re-upload.** `Book` never stored the source
   text — only `content_hash` — but it does not need to: the ordered `raw_text` sequence *is* the
   complete persisted token stream. This is only possible *because* the two steps are decoupled.
3. **`REQ-002-005`'s token boundaries stay the single source of truth.** Running spaCy's own
   tokenizer over raw text would produce a different token count and different boundaries than the
   persisted rows, breaking the 1:1 mapping and silently diverging from the SPEC-002 §2.2 contract.

---

## 3. Requirements

### Requirement: REQ-003-001 — The backend runtime is pinned to Python 3.12

The `apps/api` project SHALL pin its resolved interpreter to Python 3.12. `pyproject.toml` MUST
declare an upper bound that excludes 3.13 and above, and the resolved virtual environment MUST
report a 3.12 version. This pin is a **hard prerequisite** and MUST land before any NLP dependency
is added.

**Why, verified rather than assumed.** `thinc 9.1.1` — spaCy's own dependency — publishes wheels for
**cp312 only**, the narrowest constraint in the chain (`spacy 3.8.15` publishes cp312 and cp313).
The repository's `apps/api/.venv` currently resolves to **3.14.5**, and `spacy`'s declared
`requires_python: <3.15,>=3.9` is **not** a safety net: the resolution succeeds and then attempts a
fragile C++/Cython source build of `thinc`. A green `uv add` is not evidence of a working install.

Acceptance: **AC-003-01** — Given the `apps/api` project, when the resolved interpreter version is
read, then it is `3.12.x`; and when `pyproject.toml` is read, then `requires-python` excludes `3.13`
and above; and when `mypy`'s `python_version` is read, then it is `3.12`, matching the runtime.

#### Scenario: The venv resolves to the pinned interpreter

- GIVEN the `apps/api` project after dependency installation
- WHEN the interpreter version is queried
- THEN it reports `3.12.x`

#### Scenario: The declared bound cannot silently drift upward

- GIVEN `pyproject.toml`
- WHEN `requires-python` is read
- THEN it excludes `3.13` and above
- AND the declared bound, the resolved runtime, and `mypy`'s `python_version` agree

#### Scenario: The NLP dependency installs from a wheel, not a source build

- GIVEN the pinned 3.12 environment
- WHEN the NLP dependency and its language model are installed
- THEN the installation completes without compiling a C or Cython extension from source

### Requirement: REQ-003-002 — The annotation value object is pure and lives in the domain

The domain SHALL provide a frozen value object carrying one occurrence's `pos`, `lemma`,
`pos_confidence` and `lemma_confidence`. It MUST live in `domain/`, MUST import only the standard
library, and MUST NOT import spaCy, Stanza, SQLAlchemy, FastAPI, Pydantic, or any other framework
or NLP library (Art. VII.1, ADR-0002). No spaCy `Doc`, `Token`, `Vocab`, or `Language` object MAY
cross out of the adapter module.

The existing AST-based domain isolation guard (`tests/unit/test_domain_isolation.py`, hook H2) MUST
be **extended** to cover the NLP libraries, not replaced.

Acceptance: **AC-003-02** — Given the shipped `domain/` package, when its imports are inspected
structurally, then no module imports `spacy`, `thinc`, `stanza`, `sqlalchemy`, `fastapi`, or
`pydantic`; and given the whole source tree, when it is inspected, then no module outside the NLP
adapter package references a spaCy type.

#### Scenario: The domain has no NLP dependency

- GIVEN the `domain/` package
- WHEN its imports are inspected structurally
- THEN only standard-library modules are imported

#### Scenario: No spaCy type escapes the adapter

- GIVEN the shipped sources
- WHEN every module outside the NLP adapter package is inspected
- THEN none references a spaCy type
- AND the value object returned by the port is a plain frozen dataclass

### Requirement: REQ-003-003 — The analyzer port takes pre-tokenized input and an explicit language

The application SHALL define a `LinguisticAnalyzer` port that accepts (a) an ordered sequence of
already-tokenized textual forms and (b) an **explicit language identifier**, and returns one
annotation per input token. The port MUST NOT accept raw document text (§2.6 S4).

The port, the domain value object, and the persisted schema MUST NOT contain an ISO-639 literal, a
language default, or any English-specific assumption, extending `REQ-PFB-LANG-01` and `AC-002-06`
(ADR-0008). The default language for a run is **configuration**, not a hardcode, and MUST live in
`Settings`. Only the English model is installed and tested in this cycle; that is an installation
fact, not a contract fact.

Requesting a language with no installed analyzer MUST raise `UNSUPPORTED_LANGUAGE`. It MUST NOT
fall back to English, and MUST NOT proceed unannotated.

Acceptance: **AC-003-03** — Given the port module, the domain value object, and the persisted
schema, when each is inspected structurally, then none contains an ISO-639 literal or a language
default; and given a request for a language with no installed analyzer, when annotation runs, then it
fails with `UNSUPPORTED_LANGUAGE`, no English pipeline is loaded, and no annotation row is written.

#### Scenario: The port carries no hardcoded language

- GIVEN the port module and the domain value object
- WHEN they are inspected structurally for ISO-639 literals and language defaults
- THEN there are zero matches

#### Scenario: An unsupported language fails loudly

- GIVEN a configured language with no installed analyzer
- WHEN annotation is requested for an import
- THEN it fails with `UNSUPPORTED_LANGUAGE`
- AND no annotation is persisted
- AND no fallback to English occurs

#### Scenario: A fake analyzer satisfies the port structurally

- GIVEN a test double implementing the port's shape
- WHEN it is checked against the port
- THEN it satisfies it without importing any NLP library

### Requirement: REQ-003-004 — Annotation preserves the persisted token stream exactly

The analyzer SHALL return exactly one annotation per input token, in the same order, with the same
length. It MUST NOT split, merge, insert, drop, or reorder tokens. The write path MUST map
annotation `i` onto the occurrence at `position = i` for that `book_id`, and MUST NOT modify
`raw_text`, `normalized_text`, or `position` on any row (§2.1 L2, §2.6 S3).

A length or ordering mismatch between input tokens and returned annotations MUST fail the run with
`ANNOTATION_FAILED`. It MUST NOT be reconciled by truncation, padding, or positional guessing.

Acceptance: **AC-003-04** — Given a synthetic import whose token count is `N`, when annotation runs,
then exactly `N` annotations are returned and exactly `N` occurrence rows are updated, each matched
by `position`; and given a stub analyzer returning `N-1` annotations, then the run fails with
`ANNOTATION_FAILED` and zero rows are updated; and given the synthetic text
`state-of-the-art don't covid19`, when annotation runs, then the persisted `raw_text` values are
byte-identical to their pre-annotation values.

#### Scenario: One annotation per persisted token, in order

- GIVEN a synthetic import with `N` occurrences
- WHEN annotation runs
- THEN `N` annotations are produced and each is written to the occurrence at the matching `position`

#### Scenario: A count mismatch fails instead of being reconciled

- GIVEN a stub analyzer that returns one fewer annotation than it received tokens
- WHEN annotation runs
- THEN the run fails with `ANNOTATION_FAILED` and no row is updated

#### Scenario: SPEC-002 token boundaries survive annotation

- GIVEN a synthetic import containing `state-of-the-art` and `don't`
- WHEN annotation runs
- THEN each remains exactly one occurrence with its original `raw_text` and `position`

### Requirement: REQ-003-005 — POS is a Universal POS tag recorded per occurrence

`Occurrence.pos` SHALL hold a UPOS tag from the closed 17-value set of §2.2, or `NULL` when the
occurrence has not been annotated. A value outside that set MUST fail the run with
`ANNOTATION_FAILED` (§2.2 P3). No fine-grained, language-specific tagset MAY be persisted in `pos`
(P2). No entity SHALL carry a global or aggregate POS, and `pos` MUST NOT appear on `Book` (P5,
ADR-0006, Art. V.2–3).

Acceptance: **AC-003-05** — Given a synthetic English import annotated by the real adapter, when
every occurrence is read, then every non-null `pos` is a member of the 17-tag set; and given a
synthetic text where one textual form appears in two grammatical roles, then the two occurrences
carry different `pos` values; and given a stub analyzer emitting `NN`, then the run fails with
`ANNOTATION_FAILED`; and given the persisted schema, then `book` has no part-of-speech column.

#### Scenario: Every persisted tag is a UPOS tag

- GIVEN an annotated synthetic import
- WHEN every occurrence is read
- THEN each non-null `pos` is one of the 17 UPOS tags

#### Scenario: The same form takes different tags in different contexts

- GIVEN a synthetic text using one form as a noun in one sentence and a verb in another
- WHEN annotation runs
- THEN the two occurrences carry different `pos` values
- AND no single tag is stored for the form as a whole

#### Scenario: A non-UPOS tag is rejected, not coerced

- GIVEN a stub analyzer emitting the Penn Treebank tag `NN`
- WHEN annotation runs
- THEN the run fails with `ANNOTATION_FAILED`
- AND the value is not stored and is not coerced to `X`

### Requirement: REQ-003-006 — Lemma is a third distinct value recorded per occurrence

`Occurrence` SHALL expose a nullable `lemma` column holding the canonical dictionary headword for
that occurrence's contextual reading, stored verbatim as the analyzer emits it (§2.1 L3). It MUST
remain a separate column from `raw_text` and `normalized_text` (L1, L2), MUST be `NULL` rather than
`""` when unavailable (L4), MAY be a string absent from the source text (L5), and MUST be recorded
per occurrence rather than per normalized form or per book (L6).

Acceptance: **AC-003-06** — Given a synthetic English text containing `run`, `ran` and `running`,
when annotation runs, then all three occurrences carry `lemma` `run` while their `raw_text` values
stay `run`, `ran` and `running` and their `normalized_text` values stay `run`, `ran` and `running`;
and given a stub analyzer emitting `"  "`, then the persisted `lemma` is `NULL` and not `""`.

#### Scenario: Inflected forms share one lemma while keeping their own forms

- GIVEN a synthetic English text containing `run`, `ran` and `running`
- WHEN annotation runs
- THEN all three occurrences carry `lemma` `run`
- AND each keeps its own distinct `raw_text` and `normalized_text`

#### Scenario: A lemma need not occur in the source text

- GIVEN a synthetic text containing `ran` but not `run`
- WHEN annotation runs
- THEN the occurrence's `lemma` is `run`
- AND no validation rejects it for being absent from the source

#### Scenario: An empty lemma is stored as null

- GIVEN a stub analyzer returning a whitespace-only lemma
- WHEN annotation runs
- THEN the persisted `lemma` is `NULL`, not the empty string

### Requirement: REQ-003-007 — Provenance is persisted for every automatic annotation

Every automatically annotated occurrence SHALL carry recoverable provenance with all seven fields of
§2.4: `source`, `model_name`, `model_version`, `language`, `processed_at`, `pos_confidence`,
`lemma_confidence`. The first five MUST be non-null. `language` MUST record the language of the
pipeline that actually ran and MUST NOT be inferred from a hardcoded default at read time.

Acceptance: **AC-003-07** — Given a synthetic import annotated by the real adapter, when provenance
is read for any occurrence, then `source`, `model_name`, `model_version`, `language` and
`processed_at` are all non-null, `model_version` matches the installed pipeline's reported version,
and `language` equals the language the run was invoked with; and given the same import annotated
twice with the same pinned model, then both runs record the same `source`, `model_name`,
`model_version` and `language`, and a later `processed_at`.

#### Scenario: Provenance is complete for every annotated occurrence

- GIVEN a synthetic import annotated by the real adapter
- WHEN provenance is read for every occurrence
- THEN all five non-nullable fields are populated
- AND `model_version` matches the installed pipeline's reported version

#### Scenario: The language of the run is recorded, not assumed

- GIVEN an import whose `Book.language` is unset
- WHEN annotation runs with an explicit language
- THEN the provenance records that language
- AND `Book.language` remains unset

### Requirement: REQ-003-008 — Confidence is bounded, nullable, and never fabricated

`pos_confidence` and `lemma_confidence` SHALL each be a float within the closed interval
`[0.0, 1.0]` or `NULL`, independently of one another (§2.3 C1, C2). No layer MAY compute, estimate,
default, smooth, or otherwise fabricate a confidence the analyzer did not report (C3). `NULL` MUST
NOT be read, rendered, or documented as `0.0`, as low confidence, or as an error (C4). A value
outside `[0.0, 1.0]` MUST fail the run with `ANNOTATION_FAILED` rather than be clamped.

Acceptance: **AC-003-08** — Given any annotated occurrence, when both confidence values are read,
then each is `NULL` or a float in `[0.0, 1.0]`; and given a stub analyzer emitting `1.4`, then the
run fails with `ANNOTATION_FAILED` and the value is not clamped to `1.0`; and given an analyzer
reporting no lemma confidence, then `lemma_confidence` is `NULL` while `pos_confidence` may hold a
value.

#### Scenario: Every confidence is null or within range

- GIVEN an annotated synthetic import
- WHEN every confidence value is read
- THEN each is `NULL` or a float in `[0.0, 1.0]`

#### Scenario: An out-of-range confidence fails instead of being clamped

- GIVEN a stub analyzer emitting a confidence of `1.4`
- WHEN annotation runs
- THEN the run fails with `ANNOTATION_FAILED`
- AND no clamped value is persisted

#### Scenario: The two confidences are independent

- GIVEN an analyzer that reports a POS confidence but no lemma confidence
- WHEN annotation runs
- THEN `pos_confidence` holds the reported value and `lemma_confidence` is `NULL`

### Requirement: REQ-003-009 — Confidence is always visible on every classification

The API SHALL return `pos_confidence` and `lemma_confidence` for **every** annotated occurrence it
exposes, including when the value is `NULL`: the key MUST be present with a JSON `null` and MUST NOT
be omitted (§2.3 C5). The UI MUST render both values for every row, MUST distinguish "no confidence
reported" from a numeric value, and MUST NOT convey that distinction by colour alone (Art. IX.4).

In this capability confidence is **informational**. No filter, sort, threshold, warning banner,
blocking state, or automatic re-run MAY key off it (C6). See §5 `AMB-2` for the accepted consequence.

Acceptance: **AC-003-09** — Given any annotated occurrence in an API response, when the body is
inspected, then both confidence keys are present, with either a number in `[0.0, 1.0]` or JSON
`null`; and given a mocked response where one row has both confidences `null` and another has
numeric values, when the UI renders, then both rows show a confidence cell whose distinction is
readable as text without colour; and given the shipped frontend sources, when they are searched for
filtering, sorting, or thresholding on a confidence value, then there are zero matches.

#### Scenario: The confidence key is present even when null

- GIVEN an occurrence whose analyzer reported no confidence
- WHEN the API response is inspected
- THEN both confidence keys are present with JSON `null`
- AND neither key is omitted

#### Scenario: Null and numeric confidence are distinguishable without colour

- GIVEN a mocked response with one null-confidence row and one numeric-confidence row
- WHEN the table renders
- THEN each row shows a confidence cell distinguishable as text

#### Scenario: Nothing acts on confidence in this capability

- GIVEN the shipped backend and frontend sources
- WHEN they are searched for filtering, sorting, or thresholding on confidence
- THEN there are zero matches

### Requirement: REQ-003-010 — A manual correction wins at read time

Every read that exposes an effective `pos` or `lemma` SHALL resolve it by the §2.5 rule: the
`ManualCorrection` value for that `(occurrence, field)` if one exists, otherwise the automatic value
(R1). The automatic value MUST be retained as the audit value (R4). Every such read MUST also expose
a per-field origin marker distinguishing `automatic` from `manual` (R5).

Precedence MUST be enforced in the application or persistence layer. The API layer MUST NOT contain
it (Art. VII.4) and the frontend MUST NOT contain it (Art. VII.5, `REQ-002-014`).

Acceptance: **AC-003-10** — Given an annotated import where an occurrence has automatic `pos` `NOUN`
and a seeded `ManualCorrection` of `VERB` for `pos`, when the occurrence is read, then the effective
`pos` is `VERB`, its origin marker is `manual`, the automatic value `NOUN` is still recoverable, and
the effective `lemma` on that same occurrence is still the automatic value with origin `automatic`;
and given the frontend sources, when they are searched for correction-precedence logic, then there
are zero matches.

#### Scenario: A seeded correction wins on read

- GIVEN an occurrence with automatic `pos` `NOUN` and a seeded manual correction of `VERB`
- WHEN the occurrence is read
- THEN the effective `pos` is `VERB` with origin `manual`
- AND the automatic `NOUN` remains recoverable as the audit value

#### Scenario: Precedence is per field, not per occurrence

- GIVEN an occurrence with a manual correction for `pos` only
- WHEN it is read
- THEN `pos` has origin `manual` and `lemma` has origin `automatic`

#### Scenario: The frontend contains no precedence logic

- GIVEN the frontend sources
- WHEN they are searched for correction-precedence resolution
- THEN there are zero matches

### Requirement: REQ-003-011 — Reprocessing writes unconditionally and never touches corrections

The annotation write path SHALL write automatic values and provenance **unconditionally**, without
reading `ManualCorrection` (§2.5 R2), and MUST NOT insert, update, or delete any `ManualCorrection`
row (R3). No code path in this capability writes a `ManualCorrection` row; the table ships with
schema only (R6). Re-running annotation over an already-annotated import MUST therefore be safe by
construction — there is no branch that could fail to check (Art. V.9, ADR-0007 point 2).

Acceptance: **AC-003-11** — Given an annotated import with a seeded manual correction, when
annotation is re-run over it, then the `ManualCorrection` row is byte-identical afterwards, the
effective value is still the corrected one, and the automatic value has been updated to the new run's
output; and given the annotation write path's sources, when they are inspected structurally, then
they contain no read of, insert into, update of, or delete from the correction table.

#### Scenario: Reprocessing leaves the correction untouched

- GIVEN an annotated import with a seeded manual correction
- WHEN annotation is re-run
- THEN the correction row is unchanged and the effective value is still the corrected one

#### Scenario: The automatic value is refreshed underneath the correction

- GIVEN a re-run whose analyzer returns a different automatic value
- WHEN the occurrence is read
- THEN the effective value is still the corrected one
- AND the newly written automatic value is recoverable as the audit value

#### Scenario: The write path cannot reach the correction table

- GIVEN the annotation write path's sources
- WHEN they are inspected structurally
- THEN they contain no reference to the correction table

### Requirement: REQ-003-012 — Annotation is a separate step and import behaviour is unchanged

`POST /api/v1/imports` SHALL NOT run annotation (§2.6 S1). Its status codes, response body, error
codes, and persisted rows MUST be identical to the `002-text-import` baseline. Every occurrence
written by the import path MUST still have `pos IS NULL` and `lemma IS NULL`, preserving
`REQ-002-010` literally.

Acceptance: **AC-003-12** — Given a synthetic file imported through `POST /api/v1/imports`, when
every persisted occurrence is read immediately afterwards, then each has `pos IS NULL` and
`lemma IS NULL`; and when the response body is validated against `import.v1.json` v1, then it
validates unchanged; and when the complete `002-text-import` acceptance suite is re-run, then it
passes with no requirement weakened.

#### Scenario: Import still writes no annotation

- GIVEN a synthetic file imported through the API
- WHEN every persisted occurrence is read immediately afterwards
- THEN each has `pos IS NULL` and `lemma IS NULL`

#### Scenario: The SPEC-002 contract is byte-compatible

- GIVEN an import response body
- WHEN it is validated against `import.v1.json` v1
- THEN it validates without modification to that schema

### Requirement: REQ-003-013 — Already-imported corpora are annotatable without re-upload

An import persisted before this capability shipped SHALL be annotatable using only its stored data.
The annotation input MUST be `Occurrence.raw_text` ordered by `Occurrence.position` for that
`book_id` (§2.6 S3). No re-upload, no stored source text, and no re-tokenization MAY be required.

Acceptance: **AC-003-14** — Given an import created through the SPEC-002 path with every `pos` and
`lemma` null, when annotation is run against its id and no file is supplied, then every occurrence
gains a `pos` and a `lemma`, the occurrence count is unchanged, and every `raw_text`,
`normalized_text` and `position` value is byte-identical to before the run.

#### Scenario: A pre-existing import is annotated in place

- GIVEN an import created before this capability, with all annotations null
- WHEN annotation is run against its id with no file supplied
- THEN every occurrence gains a `pos` and a `lemma`

#### Scenario: Reprocessing changes no tokenization output

- GIVEN a pre-existing import
- WHEN annotation runs
- THEN the occurrence count is unchanged
- AND every `raw_text`, `normalized_text` and `position` is byte-identical to before the run

### Requirement: REQ-003-014 — Annotation is atomic per import

An annotation run SHALL be atomic for the import it targets. A run that fails at any point MUST
leave the import in exactly the state it had before the run: no partially annotated occurrence, no
orphan provenance record, and no provenance record without its annotation (Art. X.4). A failed run
MUST NOT leave some occurrences carrying the new model version and others the old one.

Acceptance: **AC-003-15** — Given an import of at least two occurrences and a stub analyzer that
fails after the first, when annotation runs, then the run fails, every occurrence retains its
pre-run `pos`, `lemma` and provenance, and no provenance record exists without its occurrence
annotation; and given a previously annotated import, when a failing re-run is attempted, then every
occurrence still reports the previous run's `model_version`.

#### Scenario: A mid-run failure rolls the whole run back

- GIVEN an import of at least two occurrences and an analyzer that fails partway
- WHEN annotation runs
- THEN the run fails and every occurrence retains its pre-run values

#### Scenario: No mixed model versions survive a failure

- GIVEN a previously annotated import
- WHEN a failing re-run is attempted
- THEN every occurrence still reports the previous run's `model_version`

### Requirement: REQ-003-015 — One additive, reversible migration

Exactly one additive Alembic revision SHALL add `Occurrence.lemma`, the provenance storage, and the
`ManualCorrection` table. It MUST NOT drop, rename, retype, or make non-nullable any column that
`002-text-import` created. Its `downgrade()` MUST return the schema to the SPEC-002 baseline
(Art. VI.4).

Acceptance: **AC-003-16** — Given a database at the SPEC-002 baseline, when `alembic upgrade head`
runs, then it exits `0` and the `lemma` column, provenance storage and correction table exist; and
when `alembic downgrade -1` runs, then it exits `0`, none of the three exist, and the `book` and
`occurrence` tables are structurally identical to the SPEC-002 baseline; and given a database
already holding SPEC-002 imports, when the upgrade runs, then every pre-existing occurrence row
survives with its `raw_text`, `normalized_text` and `position` unchanged.

#### Scenario: The migration applies and reverses cleanly

- GIVEN a database at the SPEC-002 baseline
- WHEN `alembic upgrade head` then `alembic downgrade -1` run
- THEN both exit `0` and the schema returns to the SPEC-002 baseline

#### Scenario: Existing data survives the upgrade

- GIVEN a database holding SPEC-002 imports
- WHEN the upgrade runs
- THEN every occurrence row survives with its tokenization values unchanged

### Requirement: REQ-003-016 — Annotation runs locally and offline

Annotation SHALL run entirely on the user's machine. No token, textual form, lemma, normalized form,
or any other substring of the imported text MAY be transmitted to any network endpoint (Art. IV.4–5,
ADR-0005). The language model MUST be installed as an ordinary declared dependency, and annotation
MUST NOT trigger a model download, a licence check, a telemetry call, or any other network request
at run time.

Acceptance: **AC-003-17** — Given a machine with the model installed and outbound network access
disabled, when a synthetic import is annotated, then the run succeeds; and given a test that fails
on any outbound socket connection, when annotation runs, then no connection is attempted.

#### Scenario: Annotation succeeds with the network disabled

- GIVEN the model installed and outbound network access disabled
- WHEN a synthetic import is annotated
- THEN the run succeeds

#### Scenario: No network call is attempted at run time

- GIVEN a test that fails on any outbound socket connection
- WHEN annotation runs
- THEN no connection is attempted

### Requirement: REQ-003-017 — Annotation has its own contract; `import.v1.json` v1 is frozen

The API SHALL expose, for an annotated import, per occurrence: the effective `pos`, the effective
`lemma`, `pos_confidence`, `lemma_confidence`, a per-field origin marker, and the provenance
identity. That data MUST be carried on a **contract distinct from `import.v1.json` v1**, which MUST
remain byte-compatible and MUST NOT gain a property.

**Why the v1 schema cannot simply grow.** `import.v1.json` sets `additionalProperties: false` on both
the envelope and each form row, so adding a property is a breaking change to a pinned, versioned
contract. It is also the wrong shape: that document is grouped by normalized form, while annotation
is per occurrence. Reusing it would force a one-lemma-per-group answer, which §2.1 L6 and ADR-0006
forbid.

Acceptance: **AC-003-18** — Given the shipped `import.v1.json`, when it is compared against the
SPEC-002 baseline, then it is byte-identical; and given an annotated import read through the
annotation contract, when a returned occurrence is inspected, then it carries effective `pos`,
effective `lemma`, both confidence keys, a per-field origin marker, and the provenance identity, and
it validates against the versioned annotation schema.

#### Scenario: The import contract is unchanged

- GIVEN the shipped `import.v1.json`
- WHEN it is compared against the SPEC-002 baseline
- THEN it is byte-identical

#### Scenario: The annotation contract carries the full per-occurrence record

- GIVEN an annotated import read through the annotation contract
- WHEN a returned occurrence is inspected
- THEN it carries effective `pos`, effective `lemma`, both confidences, an origin marker, and provenance
- AND it validates against the versioned annotation schema

### Requirement: REQ-003-018 — The frontend duplicates no linguistic rules

The frontend SHALL render exactly what the API returns. It MUST NOT lemmatize, tag, tokenize,
normalize, case-fold, infer, correct, or re-derive any `pos`, `lemma`, confidence, or origin marker,
and MUST NOT apply correction precedence (Art. VII.5, `REQ-002-014`).

Presentational localization of a received UPOS tag into a human-readable label is **permitted** and
is presentation, not a linguistic rule — but the mapping MUST be total over the 17-tag set of §2.2,
and an unmapped or unexpected value MUST be rendered as the received tag rather than replaced by a
guess or by an empty cell. The annotation view MUST be keyboard-navigable, MUST carry accessible
labels, and MUST NOT depend on colour alone (Art. IX.1–4).

Acceptance: **AC-003-19** — Given the frontend sources, when they are searched for lemmatization,
tagging, tokenization, normalization, and precedence resolution, then there are zero matches in
annotation-related code; and given a mocked response, when the view renders, then each row shows the
received `lemma`, `pos`, both confidences and the origin marker verbatim; and given a mocked row
whose `pos` is a value the label map does not cover, then the raw tag is displayed and no cell is
blank.

#### Scenario: No linguistic derivation client-side

- GIVEN the annotation view's sources
- WHEN they are searched for lemmatization, tagging, normalization, and precedence resolution
- THEN there are zero matches

#### Scenario: Received values are rendered verbatim

- GIVEN a mocked annotation response
- WHEN the view renders
- THEN each row shows the received `lemma`, `pos`, both confidences and the origin marker unchanged

#### Scenario: An unmapped tag degrades to the raw tag

- GIVEN a mocked row whose `pos` the label map does not cover
- WHEN the row renders
- THEN the received tag is displayed and the cell is not blank

### Requirement: REQ-003-019 — Logs and error bodies never carry imported text or annotations

No log record and no error body emitted by annotation SHALL contain any substring of the imported
text, any textual form, normalized form, lemma, or corrected value, nor a stack trace, filesystem
path, model file location, or environment value (Art. X.2, Art. VIII.4). Failure records MUST
identify the failure by error code, import `id`, and — where applicable — the zero-based position of
the offending token, never its text.

Acceptance: **AC-003-20** — Given a synthetic text containing the sentinel `zzqxsentinel`, when it is
annotated and, separately, when annotation fails, then no captured log record from any logger
contains `zzqxsentinel`, and the failure record contains the error code and the import `id`; and
given every annotation error response body, when each is inspected, then none contains a token, a
lemma, a stack trace, or a filesystem path.

#### Scenario: A successful annotation logs no content

- GIVEN a synthetic text containing the sentinel `zzqxsentinel`
- WHEN annotation succeeds
- THEN no captured log record contains `zzqxsentinel`

#### Scenario: A failing annotation reports a code and a position, not text

- GIVEN an annotation run that fails on a specific token
- WHEN the log record and the error body are inspected
- THEN they carry the error code, the import `id` and the token position
- AND neither carries the token's text

### Requirement: REQ-003-020 — Annotation is deterministic and write-idempotent

For a fixed token sequence, a fixed `source`, `model_name`, `model_version` and `language`,
annotation SHALL produce identical `pos` and `lemma` values on every run (Art. VI.2). Re-running
annotation over an unchanged import MUST leave every effective value, every automatic value and every
provenance identity field unchanged; only `processed_at` MAY advance (Art. X.5).

**The naive idempotence property is invalid here and MUST NOT be asserted.** `AGENTS.md §6` lists
"normalizing twice equals normalizing once", which holds because `normalize()` is a pure context-free
function. Its apparent lemma analogue — "lemmatizing a lemma returns that lemma" — is **false** for a
contextual statistical tagger: a lemma analyzed in isolation has no sentence context, so `saw`
(noun lemma) analyzed alone may be tagged `VERB` and lemmatized to `see`. Asserting it would produce
a flaky test that reports a model defect where the model is behaving correctly. The valid invariant
is **stability under re-run**, specified above. See §5 `AMB-1`.

Acceptance: **AC-003-21** — Given a synthetic import and a pinned model, when annotation runs twice,
then the two runs produce identical `pos` and `lemma` values for every occurrence, and identical
`source`, `model_name`, `model_version` and `language`, with only `processed_at` differing; and given
a Hypothesis strategy generating token sequences and a deterministic fake analyzer, when annotation
runs twice over each generated sequence, then the persisted effective values are equal.

#### Scenario: Two runs of the same input agree

- GIVEN a synthetic import and a pinned model
- WHEN annotation runs twice
- THEN every `pos` and `lemma` is identical across the two runs
- AND only `processed_at` differs

#### Scenario: Re-running is a no-op on generated input

- GIVEN a generated token sequence and a deterministic fake analyzer
- WHEN annotation runs twice
- THEN the persisted effective values are equal

### Requirement: REQ-003-021 — Order-independence is scoped to processing order, not token order

The annotation of an import SHALL be independent of the order in which occurrences are read into
batches, the order in which rows are written, the batch size, and the order in which distinct imports
are annotated. For a fixed `book_id`, the mapping from `position` to `(pos, lemma)` MUST be identical
under any of those variations.

**Token-order independence is FORBIDDEN as an assertion and is not a defect when it fails.**
`AGENTS.md §6` phrases an invariant as "the input order does not alter the set of lemmas", and
`REQ-002-016` deferred exactly this re-verification to the capability that ships real lemmas. It is
re-verified here, and the honest answer is that it **does not hold at token level and must not**:
POS and lemma are *contextual* (ADR-0006, Art. V.2–3), so permuting a document's tokens legitimately
changes them. A test asserting permutation invariance over tokens would force a context-free tagger
and contradict the ADR that defines this capability. `REQ-002-016` itself is unaffected — it is
phrased over normalized forms, and normalization is context-free.

Acceptance: **AC-003-22** — Given a synthetic import, when it is annotated with two different batch
sizes and with the occurrence read order reversed, then the resulting `position` → `(pos, lemma)`
mapping is identical in every case; and given two imports annotated in either order, then each
import's mapping is unaffected by the other; and given the test suite, when the order-independence
tests are inspected, then they carry an explicit note that token-level permutation invariance is
deliberately not asserted, citing this requirement.

#### Scenario: Batch size and read order do not change the result

- GIVEN a synthetic import
- WHEN it is annotated with two different batch sizes and with the read order reversed
- THEN the `position` → `(pos, lemma)` mapping is identical in every case

#### Scenario: Annotating one import does not affect another

- GIVEN two synthetic imports
- WHEN they are annotated in either order
- THEN each import's mapping is unchanged

#### Scenario: The suite records why token permutation is not asserted

- GIVEN the order-independence tests
- WHEN they are inspected
- THEN they carry an explicit note citing this requirement

### Requirement: REQ-003-022 — `PROPN` is persisted like any other tag and no proper-noun filter ships

`PROPN` SHALL be stored, returned, and rendered exactly like any other UPOS tag. No filter,
suppression, exclusion default, separate entity, or special-case branch for proper nouns MAY be
introduced by this capability (§2.2 P4). Consequently `docs/product-vision.md` §10 step 4 ("excluye
nombres propios") remains **knowingly unimplemented** until roadmap item 6, and MUST be recorded as
such rather than partially satisfied here.

Acceptance: **AC-003-23** — Given a synthetic text containing a capitalized invented proper name,
when annotation runs, then the occurrence is persisted with `pos` `PROPN` and is present in every
API response and in the rendered view with no filtering applied; and given the shipped sources, when
they are searched for a proper-noun filter, exclusion default, or `PROPN` special case, then there
are zero matches.

#### Scenario: A proper noun is persisted and surfaced like any other token

- GIVEN a synthetic text containing a capitalized invented proper name
- WHEN annotation runs
- THEN the occurrence carries `pos` `PROPN` and appears unfiltered in the API response and the view

#### Scenario: No proper-noun special case exists anywhere

- GIVEN the shipped backend and frontend sources
- WHEN they are searched for a proper-noun filter, exclusion default, or `PROPN` special case
- THEN there are zero matches

### Requirement: REQ-003-023 — The `002-text-import` naming guard is narrowed, never disabled

The `AC-002-10` naming guard SHALL be narrowed to permit the symbols this capability legitimately
introduces, and MUST remain zero-match everywhere else. The narrowing MUST be an **explicit,
enumerated allow-list** of exact symbol and property names, and MUST NOT be implemented by deleting
the guard, by excluding a whole file or directory, by weakening the pattern, or by relaxing the AST
criterion to a text search.

Every entry in the allow-list MUST name a value that is a **genuine lemma** produced by a real
lemmatizer. `normalized_form` and `display_form` MUST NOT be renamed, MUST NOT be aliased to a
lemma-shaped name, and MUST NOT be described as a lemma anywhere in prose, contract surface, or UI
copy. `REQ-002-007`'s protected intent — that a normalized form is never mislabelled as a lemma —
survives fully intact.

The accompanying delta at `../002-text-import/spec.md` modifies `REQ-002-007` for this purpose and
for no other. See §5 `CONTRA-1`.

Acceptance: **AC-003-24** — Given the shipped sources, the versioned schemas, and the served OpenAPI
document, when the narrowed guard runs, then every match is a member of the enumerated allow-list and
there are zero matches outside it; and given a deliberate rename of `normalized_form` to any
lemma-shaped name, when the guard runs, then it fails; and given the guard's implementation, when it
is inspected, then it is still AST-based, still covers every previously covered file, and the
allow-list is a finite explicit enumeration rather than a path or pattern exclusion.

#### Scenario: Legitimate lemma symbols pass and nothing else does

- GIVEN the shipped sources, schemas and served OpenAPI document
- WHEN the narrowed guard runs
- THEN every match is a member of the enumerated allow-list
- AND there are zero matches outside it

#### Scenario: Mislabelling a normalized form still fails

- GIVEN `normalized_form` renamed to a lemma-shaped name
- WHEN the guard runs
- THEN it fails

#### Scenario: The guard was narrowed, not weakened

- GIVEN the guard's implementation
- WHEN it is inspected
- THEN it is still AST-based over every previously covered file
- AND the allow-list is a finite explicit enumeration, not a path or pattern exclusion

---

## 4. Error contract

Annotation reuses the shared error envelope of `002-text-import` §4. The envelope shape is unchanged;
the error-code enumeration gains the rows below.

| Code | HTTP | Trigger | Class (Art. X.3) |
|------|------|---------|------------------|
| `IMPORT_NOT_FOUND` | 404 | Annotation requested for an unknown or already-deleted import `id` (reused from SPEC-002) | User |
| `UNSUPPORTED_LANGUAGE` | 422 | The requested language has no installed analyzer (`REQ-003-003`) | User |
| `ANALYZER_UNAVAILABLE` | 503 | The configured model is installed but cannot be loaded | Processing |
| `ANNOTATION_FAILED` | 500 | The analyzer returned a malformed result: wrong length, wrong order, a tag outside the §2.2 set, or a confidence outside `[0.0, 1.0]` | Processing |

Every error body MUST carry a distinct code and a comprehensible, actionable message (Art. VIII.4).
Error bodies MUST NOT contain imported text, textual forms, lemmas, corrected values, stack traces,
filesystem paths, model file locations, or environment values (`REQ-003-019`).

`ANNOTATION_FAILED` is deliberately a `500`, not a `422`: every one of its triggers is an adapter or
model defect, never anything the user supplied. Reporting it as a client error would tell the user to
fix an input that is already correct.

---

## 5. Ambiguities and contradictions recorded and resolved (AGENTS.md §9)

Each item below was an ambiguity or a contradiction in the inputs. None was resolved silently.

| ID | Ambiguity or contradiction | Resolution in this spec | Status |
|----|----------------------------|-------------------------|--------|
| **CONTRA-1** | **`AC-002-10`'s guard cannot coexist with a real lemma.** `REQ-002-007`'s *text* is already capability-scoped ("introduced by this capability"), but `AC-002-10` and its implementation (`tests/unit/test_no_lemma_naming.py`) walk `apps/api/src/wheel_vocabulary/**/*.py`, `apps/web/src/**`, `Base.metadata` column names, the pinned JSON Schema, and the served OpenAPI document, asserting **zero** matches for `lemma\|lemas\|lexeme\|lexema`. `Occurrence.lemma`, `LinguisticAnnotation.lemma`, the DTO field, the TypeScript type, and the reflected column name all land inside that walk. **The existing suite will fail — this is not a naming preference, it is a broken build.** The proposal did not identify it. | The requirement's *intent* is preserved and its *mechanism* is narrowed. `REQ-003-023` mandates an explicit, enumerated allow-list of exact symbol names, each of which must denote a genuine lemma; everything outside stays zero-match; `normalized_form`/`display_form` keep their names and may still never be described as lemmas. A `MODIFIED` delta at `../002-text-import/spec.md` amends `REQ-002-007`/`AC-002-10` for this and nothing else. | **Closed. This is the only modification made to SPEC-002. Do not "fix" this by deleting the guard, excluding a file, or reverting the AST criterion to a grep — `AC-002-10`'s own rationale forbids all three** |
| **CONTRA-2** | **`REQ-002-010` (per-occurrence POS reserved and unpopulated) appears to contradict this capability populating `pos`.** The proposal left this conditional on whether annotation writes into the import path. | **Not a contradiction.** §2.6 makes annotation a separate step, so import still writes `pos = None` and `REQ-002-010` — scoped to "every row written by this capability" — stays literally true. **No `MODIFIED` delta is emitted against `REQ-002-010`.** Enforced by `REQ-003-012`. | **Closed. Do not re-open. Deferring annotation out of the import path is also what makes `REQ-003-013` (reprocessing without re-upload) possible** |
| **AMB-1** | `AGENTS.md §6` requires an idempotence invariant. Its literal lemma analogue — "lemmatizing a lemma returns that lemma" — is not type-correct for a sequence-in/sequence-out port and is **empirically false** for a contextual tagger (a lemma analyzed without sentence context can be re-tagged and re-lemmatized). | The valid invariant is **stability under re-run with a pinned model** (`REQ-003-020`), plus write-idempotence (Art. X.5). Asserting the naive form is forbidden: it produces a flaky test that reports correct model behaviour as a defect. | Accepted |
| **AMB-2** | Confidence is specified as always visible (`REQ-003-009`), but the manual-correction write path ships in SPEC-004. For one cycle a user can see that a classification is uncertain and can do nothing about it. | **Accepted knowingly, with its consequence stated: for one release the low-confidence signal is informational only.** The alternative — hiding confidence until it is actionable — is worse: it would delay the provenance schema, force a second migration, and leave SPEC-004 introducing storage, precedence and UX simultaneously. `REQ-003-009` C6 forbids any behaviour keying off confidence so no premature semantics are baked in. | **Accepted tradeoff, not an oversight. Record it as such in the release notes** |
| **AMB-3** | `AGENTS.md §6` and `REQ-002-016` require input-order independence, and `REQ-002-016` explicitly defers re-verification "against real lemmas when lemmatization ships". | Re-verified, and the answer is **negative at token level and correctly so**: POS and lemma are contextual (ADR-0006), so token permutation legitimately changes them. `REQ-003-021` scopes the invariant to batch size, read order, write order and inter-import order, and forbids the token-permutation assertion. `REQ-002-016` is unaffected — normalization is context-free. | **Closed. `REQ-002-016`'s deferred note is hereby discharged; the test carrying that note must cite `REQ-003-021`** |
| **AMB-4** | Art. V.7 requires confidence "cuando proceda", which does not say what to store when the pipeline exposes none. | `NULL`, never a fabricated number, and `NULL` is a distinct fact from `0.0` (§2.3 C3, C4). Independent per field (C2). | Accepted |
| **AMB-5** | The POS tagset was unspecified. spaCy exposes both coarse `pos_` (UPOS) and fine-grained `tag_` (Penn Treebank for English). | UPOS, the closed 17-tag set of §2.2. Penn Treebank is English-specific and would hardcode English into the schema, contradicting ADR-0008 and the swappable-adapter premise of ADR-0001/0002. | Accepted. A fine-grained tag column remains additively possible later |
| **AMB-6** | ADR-0002 says the port "lives in domain or application", while SPEC-002's shipped precedent places ports in `application/`. | Follow the codebase, not the looser ADR wording: the port lives in `application/`, the pure value object in `domain/` (`REQ-003-002`, `REQ-003-003`). | Accepted |
| **AMB-7** | The proposal listed reprocessing existing imports as possibly deferrable. | **In scope** (`REQ-003-013`). It costs almost nothing once §2.6 decouples the steps, and deferring it would leave every pre-existing corpus permanently unannotatable without re-upload. | **Closed. In scope** |
| **AMB-8** | Whether annotation data extends `import.v1.json` or gets its own contract was unstated. | Its own contract (`REQ-003-017`). `import.v1.json` sets `additionalProperties: false`, so extending it is a breaking change to a pinned schema, and its per-group shape cannot carry per-occurrence data without violating §2.1 L6. | Accepted |
| **AMB-9** | `Book.language` exists and is unset; the only installed model is English. It was unclear where the language of a run is recorded. | On the **provenance record** (§2.4), supplied explicitly to the port (`REQ-003-003`). `Book.language` stays unset; detection remains OQ-2. This is what keeps the schema multi-language without hardcoding English. | Accepted |

---

## 6. Product-visible decisions

These change what appears on screen. They are decisions, not implementation details.

| # | Decision | What the user sees | Status |
|---|----------|--------------------|--------|
| PV-1 | Lemma grouping is the primary value; POS is secondary (Decision 1) | `run`, `ran` and `running` are recognisably one word. Under budget pressure POS yields before lemma | Accepted |
| PV-2 | Confidence is always visible, on every classification, including when unreported | Every row shows a confidence value or an explicit "not reported" marker — never a blank cell and never a fabricated number | Accepted. Informational for one cycle (§5 AMB-2) |
| PV-3 | POS is shown as a UPOS tag, optionally localized into a readable label | The user sees `NOUN`/`VERB` semantics, not Penn Treebank codes like `NN`/`VBD` | Accepted |
| PV-4 | Proper nouns are tagged `PROPN` and shown like every other word | Character names and place names appear in the list. Excluding them arrives with roadmap item 6; `product-vision §10 step 4` is **knowingly unimplemented** until then | Accepted, explicitly incomplete |
| PV-5 | Annotation is an explicit step, not part of upload | Importing a file does not automatically produce lemmas; annotation is triggered separately, and existing imports can be annotated without re-uploading | Accepted (§2.6) |
| PV-6 | A corrected value is visibly marked as corrected | When SPEC-004 ships corrections, each field already carries an `automatic`/`manual` origin marker, so a user can see why a value differs from the pipeline output | Accepted |
| PV-7 | Multiword expressions are not detected | `give up` remains two separate annotated occurrences with their own lemmas. Unchanged from SPEC-002 §6 PV-3's neighbouring limitation | Accepted; roadmap item 7 / ADR-0009 |

---

## 7. Explicit non-additions

This capability does NOT specify: the manual-correction **write path**, endpoint, or UI (SPEC-004 —
only the table, the precedence mechanism and the origin marker ship here); a proper-noun filter or
separate proper-noun entity (roadmap item 6 — `docs/product-vision.md` §10 step 4 stays knowingly
unimplemented); multiword-expression detection, `MultiwordExpression`, or `mwe_kind` (roadmap item 7,
ADR-0009); the vocabulary browser UI or any lemma-grouped view (roadmap item 5); language detection
(OQ-2); per-language adapter selection or any second installed language model (OQ-4); a translation
provider or consent gate (OQ-3); a `Lexeme` or `WordForm` entity; aggregate POS distributions stored
as data; a fine-grained language-specific tag column; re-import deduplication by `content_hash`;
asynchronous annotation states beyond success and failure; pagination of annotation results; or any
EPUB support.

It also explicitly does NOT permit: deriving a lemma from `normalize()` or from `normalized_text`;
storing a fabricated or defaulted confidence; a write-time precedence check; any code path that
writes a `ManualCorrection` row; running annotation inside the import request; re-tokenizing inside
the analyzer; persisting a non-UPOS tag; a global or aggregate POS field on any entity; a
proper-noun special case; disabling, deleting, path-excluding, or grep-reverting the `AC-002-10`
guard; or renaming `normalized_form` or `display_form`.

It does NOT choose module names, file layouts, DTO shapes, route paths, column types, index
strategy, transaction boundaries, or task ordering — `sdd-design` and `sdd-tasks` own those.

---

## 8. Verification hooks

| Hook | Check | Verifies |
|------|-------|----------|
| H1 | Resolved interpreter reports `3.12.x`; `requires-python` excludes `3.13+`; `mypy` `python_version` agrees; the NLP install compiles no source extension | AC-003-01 |
| H2 | Extended AST domain-isolation guard finds zero `spacy\|thinc\|stanza\|sqlalchemy\|fastapi\|pydantic` imports in `domain/`, and no spaCy type outside the adapter package | AC-003-02 |
| H3 | Structural search for ISO-639 literals and language defaults in the port, value object and schema returns zero matches; `UNSUPPORTED_LANGUAGE` path writes nothing | AC-003-03 |
| H4 | Every persisted `pos` is a member of the 17-tag UPOS set; a stub emitting `NN` fails the run; `book` has no POS column | AC-003-05 |
| H5 | Every confidence is `NULL` or within `[0.0, 1.0]`; an out-of-range value fails rather than clamps; both keys always present on the wire, `null` included | AC-003-08, AC-003-09 |
| H6 | Seeded-correction precedence test: effective value is the correction, origin marker is `manual`, automatic value stays recoverable; structural check proves the write path never references the correction table | AC-003-10, AC-003-11 |
| H7 | `alembic upgrade head` then `alembic downgrade -1` against a database holding SPEC-002 data both exit `0`; pre-existing occurrence rows survive with tokenization values byte-identical | AC-003-16 |
| H8 | Full `002-text-import` acceptance suite re-run passes unchanged; `import.v1.json` byte-identical to the SPEC-002 baseline; freshly imported occurrences still have `pos IS NULL` and `lemma IS NULL` | AC-003-12, AC-003-18 |
| H9 | Narrowed `AC-002-10` guard: every match is in the enumerated allow-list, zero outside; renaming `normalized_form` to a lemma-shaped name still fails; guard remains AST-based over every previously covered file | AC-003-24 |
| H10 | Hypothesis properties pass with the `filterwarnings` gate unchanged: confidence within range; re-run stability and write-idempotence; batch/read/write-order independence; annotation never mutates `raw_text`/`normalized_text`/`position`; seeded corrections survive reprocessing. The order-independence test carries the `REQ-003-021` note; **no token-permutation assertion exists** | AC-003-21, AC-003-22, AC-003-11, AC-003-14 |
| H11 | Annotation succeeds with outbound network disabled; a socket-blocking test observes zero connection attempts | AC-003-17 |
| H12 | Log capture over a sentinel-bearing synthetic annotation yields zero records containing the sentinel; every annotation error body is free of tokens, lemmas, stack traces and paths | AC-003-20 |
| H13 | Structural search for a proper-noun filter, exclusion default, or `PROPN` special case returns zero matches; a `PROPN` occurrence appears unfiltered end to end | AC-003-23 |
| H14 | Every fixture is synthetic or public domain and resembles no copyrighted work; the installed language model is a declared dependency and no book text is committed (Art. IV.1–2) | Art. IV compliance |
| H15 | Coverage gates hold: `domain/` and `application/` at 90% or above, global at 80% or above (Art. II) | Art. II compliance |

---

## 9. Traceability

`docs/traceability-matrix.md` MUST gain one row per requirement `REQ-003-001` … `REQ-003-023`,
each carrying its `AC-003-##` reference, its test file(s), its task ID(s) and its status, before this
capability can be considered done (Art. I.5, Art. XI, `AGENTS.md` §10).

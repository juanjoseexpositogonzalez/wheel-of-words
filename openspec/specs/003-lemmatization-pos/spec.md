# Specification for 003-lemmatization-pos

This is the specification for capability `003-lemmatization-pos`: per-occurrence lemma and
part-of-speech annotation, its provenance and confidence, and the read-time precedence mechanism
that makes reprocessing safe.

It is a **new capability**, so the original 23 requirements (`REQ-003-001` … `REQ-003-023`) below
are a full specification, not a delta. One separate delta accompanied it — `../002-text-import/spec.md`
— and it modified exactly one requirement of `002-text-import`. See §6 `CONTRA-1` for why that delta
was unavoidable and why it was the *only* change made to SPEC-002.

A later archived change, `spec-003-harden-guards-and-claims`, added six hardening requirements
(`REQ-003H-001` … `REQ-003H-006`) and their normative rules (§3 below). The archived source delta
remains at
`openspec/changes/archive/2026-08-26-spec-003-harden-guards-and-claims/specs/003-lemmatization-pos/spec.md`.
See §6 `DEC-1` for the pre-archive targeting decision.

Section numbers `§2`, `§2.x`, `§5`, `§6`, `§7`, `§8` referenced inside the original 23 requirements
refer to the sections of this document. Section references of the form `§3.x` referenced inside the
hardening requirements (§3 and `REQ-003H-###`) refer to §3 of this document. References of the form
`§2.x` prefixed with `SPEC-002` refer to `openspec/specs/002-text-import/spec.md`.

## 1. Metadata

| Field | Value |
|-------|-------|
| Capability | `003-lemmatization-pos` |
| Requirement prefix | `REQ-003-###` (original) and `REQ-003H-###` (hardening) — the `H` deliberately distinguishes the two families |
| Acceptance prefix | `AC-003-##` (original) and `AC-003H-##` (hardening) |
| Roadmap item | 4 — Lematización y POS (`docs/product-vision.md` §12) |
| Governing constitution | v2.0.0 (2026-07-15, multi-language amendment 2026-07-16) |
| Governing ADRs | 0001, 0002, 0003, 0005, 0006, 0007, 0008, 0009, 0010, **0011** |
| Language | English (methodology artifact, ADR-0010). Product docs stay Spanish. |
| Test runner | `cd apps/api && uv run pytest` — strict TDD, zero-warning `filterwarnings` gate |
| Depends on | `002-text-import` (archived, 23 requirements) |
| Hardening evidence base | Engram observation `#4790`, `sdd/lemmatization-pos/judgment-ledger` — frozen adversarial ledger, treated as established fact and not re-investigated |
| State to preserve | 503 backend / 67 frontend / 4 E2E green; 100% backend coverage; `domain`+`application` ≥90%, global ≥80%; linters clean; `api/schemas/import.v1.json` byte-identical at SHA-256 `def94cb6…554258`; `annotation.v1.json` byte-identical |

**What the hardening change was.** Two Judgment Day rounds patched symptoms. Six findings (H1–H6)
survived, each with an existing reproduction. Every one of them is a **binding-granularity defect**:
a rule was stated at a coarser grain than the thing it was meant to constrain — an exemption bound
to a container instead of to a name, to a syntactic category instead of to an instance, a claim
written by hand instead of derived from its subject, an obligation enforced in code but not stated
in the contract, and a guarantee stated stronger than the check that backs it. The hardening delta
specified the **invariant each of those grains must satisfy**, not a patch per symptom.

**What the hardening change was not.** It re-opened nothing recorded as closed. Out of scope, and
MUST NOT be addressed there: the parser exclusion (ADR-0011 records it as a knowingly deferred
architecture decision); f-string / `str.join` / `%`-format evasions of the isolation guard;
`_path_segments` nested-array handling; memory footprint; the one-`UPDATE`-per-occurrence design;
registry thread-safety; the `SPACE` POS tag; unit-test markers opening databases; and everything
both judges confirmed closed — SQLite chunking, model-path translation, the deletion cascade,
score-normalization checks, and the main same-text swap case.

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
be narrowed. That is a real, resolvable conflict, not a naming argument — see §6 `CONTRA-1` and
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
| P4 | `PROPN` MUST be persisted like every other tag. No filter, no suppression, no special case ships in this capability | Decision: proper-noun handling is roadmap item 6. Filtering here would pre-empt that capability's design with an unreviewed heuristic. See §7 PV-4 and §8 |
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
| C6 | In this capability confidence is **informational only**. No filter, sort, threshold, warning, block, or automatic re-run MAY key off it | Acting on low confidence requires a correction path, which is SPEC-004. See §6 `AMB-2` — this is a knowingly accepted tradeoff with a recorded consequence, not an oversight |

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

## 3. Normative rules (hardening)

Everything in this section is normative and binding on the hardening requirements in §4
(`REQ-003H-001` … `REQ-003H-006`). Each rule is cited by identifier from the acceptance criteria that
enforce it. These rules were added by the archived change `spec-003-harden-guards-and-claims`.

### 3.1 Binding granularity — an exemption binds to a name at a site, never to a container

A guard is a total prohibition minus an enumerated set of exemptions. Its strength is decided
entirely by how precisely each exemption is bound. The observed defects are all the same shape: the
Python leg binds `symbol → module`, the reflected-column leg binds `column → table`, and the JSON leg
binds `path → component` — a container that also holds names the guard is supposed to catch.

| # | Rule | Reason |
|---|------|--------|
| B1 | Every exemption SHALL be the pair `(exact name, owning site)`. Neither half alone MAY exempt anything. An exact-name match at a non-owning site MUST produce a violation, and an owning site MUST NOT exempt a name outside the enumeration | This is already the shipped Python and reflected-column behaviour. Stating it as the invariant is what makes the other legs' deviation a specification violation rather than a style difference |
| B2 | The owning site SHALL be the **narrowest structural unit the leg's own parse exposes that can contain exactly the exempt names and nothing else**. Per leg: Python → `(symbol, module path)`; reflected columns → `(column, table)`; JSON Schema → `(property name, declaring schema definition)`; served OpenAPI → `(property name, declaring schema component)`; TypeScript → `(symbol, module path)` | "Narrowest unit the parse exposes" is verifiable against the parse tree. "Reasonably narrow" is not |
| B3 | Binding an exemption to a container that also holds non-exempt names is FORBIDDEN. Where such a binding exists, renaming any non-exempt member of that container to an exempt name MUST produce a violation | `$defs.occurrence` holds `position`, `raw_text`, `pos`, `pos_origin`, `automatic_pos`, `pos_confidence` alongside the four lemma-bearing properties. Binding to the component exempts all ten. This is the exact mutation `docs/traceability-matrix.md` cites as proof of closure, and it currently yields zero violations |
| B4 | A structural path SHALL be decomposed by the traversal that produced it, never by re-splitting a rendered path string on a delimiter that MAY legally occur inside a name. A key literally named `occurrence.extra` MUST NOT decompose into the segments `occurrence` and `extra` | Re-splitting on `.` makes any name containing a dot inherit the exemption of a same-named ancestor segment. The path renderer and the path matcher must agree, and the only way to guarantee that is to carry the segments rather than reconstruct them |
| B5 | An implementation of B1–B4 SHALL exist **once**. Two guards MUST NOT carry independently maintained copies of the same helper | The helper is duplicated across `test_no_lemma_naming.py` and `test_annotation_contract.py`, so a fix applied to one leaves the other exploitable. That is the observed condition, not a hypothetical |
| B6 | A per-site owning set MUST enumerate only the names that site legitimately declares or handles. Granting a site the whole allow-list is a container binding wearing B1's clothes | The frontend leg maps both owning files to the entire symbol set, so `lemmatizer` — a spaCy pipe name that no frontend module declares — is exempt in `apps/web` where nothing owns it |

### 3.2 Exemption scoping — an exemption names the instance that earned it

| # | Rule | Reason |
|---|------|--------|
| E1 | An exemption SHALL name the **instance** that produced the false positive, never the syntactic category that instance belongs to | `_DOCSTRING_OWNERS = (ast.Module,)` exempts every module docstring in the scan because one module's explanatory prose tripped the guard. One instance earned it; a category received it |
| E2 | Every exemption SHALL record, adjacent to itself, (a) the specific false positive that earned it, and (b) why the exempted region cannot carry a real violation — by exactly one of: **(b-i)** a downstream leg re-catches anything published from that region, or **(b-ii)** the exempted region is a single enumerated, reviewed instance | Without (b) an exemption is an assertion of safety with no stated mechanism. The two guards in question differ precisely here, and that difference must be written down rather than inferred — see §6 `CONTRA-3` |
| E3 | An exemption justified as "this region is prose" MUST NOT be granted to a region that is runtime-reachable, unless E2(b-i) applies. A module docstring is reachable as `__doc__` exactly as a function docstring is | This is the fix's own stated reason for revoking the function and class exemptions. Applying that reason to two of three cases and not the third is the defect. Reproduced: a module docstring holding `DELETE FROM manual_correction WHERE 1=1`, executed via `text(__doc__)`, yields zero violations |
| E4 | Where an exemption rests on E2(b-ii), the guard SHALL **pin the exempted instance's content**, so that replacing the reviewed prose with a real violation still fails | A named-instance exemption bounds *where* a violation can hide but not *what* can be put there. Pinning the content closes the remainder without widening the guard |

### 3.3 Evidence obligations for absence assertions

Every hardening requirement in §4 that is enforced by an assertion of the form "there are zero
matches" carries all three of these. This repository's guards have twice passed while proving nothing.

| # | Rule |
|---|------|
| M1 | Each absence assertion SHALL be accompanied by a **mutation check**: a real violation of exactly the kind the assertion exists to catch, introduced and observed failing, with the **observed failure output recorded verbatim in the test docstring** |
| M2 | Each scan, walk, glob, or enumeration SHALL have a **non-vacuity test** that fails closed when the enumeration resolves to zero inputs or fails to reach a named expected input |
| M3 | Each exemption SHALL have a **boundary control test**: the same construct placed outside the exempt site still produces a violation, proving the miss the exemption creates is exactly the miss it was granted |

### 3.4 Prohibited remedies

| # | Rule |
|---|------|
| W1 | No hardening requirement in §4 MAY be satisfied by **deleting a guard**, by **excluding a file or directory** from a walk, by **weakening a search pattern**, by **relaxing an AST criterion to a text search**, or by **narrowing the set of scanned inputs** |
| W2 | No hardening requirement in §4 MAY be satisfied by **adding an entry to an allow-list** or by **widening an owning set** in place of tightening a binding |
| W3 | No hardening requirement in §4 MAY be satisfied by **removing the subject of a claim** in place of correcting the claim. The single exception is `REQ-003H-003`, where deleting the **prose claim** is an explicitly permitted remedy — deleting the guard, the enumeration, or the pinned model is not |
| W4 | Every guard MUST still walk every input it walked before this change, and every leg MUST remain parse-based where it is parse-based today |

### 3.5 Claim provenance — assertions about a pinned model are generated, not written

| # | Rule | Reason |
|---|------|--------|
| K1 | A document assertion about the internals of the pinned model — rule counts, the contents of the `attribute_ruler` rule table, per-target fine-tag cardinality, the exactness of any `fine tag → UPOS` mapping, or any measured posterior — SHALL be produced by an **executable enumeration of that model**, or SHALL NOT appear in prose | Three consecutive rounds asserted a false fact in this same paragraph, each time by *reasoning* about the rule table instead of enumerating it. Round 2 was explicitly instructed to verify empirically and shipped a different false claim. The defect class is hand-written model-internal prose, not any individual sentence |
| K2 | The enumeration SHALL read the pinned model **at run time**. It MUST NOT restate a value transcribed from a previous run, and no expected value MAY be hardcoded except as a mutation fixture | A transcribed number is a hand-written claim with an extra step |
| K3 | The enumeration SHALL account for **this adapter's actual runtime pipe set**, and SHALL report reachable and structurally unreachable rules separately | `parser` is excluded (ADR-0011), so `DEP` is unset and `DEP`-conditioned rules can never fire. The AUX rule-count claim is wrong precisely because a `DEP`-conditioned catch-all rule mapping 46 of 50 fine labels was counted as if the table alone decided the answer, and one mapping's exactness comes from an exception that is unreachable for the same reason. Reachability is load-bearing, not a detail |
| K4 | The enumeration MAY require the model to be loaded and MAY therefore be gated `@pytest.mark.integration`. `domain` stays stdlib-only (SPEC-003 `REQ-003-002`). A gated test MUST still execute under the project's standard verification command, and MUST fail loudly rather than pass vacuously when the model is absent | Gating is a cost control, not an escape hatch |
| K5 | **This specification states no exact-mapping set, no rule count, and no posterior**, and no downstream artifact of this change may introduce one except as the enumeration's output. K1 binds this document too | Writing the fourth hand-written claim inside the requirement that forbids hand-written claims is the failure mode most available to this change. See §6 `CONTRA-4` |

### 3.6 Claim strength — a guarantee never exceeds the check that backs it

| # | Rule | Reason |
|---|------|--------|
| G1 | A stated guarantee SHALL NOT exceed what the check enforces. Where a check consumes a value **the checked party itself reports**, the guarantee is the reporter's **self-consistency with its input**, never the correctness of what it reported | `source_index` is self-reported by the analyzer. A swap of two same-text annotations with consistently reassigned indices passes. The shipped adapter derives `source_index` from the document's own enumeration and cannot exhibit this, which makes it a contract-strength question, not a live defect |
| G2 | A bounded guarantee SHALL be stated identically in **every** location that carries it — the port contract, the specification, and `docs/traceability-matrix.md` — within **one work unit**. No partial correction may stand | Precedent: SPEC-003 §6 `FACT-1`, corrected across six artifacts in one work unit specifically so no stale copy survived. The present cycle exists because a claim was written stronger than its enforcement; leaving one copy strong would repeat it |
| G3 | An accepted bound SHALL be **executable**: a test MUST exercise the case the guarantee does not cover and record its acceptance as specified behaviour | An accepted limitation recorded only in prose is indistinguishable from an unnoticed one. Making it a passing test with a stated reason gives a future change something to flip |

---

## 4. Requirements

### Requirement: REQ-003-001 — The backend runtime is pinned to Python 3.12

The `apps/api` project SHALL pin its resolved interpreter to Python 3.12. `pyproject.toml` MUST
declare an upper bound that excludes 3.14 and above, and the resolved virtual environment MUST
report a 3.12 version. This pin is a **hard prerequisite** and MUST land before any NLP dependency
is added.

**Why, verified rather than assumed.** `spacy 3.8.15` publishes wheels for **cp312 and cp313
only** — no cp314 — making spaCy itself the narrowest constraint in the chain. (`spacy 3.8.15`
declares `thinc<8.4.0,>=8.3.12` and never resolves thinc 9.x; the `thinc 8.3.13` this project
actually resolves publishes wheels for cp312, cp313 **and** cp314, so thinc is not the constraint —
see §6 FACT-1 for the full record of this correction.) The repository's `apps/api/.venv` currently
resolves to **3.14.5**, and `spacy`'s declared `requires_python: <3.15,>=3.9` is **not** a safety
net: the resolution succeeds and then attempts a fragile C++/Cython source build against an
interpreter with no prebuilt spaCy wheel. A green `uv add` is not evidence of a working install.

`requires-python` states what is *supported* (bounded by spaCy's wheel matrix). `.python-version`
states what is *tested*: it stays pinned to exactly `3.12`, the single interpreter this project runs
its suite against, which matters with a pinned statistical model. The two are allowed to differ, and
do, on purpose.

Acceptance: **AC-003-01** — Given the `apps/api` project, when the resolved interpreter version is
read, then it is `3.12.x`; and when `pyproject.toml` is read, then `requires-python` excludes `3.14`
and above; and when `mypy`'s `python_version` is read, then it is `3.12`, matching the runtime.

#### Scenario: The venv resolves to the pinned interpreter

- GIVEN the `apps/api` project after dependency installation
- WHEN the interpreter version is queried
- THEN it reports `3.12.x`

#### Scenario: The declared bound cannot silently drift upward

- GIVEN `pyproject.toml`
- WHEN `requires-python` is read
- THEN it excludes `3.14` and above
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
blocking state, or automatic re-run MAY key off it (C6). See §6 `AMB-2` for the accepted consequence.

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

Every read that exposes an effective `pos` or `lemma` SHALL resolve it by the §2.5 precedence rule: the
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
is **stability under re-run**, specified above. See §6 `AMB-1`.

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
for no other. See §6 `CONTRA-1`.

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

### Requirement: REQ-003H-001 — Every guard exemption binds to a name at its owning site

Every exemption in every leg of the `AC-002-10` naming guard and of the annotation-contract guard
SHALL satisfy §3.1 B1–B6. The JSON Schema and served-OpenAPI legs MUST bind each exemption to a
**lemma-bearing property name within its declaring schema definition**, never to the definition as a
whole. Path decomposition MUST satisfy B4. The helper implementing this binding MUST exist once and
be shared by both guards (B5). Each leg's owning set MUST enumerate only the names that site
legitimately declares (B6).

This requirement is the invariant, stated once, that every leg must satisfy. It MUST NOT be
discharged by patching the JSON leg alone. `annotation.v1.json` and `import.v1.json` MUST remain
byte-identical: the defect is in the guard's binding, not in the schemas. §3.4 W1, W2 and W4 apply in
full.

Acceptance: **AC-003H-01** — Given `annotation.v1.json`, when each of `position`, `raw_text`, `pos`,
`pos_origin`, `automatic_pos` and `pos_confidence` inside `$defs.occurrence` is renamed **in turn** to
the bare allow-listed name `lemma`, then **each** rename produces at least one violation; and given
the four genuinely lemma-bearing properties of that same definition, when the guard runs unmutated,
then there are zero violations; and given a document containing an object key literally named
`occurrence.extra` whose value is an allow-listed name, when the guard runs, then it produces a
violation; and given the frontend leg, when the owning set of each owning file is read, then it
contains only names that file declares and does not contain `lemmatizer`; and given both Python
guards, when the binding helper is located, then exactly one implementation exists and both import
it; and given the schema glob, when it resolves to zero files, then the suite fails; and given each
absence assertion above, when its test is read, then its docstring records the observed failure
output of a real mutation (§3.3 M1–M3).

#### Scenario: Renaming a sibling property to an allow-listed name is caught

- GIVEN `annotation.v1.json` with `$defs.occurrence.properties.raw_text` renamed to `lemma`
- WHEN the naming guard and the annotation-contract guard run
- THEN each reports at least one violation
- AND the same holds for `position`, `pos`, `pos_origin`, `automatic_pos` and `pos_confidence`

#### Scenario: The genuine lemma properties still pass

- GIVEN the unmutated `annotation.v1.json`
- WHEN both guards run
- THEN `lemma`, `lemma_confidence`, `lemma_origin` and `automatic_lemma` produce zero violations
- AND the schema file is byte-identical to its pre-change bytes

#### Scenario: A key containing a dot does not inherit an ancestor's exemption

- GIVEN a JSON document with an object key literally named `occurrence.extra` holding an allow-listed name
- WHEN the guard decomposes that path
- THEN the key is not treated as passing through an owning segment
- AND a violation is reported

#### Scenario: An owning set grants only what its site declares

- GIVEN the frontend guard's per-file owning sets
- WHEN each is read
- THEN it enumerates only names that file declares
- AND `lemmatizer` is exempt in no frontend file

#### Scenario: The binding helper exists once

- GIVEN the two Python guards
- WHEN the path-decomposition and binding helper is located
- THEN exactly one implementation exists and both guards import it

#### Scenario: The scan fails closed

- GIVEN a schema glob that resolves to zero files
- WHEN the suite runs
- THEN it fails rather than passing vacuously

### Requirement: REQ-003H-002 — Every guard exemption names the instance that earned it

Every exemption in the annotation write-path isolation guard SHALL satisfy §3.2 E1–E4. The docstring
exemption MUST be scoped to the **specific module** whose explanatory prose produced the false
positive, identified by module path, and MUST NOT be expressed as a syntactic category such as "every
module docstring". Its justification MUST be recorded per E2, and because it rests on E2(b-ii) the
exempted docstring's content MUST be pinned per E4.

The function and class legs are already closed and MUST remain closed. §3.4 W1 and W4 apply: the
guard MUST continue to walk every module it walks today, and MUST remain AST-based.

Acceptance: **AC-003H-02** — Given a synthetic module whose **module docstring** is
`DELETE FROM manual_correction WHERE 1=1`, when the isolation guard runs over it, then it reports a
violation, and the test docstring records the observed failure output; and given the one production
module whose module docstring legitimately names the correction table in explanatory prose, when the
guard runs over the shipped tree, then there are zero violations; and given that same module with its
exempted docstring replaced by text that is not the reviewed prose, when the guard runs, then it
reports a violation (E4); and given the same SQL placed in a function docstring, in a class
docstring, and as an ordinary string literal, when the guard runs, then each reports a violation
(§3.3 M3); and given the guard's module walk, when it resolves to zero modules or fails to reach
`annotation_write_repository.py`, then the suite fails (M2).

#### Scenario: A module docstring holding forbidden SQL is caught

- GIVEN a synthetic module whose module docstring is `DELETE FROM manual_correction WHERE 1=1`
- WHEN the isolation guard runs
- THEN it reports a violation
- AND the test docstring records the observed failure output

#### Scenario: The one reviewed prose docstring still passes

- GIVEN the production module whose module docstring explains, in prose, that it never references the correction table
- WHEN the guard runs over the shipped tree
- THEN there are zero violations

#### Scenario: The exempted instance's content is pinned

- GIVEN the exempted module docstring replaced by text other than the reviewed prose
- WHEN the guard runs
- THEN it reports a violation

#### Scenario: The already-closed legs stay closed

- GIVEN the same SQL in a function docstring, a class docstring, and an ordinary string literal
- WHEN the guard runs over each
- THEN each reports a violation

#### Scenario: The module walk fails closed

- GIVEN a walk that reaches no module, or that omits `annotation_write_repository.py`
- WHEN the suite runs
- THEN it fails

### Requirement: REQ-003H-003 — Claims about pinned-model internals are generated by executable enumeration or do not exist

`openspec/specs/003-lemmatization-pos/spec.md` (this document) and `docs/traceability-matrix.md` SHALL NOT contain
a hand-written assertion about the pinned `en_core_web_sm` model's internals, as defined by §3.5 K1.
Each such claim MUST either **(a)** be the output of an executable enumeration satisfying K2, K3 and
K4, cited from the prose that carries it, or **(b)** not exist.

The enumeration MUST report, from the pinned model read at run time: the total rule count of
`attribute_ruler`; for each target UPOS, the set of distinct fine tags that reach it; the subset of
those rules that are structurally unreachable under this adapter's `_EXCLUDED_PIPES` and the reason;
and the set of `fine tag → UPOS` mappings that are exact, computed from the foregoing rather than
asserted.

The existing self-contradiction — a prose claim that a named pair of mappings is exhaustively "the
only" exact ones, contradicted two paragraphs later by admitting a third — MUST be resolved by
**replacing the claim with a reference to the enumeration's output**, not by editing the sentence.
Rewording is the remedy that has already failed three times. §3.5 K5 binds this change's own
artifacts: no requirement, task, design note, or commit message produced here may state which
mappings are exact.

Acceptance: **AC-003H-03** — Given the pinned model loaded at run time, when the enumeration runs,
then it emits the rule count, the per-target fine-tag sets, the reachable/unreachable partition under
`_EXCLUDED_PIPES`, and the computed exact-mapping set, and the test asserts the documented claim
against that output rather than against a transcribed constant; and given this document §P1 and
`docs/traceability-matrix.md`, when each is searched for a rule count, a per-target tag count, a
posterior value, or an exactness assertion that is not carried by a citation of the enumeration, then
there are zero matches; and given the same two documents, when they are read end to end, then no
statement in either contradicts another; and given the enumeration test with one expected value
mutated, when it runs, then it fails, and its docstring records the observed failure output; and given
an environment where the pinned model cannot be loaded, when the suite runs, then the test is skipped
or fails explicitly and never reports a vacuous pass; and given `domain/`, when its imports are
inspected structurally, then it still imports only the standard library.

#### Scenario: The claim is the enumeration's output

- GIVEN the pinned model loaded at run time
- WHEN the enumeration runs
- THEN it emits the rule count, per-target fine-tag sets, the reachable/unreachable partition, and the computed exact-mapping set
- AND the documented claim is asserted against that output, not against a transcribed constant

#### Scenario: No hand-written model-internal claim survives

- GIVEN this document §P1 and `docs/traceability-matrix.md`
- WHEN each is searched for a rule count, a tag count, a posterior, or an exactness assertion
- THEN every match is carried by a citation of the enumeration
- AND no statement in either document contradicts another

#### Scenario: The enumeration is not vacuous

- GIVEN the enumeration test with one expected value mutated
- WHEN it runs
- THEN it fails
- AND its docstring records the observed failure output

#### Scenario: A missing model does not produce a silent pass

- GIVEN an environment where the pinned model cannot be loaded
- WHEN the suite runs
- THEN the test is skipped or fails explicitly
- AND it never reports a vacuous pass

#### Scenario: The domain stays stdlib-only

- GIVEN `domain/` after the enumeration ships
- WHEN its imports are inspected structurally
- THEN only standard-library modules are imported

### Requirement: REQ-003H-004 — The analyzer port documents every obligation the application enforces

Every property of a port's return value that the application **rejects** SHALL be stated as a
documented obligation on that port. No rejection branch MAY exist without a corresponding documented
obligation, because an adapter that satisfies the whole documented contract and is still rejected at
run time makes the contract false.

Specifically, `LinguisticAnalyzer.analyze` MUST document the `source_index` obligation the write path
already enforces: the annotation at list index `i` MUST carry `source_index == i`, the zero-based
index of the token in the supplied `tokens` sequence it was computed for. The documentation MUST name
the failure — `ANNOTATION_FAILED` — and MUST sit alongside the existing `raw_text` obligation rather
than replacing it. The two obligations are checked together and MUST be documented together.

`source_index` MUST also be discoverable outside the source file: it MUST appear wherever the
annotation contract is described in `docs/`. This requirement adds documentation and MUST NOT change
the enforced behaviour, the port's signature, or the persisted schema.

Acceptance: **AC-003H-04** — Given `application/annotation/ports.py`, when
`LinguisticAnalyzer.analyze`'s documented contract is read, then it states the `source_index == i`
obligation, names `ANNOTATION_FAILED` as its failure, and retains the `raw_text` obligation; and given
every rejection branch of the application's annotation validation, when each is enumerated, then each
has a documented obligation on the port it validates; and given a test double that satisfies every
documented obligation, when annotation runs, then it is accepted and rows are written; and given the
documented obligation sentence deleted, when the guarding test runs, then it fails, with the observed
failure output recorded in its docstring; and given `docs/`, when it is searched for `source_index`,
then the annotation contract description names it.

#### Scenario: The port states the obligation the code enforces

- GIVEN `ports.py`
- WHEN `LinguisticAnalyzer.analyze`'s documented contract is read
- THEN it states the `source_index == i` obligation and names `ANNOTATION_FAILED`
- AND the existing `raw_text` obligation is still stated

#### Scenario: A fully conformant adapter is accepted

- GIVEN a test double satisfying every documented obligation of the port
- WHEN annotation runs
- THEN the run succeeds and rows are written

#### Scenario: Every rejection branch has a documented obligation

- GIVEN every rejection branch of the application's annotation validation
- WHEN each is enumerated against the port's documented obligations
- THEN each branch maps to a documented obligation

#### Scenario: The documentation guard is not vacuous

- GIVEN the documented obligation sentence removed from the port
- WHEN the guarding test runs
- THEN it fails
- AND its docstring records the observed failure output

### Requirement: REQ-003H-005 — The traceability matrix describes the shipped mechanism

`docs/traceability-matrix.md` SHALL describe the mechanism that actually ships. The `REQ-003-004` row
MUST state that annotation-to-occurrence pairing is verified by **both** `raw_text` content equality
**and** `source_index == position`; MUST cite the regression test that reproduces the same-text swap;
and MUST describe the property test in its **shipped** form rather than its superseded pre-fix form.

The row MUST NOT describe the `raw_text` check as verification "by identity": the review established
that it is content equality, which is exactly why `source_index` was added. Per §3.6 G1 the wording
MUST match the strength of the check. The matrix MUST also gain one row per requirement
`REQ-003H-001` … `REQ-003H-006`, each carrying its `AC-003H-##` reference, its test file(s), its task
ID(s) and its status. `docs/` is Spanish (ADR-0010); these edits stay Spanish.

Per `AGENTS.md` §10 this change is not done until the matrix is correct.

Acceptance: **AC-003H-05** — Given the `REQ-003-004` row, when it is read, then it names both the
`raw_text` and the `source_index` checks, cites the swap regression test, and describes the property
test's current form; and given the whole matrix, when it is searched for a claim that pairing is
verified by identity, then there are zero matches; and given every test name the matrix cites, when
each is resolved against the suite, then each exists — a row citing a test that does not exist MUST
fail the check; and given the matrix, when it is read, then rows exist for `REQ-003H-001` …
`REQ-003H-006` with acceptance, test, task and status populated.

#### Scenario: The row describes what ships

- GIVEN the `REQ-003-004` row
- WHEN it is read
- THEN it names both the `raw_text` and the `source_index` checks
- AND it cites the swap regression test and the property test's current form

#### Scenario: The superseded wording is gone

- GIVEN the whole matrix
- WHEN it is searched for a claim that pairing is verified by identity
- THEN there are zero matches

#### Scenario: Every cited test exists

- GIVEN every test name the matrix cites
- WHEN each is resolved against the suite
- THEN each exists
- AND a row citing a nonexistent test fails the check

#### Scenario: The new requirements are traceable

- GIVEN the matrix after this change
- WHEN it is read
- THEN one row exists per `REQ-003H-001` … `REQ-003H-006` with acceptance, test, task and status

### Requirement: REQ-003H-006 — The `source_index` guarantee is stated at its true strength

The guarantee the pairing check provides SHALL be stated per §3.6 G1–G3, and the mechanism MUST NOT
be strengthened in this change (§6 `DEC-2`).

The accurate, bounded statement is: the check proves that the analyzer's output is **self-consistent
with the input it was given** — each annotation reports both the token text and the input index it
claims to have been computed for, and both MUST agree with the occurrence at that position, so an
internally reordered result of equal length is rejected instead of being written to the wrong
occurrence. It does **not** prove that the annotation is linguistically correct for that token, and it
cannot detect an analyzer that swaps two same-text annotations while consistently reassigning
`source_index`, because `source_index` is self-reported by the analyzer.

The shipped adapter derives `source_index` from the document's own enumeration and therefore cannot
exhibit that residual case. Strengthening the mechanism would require a source of truth independent
of the analyzer, which is over-engineering for a case the shipped adapter cannot produce. That is a
recorded decision, not a silent omission.

This bounded statement MUST appear, in the same terms, in the port contract, in the specification, and
in `docs/traceability-matrix.md`, within one work unit (G2). No location may keep the stronger
wording.

Acceptance: **AC-003H-06** — Given the port contract, the specification and the traceability matrix,
when each is read, then each states the bounded guarantee in the same terms, and none claims
correctness, tamper-resistance, or verification by identity; and given a stub analyzer that swaps two
same-text annotations while consistently reassigning `source_index`, when annotation runs, then the
run is accepted, and a test records that acceptance as the documented bound with a citation to this
requirement (G3); and given a stub analyzer that swaps two same-text annotations **without**
reassigning `source_index`, when annotation runs, then it fails with `ANNOTATION_FAILED` and writes
nothing; and given the shipped adapter, when `source_index` is produced, then it is the document's own
enumeration index.

#### Scenario: One bounded statement, three locations

- GIVEN the port contract, the specification and the traceability matrix
- WHEN each is read
- THEN each states the same bounded guarantee
- AND none claims correctness, tamper-resistance, or verification by identity

#### Scenario: The uncovered case is accepted, and executable

- GIVEN a stub analyzer that swaps two same-text annotations and consistently reassigns `source_index`
- WHEN annotation runs
- THEN the run is accepted
- AND a test records that acceptance as the documented bound, citing this requirement

#### Scenario: The covered case still fails

- GIVEN a stub analyzer that swaps two same-text annotations without reassigning `source_index`
- WHEN annotation runs
- THEN it fails with `ANNOTATION_FAILED` and writes nothing

#### Scenario: The adapter cannot exhibit the residual case

- GIVEN the shipped adapter
- WHEN `source_index` is produced
- THEN it is the document's own enumeration index

---

## 5. Error contract

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

## 6. Ambiguities, contradictions and decisions recorded and resolved (AGENTS.md §9)

Each item below was an ambiguity or a contradiction in the inputs. None was resolved silently.

| ID | Ambiguity, contradiction or open decision | Resolution | Status |
|----|-------------------------------------------|------------|--------|
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
| **FACT-1** | **A factual error in the recorded rationale for `REQ-003-001`, propagated into this spec, design.md, tasks.md, proposal.md, the traceability matrix, and the implemented `requires-python` bound.** The original claim was: "`thinc 9.1.1` publishes wheels for cp312 only, and is the narrowest constraint in the dependency chain, therefore the interpreter must be pinned below 3.13." This was false — the inspected `thinc` version was simply the wrong one; nothing in this project's dependency graph ever resolves thinc 9.x. | **Refuted by direct evidence, re-checked against PyPI and the resolved `apps/api/uv.lock`.** `spacy 3.8.15` declares `thinc<8.4.0,>=8.3.12` and never resolves thinc 9.x. `thinc 8.3.13` — the version this project actually resolves — publishes wheels for **cp312, cp313 and cp314** (`requires_python: <3.15,>=3.10`). `spacy 3.8.15` itself publishes wheels for **cp312 and cp313 only** — no cp314. Therefore **spaCy, not thinc, is the narrowest constraint**, and the correct upper bound is `<3.14`, not `<3.13`; Python 3.13 would have worked. `requires-python` is widened to `>=3.12,<3.14` everywhere it was recorded. `.python-version` stays pinned to exactly `3.12` — deliberately narrower than the supported range, because it names the single interpreter this project's suite actually tests against, which matters with a pinned statistical model. `requires-python` states what is *supported*; `.python-version` states what is *tested*. They are allowed to differ, and now do, on purpose. **Method lesson: when reasoning about wheel availability for a transitive dependency, inspect the version the resolver actually selects (`uv.lock`), never the latest release on PyPI.** | **Closed. Corrected in this spec, `design.md`, `tasks.md`, `proposal.md`, `docs/traceability-matrix.md`, `test_python_pin.py`, and `pyproject.toml` in the same work unit — no partial correction left standing** |
| **DEC-1** | **Pre-archive delta-spec target.** Before archive, `003-lemmatization-pos` had no baseline spec: it existed only in the not-yet-archived `lemmatization-pos` change, so "amend the baseline" was not available and "amend the other change's files directly" would have erased this change's own audit trail. | The change carried its own delta specs under `openspec/changes/spec-003-harden-guards-and-claims/specs/`, which amended the in-flight `openspec/changes/lemmatization-pos/specs/` documents. Archive promoted the reconciled hardening requirements into `openspec/specs/003-lemmatization-pos/spec.md` and preserved the original delta under `openspec/changes/archive/2026-08-26-spec-003-harden-guards-and-claims/`. Settled by the orchestrator. | **Closed. Do not re-open** |
| **DEC-2** | **H6 direction.** Strengthen the `source_index` mechanism, or state the real bounded guarantee accurately. | **State the bounded guarantee** (`REQ-003H-006`). Strengthening requires a source of truth independent of the analyzer, which is over-engineering for a case the shipped adapter cannot exhibit. **This whole cycle exists because claims were written stronger than what is enforced; the fix must not repeat that pattern.** Settled by the orchestrator. | **Closed. Do not re-open** |
| **DEC-3** | Whether these findings modify existing `003-lemmatization-pos` requirements. `REQ-003-004` and `REQ-003-011` are the requirements whose guards have holes. | **`ADDED` only.** Neither requirement is wrong — each is silent where this change adds an obligation. Under the delta convention a `MODIFIED` block replaces the whole requirement at archive time, so re-stating a correct requirement in order to append to it risks losing scenarios for no gain. The one genuine `MODIFIED` is `REQ-002-007`, in the companion delta, because its acceptance criterion is currently satisfiable by a guard that has the hole. | Accepted |
| **REC-1** | **H3 has been wrong three times running**, in the same paragraph. Round 1 wrote a false claim. Round 2, explicitly instructed to verify empirically, wrote a *different* false claim and shipped a statement that contradicts itself two paragraphs later. Round 3 would be a fourth attempt at the same method. | The requirement is **structural, not editorial** (`REQ-003H-003`, §3.5). "Write the paragraph correctly" is forbidden as a remedy: it is what failed twice. The claim must be produced by an executable enumeration bound to the pinned model, or must not exist. Hand-written model-internal prose is treated as the **defect class**, not the sentence as the defect. | **Closed as specified. The remedy is generation, never rewording** |
| **CONTRA-3** | **Two guards define a docstring exemption and only one of them may keep a syntactic one.** `AC-002-10`'s Python leg exempts module, class and function docstrings; the write-path isolation guard was narrowed to module docstrings only and is still exploitable. Applying one rule to both would either re-break `AC-002-10` (whose own rationale requires prose to be able to name the concept it forbids) or leave the isolation guard open. | **Not a contradiction — the two differ under §3.2 E2.** `AC-002-10`'s exemption is justified by **E2(b-i)**: anything a docstring publishes is re-caught by the served-OpenAPI leg, which is exactly where a docstring stops being prose and becomes contract. The isolation guard has **no** re-catch leg, so its exemption can only be justified by **E2(b-ii)**, which requires a named instance and, per E4, pinned content. The rule is one rule; the two guards satisfy different clauses of it, and that MUST now be written down in each guard rather than inferred. | **Closed. `AC-002-10`'s docstring exemption is retained and its E2(b-i) justification made explicit; the isolation guard's is rescoped under E2(b-ii)+E4** |
| **AMB-10** | **`REQ-003H-002`'s residual.** Scoping the exemption to one named module still leaves that module's `__doc__` runtime-reachable. Narrowing alone does not close the hole; it only bounds where it can hide. | Closed by **E4**: the guard pins the exempted docstring's content, so replacing reviewed prose with a real violation fails. Bounding *where* plus pinning *what* is complete without widening the guard or removing a legitimate exemption. | Accepted |
| **CONTRA-4** | **This specification is itself at risk of becoming the fourth false model-internal claim.** The most natural way to specify `REQ-003H-003` is to state the correct exact-mapping set — which would be a hand-written assertion inside the requirement forbidding hand-written assertions. | **K5.** This document states no exact-mapping set, no rule count and no posterior, and forbids any downstream artifact of this change from introducing one except as the enumeration's output. The acceptance criterion asserts the *shape and provenance* of the enumeration's output, never its values. | **Closed. K1 binds this document** |
| **AMB-11** | K4 gates the enumeration as an integration test, which risks the claim being verified only in environments that have the model — while the documents it governs ship everywhere. | Accepted, with the consequence stated: the enumeration MUST fail loudly or skip explicitly when the model is absent, never pass vacuously, and it MUST run under the project's standard verification command. The prose-side check (zero un-cited model-internal claims in the two documents) is a **plain document scan** with no model dependency, so the falsifiable half of `REQ-003H-003` runs unconditionally. | **Accepted tradeoff, recorded** |
| **AMB-12** | H1 spans two capabilities: the naming guard belongs to `002-text-import`'s `AC-002-10`, the annotation-contract guard and `annotation.v1.json` to `003-lemmatization-pos`. Splitting the invariant across two deltas would let the two halves drift — the exact failure H1 is. | The invariant is defined **once**, here, as §3.1. The companion `002-text-import` delta amends `AC-002-10` to require it by reference rather than restating it. Precedent: the in-flight 002 delta already cites `003-lemmatization-pos` §6 `CONTRA-1` and `REQ-003-023`. | Accepted |

---

## 7. Product-visible decisions

These change what appears on screen. They are decisions, not implementation details.

| # | Decision | What the user sees | Status |
|---|----------|--------------------|--------|
| PV-1 | Lemma grouping is the primary value; POS is secondary (Decision 1) | `run`, `ran` and `running` are recognisably one word. Under budget pressure POS yields before lemma | Accepted |
| PV-2 | Confidence is always visible, on every classification, including when unreported | Every row shows a confidence value or an explicit "not reported" marker — never a blank cell and never a fabricated number | Accepted. Informational for one cycle (§6 AMB-2) |
| PV-3 | POS is shown as a UPOS tag, optionally localized into a readable label | The user sees `NOUN`/`VERB` semantics, not Penn Treebank codes like `NN`/`VBD` | Accepted |
| PV-4 | Proper nouns are tagged `PROPN` and shown like every other word | Character names and place names appear in the list. Excluding them arrives with roadmap item 6; `product-vision §10 step 4` is **knowingly unimplemented** until then | Accepted, explicitly incomplete |
| PV-5 | Annotation is an explicit step, not part of upload | Importing a file does not automatically produce lemmas; annotation is triggered separately, and existing imports can be annotated without re-uploading | Accepted (§2.6) |
| PV-6 | A corrected value is visibly marked as corrected | When SPEC-004 ships corrections, each field already carries an `automatic`/`manual` origin marker, so a user can see why a value differs from the pipeline output | Accepted |
| PV-7 | Multiword expressions are not detected | `give up` remains two separate annotated occurrences with their own lemmas. Unchanged from SPEC-002 §6 PV-3's neighbouring limitation | Accepted; roadmap item 7 / ADR-0009 |

---

## 8. Explicit non-additions

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

The hardening change does NOT specify, and MUST NOT be used to justify: re-applying the parser
exclusion or re-opening ADR-0011; f-string, `str.join` or `%`-format evasions of the isolation guard;
nested-array handling in JSON path decomposition; memory footprint; the one-`UPDATE`-per-occurrence
write design; registry thread-safety; the `SPACE` POS tag; unit-test markers that open databases; or
anything both judges confirmed closed — SQLite chunking, model-path translation, the deletion
cascade, score-normalization checks, and the main same-text swap case.

The hardening change also does NOT permit: strengthening the `source_index` mechanism (DEC-2);
changing the port's signature, the persisted schema, the error contract, or any runtime behaviour;
modifying `import.v1.json` or `annotation.v1.json`; or satisfying any hardening requirement by any
remedy §3.4 forbids.

Neither change chooses module names, file layouts, DTO shapes, route paths, column types, index
strategy, transaction boundaries, helper placement, task ordering, or slice boundaries —
`sdd-design` and `sdd-tasks` own those.

---

## 9. Verification hooks

| Hook | Check | Verifies |
|------|-------|----------|
| H1 | Resolved interpreter reports `3.12.x`; `requires-python` excludes `3.14+`; `mypy` `python_version` agrees; the NLP install compiles no source extension | AC-003-01 |
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
| HG1 | Renaming each of the six non-lemma properties of `$defs.occurrence` to `lemma` produces a violation in both guards; the four genuine lemma properties still pass; a key named `occurrence.extra` is caught; the frontend owning sets grant only declared names; exactly one binding helper exists and both guards import it; the schema glob fails closed | AC-003H-01 |
| HG2 | A synthetic module docstring holding `DELETE FROM manual_correction WHERE 1=1` produces a violation; the one reviewed production docstring passes; replacing its pinned content produces a violation; function docstring, class docstring and plain literal each still produce a violation; the module walk fails closed | AC-003H-02 |
| HG3 | The enumeration reads the pinned model at run time and emits rule count, per-target fine-tag sets, the reachable/unreachable partition under `_EXCLUDED_PIPES`, and the computed exact set; this document §P1 and the matrix carry zero un-cited model-internal claims and no self-contradiction; a mutated expected value fails; a missing model skips or fails, never passes; `domain/` remains stdlib-only | AC-003H-03 |
| HG4 | `ports.py` documents `source_index == i` and names `ANNOTATION_FAILED` while retaining the `raw_text` obligation; every rejection branch maps to a documented obligation; a fully conformant double is accepted; deleting the obligation sentence fails the guarding test; `docs/` names `source_index` | AC-003H-04 |
| HG5 | The `REQ-003-004` row names both checks, cites the swap regression test and the property test's current form; zero matches for a claim of identity-based pairing; every test name the matrix cites resolves against the suite; rows exist for `REQ-003H-001` … `REQ-003H-006` | AC-003H-05 |
| HG6 | Port contract, spec and matrix state the same bounded guarantee; a consistently-reindexed same-text swap is accepted and recorded as the documented bound; an inconsistently-reindexed swap fails `ANNOTATION_FAILED` and writes nothing; the adapter's `source_index` is the document's own enumeration index | AC-003H-06 |
| HG7 | Every absence assertion introduced or amended here carries a mutation check with observed output in its docstring (M1), a non-vacuity test (M2), and a boundary control (M3) | §3.3 compliance |
| HG8 | No guard deleted, no file or directory excluded, no pattern weakened, no AST criterion reverted to a text search, no allow-list entry added, no owning set widened; every guard walks every input it walked before | §3.4 compliance |
| HG9 | 503 backend / 67 frontend / 4 E2E green; 100% backend coverage held; `domain`+`application` ≥90%, global ≥80%; linters and type checks clean; `import.v1.json` SHA-256 `def94cb6…554258` and `annotation.v1.json` byte-identical | State preserved |

---

## 10. Traceability

`docs/traceability-matrix.md` MUST carry one row per requirement `REQ-003-001` … `REQ-003-023` and
`REQ-003H-001` … `REQ-003H-006`, each carrying its `AC-003-##` or `AC-003H-##` reference, its test
file(s), its task ID(s) and its status, and MUST have its `REQ-003-004` row corrected per
`REQ-003H-005`, before this capability can be considered done (Art. I.5, Art. XI, `AGENTS.md` §10).
`REQ-003H-005` is the requirement that makes this section enforceable rather than aspirational: every
test name the matrix cites must resolve against the suite.
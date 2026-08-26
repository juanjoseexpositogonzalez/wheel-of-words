# Specification for 003-lemmatization-pos hardening

Archived change: `spec-003-harden-guards-and-claims`.

This baseline specification records the archived hardening requirements added by
`spec-003-harden-guards-and-claims`. The archived source delta remains at
`openspec/changes/archive/2026-08-26-spec-003-harden-guards-and-claims/specs/003-lemmatization-pos/spec.md`.
See §4 `DEC-1` for the pre-archive targeting decision.

A companion delta accompanies it — `../002-text-import/spec.md` — which modifies exactly one
requirement of `002-text-import` (`REQ-002-007`/`AC-002-10`), because the binding invariant defined
in §2.1 below is cross-cutting and that requirement is where the naming guard's acceptance criterion
lives.

Section references of the form `§2.x` are to **this** document. References prefixed `SPEC-003 §n`
are to the in-flight `003-lemmatization-pos` specification.

## 1. Metadata

| Field | Value |
|-------|-------|
| Capability amended | `003-lemmatization-pos` (in-flight), `002-text-import` (companion delta) |
| Requirement prefix | `REQ-003H-###` — deliberately distinct from `REQ-003-###` so the two families cannot collide when both changes reconcile at archive |
| Acceptance prefix | `AC-003H-##` |
| Delta kind | `ADDED` only. No requirement of `003-lemmatization-pos` is modified, removed, or renamed — see §4 `DEC-3` |
| Governing constitution | v2.0.0 (2026-07-15, multi-language amendment 2026-07-16) |
| Governing ADRs | 0002, 0003, 0005, 0006, 0007, 0008, 0010, **0011** |
| Language | English (methodology artifact, ADR-0010). `docs/` stays Spanish |
| Test runner | `cd apps/api && uv run pytest` — strict TDD, zero-warning `filterwarnings` gate |
| Evidence base | Engram observation `#4790`, `sdd/lemmatization-pos/judgment-ledger` — frozen adversarial ledger, treated as established fact and not re-investigated |
| State to preserve | 503 backend / 67 frontend / 4 E2E green; 100% backend coverage; `domain`+`application` ≥90%, global ≥80%; linters clean; `api/schemas/import.v1.json` byte-identical at SHA-256 `def94cb6…554258`; `annotation.v1.json` byte-identical |

**What this change is.** Two Judgment Day rounds patched symptoms. Six findings (H1–H6) survived,
each with an existing reproduction. Every one of them is a **binding-granularity defect**: a rule was
stated at a coarser grain than the thing it was meant to constrain — an exemption bound to a
container instead of to a name, to a syntactic category instead of to an instance, a claim written by
hand instead of derived from its subject, an obligation enforced in code but not stated in the
contract, and a guarantee stated stronger than the check that backs it. This delta specifies the
**invariant each of those grains must satisfy**, not a patch per symptom.

**What this change is not.** It re-opens nothing recorded as closed. Out of scope, and MUST NOT be
addressed here: the parser exclusion (ADR-0011 records it as a knowingly deferred architecture
decision); f-string / `str.join` / `%`-format evasions of the isolation guard; `_path_segments`
nested-array handling; memory footprint; the one-`UPDATE`-per-occurrence design; registry
thread-safety; the `SPACE` POS tag; unit-test markers opening databases; and everything both judges
confirmed closed — SQLite chunking, model-path translation, the deletion cascade, score-normalization
checks, and the main same-text swap case.

---

## 2. Normative rules

Everything in this section is normative and binding on the requirements in §3. Each rule is cited by
identifier from the acceptance criteria that enforce it.

### 2.1 Binding granularity — an exemption binds to a name at a site, never to a container

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

### 2.2 Exemption scoping — an exemption names the instance that earned it

| # | Rule | Reason |
|---|------|--------|
| E1 | An exemption SHALL name the **instance** that produced the false positive, never the syntactic category that instance belongs to | `_DOCSTRING_OWNERS = (ast.Module,)` exempts every module docstring in the scan because one module's explanatory prose tripped the guard. One instance earned it; a category received it |
| E2 | Every exemption SHALL record, adjacent to itself, (a) the specific false positive that earned it, and (b) why the exempted region cannot carry a real violation — by exactly one of: **(b-i)** a downstream leg re-catches anything published from that region, or **(b-ii)** the exempted region is a single enumerated, reviewed instance | Without (b) an exemption is an assertion of safety with no stated mechanism. The two guards in question differ precisely here, and that difference must be written down rather than inferred — see §4 `CONTRA-3` |
| E3 | An exemption justified as "this region is prose" MUST NOT be granted to a region that is runtime-reachable, unless E2(b-i) applies. A module docstring is reachable as `__doc__` exactly as a function docstring is | This is the fix's own stated reason for revoking the function and class exemptions. Applying that reason to two of three cases and not the third is the defect. Reproduced: a module docstring holding `DELETE FROM manual_correction WHERE 1=1`, executed via `text(__doc__)`, yields zero violations |
| E4 | Where an exemption rests on E2(b-ii), the guard SHALL **pin the exempted instance's content**, so that replacing the reviewed prose with a real violation still fails | A named-instance exemption bounds *where* a violation can hide but not *what* can be put there. Pinning the content closes the remainder without widening the guard |

### 2.3 Evidence obligations for absence assertions

Every requirement in §3 that is enforced by an assertion of the form "there are zero matches" carries
all three of these. This repository's guards have twice passed while proving nothing.

| # | Rule |
|---|------|
| M1 | Each absence assertion SHALL be accompanied by a **mutation check**: a real violation of exactly the kind the assertion exists to catch, introduced and observed failing, with the **observed failure output recorded verbatim in the test docstring** |
| M2 | Each scan, walk, glob, or enumeration SHALL have a **non-vacuity test** that fails closed when the enumeration resolves to zero inputs or fails to reach a named expected input |
| M3 | Each exemption SHALL have a **boundary control test**: the same construct placed outside the exempt site still produces a violation, proving the miss the exemption creates is exactly the miss it was granted |

### 2.4 Prohibited remedies

| # | Rule |
|---|------|
| W1 | No requirement in §3 MAY be satisfied by **deleting a guard**, by **excluding a file or directory** from a walk, by **weakening a search pattern**, by **relaxing an AST criterion to a text search**, or by **narrowing the set of scanned inputs** |
| W2 | No requirement in §3 MAY be satisfied by **adding an entry to an allow-list** or by **widening an owning set** in place of tightening a binding |
| W3 | No requirement in §3 MAY be satisfied by **removing the subject of a claim** in place of correcting the claim. The single exception is `REQ-003H-003`, where deleting the **prose claim** is an explicitly permitted remedy — deleting the guard, the enumeration, or the pinned model is not |
| W4 | Every guard MUST still walk every input it walked before this change, and every leg MUST remain parse-based where it is parse-based today |

### 2.5 Claim provenance — assertions about a pinned model are generated, not written

| # | Rule | Reason |
|---|------|--------|
| K1 | A document assertion about the internals of the pinned model — rule counts, the contents of the `attribute_ruler` rule table, per-target fine-tag cardinality, the exactness of any `fine tag → UPOS` mapping, or any measured posterior — SHALL be produced by an **executable enumeration of that model**, or SHALL NOT appear in prose | Three consecutive rounds asserted a false fact in this same paragraph, each time by *reasoning* about the rule table instead of enumerating it. Round 2 was explicitly instructed to verify empirically and shipped a different false claim. The defect class is hand-written model-internal prose, not any individual sentence |
| K2 | The enumeration SHALL read the pinned model **at run time**. It MUST NOT restate a value transcribed from a previous run, and no expected value MAY be hardcoded except as a mutation fixture | A transcribed number is a hand-written claim with an extra step |
| K3 | The enumeration SHALL account for **this adapter's actual runtime pipe set**, and SHALL report reachable and structurally unreachable rules separately | `parser` is excluded (ADR-0011), so `DEP` is unset and `DEP`-conditioned rules can never fire. The AUX rule-count claim is wrong precisely because a `DEP`-conditioned catch-all rule mapping 46 of 50 fine labels was counted as if the table alone decided the answer, and one mapping's exactness comes from an exception that is unreachable for the same reason. Reachability is load-bearing, not a detail |
| K4 | The enumeration MAY require the model to be loaded and MAY therefore be gated `@pytest.mark.integration`. `domain` stays stdlib-only (SPEC-003 `REQ-003-002`). A gated test MUST still execute under the project's standard verification command, and MUST fail loudly rather than pass vacuously when the model is absent | Gating is a cost control, not an escape hatch |
| K5 | **This specification states no exact-mapping set, no rule count, and no posterior**, and no downstream artifact of this change may introduce one except as the enumeration's output. K1 binds this document too | Writing the fourth hand-written claim inside the requirement that forbids hand-written claims is the failure mode most available to this change. See §4 `CONTRA-4` |

### 2.6 Claim strength — a guarantee never exceeds the check that backs it

| # | Rule | Reason |
|---|------|--------|
| G1 | A stated guarantee SHALL NOT exceed what the check enforces. Where a check consumes a value **the checked party itself reports**, the guarantee is the reporter's **self-consistency with its input**, never the correctness of what it reported | `source_index` is self-reported by the analyzer. A swap of two same-text annotations with consistently reassigned indices passes. The shipped adapter derives `source_index` from the document's own enumeration and cannot exhibit this, which makes it a contract-strength question, not a live defect |
| G2 | A bounded guarantee SHALL be stated identically in **every** location that carries it — the port contract, the specification, and `docs/traceability-matrix.md` — within **one work unit**. No partial correction may stand | Precedent: SPEC-003 §5 `FACT-1`, corrected across six artifacts in one work unit specifically so no stale copy survived. The present cycle exists because a claim was written stronger than its enforcement; leaving one copy strong would repeat it |
| G3 | An accepted bound SHALL be **executable**: a test MUST exercise the case the guarantee does not cover and record its acceptance as specified behaviour | An accepted limitation recorded only in prose is indistinguishable from an unnoticed one. Making it a passing test with a stated reason gives a future change something to flip |

---

## 3. ADDED Requirements

### Requirement: REQ-003H-001 — Every guard exemption binds to a name at its owning site

Every exemption in every leg of the `AC-002-10` naming guard and of the annotation-contract guard
SHALL satisfy §2.1 B1–B6. The JSON Schema and served-OpenAPI legs MUST bind each exemption to a
**lemma-bearing property name within its declaring schema definition**, never to the definition as a
whole. Path decomposition MUST satisfy B4. The helper implementing this binding MUST exist once and
be shared by both guards (B5). Each leg's owning set MUST enumerate only the names that site
legitimately declares (B6).

This requirement is the invariant, stated once, that every leg must satisfy. It MUST NOT be
discharged by patching the JSON leg alone. `annotation.v1.json` and `import.v1.json` MUST remain
byte-identical: the defect is in the guard's binding, not in the schemas. §2.4 W1, W2 and W4 apply in
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
output of a real mutation (§2.3 M1–M3).

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

Every exemption in the annotation write-path isolation guard SHALL satisfy §2.2 E1–E4. The docstring
exemption MUST be scoped to the **specific module** whose explanatory prose produced the false
positive, identified by module path, and MUST NOT be expressed as a syntactic category such as "every
module docstring". Its justification MUST be recorded per E2, and because it rests on E2(b-ii) the
exempted docstring's content MUST be pinned per E4.

The function and class legs are already closed and MUST remain closed. §2.4 W1 and W4 apply: the
guard MUST continue to walk every module it walks today, and MUST remain AST-based.

Acceptance: **AC-003H-02** — Given a synthetic module whose **module docstring** is
`DELETE FROM manual_correction WHERE 1=1`, when the isolation guard runs over it, then it reports a
violation, and the test docstring records the observed failure output; and given the one production
module whose module docstring legitimately names the correction table in explanatory prose, when the
guard runs over the shipped tree, then there are zero violations; and given that same module with its
exempted docstring replaced by text that is not the reviewed prose, when the guard runs, then it
reports a violation (E4); and given the same SQL placed in a function docstring, in a class
docstring, and as an ordinary string literal, when the guard runs, then each reports a violation
(§2.3 M3); and given the guard's module walk, when it resolves to zero modules or fails to reach
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

`openspec/changes/lemmatization-pos/design.md` §P1 and `docs/traceability-matrix.md` SHALL NOT contain
a hand-written assertion about the pinned `en_core_web_sm` model's internals, as defined by §2.5 K1.
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
Rewording is the remedy that has already failed three times. §2.5 K5 binds this change's own
artifacts: no requirement, task, design note, or commit message produced here may state which
mappings are exact.

Acceptance: **AC-003H-03** — Given the pinned model loaded at run time, when the enumeration runs,
then it emits the rule count, the per-target fine-tag sets, the reachable/unreachable partition under
`_EXCLUDED_PIPES`, and the computed exact-mapping set, and the test asserts the documented claim
against that output rather than against a transcribed constant; and given `design.md` §P1 and
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

- GIVEN `design.md` §P1 and `docs/traceability-matrix.md`
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
that it is content equality, which is exactly why `source_index` was added. Per §2.6 G1 the wording
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

The guarantee the pairing check provides SHALL be stated per §2.6 G1–G3, and the mechanism MUST NOT
be strengthened in this change (§4 `DEC-2`).

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

## 4. Ambiguities, contradictions and decisions recorded and resolved (AGENTS.md §9)

None was resolved silently.

| ID | Ambiguity, contradiction or open decision | Resolution | Status |
|----|-------------------------------------------|------------|--------|
| **DEC-1** | **Pre-archive delta-spec target.** Before archive, `003-lemmatization-pos` had no baseline spec: it existed only in the not-yet-archived `lemmatization-pos` change, so "amend the baseline" was not available and "amend the other change's files directly" would have erased this change's own audit trail. | The change carried its own delta specs under `openspec/changes/spec-003-harden-guards-and-claims/specs/`, which amended the in-flight `openspec/changes/lemmatization-pos/specs/` documents. Archive promoted the reconciled hardening requirements into `openspec/specs/003-lemmatization-pos/spec.md` and preserved the original delta under `openspec/changes/archive/2026-08-26-spec-003-harden-guards-and-claims/`. Settled by the orchestrator. | **Closed. Do not re-open** |
| **DEC-2** | **H6 direction.** Strengthen the `source_index` mechanism, or state the real bounded guarantee accurately. | **State the bounded guarantee** (`REQ-003H-006`). Strengthening requires a source of truth independent of the analyzer, which is over-engineering for a case the shipped adapter cannot exhibit. **This whole cycle exists because claims were written stronger than what is enforced; the fix must not repeat that pattern.** Settled by the orchestrator. | **Closed. Do not re-open** |
| **DEC-3** | Whether these findings modify existing `003-lemmatization-pos` requirements. `REQ-003-004` and `REQ-003-011` are the requirements whose guards have holes. | **`ADDED` only.** Neither requirement is wrong — each is silent where this change adds an obligation. Under the delta convention a `MODIFIED` block replaces the whole requirement at archive time, so re-stating a correct requirement in order to append to it risks losing scenarios for no gain. The one genuine `MODIFIED` is `REQ-002-007`, in the companion delta, because its acceptance criterion is currently satisfiable by a guard that has the hole. | Accepted |
| **REC-1** | **H3 has been wrong three times running**, in the same paragraph. Round 1 wrote a false claim. Round 2, explicitly instructed to verify empirically, wrote a *different* false claim and shipped a statement that contradicts itself two paragraphs later. Round 3 would be a fourth attempt at the same method. | The requirement is **structural, not editorial** (`REQ-003H-003`, §2.5). "Write the paragraph correctly" is forbidden as a remedy: it is what failed twice. The claim must be produced by an executable enumeration bound to the pinned model, or must not exist. Hand-written model-internal prose is treated as the **defect class**, not the sentence as the defect. | **Closed as specified. The remedy is generation, never rewording** |
| **CONTRA-3** | **Two guards define a docstring exemption and only one of them may keep a syntactic one.** `AC-002-10`'s Python leg exempts module, class and function docstrings; the write-path isolation guard was narrowed to module docstrings only and is still exploitable. Applying one rule to both would either re-break `AC-002-10` (whose own rationale requires prose to be able to name the concept it forbids) or leave the isolation guard open. | **Not a contradiction — the two differ under §2.2 E2.** `AC-002-10`'s exemption is justified by **E2(b-i)**: anything a docstring publishes is re-caught by the served-OpenAPI leg, which is exactly where a docstring stops being prose and becomes contract. The isolation guard has **no** re-catch leg, so its exemption can only be justified by **E2(b-ii)**, which requires a named instance and, per E4, pinned content. The rule is one rule; the two guards satisfy different clauses of it, and that MUST now be written down in each guard rather than inferred. | **Closed. `AC-002-10`'s docstring exemption is retained and its E2(b-i) justification made explicit; the isolation guard's is rescoped under E2(b-ii)+E4** |
| **AMB-10** | **`REQ-003H-002`'s residual.** Scoping the exemption to one named module still leaves that module's `__doc__` runtime-reachable. Narrowing alone does not close the hole; it only bounds where it can hide. | Closed by **E4**: the guard pins the exempted docstring's content, so replacing reviewed prose with a real violation fails. Bounding *where* plus pinning *what* is complete without widening the guard or removing a legitimate exemption. | Accepted |
| **CONTRA-4** | **This specification is itself at risk of becoming the fourth false model-internal claim.** The most natural way to specify `REQ-003H-003` is to state the correct exact-mapping set — which would be a hand-written assertion inside the requirement forbidding hand-written assertions. | **K5.** This document states no exact-mapping set, no rule count and no posterior, and forbids any downstream artifact of this change from introducing one except as the enumeration's output. The acceptance criterion asserts the *shape and provenance* of the enumeration's output, never its values. | **Closed. K1 binds this document** |
| **AMB-11** | K4 gates the enumeration as an integration test, which risks the claim being verified only in environments that have the model — while the documents it governs ship everywhere. | Accepted, with the consequence stated: the enumeration MUST fail loudly or skip explicitly when the model is absent, never pass vacuously, and it MUST run under the project's standard verification command. The prose-side check (zero un-cited model-internal claims in the two documents) is a **plain document scan** with no model dependency, so the falsifiable half of `REQ-003H-003` runs unconditionally. | **Accepted tradeoff, recorded** |
| **AMB-12** | H1 spans two capabilities: the naming guard belongs to `002-text-import`'s `AC-002-10`, the annotation-contract guard and `annotation.v1.json` to `003-lemmatization-pos`. Splitting the invariant across two deltas would let the two halves drift — the exact failure H1 is. | The invariant is defined **once**, here, as §2.1. The companion `002-text-import` delta amends `AC-002-10` to require it by reference rather than restating it. Precedent: the in-flight 002 delta already cites `003-lemmatization-pos` §5 `CONTRA-1` and `REQ-003-023`. | Accepted |

---

## 5. Verification hooks

| Hook | Check | Verifies |
|------|-------|----------|
| HG1 | Renaming each of the six non-lemma properties of `$defs.occurrence` to `lemma` produces a violation in both guards; the four genuine lemma properties still pass; a key named `occurrence.extra` is caught; the frontend owning sets grant only declared names; exactly one binding helper exists and both guards import it; the schema glob fails closed | AC-003H-01 |
| HG2 | A synthetic module docstring holding `DELETE FROM manual_correction WHERE 1=1` produces a violation; the one reviewed production docstring passes; replacing its pinned content produces a violation; function docstring, class docstring and plain literal each still produce a violation; the module walk fails closed | AC-003H-02 |
| HG3 | The enumeration reads the pinned model at run time and emits rule count, per-target fine-tag sets, the reachable/unreachable partition under `_EXCLUDED_PIPES`, and the computed exact set; `design.md` §P1 and the matrix carry zero un-cited model-internal claims and no self-contradiction; a mutated expected value fails; a missing model skips or fails, never passes; `domain/` remains stdlib-only | AC-003H-03 |
| HG4 | `ports.py` documents `source_index == i` and names `ANNOTATION_FAILED` while retaining the `raw_text` obligation; every rejection branch maps to a documented obligation; a fully conformant double is accepted; deleting the obligation sentence fails the guarding test; `docs/` names `source_index` | AC-003H-04 |
| HG5 | The `REQ-003-004` row names both checks, cites the swap regression test and the property test's current form; zero matches for a claim of identity-based pairing; every test name the matrix cites resolves against the suite; rows exist for `REQ-003H-001` … `REQ-003H-006` | AC-003H-05 |
| HG6 | Port contract, spec and matrix state the same bounded guarantee; a consistently-reindexed same-text swap is accepted and recorded as the documented bound; an inconsistently-reindexed swap fails `ANNOTATION_FAILED` and writes nothing; the adapter's `source_index` is the document's own enumeration index | AC-003H-06 |
| HG7 | Every absence assertion introduced or amended here carries a mutation check with observed output in its docstring (M1), a non-vacuity test (M2), and a boundary control (M3) | §2.3 compliance |
| HG8 | No guard deleted, no file or directory excluded, no pattern weakened, no AST criterion reverted to a text search, no allow-list entry added, no owning set widened; every guard walks every input it walked before | §2.4 compliance |
| HG9 | 503 backend / 67 frontend / 4 E2E green; 100% backend coverage held; `domain`+`application` ≥90%, global ≥80%; linters and type checks clean; `import.v1.json` SHA-256 `def94cb6…554258` and `annotation.v1.json` byte-identical | State preserved |

---

## 6. Explicit non-additions

This delta does NOT specify, and MUST NOT be used to justify: re-applying the parser exclusion or
re-opening ADR-0011; f-string, `str.join` or `%`-format evasions of the isolation guard; nested-array
handling in JSON path decomposition; memory footprint; the one-`UPDATE`-per-occurrence write design;
registry thread-safety; the `SPACE` POS tag; unit-test markers that open databases; or anything both
judges confirmed closed — SQLite chunking, model-path translation, the deletion cascade,
score-normalization checks, and the main same-text swap case.

It also does NOT permit: strengthening the `source_index` mechanism (DEC-2); changing the port's
signature, the persisted schema, the error contract, or any runtime behaviour; modifying
`import.v1.json` or `annotation.v1.json`; or satisfying any requirement by any remedy §2.4 forbids.

It does NOT choose module names, file layouts, helper placement, task ordering, or slice boundaries —
`sdd-design` and `sdd-tasks` own those.

---

## 7. Traceability

`docs/traceability-matrix.md` MUST gain one row per requirement `REQ-003H-001` … `REQ-003H-006`, each
carrying its `AC-003H-##` reference, its test file(s), its task ID(s) and its status, and MUST have
its `REQ-003-004` row corrected per `REQ-003H-005`, before this change can be considered done
(Art. I.5, Art. XI, `AGENTS.md` §10). `REQ-003H-005` is the requirement that makes this section
enforceable rather than aspirational: every test name the matrix cites must resolve against the suite.

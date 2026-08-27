# Delta for 002-text-import

Change: `spec-003-harden-guards-and-claims`.

**Scope of this delta: exactly one requirement.** `REQ-002-007` is modified again so that
`AC-002-10`'s allow-list mechanism is bound at a granularity that cannot be bypassed. Nothing else in
`002-text-import` changes.

**This delta stacks on the in-flight `lemmatization-pos` delta**, not on the archived baseline.
`openspec/changes/archive/2026-08-26-lemmatization-pos/specs/002-text-import/spec.md` already carries a `MODIFIED`
`REQ-002-007` that narrowed the guard to an enumerated allow-list. The block below is that block,
carried forward **in full** and then amended — so that when both changes reconcile into
`openspec/specs/002-text-import/spec.md` at archive time, the surviving requirement is complete rather
than a fragment. See `../003-lemmatization-pos/spec.md` §4 `DEC-1` and `AMB-12`.

**Why `REQ-002-007` must change again.** The narrowing shipped correctly on the Python and
reflected-column legs, which bind `symbol → module` and `column → table`. The JSON Schema and served
OpenAPI legs bind `path → schema component` instead — a **container** that also holds the very names
the guard exists to catch. `$defs.occurrence` in `annotation.v1.json` holds `position`, `raw_text`,
`pos`, `pos_origin`, `automatic_pos` and `pos_confidence` alongside the four lemma-bearing properties,
so renaming any one of the six to the bare name `lemma` currently yields **zero violations** — the
exact mutation `docs/traceability-matrix.md` cites as proof that this defect was closed. Path
decomposition compounds it: a rendered path re-split on every `.` lets a key literally named
`occurrence.extra` inherit the owning segment's exemption. The helper is duplicated across two guards,
so a fix to one leaves the other exploitable. The requirement's *text* never stated the binding
invariant, so the current implementation satisfies `AC-002-10` as written while leaving the hole open.
That is a specification gap, not only an implementation bug, and it is fixed here.

The invariant itself is defined **once**, in `../003-lemmatization-pos/spec.md` §2.1 (`B1`–`B6`), and
required here by reference. Restating it in two places is precisely the drift failure `B5` exists to
prevent.

## MODIFIED Requirements

### Requirement: REQ-002-007 — Neither the grouping key nor the display form is labelled "lemma" or "lexeme"

No API path, request field, response key, error code, database column, identifier, or user-visible
string introduced by this capability SHALL contain `lemma`, `lemas`, `lexeme`, or `lexema`. The
grouping key MUST be named `normalized_form` and the display form MUST be named `display_form`.
Neither name nor any label attached to either MAY describe the value as a lemma or a lexeme — a
display form is the most frequent *textual form* in the group, not a canonical dictionary headword.
The UI MUST state that it lists normalized forms and MUST NOT claim that inflected forms are merged
(Art. V.1).

(Previously: the allow-list was required to be an explicit enumeration of exact names, but the
requirement never stated what each entry must be *bound to*; the JSON Schema and OpenAPI legs bound
their exemption to a whole schema component, so renaming a non-lemma sibling property to an
allow-listed name produced zero violations. The allow-list is unchanged; every exemption is now bound
to a name at its owning site.)

The prohibition binds **naming and contract surface, not explanatory prose**. Module, class, and
function docstrings and `#` comments MAY name the forbidden concepts, because the clearest way to
record that a value is not a lemma is to write the word "lemma". One exception, and it is a
narrowing rather than a loophole: a docstring that a framework publishes is contract surface, not
prose. A Pydantic model docstring is serialised by FastAPI into `components.schemas.*.description`
in the served `/openapi.json` and rendered in the API browser, so it remains fully bound by the
prohibition above.

**Capability scope of the guard (added by change `lemmatization-pos`).** This requirement governs
values introduced by capability `002-text-import`. It has never governed another capability's
vocabulary, and it MUST NOT be read as forbidding the word `lemma` for a value that genuinely *is* a
lemma. Capability `003-lemmatization-pos` introduces a real lemma, produced by a real lemmatizer,
stored per occurrence alongside — never instead of — `normalized_form` and `display_form`. Naming
that value `lemma` is the honest name and is exactly what this requirement protects: it keeps the two
concepts distinguishable rather than collapsing them.

The guard is therefore narrowed by an **explicit, enumerated allow-list of exact symbol and property
names**, each of which MUST denote a genuine lemma owned by another capability's specification. The
narrowing MUST NOT be implemented by deleting the guard, by excluding a file or directory from the
walk, by weakening the search pattern, or by relaxing the AST criterion to a text search — the
rationale below forbids the last of those explicitly, and the first three would forfeit the guard
entirely. Every symbol outside the allow-list MUST still produce zero matches, and
`normalized_form`/`display_form` MUST NOT be renamed, aliased to a lemma-shaped name, or described as
a lemma in any prose, contract surface, or UI string.

**Binding granularity (added by change `spec-003-harden-guards-and-claims`).** An enumeration of
exact names is only as strong as what each entry is bound to. Every exemption in every leg of this
guard SHALL satisfy `../003-lemmatization-pos/spec.md` §2.1 `B1`–`B6`: an exemption is the pair
`(exact name, owning site)`, neither half exempting anything alone; the owning site is the **narrowest
structural unit that leg's own parse exposes** which can contain exactly the exempt names and nothing
else; binding to a container that also holds non-exempt names is FORBIDDEN; a structural path is
decomposed by the traversal that produced it, never by re-splitting a rendered path string on a
delimiter that MAY occur inside a name; the implementation of that binding exists **once** and is
shared by every guard that needs it; and a per-site owning set enumerates only the names that site
legitimately declares, never the whole allow-list by default.

Concretely, for the two legs that currently deviate: the JSON Schema and served-OpenAPI legs MUST bind
each exemption to a **lemma-bearing property name within its declaring schema definition or component**
— never to the definition or component as a whole. This narrows the guard further; it MUST NOT be
implemented by widening the allow-list, by adding an owning site, or by any remedy
`../003-lemmatization-pos/spec.md` §2.4 forbids.

**Exemption scoping.** This guard's docstring exemption is retained, and its justification is now
stated explicitly rather than left implicit: it satisfies
`../003-lemmatization-pos/spec.md` §2.2 `E2(b-i)` — anything a docstring publishes is re-caught by the
served-OpenAPI leg, which is exactly the point at which a docstring stops being prose and becomes
contract. A guard with no such re-catch leg MUST NOT copy this exemption; it may only exempt a named,
reviewed instance with pinned content under `E2(b-ii)` and `E4`. See
`../003-lemmatization-pos/spec.md` §4 `CONTRA-3`.

Acceptance: **AC-002-10** — Given the shipped backend and frontend sources, the versioned JSON
Schemas, and the served OpenAPI document, when each is inspected structurally for
`lemma|lemas|lexeme|lexema` (case-insensitive), then every match is a member of the explicitly
enumerated allow-list of another capability's genuine-lemma symbols **and is bound to the site that
owns it**, and the match count outside that allow-list is zero in each of:

- **Python sources** (`apps/api/src/wheel_vocabulary/`), parsed into an AST with the standard
  library `ast` module: every identifier — variable, parameter, function, method, class, attribute,
  import alias, and dataclass or model field name — and every string literal that is **not** a
  docstring. The exemption is defined as the first statement of a module, class, or function body,
  never as "any string constant": exempting string constants at large would remove response keys,
  JSON Schema property names, and user-facing messages from the guard, which is the majority of what
  it exists to catch. `#` comments are outside the AST and therefore outside the guard by
  construction. Each allow-listed name is exempt only in the module that owns it.
- **TypeScript sources** (`apps/web/src/**/*.{ts,tsx}`), parsed into an AST with the TypeScript
  compiler API (`ts.createSourceFile`, already available through the `typescript` dependency that
  backs `tsc --noEmit`, so this leg adds no package): every identifier, every string literal, every
  template-literal token, and every JSX text node. TypeScript has no docstring construct, so this
  leg defines no docstring exemption — the equivalent carve-out is unnecessary because `//` and
  `/* */` comments never enter the tree `ts.createSourceFile` produces, exactly as `#` comments never
  enter the Python one. This directory is TypeScript, not Python; the two legs are stated separately
  because they are parsed by different tools, not because they enforce different rules. Each owning
  file's exempt set enumerates only the names that file declares (`B6`).
- **The persisted column names** reflected from `Base.metadata`, which catches a rename regardless of
  how the source spells it. Each allow-listed column name is exempt only on the table that owns it.
- **The versioned JSON Schemas** (`api/schemas/*.json`), parsed as JSON: every object key and
  every string value. JSON has no docstring, so nothing in it is exempt. Each allow-listed property
  name is exempt only **as that property of the definition that declares it**; renaming any sibling
  property of that same definition to an allow-listed name MUST produce a violation, and a key whose
  own name contains a `.` MUST NOT inherit an ancestor segment's exemption.
- **The served OpenAPI document**: every string. This leg is what keeps the docstring exemption
  scoped — it catches a docstring at exactly the point where it stops being prose and becomes
  published contract. Its exemptions bind to property names within the declaring schema component,
  on the same terms as the JSON Schema leg.

and when the read response for this capability is inspected, then the per-row grouping key is
`normalized_form` and the per-row display value is `display_form`; and when the allow-list itself is
inspected, then it is a finite explicit enumeration of exact names, not a path exclusion, a directory
exclusion, or a pattern relaxation; and when the binding implementation is located, then exactly one
implementation exists and every guard that needs it imports that one; and when each absence assertion
in this guard is inspected, then it carries a mutation check whose observed failure output is recorded
in its docstring, a non-vacuity test that fails closed on an empty walk, and a boundary control test
(`../003-lemmatization-pos/spec.md` §2.3 `M1`–`M3`).

**Rationale — this MUST NOT be reverted to a text search.** `AC-002-10` originally mandated a
literal case-insensitive grep over the source tree. That guard forbade the word inside the very
sentence explaining why the word is forbidden, and it caused a concrete regression: cut `1a` shipped
`domain/models.py:36` reading "neither is a lemma or a lexeme (`REQ-002-007`)" — accurate, useful
documentation — and cut `1b` had to reword it to "canonical dictionary headword" solely to get the
suite green, making the docstring less clear in order to satisfy a check that was never aimed at
docstrings. This project had already resolved the identical dilemma in the opposite direction: the
domain isolation guard for `AC-002-06` (hook H2, `tests/unit/test_domain_isolation.py`) is AST-based
precisely because domain docstrings legitimately contain "FastAPI", "SQLAlchemy", and "Pydantic"
while explaining that those imports are prohibited. A text search would false-positive on the
comment documenting the rule. The two guards are hereby unified on the AST criterion. A text search
is the weaker instrument, not the stronger one: it cannot tell a field name from a comment, so it
fires on prose it should ignore while catching nothing that a structural walk misses.

**Rationale — the allow-list MUST stay an enumeration, not an exclusion.** The same reasoning applies
one level up. Excluding `infrastructure/persistence/models.py` from the walk to admit
`Occurrence.lemma` would also admit a future rename of `normalized_text` to `lemma_text` in that same
file — silently, and in exactly the module where it would do the most damage. An enumeration of exact
names admits precisely the symbols that were reviewed and nothing else, so the guard keeps catching
the regression it was written to catch while permitting the value it was never aimed at.

**Rationale — an enumeration bound to a container is an exclusion in disguise.** The same reasoning
applies one level further. Binding the exemption to `$defs.occurrence` rather than to the property
names inside it admits every property that definition happens to hold — which is a file exclusion
scoped to a schema definition, arrived at by a different route and with the same effect. The
enumeration stayed exact; only the binding was coarse, and the binding is where the strength lives. A
guard whose own cited proof-of-closure mutation passes silently is not a guard.

#### Scenario: No lemma naming leaks into the contract

- GIVEN the backend sources, frontend sources, reflected column names, JSON Schemas, and served
  OpenAPI document
- WHEN each is inspected structurally for `lemma|lemas|lexeme|lexema` — identifiers and
  non-docstring literals for Python, identifiers and non-comment literals (including template
  literals and JSX text) for TypeScript, keys and values for JSON and OpenAPI
- THEN every match is a member of the enumerated allow-list
- AND every match is bound to the site that owns it
- AND there are zero matches outside it

#### Scenario: Prose may name the concept it rules out, naming may not

- GIVEN a class docstring reading "neither is a lemma or a lexeme (`REQ-002-007`)"
- WHEN the guard runs over it
- THEN the docstring passes
- AND a field in the same module renamed to `lemma_form` still fails
- AND a response-key literal changed to `"lemma_form"` still fails
- GIVEN a TypeScript source containing the code comment
  `// a form is not a lemma and not a lexeme`
- WHEN the guard runs over it
- THEN the comment passes
- AND an identifier such as `lemmaCount` in the same source still fails
- AND a string literal such as `"lemma_form"` in the same source still fails

#### Scenario: Inflected forms stay separate and are labelled honestly

- GIVEN a synthetic text containing `corro`, `corres`, and `corría`
- WHEN the client reads the import
- THEN three distinct rows are returned
- AND the UI describes them as normalized forms

#### Scenario: A genuine lemma from another capability is admitted by name

- GIVEN the allow-list enumerating the genuine-lemma symbols of `003-lemmatization-pos`
- WHEN the guard runs over the shipped sources
- THEN those exact symbols pass
- AND every other occurrence of the pattern still fails

#### Scenario: Renaming a normalized form to a lemma-shaped name still fails

- GIVEN `normalized_form` renamed to any name matching `lemma|lemas|lexeme|lexema`
- WHEN the guard runs
- THEN it fails
- AND the allow-list does not admit it, because the allow-list enumerates exact names

#### Scenario: An allow-listed name at a non-owning site still fails

- GIVEN an allow-listed name such as `lemma` introduced in a module, on a table, in a schema
  definition, or in a frontend file that does not own it
- WHEN the guard runs
- THEN it fails
- AND the exemption does not apply, because an exemption is a name **and** its owning site

#### Scenario: Renaming a sibling property inside an owning definition still fails

- GIVEN `$defs.occurrence.properties.raw_text` in `annotation.v1.json` renamed to the bare
  allow-listed name `lemma`
- WHEN the guard runs
- THEN it fails
- AND the same holds for `position`, `pos`, `pos_origin`, `automatic_pos` and `pos_confidence`
- AND the four genuinely lemma-bearing properties of that same definition still pass

#### Scenario: A key whose own name contains a dot inherits nothing

- GIVEN a JSON document containing an object key literally named `occurrence.extra` whose value is an
  allow-listed name
- WHEN the guard decomposes that path
- THEN the key is not treated as passing through an owning segment
- AND it fails

#### Scenario: One binding implementation, shared

- GIVEN every guard that applies this allow-list
- WHEN the binding and path-decomposition implementation is located
- THEN exactly one implementation exists
- AND every such guard imports that one

#### Scenario: The guard was narrowed, not weakened

- GIVEN the guard's implementation after this change
- WHEN it is inspected
- THEN it is still AST-based and still walks every file it walked before
- AND the allow-list is a finite explicit enumeration of exact names, not a path exclusion, a
  directory exclusion, or a pattern relaxation
- AND no allow-list entry was added and no owning set was widened to satisfy this change

#### Scenario: The guard's own assertions are not vacuous

- GIVEN each absence assertion in this guard
- WHEN its test is inspected
- THEN its docstring records the observed failure output of a real mutation
- AND a non-vacuity test fails closed when the walk resolves to nothing
- AND a boundary control test proves the exemption misses only what it was granted

# Delta for 002-text-import

Change: `lemmatization-pos` (SPEC-003, capability `003-lemmatization-pos`).

**Scope of this delta: exactly one requirement.** `REQ-002-007` is modified so its acceptance
criterion can coexist with a genuine lemma introduced by a different capability. Nothing else in
`002-text-import` changes.

**`REQ-002-010` is deliberately NOT modified.** SPEC-003 makes annotation a step separate from
import (`003-lemmatization-pos` §2.6), so the import path still writes `pos = None` on every row and
`REQ-002-010` — scoped to "every row written by this capability" — stays literally true. See
`003-lemmatization-pos` §5 `CONTRA-2`.

**Why `REQ-002-007` must change anyway.** Its normative text is already capability-scoped ("No API
path, request field, response key, error code, database column, identifier, or user-visible string
introduced by *this capability*"), and that text is preserved verbatim below. Its acceptance
criterion is not: `AC-002-10` and its shipped guard walk whole directories, `Base.metadata` column
names, the pinned JSON Schema and the served OpenAPI document, asserting **zero** matches for
`lemma|lemas|lexeme|lexema`. Capability `003-lemmatization-pos` adds `Occurrence.lemma`, a domain
value object field, a DTO field and a TypeScript type inside that walk, so the existing suite fails.
The mechanism is therefore narrowed to an explicit allow-list; the protected intent is untouched.
See `003-lemmatization-pos` §5 `CONTRA-1` and `REQ-003-023`.

## MODIFIED Requirements

### Requirement: REQ-002-007 — Neither the grouping key nor the display form is labelled "lemma" or "lexeme"

No API path, request field, response key, error code, database column, identifier, or user-visible
string introduced by this capability SHALL contain `lemma`, `lemas`, `lexeme`, or `lexema`. The
grouping key MUST be named `normalized_form` and the display form MUST be named `display_form`.
Neither name nor any label attached to either MAY describe the value as a lemma or a lexeme — a
display form is the most frequent *textual form* in the group, not a canonical dictionary headword.
The UI MUST state that it lists normalized forms and MUST NOT claim that inflected forms are merged
(Art. V.1).

(Previously: the acceptance criterion required zero matches across the whole source tree, which no
longer holds once a different capability introduces a genuine lemma; the guard is now narrowed to an
enumerated allow-list instead of being deleted or weakened.)

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

Acceptance: **AC-002-10** — Given the shipped backend and frontend sources, the versioned JSON
Schemas, and the served OpenAPI document, when each is inspected structurally for
`lemma|lemas|lexeme|lexema` (case-insensitive), then every match is a member of the explicitly
enumerated allow-list of another capability's genuine-lemma symbols, and the match count outside that
allow-list is zero in each of:

- **Python sources** (`apps/api/src/wheel_vocabulary/`), parsed into an AST with the standard
  library `ast` module: every identifier — variable, parameter, function, method, class, attribute,
  import alias, and dataclass or model field name — and every string literal that is **not** a
  docstring. The exemption is defined as the first statement of a module, class, or function body,
  never as "any string constant": exempting string constants at large would remove response keys,
  JSON Schema property names, and user-facing messages from the guard, which is the majority of what
  it exists to catch. `#` comments are outside the AST and therefore outside the guard by
  construction.
- **TypeScript sources** (`apps/web/src/**/*.{ts,tsx}`), parsed into an AST with the TypeScript
  compiler API (`ts.createSourceFile`, already available through the `typescript` dependency that
  backs `tsc --noEmit`, so this leg adds no package): every identifier, every string literal, every
  template-literal token, and every JSX text node. TypeScript has no docstring construct, so this
  leg defines no docstring exemption — the equivalent carve-out is unnecessary because `//` and
  `/* */` comments never enter the tree `ts.createSourceFile` produces, exactly as `#` comments never
  enter the Python one. This directory is TypeScript, not Python; the two legs are stated separately
  because they are parsed by different tools, not because they enforce different rules.
- **The persisted column names** reflected from `Base.metadata`, which catches a rename regardless of
  how the source spells it.
- **The versioned JSON Schemas** (`api/schemas/*.json`), parsed as JSON: every object key and
  every string value. JSON has no docstring, so nothing in it is exempt.
- **The served OpenAPI document**: every string. This leg is what keeps the docstring exemption
  scoped — it catches a docstring at exactly the point where it stops being prose and becomes
  published contract.

and when the read response for this capability is inspected, then the per-row grouping key is
`normalized_form` and the per-row display value is `display_form`; and when the allow-list itself is
inspected, then it is a finite explicit enumeration of exact names, not a path exclusion, a directory
exclusion, or a pattern relaxation.

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

#### Scenario: No lemma naming leaks into the contract

- GIVEN the backend sources, frontend sources, reflected column names, JSON Schemas, and served
  OpenAPI document
- WHEN each is inspected structurally for `lemma|lemas|lexeme|lexema` — identifiers and
  non-docstring literals for Python, identifiers and non-comment literals (including template
  literals and JSX text) for TypeScript, keys and values for JSON and OpenAPI
- THEN every match is a member of the enumerated allow-list
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

#### Scenario: The guard was narrowed, not weakened

- GIVEN the guard's implementation after this change
- WHEN it is inspected
- THEN it is still AST-based and still walks every file it walked before
- AND the allow-list is a finite explicit enumeration of exact names, not a path exclusion, a
  directory exclusion, or a pattern relaxation

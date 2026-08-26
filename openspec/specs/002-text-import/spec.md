# Capability 002-text-import

This is the source-of-truth specification for capability `002-text-import`. It records the
observable and verifiable behavior for importing a `.txt` file and viewing word frequencies,
together with the frontend presentation of the normalized and display forms.

It carries two requirement families, both binding:

- `REQ-002-001` … `REQ-002-018` — the text-import capability (upload, tokenization, normalization,
  aggregation, persistence, deletion), merged from the archived `text-import` change.
- `REQ-UI-DISPLAY-NORMALIZED-001` … `-005` — the frequency-form presentation behavior, merged from
  the archived `ui-display-normalized-explanation` change. See the final section of this document.

Section numbers `§2`, `§2.4`, `§2.5`, `§4`, and `§5` referenced inside the requirements below refer
to the sections of this document.

## 1. Metadata

| Field | Value |
|-------|-------|
| Capability | `002-text-import` |
| Requirement prefixes | `REQ-002-###`, `REQ-UI-DISPLAY-NORMALIZED-###` |
| Acceptance prefix | `AC-002-##` |
| Governing constitution | v2.0.0 (2026-07-15, multi-language amendment 2026-07-16) |
| Language | English (methodology artifact, ADR-0010). Product docs stay Spanish. |
| Test runner | `cd apps/api && uv run pytest` — strict TDD, zero-warning `filterwarnings` gate |

### 1.1 Glossary alignment (ADR-0010: `docs/glossary.md` is Spanish)

This spec uses English terms for the canonical Spanish glossary entries, cited once here and not
renamed thereafter: **forma normalizada** = *normalized form*; **forma textual** = *textual form*;
**aparición** = *occurrence*; **token** = *token*; **lema** = *lemma*; **corpus** = *corpus*.
Per `REQ-002-007` and Art. V.1, this capability groups by *normalized form*; **lemma** and **lexeme**
name a different concept and MUST NOT appear in any API field, response key, or UI string.

---

## 2. Normalization and tokenization contract (normative)

`REQ-002-005` depends on rules the proposal left abstract. They are pinned here because they change
what the user sees, and Art. I.4 forbids resolving ambiguity in code instead of the specification.
All rules are stdlib-only (`unicodedata`, `re`, `hashlib`), language-generic, and force neither
OQ-2 (language detection) nor OQ-4 (per-language NLP library).

### 2.1 Character classes

Classes are defined by **Unicode general category**, not by an ASCII-shaped regex, so no rule
encodes an English-only assumption (the `REQ-PFB-LANG-01` precedent).

| Class | Definition |
|-------|------------|
| Word character | General category `L*` (letter), `M*` (mark), or `Nd` (decimal digit) |
| Joiner | Apostrophes `U+0027 ' U+2019 ' U+02BC ʼ U+2018 '`; hyphens `U+002D -`, `U+2010 ‐` |
| Separator | Every other character, including all whitespace, `_`, and every dash that is not a joiner |

Marks (`M*`) are word characters on purpose: Devanagari, Thai, Hebrew, and Arabic vowel signs have
no precomposed forms, and excluding them would silently truncate those scripts (ADR-0008).

### 2.2 Tokenization rules

| # | Rule | Example | Reason |
|---|------|---------|--------|
| T1 | `U+00AD SOFT HYPHEN` is transparent to token-boundary detection. It MUST NOT be removed from the document before tokenization; emitted `raw_text` and `display_form` retain it, while normalization/grouping keys remove it. | `inter⟨SHY⟩national` → one raw/display token retaining SHY; grouping key `international` | It is invisible formatting for grouping, but preserving source slices keeps display forms verbatim for `AC-002-24`. |
| T2 | A token is a maximal run of word characters, optionally joined by **single internal** joiners between word characters | `state-of-the-art` → one token | Hyphenated compounds are one lexical unit; splitting invents four words the author did not write |
| T3 | An apostrophe between word characters is internal, so the token is not split | `don't`, `l'homme`, `O'Neill` → one token each | Splitting yields the noise token `t`. Where the split is real (French `l'`) it is language-specific and needs the deferred NLP adapter (OQ-4) — a **documented limitation**, not a silent guess |
| T4 | A joiner that is not between two word characters is a separator | `inter-⏎national` → `inter`, `national`; `-dash-` → `dash` | Prevents dangling punctuation entering a token |
| T5 | `U+2013 –`, `U+2014 —`, `U+2212 −` are separators, never joiners | `word—word` → two tokens | En/em dashes punctuate clauses; only hyphens join words |
| T6 | A token MUST contain at least one `L*` character, otherwise it is discarded | `2026` and `1914–1918` are discarded; `covid19`, `3rd` are kept | Bare numerals are not vocabulary; keeping them floods the table with years, chapter numbers, and page artifacts |
| T7 | `_` is a separator | `snake_case` → `snake`, `case` | Not a letter and not an orthographic joiner |
| T8 | All Unicode whitespace separates equally, including `\n`, `\r\n`, `\t`, `U+00A0`, `U+200B`, `U+2028/9` | `line1\r\nline2` ≡ `line1\nline2` | Windows-authored `.txt` must give byte-identical results |
| T9 | Hyphenation across a line break is **not** rejoined | `well-⏎known` → `well`, `known` | Distinguishing a soft line-break hyphen from a real compound hyphen is a dictionary question (OQ-4). A naive rejoin corrupts genuine compounds. **Documented limitation.** |
| T10 | `Occurrence.position` is the zero-based **token index** in the emitted token sequence, not a byte or character offset | third token → `position = 2` | Character offsets are ambiguous under normalization forms; a token index is stable, testable, and sufficient (see §5, AMB-1) |

Consequence of T2/T3: multiword expressions are not detected. `give up` is two normalized forms.
This is the limitation the proposal already declared, restated here so it is visible at spec level
(Art. V.6 / ADR-0009 remain unimplemented, not violated).

### 2.3 `normalize(text: str) -> str` — ordered pipeline

Order is normative. It was validated against the full Unicode code-point range plus randomized
multi-character fuzzing; a different order breaks `REQ-002-015`.

| Step | Operation | Example | Reason |
|------|-----------|---------|--------|
| N1 | `unicodedata.normalize("NFC", …)` | `cafe`+`U+0301` → `café` | Unifies the two encodings of one accented character so they group as one row |
| N2 | `str.casefold()` — **not** `str.lower()` | `Straße` → `strasse`; `ΣΊΣΥΦΟΣ` → `σίσυφοσ` | `lower()` leaves `ß` and final sigma `ς` unmatched to `ss`/`σ`. ADR-0008 commits to multiple languages, so caseless matching must be Unicode-full, not ASCII-shaped |
| N3 | `unicodedata.normalize("NFC", …)` again | `ﬀ`-style expansions recomposed | Casefolding can emit decomposed sequences; re-composing restores a canonical single form |
| N4 | Fold every apostrophe in §2.1 to `U+0027`, every hyphen to `U+002D` | `don't` ≡ `don't` | Typographic vs. ASCII apostrophe is an arbitrary artifact of the authoring tool; not unifying them splits one word into two rows |
| N5 | Strip leading and trailing joiners; discard the token if nothing remains | `ŉ` (`U+0149`) → `'n` → `n` | Casefold expansion can expose a leading apostrophe. Without N5 the pipeline is **not** idempotent |

**N4 MUST run after N2/N3, never before.** `U+0149 ŉ` casefolds to `U+02BC` + `n`; folding
apostrophes first makes `normalize(normalize(x)) != normalize(x)` and fails `REQ-002-015`.

**The standalone `ŉ` of the N5 row above is illustrative only and MUST NOT be the sole test of
that ordering.** Standing alone, the `U+02BC` that casefolding exposes lands on an edge, so N5
strips it under *either* order and `normalize("ŉ")` is `n`, idempotently, even when N4 runs first.
The ordering is therefore only observable when the expansion occurs **internally**, where N5 cannot
reach it: with N4 misordered, `a\u0149b` yields `aʼnb` on the first pass and `a'nb` on the second.
Any suite verifying this ordering MUST include at least one internal occurrence; a suite built on
the standalone example alone reports green on a non-idempotent pipeline.

Diacritics are **preserved**: `sí` ≠ `si`, `schon` ≠ `schön`. NFKC/NFKD are rejected — their
compatibility mappings are lossy (`½` → `1⁄2`, `№` → `No`) and nobody asked for them; deferring is
cheaper than reversing.

### 2.4 Ordering of the result (product-visible)

The API MUST return the list already ordered; the frontend MUST NOT re-sort (`REQ-002-014`).
Rows are ordered by the **grouping key** (the normalized form), never by the display form of
§2.5. The sort key is `(diacritic-stripped casefolded form, normalized form)`, where the first
component is the NFD form of the grouping key with `M*` characters removed, computed **for ordering
only** and never stored. The second component makes the order total and deterministic.

**Why the grouping key and not the display form.** The grouping key is the row's stable identity: it
is unique per row by construction and depends only on the set of forms present. The display form
depends on *frequencies*, so importing one more occurrence can flip a group's majority surface form
and would silently re-sort the table for a reason that has nothing to do with alphabet. Ordering by
the key keeps the position of a row a function of the word itself (Art. VI.2 reproducibility). The
two can therefore differ visibly — a row keyed `strasse` and displayed `Straße` sorts under `s`,
not under `S` — and that is the intended behaviour, not a defect.

Locale collation (`locale.strxfrm`, ICU) is rejected: it needs a known language (OQ-2, deferred),
is process-global, and varies across platforms, which would break Art. VI.2 reproducibility and CI
determinism.

### 2.5 Display form selection (product-visible)

The grouping key and the display form are **distinct concepts** and MUST NOT be conflated. The key
(`normalized_form`) is a synthetic identity used only to decide which occurrences belong to the same
row. The display form (`display_form`) is the string the user reads, and it MUST be a **textual
form** (`Occurrence.raw_text`) that literally occurs in the imported text.

Within one group, the display form is selected as:

| Step | Rule |
|------|------|
| D1 | Count occurrences of each distinct `raw_text` in the group |
| D2 | Select the `raw_text` with the highest count |
| D3 | Break ties by ascending Unicode code-point order of the `raw_text` |

Worked example — the synthetic text `Straße straße STRASSE Straße` produces one group keyed
`strasse` with counts `Straße: 2`, `straße: 1`, `STRASSE: 1`. D2 selects `Straße`. Had all three
counted `1`, D3 would select `STRASSE` (`U+0053 S` precedes `U+0073 s`).

**Why this rule is order-independent.** D1 is a count over a multiset, D2 is a maximum over those
counts, and D3 is a total order over distinct strings. All three are functions of the *multiset* of
textual forms, so no permutation of the input can change the outcome.

**A first-occurrence rule is FORBIDDEN.** "Display whichever surface form appeared first" is a
function of the input *sequence*, not the multiset. Re-ordering the input would change the displayed
value while the grouping key stayed identical, which breaks `REQ-002-016` and the `AGENTS.md §6`
order-independence invariant. Any tie-break based on position, insertion order, database row id, or
iteration order of an unordered collection is forbidden for the same reason.

---

## 3. Requirements — text-import capability

### Requirement: REQ-002-001 — Upload-only `.txt` intake

The API SHALL accept an imported text only as a multipart file upload on
`POST /api/v1/imports`. It MUST NOT accept a filesystem path, URL, or inline text body.

Acceptance: **AC-002-01** — Given a running backend, when a client posts a multipart request with a
synthetic `.txt` part, then the response is HTTP 201 with a frequency-table body (and an import
`id`); and when a client posts a JSON body carrying a filesystem path instead of a file part, then
the response is HTTP 422 and nothing is imported — no `Book` row is created.

#### Scenario: A synthetic file uploads successfully

- GIVEN a synthetic UTF-8 `.txt` file
- WHEN the client posts it as multipart form data to `POST /api/v1/imports`
- THEN the response is HTTP 201 and carries the frequency table

#### Scenario: A filesystem path is refused

- GIVEN a JSON body `{"path": "/tmp/book.txt"}`
- WHEN the client posts it to `POST /api/v1/imports`
- THEN the response is HTTP 422 and no import is persisted

### Requirement: REQ-002-002 — Extension and content-type validation before processing

The API SHALL reject an upload whose filename extension is not `.txt` (case-insensitive) or whose
declared content type is neither `text/plain` nor `application/octet-stream`, and SHALL do so
**before** decoding or tokenizing any byte. The error MUST carry code `INVALID_FILE_TYPE` and MUST
name the accepted extension. The supplied filename MUST NOT be used as a filesystem path
(`docs/architecture/overview.md §9`).

Acceptance: **AC-002-02** — Given a running backend, when a client uploads `notes.pdf`, then the
response is HTTP 422 with error code `INVALID_FILE_TYPE`, the message contains `.txt`, and nothing
is imported — no `Book` row and no `Occurrence` row exist.

#### Scenario: Wrong extension is refused before processing

- GIVEN a file named `notes.pdf` with valid UTF-8 bytes
- WHEN the client uploads it
- THEN the response is HTTP 422 with code `INVALID_FILE_TYPE`
- AND no persistence occurred

#### Scenario: Uppercase extension is accepted

- GIVEN a file named `SAMPLE.TXT` with valid UTF-8 bytes
- WHEN the client uploads it
- THEN the response is HTTP 201

### Requirement: REQ-002-003 — Configurable maximum import size

`Settings` SHALL expose `max_import_size_bytes: int`, overridable by the environment variable
`MAX_IMPORT_SIZE_BYTES`, defaulting to `4194304` (4 MiB). An upload whose byte length exceeds the
configured value MUST be rejected with HTTP 413, error code `FILE_TOO_LARGE`, and a message stating
the configured limit. The limit MUST be enforced before tokenization.

**Why 4 MiB.** The design quantified a 10 MiB import at roughly 1.72 M occurrence rows and about
12 s of synchronous request time, which invites proxy and browser timeouts on a path that has no
asynchronous state machine (§5 CONTRA-1). 4 MiB is roughly 688 k tokens and about 3.4 s, and still
clears *War and Peace* (≈3.2 MB of plain text, public domain) with margin. The value remains one
setting, so a user with a larger corpus and a tolerant proxy can raise it.

Acceptance: **AC-002-03** — Given `Settings()` constructed with no environment overrides, when
`max_import_size_bytes` is read, then it equals `4194304`; and given `MAX_IMPORT_SIZE_BYTES=64`,
then it equals `64`.
**AC-002-04** — Given `max_import_size_bytes = 64`, when a client uploads a 65-byte `.txt`, then the
response is HTTP 413 with code `FILE_TOO_LARGE`, the message contains `64`, and nothing is imported
— no `Book` row exists.

#### Scenario: Default limit is the documented value

- GIVEN no `MAX_IMPORT_SIZE_BYTES` in the environment
- WHEN `Settings()` is constructed
- THEN `max_import_size_bytes` equals `4194304`

#### Scenario: Oversized upload is rejected with the limit surfaced

- GIVEN `max_import_size_bytes` configured to `64`
- WHEN a client uploads a 65-byte file
- THEN the response is HTTP 413 with code `FILE_TOO_LARGE` and the message names the limit

#### Scenario: A file exactly at the limit is accepted

- GIVEN `max_import_size_bytes` configured to `64`
- WHEN a client uploads a 64-byte valid UTF-8 file
- THEN the response is HTTP 201

### Requirement: REQ-002-004 — Strict UTF-8 decoding with an actionable rejection

The text extractor SHALL decode uploaded bytes as UTF-8 with strict error handling. It MUST NOT
guess, sniff, or fall back to another encoding, and MUST NOT add a dependency. A byte sequence that
is not valid UTF-8 MUST be rejected with HTTP 422, error code `INVALID_ENCODING`, and a message that
names the expected encoding (`UTF-8`) and tells the user how to convert the file. A leading UTF-8
BOM (`U+FEFF`) MUST be stripped and MUST NOT cause rejection.

Acceptance: **AC-002-05** — Given a running backend, when a client uploads a `.txt` containing the
byte `0xFF` (invalid UTF-8), then the response is HTTP 422 with error code `INVALID_ENCODING`, the
message contains `UTF-8` and conversion guidance, and nothing is imported (no `Book` row exists);
and when a client uploads UTF-8 bytes prefixed with `EF BB BF`, then the response is HTTP 201 and
the first normalized form does not begin with `U+FEFF`.

#### Scenario: Non-UTF-8 bytes are rejected actionably

- GIVEN a `.txt` file containing the byte `0xFF`
- WHEN the client uploads it
- THEN the response is HTTP 422 with code `INVALID_ENCODING`
- AND the message names `UTF-8` and how to convert the file

#### Scenario: A UTF-8 BOM is tolerated

- GIVEN a UTF-8 file whose first three bytes are `EF BB BF`
- WHEN the client uploads it
- THEN the response is HTTP 201 and no normalized form starts with `U+FEFF`

### Requirement: REQ-002-005 — Pure, language-generic tokenization and normalization

The domain SHALL provide tokenization and a pure `normalize(text: str) -> str` implementing §2
exactly. Both MUST live in `domain/`, MUST import only the standard library, MUST NOT import
FastAPI, SQLAlchemy, Pydantic, or any NLP library (Art. VII.1), and MUST NOT take a language
parameter, carry a language default, or contain an ISO-639 literal (`REQ-PFB-LANG-01`).

Acceptance: **AC-002-06** — Given the shipped `domain/` package, when its source is inspected, then
no module imports `fastapi`, `sqlalchemy`, `pydantic`, or `spacy`, and no function exposes a
language parameter or ISO-639 string literal.
**AC-002-07** — Given each rule row in §2.2 and §2.3, when the documented input is tokenized and
normalized, then the documented output is produced exactly, for all of `T1`–`T10` and `N1`–`N5`.

#### Scenario: Tokenization rules hold on synthetic input

- GIVEN the synthetic text `state-of-the-art don't 2026 covid19 word—word snake_case`
- WHEN it is tokenized
- THEN the tokens are `state-of-the-art`, `don't`, `covid19`, `word`, `word`, `snake`, `case`
- AND `2026` is absent because it contains no letter

#### Scenario: Case folding is Unicode-full, not ASCII-shaped

- GIVEN the synthetic tokens `Straße` and `STRASSE`
- WHEN each is normalized
- THEN both produce `strasse`

#### Scenario: Combining marks survive tokenization

- GIVEN a token written as `cafe` followed by `U+0301`
- WHEN it is tokenized and normalized
- THEN it produces `café`, identical to the precomposed spelling

#### Scenario: The domain has no framework dependency

- GIVEN the `domain/` package
- WHEN its imports are inspected
- THEN only standard-library modules are imported

### Requirement: REQ-002-006 — Aggregation by normalized form with frequency and order

The application SHALL aggregate occurrences by normalized form, producing for each distinct form a
frequency equal to its number of occurrences, ordered per §2.4. `GET /api/v1/imports/{id}` MUST
return that list together with the count of distinct normalized forms and the total token count.
Each row MUST carry **both** the grouping key `normalized_form` and the display form `display_form`
selected per §2.5 and `REQ-002-018`.

Acceptance: **AC-002-08** — Given a synthetic text where a normalized form occurs three times, when
the import is read, then that form appears exactly once in the list with `frequency` equal to `3`,
each row carries a non-empty `normalized_form` and a non-empty `display_form`, and the sum of all
`frequency` values equals the reported total token count.
**AC-002-09** — Given a synthetic text containing `zebra`, `ábaco`, and `abandonar`, when the import
is read, then the returned order is `ábaco`, `abandonar`, `zebra` by `normalized_form`, and the
frontend renders that received order unchanged.

#### Scenario: Repeated forms collapse into one row with a count

- GIVEN a synthetic text where one normalized form occurs three times
- WHEN the client reads the import
- THEN the form appears once with `frequency` `3`

#### Scenario: Ordering is diacritic-insensitive and server-side

- GIVEN a synthetic text containing `zebra`, `ábaco`, and `abandonar`
- WHEN the client reads the import
- THEN the response order is `ábaco`, `abandonar`, `zebra`

### Requirement: REQ-002-007 — Neither the grouping key nor the display form is labelled "lemma" or "lexeme"

No API path, request field, response key, error code, database column, identifier, or user-visible
string introduced by this capability SHALL contain `lemma`, `lemas`, `lexeme`, or `lexema`. The
grouping key MUST be named `normalized_form` and the display form MUST be named `display_form`.
Neither name nor any label attached to either MAY describe the value as a lemma or a lexeme — a
display form is the most frequent *textual form* in the group, not a canonical dictionary headword.
The UI MUST state that it lists normalized forms and MUST NOT claim that inflected forms are merged
(Art. V.1).

The prohibition binds **naming and contract surface, not explanatory prose**. Module, class, and
function docstrings and `#` comments MAY name the forbidden concepts, because the clearest way to
record that a value is not a lemma is to write the word "lemma". One exception, and it is a
narrowing rather than a loophole: a docstring that a framework publishes is contract surface, not
prose. A Pydantic model docstring is serialised by FastAPI into `components.schemas.*.description`
in the served `/openapi.json` and rendered in the API browser, so it remains fully bound by the
 prohibition above.

The guard is narrowed by an explicit, enumerated allow-list of exact symbol and property names. Every
exemption SHALL be the pair `(exact name, owning site)`, bound to the narrowest structural unit that
contains exactly the exempt names. Binding to a container that also holds non-exempt names is
forbidden; paths are carried from traversal rather than re-split from rendered strings; the binding
implementation exists once and is shared by every guard; and each owning set lists only names its site
declares. JSON Schema and served OpenAPI exemptions MUST bind to properties within their declaring
definition or component, never to the definition or component as a whole. These are the `B1`–`B6`
constraints defined by `003-lemmatization-pos` §2.1. The module-docstring exemption is justified by
`E2(b-i)`: anything published from it is re-caught by the served OpenAPI leg.

Acceptance: **AC-002-10** — Given the shipped backend and frontend sources, the versioned JSON
Schemas, and the served OpenAPI document, when each is inspected structurally for
`lemma|lemas|lexeme|lexema` (case-insensitive), then every match is a member of the explicitly
enumerated allow-list and is bound to its owning site, and the match count outside that allow-list
is zero in each of:

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
- **The persisted column names** reflected from `Base.metadata`: each allow-listed column is exempt
  only on the table that owns it.
- **The versioned JSON Schemas** (`api/schemas/*.json`), parsed as JSON: every object key and every
  string value. JSON has no docstring, so nothing in it is exempt. Each allow-listed property is
  exempt only as the property of the definition that declares it; renaming a sibling property to an
  allow-listed name MUST produce a violation, and a key containing `.` MUST NOT inherit an ancestor
  segment's exemption.
- **The served OpenAPI document**: every string. This leg is what keeps the docstring exemption
  scoped — it catches a docstring at exactly the point where it stops being prose and becomes
  published contract.

and when the read response is inspected, then the per-row grouping key is `normalized_form` and the
per-row display value is `display_form`; and when the binding implementation is located, exactly one
implementation exists and every guard that needs it imports it; and when each absence assertion is
inspected, its test has a mutation check with recorded output, a non-vacuity check, and a boundary
control.

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

#### Scenario: No lemma naming leaks into the contract

- GIVEN the backend sources, frontend sources, JSON Schema, and served OpenAPI document
- WHEN each is inspected structurally for `lemma|lemas|lexeme|lexema` — identifiers and
  non-docstring literals for Python, identifiers and non-comment literals (including template
  literals and JSX text) for TypeScript, keys and values for JSON and OpenAPI
- THEN there are zero matches

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

### Requirement: REQ-002-008 — Persisted corpus with a verifiable migration

The import SHALL persist a `Book` row and one `Occurrence` row per emitted token through a
repository port, so the frequency table is readable after process restart. Exactly one additive
Alembic revision SHALL create both tables; its `downgrade()` MUST return the schema to the
empty-schema baseline. The repository port MUST be defined in `application/` and implemented in
`infrastructure/` (Art. VII.2–3).

Acceptance: **AC-002-11** — Given a fresh SQLite database at the empty-schema baseline, when
`alembic upgrade head` runs, then it exits `0` and `book` and `occurrence` tables exist; and when
`alembic downgrade -1` runs, then it exits `0` and neither table exists.
**AC-002-12** — Given a text imported through the API, when a new repository instance reads the
import by `id` against the same database, then the same normalized-form frequency list is returned.

#### Scenario: Migration applies and reverses cleanly

- GIVEN a fresh database at the empty-schema baseline
- WHEN `alembic upgrade head` then `alembic downgrade -1` run
- THEN both succeed and the schema returns to the baseline

#### Scenario: Imported data survives a new session

- GIVEN a text imported through the API
- WHEN a new repository session reads the import
- THEN the identical frequency list is returned

### Requirement: REQ-002-009 — Cryptographic content hash on `Book`

`Book` SHALL store `content_hash`, the lowercase hexadecimal SHA-256 digest of the **raw uploaded
bytes** computed before decoding (Art. VI.3). The value MUST be stored for every successful import.

Acceptance: **AC-002-13** — Given the same synthetic file uploaded twice, when both `Book` rows are
read, then both `content_hash` values are equal to the SHA-256 hex digest of the file bytes computed
independently by the test; and given two files differing by one byte, then their hashes differ.

#### Scenario: Identical bytes produce an identical hash

- GIVEN the same synthetic file uploaded twice
- WHEN both `Book` rows are read
- THEN both `content_hash` values equal the independently computed SHA-256 hex digest

#### Scenario: A one-byte difference changes the hash

- GIVEN two files differing by exactly one byte
- WHEN both are imported
- THEN their `content_hash` values differ

### Requirement: REQ-002-010 — Per-occurrence POS reserved and unpopulated

`Occurrence` SHALL expose a nullable `pos` attribute that is `None` for every row written by this
capability. No entity introduced here SHALL carry a global or aggregate part-of-speech field, and
`pos` MUST NOT appear on `Book` (ADR-0006, Art. V.2–3). `raw_text` (textual form) and
`normalized_text` (normalized form) MUST remain distinct columns and MUST NOT collapse (Art. V.1).

Acceptance: **AC-002-14** — Given a successful import of a synthetic text, when every persisted
`Occurrence` is read, then each has `pos is None`, each has both `raw_text` and `normalized_text`
populated as separate values, and the `book` table has no part-of-speech column.

#### Scenario: POS is reserved but unset

- GIVEN a successfully imported synthetic text
- WHEN all `Occurrence` rows are read
- THEN every row has `pos is None`

#### Scenario: Textual and normalized forms stay distinct

- GIVEN a synthetic text containing `Straße`
- WHEN the occurrence is read
- THEN `raw_text` is `Straße` and `normalized_text` is `strasse`

### Requirement: REQ-002-011 — Deleting an import and its derived data, with confirmation

`DELETE /api/v1/imports/{id}` SHALL delete the `Book` and every `Occurrence` derived from it,
leaving no orphan rows (Art. IV.8, Art. X.4). Deleting an unknown or already-deleted `id` MUST
return HTTP 404 with error code `IMPORT_NOT_FOUND`. The UI MUST require an explicit confirmation
step before issuing the request, satisfying Art. IX.5 by the *confirmation* branch; the backend
deletion is permanent and is not undoable.

**A soft delete is FORBIDDEN — do not "improve" this into one.** Two independent reasons, settled at
maintainer review:

1. Art. IX.5 (`docs/constitution.md:100`) reads "pedirán confirmación **o** serán reversibles" — a
   disjunction. Confirmation alone satisfies it. Reversibility is not additionally required.
2. Art. IV.8 (`docs/constitution.md:54`) reads "La aplicación permitirá eliminar los datos
   importados". Retaining the user's text behind a `deleted_at` flag does **not** delete it, so a
   soft delete would put the two articles in conflict. That obligation is legal — copyright and
   privacy (Art. IV.1–5) — not cosmetic, and Art. IV wins.

Therefore no `deleted_at` column, no tombstone row, no archive table, and no recycle bin. The rows
are removed.

Acceptance: **AC-002-15** — Given an imported text with at least one occurrence, when the client
sends `DELETE /api/v1/imports/{id}`, then the response is HTTP 204, a subsequent
`GET /api/v1/imports/{id}` returns HTTP 404 with code `IMPORT_NOT_FOUND`, and zero `Occurrence` rows
remain for that `book_id`.
**AC-002-16** — Given the import list rendered in the UI, when the user activates the delete control
once, then no `DELETE` request is issued and a confirmation control is presented with an accessible
name; and when the user confirms, then exactly one `DELETE` request is issued; and when the user
cancels, then no `DELETE` request is issued.

#### Scenario: Deletion removes the book and its occurrences

- GIVEN an imported text with occurrences
- WHEN the client sends `DELETE /api/v1/imports/{id}`
- THEN the response is HTTP 204 and no occurrence remains for that `book_id`

#### Scenario: Deleting an unknown import is a clean 404

- GIVEN an `id` that does not exist
- WHEN the client sends `DELETE /api/v1/imports/{id}`
- THEN the response is HTTP 404 with code `IMPORT_NOT_FOUND`

#### Scenario: The UI requires confirmation first

- GIVEN the import is rendered with a delete control
- WHEN the user activates delete once and then cancels
- THEN no `DELETE` request is issued

### Requirement: REQ-002-012 — An empty file is a successful import with zero unique forms

A syntactically valid upload containing zero bytes, or containing only separators, SHALL succeed.
The response MUST be HTTP 201, `import_status` MUST be `succeeded`, the normalized-form list MUST be
empty, and the distinct-form count MUST be `0`. The UI MUST render an explicit zero state, not an
error state (Art. IX.3).

Acceptance: **AC-002-17** — Given a zero-byte `.txt` and, separately, a `.txt` containing only
`" \n\t"`, when each is uploaded, then each response is HTTP 201 with `import_status` `succeeded`,
an empty list, a distinct-form count of `0`, and the UI shows a zero-state message rather than an
error.

#### Scenario: A zero-byte file imports successfully

- GIVEN a zero-byte `.txt` file
- WHEN the client uploads it
- THEN the response is HTTP 201 with an empty list and a count of `0`

#### Scenario: A whitespace-only file imports successfully

- GIVEN a `.txt` containing only spaces, tabs, and newlines
- WHEN the client uploads it
- THEN the response is HTTP 201 with a count of `0`

### Requirement: REQ-002-013 — Logs never contain raw imported text

No log record emitted by import, read, or delete SHALL contain any substring of the imported text,
any normalized form or display form derived from it, or the raw uploaded bytes (Art. X.2). A display
form is literal text from the user's file and is therefore covered by this prohibition. Failure logs MUST
identify the failure by error code and import `id` only. `import_status` MUST be one of `succeeded`
or `failed`; no intermediate state ships in this capability. This terminal-only status is
**confirmed** against Art. IX.6 — see §5 `CONTRA-1`; the in-flight signal is a UI state
(`REQ-002-014`), not a persisted status value.

> **Contract note (schema narrowing).** The two-value enum above is the domain vocabulary. The
> serialized response contract deliberately narrows it: `api/schemas/import.v1.json` sets
> `import_status` to `{"enum": ["succeeded"]}`, because a failed import returns an error envelope and
> never a 201 success body — `"failed"` can never be serialized on this route. `persistence/models.py`
> documents the same terminal-only invariant. The narrowing is intentional and tighter than this
> requirement; it is recorded here so the spec/contract divergence is explicit rather than a trap for a
> reader who expects the served enum to carry both values.

Acceptance: **AC-002-18** — Given a synthetic text containing the distinctive sentinel token
`zzqxsentinel`, when the file is imported and, separately, when an import fails after decoding, then
no captured log record from any logger contains `zzqxsentinel`, and the failure record contains the
error code and the import `id`.

#### Scenario: A successful import logs no content

- GIVEN a synthetic text containing the sentinel `zzqxsentinel`
- WHEN the import succeeds
- THEN no captured log record contains `zzqxsentinel`

#### Scenario: A failing import logs a code, not content

- GIVEN an import that fails
- WHEN log records are captured
- THEN they contain the error code and import `id` and no imported text

### Requirement: REQ-002-014 — The frontend duplicates no linguistic rules

The frontend SHALL render exactly what the API returns. It MUST NOT tokenize, case-fold, apply
Unicode normalization, strip punctuation, re-sort the list, recompute any frequency, derive a
grouping key, or select a display form (Art. VII.5). Both `normalized_form` and `display_form`
arrive from the API already computed. The import form and the frequency table MUST be keyboard-navigable, MUST have
accessible labels, MUST make loading, success, and error states perceptible without colour alone,
and MUST NOT depend on colour to convey the frequency column (Art. IX.1–4).

Acceptance: **AC-002-19** — Given the frontend sources under `apps/web/src/`, when they are searched
for `normalize(`, `toLowerCase(`, `localeCompare(`, `.sort(`, and `NFC|NFD|NFKC|NFKD`, then there
are zero matches in import or frequency-table code; and given a mocked API response in a deliberately
non-alphabetical order whose `display_form` differs from its `normalized_form`, when the table
renders, then the DOM row order equals the received order and each row shows the received
`display_form` verbatim without re-deriving it from `normalized_form`.

#### Scenario: No linguistic transformation client-side

- GIVEN the import and frequency-table sources
- WHEN they are searched for normalization, case-folding, and sorting calls
- THEN there are zero matches

#### Scenario: The table renders the received order verbatim

- GIVEN a mocked response whose rows are not alphabetical
- WHEN the table renders
- THEN the DOM row order equals the received order

#### Scenario: The display form is rendered, not recomputed

- GIVEN a mocked row with `normalized_form` `strasse` and `display_form` `Straße`
- WHEN the table renders
- THEN the visible cell reads `Straße`

#### Scenario: The table is perceivable without colour

- GIVEN the rendered frequency table
- WHEN it is inspected
- THEN each row exposes its form and frequency as text with an accessible column header

### Requirement: REQ-002-015 — `normalize` is idempotent

For every string `x`, `normalize(normalize(x))` SHALL equal `normalize(x)` (`AGENTS.md §6`).

Acceptance: **AC-002-20** — Given a Hypothesis strategy generating arbitrary text, when `normalize`
is applied twice, then the result equals a single application for every generated example, with no
`filterwarnings` violation.

#### Scenario: Double normalization is a fixed point

- GIVEN arbitrary generated text
- WHEN `normalize` is applied twice
- THEN the result equals one application

#### Scenario: Known adversarial code points are stable

- GIVEN the tokens `ŉ` (`U+0149`), `Straße`, `ẞ` (`U+1E9E`), `İ` (`U+0130`), and `ΣΊΣΥΦΟΣ`
- WHEN each is normalized twice
- THEN each equals its single normalization

### Requirement: REQ-002-016 — The unique-form set, frequencies, and display forms are independent of input order

For any multiset of tokens, the set of distinct normalized forms, each form's frequency, **and each
group's selected display form** SHALL be independent of the order in which the tokens are presented.
The display form is included because §2.5 selects it from data that could tempt a positional
tie-break; extending the property here is what mechanically forbids one. This is the normalized-form
analogue of the `AGENTS.md §6` invariant phrased over lemmas; it MUST be re-verified against real
lemmas when lemmatization ships, and the test MUST carry that note.

Acceptance: **AC-002-21** — Given a Hypothesis strategy generating a list of `(raw_text)` token
strings, when the list is aggregated and then aggregated again after an arbitrary permutation, then
the set of distinct normalized forms, the full form-to-frequency mapping, **and** the full
form-to-display-form mapping are all equal.

#### Scenario: Permuting the input does not change the result

- GIVEN a generated list of tokens
- WHEN it is aggregated, permuted, and aggregated again
- THEN the form-to-frequency mappings are equal
- AND the form-to-display-form mappings are equal

#### Scenario: Permuting a tied group does not change the display form

- GIVEN the synthetic tokens `Straße`, `straße`, `STRASSE`, each occurring once
- WHEN they are aggregated in any permutation
- THEN the display form is `STRASSE` every time, by the §2.5 D3 code-point tie-break

### Requirement: REQ-002-017 — Frequencies are never negative

Every frequency produced by aggregation, persisted on read, or returned by the API SHALL be an
integer greater than or equal to `1` for any listed form, and the aggregate MUST never contain a
form with frequency `0` or below (`AGENTS.md §6`).

Acceptance: **AC-002-22** — Given a Hypothesis strategy generating arbitrary token lists, when the
tokens are aggregated, then every frequency is an integer `>= 1`; and given any API read response,
then every `frequency` value is an integer `>= 1`.

#### Scenario: Generated inputs never yield a non-positive frequency

- GIVEN an arbitrary generated token list
- WHEN it is aggregated
- THEN every frequency is an integer `>= 1`

#### Scenario: The API never returns a zero row

- GIVEN any successful read response
- WHEN every row is inspected
- THEN no `frequency` is `0` or negative

### Requirement: REQ-002-018 — Each group displays a real surface form, chosen deterministically

The grouping key and the display form SHALL be distinct, separately named values, and both SHALL be
returned for every row.

- The **grouping key** (`normalized_form`) is the §2.3 output. It decides row membership only. It is
  synthetic and MAY be a spelling that appears nowhere in the text.
- The **display form** (`display_form`) is the value shown to the user. It SHALL be a textual form
  (`Occurrence.raw_text`) that literally occurs in the imported text, selected by §2.5 D1–D3:
  highest occurrence count within the group, ties broken by ascending Unicode code-point order.

Selection MUST be a function of the multiset of textual forms in the group only. Any rule that
depends on input sequence, insertion order, database row id, or the iteration order of an unordered
collection is FORBIDDEN, because it would break `REQ-002-016`.

Neither value MAY be called, labelled, or presented as a lemma or a lexeme (`REQ-002-007`). The
display form is the most frequent inflected spelling, not a dictionary headword; the two must not be
confused (Art. V.1, Art. V.4).

The display form SHALL be derived by aggregation over `Occurrence.raw_text`, which
`REQ-002-010` already persists. **No new column and no change to the `REQ-002-008` migration is
required.**

Acceptance: **AC-002-23** — Given the synthetic text `Straße straße STRASSE Straße`, when the import
is read, then exactly one row is returned, its `normalized_form` is `strasse`, its `display_form` is
`Straße`, and its `frequency` is `4`; and given the synthetic text `Straße straße STRASSE` where all
three counts tie at `1`, then `display_form` is `STRASSE` by code-point order.
**AC-002-24** — Given any successful read response, when every row is inspected, then each row
carries both `normalized_form` and `display_form` as separate non-empty keys, and each `display_form`
value occurs as a substring of the originally imported text; and given the persisted schema, when it
is inspected, then no column was added for the display form.

#### Scenario: The majority surface form is displayed

- GIVEN the synthetic text `Straße straße STRASSE Straße`
- WHEN the client reads the import
- THEN one row is returned with `normalized_form` `strasse`, `display_form` `Straße`, `frequency` `4`

#### Scenario: A tie is broken by code-point order, not by position

- GIVEN the synthetic text `Straße straße STRASSE`, each form occurring once
- WHEN the client reads the import
- THEN `display_form` is `STRASSE`

#### Scenario: The display form exists in the source text

- GIVEN any imported synthetic text
- WHEN every returned `display_form` is checked against the source
- THEN each occurs verbatim in the imported text

#### Scenario: No schema change was needed

- GIVEN the shipped Alembic revision
- WHEN its `upgrade()` is inspected
- THEN it creates no column dedicated to the display form

---

## 4. Error contract

| Code | HTTP | Trigger | Class (Art. X.3) |
|------|------|---------|------------------|
| `INVALID_FILE_TYPE` | 422 | Extension not `.txt`, or unsupported content type | Format |
| `FILE_TOO_LARGE` | 413 | Byte length above `max_import_size_bytes` | User |
| `INVALID_ENCODING` | 422 | Bytes are not valid UTF-8 | Format |
| `IMPORT_NOT_FOUND` | 404 | Unknown or already-deleted import `id` | User |
| `INVALID_REQUEST` | 422 | Request validation fails, including an omitted multipart file or an incompatible body (`AC-002-01`) | User |

Every error body MUST carry a distinct code and a message that is comprehensible and actionable
(Art. VIII.4), including `INVALID_REQUEST`; all rows use the shared error envelope. Error bodies MUST
NOT contain imported text, stack traces, file paths, or environment values.

---

## 5. Ambiguities and contradictions recorded and resolved (AGENTS.md §9)

Each item below was an ambiguity or contradiction in the inputs. None was resolved silently.
All are **closed**; the Status column records the outcome.

| ID | Ambiguity | Resolution in this spec | Status |
|----|-----------|-------------------------|--------|
| AMB-1 | The proposal defines `Occurrence.position` as "index/offset in the source" — two incompatible meanings. A character offset is unstable across Unicode normalization forms. | `position` is the zero-based **token index** (§2.2 T10). | Accepted. Reversible later via an additive `char_offset` column |
| AMB-2 | Art. IX.5 requires destructive actions to be "confirmed **or** reversible"; the orchestrator brief said "confirmed **and** reversible". | The brief was wrong; `docs/constitution.md:100` is a disjunction, so confirmation alone satisfies it. A soft delete would additionally **conflict** with Art. IV.8 (`docs/constitution.md:54`): text retained behind a `deleted_at` flag is not deleted, and that duty is legal (copyright, privacy), not cosmetic. See `REQ-002-011`. | **Closed. Permanent delete is binding — soft delete is forbidden, not merely out of scope** |
| AMB-3 | No maximum file size exists anywhere in the docs (explore OQ-4 unanswered). | Default `4194304` bytes (4 MiB) — above *War and Peace* (≈3.2 MB plain text, public domain), below the synchronous-timeout risk the design quantified. | Accepted. Configurable via one setting |
| AMB-4 | `AGENTS.md §6` phrases the order-independence invariant over *lemmas*, which do not exist in this slice. | Tested over normalized forms with an explicit in-test note to re-verify against lemmas later (`REQ-002-016`), per explore §7 option 1. | Accepted |
| AMB-5 | "Alphabetical" is undefined for accented and non-Latin scripts, and true collation needs a known language (OQ-2, deferred). | Diacritic-insensitive deterministic sort key over the **grouping key** (§2.4); locale collation rejected on Art. VI.2 reproducibility grounds. | Accepted |
| CONTRA-1 | The design read Art. IX.6 as requiring *progress reporting* for a long import, and concluded that a terminal-only `succeeded\|failed` `import_status` could not satisfy it — an apparent contradiction with `REQ-002-013` and with deferring the async state machine. | **Not a contradiction.** `docs/constitution.md:101` reads "Las operaciones largas mostrarán progreso **o** estado" — a disjunction, exactly like Art. IX.5 in `AMB-2`. Showing *state* discharges the article; *progress* is one permitted way to do it, not the only one. A perceptible "importing" state in the UI therefore satisfies Art. IX.6, and Art. IX.3 ("Carga, éxito y error serán perceptibles", `docs/constitution.md:98`) already makes that loading state mandatory via `REQ-002-014`. | **Closed. Terminal `import_status` stays as specified; the `pending/running/cancelled` async state machine stays deferred; a perceptible in-flight UI state is what discharges Art. IX.6. Do not re-litigate — the article is a disjunction** |

## 6. Product-visible decisions

These change what appears on screen. They are decisions, not implementation details.
PV-1 is **resolved**; PV-2 through PV-7 were accepted as specified.

| # | Decision | What the user sees | Status |
|---|----------|--------------------|--------|
| PV-1 | `casefold()` over `lower()` (N2) as the **grouping key**, with a real surface form as the **display form** (§2.5, `REQ-002-018`) | `Straße` and `STRASSE` collapse into one row, and that row reads `Straße` — a spelling that genuinely occurs in the text. The synthetic key `strasse` is never displayed | **Resolved.** Neither original option was taken: grouping stays casefolded, display is the majority surface form |
| PV-2 | Pure numerals are dropped (T6) | Years, chapter numbers, and page numbers never appear; `covid19` and `3rd` still do | Accepted |
| PV-3 | Hyphenated compounds stay whole (T2) | `state-of-the-art` is one row; `state`, `of`, `the`, `art` do not each gain a count from it | Accepted |
| PV-4 | Apostrophe variants unify (N4) | `don't` and `don't` are one row; `l'homme` stays one row rather than `l'` + `homme` | Accepted |
| PV-5 | Diacritic-insensitive ordering by the grouping key (§2.4) | `ábaco` sorts next to `abandonar`, not after `zebra`. A row keyed `strasse` and displayed `Straße` sorts under `s` | Accepted |
| PV-6 | Line-break hyphenation is not rejoined (T9) | A word split across lines as `well-⏎known` yields `well` and `known` | Accepted; needs a dictionary, deferred with OQ-4 |
| PV-7 | Default size limit **4 MiB** | Uploads above 4 MiB are refused with the limit named. Roughly 688 k tokens and ≈3.4 s of synchronous work; 10 MiB would have been ≈1.72 M rows and ≈12 s, inviting proxy and browser timeouts | Accepted; configurable |

## 7. Explicit non-additions

This capability does NOT specify: lemmatization, `Lexeme`, POS population, multiword-expression
detection, manual corrections, provenance or confidence population, language detection, an NLP
dependency, EPUB, asynchronous processing states beyond `succeeded`/`failed` (confirmed against
Art. IX.6 — see §5 `CONTRA-1`), re-import
deduplication by `content_hash`, or pagination of the frequency table. It does NOT choose module
names, file layouts, DTO shapes, or task ordering — design and tasks own those.

It also explicitly does NOT permit: a soft delete, `deleted_at` column, tombstone, or recycle bin
(`REQ-002-011`, AMB-2); a user-configurable display-form preference; or any second display
candidate beyond the single `display_form` of `REQ-002-018`.

## 8. Verification hooks

| Hook | Check | Verifies |
|------|-------|----------|
| H1 | Structural (AST) search for `lemma\|lemas\|lexeme\|lexema` across `apps/api/src/wheel_vocabulary/` and `apps/web/src/` — identifiers and non-docstring literals — plus every key and string value of `import.v1.json` and of the served OpenAPI document, returns zero matches. Docstrings and `#` comments are out of scope, per the AC-002-10 rationale; do not revert this to a grep | AC-002-10 |
| H2 | Search `domain/` for `fastapi\|sqlalchemy\|pydantic\|spacy` and for ISO-639 literals returns zero matches | AC-002-06 |
| H3 | `alembic upgrade head` then `alembic downgrade -1` against a fresh SQLite both exit `0` | AC-002-11 |
| H4 | Hypothesis properties for idempotence, order-independence (keys, frequencies, **and display forms**), and non-negative frequency pass with the `filterwarnings` gate unchanged | AC-002-20, AC-002-21, AC-002-22 |
| H5 | Log capture over a sentinel-bearing synthetic import yields zero records containing the sentinel | AC-002-18 |
| H6 | Every fixture used by this capability is synthetic or public domain and resembles no copyrighted series (Art. IV.1–2) | Art. IV compliance |
| H7 | Every returned `display_form` occurs verbatim in the imported source text, and the Alembic revision adds no display-form column | AC-002-24 |
| H8 | Search the shipped Alembic revision and models for `deleted_at\|is_deleted\|tombstone` returns zero matches | AC-002-15, AMB-2 |

---

## 9. Requirements — frequency-form presentation

These requirements record the observable frontend behavior for frequency results, merged from the
archived `ui-display-normalized-explanation` change. They do not change the backend, API schema,
persistence, or import semantics.

### Requirement: REQ-UI-DISPLAY-NORMALIZED-001 — Display Both API Forms

The frequency results UI MUST render, for every frequency row, the API-provided
`display_form` as the primary displayed text and the API-provided
`normalized_form` as a visible secondary value identified as the grouping key.

#### Scenario: Every row exposes both values

- GIVEN the API returns multiple frequency rows with distinct `display_form` and `normalized_form` values
- WHEN the frequency results UI renders
- THEN each row visibly contains both values without deriving either value

### Requirement: REQ-UI-DISPLAY-NORMALIZED-002 — Preserve Display Text

The UI MUST preserve the API-provided display form verbatim, including casing
and characters, while showing the normalized key separately.

#### Scenario: German sharp-s remains readable

- GIVEN a row has `display_form` `Straße` and `normalized_form` `strasse`
- WHEN the row renders
- THEN `Straße` is the primary displayed text
- AND `strasse` is visible as the grouping key

### Requirement: REQ-UI-DISPLAY-NORMALIZED-003 — Explain the Secondary Role

The UI MUST use concise, accessible copy that describes `normalized_form` as a
grouping key or secondary value, MUST NOT describe it as canonical spelling,
and MUST NOT use lemma or lexeme terminology.

#### Scenario: Copy avoids linguistic overclaiming

- GIVEN a frequency table contains displayed forms and grouping keys
- WHEN a user reads its caption, labels, or accessible text
- THEN the roles of the two values are understandable
- AND no canonical-spelling, lemma, or lexeme claim is presented

### Requirement: REQ-UI-DISPLAY-NORMALIZED-004 — Render API Values Without Derivation

The frontend MUST render both received fields directly and MUST NOT normalize,
case-fold, transliterate, tokenize, or otherwise linguistically derive values
for presentation.

#### Scenario: Non-derived values remain unchanged

- GIVEN `display_form` and `normalized_form` differ in casing or spelling
- WHEN the component renders the row
- THEN the exact received strings are shown in their assigned roles
- AND no client-side linguistic transformation occurs

### Requirement: REQ-UI-DISPLAY-NORMALIZED-005 — Keep the SPEC-002 Boundary

This UI change MUST be limited to the observable frequency-row presentation and
MUST NOT require backend/API schema, persistence, import, or stored-data changes.

#### Scenario: Existing contract remains sufficient

- GIVEN the existing API contract provides both form fields
- WHEN the UI behavior is implemented and validated
- THEN no backend or API contract change is needed
- AND focused Vitest component/contract tests, frontend typecheck, and lint validate the slice

### Presentation validation expectations

- Focused Vitest component/contract tests MUST cover row values, `Straße`/`strasse`, accessible copy, and direct API rendering.
- Frontend typecheck and lint MUST pass.
- Playwright SHOULD cover the copy only if the primary import flow treats it as critical.

### Presentation task traceability

| Requirement | Tasks |
|---|---|
| REQ-UI-DISPLAY-NORMALIZED-001 | T101, T201 |
| REQ-UI-DISPLAY-NORMALIZED-002 | T102 |
| REQ-UI-DISPLAY-NORMALIZED-003 | T102, T201 |
| REQ-UI-DISPLAY-NORMALIZED-004 | T101, T202, T301 |
| REQ-UI-DISPLAY-NORMALIZED-005 | T202, T301, T303 |

### Presentation non-goals

- Backend, API schema, persistence, or import changes.
- Frontend linguistic derivation or normalization.
- Heavy Unicode-oriented explanatory copy.
- Lemma or lexeme terminology.

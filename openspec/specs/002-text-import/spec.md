# Delta for 002-text-import: Frequency Form Explanation

This delta records the observable frontend behavior for frequency results. It
does not change the backend, API schema, persistence, or import semantics.

## ADDED Requirements

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

## Validation Expectations

- Focused Vitest component/contract tests MUST cover row values, `Straße`/`strasse`, accessible copy, and direct API rendering.
- Frontend typecheck and lint MUST pass.
- Playwright SHOULD cover the copy only if the primary import flow treats it as critical.

## Task Traceability

| Requirement | Tasks |
|---|---|
| REQ-UI-DISPLAY-NORMALIZED-001 | T101, T201 |
| REQ-UI-DISPLAY-NORMALIZED-002 | T102 |
| REQ-UI-DISPLAY-NORMALIZED-003 | T102, T201 |
| REQ-UI-DISPLAY-NORMALIZED-004 | T101, T202, T301 |
| REQ-UI-DISPLAY-NORMALIZED-005 | T202, T301, T303 |

## Non-Goals

- Backend, API schema, persistence, or import changes.
- Frontend linguistic derivation or normalization.
- Heavy Unicode-oriented explanatory copy.
- Lemma or lexeme terminology.

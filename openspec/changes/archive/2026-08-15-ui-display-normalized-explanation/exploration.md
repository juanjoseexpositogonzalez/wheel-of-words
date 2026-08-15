## Exploration: Explain display-form and normalized-form differences in the UI

### Current State
The results screen renders `FrequencyTable` with the API-provided `display_form` and frequency, preserving server order and performing no client-side linguistic transformation. The table caption says that it is a list of normalized forms, but the grouping key (`normalized_form`) is not rendered, and no copy explains why the visible display form can differ from the normalized key.

The frontend contract already carries both values in `FormFrequency`. Existing tests pin verbatim display rendering with `Straße` versus `strasse`, received ordering, accessible headers, and the absence of frontend linguistic rules. The E2E test only asserts that the table and a representative word are visible.

SPEC-002 defines the distinction normatively: `normalized_form` is a synthetic grouping identity; `display_form` is a textual form that literally occurs in the imported text and is selected deterministically. Rows are sorted by the normalized key, not the display form. Tokenization removes `U+00AD SOFT HYPHEN` before tokenization, so invisible formatting can affect grouping/tokenization without appearing as a visible character. `REQ-002-007` requires the UI to say it lists normalized forms and forbids lemma/lexeme terminology; `REQ-002-018` and AC-002-24 protect the separate display-form contract.

### Affected Areas
- `apps/web/src/components/FrequencyTable.tsx` — likely location for explanatory copy and, if selected, an additional normalized-key presentation.
- `apps/web/tests/components/FrequencyTable.test.tsx` — component-level assertions for the explanation, accessible labeling, and the existing display-form/verbatim invariants.
- `apps/web/e2e/import.spec.ts` — optional observable-flow assertion if the copy is considered part of the critical import experience.
- `apps/web/src/types/imports.ts` — already exposes both fields; likely no contract change unless the UI requires a new API value.
- `openspec/changes/text-import/specs/002-text-import/spec.md` — should be updated only if the new behavior changes the SPEC-002 UI contract or adds an acceptance criterion.
- `openspec/changes/ui-display-normalized-explanation/` — future proposal/spec/design/tasks artifacts for this slice; the current exploration is the only artifact created in this phase.

### Approaches
1. **Inline explanatory note using the existing display** — Keep the two-column table and add concise, accessible copy near the caption explaining that visible values are textual forms, while normalized forms are grouping keys; mention that invisible formatting such as SOFT HYPHEN may be removed before grouping.
   - Pros: Smallest vertical slice; no API or data-model change; preserves the current table and existing acceptance behavior; easiest to test and translate.
   - Cons: Users cannot inspect the exact normalized key for a particular row; exact wording needs a product decision to avoid overloading a compact table.
   - Effort: Low

2. **Expose both values in the table** — Add a normalized-form column or row-level disclosure while retaining the display-form column as the primary visible value, accompanied by explanatory copy.
   - Pros: Makes the distinction concrete for every result, including `Straße`/`strasse`; gives users a direct way to understand grouping and sorting.
   - Cons: Larger visual and accessibility change; requires deciding whether the normalized key is user-facing terminology or technical detail; increases E2E and responsive-layout coverage; may make invisible-character cases confusing rather than clearer.
   - Effort: Medium

### Recommendation
Treat this as a product/UI change with a possible SPEC-002 documentation delta, not as a backend or linguistic-processing change. Start with Approach 1: add a short Spanish explanatory note while keeping the API-provided `display_form` as the visible value and explicitly stating that normalized forms are internal grouping keys. Before proposal, the product decision should settle the exact user-facing copy and whether SOFT HYPHEN should be named directly or described as invisible formatting. Do not add frontend normalization, derive one field from the other, or change the API contract.

If the product goal requires users to audit exact grouping decisions, choose Approach 2 instead and make the normalized key an explicitly secondary value with a defined accessible label. In either case, update SPEC-002 only to record the new observable UI explanation and acceptance criterion; do not rewrite the existing raw/display/normalized semantics.

Likely later checks are focused Vitest assertions for the explanatory text and the `display_form`/`normalized_form` distinction, the existing no-linguistic-rules and no-forbidden-naming contract tests, TypeScript/lint checks, and one Playwright assertion if the note is part of the primary import journey. A synthetic fixture such as `Straße`/`strasse` is sufficient; an explicit SOFT HYPHEN fixture should remain synthetic and should verify copy/visibility expectations rather than duplicate backend tokenization rules.

### Risks
- Ambiguous copy could imply that `display_form` is the raw source string in all cases without explaining that SOFT HYPHEN is removed before tokenization, or could expose implementation detail users do not need.
- Showing `normalized_form` may turn a stable grouping key into an apparent canonical spelling, conflicting with the spec's statement that it is synthetic and not a dictionary headword.
- Updating SPEC-002 while the text-import change remains an active/blocked hotspot could create unnecessary merge contention; keep the proposal delta isolated until the product decision is made.
- Any frontend implementation must preserve the existing AST-based no-linguistic-rules and no-forbidden-naming guards.

### Ready for Proposal
Yes, with one product decision to carry into the proposal: approve the minimal explanatory note or require row-level visibility of the normalized key, and approve neutral Spanish wording for invisible-formatting examples. The recommended default is the minimal note, which is independent of blocked text-import hotspots and fits the single-PR, 400-line review budget.

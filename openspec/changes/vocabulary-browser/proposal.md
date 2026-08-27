# Proposal: Vocabulary Browser (005-vocabulary-browser)

## Intent

Roadmap item 5 (`docs/product-vision.md` §12, "Navegador de vocabulario"). Annotation output is currently viewable only as a flat, position-ordered occurrence table (`apps/web/src/components/AnnotationTable.tsx`), one `<tr>` per token. This change adds a read-only grouped vocabulary view: occurrences aggregated into `(lemma, POS)` study units with counts, filterable by POS.

## Problem Statement

- `GET /api/v1/imports/{id}/annotation` returns one row per occurrence with no `GROUP BY` (`annotation_repository.py:106`); a 688k-occurrence book serializes 688k objects to answer "what are the lemma groups" (`openspec/specs/002-text-import/spec.md:213-215`).
- No aggregate read path exists on the API. `api/annotation.ts` exposes no grouping or filter parameter on the wire.
- The one server-side grouping precedent is `frequency_pairs` (`book_repository.py:94`), which groups on `(raw_text, normalized_text)`, not lemma/POS.

## Scope

### In Scope (full capability)
- New read-only endpoint returning `(lemma, POS)` groups with occurrence counts.
- Grouped frontend list view.
- POS filter over those groups.

### Out of Scope (non-goals)
- **Manual-correction writing** — reserved for SPEC-004 (`openspec/specs/003-lemmatization-pos/spec.md:185`, R6). No write affordance, even inline.
- **Confidence-driven behaviour** — C6 (`spec.md:132`). The browser MUST NOT sort, filter, threshold, badge, or visually treat groups by confidence. Confidence may be shown per occurrence only.
- **Stored per-lemma POS** — P5 (§2.2) forbids it; POS grouping is computed at query time.
- Pagination controls beyond the slice-1 decision below.

## Capabilities

### New Capabilities
- `005-vocabulary-browser`: read-only grouped vocabulary view — `(lemma, POS)` groups with counts and a POS filter, computed over precedence-resolved values.

### Modified Capabilities
- None. This change inherits SPEC-003 constraints but adds no requirement to `003-lemmatization-pos`.

## Adopted Decisions

### Decision A — group by the `(lemma, POS)` pair, not lemma alone
Rationale: ADR-0006 rejects a single global POS per lemma; `run` VERB and `run` NOUN are distinct study items. Grouping by lemma alone merges homographs and makes the POS filter semantically ambiguous. Matches the `frequency_pairs` SQL-grouping precedent (`book_repository.py:94`).
- **NULL POS** (analyzer emitted a lemma but no tag) → its own visible bucket for that lemma, not hidden.
- **NULL lemma** (pre-annotation, a valid documented state per S1-S4) → one visible "unannotated" group, never silently excluded.
- **Tradeoff (honest):** a learner sees `run` twice with no visual link unless the UI re-groups for display. Accepted — correctness over cosmetic linking.

### Decision B — aggregate on precedence-resolved effective values, never raw `occurrence.lemma`/`.pos`
Rationale: Constitution Art. V and ADR-0007 require manual corrections to take precedence and reprocessing to never silently overwrite them. SPEC-003 resolves precedence in Python at read time (`annotation_repository.py`, `AnnotatedOccurrence.__post_init__`), not SQL. Grouping on the raw columns would make corrections silently invisible once SPEC-004 ships a writer — an Art. V violation introduced today, observable only later.
- **Tradeoff (honest):** this is the harder path. The aggregate query must join `manual_correction` and resolve precedence before `GROUP BY`, so the existing covering index cannot serve it unchanged. Specified now, with tests passing against seeded corrections, so SPEC-004 extends a working mechanism instead of retrofitting one.

## Open-Question Resolutions

| # | Question | Resolution |
|---|----------|-----------|
| 1 | Grouping semantics | Decided: `(lemma, POS)` pair (Decision A). |
| 2 | NULL lemma / NULL POS | Both bucketed and **visible** (Decision A); never silently dropped (S1-S4, `spec.md` §2.6). |
| 3 | Precedence in aggregation | Decided: effective values (Decision B). |
| 4 | Pagination | Slice 1 returns all groups for one book (bounded by distinct `(lemma, POS)` count, far below the 688k occurrence count), matching `frequency_pairs`. **Gated:** design MUST benchmark at the 688k ceiling and add pagination only if a stated response-size budget is exceeded. A default with a verification gate, not a `TODO`. |
| 5 | Indexing | Deferred to design + benchmark (`@pytest.mark.bench`, per `test_import_bench.py`). Note: Decision B's join means a plain `(book_id, lemma, pos)` covering index does not fully serve effective-value grouping — index strategy is entangled with B and MUST be benchmarked, not assumed. |
| 6 | Route shape | Decided: **new** endpoint `GET /api/v1/imports/{id}/vocabulary`. Keeps `annotation.v1.json` byte-identical (hardening treats it as load-bearing state); avoids widening the locked annotation contract. |

## Vertical Slice & Changed-Line Estimate

Full scope (endpoint + repository aggregate + DTOs + client + types + grouped component + POS filter + TDD tests per `AGENTS.md`) forecasts **~600-750 changed lines, over the 400-line review budget**. Slice boundary:

- **Slice 1 (this PR)** — grouped read: new endpoint + precedence-resolved aggregate (Decision B baked in) + DTOs + minimal frontend list view. **No POS filter control.** Observable value: user sees `(lemma, POS)` groups with counts (Art. III). Estimate **~400-430 lines** — near budget; `sdd-tasks` MUST confirm the forecast and, if over, chain a backend-PR then a frontend-PR.
- **Slice 2 (follow-up)** — POS filter as a `WHERE effective_pos = ?` predicate plus a facet control on the settled group shape.

Honest note: the anchor's "filter by POS" is fully delivered only at slice 2; slice 1 delivers the grouping. Delivery strategy is `ask-on-risk` and this forecast exceeds 400 lines — a human decision on slicing is expected before apply.

## Inherited Constraints (binding, cited)

| ID | File:line | Binds this change to |
|----|-----------|----------------------|
| C6 | `openspec/specs/003-lemmatization-pos/spec.md:132` | No browser behaviour keys off confidence. |
| R6 | `openspec/specs/003-lemmatization-pos/spec.md:185` | No `ManualCorrection` write path. |
| P5 | `openspec/specs/003-lemmatization-pos/spec.md` §2.2 | No stored aggregate POS; compute at query time. |
| L6 | `openspec/specs/003-lemmatization-pos/spec.md` §2.1 | Lemma is per-occurrence; groups are derived views, not persisted. |
| S1-S4 | `openspec/specs/003-lemmatization-pos/spec.md` §2.6 | Pre-annotation (all-NULL) is a valid state to render. |
| Scale | `openspec/specs/002-text-import/spec.md:213-215, 834` | 688k-occurrence ceiling drives the pagination/index gates. |

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `.../persistence/annotation_repository.py` | New | Aggregate method, precedence-resolved. Existing `read()` untouched. |
| `.../persistence/models.py` | Modified? | Possible new index, pending benchmark (Q5). |
| `apps/api/migrations/versions/0004_*.py` | New? | Migration only if an index is added. |
| `.../application/annotation/` | New | Use case for the grouped read. |
| `.../api/routes/annotation.py`, `api/dtos/annotation.py` | New | New route + group DTOs. |
| `apps/web/src/api/annotation.ts`, `types/annotation.ts` | Modified | New client fn + group types. |
| `apps/web/src/components/VocabularyBrowser.tsx` | New | Grouped view; reuses `UPOS_LABELS`. `AnnotationTable.tsx` untouched. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Slice 1 exceeds the 400-line budget | Medium | `sdd-tasks` confirms forecast; chain backend/frontend PRs; ask-on-risk gate. |
| Effective-value grouping cannot use a covering index → slow at 688k | Medium | Design-phase benchmark (Q5) before commit. |
| UI accidentally keys on confidence | Low | C6 non-goal stated; verify in review. |
| Annotation contract widening | Low | New endpoint (Q6); `annotation.v1.json` untouched. |

## Rollback Plan

New endpoint, new frontend component, and one optional additive index migration. Rollback: revert the endpoint and component; run the `0004` down-revision to drop the additive index. No existing contract, route, or table column is modified, so the revert is isolated.

## Dependencies

- SPEC-003 data model (shipped): `occurrence.lemma`/`.pos`, `annotation_provenance`, `manual_correction` (schema-only, no writer yet).

## Success Criteria

- [ ] `GET /api/v1/imports/{id}/vocabulary` returns `(lemma, POS)` groups with occurrence counts, resolved on effective values.
- [ ] NULL-lemma and NULL-POS buckets are present and visible.
- [ ] No confidence-driven behaviour anywhere in the browser (C6).
- [ ] No `ManualCorrection` write path added (R6).
- [ ] `annotation.v1.json` remains byte-identical.
- [ ] Grouping proven correct against seeded manual corrections.

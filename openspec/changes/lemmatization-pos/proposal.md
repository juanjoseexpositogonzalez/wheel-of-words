# Proposal: SPEC-003 — Lemmatization and per-occurrence POS

Change slug `lemmatization-pos`. Roadmap item 4 (`docs/product-vision.md` §12). Builds on the
archived `002-text-import`, which reserved the hooks this capability fills.

## Intent

SPEC-002 reserved `Occurrence.pos` (always `None`) and a `Book.language` hook but ships no NLP.
Learners cannot see that run/ran/running are one word, nor each occurrence's part of speech.
SPEC-003 populates a genuine per-occurrence lemma and POS through a swappable spaCy adapter — the
data foundation the vocabulary browser (item 5) later groups on.

## Scope

### In Scope
- Pin `apps/api` venv to **Python 3.12** (hard prerequisite — see Dependencies).
- Pure `LinguisticAnnotation` value object + `LinguisticAnalyzer` port (pre-tokenized input;
  multi-language by design per ADR-0008; only English installed/tested this cycle).
- `SpacyLinguisticAnalyzer` (English, tagger+lemmatizer only) building `Doc(vocab, words=tokens)`
  from the SPEC-002 token stream — never re-tokenizes (protects REQ-002-005).
- Additive Alembic migration: `Occurrence.lemma`, per-occurrence provenance (source,
  model_version, processed_at, pos/lemma confidence), `ManualCorrection` table (schema only).
- `AnnotateImport` use case + repository write/read with **read-time precedence** (ADR-0007).
- API + frontend surface exposing `lemma`, `pos`, and **always-visible confidence**.

### Out of Scope (non-goals)
- Manual-correction write path/UI → **SPEC-004** (schema + precedence laid now so it can build on it).
- Proper-noun filter → item 6 (`PROPN` persisted like any tag; `product-vision §10 step 4` stays
  knowingly incomplete until then).
- Multiword expressions → item 7 / ADR-0009. Vocabulary browser UI, language detection, and
  per-language adapter selection are also deferred.

## Capabilities

### New Capabilities
- `003-lemmatization-pos`: per-occurrence lemma + POS + provenance/confidence via a spaCy
  port/adapter; read-time correction precedence; Python 3.12 pin.

### Modified Capabilities
- `002-text-import` (REQ-002-010): **conditional** — needed only if annotation writes into the
  import path so import rows gain `pos`/`lemma`. The recommended design keeps annotation a
  **separate step**, leaving REQ-002-010 literally true → then this is **None**. sdd-spec/sdd-design
  MUST resolve. `normalized_form`/`display_form` and REQ-002-007's naming ban stay untouched; the new
  `lemma` field is a distinct, honestly-named concept (a real lemma, unlike 002's normalized form).

## Approach

spaCy confirmed, not reopened (ADR-0001). Hexagonal: value object in `domain/` (stdlib only), port
in `application/lemmatization/`, adapter in `infrastructure/nlp/` — no spaCy type crosses the port.
Confidence stays nullable where the pipeline exposes none (Art. V.7 "cuando proceda"). Precedence is
enforced on every read, never at write, so reprocessing can never silently overwrite a correction.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `apps/api/pyproject.toml` + venv | Modified | Pin Python 3.12; add spaCy + English model |
| `domain/models.py` | New | `LinguisticAnnotation` frozen dataclass |
| `application/lemmatization/` | New | `LinguisticAnalyzer` port + `AnnotateImport` |
| `infrastructure/nlp/spacy_analyzer.py` | New | spaCy adapter (pre-tokenized input) |
| `infrastructure/persistence/` | Modified | lemma/provenance write, precedence read |
| `apps/api/migrations/versions/` | New | additive revision |
| `api/`, `apps/web/` | Modified | expose lemma/pos/confidence |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| `spacy 3.8.15` wheels are cp312/cp313 only; venv resolves to 3.14.5 | High | Pin 3.12 first, as its own slice, before any NLP work |
| Cut 2 (adapter + migration + use case + repo write) busts the 400-line budget | Med | sdd-tasks MUST re-forecast Cut 2; if over, split use-case+repo from adapter+migration (the exploration PR1/PR2 fault line) rather than shipping oversized |
| Confidence is visible but non-actionable for one cycle | Accepted | Documented assumption, not oversight: acting on low confidence arrives in SPEC-004 |
| Reprocess-existing-imports is unstated in the 3-cut shape | Low | sdd-spec confirms whether reprocess ships now or defers (backfill is possible from `raw_text` ordered by `position`, no re-upload) |

## Rollback Plan

Additive migration only: `downgrade()` drops `lemma`, the provenance table, and `ManualCorrection`,
returning to the SPEC-002 baseline (mirrors `0002_book_occurrence.py`, tested by
`test_alembic_0002.py`). Revert the venv pin and drop the spaCy dependency. Feature-branch chain:
revert child PRs newest-first back to the SPEC-003 tracker branch.

## Dependencies

**Python 3.12 pin is a hard prerequisite.** `spacy 3.8.15` publishes wheels for **cp312 and cp313
only** — no cp314 — making spaCy itself the narrowest constraint in the chain. (`thinc`, spaCy's own
dependency, is pinned by spaCy to `<8.4.0,>=8.3.12` and resolves to `8.3.13`, which ships cp312,
cp313 **and** cp314 — thinc is not the constraint.) The venv currently resolves to 3.14.5, and
`spacy` metadata (`<3.15,>=3.9`) is not a safety net: `uv add spacy` resolves, then attempts a
fragile C++/Cython source build against an interpreter with no prebuilt wheel. Pin before any
adapter work.

## Success Criteria

- [ ] A newly imported book yields per-occurrence `lemma` and `pos` from spaCy; run/ran/running share lemma `run`.
- [ ] Provenance + confidence persisted per occurrence; confidence visible in the API response.
- [ ] A seeded manual correction wins at read time; reprocessing never overwrites it.
- [ ] `domain/` imports no spaCy/SQLAlchemy/FastAPI (isolation guard extended, not replaced).
- [ ] Each of the 3 chained PRs lands under 400 authored lines, or records a `size:exception`.

## Delivery (chained PRs — feature-branch-chain onto the SPEC-003 tracker branch)

1. Pin Python 3.12 + domain port (`LinguisticAnnotation`, `LinguisticAnalyzer`).
2. spaCy adapter + Alembic migration + `AnnotateImport` use case + repository write path.
3. API + frontend surface (lemma / pos / confidence).

Priority under budget pressure: **lemma population is non-negotiable** — if a cut is forced, POS
yields before lemma (Decision 1). PR 1 targets the tracker branch; PRs 2–3 target the previous
slice; rebase until each child diff is clean.

# Exploration: SPEC-003 — Lemmatization and per-occurrence POS

Change slug: `lemmatization-pos`. Roadmap item 4 (`docs/product-vision.md` §12). Builds on
`002-text-import` (23 requirements, archived) which deliberately reserved the hooks this
capability fills.

## Current State

SPEC-002 shipped a hexagonal import pipeline that already anticipates this capability but does
not implement it:

- `ImportText.execute()` (`apps/api/src/wheel_vocabulary/application/imports/use_cases.py:111`)
  runs an ordered gate: classify → size-check → read+hash → decode → **`_gate_5_aggregate`**
  (tokenize + normalize + build frequency table) → persist. No NLP step exists anywhere in this
  chain.
- `domain/text/tokenizer.py::tokenize()` and `domain/text/normalizer.py::normalize()` are pure,
  stdlib-only, and constitute the **normative tokenization contract** (spec §2, `REQ-002-005`).
  They produce `Token(raw_text, position)` value objects. SPEC-003 MUST consume this token stream
  as-is — re-tokenizing inside the NLP adapter would silently diverge from `REQ-002-005` and
  break `AC-002-24` (display forms must be verbatim source slices).
- `domain/frequency.py::build_table()` aggregates by `normalized_form` only. It has no concept of
  POS or lemma and does not need one — POS/lemma live on `Occurrence`, not on the frequency row
  (ADR-0006).
- `infrastructure/persistence/models.py`:
  - `Occurrence.pos: Mapped[str | None]` (line 75) — **the reserved slot**, always `None` today.
    No index on it.
  - `Occurrence.raw_text` / `Occurrence.normalized_text` are separate columns (`REQ-002-010`) —
    SPEC-003 must not collapse them and must not reuse either as a lemma stand-in.
  - `Book.language: Mapped[str | None]` (line 37) — an ADR-0008 hook, always unset. No raw text is
    stored anywhere on `Book`; only `content_hash` is kept.
  - Migration `0002_book_occurrence.py` already created `occurrence.pos` — SPEC-003 does not need
    to add that column, only to start writing to it.
- `application/imports/ports.py::BookRepository` (Protocol) has `create`, `frequency_pairs`,
  `delete` — no method writes or reads POS/lemma. A new port is needed.
- `SqlAlchemyBookRepository._insert_occurrences()` (`infrastructure/persistence/book_repository.py:65`)
  hard-codes `"pos": None` on every insert — this is the literal line SPEC-003 changes.
- No `Lexeme`, `WordForm`, `ManualCorrection`, or `LinguisticAnalyzer` code exists yet. They are
  named only in `docs/architecture/overview.md §4/§8` and ADR-0006/0007 as forward references.
- `apps/api/pyproject.toml` has **no NLP dependency** — `spacy`/`stanza` is absent from
  `dependencies`.
- ADR-0001 (Accepted, 2026-07-15) already decided: *"spaCy como primer adaptador NLP."*
  ADR-0002 and ADR-0005 both describe the `LinguisticAnalyzer` port as spaCy's home. This is a
  standing precedent, not an open question — see §2 below.

### Affected Areas

- `apps/api/src/wheel_vocabulary/domain/models.py` — add a pure `LinguisticAnnotation`-shaped
  value object (or extend `Token`) if the domain needs one; stdlib only.
- `apps/api/src/wheel_vocabulary/application/imports/ports.py` (or a new
  `application/lemmatization/ports.py`) — new `LinguisticAnalyzer` Protocol.
- `apps/api/src/wheel_vocabulary/application/imports/use_cases.py` — new use case to run
  annotation (see §6).
- `apps/api/src/wheel_vocabulary/infrastructure/persistence/models.py` — `Occurrence.pos` starts
  being populated; likely a new `lemma` column and provenance columns/table.
- `apps/api/src/wheel_vocabulary/infrastructure/persistence/book_repository.py` — annotation
  write path.
- `apps/api/src/wheel_vocabulary/infrastructure/nlp/` (new package) — spaCy adapter.
- `apps/api/migrations/versions/` — new additive revision(s).
- `apps/api/pyproject.toml` — add `spacy` dependency + English model.
- `apps/api/src/wheel_vocabulary/api/` — DTO/schema updates to surface `pos`/`lemma`, possibly a
  new route.
- `apps/web/src/types/imports.ts`, `apps/web/src/components/FrequencyTable.tsx` — only if the
  scope decision in §6 includes a frontend surface.

## NLP Engine Choice: spaCy (confirmed, not re-opened)

ADR-0001 already committed to spaCy as the first NLP adapter, and ADR-0002/0005 already frame the
`LinguisticAnalyzer` port around it being swappable. I am not re-litigating that decision from
zero — I am validating it against this capability's concrete requirements, because ADRs 0001/0002
predate any real NLP code and the commitment deserves a sanity check before design locks it in.

| Dimension | spaCy | Stanza | Verdict |
|---|---|---|---|
| Model footprint | Small pipelines (`en_core_web_sm`-class, tagger+lemmatizer only, NER/parser can be disabled) are tens of MB, pip-installable, no runtime download prompt beyond the initial `pip`/`uv` install | PyTorch-based; the runtime itself (PyTorch) is hundreds of MB before any language model is added, plus a first-run model download from Stanford's CDN | spaCy — ADR-0005 local-first wants the smallest footprint that still runs fully offline after install |
| POS/lemma quality on literary prose | Rule-based + statistical lemmatizer (edit-tree lemmatizer in modern pipelines) tuned per-language; solid on standard prose, degrades somewhat on archaic/dialectal literary language same as any statistical tagger | Trained uniformly on Universal Dependencies treebanks across ~70 languages; often edges out spaCy on languages with sparser spaCy training data, comparable to spaCy on English/major languages | Roughly comparable for the first-implemented language (English); Stanza's edge shows up mainly on lower-resource languages, which is a later-roadmap concern (ADR-0008 OQ-4), not this slice |
| Multi-language support (ADR-0008) | 20+ languages shipped as separate small models, consistent API across languages | ~70 languages via Universal Dependencies, generally more linguistically consistent tagsets | Both satisfy "adapter-swappable"; spaCy's per-language model catalog already covers the realistic near-term roadmap |
| Licensing | MIT | Apache 2.0 | Both compatible; no blocker either way |
| Offline operation | Fully offline once the model wheel is installed; no network call at inference time | Fully offline once the model is downloaded once and cached locally; the first-run download itself must be treated deliberately under ADR-0005 (downloading a *model* is not the same as sending *book content* to a third party, but it still needs to be an explicit, documented step, not a silent implicit network call inside a request handler) | spaCy — model ships as a normal Python package via `uv add`, so "offline after install" is unambiguous and matches how this project already manages dependencies. Stanza's download-on-first-use pattern needs extra plumbing to stay honest about ADR-0005 |
| Processing time on a full novel (~100–150k tokens) | Tagger+lemmatizer-only pipeline (NER/parser disabled) runs on the order of low single-digit seconds to tens of seconds on CPU | Neural biaffine pipeline is materially slower on CPU without a GPU — plausibly low minutes for the same input | spaCy — keeps a full-novel pass inside "fast enough that Art. IX.6's disjunction (progress *or* state) is satisfied by state alone," matching the precedent SPEC-002 already set for import (`CONTRA-1`) |
| Python 3.12 compatibility | Supported on 3.12; **this repo's actual `apps/api/.venv` resolves to Python 3.14.5** (`pyproject.toml` only declares `>=3.12`), which is a real, unverified risk — spaCy's C-extension build chain (Cython/Thinc/NumPy) has historically lagged the newest CPython by months | Same class of risk via PyTorch's own C-extension build chain, typically lags newest CPython similarly or worse | **Verify before design locks in**: run `uv add spacy` (or `spacy[lookups]` + `en_core_web_sm`) against the *actual* 3.14 venv as the first design-phase spike. If wheels are unavailable for 3.14, the fix is pinning the project's `uv`-managed Python to 3.12 for `apps/api` (already permitted by `requires-python = ">=3.12"`), not swapping NLP libraries |

**Recommendation: spaCy, small English pipeline (`en_core_web_sm`-class), tagger+lemmatizer
components only, NER/parser disabled.** This confirms ADR-0001 rather than reopening it. The one
concrete, non-hedged risk to close before `sdd-design`: confirm spaCy has installable wheels for
the Python version the `apps/api` venv actually resolves to. If not, pin the venv to 3.12 — do not
default to it silently.

## Provenance and Confidence — Proposed Data Model

Constitution Art. V.7 ("resultados automáticos guardan fuente, versión, fecha y confianza cuando
proceda") and ADR-0007 (manual corrections precedence, no silent overwrite on reprocessing) both
bind this directly.

Proposed shape (to be finalized in `sdd-design`, not decided here):

1. **`Occurrence.lemma: str | None`** — new nullable column, additive migration, mirrors the
   existing `pos` column exactly (same nullability, same "reserved, capability-scoped" pattern
   SPEC-002 already established for `pos`).
2. **Provenance lives per-occurrence, not per-field.** spaCy computes POS and lemma in one
   `nlp(doc)` pass sharing the same pipeline/model identity, so one provenance row per occurrence
   is sufficient rather than one row per `(occurrence, field)`:
   - `occurrence_id` (FK, unique — one provenance row per occurrence)
   - `source` (e.g. `"spacy"`)
   - `model_version` (e.g. `"en_core_web_sm-3.7.x"`)
   - `processed_at`
   - `pos_confidence: float | None`, `lemma_confidence: float | None` — nullable independently,
     because spaCy does not expose a per-token confidence score for every component; Art. V.7's
     "cuando proceda" (when applicable) licenses leaving it `NULL` rather than fabricating a
     number.
3. **`ManualCorrection`** — separate table, one row per correction:
   - `id`, `occurrence_id` (FK), `field` (`"pos" | "lemma"`), `corrected_value`, `corrected_at`.
   - Read path: serving `pos`/`lemma` for an occurrence checks `ManualCorrection` for that
     `(occurrence_id, field)` first; falls back to the automatic value only if absent.
   - Reprocessing path: writes the new automatic value to `Occurrence.pos`/`lemma` and the
     provenance row **unconditionally** — but a `ManualCorrection` row is never read from or
     written to by reprocessing, and the *serving* layer is what re-applies precedence on every
     read. This satisfies ADR-0007 point 2 literally: the automatic value is "discarded or stored
     as a shadow value — never applied as the active value" whenever a correction exists, because
     the correction is checked at read time, every time, not baked into a single write.

This shape needs a `sdd-design` pass to settle exact column types and index strategy, but the
precedence mechanism (auto value + correction table, merged at read time, never at write time) is
the one piece that must not drift — it is the literal ADR-0007 invariant.

## Hexagonal Placement

Following the exact pattern SPEC-002 already established (`application/imports/ports.py` is where
`BookRepository`/`TextExtractor` live as `Protocol`s, not in `domain/`) — despite ADR-0002 saying
the port "lives in domain or application," the codebase's actual precedent is application-layer
ports. SPEC-003 should follow the codebase, not the ADR's looser wording.

- **`domain/`** (stdlib only, zero framework/NLP imports, verified by the existing AST-based
  `tests/unit/test_domain_isolation.py` guard which SPEC-003 extends, not replaces):
  - A pure `LinguisticAnnotation` (or similarly named) frozen dataclass: `pos: str`,
    `lemma: str`, no behavior. This is the shape the port returns and the shape use cases pass to
    the repository — spaCy's `Doc`/`Token` objects must never cross this boundary.
- **`application/lemmatization/ports.py`** (new module, or extend `imports/ports.py` — a design
  decision, not an exploration one):
  ```python
  @runtime_checkable
  class LinguisticAnalyzer(Protocol):
      def analyze(self, tokens: Sequence[str]) -> Sequence[LinguisticAnnotation]:
          """One annotation per input token, same order, same length.

          Takes pre-tokenized text — never raw text — so spaCy's own tokenizer
          never runs and REQ-002-005's token boundaries stay the single source
          of truth (see Migration Impact below).
          """
          ...
  ```
  - `application/lemmatization/use_cases.py`: a new use case (e.g. `AnnotateImport`) that reads
    an import's occurrences ordered by `position`, calls `LinguisticAnalyzer.analyze()`, and
    persists through a new repository method.
- **`infrastructure/nlp/spacy_analyzer.py`** (new): `SpacyLinguisticAnalyzer` implementing the
  port. Wraps `spacy.load(...)`, builds a `spacy.tokens.Doc(vocab, words=tokens)` from the
  **already-tokenized** SPEC-002 token stream (critical — see Migration Impact), runs only the
  tagger+lemmatizer components, converts spaCy's `Token.pos_`/`Token.lemma_` into the pure
  `LinguisticAnnotation` value objects. No spaCy type ever leaves this module.
- **`infrastructure/persistence/`**: extend `SqlAlchemyBookRepository` (or add a sibling
  `SqlAlchemyAnnotationRepository`) with the write/read methods for annotation + provenance +
  correction precedence.
- **`api/`**: new DTO fields (`pos`, `lemma`) on whatever response surfaces occurrence-level data,
  and — pending the scope decision in the next section — possibly a new route to trigger
  annotation. No business rule (e.g. no precedence logic) belongs here.

## Migration Impact

- One additive Alembic revision (following the `0002_book_occurrence.py` precedent exactly):
  add `Occurrence.lemma` (nullable), add the provenance table, add `ManualCorrection` (if in
  scope — see §6). `downgrade()` reverses cleanly to the pre-SPEC-003 baseline, per the same
  pattern SPEC-002 already tested (`tests/integration/test_alembic_0002.py`).
- **Existing imported corpora can be backfilled without re-upload.** `Book` never stored the
  original uploaded text — only `content_hash`. But it doesn't need to: `Occurrence.raw_text`
  ordered by `Occurrence.position` per `book_id` is already the complete, ordered token stream
  SPEC-002 persisted. Reprocessing an existing import means: read that ordered `raw_text`
  sequence, feed it to `SpacyLinguisticAnalyzer.analyze()` as pre-tokenized input, write the
  results. No new file, no re-tokenization, no drift from `REQ-002-005`'s boundaries.
- This is also why the adapter must build a spaCy `Doc` from pre-tokenized words rather than
  calling `nlp(text)` on raw text: `nlp(text)` runs spaCy's own tokenizer, which does not
  implement §2.2's T1–T10 rules and would silently produce a different token count/boundaries
  than what SPEC-002 persisted, breaking the 1:1 mapping to `Occurrence` rows.

## Scope Boundary — Smallest Useful Vertical Slice

**In scope for SPEC-003** (produces observable, verifiable value per Art. III.2):

- `Occurrence.pos` and `Occurrence.lemma` populated by an automatic spaCy pass for a newly
  imported book (or via an explicit reprocess step for already-imported ones — same code path).
- Provenance stored per occurrence (source, model version, processed date; confidence where the
  pipeline actually exposes one).
- `LinguisticAnalyzer` port + spaCy adapter, hexagonally placed, with a fake/stub analyzer for
  unit tests so the test suite doesn't require the real model to exercise use-case logic.
- API surface: at minimum, `pos`/`lemma` become visible in a JSON response (even without a UI
  change, this is "observable" — Art. III.2 does not require a UI, and Art. III.4 says each slice
  crosses only the layers it needs).

**Explicitly DEFERRED — do NOT pull into SPEC-003** (mirrors the "Explicit non-additions" pattern
`002-text-import/spec.md` §7 already used):

- **Multiword expression detection** (roadmap item 7, ADR-0009) — a distinct capability with its
  own entity (`MultiwordExpression`, `mwe_kind`) and its own NLP adapter responsibilities. The
  orchestrator's instruction is explicit and the ADR agrees: this MUST NOT be pulled in here.
- **Proper-noun / fictional-term separate modeling** (roadmap item 6, Art. V.5) — separate
  capability.
- **Vocabulary browser UI** (roadmap item 5) — grouping occurrences into a browsable
  lemma/POS-filtered view is the next capability's job, not this one's. SPEC-003 only needs to
  make `pos`/`lemma` exist and be readable.
- **Full manual-correction UX/API** — ADR-0007 explicitly leaves the UX shape open (OQ-1:
  "day-one interactive editing vs. a deferred correction queue"). Recommend deferring the
  correction *endpoint and UI* to a follow-up spec. SPEC-003 should still lay the `ManualCorrection`
  table now (cheap, additive, avoids a second migration churn later) but does not need to build
  any code path that writes to it.
- **Language detection** (OQ-2) — `Book.language` stays unset; SPEC-003 hardcodes the English
  pipeline for the first cut, consistent with ADR-0008 ("English is the first-implemented
  language, not the exclusive scope").
- **Per-language NLP adapter selection** (OQ-4) — one language, one adapter, this slice only.

## Review-Budget Risk (400-line budget, cached `single-pr`)

**Forecast: HIGH risk. This cannot fit one 400-line PR, even at the minimal in-scope boundary
above.** Saying otherwise would not be honest given SPEC-002's own precedent: 23 requirements for
"upload, tokenize, normalize, persist, delete" already spanned many files at meaningfully more
than 400 authored lines in total. SPEC-003's *smallest* useful slice adds an entire new adapter
category (NLP, not previously present in this codebase at all), a new port, a new migration
touching two-plus tables, a new use case, and a test suite that needs both a fake-analyzer unit
path and a real-spaCy integration path (`@pytest.mark.integration`, likely `@pytest.mark.slow` or
similar given model load time) — that is comfortably over budget on its own, before manual
corrections or reprocessing are even counted.

**Recommended cut lines** for `sdd-tasks` to plan as chained/stacked PRs:

1. **PR 1 — Port + adapter + migration, no wiring.** `LinguisticAnalyzer` port, pure
   `LinguisticAnnotation` value object, `SpacyLinguisticAnalyzer` adapter (pre-tokenized input),
   spaCy dependency added, the additive migration (`lemma` column + provenance table only — no
   `ManualCorrection` yet). Unit tests against a fake analyzer + one integration test proving the
   real spaCy adapter round-trips correctly. No use case wiring into the import flow yet.
2. **PR 2 — Use case + repository write path + API surface.** `AnnotateImport` use case,
   repository methods to persist pos/lemma/provenance, DTO/schema changes to expose them, wired
   either into the import flow or a new explicit endpoint (design decides). Tests: unit
   (use case with fake analyzer/repository) + integration (real DB) + contract (schema).
3. **PR 3 — Reprocess-existing-imports path**, if in scope for this capability at all (vs.
   deferring reprocessing itself to a later spec — a legitimate option since every "newly
   imported book gets pos/lemma automatically" already satisfies Art. III.2 observable value
   without touching pre-existing rows).
4. **PR 4 (separate spec, not this change) — Manual corrections.** ADR-0007's precedence
   mechanics, the `ManualCorrection` write path, and the "reprocessing never silently overwrites"
   test suite are substantial enough to be their own vertical slice, and the UX shape is still an
   open question (OQ-1) that shouldn't block PRs 1–3.

**Decision needed before apply: Yes.** `single-pr` was cached at session start but conflicts with
this forecast. The orchestrator should either accept a chained-PR delivery strategy for this
change or explicitly record a `size:exception` before `sdd-tasks` runs — proceeding on the cached
`single-pr` assumption without addressing this will produce a `sdd-tasks` plan that violates the
400-line guard from the start.

**400-line budget risk: High.**
**Chained PRs recommended: Yes — at least 3 for this change, with manual corrections split into a
separate downstream spec entirely.**

## Ready for Proposal

**Yes, with one explicit open item to carry into the proposal**: the `single-pr` vs. chained-PR
delivery-strategy conflict above needs a decision (from the user or the orchestrator) before
`sdd-tasks` can produce a plan that satisfies the review-workload guard. Everything else —
engine choice, hexagonal placement, migration approach, provenance shape, scope boundary — has a
concrete, non-hedged recommendation above and is ready to carry into `sdd-propose`.

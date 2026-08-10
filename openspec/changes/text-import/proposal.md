# Proposal: SPEC-002 — Import a .txt and view word frequencies

> Source: issue #11. Repo `main` @ `aefbcf0`, working tree clean. Persistence mode: openspec + engram.
> Product forks in `explore.md §13` are **resolved** (see Settled Decisions); this proposal does not reopen them.

## Intent

Ship the first product-facing vertical slice: a learner uploads a legally supplied `.txt`, and the app persists it locally and shows an alphabetical list of unique **normalized word forms** with frequency counts. This is the first domain model the project will own (`domain/` today holds only `__init__.py`), so its shape must carry the full linguistic model later **without a destructive migration**.

## Settled Decisions (do not reopen)

1. **Group by NORMALIZED FORM, not lemma** (Approach A). "corro/corres/corría" are three entries. API and UI MUST say *normalized forms*, never *lemma/lexeme* (Art. V.1). Defers OQ-2/OQ-4.
2. **Persist the corpus** — minimal `Book` + `Occurrence` in SQLite. Consequence: Art. IV.8 deletion is a REAL requirement this slice.
3. **Strict UTF-8** — reject non-UTF-8 with an actionable "how to convert" error. No `charset-normalizer`, no new dependency.
4. **File upload only** (`UploadFile`); no local-path input (overview §9).
5. **Configurable size limit** with a sane default, wired through `infrastructure/settings.py`.
6. **Deletion in scope** (Art. IV.8), reversible/confirmed (Art. IX.5).
7. **Property tests phrased over normalized forms** (technical call).

## Scope

### In Scope
- Domain: pure `normalize(text: str) -> str` (stdlib only, language-generic), tokenization, frequency aggregation, alphabetical sort.
- Application: `ImportText` use case + `TextExtractor` port + `BookRepository` port + `DeleteBook` use case.
- Infrastructure: `PlainTextExtractor` (strict UTF-8), SQLAlchemy `Book`/`Occurrence` models + repository, one Alembic revision, `max_import_size_bytes` setting.
- API: thin `POST /api/v1/imports`, `GET /api/v1/imports/{id}`, `DELETE /api/v1/imports/{id}`; DTOs; error mapping (413/422); JSON Schema — mirrors `routes/health.py` + `dependencies.py`.
- Frontend: import form, frequency table (keyboard-navigable, not color-only), delete-with-confirm; `client.ts`/`types` fns mirroring `StatusPage.tsx`. Renders only what the API returns.
- Tests (RED→GREEN): domain unit + Hypothesis properties, API, persistence + migration integration, component, E2E. Docs + traceability updated.

### Out of Scope (non-goals)
- Lemmatization, `Lexeme`, POS population (`pos` reserved as `None`), MWE detection ("give up" counts as two forms — documented limitation), language detection, NLP dependency (spaCy), EPUB, async processing state machine, manual corrections.

## Capabilities

### New Capabilities
- `002-text-import`: upload a `.txt`, persist it as a corpus, and read/delete its normalized-form frequency table.

### Modified Capabilities
- None. The foundation empty-schema baseline (`REQ-PFB-CONTRACT-02`) was a point-in-time state, not a permanent invariant; adding the first user tables is expected evolution, recorded as a new `architecture-baseline.md` invariant row at archive.

## Approach

Follow the `Clock` port/adapter precedent exactly. Pure linguistic transforms live in `domain/` (Art. VII.1/VII.7). I/O boundaries (bytes→str decoding, persistence) are `infrastructure` adapters behind `application` `Protocol` ports. The route is thin (Art. VII.4); DI is wired in `api/dependencies.py`. The frontend duplicates no linguistic rules (Art. VII.5).

## Schema extensibility — HOW each future concern attaches additively

The persisted shape is `Book(id, language?, content_hash, import_status, created_at)` + `Occurrence(id, book_id, raw_text, normalized_text, position, pos?)`. It stays open because **future work is added as new nullable columns or new sibling tables, never by rewriting or un-merging existing rows**:

| Future concern (ADR/Art.) | How the shape stays open — additive, non-destructive |
|---|---|
| Per-occurrence `pos` (ADR-0006, Art. V.2–3) | `Occurrence.pos` exists now, nullable, `None` this slice. Later = populate the column. POS is **never** a global field on `Book`/lemma, so no restructuring. |
| `lemma` beside normalized + textual form (Art. V.1) | `raw_text` (textual) and `normalized_text` (normalized) are **distinct columns** now. A future `Lexeme` table + nullable `Occurrence.lemma_id` FK adds lemma grouping without altering existing columns. The three forms never collapse. |
| MWE separate from single-word lemmas (ADR-0009) | Nothing here names or stores MWEs, and single-word forms are **never** flagged `is_mwe`. A future `MultiwordExpression` table with `mwe_kind` is a new sibling keyed to spans — no un-merge migration needed. |
| Manual corrections + provenance/confidence (ADR-0007, Art. V.7–9) | Automatic-provenance fields (source/version/date/confidence) are reserved nullable on the persisted record. A future `ManualCorrection(occurrence, field)` table is additive; reprocessing checks it. Storing provenance now lets reprocessing distinguish auto vs. manual later without a rewrite. |
| Multiple languages (ADR-0008) | `Book.language` is nullable now (single assumed language, no detection — OQ-2 deferred). No language-named entity types exist, so a new language = new NLP adapter + `mwe_kind` value, not a migration. |

Residual risk: committing `Book`/`Occurrence` before lemma/POS/MWE land may need one **additive** migration later. Bounded, not destructive: Art. VI.4 tolerates versioned migrations, and the ADRs already fix *where* each future field attaches.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `apps/api/src/wheel_vocabulary/domain/` | New | tokenize, `normalize()`, aggregate, sort (pure, stdlib only) |
| `.../application/` | New | `ImportText`, `DeleteBook`, `TextExtractor` + `BookRepository` ports |
| `.../infrastructure/` | New/Modified | `PlainTextExtractor`, `Book`/`Occurrence` models + repository, `settings.py` size field |
| `.../infrastructure/persistence/` + `apps/api/migrations/` | New | first non-empty Alembic revision (Book/Occurrence, content hash) |
| `.../api/routes,dtos,dependencies,schemas` | New | import/read/delete routes, DTOs, error mapping, versioned JSON Schema |
| `apps/web/src/{pages,components,api,types}` | New | import form, frequency table, delete action |
| `docs/{traceability-matrix,glossary,architecture/overview,architecture/architecture-baseline}.md` | Modified | move `Book`/`Occurrence` to committed; glossary "forma normalizada" grouping; new invariant row |

## Requirements (feed to sdd-spec)

`REQ-002-001` upload-only `.txt` via `UploadFile` · `-002` validate extension/content-type before processing (format error) · `-003` configurable `max_import_size_bytes` default, reject oversized (413) · `-004` strict UTF-8 decode, actionable reject on non-UTF-8, no new dep · `-005` pure language-generic `normalize()` in domain · `-006` aggregate by normalized form, alphabetical + frequency · `-007` API/UI label as normalized forms, never lemma/lexeme · `-008` persist `Book` + `Occurrence` via repository + Alembic revision · `-009` store cryptographic `content_hash` on `Book` (Art. VI.3) · `-010` reserve per-occurrence `pos` = `None`, never global POS (ADR-0006) · `-011` delete imported text + derived data, confirmed/reversible (Art. IV.8/IX.5) · `-012` empty file → "0 unique words", not an error · `-013` logs never contain raw imported text (Art. X.2) · `-014` frontend duplicates no linguistic rules (Art. VII.5) · `-015` `normalize(normalize(x))==normalize(x)` property · `-016` unique-form set independent of token order (property; normalized-form analogue of the AGENTS §6 lemma invariant, to re-verify against real lemmas later) · `-017` frequencies never negative (property).

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Slice exceeds 400-line review budget | High | Chained/stacked PRs (see Sizing); `sdd-tasks` produces the guard forecast |
| Second additive migration once lemma/POS/MWE land | Med | Additive-only; Art. VI.4 tolerates it; ADRs fix attachment points |
| A field/label leaks "lemma" naming | Med | `REQ-002-007` explicit; review/lint the response keys and UI copy |
| Art. X.1 "explicit states" vs. Art. III minimal slice | Low | Persist minimal terminal `import_status` (succeeded/failed) only; defer full pending/running/cancelled machine to a later async cycle |
| Copyrighted text in fixtures/examples | Low | Synthetic or public-domain only; never resemble the disclaimed series name |

## Rollback Plan

Additive-only. Revert the feature branch/PRs; `alembic downgrade -1` drops `Book`/`Occurrence` back to the empty-schema baseline. No prior data to restore (foundation shipped zero user tables). Frontend routes/components removed with the revert; health flow untouched.

## Dependencies

- None new. Stdlib (`unicodedata`, `re`, `hashlib`) + existing FastAPI/SQLAlchemy/Alembic/pydantic-settings. Zero-warning `filterwarnings` gate and strict TDD (`cd apps/api && uv run pytest`) stay intact.

## Success Criteria

- [ ] Uploading a synthetic `.txt` returns an alphabetical unique-normalized-form + frequency list; empty file → "0 unique words".
- [ ] Non-UTF-8 and oversized uploads are rejected with clear, actionable, distinct format/size errors; logs carry no raw text.
- [ ] An imported text and its derived data can be deleted (Art. IV.8), with confirmation.
- [ ] `Book`/`Occurrence` persist; migration verified; `content_hash` stored; `pos` reserved `None`.
- [ ] Property tests (idempotence, order-independence, non-negative frequency) pass; suite stays 0-warning.
- [ ] No field/response key/UI string names form-grouping "lemma"; frontend duplicates no linguistic rules.

## Sizing & Chained-Slice Flag

Estimated **~900–1400 authored changed lines** across five layers + tests + docs. **400-line budget risk: High.** Chained PRs required.

### Chain shape — DECIDED (supersedes the layer-by-layer sketch)

A layer-by-layer chain (domain → POST → persistence → deletion → frontend) was rejected: it puts four backend PRs ahead of any integrated value, which Art. III.3 forbids ("Se evitarán fases horizontales largas sin valor integrado", `docs/constitution.md:42`).

The slice therefore ships as **three vertical cuts, each crossing every layer and each producing observable output** (Art. III.1–III.2):

| Cut | User-visible outcome | Requirements |
|---|---|---|
| 1 — walking skeleton | Upload a `.txt` and see the alphabetical normalized-form frequency table | `REQ-002-001`, `-005`, `-006`, `-007`, `-008`, `-010`, `-012`, `-014`, `-015`, `-016`, `-017` |
| 2 — hardening | Oversized, wrong-type, and non-UTF-8 uploads fail with distinct actionable errors; content hash stored | `REQ-002-002`, `-003`, `-004`, `-009`, `-013` |
| 3 — deletion | Delete an imported text and its derived data, with confirmation | `REQ-002-011` |

**Chain strategy: `stacked-to-main`.** Each cut merges to `main` in order, so the feature is usable after cut 1. A feature-branch-chain would withhold every cut from `main` until the end, reproducing the horizontal-phase problem this shape exists to avoid.

**Review budget: `size:exception` accepted by the maintainer** for each cut (estimated 400–700 lines each). The trade is deliberate: the project cannot simultaneously satisfy ≤400-line PRs, integrated value per PR, and this scope. Art. III.3 wins over the line budget, and the exception is recorded here rather than discovered at PR time.

`sdd-tasks` owns the authoritative per-cut forecast and guard lines within this shape.

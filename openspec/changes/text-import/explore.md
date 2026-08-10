# Exploration: SPEC-002 — import a .txt and view word frequencies

## 1. Metadata

| Field | Value |
|-------|-------|
| Change slug | `text-import` |
| Source issue | [#11](https://github.com/juanjoseexpositogonzalez/wheel-of-words/issues/11) — "SPEC-002: import a .txt and view word frequencies" |
| Repo state | `main` @ `aefbcf0`, working tree clean |
| Governing constitution | v2.0.0 (2026-07-15, multi-language amendment 2026-07-16) |
| Relevant ADRs | 0002 (hexagonal split), 0005 (local-first), 0006 (POS per occurrence), 0007 (manual corrections precedence), 0008 (multi-language scope), 0009 (MWE as language-specific instances) |
| Prior cycle | `project-foundation-bootstrap` (archived `2026-08-03`) — first code-touching cycle, ships an empty domain/application skeleton, a health endpoint, and persistence scaffolding with zero user tables |
| Persistence mode | `both` (OpenSpec + Engram, topic `sdd/text-import/explore`) |
| Phase | Exploration only. No code, tests, specs, or tasks are produced here. |

## 2. Current state

### 2.1 What is shipped

The foundation cycle delivered infrastructure, not product behavior:

- Backend: FastAPI 0.139.2 app, `GET /api/v1/health` only. `apps/api/src/wheel_vocabulary/domain/` contains a single empty `__init__.py` — **zero domain entities exist**. `application/` has one port: `Clock` (`application/clock.py`, a `Protocol`). `infrastructure/` has the `SystemClock` adapter, `Settings` (pydantic-settings), SQLAlchemy `Base`/engine helpers (`infrastructure/persistence/`), and version resolution. `api/` has `dependencies.py` (DI factories), `dtos/health.py`, `routes/health.py`, and a versioned JSON Schema (`schemas/health.v1.json`).
- Alembic has exactly one migration: an empty-schema baseline. No user tables exist in the database yet (`REQ-PFB-CONTRACT-02`).
- Frontend: React 19 + Vite, a single status page (`pages/StatusPage.tsx`) polling `/health` via a bare `fetch` wrapper (`api/client.ts`), no TanStack Query installed yet despite being named in `docs/architecture/overview.md §5` as a planned dependency.
- `apps/api/pyproject.toml` dependencies: `fastapi`, `uvicorn`, `pydantic-settings`, `sqlalchemy`, `alembic`, `jsonschema`. **No NLP library (spaCy or otherwise) is installed.** This is a material fact for the domain-model question below, not just a NDD footnote.
- Tests: 50 passed, `filterwarnings` hard-errors on `ResourceWarning` and two named deprecation classes — zero-warning discipline is already load-bearing.

### 2.2 What is documented but not built

`docs/architecture/overview.md §4` names domain entities that do not exist in code yet: `Book`, `Chapter`, `ProcessingRun`, `Lexeme`, `WordForm`, `Occurrence`, `PartOfSpeech`, `MultiwordExpression`, `LearningStatus`, `ManualCorrection`, `ExportSelection`. These are **aspirational**, not committed — `architecture-baseline.md` explicitly separates "committed invariants" (the ADR list) from "the overview" (forward-looking). SPEC-002 is the first cycle that gets to decide which of these entities, if any, are real yet.

`docs/product-vision.md §12` (roadmap) sequences the work as: (1) foundation — done, (2) **import TXT**, (3) tokenization and normalization, (4) lemmatization and POS, (5) vocabulary browser, (6) proper nouns, (7) language-specific MWEs, (8) learning status, (9) Anki export, (10) EPUB and performance. This ordering is itself evidence about intended slice size: the roadmap's own authors did not expect lemmatization to ship in the same step as import.

### 2.3 The five binding constraints from Art. V / ADR-0006 / ADR-0008 / ADR-0009

1. Textual form, normalized form, lemma, and per-occurrence contextual POS are four distinct concepts (Art. V.1) — none may collapse into another, even informally in naming.
2. POS lives on `Occurrence`, never as a single field on a lemma-like entity (Art. V.2–3, ADR-0006).
3. Multiword expressions are modeled as a separate entity family from single-word lemmas, keyed by a language-specific `mwe_kind` (Art. V.6, ADR-0009).
4. Manual corrections outrank automatic results and must survive reprocessing, with provenance and confidence recorded for automatic results (Art. V.7–9, ADR-0007).
5. The architecture is multi-language from day one at the schema level, even though English ships first; OQ-2 (language detection) and OQ-4 (per-language NLP library selection) are explicitly deferred by ADR-0008 to "future ADRs when multi-language vertical slices are implemented" — they are not blocking by default.

## 3. Affected areas (if this cycle proceeds)

- `apps/api/src/wheel_vocabulary/domain/` — currently empty; first domain code lands here.
- `apps/api/src/wheel_vocabulary/application/` — new use case(s) alongside the existing `Clock` port.
- `apps/api/src/wheel_vocabulary/infrastructure/` — new adapter(s) for text extraction/encoding and, if persistence is chosen, a repository following the `infrastructure/persistence/` pattern already established (`base.py`, `engine.py`).
- `apps/api/src/wheel_vocabulary/api/routes/`, `api/dtos/`, `api/dependencies.py` — new import route, following the thin-route + `Depends()` pattern in `routes/health.py`.
- `apps/api/migrations/` — a new Alembic revision only if persistence is chosen; otherwise the baseline stays empty-schema.
- `apps/web/src/pages/`, `apps/web/src/components/`, `apps/web/src/api/client.ts`, `apps/web/src/types/` — new import page/form and a frequency table, following the `StatusPage.tsx` / `client.ts` pattern.
- `docs/architecture/overview.md §4/§8` — will need to move some entities from "previsto" to "committed" once this cycle lands; `architecture-baseline.md` gets a new invariant row if a domain/architecture decision is made (e.g., "unique words this slice are grouped by normalized form, not lemma").
- `docs/glossary.md` — if a new domain concept is introduced without an exact existing glossary term (see §4.1), the glossary needs an entry before code names it, per the glossary's own contribution rule ("actualizar primero el ADR o artículo... y luego reflejar el cambio aquí").

## 4. The central tension, resolved into a concrete recommendation

The issue's plain-language ask — "unique words with frequency" — has two honest readings, and picking the wrong one either violates the constitution or blows the slice budget:

- **Reading A**: unique words = unique **normalized forms** (case-folded, punctuation-stripped strings). No merging of "run"/"running". This requires no NLP model, only pure string transformations.
- **Reading B**: unique words = unique **lemmas** (dictionary headwords). "run"/"running"/"ran" collapse into one row. This requires a lemmatizer, which requires an NLP adapter, which is currently not a dependency of `apps/api`.

### 4.1 Why Reading A does not violate Art. V

Art. V.1 requires that textual form, normalized form, and lemma stay **distinguishable** — it does not require that lemma be computed in every slice. Grouping by normalized form is not a violation as long as:

1. The domain never *calls* the grouping "lemma" or introduces a `Lexeme` entity that isn't actually a lemma (that would be lying to the model, not simplifying it).
2. The `Occurrence`-shaped record (if introduced) leaves room for a `pos` field to arrive later as `None`/absent rather than requiring a schema rewrite (ADR-0006 already anticipates POS as a per-occurrence field, so the shape is known in advance even if unpopulated).
3. No MWE detection is attempted this slice, and this is stated as a known, intentional limitation (phrasal verbs like "give up" will count as two independent normalized-form entries this slice — accurate to what the slice does, not what the product eventually does).

This reading also has a bonus consequence for Q6 below: it does **not** force resolution of OQ-2 or OQ-4.

### 4.2 Why Reading B is the over-build the user warned about

Reading B pulls in an NLP library (spaCy is the ADR-0001 default) as a new dependency, forces immediate resolution of OQ-4 (which model, for which language), likely brushes against OQ-2 (a lemmatizer needs to know the language to load the right model), and jumps two roadmap steps (3: tokenization/normalization, 4: lemmatization/POS) into a slice that the roadmap itself scoped as step 2. It is the textbook Art. III violation: a horizontal phase (install and wire an NLP pipeline) disguised as a vertical slice.

**This document does not pick Reading A as final** — that is a product-facing wording decision (see Open Product Question #2) — but every layer/persistence/contract analysis below assumes Reading A as the technically sound default for slice sizing, and flags exactly where Reading B would change the answer.

## 5. Domain model — minimum viable, without foreclosing the future (Q1)

### Two approaches

| | **Approach A — Normalized-form slice** | **Approach B — Lemma-now slice** |
|---|---|---|
| New domain concepts | `Token` (raw unit from tokenization), `Occurrence` (position + raw form + normalized form, `pos: PartOfSpeech \| None` reserved for later), a pure `normalize(text: str) -> str` function | All of Approach A **plus** `Lexeme`, `PartOfSpeech` populated, an NLP adapter port (`LinguisticAnalyzer`) |
| New dependency | None (stdlib only: `str.casefold`, `unicodedata`, `re`) | spaCy or equivalent + a downloaded language model |
| Forces OQ-4 now? | No | Yes |
| Forces OQ-2 now? | No (single assumed language per import, no auto-detection needed) | Likely (model selection needs a language) |
| Matches roadmap sequencing (`product-vision.md §12`) | Yes — stays inside step 2 | No — pulls in step 4 |
| MWE handling | Explicitly out of scope, phrasal verbs split into component words (documented limitation) | Same limitation unless MWE detection is also added (ADR-0009 scope), which would be a third roadmap step folded in |
| Effort | Low | Medium–High |
| Risk to the 400-line review budget (Section E) | Low | Medium–High (model wiring, config, larger test surface) |

**Recommendation**: Approach A. It is the smaller, constitutionally clean slice, and it does not close any door — a later cycle adds a `Lexeme` entity and a `lemma_id` foreign key (or equivalent) on `Occurrence` without touching the normalization or tokenization code written now. Approach B is not "wrong," but it is a different, bigger cycle that should be proposed as such, explicitly, rather than smuggled into "import a .txt."

### Minimum entity shape (illustrative, not a design commitment)

```
Token            — raw lexical unit from tokenization, pre-normalization (per glossary "Token")
WordForm-ish attrs on Occurrence:
  Occurrence.raw_text        — forma textual (Art. V.1)
  Occurrence.normalized_text — forma normalizada (Art. V.1)
  Occurrence.position        — index/offset in the source
  Occurrence.pos             — reserved, None this slice (ADR-0006 shape, not yet populated)
```

Whether `Occurrence` is a persisted SQLAlchemy entity or an in-memory dataclass depends entirely on the persistence question in §6 — the *shape* is the same either way, which is exactly the point: the shape decision and the persistence decision are separable, and only one of them needs to happen now.

## 6. Persistence: stateless import-and-display, or persisted corpus? (Q2)

### Two approaches

**Approach P1 — Stateless (upload → compute → return → discard)**
- The API endpoint accepts a file, extracts text, tokenizes, normalizes, aggregates, and returns the frequency list in the HTTP response body. Nothing is written to SQLite. The Alembic baseline stays empty-schema.
- Pros: smallest possible slice; no migration; no cascade/delete design; no "processing state" machine needed since the whole thing is one synchronous request/response.
- Cons: forecloses, or at least defers expensively, several roadmap items that assume a persisted corpus — reprocessing (ADR-0007 has nothing to reprocess), manual corrections (nothing to correct), "known/ignored" learning status (roadmap item 8), and `product-vision.md §5` bullet 1, "Importar una obra" as a *durable* action, not a one-shot view. It also does not exercise Constitution Art. IV.8 ("permitirá eliminar los datos importados") — trivially satisfied by having nothing to delete, but that is a footnote, not a feature.

**Approach P2 — Minimal persistence (a `Book`/corpus row + `Occurrence` rows)**
- The import endpoint persists a `Book` (or similarly-named) record and one row per occurrence (or, at minimum, per normalized form with a count — see note below), following the existing `infrastructure/persistence/` pattern (`Base`, `engine.py`). A separate read endpoint lists the frequency table for a given book ID.
- Pros: matches `docs/architecture/overview.md §4`'s already-named `Book`/`ProcessingRun` entities; gives the next cycle (corrections, learning status) something to attach to instead of re-plumbing storage and the frequency feature at the same time; makes Art. IV.8 (deletion) a real, testable requirement instead of a non-issue.
- Cons: bigger slice — schema design, a migration, delete semantics, and (per `overview.md §7`) the temptation to model explicit processing states (`pending/running/succeeded/failed/cancelled`) even though a small `.txt` file is likely synchronous. Committing to a persisted `Occurrence` shape before POS/lemma/MWE land risks a second migration soon after, though the constitution explicitly tolerates this (Art. VI.4: "Las migraciones están versionadas") — it is a cost, not a violation.

### What each choice costs later

- Choosing P1 now means the *next* cycle that wants persistence has to build storage **and** retrofit the frequency feature to read from it in the same slice — a strictly bigger, riskier slice than doing a small persistence step now.
- Choosing P2 now means committing a schema shape earlier than the linguistic model is fully known, with a small but real chance of a second migration once lemma/POS/MWE/corrections land. This is bounded risk, not unbounded risk, because ADR-0006/0007/0009 already specify *where* those future fields will attach (`Occurrence`, not `Lexeme`/`WordForm`).

**This is a genuine product/business fork, not a technical one** — see Open Product Question #1. This document does not resolve it silently.

## 7. Where normalization belongs, and its invariants (Q3)

### Placement

Per ADR-0002 and Constitution Art. VII.7 ("Se favorecerán funciones puras para transformaciones"), normalization is a pure `str -> str` function with no I/O and no third-party dependency (`str.casefold()`, `unicodedata.normalize("NFC", ...)`, and a punctuation-stripping regex are sufficient and stdlib-only). That places it squarely in **`domain`**, alongside tokenization (splitting raw text into tokens) and frequency aggregation (counting normalized forms). None of these need FastAPI, SQLAlchemy, or an NLP library.

Encoding detection/decoding (raw uploaded `bytes` → `str`) is a different concern — it is about interpreting an I/O boundary (an uploaded file), not a linguistic transformation over already-decoded text. That belongs in **`infrastructure`**, as a `TextExtractor`-shaped adapter (already named in `overview.md §8`), mirroring the existing `Clock` port/adapter split (`application/clock.py` protocol, `infrastructure/clock.py` implementation).

### Avoiding hidden English-only assumptions

Per the precedent set by `REQ-PFB-LANG-01` in the foundation cycle (no English-only hardcoding, even in an empty skeleton), the normalization function should be written as `normalize(text: str) -> str`, not `normalize_english(text: str)`, using Unicode-general operations. This does not require solving OQ-2 — it just means not writing a function whose name or default arguments assume English, exactly as the prior cycle already enforced for the empty skeleton.

### Invariants (property-based, per `AGENTS.md §6`)

AGENTS.md names two invariants verbatim:

> "Normalizar dos veces equivale a normalizar una vez."
> "El orden de entrada no altera el conjunto de lemas."

The first maps directly: `normalize(normalize(x)) == normalize(x)` — idempotence, testable today with Hypothesis, no caveats.

The second is worded around **lemma**, which does not exist in Approach A's scope this slice (see §5). Two honest options, not a silent substitution:

1. Test the analogous claim over what *does* exist this slice — "the set of unique normalized forms is independent of input token order" — and note explicitly in the spec/tests that this is the normalized-form analogue of the AGENTS.md lemma invariant, to be re-verified against the real lemma set once lemmatization ships.
2. Treat the AGENTS.md wording as forward-looking and defer writing this specific property test until lemma exists, testing only order-independence at the token/normalization level for now.

Flagging this discrepancy explicitly rather than quietly reinterpreting "lemma" as "normalized form" in the test suite (see Open Product/Spec Question #7 — this is really a spec-phase wording decision once Reading A vs B is settled).

Two more invariants apply cleanly regardless of A/B: frequencies are never negative (trivial from counting, but worth a named property test since AGENTS.md calls it out explicitly), and — only if Approach P2 (persistence) is chosen — manual corrections surviving reprocessing is **not exercised this slice** (no `ManualCorrection` entity ships here; noted as an explicit non-goal, not silently skipped).

## 8. File input contract (Q4)

### Upload vs. local path

`docs/product-vision.md` frames this as a **web application** ("aplicación web"), and the issue says "select or provide a .txt file" — browser-side file selection. `docs/architecture/overview.md §9` already lists file-handling security requirements (extension/content validation, configurable size limits, distrust of filenames, no execution of imported content, sanitized logs) that presuppose an **upload** model, not a raw filesystem path typed into a form. A local-path input would also silently assume the browser and the backend share a filesystem, which breaks the moment the backend runs anywhere other than literally the same machine session — a fragile assumption for a web app even a local-first one.

**Recommendation**: multipart HTTP upload (`UploadFile` in FastAPI), matching the existing `POST`-free, thin-route pattern in `routes/health.py`. This stays fully local-first per ADR-0005 — the file goes to the user's own backend process, not to any third party.

### Open, unresolved contract details

- **Size limit**: not specified anywhere in the docs today. Needs an explicit number (e.g., a configurable `max_import_size_bytes` in `Settings`, mirroring the existing `Settings` pattern) — this is Open Product Question #4.
- **Encoding**: real-world `.txt` files are not reliably UTF-8 (Windows-1252/Latin-1 exports are common). Two approaches:
  - **Strict UTF-8 only**: reject anything else with a clear, user-facing "encoding not recognized" error (Art. X.3: distinguish format errors from processing/internal errors). Zero new dependency, but rejects legitimate files.
  - **Best-effort detection** via a small library such as `charset-normalizer` (permissive MIT license, pure Python, no compiled extension) with a confidence threshold, falling back to the same rejection message when confidence is too low. Better UX, one small added dependency, more test surface (confidence edge cases).
  This is Open Product Question #5 — not decided here.
- **Malformed input**: empty file (valid, should render "0 unique words," not an error), non-UTF-8/undecodable bytes (format error), wrong extension or content-type mismatch (reject before processing), oversized file (reject with the configured limit surfaced to the user). Each of these needs its own acceptance criterion in the spec phase — none are decided here beyond naming the categories, per Art. X.3.

## 9. Layer placement (Q5)

Following the `Clock` port/adapter precedent exactly:

| Layer | New responsibility | Depends on |
|---|---|---|
| `domain/` | Tokenization, `normalize()`, frequency aggregation, alphabetical sort of results — all pure functions/value objects over `str`/`Occurrence`. Zero third-party imports. | stdlib only |
| `application/` | An `ImportText` (naming TBD) use case: takes raw bytes + filename, calls a `TextExtractor` port for bytes→str, calls domain functions, optionally calls a repository port (if P2), returns a result DTO. Also the `TextExtractor` **port** definition (a `Protocol`, like `Clock`). | `domain`, ports only |
| `infrastructure/` | `PlainTextExtractor` adapter (implements `TextExtractor`): decodes bytes, applies the chosen encoding policy from §8. If P2: a repository adapter under `infrastructure/persistence/`, following `base.py`/`engine.py` conventions, plus a new Alembic revision. | `application` ports, SQLAlchemy, optionally `charset-normalizer` |
| `api/` | A thin `POST /api/v1/imports` (naming TBD) route using `UploadFile`, a response DTO (Pydantic), and error mapping (413 too-large, 422 malformed/wrong-encoding) — no business logic in the route body, matching `routes/health.py`. Wired via `dependencies.py`. | `application` |
| Frontend | An import page/form (mirrors `StatusPage.tsx`), a `fetch`-based client function (mirrors `client.ts`), and a results table component with the same three-state (loading/success/error) contract already established for the health screen, keyboard-navigable, not color-only (Art. IX.3–4). No linguistic logic client-side — it renders exactly what the API returns (Art. VII.5, `overview.md §5`: "No contiene reglas lingüísticas"). | `api` contract only |

## 10. Does this slice force OQ-2 or OQ-4? (Q6)

With Approach A (§5) and the encoding policy of §8, **no**. Neither language auto-detection (OQ-2) nor NLP-library-per-language selection (OQ-4) is invoked: normalization is a generic Unicode operation, not a per-language ruleset, and no lemmatizer is loaded. This matches ADR-0008's own framing — those two open questions are deferred "to future ADRs when multi-language vertical slices are implemented," and this slice is explicitly not that.

With Approach B, OQ-4 is forced immediately (you cannot wire spaCy without picking a model), and OQ-2 is at minimum brushed against (a lemmatizer needs to know which language model to load, even if the product currently only *ships* English).

## 11. Legal/copyright risk flags (Constitution Art. IV — non-negotiable)

- Any test fixture `.txt` used for tokenization/normalization/frequency tests **must** be synthetic (hand-written for the test) or genuinely public domain (e.g., an explicitly public-domain Project Gutenberg text, cited as such). Given the project's own working name references a copyrighted book series ("Wheel of Time," explicitly disclaimed in `product-vision.md §1`), extra care is warranted: no fixture should resemble or quote that series' text, even for a "just testing tokenization" excuse.
- If a demo/example import file ships anywhere in the repo (README, seed data, Storybook-equivalent), it must be public domain and should say so in a comment or accompanying note.
- If P2 (persistence) is chosen, Art. IV.8 ("la aplicación permitirá eliminar los datos importados") becomes a real, testable requirement, not a footnote — the spec phase should decide whether deletion ships in this cycle or is an explicit, tracked non-goal with a follow-up issue.
- Error logs and any future observability must not leak raw imported text content (Art. X.2: "sin contenido sensible") — worth a spec-level requirement if P2 is chosen and processing errors get logged with context.
- If `charset-normalizer` (or similar) is added as a dependency, confirm its license (MIT) is compatible with the project's license posture before use — low risk, but a five-minute check worth doing explicitly rather than assuming.

## 12. Ready for Proposal

**Partially** — the codebase investigation and constraint analysis are complete, but this exploration surfaces genuine product/business forks that the proposal phase cannot resolve on its own. The orchestrator should get explicit answers to the open questions in §13 from the user before `sdd-propose` runs, or the proposal phase will end up making silent product decisions that Constitution Art. I.4 says must not happen ("las ambigüedades deben resolverse en la especificación, no ocultarse en el código" — and not in an unstated proposal assumption either).

## 13. Open product questions for the user (must be answered before proposal)

1. **Persistence scope** (§6): does this slice persist the imported book/corpus (enabling later revisit, corrections, deletion), or is a stateless "upload → view once → discard" acceptable, with persistence deferred to a later cycle? This single answer resizes the whole slice.
2. **What "unique word" means to the user** (§4): case/punctuation-normalized word forms only (no merging of inflected forms — "run" and "running" stay separate rows), or does the user expect them merged as they would be in a dictionary (which requires lemmatization now, pulling in an NLP dependency and OQ-4 immediately)? This is the actual product ask behind the issue title and should not be assumed by the proposal phase.
3. **Input contract**: is browser file upload the only supported path, or does the user also want a local-filesystem-path input for this slice (e.g., a CLI-adjacent workflow)? The recommendation above assumes upload-only.
4. **Maximum file size**: what is the accepted upper bound for an imported `.txt` file this slice? No number exists anywhere in the docs today.
5. **Encoding policy**: strict UTF-8 only (simpler, may reject legitimate real-world files), or best-effort encoding detection with a fallback error (better UX, one small added dependency)?
6. **Deletion** (if persistence is chosen): does this slice need to satisfy Art. IV.8 (delete imported data) now, or is that an explicit, tracked non-goal for a follow-up cycle?
7. **Property-test wording** (§7): should the spec phase test "order-independence of the unique normalized-form set" as a stand-in for the AGENTS.md-named "lemma set" invariant this slice, with an explicit note that it will be re-verified against real lemmas once lemmatization ships? Or should that specific property test be deferred entirely until lemma exists?

## Key Learnings

1. The backend has zero domain entities and zero NLP dependencies today, which makes lemma-based "unique words" a materially larger slice than normalized-form-based "unique words," not just a naming choice.
2. ADR-0006 already reserves a per-occurrence `pos` field shape, so a slice that leaves `pos` unpopulated (`None`) does not violate Art. V as long as it never mislabels normalized-form grouping as lemma grouping.
3. Choosing normalized-form grouping over lemma grouping this slice also defers OQ-2 (language detection) and OQ-4 (per-language NLP library) cleanly, matching ADR-0008's own deferral framing.
4. The persistence question (stateless vs. a minimal `Book`/`Occurrence` schema) is a genuine product fork with asymmetric later costs, not a technical detail — P1 now means a bigger retrofit slice later, P2 now means committing schema before the linguistic model is fully known.
5. `docs/architecture/overview.md §9` already specifies file-upload security requirements (size limits, content validation, filename distrust), which is strong existing evidence that upload (not local-path input) is the intended contract for this feature.

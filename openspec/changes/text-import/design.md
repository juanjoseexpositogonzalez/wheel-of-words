# Design — text-import (SPEC-002 / capability `002-text-import`)

> Answers `openspec/changes/text-import/specs/002-text-import/spec.md` (18 REQ / 24 AC / 44 scenarios).
> Repo `main` @ `aefbcf0`. Persistence mode: `openspec` + `engram` (`sdd/text-import/design`).
> Language: English (methodology artifact, ADR-0010). Product docs and UI copy stay Spanish.
> **Size note:** the generic 800-word design budget is deliberately exceeded. The orchestrator brief
> requires schema, port signatures, an error taxonomy, quantified scale arithmetic, and a cut verdict
> in this artifact. Tables carry the density.

**Amendment 1 (maintainer review).** Both blockers are **closed**.

- **CONTRA-1 withdrawn — my reading of Art. IX.6 was wrong.** `docs/constitution.md:101` reads
  "Las operaciones largas mostrarán progreso **o** estado" — a **disjunction**, structurally identical
  to Art. IX.5 (`docs/constitution.md:100`, "pedirán confirmación **o** serán reversibles"), which the
  spec phase already read correctly as a disjunction and which `REQ-002-011` relies on. A perceptible
  "importando…" state in the UI discharges Art. IX.6 on the *estado* branch. No progress bar, no async
  state machine, no intermediate `import_status` is required. The terminal `succeeded|failed` of
  `REQ-002-013` stands exactly as specified. I applied the disjunction correctly to Art. IX.5 and then
  failed to apply it to Art. IX.6 one article later.
- **Size limit is now 4 MiB (`4194304`).** The spec is being amended in parallel to pin the literal.
  §3 is recomputed against it.
- **CONTRA-5 accepted.** Cut 1 splits. `T-GUARD` is **dropped**: `REQ-002-003` moves into the first cut
  as a real configurable setting rather than a hard-coded stopgap on a path merging to `main`. §12 is
  rewritten, and the same principle is extended to `REQ-002-002` and `REQ-002-004` (§12.1).
- **CONTRA-2, CONTRA-3, CONTRA-4 stand as resolved.** Document-level NFC remains forbidden, only `pos`
  ships reserved, and the forbidden-pattern grep is scoped for `AC-002-19`.
- §3.4 response-body figure **corrected**; the original was overstated ~2.6×. Derivation now shown.

---

## 1. Technical approach in one paragraph

The import is a **single synchronous request** that streams the upload under a byte cap, hashes it,
decodes it strictly, and hands a `str` to four pure `domain` functions (tokenize → normalize →
aggregate → sort). Persistence writes one `Occurrence` row per token through a `BookRepository` port.
**The read path never re-implements a linguistic rule**: the repository returns raw
`(raw_text, normalized_text, count)` triples — mechanical counting only — and the *same*
`domain.frequency.build_table()` that the import path uses applies D1/D2/D3 and the §2.4 sort key.
One implementation of the rule, two data sources. That single choice is what makes `AC-002-21`
(order independence over keys, frequencies **and** display forms) a pure unit test with no database,
and it is what keeps `infrastructure` free of linguistic logic under ADR-0002 / Art. VII.

---

## 2. Layer map (ADR-0002, Art. VII.1–VII.5)

| Layer | Modules | Imports allowed |
|---|---|---|
| `domain/` | `text/tokenizer.py`, `text/normalizer.py`, `frequency.py`, `models.py` | stdlib only (`unicodedata`, `re`, `dataclasses`, `collections`) |
| `application/` | `imports/use_cases.py`, `imports/ports.py`, `imports/errors.py` | `domain`, `typing.Protocol` |
| `infrastructure/` | `text_extraction.py`, `persistence/models.py`, `persistence/book_repository.py`, `settings.py` | SQLAlchemy, pydantic-settings |
| `api/` | `routes/imports.py`, `dtos/imports.py`, `errors.py`, `dependencies.py`, `schemas/import.v1.json` | FastAPI, Pydantic, `application` |
| `apps/web/src/` | `pages/ImportPage.tsx`, `components/{ImportForm,FrequencyTable,DeleteImportButton}.tsx`, `api/imports.ts`, `types/imports.ts` | API contract only |

`domain/` and `application/` are already `strict = true` in mypy (`apps/api/pyproject.toml`). No
change. `AC-002-06` / hook H2 is satisfied structurally, not by convention.

---

## 3. The scale question — per-occurrence rows at 4 MiB (quantified)

`REQ-002-008` mandates one `Occurrence` row per emitted token and `REQ-002-010` reserves per-occurrence
`pos`. Recomputed against the amended limit of **4,194,304 bytes**. Numbers are engineering estimates
from record layout and known SQLite/CPython throughput classes; **`T-BENCH` in tasks must confirm them
against a generated synthetic corpus before the persistence cut merges.**

**Two different populations are counted below and must not be mixed.** §3.1–§3.3 count **tokens**
(occurrences) — they drive rows, storage and insert cost. §3.4 counts **types** (distinct normalized
forms) — they drive the response body and read cost. Token count grows linearly with bytes; type count
grows **sublinearly**, per Heaps' law. Conflating them is exactly how the previous response-body figure
went wrong (§3.4.4).

### 3.1 Token yield (occurrences)

| Input | bytes/token (UTF-8, incl. one separator) | tokens at 4 MiB |
|---|---|---|
| English prose | ~6.1 | **~688 k** |
| Spanish prose | ~6.4 | ~655 k |
| German prose | ~7.3 | ~575 k |
| Adversarial `"a "` ×N | 2.0 | **~2.10 M** |

A byte cap bounds token count only loosely: the adversarial case is **3× the English yield** at the
same file size. Residual risk, quantified in §3.3.

### 3.2 Storage footprint (SQLite record layout)

Per `occurrence` row: record header ≈ 6 B (1 + 5 varints) + `book_id` ≈ 2 B + `position` ≈ 3 B +
`pos` NULL = 0 B payload + `raw_text` ≈ 5 B + `normalized_text` ≈ 5 B → payload ≈ 15 B, cell ≈ 21 B,
plus 2 B cell pointer and ~30 % page slack → **≈ 36 B/row** in the table b-tree.
Covering index `(book_id, normalized_text, raw_text)` entry ≈ 24 B + slack → **≈ 30 B/row**.

| At 688 k rows (4 MiB English) | Size |
|---|---|
| `occurrence` table | ≈ 24.8 MB |
| covering index | ≈ 20.6 MB |
| **total per 4 MiB import** | **≈ 45 MB ≈ 10.8× the source text** |

The multiplier is scale-invariant; only the absolute number moved (114 MB → 45 MB, a 2.5× reduction).
Ten imported books ≈ 450 MB in the user's local SQLite file (ADR-0005) — acceptable. The adversarial
2.10 M-token case reaches ≈ 138 MB for a single 4 MiB file; noted as residual, not mitigated (a token
cap on top of the byte cap would be speculative today, Art. VII.6).

### 3.3 Import latency (serial, single request)

| Stage | Throughput class | 688 k tokens |
|---|---|---|
| SHA-256 over 4 MiB | ~500 MB/s | 0.01 s |
| regex tokenization (`re.finditer`, C loop) | ~1.5 M tok/s | 0.46 s |
| `normalize()` per token (2× NFC, casefold, translate, strip) | ~400 k tok/s | 1.72 s |
| tuple build + **SQLAlchemy Core** `executemany`, 10 k batches, one txn | ~250 k rows/s | 2.75 s |
| **Total, with persistence** | effective ~140 k tok/s | **≈ 4.9 s** |
| **Total, cuts 1a–1c (no persistence yet)** | | **≈ 2.2 s** |

**Correction to my own earlier arithmetic.** The previous §3.6 quoted "≈ 3.4 s at 4 MiB" using a blended
200 k tok/s. The stage decomposition gives an effective **140 k tok/s**, so the honest figure is
**≈ 4.9 s** — inside a 5 s synchronous budget, but with no headroom. The adversarial 2.10 M-token file
at 4 MiB takes **≈ 15 s**; reachable only by synthetic input, never by prose.

**ORM `Session.add_all()` is forbidden for the occurrence write.** Its identity map and per-object
instrumentation run ~20× slower on the insert stage (≈ 55 s for the same file). The repository adapter
MUST use `sqlalchemy.insert()` with a batched list of dicts on the Core connection. This is a
correctness-of-delivery constraint, not a micro-optimisation.

**Art. IX.6 is discharged by state, not progress** (`docs/constitution.md:101`, disjunction — see
Amendment 1). A ~5 s import needs a perceptible "importando…" state in the UI, which cut 1c ships as
part of the three-state contract already established by `StatusPage.tsx`. No async state machine, no
intermediate `import_status`.

### 3.4 Read path — types, not tokens

#### 3.4.1 Type-count arithmetic (Heaps' law) — computed separately from §3.1

The response carries **one row per distinct normalized form**, not one per occurrence. Vocabulary grows
sublinearly: `V(n) = K · n^β`.

| Language class | K | β | Basis |
|---|---|---|---|
| English prose | 44 | 0.49 | standard empirical fit |
| Morphologically rich (Spanish, German) | 30 | 0.60 | higher β from inflectional productivity |

**Fit validation before use.** At `n = 100,000` tokens the English fit gives
`44 × 100000^0.49 = 44 × 281.9 ≈ 12,400` types. A 100 k-word English novel measures 10–15 k distinct
word types. The fit is sound.

| At 4 MiB | tokens `n` | raw types `V(n)` | × 0.85 casefold/joiner merge | **distinct normalized forms** |
|---|---|---|---|---|
| English | 688 k | `44 × 688000^0.49` = 31,900 | | **≈ 27 k** |
| Morphologically rich | 655 k | `30 × 655000^0.60` = 92,800 | | **≈ 79 k** |

Distinct `(normalized_form, raw_text)` pairs — the SQL projection row count — run ≈ 1.25× the form
count (most forms have one surface spelling; some have a sentence-initial capitalised variant):
**≈ 34 k (English) / ≈ 99 k (rich)**.

**A 688 k-token corpus therefore yields ~27 k rows, not 688 k.** That is the whole point: a 25× file-size
increase between a short story and the 4 MiB ceiling produces only a ~5× row increase.

#### 3.4.2 Row payload — derived, not assumed

Starlette's `JSONResponse` calls `json.dumps(..., ensure_ascii=False, separators=(",", ":"))` — compact
separators, no ASCII escaping. One row serialises as
`{"normalized_form":"…","display_form":"…","frequency":N}`.

| Component | bytes |
|---|---|
| key names with quotes and colons (`"normalized_form":` 18 + `"display_form":` 15 + `"frequency":` 12) | 45 |
| braces + 2 separating commas | 4 |
| quotes around the two string values | 4 |
| `normalized_form` value — **type-averaged** word length ≈ 8.5 chars (longer than the token-averaged ~5, because the type list is dominated by rare long words) | 8.5 |
| `display_form` value | 8.5 |
| `frequency` digits, mean | 2 |
| UTF-8 multi-byte accented characters, +~8 % on the two string values | +1.4 |
| **derived per-row payload** | **≈ 74 B** |

Working figure **80 B/row** (margin for longer agglutinative forms).

#### 3.4.3 Resulting body size at 4 MiB

| Language class | rows | × 80 B | **body** |
|---|---|---|---|
| English | ≈ 27 k | | **≈ 2.2 MB** |
| Morphologically rich | ≈ 79 k | | **≈ 6.3 MB** |

#### 3.4.4 The original "8–36 MB" figure was wrong — here is precisely how

| Component | Original | Corrected | Verdict |
|---|---|---|---|
| row count at 10 MiB | 40 k–180 k | Heaps gives `44 × 1720000^0.49 × 0.85` ≈ 42 k and `30 × 1720000^0.60 × 0.85` ≈ 140 k | **Row count was NOT a types/tokens conflation** — it was Heaps-consistent. But it was never derived, so it was unauditable. |
| per-row payload | 200 B (implied, never stated) | ≈ 74 B derived | **Wrong by ~2.6×.** This is the entire error. |
| body at 10 MiB | 8–36 MB | ≈ 3.4–11.2 MB | overstated ~2.6–3× |

I did not confuse occurrences with distinct forms. I asserted an undocumented 200 B/row payload that is
~2.6× the real compact-JSON row, and I published the product of two unshown numbers. The row count
being coincidentally right does not excuse it: an unauditable figure is a defect even when it lands
near the answer.

#### 3.4.5 Read latency at 4 MiB

| Stage | English (27 k forms) | Rich (79 k forms) |
|---|---|---|
| index-ordered `GROUP BY` over 688 k covering-index entries | 0.14 s | 0.14 s |
| marshalling 34 k / 99 k triples into Python | 0.03 s | 0.08 s |
| `domain.frequency.build_table()` D1/D2/D3 + §2.4 sort | 0.06 s | 0.17 s |
| Pydantic + JSON serialisation | 0.30 s | 0.87 s |
| **total `GET`** | **≈ 0.53 s** | **≈ 1.26 s** |
| *of which the aggregation segment* | *0.23 s* | *0.39 s* |

#### 3.4.6 Pagination is NOT needed at 4 MiB — no spec change requested

- 2.2 MB / 6.3 MB never crosses a network: the backend is local (ADR-0005), so this is a loopback copy.
- The payload is ~60 % literal repeated key names; gzip compresses it 6–8× to ~0.3–0.9 MB if it ever
  did travel.
- The genuine cost is **DOM size** — 79 k `<tr>` elements will jank. That is a *rendering* concern, and
  its remedies (row virtualisation, or a "mostrando las primeras N formas" affordance) compute no
  linguistic rule, derive no grouping key and re-sort nothing, so `REQ-002-014` / `AC-002-19` are
  untouched and no contract changes.
- Pagination becomes a genuine **spec** question above roughly **150 k rows / 12 MB**. Reaching that in
  any natural language needs a corpus far beyond 4 MiB, so it is unreachable under the amended limit.

**Conclusion: spec §7's exclusion of pagination stands. No maintainer decision required.**

### 3.5 Decision: **no precomputed aggregate table** — reconfirmed at 4 MiB

| Option | Tradeoff at 4 MiB | Decision |
|---|---|---|
| A — `form_frequency` aggregate written at import | Removes only the 0.23–0.39 s aggregation segment, **not** the 0.30–0.87 s serialisation that dominates `GET`. Buys ≤ 40 % of read latency in exchange for a cache whose invalidation contract must be redesigned the moment ADR-0007 corrections and reprocessing land. Speculative today (Art. VII.6). | **Rejected, more clearly than at 10 MiB** |
| B — compute on read from the `(raw, normalized, count)` projection + covering index | ≈ 40 ms at realistic novel sizes, 0.53–1.26 s at the ceiling. Zero invalidation surface. | **Chosen** |
| C — persist only aggregates, no per-token rows | Contradicts `REQ-002-008` and `REQ-002-010`. | Inadmissible |

**The pre-committed trigger was measuring the wrong thing — corrected.** The original trigger was
"`GET` p95 above 500 ms". At 4 MiB the morphologically-rich `GET` is ~1.26 s, so that trigger fires
immediately — yet an aggregate table cannot fix it, because ~69 % of that time is serialisation the
aggregate table does not touch. A trigger that fires for a cause its remedy cannot address is a bad
trigger.

**Revised trigger:** add `form_frequency` when the **aggregation segment alone**
(`BookRepository.frequency_pairs()` + `domain.frequency.build_table()`, instrumented as one span)
exceeds **250 ms p95** on the `T-BENCH` corpus. That is the only latency an aggregate table removes.
At 4 MiB the segment is 0.23 s (English) / 0.39 s (rich), so the trigger correctly stays silent for
English and correctly fires for morphologically rich corpora at the ceiling.

**If total `GET` latency is the concern instead, the lever is serialisation, not storage** — `orjson`,
or `model_construct` to skip re-validating server-built rows. Neither is proposed now.

**Escape hatch, designed rather than deferred.** `BookRepository.frequency_pairs()` returns a raw
projection; the rule lives in `domain`. Introducing `form_frequency` later is therefore *one additive
migration plus one adapter method body* — `application`, `api`, `domain` and the frontend are
untouched. **Invalidation contract, pre-committed for whoever adds it:** the aggregate is a pure
function of `occurrence` rows for one `book_id`; every writer of those rows (import, future
reprocessing, future `ManualCorrection` application) must recompute the whole book's aggregate inside
the same transaction. No partial-row invalidation, no TTL, no background job — this keeps ADR-0007's
"reprocessing never silently overwrites" guarantee checkable, because the derived table is never a
second source of truth.

### 3.6 The limit is 4 MiB (`4194304`) — accepted and pinned

| Metric at the ceiling | 10 MiB (previous) | **4 MiB (amended)** |
|---|---|---|
| occurrence rows (English) | 1.72 M | **688 k** |
| database footprint | 114 MB | **45 MB** |
| import wall time | ≈ 12 s | **≈ 4.9 s** |
| distinct forms | 42 k – 140 k | **27 k – 79 k** |
| response body | 3.4 – 11.2 MB *(corrected)* | **2.2 – 6.3 MB** |
| `GET` latency | 1.0 – 2.5 s | **0.53 – 1.26 s** |

Still clears the AMB-3 rationale ("above a full-length novel"): *War and Peace* in plain text is
≈ 3.2 MB. `Settings.max_import_size_bytes` defaults to `4_194_304`; `REQ-002-003` and `AC-002-03` are
being amended in parallel to assert that literal.

---

## 4. Data flow

```
POST /api/v1/imports  (multipart)
   │  api/routes/imports.py — thin (Art. VII.4)
   │    passes upload.filename, upload.content_type, upload.file  ── no FastAPI type crosses inward
   ▼
application/imports/use_cases.py :: ImportText
   ├─1 validate filename ext + content type      → InvalidFileTypeError   (0 bytes read)
   ├─2 stream 64 KiB chunks, abort when > limit  → FileTooLargeError      (bounded memory)
   │     └── feed hashlib.sha256 incrementally
   ├─3 TextExtractor.extract(bytes)              → InvalidEncodingError   (strict UTF-8, BOM strip)
   ├─4 domain.tokenize(text)        → tuple[Token, ...]      (raw_text + position)
   ├─5 domain.normalize(raw)        → normalized_text        (per token)
   ├─6 domain.frequency.build_table(pairs) → ordered rows    (D1/D2/D3 + §2.4)
   └─7 BookRepository.create(...)   → book_id                (Core bulk insert, one txn)
   ▼
201 { id, import_status, distinct_form_count, total_token_count, forms:[{normalized_form, display_form, frequency}] }

GET /api/v1/imports/{id}
   BookRepository.frequency_pairs(id) ──► [(raw_text, normalized_text, count)]   ← SQL counts only
                                            │
                                            └─► domain.frequency.build_table()  ← THE SAME RULE
DELETE /api/v1/imports/{id}
   BookRepository.delete(id) → explicit two-statement delete in one txn → 204 | 404
```

---

## 5. Where normalization happens — and why `AC-002-24` survives (the flagged trap)

`AC-002-24` asserts every `display_form` occurs **verbatim in the imported text**, and `display_form`
is `Occurrence.raw_text`.

**Decision: there is NO document-level text transformation. None. Ever.**

| Transformation | Where it runs | Consequence |
|---|---|---|
| NFC (`N1`, `N3`) | inside `normalize()`, on **one token**, producing `normalized_text` | `raw_text` stays a byte-exact slice of the source |
| casefold (`N2`), joiner folding (`N4`), joiner strip (`N5`) | same | same |
| `U+00AD` soft hyphen (`T1`) | **transparent character inside the tokenizer**, and stripped inside `normalize()` — *not* a pre-pass over the document | `raw_text` retains the SHY, so it is still literally in the text |

**If the document were NFC-normalized before tokenizing, `AC-002-24` would break**: a source written
as `cafe` + `U+0301` would yield `raw_text = "café"` (precomposed), a byte sequence that does not occur
in the file. That is the trap. It is closed by construction: `raw_text` is always
`source[match.start():match.end()]`.

Two consequences that are **intended behaviour, not defects**, and must be stated in the UI docs:

1. The precomposed and decomposed spellings of `café` are **two distinct `raw_text` values** competing
   separately in the D1 multiset. They still land in **one group** (same `normalized_text`). D2/D3
   picks one; both render identically on screen. Deterministic, order-independent, spec-compliant.
2. A `display_form` may contain an invisible `U+00AD`. It renders identically and it genuinely occurs
   in the file. `AC-002-24`'s substring assertion holds literally.

**Divergence from the letter of `T1`** (which says SHY is "removed from the text before tokenization"):
implementing it as a document pre-pass is the *only* reading that breaks `AC-002-24`. See **§10 CONTRA-2**.

---

## 6. Persistence schema

### 6.1 Tables (Alembic revision `0002_book_occurrence`, `down_revision = "0001_baseline"`)

**`book`**

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `INTEGER` | PK (rowid alias) | |
| `language` | `VARCHAR(35)` | NULL | ADR-0008 hook. Unset this slice, no detection (OQ-2 deferred) |
| `content_hash` | `CHAR(64)` | NOT NULL | lowercase SHA-256 hex of raw bytes (`REQ-002-009`, Art. VI.3) |
| `import_status` | `VARCHAR(16)` | NOT NULL | `succeeded` \| `failed` only (`REQ-002-013`) |
| `token_count` | `INTEGER` | NOT NULL, default `0` | total emitted tokens; `AC-002-08` sum check |
| `created_at` | `DATETIME` | NOT NULL | from the existing `Clock` port, UTC |

No `pos` column, no `deleted_at`, no `is_deleted`, no tombstone (`REQ-002-010`, `REQ-002-011`, hooks H8/H1).

**`occurrence`**

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `INTEGER` | PK | |
| `book_id` | `INTEGER` | NOT NULL, FK → `book.id` `ON DELETE CASCADE` | |
| `raw_text` | `TEXT` | NOT NULL | *forma textual* — byte-exact source slice (§5) |
| `normalized_text` | `TEXT` | NOT NULL | *forma normalizada* — grouping key |
| `position` | `INTEGER` | NOT NULL | zero-based **token index** (`T10`, AMB-1) |
| `pos` | `VARCHAR(16)` | NULL | reserved, always `None` (`REQ-002-010`, ADR-0006) |

**Indexes**

| Index | Columns | Why |
|---|---|---|
| `ix_occurrence_book_norm_raw` | `(book_id, normalized_text, raw_text)` | **covering** — serves the entire `GROUP BY` as an ordered index scan, no temp b-tree, no sort |
| `ix_book_content_hash` | `(content_hash)` — **non-unique** | cut 2. Non-unique is deliberate: spec §7 excludes re-import dedup by hash |

**No index on `(book_id, position)`.** A `UNIQUE` guard there would cost ~26 MB and an extra b-tree
write per row at the ceiling, to protect an invariant that a pure `domain` property test proves for
free (positions are `0..n-1`, contiguous, by construction of `tokenize`). Storage and insert
throughput win; the guarantee is unchanged.

### 6.2 Deletion — explicit, not `ON DELETE CASCADE`

SQLite ships with `PRAGMA foreign_keys = OFF` by default, so the declared cascade **silently does
nothing** unless the pragma is set on every connection. `AC-002-15` demands zero remaining
`Occurrence` rows. Relying on a global pragma would make that assertion depend on engine
configuration shared with the already-shipped health/foundation code.

`BookRepository.delete()` therefore issues, in one transaction:
`DELETE FROM occurrence WHERE book_id = ?` then `DELETE FROM book WHERE id = ?`, returning `False`
when the book row does not exist (→ `IMPORT_NOT_FOUND`). The FK declaration stays for schema
documentation and future-proofing. Art. X.4 (no inconsistent partial state) is satisfied by the
single transaction.

### 6.3 Reserved provenance columns — **not shipped**

`proposal.md §Schema extensibility` states that provenance fields (source / version / date /
confidence) are "reserved nullable on the persisted record". This design **ships only `pos`** as
reserved, because spec §7 lists provenance among the explicit non-additions and Art. VII.6 forbids
speculative abstraction. SQLite `ALTER TABLE ADD COLUMN` is O(1) metadata-only, so the additive path
the proposal relies on remains open at zero cost. See **§10 CONTRA-3**.

### 6.4 Extensibility check (proposal's table, re-verified against this schema)

| Future concern | Attaches how |
|---|---|
| per-occurrence `pos` (ADR-0006) | column exists, populate it |
| `lemma` (Art. V.1) | new `lexeme` table + nullable `occurrence.lemma_id` FK. `raw_text`/`normalized_text` never collapse |
| MWEs (ADR-0009) | new sibling table keyed to `(book_id, position)` spans — `position` is already the stable key |
| manual corrections (ADR-0007) | new `manual_correction(occurrence_id, field, …)` table + provenance columns via `ADD COLUMN` |
| multiple languages (ADR-0008) | `book.language` already nullable |

---

## 7. Interfaces

### 7.1 Domain (pure, stdlib only)

```python
# domain/models.py
@dataclass(frozen=True, slots=True)
class Token:
    raw_text: str        # byte-exact source slice
    position: int        # zero-based token index (T10)

@dataclass(frozen=True, slots=True)
class FormFrequency:
    normalized_form: str  # grouping key (§2.3)
    display_form: str     # majority surface form (§2.5 D1-D3)
    frequency: int        # >= 1 (REQ-002-017)

# domain/text/tokenizer.py
def tokenize(text: str) -> tuple[Token, ...]: ...          # T1-T10

# domain/text/normalizer.py
def normalize(text: str) -> str: ...                       # N1-N5, idempotent (REQ-002-015)

# domain/frequency.py
def build_table(pairs: Iterable[tuple[str, str, int]]) -> tuple[FormFrequency, ...]:
    """(raw_text, normalized_text, count) -> ordered rows. D1/D2/D3 + §2.4 sort key.

    THE single implementation of the display-form and ordering rules. Called by
    the import path (counts all 1) and by the read path (counts from SQL).
    A function of the multiset only — no positional input exists to tie-break on.
    """

def sort_key(normalized_form: str) -> tuple[str, str]: ...  # (NFD minus M*, normalized_form)
```

### 7.2 Application ports (`Protocol`, mirroring `application/clock.py`)

```python
# application/imports/ports.py
class ByteStream(Protocol):
    """Structural view of an inbound upload body. starlette UploadFile.file
    satisfies this without an adapter class (Art. VII.6)."""
    def read(self, size: int, /) -> bytes: ...

class TextExtractor(Protocol):
    def extract(self, data: bytes) -> str: ...              # raises InvalidEncodingError

class BookRepository(Protocol):
    def create(self, *, content_hash: str, token_count: int,
               created_at: datetime,
               occurrences: Sequence[tuple[str, str, int]]) -> int: ...
    def frequency_pairs(self, book_id: int) -> list[tuple[str, str, int]] | None: ...
    def delete(self, book_id: int) -> bool: ...   # cut 3
```

`frequency_pairs` returns `None` for an unknown id (→ 404) and `[]` for an empty import
(→ `REQ-002-012` zero state). Those two cases must not be conflated.

**No `exists()` on this port.** An earlier revision of this snippet declared one, and cut 2 shipped
it, but nothing ever called it: `frequency_pairs` already distinguishes the unknown id (`None`) from
the empty import (`[]`), and §6.2's `DELETE` flow calls `delete()` directly for both the `204` and
the `404` leg. It was removed before cut 2 merged rather than left as an unused port member — see
`tasks.md` contradiction note 8 and the T208 amendment. `delete()` is declared here because this
snippet documents the port's final shape; it is implemented in cut 3, not before.

### 7.3 Infrastructure adapters

```python
# infrastructure/text_extraction.py
class PlainTextExtractor:                     # implements TextExtractor
    def extract(self, data: bytes) -> str:
        text = data.decode("utf-8")           # strict; raises UnicodeDecodeError
        return text.removeprefix("\ufeff")    # BOM tolerated (AC-002-05)
        # UnicodeDecodeError is caught and re-raised as InvalidEncodingError WITHOUT
        # attaching object/start/end — those leak byte offsets into the user's text (Art. X.2)

# infrastructure/persistence/book_repository.py
class SqlAlchemyBookRepository:               # implements BookRepository
    _INSERT_BATCH = 10_000                    # Core insert(), NOT Session.add_all() — §3.3
```

### 7.4 Settings

```python
max_import_size_bytes: int = 4_194_304        # env MAX_IMPORT_SIZE_BYTES (REQ-002-003), 4 MiB
```

---

## 8. Upload handling — validation order (bounded memory)

`await file.read()` with no bound defeats the point of a size limit: Starlette spools an `UploadFile`
to a temp file above 1 MiB, so an unbounded read yields both a >4 MiB temp file **and** a >4 MiB
`bytes` object before any check runs.

**Ordered gate, enforced inside `ImportText` (application owns the policy, `api` owns the plumbing):**

| # | Gate | Bytes read | Failure |
|---|---|---|---|
| 1 | filename suffix `.txt` case-insensitively **and** content type in `{text/plain, application/octet-stream}` | 0 | `INVALID_FILE_TYPE` 422 |
| 2 | `Content-Length` header, when present, above the limit → fast reject | 0 | `FILE_TOO_LARGE` 413 |
| 3 | loop `stream.read(65536)`; accumulate into `bytearray`; feed `sha256` incrementally; **abort the instant `len(buf) > limit`** | ≤ limit + 64 KiB | `FILE_TOO_LARGE` 413 |
| 4 | strict UTF-8 decode + BOM strip | — | `INVALID_ENCODING` 422 |
| 5 | tokenize → normalize → aggregate → persist | — | — |

Notes that must survive into tasks:

- Gate 2 is an **optimisation only**. `Content-Length` is client-supplied and may be absent under
  chunked transfer encoding. Gate 3 is the enforcement.
- Comparison is `>`, not `>=` — `AC-002-03`'s "a file exactly at the limit is accepted" scenario.
- The route is `def`, not `async def` (FastAPI runs it in the threadpool), matching `routes/health.py`.
  This is what lets `ByteStream` stay a synchronous `Protocol` and keeps `application` async-free.
- Aborting early leaves the request body undrained. Uvicorn sends the response and closes the
  connection cleanly; no explicit drain is added.

---

## 9. Error taxonomy

### 9.1 Exception types

Declared in `application/imports/errors.py` — the port module owns its failure types, so
`infrastructure` may raise them without `application` ever importing `infrastructure`.

```python
class ImportError_(Exception):          # base; never raised directly
    code: ClassVar[str]
class InvalidFileTypeError(ImportError_):  code = "INVALID_FILE_TYPE"
class FileTooLargeError(ImportError_):     code = "FILE_TOO_LARGE"    # carries limit: int
class InvalidEncodingError(ImportError_):  code = "INVALID_ENCODING"
class ImportNotFoundError(ImportError_):   code = "IMPORT_NOT_FOUND"
```

Each carries **only** safe, non-textual interpolation values (`limit`, accepted extension, expected
encoding). No exception ever holds a slice of the user's text, a byte offset into it, or a filesystem
path (Art. X.2, `REQ-002-013`).

### 9.2 Wire mapping (`api/errors.py`, one `ExceptionHandler` per class + a `RequestValidationError` handler)

| Code | HTTP | Trigger | Art. X.3 class | Message shape (no user text) |
|---|---|---|---|---|
| `INVALID_FILE_TYPE` | 422 | extension ≠ `.txt`, or content type outside the allowlist | Format | "Solo se admiten archivos `.txt`." |
| `FILE_TOO_LARGE` | 413 | byte length `>` `max_import_size_bytes` | User | "El archivo supera el límite de {limit} bytes." |
| `INVALID_ENCODING` | 422 | bytes are not valid UTF-8 | Format | "El archivo debe estar codificado en UTF-8. Conviértelo con …" |
| `IMPORT_NOT_FOUND` | 404 | unknown or already-deleted `id` | User | "La importación solicitada no existe." |
| `INVALID_REQUEST` | 422 | **design addition** — FastAPI `RequestValidationError` (e.g. a JSON body instead of a file part, `AC-002-01`) | User | "La petición no incluye un archivo válido." |

`INVALID_REQUEST` is added so that **every** error on these routes shares one envelope. Without it
`AC-002-01`'s JSON-path rejection returns FastAPI's native `{"detail": [...]}`, giving the capability
two different 422 shapes and violating spec §4's "every error body MUST carry a distinct code". Spec §7
assigns DTO shapes to design, so this is an addition, not a contradiction. Verify hook H1 confirms no
new code contains `lemma|lexeme|lema|lexema`.

### 9.3 Body DTO

```json
{ "error": { "code": "FILE_TOO_LARGE", "message": "El archivo supera el límite de 4194304 bytes." } }
```

`extra="forbid"` on the Pydantic model, mirroring `dtos/health.py`. Pinned in
`api/schemas/import.v1.json` (Draft 2020-12) with `X-Schema-Version: 1`, mirroring `health.v1.json`.
No stack trace, no path, no environment value ever enters `message`.

### 9.4 Logging (`REQ-002-013` / `AC-002-18`)

A single module logger emits `code=<CODE> import_id=<id|->` and **nothing else**. There is no
`extra={"filename": …}`, no exception chaining that would render the decoded text into a traceback,
and no `logger.exception()` on `UnicodeDecodeError` — `UnicodeDecodeError.__str__` embeds the
offending byte and its offset. Handlers re-raise as `InvalidEncodingError` with `from None`.

---

## 10. Contradictions surfaced (AGENTS.md §9 — recorded, NOT silently resolved)

| ID | Contradiction | Where | This design's provisional handling | Needs maintainer |
|---|---|---|---|---|
| **CONTRA-1** | ~~`REQ-002-013`'s terminal-only `import_status` vs. Art. IX.6 at a multi-second import.~~ **WITHDRAWN — not a contradiction. My reading was wrong.** | `docs/constitution.md:101` | Art. IX.6 reads "progreso **o** estado" — a **disjunction**, structurally identical to Art. IX.5 at `docs/constitution.md:100` ("confirmación **o** reversibles"), which the spec phase read correctly and `REQ-002-011` depends on. A perceptible "importando…" state discharges it on the *estado* branch; the three-state contract already established by `StatusPage.tsx` supplies it in cut 1c. `succeeded\|failed` stands as specified. No progress bar, no async state machine. The failure was mine: I applied the disjunction correctly to Art. IX.5 and then failed to apply it to Art. IX.6 one article later. | **Closed** |
| **CONTRA-2** | `T1` says `U+00AD` is "removed from the text **before tokenization**" (a document-level rewrite), but `AC-002-24` requires every `display_form` to occur verbatim in the imported text. A document pre-pass makes `raw_text` a string absent from the file. | spec §2.2 T1 vs `AC-002-24` | Implemented as a **transparent character in the tokenizer + stripped inside `normalize()`**; `raw_text` retains the SHY (§5). Preserves both `T1`'s observable effect (no split token, SHY absent from the key) and `AC-002-24` literally. | Confirm the reading; no spec edit strictly required |
| **CONTRA-3** | `proposal.md §Schema extensibility` says provenance/confidence columns are "reserved nullable" now; spec §7 lists provenance among explicit non-additions and Art. VII.6 forbids speculative abstraction. | proposal vs spec §7 | Ships **only** `pos` reserved. `ADD COLUMN` keeps the proposal's additive path open at zero cost (§6.3). | Low risk; confirm at review |
| **CONTRA-4** | The brief refers to hook **H2** as the frontend `.sort(` grep. In the shipped spec, H2 is the `domain/` framework-import check; the `.sort(` grep is `AC-002-19` under `REQ-002-014`. | brief vs spec §8 | Scoping designed for `AC-002-19` (§11). H2 read as written. | Informational |
| **CONTRA-5** | Cut 1 as allocated carries 12/18 requirements and far exceeds the accepted 400–700 `size:exception` band. | proposal §Sizing vs spec §1.2 | **Accepted.** Cut 1 splits; `T-GUARD` dropped and `REQ-002-003` moved into the first cut as a real setting. Re-sliced into five cuts in §12, all inside the band. | **Closed** |
| **CONTRA-6** *(new, non-blocking)* | Keeping `REQ-002-002` and `REQ-002-004` in a later cut forces the first cut — which merges to `main` — to either decode without strict handling or classify no filename at all, i.e. exactly the hard-coded-stopgap pattern the maintainer rejected for `REQ-002-003`. | spec §1.2 cut map | Both move into the intake cut alongside `REQ-002-003`, on the maintainer's own stated principle. Cost is ~40 src + ~55 test lines; §12.1. | Confirm at review |

---

## 11. `AC-002-19` scoping — the `.sort(` false-positive problem

A repo-wide grep for `.sort(`, `toLowerCase(`, `localeCompare(`, `normalize(`, `NFC|NFD|NFKC|NFKD`
across `apps/web/src/` will fail the day someone sorts an unrelated dropdown. The spec already scopes
the check to "import or frequency-table code"; it does not say how that scope is decided.

**Mechanism: a pinned module manifest, not a directory glob.**

`apps/web/tests/contracts/no-linguistic-rules.test.ts` declares one constant:

```ts
const IMPORT_FEATURE_MODULES = [
  "src/pages/ImportPage.tsx",
  "src/components/ImportForm.tsx",
  "src/components/FrequencyTable.tsx",
  "src/api/imports.ts",
  "src/types/imports.ts",
  // cut 3 appends "src/components/DeleteImportButton.tsx"
] as const;
```

**The manifest is cut-scoped.** It lists the modules that exist in the current cut, never future ones. `DeleteImportButton.tsx` is created in cut 3 (T309), so listing it in cut 1c would make assertion 1 unsatisfiable inside a cut that is supposed to be independently shippable.

Scoping is safe because assertion 3 is the reverse check: any new module whose name matches the feature pattern must appear in the manifest, so cut 3 cannot forget to append its component. The guard fails loudly either way, which is the property that matters.

The test asserts, in order:

1. the list is non-empty and **every entry exists on disk** — a renamed or deleted module fails loudly
   instead of silently shrinking the checked surface;
2. no listed file matches the forbidden patterns;
3. **every** file under `apps/web/src/` whose name matches `/[Ii]mport|[Ff]requenc/` **appears in the
   manifest** — a new feature module cannot be added outside the checked surface, and a later cut
   cannot forget to append its own component.

Assertions 1 and 3 are deliberately opposed: 1 forbids listing what does not exist, 3 forbids omitting
what does. Together they are what make a cut-scoped manifest safe.

Why a manifest beats the alternatives:

| Option | Why not |
|---|---|
| glob `apps/web/src/**` | false-positives on unrelated future sorting — the stated concern |
| glob a new `src/features/imports/` directory | would work, but abandons the flat `pages/components/api/types` layout the foundation cycle established; the design skill requires following existing convention |
| ESLint `no-restricted-syntax` with a `files:` override | equivalent guarantee, but the failure surfaces in lint rather than the test suite, and the spec phrases the check as a search over sources |

Adding a module to the import feature without adding it to the manifest is the one gap. It is closed
by a second assertion: every file under `apps/web/src/` whose name matches `/[Ii]mport|[Ff]requenc/`
must appear in the manifest.

---

## 12. Delivery — re-sliced (CONTRA-5 accepted)

### 12.1 Intake requirements move forward with `REQ-002-003`

The maintainer moved `REQ-002-003` into the first cut on the principle that *a hard-coded stopgap on a
path merging to `main` is worse than a proper setting that costs almost nothing*. **The same argument
applies unchanged to `REQ-002-002` and `REQ-002-004`**, so both move with it:

| REQ | Why it cannot wait for a later cut | Cost to move |
|---|---|---|
| `-004` strict UTF-8 | The first cut **must** decode bytes to `str` to tokenize at all. Leaving the polished error for later means shipping either a generic 422 for a Latin-1 file (fails Art. VIII.4, "los errores de usuario son comprensibles") or an undecorated `UnicodeDecodeError` that leaks a byte offset into user text (fails Art. X.2). | ~25 src + ~30 test |
| `-002` extension / content-type | The first cut ships a public upload endpoint to `main`. The threat matrix (§15) marks filename classification **Applicable**, and applicable rows must carry RED tests into the same delivery as the surface they guard. | ~15 src + ~25 test |

Cut "2 — hardening" therefore **dissolves**. Its five requirements land as: `-002`, `-003`, `-004`,
`-013` in the intake cut; `-009` with persistence, where `Book` first exists.

### 12.2 Line estimate for the first cut, re-measured

The earlier ~1575 figure over-counted the rule-coverage tests: `AC-002-07` is satisfied by a
`pytest.mark.parametrize` table at ~2 lines per case, not ~13. Re-measured backend-only, with the
intake requirements folded in:

| Area | Src | Tests |
|---|---|---|
| `domain` models / tokenizer / normalizer / frequency | 210 | 110 rule table + 45 D1–D3 & sort + 70 properties |
| `application` ports / errors / `ImportText` | 145 | 55 |
| `infrastructure` extractor + settings field | 35 | 50 |
| `api` routes / DTOs / errors / deps / main / JSON Schema | 230 | 145 |
| **Backend subtotal** | **620** | **475** → **≈ 1095** |
| frontend + contract test + E2E + docs | 215 | 310 → **≈ 525** |

**≈ 1620 combined, ≈ 1095 backend-only.** Both exceed the 400–700 band. Reporting now, as instructed.

### 12.3 Why the band is unreachable for a single first cut

`domain` alone is ~210 src + ~225 tests ≈ **435 lines**, because `AC-002-07` mandates a case for every
`T1`–`T10` and `N1`–`N5` row and `AC-002-20`/`-21`/`-22` mandate three Hypothesis properties. That is
already two-thirds of a 700-line budget, and it produces no output a user can see. Adding the intake
gates, the error taxonomy, the route and the JSON Schema on top reaches ~1095 before a single `.tsx`.
No **vertical** decomposition avoids this: the smallest slice containing `tokenize` + `normalize` +
`build_table` + a route + their mandated tests is ~1095 lines.

### 12.4 Recommended shape — five cuts, all inside the band

`Art. III.2` (`docs/constitution.md:41`) reads "Cada corte debe producir un resultado observable **o**
verificable" — **a disjunction**, the same construction as Art. IX.5 and Art. IX.6. A cut that ships no
UI but is fully verifiable through its tests, its OpenAPI contract and its JSON Schema satisfies
Art. III.2 on the *verificable* branch. That is what makes an in-band split legitimate here.

| # | Cut | Outcome | Requirements | Est. |
|---|---|---|---|---|
| 1 | **1a — language engine** | `tokenize`, `normalize`, `build_table`, `sort_key` with full `T`/`N`/`D` rule coverage and the three properties. *Verificable.* | `-005`, `-015`, `-016`, `-017`; domain half of `-006`, `-018` | **~435** |
| 2 | **1b — callable import** | `POST /api/v1/imports` returns the ordered table. Intake gates, error taxonomy, settings, JSON Schema. *Verificable.* | `-001`, `-002`, `-003`, `-004`, `-012`, `-013`(p), `-007`(backend); response half of `-006`, `-018` | **~660** |
| 3 | **1c — visible import** | Upload form + frequency table + zero state + "importando…" state. **Observable.** | `-014`, `-007`(frontend) | **~525** |
| 4 | **2 — persistence** | `Book`/`Occurrence` + migration + repository + `GET`; the table survives a restart. **Observable.** | `-008`, `-009`, `-010`, `-013`(closed); persistence half of `-006`, `-018` | **~490** |
| 5 | **3 — deletion** | `DELETE` + confirmation UI. **Observable.** | `-011` | **~330** |

All five sit inside or below the accepted 400–700 band. **No cut needs `size:exception`.**

**Cost, stated plainly.** Two consecutive cuts (1a, 1b) ship no UI. That is a horizontal pair, and
Art. III.3 forbids "fases horizontales **largas** sin valor integrado". Two PRs delivering integrated
value on the third is short, not *larga* — but it is the weakest point of this shape and the maintainer
should overrule it if they read III.3 more strictly. **The in-band alternative does not exist**: merging
1a+1b gives ~1095 and needs `size:exception` at ~1.6× the band ceiling.

### 12.5 Requirements that span cuts — `sdd-verify` must be told

| REQ | 1a | 1b | 1c | 2 | Complete at |
|---|---|---|---|---|---|
| `-006` aggregate + order | rule + sort | response body | rendered order | after `GET` round trip | **cut 2** |
| `-018` display form | D1–D3 rule | `display_form` field | rendered cell | `AC-002-24` "no schema column" clause | **cut 2** |
| `-007` no lemma naming | — | backend keys | UI strings | DB columns | **cut 2** (H1 re-runs every cut) |
| `-013` logs no raw text | — | success path | — | "fails after decoding" leg, which only exists once persistence can fail | **cut 2** |

None of these is a regression in the earlier cuts; each is a **partially satisfied requirement by
design**. `sdd-verify` must not read cut 1a as failing `-006`.

`ImportText` is touched twice: it returns the table in 1b and additionally persists in cut 2 — one
signature, one extra port argument. That is the whole cost of the split.

**The unbounded-upload hazard is gone.** `REQ-002-003` now lands in 1b, the same cut that first exposes
`POST` to `main`. `T-GUARD` is dropped.

Chain strategy `stacked-to-main` is unchanged.

---

## 13. Testing strategy

| Layer | What | Marker / runner | Notes |
|---|---|---|---|
| Unit, no DB | `tokenize` T1–T10, `normalize` N1–N5, `build_table` D1–D3, `sort_key` §2.4, adversarial code points (`ŉ`, `ẞ`, `İ`, `ΣΊΣΥΦΟΣ`, `Straße`) | `unit` / pytest | table-driven, one case per spec row (`AC-002-07`) |
| Unit, Hypothesis | idempotence (`AC-002-20`), order independence over keys + frequencies + **display forms** (`AC-002-21`), frequency ≥ 1 (`AC-002-22`) | `unit` | pure — `build_table` takes a projection, so no DB is needed. Test carries the `AMB-4` note to re-verify against real lemmas |
| Unit | `Settings.max_import_size_bytes` default + env override (`AC-002-03`); error DTO shape | `unit` | `monkeypatch.setenv` + `Settings()`, bypassing the `lru_cache` |
| Integration, SQLite | `alembic upgrade head` / `downgrade -1` (`AC-002-11`, H3); repository round trip in a **new session** (`AC-002-12`); `pos is None` + distinct `raw_text`/`normalized_text` (`AC-002-14`); delete leaves zero occurrences (`AC-002-15`) | `integration` | **MUST** register every engine with the existing `managed_engine` fixture — an undisposed engine raises `ResourceWarning`, which the `filterwarnings` gate turns into a failure |
| Integration, bench | `T-BENCH`: generated synthetic corpus at the 4 MiB ceiling; the default run asserts only deterministic invariants (row-count self-consistency, response body size, `Σfrequency == total_token_count`) and **measures and reports** import wall time (§3.3), `GET` total (§3.4.5), and the **aggregation segment** against the 250 ms p95 decision trigger (§3.5) without failing the build on a breach; `WHEEL_BENCH_STRICT=1` additionally asserts the §3.3/§3.4.5 wall-clock budgets on calibrated hardware, never by default CI (`tasks.md` contradiction note 7) | `integration` | fixture generated in-test, never committed (Art. IV.1–2, H6). Lands in cut 2, the first cut with persistence |
| API, preflight | explicit `OPTIONS` + `Access-Control-Request-Method` per exposed method (§14.1) | `api` | catches the `allow_methods` regression that no ordinary `TestClient` test sees |
| API, TestClient | 201/413/422/404 + codes; JSON Schema validation via `jsonschema`; BOM tolerated; empty and whitespace-only files (`AC-002-17`); sentinel log capture (`AC-002-18`, H5) | `api` | mirrors `tests/api/test_health.py`. Sentinel test must capture the **root** logger with propagation on |
| Component, Vitest | table renders received order verbatim; renders `display_form` not `normalized_form`; zero state; confirm-then-delete and cancel (`AC-002-16`); accessible column headers, no colour-only encoding (Art. IX.1–4) | vitest | mocked responses, deliberately non-alphabetical |
| Contract, Vitest | pinned-manifest linguistic-rule grep (§11, `AC-002-19`) | vitest | manifest existence assertion is part of the test |
| Repo-wide | H1 `lemma\|lemas\|lexeme\|lexema` = 0 across `apps/api/src/` + `apps/web/src/`; H8 `deleted_at\|is_deleted\|tombstone` = 0 | `unit` | extends the existing `tests/unit/test_traceability.py` pattern |
| E2E, Playwright | upload synthetic `.txt` → table visible → delete with confirmation → zero state | `e2e` | Chromium only, per the foundation design §8.3 |

**Non-negotiable gate constraints.** The suite is at 50 passed / 0 warnings / 99 % coverage and
`filterwarnings` is an error gate. Nothing here weakens it: no new `filterwarnings` entry, no
`--cov-fail-under` change, no `pytest.ini` edit. Every new branch — the size early-abort, the BOM
strip, the `None`-vs-`[]` distinction in `frequency_pairs`, each error handler — needs its own test
to hold 99 %.

---

## 14. File changes

| File | Action | Description |
|---|---|---|
| `apps/api/src/wheel_vocabulary/domain/models.py` | Create | `Token`, `FormFrequency` frozen dataclasses |
| `.../domain/text/tokenizer.py` | Create | `tokenize()` — T1–T10 |
| `.../domain/text/normalizer.py` | Create | `normalize()` — N1–N5 |
| `.../domain/frequency.py` | Create | `build_table()` D1–D3, `sort_key()` §2.4 |
| `.../application/imports/ports.py` | Create | `ByteStream`, `TextExtractor`, `BookRepository` protocols |
| `.../application/imports/errors.py` | Create | five exception types with `code` |
| `.../application/imports/use_cases.py` | Create | `ImportText`, `ReadImport`, `DeleteImport` |
| `.../infrastructure/text_extraction.py` | Create | `PlainTextExtractor` — strict UTF-8 + BOM |
| `.../infrastructure/persistence/models.py` | Create | `Book`, `Occurrence` mapped classes |
| `.../infrastructure/persistence/book_repository.py` | Create | Core bulk insert, projection query, explicit delete |
| `.../infrastructure/settings.py` | Modify | `+ max_import_size_bytes: int = 4_194_304` |
| `apps/api/migrations/versions/0002_book_occurrence.py` | Create | additive revision; `downgrade()` returns to baseline |
| `.../api/routes/imports.py` | Create | thin `POST` / `GET` / `DELETE /api/v1/imports` |
| `.../api/dtos/imports.py` | Create | request/response/error DTOs, `extra="forbid"` |
| `.../api/errors.py` | Create | exception handlers → wire envelope |
| `.../api/dependencies.py` | Modify | `+ get_text_extractor`, `get_book_repository`, `get_import_text` |
| `.../api/main.py` | Modify | include router; register handlers; extend `allow_methods` beyond `GET` |
| `.../api/schemas/import.v1.json` | Create | Draft 2020-12 contract |
| `apps/web/src/{pages/ImportPage,components/ImportForm,components/FrequencyTable,components/DeleteImportButton}.tsx` | Create | UI, keyboard-navigable, labelled, not colour-only |
| `apps/web/src/api/imports.ts`, `apps/web/src/types/imports.ts` | Create | client fns + types, mirroring `client.ts`/`health.ts` |
| `apps/web/tests/contracts/no-linguistic-rules.test.ts` | Create | §11 manifest check |
| `docs/{traceability-matrix,glossary,architecture/overview,architecture/architecture-baseline}.md` | Modify | move `Book`/`Occurrence` to committed; grouping-by-normalized-form invariant row |

### 14.1 CORS — confirmed defect, assignment, and the regression check

`apps/api/src/wheel_vocabulary/api/main.py:36` sets `allow_methods=["GET"]`. Browser `POST` and
`DELETE` fail preflight while every `TestClient` test stays green.

| Cut | Change to `main.py:36` |
|---|---|
| **1b** (first cut exposing `POST`) | `allow_methods=["GET", "POST"]` |
| **3** (first cut exposing `DELETE`) | `allow_methods=["GET", "POST", "DELETE"]` |

**Correcting my own earlier claim.** I wrote that "a `TestClient` test cannot catch this". That is
wrong, and the distinction matters. Starlette's `CORSMiddleware` acts only on requests carrying an
`Origin` header, and on preflight only for `OPTIONS` + `Access-Control-Request-Method`. `TestClient`
sends neither *by default* — so no ordinary API test catches it **incidentally**. It catches it
perfectly well when asked **explicitly**.

**Primary gate — an explicit preflight test in the default suite** (`tests/api/test_imports_cors.py`,
marker `api`, no browser, milliseconds):

- send `OPTIONS /api/v1/imports` with `Origin: http://127.0.0.1:5173` and
  `Access-Control-Request-Method: POST`;
- assert `200` and that `access-control-allow-methods` contains `POST`;
- one such test per method, added in the cut that adds the method (`POST` in 1b, `DELETE` in 3).

This runs on every `uv run pytest`, so a regression fails in seconds rather than at E2E time.

**Backstop — Playwright.** Cut 1c's upload E2E and cut 3's delete E2E drive a real browser, which
issues the real preflight. If the preflight test were ever deleted, these still fail.

**No `allow_headers` change is needed, and none should be added.** A multipart upload sends
`Content-Type: multipart/form-data`, and `Content-Type` is in Starlette's `SAFELISTED_HEADERS`; `DELETE`
sends no body. The current `allow_headers=[]` is correct — noted so nobody "fixes" it speculatively
(Art. VII.6).

---

## 15. Threat matrix (applicability-driven)

This change adds HTTP routing and a user-supplied-filename classification boundary. It adds no shell,
subprocess, VCS or PR automation. **Every applicable row below lands in cut 1b** (§12.4) — the cut that
first exposes `POST` to `main` — so no guarded surface ships ahead of its RED tests.

| Boundary | Adversarial cases | Applicability | Design response | Planned RED tests |
|---|---|---|---|---|
| Documentation-like paths / executable-file classification | `notes.pdf` renamed `notes.txt`; `SAMPLE.TXT`; `../../etc/passwd.txt`; `report.txt.exe`; missing/empty filename; content type `text/html` | **Applicable** | Allowlist on the **suffix** (`Path(name).suffix.casefold() == ".txt"`) and on content type. The filename is **never** used as a filesystem path, never joined, never written to disk under a derived name, and is not persisted (`overview.md §9`). Content is never executed or evaluated. | wrong extension → 422 `INVALID_FILE_TYPE`, no rows; uppercase `.TXT` → 201; traversal-shaped name → no path is constructed and the request is judged on suffix alone; missing filename → 422 |
| Git repository selection | `git -C`, relative/absolute paths | **N/A** — no VCS operation | — | — |
| Commit state | staged, `commit -a`, empty index | **N/A** — no VCS operation | — | — |
| Push state | tracking branch, first push, refspec | **N/A** — no VCS operation | — | — |
| PR commands | `--head`, env prefix, composed commands | **N/A** — no PR automation | — | — |

Two adjacent boundaries not in the reference matrix but applicable here, carried into tasks the same way:

| Boundary | Cases | Design response | Planned RED tests |
|---|---|---|---|
| Unbounded resource intake | body larger than the limit; lying/absent `Content-Length`; chunked transfer | §8 chunked read with early abort; header used only as a fast path | 65-byte body against a 64-byte limit → 413, memory bounded; `Content-Length` absent → still rejected at the streaming gate |
| Sensitive-content egress into logs and errors | sentinel token in body; `UnicodeDecodeError` embedding the offending byte and offset | code + `import_id` only; `raise … from None`; no `logger.exception` on decode failure | sentinel `zzqxsentinel` absent from every captured record (`AC-002-18`, H5); the 422 body contains no byte offset |

---

## 16. Migration / rollout

Additive only. `alembic upgrade head` applies `0002_book_occurrence`; `alembic downgrade -1` drops both
tables and returns the schema to the empty-schema baseline (`AC-002-11`). No data migration — the
foundation cycle shipped zero user tables. No feature flag. Rollback is a branch revert plus
`alembic downgrade -1`; the health flow is untouched.

---

## 17. Open questions

**No blockers remain.** Both blocking items are closed by Amendment 1.

- [x] ~~CONTRA-1~~ — **closed.** Art. IX.6 is a disjunction (`docs/constitution.md:101`); a perceptible
      "importando…" state discharges it. `succeeded|failed` stands. My reading was wrong.
- [x] ~~CONTRA-5~~ — **closed.** Cut 1 splits; re-sliced into five in-band cuts (§12.4).
- [x] ~~`T-GUARD`~~ — **dropped.** `REQ-002-003` moves into cut 1b as a real setting.
- [x] Size limit — **4 MiB (`4194304`)**, arithmetic recomputed in §3.
- [x] Pagination — **not needed** at 4 MiB (§3.4.6). Spec §7's exclusion stands; no spec change.

Non-blocking, for review:

- [ ] **§12.4** — two consecutive non-observable cuts (1a, 1b) is the weakest point of the in-band
      shape. It rests on Art. III.2's "observable **o** verificable" disjunction
      (`docs/constitution.md:41`). If III.3's "fases horizontales largas" is read more strictly, merge
      1a+1b into one ~1095-line cut and raise `size:exception` for it. Maintainer's call.
- [ ] **CONTRA-6** — confirm `REQ-002-002` and `REQ-002-004` moving into cut 1b alongside `-003`
      (§12.1), which dissolves the old "cut 2 — hardening".
- [ ] **CONTRA-3** — confirm that shipping only `pos` reserved (no provenance columns) is acceptable
      against `proposal.md §Schema extensibility`.
- [ ] **§3.2** — the adversarial `"a "` corpus reaches ~2.10 M rows / ~138 MB inside a 4 MiB file.
      Accepted as residual; a token-count cap alongside the byte cap would be speculative today.

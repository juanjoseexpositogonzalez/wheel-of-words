# Design — Documentation & Methodology Overhaul

## 0. Metadata

| Field | Value |
|-------|-------|
| Change slug | `docs-methodology-overhaul` |
| Capability code | `DOCS` |
| Spec version consumed | 2.0 (Engram #2254) |
| Constitution target version | 2.0.0 (MAJOR) |
| Design phase version | 1.0 |
| Language | EN throughout (Spanish only inside quoted current-file excerpts grounding diff intents) |

**Scope statement**: This design does NOT write final prose. It fixes the content contract — section outlines, diff intents, data structures, ADR beats, diagram node lists — for the `sdd-apply` phase to execute against.

---

## 1. Re-scan verification

### 1.1 A-7 re-scan — "inglés" load-bearing beyond the 4-file payload

**Command run**:
```bash
grep -rn "inglés" --include="*.md" --include="*.yaml" --include="*.txt" . \
  | grep -v "openspec/changes/" | grep -v ".atl/" | grep -v ".git/"
```

**Raw result count**: 3 matches across 3 files.

**Filtered analysis**:

| File | Line | Text (verbatim) | Verdict |
|------|------|-----------------|---------|
| `docs/constitution.md:9` | 9 | `"…vocabulario inglés procedente de obras literarias…"` | **Load-bearing — IN PAYLOAD** (constitution preamble generalization, REQ-DOCS-060) |
| `docs/product-vision.md:21` | 21 | `"Persona adulta que lee literatura en inglés…"` | **Load-bearing — IN PAYLOAD** (§4 user targeting, REQ-DOCS-066) |
| `README.md:3` | 3 | `"…aplicación web de análisis de vocabulario literario en inglés…"` | **Load-bearing — IN PAYLOAD** (line 3, REQ-DOCS-06C) |

**Verdict: A-7 CONFIRMED.** All three load-bearing "inglés" occurrences are already inside the 4-file coordinated amendment payload. No additional files require generalization. The 4-file payload scope is correct and complete.

### 1.2 A-8 re-scan — ADR-0009 rename dangling references

**Command run**:
```bash
grep -rn "Phrasal verbs and multiword\|phrasal verbs.*modeled separately\|0009" \
  --include="*.md" --include="*.yaml" . \
  | grep -v "openspec/changes/" | grep -v ".git/"
```

**Raw result count**: 0 matches for the old title; 4 matches for "phrasal" occurrences (constitution.md:62, product-vision.md:11, product-vision.md:113, product-vision.md:150, AGENTS.md:77).

**Dangling-reference analysis for ADR-0009 old title** ("Phrasal verbs and multiword expressions modeled separately"):
- No file outside `openspec/changes/` references this old title string.
- The spec already uses the new title "Multiword expressions as language-specific instances" throughout.
- The "phrasal" occurrences in product-vision and AGENTS.md are the subject of the OQ-10 amendment payload — they are being generalized, not referencing the old ADR title.

**Verdict: A-8 CONFIRMED — no dangling references.** ADR-0009 rename is clean. The new title "Multiword expressions as language-specific instances" propagates without conflict.

---

## 2. Resolved open questions

### 2.1 OQ-8 — Constitution amendment log placement

**Options considered**:
1. Extend Art. XII in-place by appending the amendment record table directly below the Art. XII text.
2. Add a new `## Registro de enmiendas` section at the end of the constitution document, after Art. XII.

**Chosen option**: **Option 2 — New `## Registro de enmiendas` section** appended as the last section of the constitution document, after Art. XII.

**Rationale**:
- Art. XII defines the *procedure*; the amendment record is the *history*. Keeping them separate preserves Art. XII's procedural text as an immutable rule (per REQ-DOCS-064 non-modification constraint) while allowing the history to grow.
- A named section is more discoverable and easier to link from cross-reference footers.
- Pattern is consistent with formal constitutional documents that separate procedure (the article) from history (an appendix-style section).
- Apply constraint: the Art. XII body text MUST be byte-identical before and after apply.

### 2.2 OQ-9 — ADR template filename

**Options considered**:
1. `docs/adr/_template.md` — underscore-prefixed, sorts first in most file browsers, convention used in some projects to mark meta-files.
2. `docs/adr/0000-template.md` — numeric prefix, fits the ADR naming convention, explicitly reserves slot 0000.

**Chosen option**: **`docs/adr/_template.md`**

**Rationale**:
- The spec (§3.4, §13 A-6) already lists `_template.md` as the primary name and notes `0000-template.md` is a cosmetic alternative.
- Using `_template.md` prevents the template from appearing in the ADR index as a numbered entry, avoiding confusion ("ADR-0000" is not a real ADR — it is a template).
- Alphabetic sort in most tools places `_template.md` first, making it immediately visible as the authoring reference.
- `0000-template.md` adds spurious numeric noise to the index table.
- Apply constraint: the ADR index `docs/adr/README.md` MUST NOT include `_template.md` as an indexed ADR entry.

### 2.3 OQ-10 — Canonical Spanish wording for "language-specific multiword expression"

**Options considered**:
1. `"expresiones multipalabra específicas del idioma"` — long, fully explicit, self-contained.
2. `"expresiones multipalabra por idioma"` — shorter, but "por idioma" is ambiguous (could mean "per language" as in one-per, not "specific to the language").
3. `"multipalabras específicas del idioma"` — drops "expresiones", loses the noun frame.
4. `"unidades fraseológicas específicas del idioma"` — more academic ("fraseológicas") but less accessible.

**Chosen wording**: **`"expresiones multipalabra específicas del idioma"`**

**Rationale**: Option 1 is the most explicit and unambiguous. The phrase already appears in spec.md §5.1 and §7.3 as the working candidate. Length is acceptable inside technical documentation. Options 2–4 sacrifice precision or introduce unfamiliar vocabulary.

**Application map** — every file and the exact form used:

| File | Section | Form used |
|------|---------|-----------|
| `docs/constitution.md` | Preamble (via amendment) | Generalized scope reads: vocabulary in any language → English framed as first-implemented. Art. V.6 post-amendment reading context only; body of Art. V.6 unchanged per REQ-DOCS-064. |
| `docs/product-vision.md` | §10 step 6 | `"Revisa expresiones multipalabra específicas del idioma"` (replaces `"Revisa phrasal verbs"`) |
| `docs/product-vision.md` | §12 item 7 | `"Expresiones multipalabra específicas del idioma"` (replaces `"Phrasal verbs"`) |
| `AGENTS.md` | §4 clause | `"Los phrasal verbs, como instancia inglesa de las expresiones multipalabra específicas del idioma, y las expresiones multipalabra en general deben modelarse separadamente."` (intent; final Spanish prose chosen in apply) |
| `docs/glossary.md` | Abstract MWE entry heading | `"Expresión multipalabra específica del idioma"` (singular, as entry heading) |
| `docs/adr/0008-multi-language-scope.md` | Decision beats | Verbatim `"expresiones multipalabra específicas del idioma"` |
| `docs/adr/0009-mwe-language-specific-instances.md` | Title + all sections | Verbatim `"expresiones multipalabra específicas del idioma"` (Spanish body) / "language-specific multiword expressions" (EN title and EN body) |
| `docs/architecture/architecture-baseline.md` | Committed invariants | EN: "multiword expressions modeled as language-specific instances (phrasal verbs = English instance)" |
| `docs/decisions-log.md` | ADR-0008 and ADR-0009 rows | EN: "abstract category: language-specific multiword expressions" |

**Apply constraint**: Apply MUST use the exact Spanish string `"expresiones multipalabra específicas del idioma"` in all ES artifacts. No synonyms, no abbreviations. In EN artifacts, the equivalent is "language-specific multiword expressions".

---

## 3. Artifact designs (methodology, EN)

### 3.1 `openspec/config.yaml`

**Full key schema** (YAML keys with type and example value):

```
schema: "spec-driven"                  # string, fixed
project: "wheel-of-words"              # string
context: |                             # multiline string block
  Tech stack: Python 3.12+/FastAPI/SQLite/SQLAlchemy/spaCy; React/TypeScript/Vite
  Architecture: Hexagonal (domain/application/infrastructure/api)
  Testing: pytest + Hypothesis + Playwright
  Style: ruff (backend), ESLint/Prettier (frontend)
stack:                                  # object
  backend: "Python 3.12 + FastAPI + SQLAlchemy 2 + Alembic + spaCy"
  frontend: "React + TypeScript + Vite + TanStack Query"
  persistence: "SQLite (MVP)"
  test_runner_backend: "pytest"
  test_runner_frontend: "Vitest + Playwright"
test_commands:                          # object
  backend: "make test-backend"
  frontend: "make test-frontend"
  all: "make test"
  lint: "make lint"
  typecheck: "make typecheck"
persistence_mode: "hybrid"             # enum: engram | openspec | hybrid | none
strict_tdd: true                       # bool
skill_registry_path: ".atl/skill-registry.md"  # string
change_slug_convention: "kebab-case"   # string
rules:                                  # object keyed by phase
  proposal: [...]                      # list of strings
  specs: [...]
  design: [...]
  tasks: [...]
  apply:
    tdd: true
    test_command: "make test"
  verify:
    test_command: "make test"
    build_command: "make lint && make typecheck"
    coverage_threshold: 80
  archive: [...]
```

**Non-negotiable properties**:
- `rules.apply.tdd: true` (constitution Art. II mandate).
- `rules.specs` MUST list: `"Use RFC 2119 keywords (MUST, SHALL, SHOULD, MAY)"`.
- `rules.verify.coverage_threshold: 80` (constitution Art. II target).
- File MUST be parseable by any YAML 1.2 parser (no tabs, no duplicate keys).

**Gitignore-policy comment block** — placement: top of file, before any YAML keys (line 1).

```yaml
# GITIGNORE POLICY (apply when repo is git-initialized):
#   - COMMIT:    openspec/config.yaml  (this file)
#   - COMMIT:    openspec/specs/       (baseline specs)
#   - GITIGNORE: openspec/changes/     (ephemeral SDD planning; re-hydrate from Engram if needed)
```

**Cross-references**: file self-references `.atl/skill-registry.md` via `skill_registry_path` key. No other cross-references required at YAML level.

### 3.2 `.atl/skill-registry.md` — SDD entries addition

**Ordering rule**: alphabetical by skill name, case-insensitive (matching existing file convention, confirmed in spec §8.2).

**Per-entry field format** (columns preserved verbatim):
```
| Skill | Trigger / description | Scope | Path |
```

**Header preservation rule**: The following MUST be byte-identical except `Last updated` date:
- Line 1: `# Skill Registry — wheel-of-words`
- Line 3 (comment): `<!-- Auto-generated by gentle-ai skill-registry refresh... -->`
- `## Sources scanned` section and all 6 source paths.
- `## Contract` section — verbatim.
- `## Loading protocol` section — verbatim.

**SDD entries to add** (11 rows; alphabetical position within existing table):

| Skill | Trigger / description | Scope | Path |
|-------|-----------------------|-------|------|
| `sdd-apply` | Implement SDD tasks from specs and design. Trigger: orchestrator launches apply for one or more change tasks. | user | `/Users/isildur/.config/opencode/skills/sdd-apply/SKILL.md` |
| `sdd-archive` | Archive a completed SDD change by syncing delta specs. | user | `/Users/isildur/.config/opencode/skills/sdd-archive/SKILL.md` |
| `sdd-design` | Create the SDD technical design and architecture approach. | user | `/Users/isildur/.config/opencode/skills/sdd-design/SKILL.md` |
| `sdd-explore` | Explore SDD ideas before committing to a change. | user | `/Users/isildur/.config/opencode/skills/sdd-explore/SKILL.md` |
| `sdd-init` | Initialize SDD context, testing capabilities, registry, and persistence. | user | `/Users/isildur/.config/opencode/skills/sdd-init/SKILL.md` |
| `sdd-onboard` | Walk users through the SDD workflow on the real codebase. | user | `/Users/isildur/.config/opencode/skills/sdd-onboard/SKILL.md` |
| `sdd-propose` | Create an SDD change proposal with intent, scope, and approach. | user | `/Users/isildur/.claude/skills/sdd-propose/SKILL.md` |
| `sdd-spec` | Write SDD delta specs with requirements and scenarios. | user | `/Users/isildur/.config/opencode/skills/sdd-spec/SKILL.md` |
| `sdd-tasks` | Break an SDD change into implementation tasks. | user | `/Users/isildur/.config/opencode/skills/sdd-tasks/SKILL.md` |
| `sdd-verify` | Execute tests and prove implementation matches specs, design, and tasks. | user | `/Users/isildur/.config/opencode/skills/sdd-verify/SKILL.md` |
| `skill-registry` | Index available skills by trigger and path. Trigger: update skills, skill registry, after skill changes. | user | `/Users/isildur/.config/opencode/skills/skill-registry/SKILL.md` |

**Apply constraint**: Final table = original 11 rows + 11 SDD rows = 22 rows total, alphabetically merged. The `Last updated` date updates to `2026-07-16`.

### 3.3 `docs/adr/README.md`

**Section outline**:
```
# ADR index — wheel-of-words
## Status vocabulary
## Numbering convention
## Authoring rules
## Index
```

**Status vocabulary**: exactly 4 statuses, defined in a small table:
- `Proposed` — under consideration; not yet binding.
- `Accepted` — decision is in force.
- `Superseded` — replaced by a later ADR (link required).
- `Deprecated` — no longer applicable (reason required).

**Numbering convention**: global sequential, zero-padded 4-digit (`ADR-NNNN`). Never per-capability-prefix.

**Authoring rules** (must enumerate):
1. Ground the Context in a specific clause or quote from a binding artifact.
2. Decision MUST be a clear, actionable statement — not a description.
3. Status MUST be set at creation; promote via a diff if it changes.
4. Date MUST reflect when the decision was effectively made (historical accuracy > creation date).
5. Consequences MUST enumerate both positives and negatives.
6. One ADR per discrete decision. If decisions are co-dependent, link them.
7. Language: EN (methodology artifact per ADR-0010).

**Index table columns**: `| ADR | Title | Status | Date | Wave |`

### 3.4 `docs/adr/_template.md` (OQ-9 → `_template.md`)

**Field order** (mandatory, in this sequence):
```
# ADR-NNNN — {Title}
**Status**: Proposed | Accepted | Superseded | Deprecated
**Date**: YYYY-MM-DD
## Context
## Decision
## Consequences
### Positive
### Negative
## Alternatives considered
## References
```

**Non-negotiable properties per field**:
- `Status`: one of the four vocabulary values only; no free-form status.
- `Date`: ISO 8601 (YYYY-MM-DD); reflects decision date, not file creation date.
- `Context`: at least one grounding quote or clause reference from a binding artifact (constitution Art. X.Y, AGENTS.md §N, or spec ID).
- `Decision`: active-voice statement ("We adopt X" or declarative "X is the chosen approach").
- `Consequences/Positive`: ≥ 1 bullet.
- `Consequences/Negative`: ≥ 1 bullet (forces honest tradeoff acknowledgment).
- `Alternatives considered`: ≥ 1 named alternative with a one-line rejection reason.
- `References`: ≥ 1 link to the grounding artifact.

**Metadata front-matter policy**: **No YAML front-matter.** Status and Date are inline bold fields, not YAML. This keeps the template readable in any Markdown viewer without front-matter parsing.

### 3.5 Seed ADRs — outline per ADR

#### ADR-0002 — Hexagonal split

- **Filename**: `docs/adr/0002-hexagonal-split.md`
- **Title**: `Hexagonal split into domain / application / infrastructure / api`
- **Status**: Accepted | **Date**: 2026-07-15 | **Wave**: 1
- **Context beats**:
  1. Must mention: AGENTS.md §5 — "El backend se divide en: domain, application, infrastructure, api" (verbatim).
  2. Must mention: Constitution Art. VII.1–4 — domain independence, use-cases in application, adapters for persistence/NLP/import/export, API without business rules.
  3. Must mention: No `code/` directory exists yet (decision precedes implementation).
  4. Must mention: The NLP adapter port enables replacing spaCy without touching domain.
- **Decision beats**:
  1. Backend MUST use four named layers: `domain`, `application`, `infrastructure`, `api`.
  2. Dependency direction: `domain` ← `application` ← `infrastructure`; `api` depends on `application` only.
  3. `domain` has zero framework dependencies (no FastAPI, SQLAlchemy, spaCy imports).
- **Consequences beats**:
  - Positive: Domain purity enables unit testing without infrastructure; NLP and DB are swappable via ports; aligns with constitution Art. VII.
  - Negative: More boilerplate for simple operations; port/adapter boundary requires discipline to maintain.
- **Alternatives beats**:
  1. Flat module structure — rejected: linguistic-domain logic bleeds into infrastructure, making unit tests infrastructure-dependent.
  2. Three-layer (no api separation) — rejected: constitution Art. VII.4 explicitly requires API to be free of business rules.
- **References**: AGENTS.md §5; Constitution Art. VII; `docs/architecture/architecture-baseline.md`.

#### ADR-0003 — TDD mandatory

- **Filename**: `docs/adr/0003-tdd-mandatory.md`
- **Title**: `TDD mandatory with strict RED → GREEN → REFACTOR`
- **Status**: Accepted | **Date**: 2026-07-15 | **Wave**: 1
- **Context beats**:
  1. Must mention: AGENTS.md §3 — RED, GREEN, REFACTOR cycle rules (verbatim).
  2. Must mention: Constitution Art. II.1–4 — each behavior begins with a failing test; implementation is minimum sufficient; refactoring requires green suite.
  3. Must mention: Coverage targets from constitution Art. II (domain/application ≥ 90%, global ≥ 80%).
  4. Must mention: No implementation may precede a failing test.
- **Decision beats**:
  1. Every new behavior MUST begin with a RED test expressing that behavior.
  2. The minimum sufficient implementation is written to turn the test GREEN.
  3. Refactoring is permitted only with a green suite.
  4. Every bug fix MUST add a regression test.
- **Consequences beats**:
  - Positive: Domain invariants are continuously validated; regression safety; forced clarity about expected behavior before implementation.
  - Negative: Higher upfront effort per feature; test infrastructure must be maintained alongside domain code.
- **Alternatives beats**:
  1. Test-after approach — rejected: constitution Art. II.1 explicitly forbids writing implementation before tests.
  2. Property-based testing only — rejected: property tests complement, not replace, behavior-specific unit tests.
- **References**: AGENTS.md §2, §3; Constitution Art. II; `docs/architecture/architecture-baseline.md`.

#### ADR-0004 — SDD + OpenSpec

- **Filename**: `docs/adr/0004-sdd-openspec.md`
- **Title**: `SDD + OpenSpec as the planning method for all features`
- **Status**: Accepted | **Date**: 2026-07-15 | **Wave**: 1
- **Context beats**:
  1. Must mention: AGENTS.md §1 — "Ninguna funcionalidad debe implementarse directamente desde una petición informal." Seven pre-code artifacts listed.
  2. Must mention: Constitution Art. I.1–5 — spec-first, numbered requirements, no confusing decisions with requirements.
  3. Must mention: `openspec/config.yaml` as the bootstrap artifact for agent sessions.
  4. Must mention: `.atl/skill-registry.md` as the skill dispatch table (REQ-DOCS-004).
- **Decision beats**:
  1. All features MUST go through spec → acceptance → plan → test-plan → tasks → traceability before any code.
  2. `openspec/` is the artifact store; Engram is the persistence backend; hybrid mode is active.
  3. Each change results in the full 7-artifact SDD artifact set (explore, proposal, spec, design, tasks, apply, verify, archive).
- **Consequences beats**:
  - Positive: Agents can bootstrap from `openspec/config.yaml` without re-reading the entire repo; traceability is built-in from day one.
  - Negative: Overhead per feature; planning is non-negotiable even for small changes.
- **Alternatives beats**:
  1. Informal task management — rejected: AGENTS.md §1 explicitly forbids implementing from informal requests.
  2. Kanban-only — rejected: no traceability to requirements; DoD cannot be enforced.
- **References**: AGENTS.md §1, §7, §8; Constitution Art. I; `openspec/config.yaml`.

#### ADR-0005 — Local-first

- **Filename**: `docs/adr/0005-local-first.md`
- **Title**: `Local-first processing; no third-party data egress by default`
- **Status**: Accepted | **Date**: 2026-07-15 | **Wave**: 1
- **Context beats**:
  1. Must mention: Constitution Art. IV.4 — "El procesamiento local será la opción predeterminada."
  2. Must mention: Constitution Art. IV.5 — "El contenido completo de una obra no se enviará a terceros sin consentimiento explícito."
  3. Must mention: AGENTS.md §4 — "El texto del libro no debe enviarse a terceros sin consentimiento explícito." and "El procesamiento local será la opción predeterminada."
  4. Must mention: Implication for architecture — NLP adapter must run locally; translation and cloud APIs require explicit consent gate.
- **Decision beats**:
  1. All NLP processing MUST run on the user's machine by default.
  2. Sending book content to any third party (including cloud NLP or translation APIs) MUST require explicit user consent per constitution Art. IV.5.
  3. Architecture baseline MUST name local-first as a committed invariant.
- **Consequences beats**:
  - Positive: Privacy by default; no network dependency for core functionality; aligns with legal invariant in Art. IV.
  - Negative: Heavy NLP models must be bundled or downloaded; no cloud offload without consent UX.
- **Alternatives beats**:
  1. Cloud-first NLP — rejected: violates constitution Art. IV.4–5.
  2. Opt-in local mode — rejected: constitution mandates local as the *default*, not an option.
- **References**: Constitution Art. IV.4–5; AGENTS.md §4; `docs/architecture/architecture-baseline.md`.

#### ADR-0006 — POS-per-occurrence

- **Filename**: `docs/adr/0006-pos-per-occurrence.md`
- **Title**: `POS assigned per occurrence; no single global POS per lemma`
- **Status**: Accepted | **Date**: 2026-07-15 | **Wave**: 1
- **Context beats**:
  1. Must mention: Constitution Art. V.2 — "Un lema puede tener múltiples categorías gramaticales."
  2. Must mention: Constitution Art. V.3 — "La categoría se registra por aparición y se agrega posteriormente."
  3. Must mention: AGENTS.md §4 — "No asignar necesariamente una única categoría gramatical global a cada lema. Conservar la categoría de cada aparición."
  4. Must mention: Domain entities `Occurrence` and `PartOfSpeech` (from `docs/architecture/overview.md` §4).
- **Decision beats**:
  1. POS is stored as a property of each `Occurrence`, not of the `Lexeme`/`Lema`.
  2. Aggregated POS distributions are derived (computed), not stored as ground truth.
  3. The domain model MUST distinguish `WordForm`, `Lexeme`, `Occurrence`, and contextual `PartOfSpeech` as separate concepts.
- **Consequences beats**:
  - Positive: Accurate handling of words with multiple POS (e.g., "run" as noun/verb); supports literary corpus where context shifts POS frequently.
  - Negative: More storage per occurrence; aggregation queries are required to compute global POS distribution.
- **Alternatives beats**:
  1. Single global POS per lemma — rejected: constitution Art. V.2 explicitly forbids it.
  2. POS on `WordForm` only — rejected: same occurrence might appear in multiple forms; POS belongs to the occurrence event, not the normalized form.
- **References**: Constitution Art. V.2–3; AGENTS.md §4; `docs/glossary.md`; `docs/architecture/architecture-baseline.md`.

#### ADR-0007 — Manual corrections precedence

- **Filename**: `docs/adr/0007-manual-corrections-precedence.md`
- **Title**: `Manual corrections take precedence and survive reprocessing`
- **Status**: Accepted | **Date**: 2026-07-16 | **Wave**: 2
- **Context beats**:
  1. Must mention: Constitution Art. V.8 — "Una corrección manual prevalece sobre el resultado automático."
  2. Must mention: Constitution Art. V.9 — "El reprocesamiento no borra silenciosamente correcciones manuales."
  3. Must mention: AGENTS.md §4 — "Las correcciones manuales prevalecen sobre resultados automáticos." and "El reprocesamiento nunca debe sobrescribir silenciosamente una corrección manual."
  4. Must mention: Domain entity `ManualCorrection` and its role in the processing pipeline (from `docs/architecture/overview.md` §4).
  5. Must mention: OQ-1 (manual-corrections UX day-one vs deferred) is still open — this ADR records the *invariant*, not the UX shape.
- **Decision beats**:
  1. Any `ManualCorrection` entity MUST take precedence over NLP automatic results for the same field.
  2. A reprocessing run MUST check for existing `ManualCorrection` records and preserve them; it MUST NOT overwrite any field that has a manual correction.
  3. Provenance metadata (source, version, date, confidence) MUST be stored for all automatic results to enable auditability.
- **Consequences beats**:
  - Positive: User corrections are durable; trust in the system is preserved; constitution Art. V.8–9 satisfied.
  - Negative: Reprocessing logic is more complex; requires a correction-check step per field; correction UX is deferred (OQ-1 open).
- **Alternatives beats**:
  1. Last-write-wins (reprocessing overwrites everything) — rejected: violates constitution Art. V.9.
  2. Manual corrections stored as flags only — rejected: flags are ambiguous; a `ManualCorrection` entity captures the corrected value, not just the flag.
- **References**: Constitution Art. V.7–9; AGENTS.md §4; `docs/glossary.md` (corrección manual, reprocesamiento, procedencia).

#### ADR-0008 — Multi-language scope

- **Filename**: `docs/adr/0008-multi-language-scope.md`
- **Title**: `Multi-language support scope from day one (three-part decision)`
- **Status**: Accepted | **Date**: 2026-07-16 | **Wave**: 2
- **Context beats**:
  1. Must mention: Constitution preamble v1.0.0 scoped to "vocabulario inglés" — the original English-only framing.
  2. Must mention: Constitution amendment v2.0.0 (this cycle) — scope generalized; English framed as first-implemented language.
  3. Must mention: Three distinct sub-decisions being codified simultaneously (see Decision beats).
  4. Must mention: Language detection strategy, NLP library selection per language, and translation provider are **deferred** (OQ-2, OQ-3, OQ-4).
  5. Must mention: "Lee literatura en el idioma que estudia" as the user-targeting principle replacing "lee literatura en inglés".
- **Decision beats** (three-part thesis, must cover all three):
  1. **Part (a) — Corpus scope**: Books analyzed by the application MAY be in any human language legally provided by the user. The system is not restricted to English-language corpora.
  2. **Part (b) — User targeting**: The target user is defined as "persona que lee literatura en el idioma que estudia" — defined by study intent, not by a specific language. English is the first-implemented language; other languages are enabled by future NLP adapter additions.
  3. **Part (c) — Abstract MWE category**: Language-specific linguistic phenomena (phrasal verbs in English, locuciones/perífrasis verbales in Spanish, Trennbare Verben in German) are modeled as instances of an abstract category "language-specific multiword expressions" (`mwe_kind` field), not as language-named entities in the domain schema.
- **Consequences beats**:
  - Positive: Architecture is multi-language by design; adding a new language requires only a new NLP adapter, not schema changes; user targeting is inclusive.
  - Negative: Language detection (OQ-2), per-language NLP selection (OQ-4), and translation consent model (OQ-3) are deferred and must be resolved before multi-language slices are implemented.
- **Alternatives beats**:
  1. English-only forever — rejected: limits product to a subset of potential users; the architecture supports multi-language at no extra cost.
  2. Language-named MWE entities (e.g., `PhrasalVerb` as a domain type) — rejected: would require schema changes per new language; the abstract `MWE` with `mwe_kind` is language-agnostic.
- **References**: Constitution preamble v2.0.0; AGENTS.md §4 (post-amendment); ADR-0009; `docs/glossary.md` (expresión multipalabra específica del idioma).

#### ADR-0009 — Multiword expressions as language-specific instances

- **Filename**: `docs/adr/0009-mwe-language-specific-instances.md`
- **Title**: `Multiword expressions as language-specific instances`
- **Status**: Accepted | **Date**: 2026-07-16 | **Wave**: 2
- **Special ADR (retitled)**: Title MUST be exactly "Multiword expressions as language-specific instances" (A-8 re-scan confirmed no conflict).
- **Context beats**:
  1. Must mention: Constitution Art. V.6 (current) — "Los phrasal verbs se modelan como expresiones multipalabra." — this is the pre-amendment reading; post-amendment reads as the English-specific instance.
  2. Must mention: ADR-0008 Part (c) — abstract MWE category decision.
  3. Must mention: AGENTS.md §4 pre-amendment: "Los phrasal verbs y expresiones multipalabra deben modelarse separadamente."
  4. Must mention: `mwe_kind` field in the domain model (string, language-specific value, e.g., `"phrasal_verb"`, `"locución_verbal"`, `"trennbares_verb"`).
  5. Must mention: MWEs remain first-class entities, separate from single-word lemmas — the separate-modeling rule is preserved.
- **Decision beats**:
  1. The domain model uses an abstract `MultiwordExpression` entity (already listed in `docs/architecture/overview.md` §4) with a `mwe_kind` field that stores the language-specific type.
  2. Phrasal verbs are the English instance of this abstraction; `mwe_kind = "phrasal_verb"` for English corpora.
  3. Spanish corpora use `mwe_kind` values for locuciones verbales and perífrasis verbales; German corpora use values for Trennbare Verben.
  4. `MultiwordExpression` entities are stored separately from `Lexeme`/`WordForm` entities — single-word lemma modeling is unaffected.
- **Consequences beats**:
  - Positive: Schema is language-agnostic; `mwe_kind` extends per language without schema changes; OQ-10 wording is consistently applied; constitution Art. V.6 post-amendment reading is codified.
  - Negative: `mwe_kind` requires per-language taxonomy maintenance; detection heuristics are language-specific and must be implemented per NLP adapter.
- **Alternatives beats**:
  1. Separate entity types per language (`PhrasalVerb`, `LocucionVerbal`) — rejected: requires schema migrations per new language; violates ADR-0008 Part (c).
  2. Treating MWEs as multi-token `Lexeme` aggregations only — rejected: loses the semantic distinction between the MWE as a lexical unit and its component tokens.
- **References**: Constitution Art. V.6; ADR-0008; AGENTS.md §4 (post-amendment); `docs/glossary.md` (expresión multipalabra específica del idioma, phrasal verb); `docs/architecture/overview.md` §4 (`MultiwordExpression` entity).

#### ADR-0010 — Documentation language policy

- **Filename**: `docs/adr/0010-documentation-language-policy.md`
- **Title**: `Documentation language policy: methodology EN, product-facing ES`
- **Status**: Accepted | **Date**: 2026-07-16 | **Wave**: 2
- **Context beats**:
  1. Must mention: Pre-change state — all docs (AGENTS.md, constitution, ADRs, specs) written in Spanish; SDD tooling defaults to English.
  2. Must mention: Unresolved tension identified in exploration §1.4 — no file declared a documentation language policy.
  3. Must mention: Language-policy split decision made during this cycle (as user decision, locked).
  4. Must mention: Two artifact families with different audiences.
- **Decision beats**:
  1. Methodology artifacts — consumed by agents, tooling, and developers — default to **English**: SDD/OpenSpec config, ADRs, architecture-baseline, decisions-log, traceability-matrix, skill-registry.
  2. Product-facing artifacts — consumed by the product owner/user — stay in **Spanish**: constitution, product-vision, glossary, definition-of-done, README.
  3. `AGENTS.md` is classified as ES (existing contract; amendments preserve ES).
  4. Mixed artifacts (e.g., traceability matrix scaffold in EN, rows may reference ES requirement IDs) follow the scaffold language.
- **Consequences beats**:
  - Positive: Clear, enforced rule; no bilingual drift in individual files; ADR-0010 itself is the self-referential proof that the policy works.
  - Negative: The EN/ES boundary must be actively enforced; future contributors must read ADR-0010 before adding docs.
- **Alternatives beats**:
  1. All-Spanish — rejected: SDD tooling is English-first; methodology artifacts in ES add friction for agents.
  2. All-English — rejected: product-facing artifacts are already in Spanish and the audience is the Spanish-speaking user/owner.
- **References**: `openspec/config.yaml` (persistence_mode, language contract); proposal §5 language mapping; `docs/adr/README.md` (EN policy); `docs/glossary.md` (ES policy).

### 3.6 `docs/architecture/architecture-baseline.md`

**Section outline**:
```
# Architecture Baseline — wheel-of-words
**Date**: 2026-07-16
**Status**: Committed
## Purpose
## Committed invariants
## System context diagram (Mermaid)
## Hexagonal layers diagram (Mermaid)
## Linguistic data flow diagram (Mermaid)
## What is deferred
## References
```

**Relationship to `docs/architecture/overview.md`**:
- `overview.md` is the living, forward-looking architecture doc (updated as decisions evolve).
- `architecture-baseline.md` is a committed-state snapshot: "as of 2026-07-16, this is what we have decided and will not change without an ADR."
- The baseline is a subset — it names what is *committed*; the overview may include aspirational elements.
- Both MUST link to each other (cross-reference network §6).

**Committed invariants section**: MUST enumerate exactly these invariants (per REQ-DOCS-018), each with a grounding §pointer:

| Invariant | Grounding |
|-----------|-----------|
| Local-first processing | Constitution Art. IV.4–5; ADR-0005 |
| Hexagonal split: domain / application / infrastructure / api | AGENTS.md §5; Constitution Art. VII.1–4; ADR-0002 |
| SQLite as MVP persistence (replaceable via SQLAlchemy port) | ADR-0001 |
| spaCy as first NLP adapter (replaceable via `LinguisticAnalyzer` port) | ADR-0001; overview.md §8 |
| Manual corrections take precedence; reprocessing is non-destructive | Constitution Art. V.8–9; ADR-0007 |
| POS assigned per occurrence; no single global POS per lemma | Constitution Art. V.2–3; ADR-0006 |
| Multiword expressions modeled as language-specific instances; phrasal verbs are the English instance; MWEs separate from single-word lemmas | Constitution Art. V.6; ADR-0008; ADR-0009 |
| Automatic results store provenance (source, version, date, confidence) | Constitution Art. V.7; AGENTS.md §4 |
| Linguistic rules MUST NOT be duplicated in the frontend | Constitution Art. VII.5; AGENTS.md §5 |

**Three Mermaid diagrams** — content contract for apply:

**Diagram 1 — System context**:
- Title: `System context — Wheel Vocabulary`
- Diagram type: `C4Context` or `flowchart LR`
- Nodes: `User`, `WheelVocabulary [Web App]`, `LocalStorage [SQLite]`, `NLPAdapter [spaCy]`, `AnkiExport`
- Edges: `User -->|imports .txt/.epub| WheelVocabulary`, `WheelVocabulary -->|reads/writes| LocalStorage`, `WheelVocabulary -->|calls| NLPAdapter`, `WheelVocabulary -->|exports .csv/.apkg| AnkiExport`
- External boundary node: `ThirdPartyAPI [Cloud NLP/Translation]` with edge labeled `REQUIRES explicit consent (Art. IV.5)` from `WheelVocabulary`
- Grouping: User and exported artifacts outside system boundary; all processing inside.

**Diagram 2 — Hexagonal layers**:
- Title: `Hexagonal architecture — backend layers`
- Diagram type: `flowchart TD` with subgraphs
- Nodes: `domain [Domain — Lexeme, Occurrence, MWE, ManualCorrection]`, `application [Application — use cases]`, `infrastructure [Infrastructure — SQLAlchemy, spaCy, TXT/EPUB extractors, Anki exporter]`, `api [API — FastAPI, OpenAPI]`, `frontend [Frontend — React/TypeScript]`
- Edges: `api --> application`, `application --> domain`, `infrastructure --> domain [via ports]`, `api -.->|OpenAPI contract| frontend`
- Grouping: `domain` in core subgraph; `infrastructure` and `api` in outer ring subgraph.
- Annotation: "domain has ZERO framework imports" (comment node or label).

**Diagram 3 — Linguistic data flow**:
- Title: `Linguistic data flow — form to occurrence`
- Diagram type: `flowchart LR`
- Nodes: `RawText`, `Token [token]`, `TextForm [forma textual]`, `NormalizedForm [forma normalizada]`, `Lemma [lema]`, `Occurrence [aparición + POS contextual]`, `MWE [expresión multipalabra específica del idioma]`, `ManualCorrection [corrección manual]`
- Edges: `RawText -->|tokenize| Token`, `Token -->|extract| TextForm`, `TextForm -->|normalize| NormalizedForm`, `NormalizedForm -->|lemmatize| Lemma`, `Lemma + context -->|record| Occurrence`, `Occurrence -->|POS tag| Occurrence`, `Occurrence -->|detect if MWE| MWE`, `ManualCorrection -->|overrides| Occurrence`
- Annotation on MWE node: `mwe_kind = "phrasal_verb" | "locución_verbal" | ...`
- Annotation on Occurrence edge from ManualCorrection: `Art. V.8: manual prevails`

### 3.7 `docs/decisions-log.md`

**Column definition**:
```
| Date | Decision | Category | Ref | Motivation | Consequences |
```

**Chronological ordering rule**: ascending by date; within same date, group by category (governance → architecture → linguistic-model → methodology → product).

**Seed entries** (26 total, chronological):

| Date | Decision | Category | Ref |
|------|----------|----------|-----|
| 2026-07-15 | Constitution v1.0.0 adopted | governance | `docs/constitution.md` |
| 2026-07-15 | ADR-0001: Monorepo + Python/FastAPI/SQLite/React/Vite stack | architecture | `docs/adr/0001-monorepo-and-stack.md` |
| 2026-07-15 | SPEC-001 DEC-001: React with Vite (no SSR, no Node backend) | product | `specs/001-project-foundation/decisions.md` |
| 2026-07-15 | SPEC-001 DEC-002: SQLite as MVP persistence | architecture | `specs/001-project-foundation/decisions.md` |
| 2026-07-15 | SPEC-001 DEC-003: FastAPI factory pattern | architecture | `specs/001-project-foundation/decisions.md` |
| 2026-07-15 | SPEC-001 DEC-004: OpenAPI as backend-frontend contract | architecture | `specs/001-project-foundation/decisions.md` |
| 2026-07-15 | SPEC-001 DEC-005: No fictitious domain in SPEC-001 | product | `specs/001-project-foundation/decisions.md` |
| 2026-07-15 | SPEC-001 DEC-006: Docker Compose optional | architecture | `specs/001-project-foundation/decisions.md` |
| 2026-07-15 | ADR-0002: Hexagonal split into 4 layers | architecture | `docs/adr/0002-hexagonal-split.md` |
| 2026-07-15 | ADR-0003: TDD mandatory (RED → GREEN → REFACTOR) | methodology | `docs/adr/0003-tdd-mandatory.md` |
| 2026-07-15 | ADR-0004: SDD + OpenSpec as planning method | methodology | `docs/adr/0004-sdd-openspec.md` |
| 2026-07-15 | ADR-0005: Local-first processing; no third-party egress by default | architecture/privacy | `docs/adr/0005-local-first.md` |
| 2026-07-15 | ADR-0006: POS assigned per occurrence; no single global POS per lemma | linguistic-model | `docs/adr/0006-pos-per-occurrence.md` |
| 2026-07-16 | ADR-0007: Manual corrections take precedence; reprocessing is non-destructive | linguistic-model | `docs/adr/0007-manual-corrections-precedence.md` |
| 2026-07-16 | ADR-0008: Multi-language scope — three-part: any-language corpora, user-targeting-by-study-language, abstract MWE category | product/architecture | `docs/adr/0008-multi-language-scope.md` |
| 2026-07-16 | ADR-0009: Multiword expressions as language-specific instances; mwe_kind field; phrasal verbs = English instance | linguistic-model | `docs/adr/0009-mwe-language-specific-instances.md` |
| 2026-07-16 | ADR-0010: Documentation language policy — methodology EN, product-facing ES | methodology | `docs/adr/0010-documentation-language-policy.md` |
| 2026-07-16 | Constitution amended to v2.0.0 (MAJOR): multi-language scope, approval date, four-file coordinated payload | governance | `docs/constitution.md §Registro de enmiendas` |
| 2026-07-16 | Engineering Playbook deferred; revisit trigger: "After first vertical slice ships end-to-end (upload a .txt file and view a lemma list with frequency)" | methodology | `openspec/changes/docs-methodology-overhaul/proposal.md §4` |
| 2026-07-16 | Language policy for products-facing artifacts: ES; for methodology: EN | methodology | `docs/adr/0010-documentation-language-policy.md` |
| 2026-07-16 | ADR template filename: `_template.md` (not `0000-template.md`) | methodology | design OQ-9 |
| 2026-07-16 | Amendment log placement: new `## Registro de enmiendas` section after Art. XII | governance | design OQ-8 |
| 2026-07-16 | Canonical ES wording for language-specific MWE: "expresiones multipalabra específicas del idioma" | linguistic-model | design OQ-10 |
| 2026-07-16 | SPEC-001 traceability matrix seeded with REQ-001-001 as worked example (non-Pendiente) | methodology | `docs/traceability-matrix.md` |
| 2026-07-16 | docs-methodology-overhaul SDD cycle executed | governance | `openspec/changes/docs-methodology-overhaul/` |
| 2026-07-16 | OpenSpec gitignore advisory: commit config.yaml and specs/; gitignore changes/ | methodology | `openspec/config.yaml` (comment block) |

### 3.8 `docs/traceability-matrix.md`

**Column definition** (verbatim from spec §6.1):

| Column | Type | Description |
|--------|------|-------------|
| REQ-ID | string | `REQ-<feature>-<n>` identifier |
| Criterio de aceptación | string | AC-ID reference or inline Given/When/Then |
| Archivo(s) de prueba | string | Path(s) to test file(s) or test-IDs |
| Tarea(s) | string | T-ID reference(s) |
| Estado | enum | `Pendiente` \| `En progreso` \| `Pasando` \| `Bloqueado` \| `Obsoleto` |

**Update-rules subsection** (§ "Reglas de actualización" intent, 5 rules):
1. Add a row when a new `REQ-<feature>-<n>` is created.
2. Update `Estado` when the corresponding task closes.
3. Move `Estado` to `Obsoleto` — do NOT delete — when a requirement is superseded.
4. `Bloqueado` requires a linked reason in the same row.
5. Row ownership: the person/agent closing the referenced task is responsible for the update.

**5 seed rows** chosen from SPEC-001 (from `specs/001-project-foundation/traceability.md`):

| REQ-ID | Criterio de aceptación | Archivo(s) de prueba | Tarea(s) | Estado |
|--------|------------------------|----------------------|----------|--------|
| REQ-001-001 | AC-001 | `tests/api/test_health.py::test_health_endpoint` | T014–T016 | Pendiente |
| REQ-001-002 | AC-001 | `tests/unit/test_backend_startup.py`, `tests/api/test_health.py` | T012–T016 | Pendiente |
| REQ-001-007 | AC-007 | `tests/unit/test_domain_purity.py` | T004–T010 | Pendiente |
| REQ-DOCS-004 | AC-004 | (manual review of `.atl/skill-registry.md` diff) | (Wave-A tasks from this change) | **Pasando** |
| REQ-DOCS-001 | AC-001 | (manual: `python -c "import yaml; yaml.safe_load(open('openspec/config.yaml'))"`) | (Wave-A tasks) | Pendiente |

**Non-Pendiente row rationale**: `REQ-DOCS-004` is set to `Pasando` to demonstrate the update workflow, as required by REQ-DOCS-042. It will be updated to `Pasando` after the skill-registry apply task closes.

**DoD gate wording for AGENTS.md §10** (verbatim Spanish, from spec §6.4):
```
- La matriz de trazabilidad se ha actualizado con los identificadores de requisito, criterio de aceptación, prueba y tarea correspondientes.
```

---

## 4. Artifact designs (product-facing, ES design contract in EN)

### 4.1 `docs/glossary.md`

**Section outline**:
```
# Glosario del dominio lingüístico
## Cómo usar este glosario
## Categorías
## Términos
```

**Entry template** (each term as an `###` heading):
```
### <Término en español>

**Categoría**: concepto | entidad | atributo | proceso | relación
**Definición**: [one-line, complete sentence, in Spanish]
**Referencias**: [at least one link to AGENTS.md §N, constitution Art. V.X, ADR, or spec]
**Impacto multiidioma**: [language-agnostic | language-specific — one sentence]
```

**Grouping**: alphabetical within the `## Términos` section. No sub-grouping by category (category is a field in the entry, not a navigation section) — keeps the glossary flat and easy to scan.

**13 canonical entries** (design contract per spec §5.1):

| Term (ES) | Category | One-line definition intent | Key cross-refs | Multi-language note |
|-----------|----------|---------------------------|----------------|---------------------|
| Aparición | entity | Individual instance of a form/lemma at a specific position in text; carries contextual POS. | AGENTS.md §4; Constitution Art. V.3 | Language-agnostic |
| Categoría gramatical contextual | attribute | POS assigned to a specific occurrence, not to the lemma globally; aggregated after storage. | AGENTS.md §4; Constitution Art. V.2–3; ADR-0006 | Tagsets vary by language and NLP model |
| Corrección manual | process | User adjustment that overrides the automatic result for a field; durable across reprocessing. | AGENTS.md §4; Constitution Art. V.8; ADR-0007 | Language-agnostic |
| **Expresión multipalabra específica del idioma** (abstract entry) | entity (abstract) | Abstract category for language-specific multi-token lexical units, instantiated via `mwe_kind`. Examples: phrasal verbs (English), locuciones and perífrasis verbales (Spanish), Trennbare Verben (German). | AGENTS.md §4 (post-amendment); Constitution Art. V.6; ADR-0008; ADR-0009 | Abstract; instances are language-specific |
| Expresión multipalabra | entity | General lexical unit composed of 2+ tokens treated as a single lemma. The abstract entry above is a linguistic specialization. | AGENTS.md §4; Constitution Art. V.6 | Language-agnostic pattern; instances are language-specific |
| Forma normalizada | attribute | String after deterministic normalization is applied to the text form. | AGENTS.md §4; Constitution Art. V.1 | Normalization rules are language-specific |
| Forma textual | attribute | Exact string as it appears in the original text, without transformation. | AGENTS.md §4; Constitution Art. V.1 | Language-agnostic |
| Lema | entity | Canonical form that groups equivalent inflected forms; the lookup form in a dictionary. | AGENTS.md §4; Constitution Art. V.1, V.4 | Lemmatization models are language-specific |
| Phrasal verb (instancia inglesa) | entity (instance) | Verb composed of a base verb + particle(s); the English instance of "expresión multipalabra específica del idioma". | AGENTS.md §4; Constitution Art. V.6; ADR-0009 | English-specific instance of the abstract MWE entry |
| Procedencia | attribute | Metadata recording source, version, date, and confidence of an automatic result. | AGENTS.md §4; Constitution Art. V.7 | Language-agnostic |
| Puntuación de confianza | attribute | Numeric certainty level for an uncertain automatic result. | AGENTS.md §4; Constitution Art. V.7 | Language-agnostic |
| Reprocesamiento | process | Re-execution of the NLP pipeline; MUST NOT silently overwrite manual corrections. | AGENTS.md §4; Constitution Art. V.9; ADR-0007 | Language-agnostic |
| Token | concept | Primary lexical unit extracted during tokenization, prior to normalization. | AGENTS.md §4; Constitution Art. V.1 | Language-agnostic; segmentation rules vary by language |

**Abstract-MWE entry specifics** (OQ-10 wording baked in):
- Heading: `### Expresión multipalabra específica del idioma`
- Category: `entidad (abstracta)`
- Definition intent: Names the abstract category; lists English (phrasal verbs), Spanish (locuciones/perífrasis verbales), German (Trennbare Verben) as **named instances**, not as peer concepts.
- References: AGENTS.md §4 (post-amendment), constitution Art. V.6, ADR-0008, ADR-0009.
- The `Phrasal verb` entry MUST read: "Instancia inglesa de la expresión multipalabra específica del idioma. Ver también: Expresión multipalabra específica del idioma."

### 4.2 `docs/definition-of-done.md`

**Section outline**:
```
# Definición de Terminado — Wheel Vocabulary
## Alcance y jerarquía
## Criterios de terminado (referencia constitución Art. XI)
## Criterios operativos (referencia AGENTS.md §10)
## Puerta de trazabilidad
## Referencias
```

**Content intent per section**:
- `## Alcance y jerarquía`: 1-paragraph intro. MUST contain the explicit sentence: "La Constitución Art. XI es la fuente canónica en caso de conflicto entre este documento y cualquier otra definición."
- `## Criterios de terminado`: Quote or paraphrase constitution Art. XI — but NOT verbatim copy of the full article text (per REQ-DOCS-052). Must link to `docs/constitution.md#artículo-xi`.
- `## Criterios operativos`: Reference or quote AGENTS.md §10 items as a checklist. MUST include the traceability-matrix bullet (per REQ-DOCS-043): `"La matriz de trazabilidad se ha actualizado con los identificadores de requisito, criterio de aceptación, prueba y tarea correspondientes."`. Must link to `AGENTS.md#10-definición-de-terminado`.
- `## Puerta de trazabilidad`: 1-2 sentences reminding that the traceability matrix is a hard DoD gate; link to `docs/traceability-matrix.md`.
- `## Referencias`: Links to `docs/constitution.md`, `AGENTS.md`, `docs/traceability-matrix.md`.

**Language**: ES throughout.
**Apply constraint**: This file MUST NOT duplicate the full article text of constitution Art. XI verbatim — reference and quote are acceptable; copy-paste is not.

---

## 5. Amendment payload — diff intents (v1.0.0 → v2.0.0 MAJOR)

### 5.1 `docs/constitution.md`

**Header block** (lines 1–5):

| Location | Current (verbatim) | Diff intent | Language |
|----------|-------------------|-------------|----------|
| Line 3 | `**Versión:** 1.0.0` | Change to `**Versión:** 2.0.0` | ES |
| Line 4 | `**Estado:** Aprobada para el inicio del proyecto` | Add new line below: `**Fecha de aprobación:** 2026-07-15` | ES |

**Preamble** (lines 7–11):

| Location | Current (verbatim) | Diff intent | Language |
|----------|-------------------|-------------|----------|
| Line 9 | `"Wheel Vocabulary es una aplicación web destinada a extraer, clasificar, consultar y estudiar vocabulario inglés procedente de obras literarias aportadas legalmente por el usuario."` | New wording MUST: (a) preserve subject `"Wheel Vocabulary es una aplicación web"`, (b) remove `"inglés"` as a scope qualifier for the vocabulary, (c) frame the vocabulary as being in the language the user studies, (d) mention English as the first-implemented language (factual continuity), (e) keep `"obras literarias aportadas legalmente por el usuario"`. Final ES wording chosen by apply. | ES |

**Amendment record** (new section at end of file, after Art. XII):

| Location | Current | Diff intent | Language |
|----------|---------|-------------|----------|
| After Art. XII (end of file) | Nothing | Add new `## Registro de enmiendas` section with a Markdown table. First row: Date=2026-07-16, Cambio=summary from spec §7.2, Motivación=spec §7.2, Consecuencias=spec §7.2 (4 items), Versión anterior=1.0.0, Versión nueva=2.0.0. | ES |

**Cross-reference footer** (after amendment record):
Add `## Referencias` section linking to: `docs/adr/README.md`, `docs/architecture/architecture-baseline.md`, `docs/glossary.md`, `docs/definition-of-done.md`.

**Explicit non-modifications** (REQ-DOCS-064): Art. I, II, III, IV, V, VI, VII, VIII, IX, X, XI body text — zero changes. Art. XII body text — zero changes (only `## Registro de enmiendas` appended below).

### 5.2 `docs/product-vision.md`

| Location | Current (verbatim) | Diff intent | Language |
|----------|-------------------|-------------|----------|
| §4 line 21 | `"Persona adulta que lee literatura en inglés, desea ampliar vocabulario, usa o puede usar Anki, valora la precisión lingüística y quiere conservar el control sobre sus archivos."` | Replace `"en inglés"` with `"en el idioma que estudia"`. All other attributes of the user persona remain identical. Final ES wording chosen by apply. | ES |
| §10 step 6 line ~113 | `"6. Revisa phrasal verbs."` | Replace `"phrasal verbs"` with `"expresiones multipalabra específicas del idioma"` (OQ-10 canonical wording). The step number (6) and surrounding list items are unchanged. | ES |
| §12 item 7 line ~150 | `"7. Phrasal verbs."` | Replace with `"7. Expresiones multipalabra específicas del idioma."` (OQ-10 canonical wording, title-case). | ES |

**§8 "Fuera de alcance inicial"** (lines 72–83): **EXPLICITLY UNCHANGED**. The full list including "Traducción automática masiva de pago" remains byte-identical. Translation stays out of MVP scope per REQ-DOCS-069.

**Cross-reference footer** (new, additive):
Add `## Referencias` section at end of file linking to: `docs/constitution.md`, `docs/glossary.md`.

**Unchanged sections**: §1, §2, §3, §5, §6, §7, §8, §9, §11 body text — zero changes.

### 5.3 `README.md`

| Location | Current (verbatim) | Diff intent | Language |
|----------|-------------------|-------------|----------|
| Line 3 | `"Este paquete define el marco de trabajo para construir una aplicación web de análisis de vocabulario literario en inglés, comenzando por *The Eye of the World* como primer corpus aportado legalmente por el usuario."` | Remove `"en inglés"` as scope qualifier. MUST retain `"comenzando por *The Eye of the World* como primer corpus aportado legalmente por el usuario"` — *The Eye of the World* remains as the named initial corpus. New wording frames the app as multi-language vocabulary analysis (e.g., "en el idioma que estudia el usuario"). Final ES wording chosen by apply. | ES |

**New section** (additive): Add `## Referencias metodológicas` section after the existing `## Siguiente especificación recomendada` section. Links to: `docs/constitution.md`, `AGENTS.md`, `docs/glossary.md`, `docs/adr/README.md`, `docs/definition-of-done.md`.

**Unchanged**: Repo-tree diagram (`## Contenido`), `## Flujo obligatorio` diagram, `## Alcance del paquete` bullets, `## Siguiente especificación recomendada`.

### 5.4 `AGENTS.md`

**§4 amendment** (one clause change):

| Location | Current (verbatim) | Diff intent | Language |
|----------|-------------------|-------------|----------|
| §4 line 77 | `"- Los phrasal verbs y expresiones multipalabra deben modelarse separadamente."` | Rewrite this single bullet to: (a) name phrasal verbs as the English instance of "expresiones multipalabra específicas del idioma" (OQ-10 canonical wording), (b) preserve the separate-modeling rule (MWEs modeled separately from single-word lemmas), (c) make the abstract MWE concept first, phrasal verb as the English instance. Final ES wording chosen by apply. Example intent (not final prose): "Las expresiones multipalabra específicas del idioma — como los phrasal verbs en inglés — deben modelarse separadamente de los lemas de una sola palabra." | ES |

**§10 additive change** (one bullet added):
Add bullet with verbatim text from spec §6.4:
```
- La matriz de trazabilidad se ha actualizado con los identificadores de requisito, criterio de aceptación, prueba y tarea correspondientes.
```

**New `## Referencias` section** (additive, end of file):
Links to (in this order): `docs/constitution.md`, `docs/adr/README.md`, `docs/architecture/architecture-baseline.md`, `docs/glossary.md`, `docs/traceability-matrix.md`, `docs/definition-of-done.md`, `docs/decisions-log.md`.

**Unchanged sections**: §1, §2, §3, §5, §6, §7, §8, §9, §11 body text — zero changes.

### 5.5 Coordination invariant restatement

The four amendment files (`docs/constitution.md`, `docs/product-vision.md`, `README.md`, `AGENTS.md`) MUST land in a **single coordinated apply batch**. Apply MUST write all four in one task group; verify MUST check all four for their respective changes before reporting pass. If any of the four is missing its change, verify MUST report failure. This is a hard constraint per REQ-DOCS-06B.

**Cross-language consistency check after apply**: After the four files are written, apply MUST re-scan for residual "inglés" as a sole scope claim (same grep as A-7) to confirm zero new occurrences outside the OQ-10 canonicalized contexts.

---

## 6. Cross-reference network

| Source file | Links to | Requirement |
|-------------|----------|-------------|
| `AGENTS.md` | constitution, ADR index, architecture-baseline, glossary, traceability-matrix, definition-of-done, decisions-log | REQ-DOCS-070 |
| `docs/constitution.md` | ADR index, architecture-baseline, glossary, definition-of-done | REQ-DOCS-071 |
| `docs/product-vision.md` | constitution, glossary | REQ-DOCS-072 |
| `docs/architecture/overview.md` | architecture-baseline, ADR index | REQ-DOCS-073 |
| `README.md` | constitution, AGENTS.md, glossary, ADR index, definition-of-done | REQ-DOCS-074 |
| `docs/adr/README.md` | constitution, architecture-baseline, decisions-log | derived REQ-DOCS-010 |
| `docs/adr/*.md` (each ADR) | grounding constitution/AGENTS.md clause, related ADRs, decisions-log | derived REQ-DOCS-013 |
| `docs/architecture/architecture-baseline.md` | ADR index, glossary, overview.md | derived REQ-DOCS-017 |
| `docs/glossary.md` | constitution Art. V, AGENTS.md §4 | derived REQ-DOCS-030 |
| `docs/definition-of-done.md` | constitution Art. XI, AGENTS.md §10, traceability-matrix | derived REQ-DOCS-050 |
| `docs/decisions-log.md` | ADR index (per-row refs), constitution §Registro de enmiendas | derived REQ-DOCS-019 |
| `docs/traceability-matrix.md` | AGENTS.md §10, per-spec traceability files | derived REQ-DOCS-040 |

**Bidirectionality policy**: For every A → B link in the table above, B MUST contain a reciprocal reference to A (per REQ-DOCS-075). Apply is responsible for ensuring bidirectionality; verify MUST check each direction.

---

## 7. Slice-boundary recommendations (input to `sdd-tasks`)

**Refined partition** from proposal §7:

| Slice | Files created/modified | Req IDs satisfied | Est. lines | Dependency | Rationale |
|-------|----------------------|-------------------|------------|------------|-----------|
| **A** — SDD bootstrap | `openspec/config.yaml` (new), `.atl/skill-registry.md` (modified) | REQ-DOCS-001–006 | ~120 | None | Bootstrap first; agents need config and registry for all subsequent phases |
| **B** — ADR + architecture commitment (Wave 1) | `docs/adr/README.md` (new), `docs/adr/_template.md` (new), `docs/adr/0002`–`0006` (new 5 ADRs, Wave 1), `docs/decisions-log.md` (new, partial — Wave 1 entries only) | REQ-DOCS-010–016 (Wave 1), REQ-DOCS-019–020 (partial) | ~500–600 | Slice A complete | ADR infrastructure before ADR content; Wave 1 foundational ADRs before Wave 2 contextual ones |
| **C** — ADR Wave 2 + domain legibility + architecture baseline | `docs/adr/0007`–`0010` (new 4 ADRs, Wave 2), `docs/architecture/architecture-baseline.md` (new), `docs/glossary.md` (new), decisions-log Wave 2 entries appended | REQ-DOCS-013–018 (Wave 2), REQ-DOCS-019–021 (complete), REQ-DOCS-030–034 | ~700–900 | Slice B complete (decisions-log Wave 1 rows must exist before Wave 2 appended; ADR-0008/0009 depend on ADR-0005/0006 for cross-refs) | Contextual ADRs depend on foundational ones for cross-references; baseline references all ADRs |
| **D** — Traceability, DoD, cross-references | `docs/traceability-matrix.md` (new), `docs/definition-of-done.md` (new), `docs/architecture/overview.md` (cross-ref footer added) | REQ-DOCS-040–044, REQ-DOCS-050–052, REQ-DOCS-073, REQ-DOCS-075 (partial) | ~200 | Slice C complete (matrix references ADR files created in C; DoD references glossary from C) | Enforcement layer; cross-refs can only be bidirectional after the target files exist |
| **E** — Amendment payload (4-file coordinated) | `docs/constitution.md` (amended), `docs/product-vision.md` (amended), `README.md` (amended), `AGENTS.md` (amended + §10 bullet + cross-ref footer) | REQ-DOCS-043, REQ-DOCS-060–064, REQ-DOCS-06A–06C, REQ-DOCS-06B, REQ-DOCS-070–075 (remaining) | ~150 | Slices A–D complete (amendment references ADR index, baseline, glossary, traceability-matrix — all must exist) | **Amendment payload MUST be its own slice E** (see below) |

**Amendment payload placement decision**: **Slice E (own slice)**, NOT merged into slice D.

**Rationale**: The coordination invariant (REQ-DOCS-06B) requires all four files to ship atomically. Merging into slice D would couple the amendment's coordination constraint with traceability/DoD work, making partial-apply detection harder. A dedicated slice E:
1. Makes the coordination invariant trivially verifiable (entire slice = the four files).
2. Allows verify to check the four-file completeness as a single gate.
3. Aligns with the spec §7.6 statement: "The apply plan MUST group these four amendments into a single slice."
4. Cross-refs from the amendment files (constitution → ADR index, baseline, glossary; AGENTS.md → traceability-matrix, DoD) can only be bidirectionally complete after slices A–D create the target files.

**Inter-slice dependencies** (enforced ordering):
- Slice B MUST complete before Slice C (decisions-log Wave 1 rows are appended in C).
- Slice C MUST complete before Slice D (traceability-matrix and DoD reference files created in C).
- Slices A–D MUST all complete before Slice E (amendment cross-refs point to files created in A–D).
- Slice A → B → C → D → E is the mandatory execution order.

---

## 8. Assumptions for apply

1. **OQ-10 canonical wording** is `"expresiones multipalabra específicas del idioma"` (§2.3). Apply MUST use this exact string in all ES artifacts and "language-specific multiword expressions" in all EN artifacts. No synonyms.
2. **OQ-8 placement**: `## Registro de enmiendas` is a new section appended after Art. XII, not an inline extension. Apply MUST NOT touch Art. XII body text.
3. **OQ-9 filename**: Template file is `docs/adr/_template.md`. Apply MUST NOT create `docs/adr/0000-template.md`.
4. **§8 product-vision**: Lines 72–83 (`## Fuera de alcance inicial` / "Traducción automática masiva de pago" etc.) are byte-identical before and after apply.
5. **ADR-0001 content**: `docs/adr/0001-monorepo-and-stack.md` body text is byte-identical before and after apply (only cross-ref footer MAY be appended).
6. **Constitution Art. I–XI body text**: Zero modification. Only header lines 3–4, preamble line 9, and the new `## Registro de enmiendas` section are changed.
7. **Skill-registry**: Existing 11 rows are preserved verbatim; the `Last updated` date is bumped to `2026-07-16`; 11 SDD rows are added; alphabetical order is maintained.
8. **Decisions-log**: 26 seed rows defined in §3.7. Engineering Playbook deferral row MUST contain the exact trigger string from REQ-DOCS-021: `"After first vertical slice ships end-to-end (upload a .txt file and view a lemma list with frequency)"`.
9. **Wave assignment in ADR index**: ADR README index column `Wave` MUST show `1` for ADR-0002..0006 and `2` for ADR-0007..0010.
10. **Cross-reference network** (§6): Apply is responsible for ensuring bidirectionality. Every A → B link implies apply also adds B → A.

---

## 9. Open items carried to tasks/apply

- **OQ-1**: Manual-corrections UX (day-one vs deferred) — not resolved by design. ADR-0007 records the invariant; UX shape requires a future decision. Does not block this change.
- **OQ-2**: Language detection strategy — future ADR after first multi-language vertical slice.
- **OQ-3**: Translation provider strategy — future ADR; requires constitution Art. IV.5 consent model.
- **OQ-4**: NLP library selection per language — future ADR.

---

## 10. Threat matrix

N/A — this change creates only documentation and YAML configuration files. No routing, shell commands, subprocesses, VCS/PR automation, executable-file classification, or process-integration boundary is introduced. No threat-matrix rows are applicable.

---

## 11. Skill resolution

| Skill | Status | Role |
|-------|--------|------|
| `_shared` | Loaded (direct read) | Confirmed not invokable; support reference only |
| `sdd-design` | Loaded (direct read as executor) | Governs this phase; design contract rules applied |
| `cognitive-doc-design` | Loaded (direct read) | Applied: lead-with-answer headers (§2, §5), recognition-over-recall tables (§3.5, §3.7), chunking by artifact family, signposting with `###` headings per artifact, progressive disclosure (§3 methodology before §4 product-facing) |

**Skill resolution result**: `paths-injected` — all three skills loaded from exact `SKILL.md` paths. No fallback required.

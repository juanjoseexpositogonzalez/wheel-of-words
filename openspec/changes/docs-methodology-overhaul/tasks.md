# Tasks — Documentation & Methodology Overhaul

## 0. Metadata

| Field | Value |
|-------|-------|
| Change slug | `docs-methodology-overhaul` |
| Capability code | `DOCS` |
| Spec version consumed | 2.0 (Engram #2254) |
| Design version consumed | 1.0 (Engram #2259) |
| Delivery strategy | 5 chained slices (A → B → C → D → E); review budget ≤ 400 lines/slice |
| Amendment coordination invariant | REQ-DOCS-06B: Slice E is atomic; 4 files apply as one work unit — no partial applies allowed |
| TDD mode | Not applicable (no code; acceptance is verifiable by inspection) |
| Total task count | 41 tasks (A:3, B:10, C:9, D:4, E:15) |

---

## 1. Global preconditions

- `openspec/changes/docs-methodology-overhaul/` contains `proposal.md`, `spec.md`, `design.md` — all three must exist before any task runs.
- No uncommitted edits to any of the 23 artifact files listed in spec §2 (sanity check).
- Apply agent has read: spec.md, design.md, and this tasks.md before executing any slice.
- `.atl/skill-registry.md` exists and is readable (it will be modified in Slice A).
- `docs/adr/0001-monorepo-and-stack.md` exists (referenced unchanged in Slice B).
- Design OQ-8/OQ-9/OQ-10 decisions are locked: `## Registro de enmiendas` section, `_template.md` filename, `"expresiones multipalabra específicas del idioma"` wording.

---

## 2. Slice A — SDD/OpenSpec Bootstrap (~120 lines)

### 2.1 Rationale

Slice A gives every subsequent session a cold-start capability: `openspec/config.yaml` lets agents bootstrap SDD context without reading the full repo, and the skill-registry update makes all 11 SDD skills dispatchable. All other slices depend on this foundation being in place.

### 2.2 Deliverables

- `openspec/config.yaml` — new file (REQ-DOCS-001, 002, 003)
- `.atl/skill-registry.md` — modified: 11 SDD rows added (REQ-DOCS-004, 005, 006)

### 2.3 Tasks

**TA01 [SPEC] Create `openspec/config.yaml`**
- File: `openspec/config.yaml`
- Content contract: Design §3.1 (full key schema, non-negotiable properties, gitignore-policy comment block at line 1)
- REQ-DOCS-001, REQ-DOCS-002, REQ-DOCS-003 / AC-001, AC-002, AC-003
- Done when:
  - File exists at `openspec/config.yaml`
  - `python -c "import yaml; yaml.safe_load(open('openspec/config.yaml'))"` exits 0
  - `grep -c "gitignore" openspec/config.yaml` returns ≥ 1
  - Top-level keys present: `project`, `stack`, `test_commands`, `persistence_mode`, `strict_tdd`, `skill_registry_path`, `change_slug_convention`, `rules`
  - `rules.apply.tdd: true`; `rules.specs` contains `"RFC 2119"`; `rules.verify.coverage_threshold: 80`
- Est. lines: ~80

**TA02 [SPEC] Add 11 SDD entries to `.atl/skill-registry.md`**
- File: `.atl/skill-registry.md`
- Content contract: Design §3.2 (11-row entry list, alphabetical merge, header preservation rule, `Last updated` bump to 2026-07-16)
- REQ-DOCS-004, REQ-DOCS-005, REQ-DOCS-006 / AC-004, AC-005, AC-006
- Done when:
  - `grep -c "sdd-" .atl/skill-registry.md` returns ≥ 11
  - All 11 skills from spec §8.1 present with correct absolute paths
  - Previously existing 11 skill rows still present (no deletions)
  - Header auto-generation comment and `## Loading protocol` section byte-identical (except `Last updated` date)
  - Table is alphabetically sorted by skill name
- Est. lines: +22 rows (~44 lines added, table only)

**TA03 [DOC] Verify Slice A completion**
- File: N/A (inspection task)
- Content contract: This tasks.md §2.4 checklist
- REQ-DOCS-001–006 / AC-001–006
- Done when: All four checklist items in §2.4 pass
- Est. lines: 0

### 2.4 Verification checklist for Slice A

- [x] `openspec/config.yaml` exists and parses as valid YAML 1.2
- [x] `grep -c "gitignore" openspec/config.yaml` ≥ 1 (gitignore-policy comment block present)
- [x] `.atl/skill-registry.md` contains all 11 SDD skill entries with correct paths
- [x] `.atl/skill-registry.md` previously existing 11 rows preserved verbatim (except `Last updated` date)

---

## 3. Slice B — Foundational Commitment Layer (~500–600 lines)

### 3.1 Rationale

Slice B establishes the ADR infrastructure (index + template) and the 5 foundational Wave 1 ADRs (decisions already encoded in AGENTS.md §5 and constitution Art. II, IV, V, VII). The decisions-log is created here with Wave 1 entries; Wave 2 entries are appended in Slice C. Slice C's ADR-0008/0009 cross-references depend on the foundational ADRs existing first.

### 3.2 Deliverables

- `docs/adr/README.md` — new (REQ-DOCS-010)
- `docs/adr/_template.md` — new (REQ-DOCS-011)
- `docs/adr/0002-hexagonal-split.md` — new, Wave 1 (REQ-DOCS-013–016)
- `docs/adr/0003-tdd-mandatory.md` — new, Wave 1 (REQ-DOCS-013–016)
- `docs/adr/0004-sdd-openspec.md` — new, Wave 1 (REQ-DOCS-013–016)
- `docs/adr/0005-local-first.md` — new, Wave 1 (REQ-DOCS-013–016)
- `docs/adr/0006-pos-per-occurrence.md` — new, Wave 1 (REQ-DOCS-013–016)
- `docs/decisions-log.md` — new (initial file with Wave 1 entries; Wave 2 appended in Slice C) (REQ-DOCS-019–020 partial)

### 3.3 Tasks

**TB01 [DOC] Create `docs/adr/README.md` — ADR index**
- File: `docs/adr/README.md`
- Content contract: Design §3.3 (section outline, 4-status vocabulary, numbering convention, 7 authoring rules, index table columns `ADR | Title | Status | Date | Wave`)
- REQ-DOCS-010 / AC-010
- Done when:
  - File exists at `docs/adr/README.md`
  - `grep -c "Proposed\|Accepted\|Superseded\|Deprecated" docs/adr/README.md` ≥ 4
  - Index table present with column headers `| ADR | Title | Status | Date | Wave |`
  - 7 authoring rules enumerated
- Est. lines: ~50

**TB02 [DOC] Create `docs/adr/_template.md` — canonical ADR template**
- File: `docs/adr/_template.md`
- Content contract: Design §3.4 (field order: title, Status, Date, Context, Decision, Consequences/Positive/Negative, Alternatives considered, References; no YAML front-matter; non-negotiable per-field properties)
- REQ-DOCS-011 / AC-011
- Done when:
  - File exists at `docs/adr/_template.md` (NOT `0000-template.md` — OQ-9 locked)
  - `grep -c "^## Context\|^## Decision\|^## Consequences\|^### Positive\|^### Negative\|^## Alternatives\|^## References" docs/adr/_template.md` = 7
  - No YAML front-matter present
- Est. lines: ~35

**TB03 [DOC] Create `docs/adr/0002-hexagonal-split.md`**
- File: `docs/adr/0002-hexagonal-split.md`
- Content contract: Design §3.5 ADR-0002 beats (context: AGENTS.md §5, Constitution Art. VII.1–4, no `code/` dir, NLP port; decision: 4 named layers, dependency direction; consequences; alternatives: flat module, 3-layer; references)
- REQ-DOCS-013, REQ-DOCS-014, REQ-DOCS-015, REQ-DOCS-016 / AC-013, AC-014, AC-015, AC-016
- Done when:
  - `grep "Status.*Accepted" docs/adr/0002-hexagonal-split.md` passes
  - `grep "Date.*2026-07-15" docs/adr/0002-hexagonal-split.md` passes
  - Context mentions AGENTS.md §5 and Constitution Art. VII
- Est. lines: ~60

**TB04 [DOC] Create `docs/adr/0003-tdd-mandatory.md`**
- File: `docs/adr/0003-tdd-mandatory.md`
- Content contract: Design §3.5 ADR-0003 beats (context: AGENTS.md §3, Constitution Art. II.1–4, coverage targets; decision: RED test first, minimum GREEN impl, REFACTOR with green suite, bug-fix regression test; alternatives: test-after, property-only)
- REQ-DOCS-013, REQ-DOCS-014, REQ-DOCS-015, REQ-DOCS-016 / AC-013, AC-014, AC-015, AC-016
- Done when:
  - `grep "Status.*Accepted" docs/adr/0003-tdd-mandatory.md` passes
  - `grep "Date.*2026-07-15" docs/adr/0003-tdd-mandatory.md` passes
  - Context mentions AGENTS.md §3 and coverage thresholds
- Est. lines: ~55

**TB05 [DOC] Create `docs/adr/0004-sdd-openspec.md`**
- File: `docs/adr/0004-sdd-openspec.md`
- Content contract: Design §3.5 ADR-0004 beats (context: AGENTS.md §1 7-artifact list, Constitution Art. I.1–5, openspec/config.yaml, skill-registry; decision: 7-artifact SDD set mandatory before code, hybrid persistence mode; alternatives: informal, kanban-only)
- REQ-DOCS-013, REQ-DOCS-014, REQ-DOCS-015, REQ-DOCS-016 / AC-013, AC-014, AC-015, AC-016
- Done when:
  - `grep "Status.*Accepted" docs/adr/0004-sdd-openspec.md` passes
  - `grep "Date.*2026-07-15" docs/adr/0004-sdd-openspec.md` passes
  - Context mentions `openspec/config.yaml` and `.atl/skill-registry.md`
- Est. lines: ~55

**TB06 [DOC] Create `docs/adr/0005-local-first.md`**
- File: `docs/adr/0005-local-first.md`
- Content contract: Design §3.5 ADR-0005 beats (context: Constitution Art. IV.4–5, AGENTS.md §4, NLP adapter implication; decision: local processing default, third-party consent gate; alternatives: cloud-first, opt-in local)
- REQ-DOCS-013, REQ-DOCS-014, REQ-DOCS-015, REQ-DOCS-016 / AC-013, AC-014, AC-015, AC-016
- Done when:
  - `grep "Status.*Accepted" docs/adr/0005-local-first.md` passes
  - `grep "Date.*2026-07-15" docs/adr/0005-local-first.md` passes
  - Context mentions Constitution Art. IV.4–5
- Est. lines: ~55

**TB07 [DOC] Create `docs/adr/0006-pos-per-occurrence.md`**
- File: `docs/adr/0006-pos-per-occurrence.md`
- Content contract: Design §3.5 ADR-0006 beats (context: Constitution Art. V.2–3, AGENTS.md §4, Occurrence entity; decision: POS on Occurrence not Lexeme, aggregated POS derived; alternatives: global POS per lemma, POS on WordForm only)
- REQ-DOCS-013, REQ-DOCS-014, REQ-DOCS-015, REQ-DOCS-016 / AC-013, AC-014, AC-015, AC-016
- Done when:
  - `grep "Status.*Accepted" docs/adr/0006-pos-per-occurrence.md` passes
  - `grep "Date.*2026-07-15" docs/adr/0006-pos-per-occurrence.md` passes
  - Context mentions Constitution Art. V.2–3 and the `Occurrence` entity
- Est. lines: ~55

**TB08 [DOC] Update `docs/adr/README.md` index — add Wave 1 ADRs**
- File: `docs/adr/README.md`
- Content contract: Design §3.3 index table; spec §4.1 Wave 1 rows (ADR-0001–0006, Wave 1 for 0002–0006); OQ-9: `_template.md` MUST NOT appear as an indexed entry
- REQ-DOCS-010, REQ-DOCS-016 / AC-010, AC-016
- Done when:
  - Index table contains rows for ADR-0001 through ADR-0006
  - ADR-0002..0006 show `Wave 1` in the Wave column
  - `grep "_template" docs/adr/README.md` returns 0 (template NOT in index)
- Est. lines: +6 rows (~12 lines)

**TB09 [DOC] Create `docs/decisions-log.md` — initial file with Wave 1 entries**
- File: `docs/decisions-log.md`
- Content contract: Design §3.7 (column definition, chronological ordering, seed entries rows 1–13 from the Wave 1 date range); spec §4.3 seed rows; Engineering Playbook deferral row with exact trigger wording per REQ-DOCS-021
- REQ-DOCS-019, REQ-DOCS-020, REQ-DOCS-021 / AC-019, AC-020, AC-021
- Done when:
  - File exists with columns `| Date | Decision | Category | Ref | Motivation | Consequences |`
  - All 2026-07-15-dated seed rows present (Constitution v1.0.0 adoption, ADR-0001, SPEC-001 DEC-001..006, ADR-0002..0006)
  - Engineering Playbook deferral row includes exact string: `"After first vertical slice ships end-to-end (upload a .txt file and view a lemma list with frequency)"`
  - Wave 2 entries NOT yet present (they come in Slice C)
- Est. lines: ~70

**TB10 [DOC] Verify Slice B completion**
- File: N/A (inspection task)
- Content contract: This tasks.md §3.4 checklist
- REQ-DOCS-010–016 (Wave 1), REQ-DOCS-019–020 (partial) / AC-010–016, AC-019–021
- Done when: All checklist items in §3.4 pass
- Est. lines: 0

### 3.4 Verification checklist for Slice B

- [ ] `docs/adr/README.md` exists; `grep -c "Proposed\|Accepted\|Superseded\|Deprecated"` ≥ 4; index table has `Wave` column
- [ ] `docs/adr/_template.md` exists; contains all 7 required heading patterns; no YAML front-matter
- [ ] ADR-0002..0006: each file exists, Status=Accepted, Date=2026-07-15, conforms to `_template.md`
- [ ] ADR index does NOT include `_template.md` as a numbered entry
- [ ] `docs/decisions-log.md` exists; Wave 1 seed rows (2026-07-15) present; Engineering Playbook deferral row includes verbatim trigger string
- [ ] Wave 2 entries (2026-07-16, ADR-0007..0010) NOT yet in decisions-log (they belong to Slice C)

---

## 4. Slice C — Contextual Commitment + Domain Legibility (~700–900 lines)

### 4.1 Rationale

Slice C completes the ADR suite with Wave 2 contextual decisions (manual corrections, multi-language scope, MWE abstraction, documentation language policy), builds the architecture baseline (which references all ADRs), creates the domain glossary (ES), and appends Wave 2 entries to the decisions-log. ADR-0008/0009 reference ADR-0005/0006 for cross-references; the baseline and glossary reference all ADRs — so Slice B must be complete first.

### 4.2 Deliverables

- `docs/adr/0007-manual-corrections-precedence.md` — new, Wave 2 (REQ-DOCS-013–016)
- `docs/adr/0008-multi-language-scope.md` — new, Wave 2 (REQ-DOCS-013–016)
- `docs/adr/0009-mwe-language-specific-instances.md` — new, Wave 2 (REQ-DOCS-013–016)
- `docs/adr/0010-documentation-language-policy.md` — new, Wave 2 (REQ-DOCS-013–016)
- `docs/adr/README.md` — updated: Wave 2 ADRs added to index (REQ-DOCS-010, 016)
- `docs/architecture/architecture-baseline.md` — new (REQ-DOCS-017, 018)
- `docs/glossary.md` — new (REQ-DOCS-030–034)
- `docs/decisions-log.md` — updated: Wave 2 entries appended (REQ-DOCS-019–021 complete)

### 4.3 Tasks

**TC01 [DOC] Create `docs/adr/0007-manual-corrections-precedence.md`**
- File: `docs/adr/0007-manual-corrections-precedence.md`
- Content contract: Design §3.5 ADR-0007 beats (context: Constitution Art. V.8–9, AGENTS.md §4, ManualCorrection entity, OQ-1 still open; decision: ManualCorrection precedence, reprocessing check per field, provenance metadata; alternatives: last-write-wins, flags-only)
- REQ-DOCS-013, REQ-DOCS-014, REQ-DOCS-015, REQ-DOCS-016 / AC-013, AC-014, AC-015, AC-016
- Done when:
  - `grep "Status.*Accepted" docs/adr/0007-manual-corrections-precedence.md` passes
  - `grep "Date.*2026-07-16" docs/adr/0007-manual-corrections-precedence.md` passes
  - ADR mentions OQ-1 as still open (UX shape deferred)
- Est. lines: ~65

**TC02 [DOC] Create `docs/adr/0008-multi-language-scope.md`**
- File: `docs/adr/0008-multi-language-scope.md`
- Content contract: Design §3.5 ADR-0008 beats; three-part decision: (a) any-language corpora, (b) user targeting via "idioma que estudia", (c) abstract MWE category; OQ-2/3/4 explicitly deferred; references ADR-0009; OQ-10 wording `"expresiones multipalabra específicas del idioma"`
- REQ-DOCS-013, REQ-DOCS-014, REQ-DOCS-015, REQ-DOCS-016 / AC-013, AC-014, AC-015, AC-016
- Done when:
  - `grep "Status.*Accepted" docs/adr/0008-multi-language-scope.md` passes
  - `grep "Date.*2026-07-16" docs/adr/0008-multi-language-scope.md` passes
  - All three decision parts (a)(b)(c) are explicit in the Decision section
  - OQ-2, OQ-3, OQ-4 listed as deferred
- Est. lines: ~70

**TC03 [DOC] Create `docs/adr/0009-mwe-language-specific-instances.md`**
- File: `docs/adr/0009-mwe-language-specific-instances.md`
- Content contract: Design §3.5 ADR-0009 beats; title MUST be exactly "Multiword expressions as language-specific instances" (A-8 confirmed); `mwe_kind` field; phrasal verb as English instance; Spanish locuciones; German Trennbare Verben; MWEs separate from Lexeme; references ADR-0008; OQ-10 ES wording in Spanish body
- REQ-DOCS-013, REQ-DOCS-014, REQ-DOCS-015, REQ-DOCS-016 / AC-013, AC-014, AC-015, AC-016
- Done when:
  - File title is exactly `# ADR-0009 — Multiword expressions as language-specific instances`
  - `grep "Status.*Accepted" docs/adr/0009-mwe-language-specific-instances.md` passes
  - `grep "Date.*2026-07-16" docs/adr/0009-mwe-language-specific-instances.md` passes
  - `grep "mwe_kind" docs/adr/0009-mwe-language-specific-instances.md` returns ≥ 1
- Est. lines: ~70

**TC04 [DOC] Create `docs/adr/0010-documentation-language-policy.md`**
- File: `docs/adr/0010-documentation-language-policy.md`
- Content contract: Design §3.5 ADR-0010 beats; two families (methodology EN, product-facing ES); AGENTS.md classified as ES; mixed artifacts follow scaffold language; ADR-0010 self-referentially proves the policy works; alternatives: all-ES, all-EN
- REQ-DOCS-013, REQ-DOCS-014, REQ-DOCS-015, REQ-DOCS-016 / AC-013, AC-014, AC-015, AC-016
- Done when:
  - `grep "Status.*Accepted" docs/adr/0010-documentation-language-policy.md` passes
  - `grep "Date.*2026-07-16" docs/adr/0010-documentation-language-policy.md` passes
  - File is written in English (methodology artifact per ADR-0010 itself)
- Est. lines: ~55

**TC05 [DOC] Update `docs/adr/README.md` index — add Wave 2 ADRs**
- File: `docs/adr/README.md`
- Content contract: Design §3.3; spec §4.1 Wave 2 rows (ADR-0007..0010, Wave 2)
- REQ-DOCS-010, REQ-DOCS-016 / AC-010, AC-016
- Done when:
  - Index table contains rows for ADR-0007..0010 with `Wave 2`
  - All 10 ADRs (0001–0010) now present in the index
- Est. lines: +4 rows (~8 lines)

**TC06 [DOC] Create `docs/architecture/architecture-baseline.md`**
- File: `docs/architecture/architecture-baseline.md`
- Content contract: Design §3.6 (section outline, committed invariants table with 9 rows and grounding §pointers, 3 Mermaid diagrams — system context, hexagonal layers, linguistic data flow — with exact node/edge contracts from design §3.6)
- REQ-DOCS-017, REQ-DOCS-018 / AC-017, AC-018
- Done when:
  - File exists; `grep -c "mermaid" docs/architecture/architecture-baseline.md` ≥ 3
  - Committed invariants section contains all 9 invariants from REQ-DOCS-018 (incl. MWEs as language-specific instances with phrasal verbs as English instance)
  - EN throughout
  - Links to `docs/adr/README.md`, `docs/glossary.md`, `docs/architecture/overview.md`
- Est. lines: ~200

**TC07 [DOC] Create `docs/glossary.md` — domain glossary (ES)**
- File: `docs/glossary.md`
- Content contract: Design §4.1 (section outline, 13 canonical entries, entry template with Categoría/Definición/Referencias/Impacto multiidioma, alphabetical ordering, abstract MWE entry with OQ-10 wording as heading `### Expresión multipalabra específica del idioma`, phrasal verb entry as instance-example)
- REQ-DOCS-030, REQ-DOCS-031, REQ-DOCS-032, REQ-DOCS-033, REQ-DOCS-034 / AC-030, AC-031, AC-032, AC-033, AC-034
- Done when:
  - File exists in Spanish
  - `grep -c "^### " docs/glossary.md` ≥ 13
  - `grep "Expresión multipalabra específica del idioma" docs/glossary.md` returns ≥ 1 (OQ-10 canonical heading present)
  - Each entry has `**Categoría**`, `**Definición**`, `**Referencias**`, `**Impacto multiidioma**` fields
  - `grep "instancia inglesa\|instancia.*inglés\|phrasal verb.*instancia" docs/glossary.md` ≥ 1 (phrasal verb positioned as instance)
- Est. lines: ~200

**TC08 [DOC] Append Wave 2 entries to `docs/decisions-log.md`**
- File: `docs/decisions-log.md`
- Content contract: Design §3.7 seed entries rows 14–26 (all 2026-07-16-dated rows: ADR-0007..0010, constitution amendment, Engineering Playbook deferral if not already present, language policy, ADR template filename OQ-9, amendment log placement OQ-8, OQ-10 canonical wording, SPEC-001 traceability seed, docs-methodology-overhaul cycle, openspec gitignore advisory)
- REQ-DOCS-019, REQ-DOCS-020, REQ-DOCS-021 / AC-019, AC-020, AC-021
- Done when:
  - All 2026-07-16 seed rows from design §3.7 present (total 26 rows)
  - Row for constitution amendment to v2.0.0 present
  - Row for `docs-methodology-overhaul SDD cycle executed` present
  - Chronological order preserved (ascending by date)
- Est. lines: ~60

**TC09 [DOC] Verify Slice C completion**
- File: N/A (inspection task)
- Content contract: This tasks.md §4.4 checklist
- REQ-DOCS-013–021 (complete), REQ-DOCS-030–034 / AC-013–021, AC-030–034
- Done when: All checklist items in §4.4 pass
- Est. lines: 0

### 4.4 Verification checklist for Slice C

- [ ] ADR-0007..0010: each file exists, Status=Accepted, dates=2026-07-16, conform to `_template.md`
- [ ] ADR-0009 title is exactly "Multiword expressions as language-specific instances"; `mwe_kind` present
- [ ] `docs/adr/README.md` index now covers ADR-0001..0010; ADR-0002..0006 show Wave 1, ADR-0007..0010 show Wave 2
- [ ] `docs/architecture/architecture-baseline.md` exists; `grep -c "mermaid"` ≥ 3; 9 committed invariants enumerated
- [ ] `docs/glossary.md` exists in Spanish; 13+ entries; abstract MWE entry heading is `### Expresión multipalabra específica del idioma`; phrasal verb entry reads as instance-example (OQ-10 compliant)
- [ ] `docs/decisions-log.md` now has all 26 seed rows; Wave 2 rows appended; chronological order preserved
- [ ] `grep "expresiones multipalabra específicas del idioma" docs/adr/0008-multi-language-scope.md docs/adr/0009-mwe-language-specific-instances.md docs/glossary.md` returns ≥ 3 matches (OQ-10 canonical wording present)

---

## 5. Slice D — Traceability + DoD Enforcement (~200 lines)

### 5.1 Rationale

Slice D creates the enforcement layer: the traceability matrix (references ADR files from Slice B/C), the definition-of-done extract (references glossary from Slice C), and the cross-reference footer on `architecture/overview.md`. The AGENTS.md §10 DoD gate line is part of the atomic amendment in Slice E (AGENTS.md is amended as a unit).

### 5.2 Deliverables

- `docs/traceability-matrix.md` — new (REQ-DOCS-040–042, 044)
- `docs/definition-of-done.md` — new (REQ-DOCS-050–052)
- `docs/architecture/overview.md` — additive cross-reference footer only (REQ-DOCS-073, 075)

### 5.3 Tasks

**TD01 [DOC] Create `docs/traceability-matrix.md`**
- File: `docs/traceability-matrix.md`
- Content contract: Design §3.8 (column definition: `REQ-ID | Criterio de aceptación | Archivo(s) de prueba | Tarea(s) | Estado`; 5 seed rows from design §3.8; one non-`Pendiente` row: REQ-DOCS-004 = Pasando; update-rules subsection with 5 rules; REQ-DOCS-001 row = Pendiente as additional worked row)
- REQ-DOCS-040, REQ-DOCS-041, REQ-DOCS-042, REQ-DOCS-044 / AC-040, AC-041, AC-042, AC-044
- Done when:
  - File exists; column headers match spec §6.1 exactly
  - At least one row with `Estado` = `Pasando` (REQ-DOCS-004 row)
  - `## Reglas de actualización` section present with 5 rules
  - `grep "REQ-DOCS-001\|REQ-001-001\|REQ-DOCS-004" docs/traceability-matrix.md` ≥ 2 rows
- Est. lines: ~60

**TD02 [DOC] Create `docs/definition-of-done.md`**
- File: `docs/definition-of-done.md`
- Content contract: Design §4.2 (section outline, ES language, explicit "Art. XI es fuente canónica" statement, criteria referencing constitution Art. XI without verbatim duplication, AGENTS.md §10 reference, traceability-matrix DoD gate wording per spec §6.4, references section)
- REQ-DOCS-050, REQ-DOCS-051, REQ-DOCS-052 / AC-050, AC-051, AC-052
- Done when:
  - File exists in Spanish
  - `grep "canónica\|canónica en caso de conflicto" docs/definition-of-done.md` ≥ 1
  - `grep "matriz de trazabilidad" docs/definition-of-done.md` ≥ 1 (DoD gate mentioned)
  - File does NOT contain verbatim full-text copy of Art. XI (reference only)
  - Links to `docs/constitution.md`, `AGENTS.md`, `docs/traceability-matrix.md`
- Est. lines: ~70

**TD03 [DOC] Add cross-reference footer to `docs/architecture/overview.md`**
- File: `docs/architecture/overview.md`
- Content contract: Design §6 cross-reference network; spec §3.15 (additive footer only, links to `docs/architecture/architecture-baseline.md` and `docs/adr/README.md`)
- REQ-DOCS-073, REQ-DOCS-075 / AC-083, AC-085
- Done when:
  - `grep "architecture-baseline" docs/architecture/overview.md` ≥ 1
  - `grep "adr/README" docs/architecture/overview.md` ≥ 1
  - No other body text in `overview.md` was modified
- Est. lines: ~10

**TD04 [DOC] Verify Slice D completion**
- File: N/A (inspection task)
- Content contract: This tasks.md §5.4 checklist
- REQ-DOCS-040–052, REQ-DOCS-073, REQ-DOCS-075 / AC-040–052, AC-083, AC-085
- Done when: All checklist items in §5.4 pass
- Est. lines: 0

### 5.4 Verification checklist for Slice D

- [ ] `docs/traceability-matrix.md` exists; column headers match spec §6.1; ≥ 1 non-`Pendiente` row
- [ ] `docs/traceability-matrix.md` contains `## Reglas de actualización` with 5 rules
- [ ] `docs/definition-of-done.md` exists in Spanish; "canónica en caso de conflicto" explicit; no verbatim Art. XI copy
- [ ] `docs/definition-of-done.md` links to `docs/constitution.md`, `AGENTS.md`, `docs/traceability-matrix.md`
- [ ] `docs/architecture/overview.md` cross-reference footer added linking to `architecture-baseline.md` and `docs/adr/README.md`; no other body text modified

---

## 6. Slice E — Amendment Payload v1.0.0 → v2.0.0 (atomic)

### 6.1 Rationale

The amendment payload is a **coordinated four-file atomic apply**. REQ-DOCS-06B explicitly forbids partial applies. All cross-references added in the amendment files (constitution → ADR index, baseline, glossary; AGENTS.md → traceability-matrix, DoD) require Slices A–D to have created the target files first. Slice E is its own slice precisely so the coordination invariant is trivially verifiable as a single gate.

`size:exception` flag: Slice E is expected to be ~150–250 lines of diffs across 4 files. This fits within the 400-line budget. However, the atomicity constraint means it cannot be split — if diff count exceeds 400, apply MUST request a `size:exception` from the user before proceeding. See §8.

### 6.2 Deliverables (atomic — all 4 apply together)

- `docs/constitution.md` — amended: version bump 1.0.0 → 2.0.0, header date, preamble generalization, `## Registro de enmiendas` section, cross-reference footer
- `docs/product-vision.md` — amended: §4 user targeting, §10 step 6 MWE, §12 item 7 MWE, cross-reference footer
- `README.md` — amended: line 3 generalized, `## Referencias metodológicas` section added
- `AGENTS.md` — amended: §4 MWE clause, §10 DoD gate line, `## Referencias` section

### 6.3 Tasks

**TE01 [DOC] `docs/constitution.md` — version header bump (1.0.0 → 2.0.0)**
- File: `docs/constitution.md`
- Content contract: Design §5.1 header block diff (Line 3: `1.0.0` → `2.0.0`)
- REQ-DOCS-062 / AC-062
- Done when: `grep "Versión.*2.0.0" docs/constitution.md` passes
- Est. lines: +1 (1-line change)

**TE02 [DOC] `docs/constitution.md` — add approval date line**
- File: `docs/constitution.md`
- Content contract: Design §5.1 header block diff (add `**Fecha de aprobación:** 2026-07-15` below existing status line)
- REQ-DOCS-061 / AC-061
- Done when: `grep "Fecha de aprobación.*2026-07-15" docs/constitution.md` passes
- Est. lines: +1 (1 new line)

**TE03 [DOC] `docs/constitution.md` — generalize preamble**
- File: `docs/constitution.md`
- Content contract: Design §5.1 preamble diff intent (remove "inglés" as sole scope qualifier; frame vocabulary as being in the language the user studies; English as first-implemented; preserve "obras literarias aportadas legalmente por el usuario"; final ES wording chosen by apply)
- REQ-DOCS-060 / AC-060
- Done when:
  - `grep "vocabulario inglés" docs/constitution.md` returns 0
  - `grep "idioma\|languages\|cualquier idioma" docs/constitution.md` ≥ 1 (multi-language framing present)
  - Art. I–XI body text unchanged (only preamble line 9 modified)
- Est. lines: ~3 (replace ~1 line)

**TE04 [DOC] `docs/constitution.md` — add `## Registro de enmiendas` section**
- File: `docs/constitution.md`
- Content contract: Design §5.1 amendment record diff (new section after Art. XII, Markdown table, fields: Fecha=2026-07-16, Cambio, Motivación, Consecuencias from spec §7.2, Versión anterior=1.0.0, Versión nueva=2.0.0); Art. XII body text MUST remain byte-identical (OQ-8 locked)
- REQ-DOCS-063 / AC-063
- Done when:
  - `grep "Registro de enmiendas" docs/constitution.md` ≥ 1
  - `grep "2.0.0.*1.0.0\|1.0.0.*2.0.0" docs/constitution.md` ≥ 1 (version fields in amendment record)
  - `grep "2026-07-16" docs/constitution.md` ≥ 1
  - Art. XII body text verified byte-identical before and after
- Est. lines: ~30

**TE05 [DOC] `docs/constitution.md` — add cross-reference footer**
- File: `docs/constitution.md`
- Content contract: Design §5.1 cross-reference footer (links to `docs/adr/README.md`, `docs/architecture/architecture-baseline.md`, `docs/glossary.md`, `docs/definition-of-done.md`)
- REQ-DOCS-071, REQ-DOCS-075 / AC-081, AC-085
- Done when:
  - `grep "adr/README\|architecture-baseline\|glossary\|definition-of-done" docs/constitution.md` ≥ 4 matches
- Est. lines: ~8

**TE06 [DOC] `docs/product-vision.md` — generalize §4 user targeting**
- File: `docs/product-vision.md`
- Content contract: Design §5.2 diff (§4 line ~21: replace "en inglés" with "en el idioma que estudia"; all other user persona attributes unchanged)
- REQ-DOCS-066 / AC-067
- Done when:
  - `grep "en inglés" docs/product-vision.md` returns 0 in §4 (check line 21 area)
  - `grep "idioma que estudia" docs/product-vision.md` ≥ 1
- Est. lines: ~2 (1-line replace)

**TE07 [DOC] `docs/product-vision.md` — generalize §10 step 6 MWE wording**
- File: `docs/product-vision.md`
- Content contract: Design §5.2 diff (§10 step 6: replace "phrasal verbs" with "expresiones multipalabra específicas del idioma" — OQ-10 canonical wording)
- REQ-DOCS-067 / AC-068
- Done when:
  - `grep "expresiones multipalabra específicas del idioma" docs/product-vision.md` ≥ 1
  - `grep "Revisa phrasal verbs" docs/product-vision.md` returns 0
- Est. lines: ~2 (1-line replace)

**TE08 [DOC] `docs/product-vision.md` — generalize §12 item 7 MWE wording**
- File: `docs/product-vision.md`
- Content contract: Design §5.2 diff (§12 item 7: replace "Phrasal verbs" with "Expresiones multipalabra específicas del idioma" — title-case; OQ-10 canonical wording); §8 "Fuera de alcance inicial" explicitly unchanged (REQ-DOCS-069)
- REQ-DOCS-068, REQ-DOCS-069 / AC-069, AC-070
- Done when:
  - `grep "Expresiones multipalabra específicas del idioma" docs/product-vision.md` ≥ 1 (§12 item 7)
  - `grep "^7\. Phrasal verbs" docs/product-vision.md` returns 0
  - `grep "Fuera de alcance inicial" docs/product-vision.md` still present (§8 untouched)
  - `grep "Traducción automática" docs/product-vision.md` still present (§8 item unchanged)
- Est. lines: ~2 (1-line replace)

**TE09 [DOC] `docs/product-vision.md` — add cross-reference footer**
- File: `docs/product-vision.md`
- Content contract: Design §5.2 cross-reference footer (links to `docs/constitution.md`, `docs/glossary.md`)
- REQ-DOCS-072, REQ-DOCS-075 / AC-082, AC-085
- Done when: `grep "constitution\|glossary" docs/product-vision.md` ≥ 2 (in cross-ref section)
- Est. lines: ~6

**TE10 [DOC] `README.md` — generalize line 3 multi-language scope**
- File: `README.md`
- Content contract: Design §5.3 diff (line 3: remove "en inglés" as scope qualifier; retain "comenzando por *The Eye of the World*"; frame as multi-language vocabulary analysis; final ES wording chosen by apply)
- REQ-DOCS-06C / AC-066
- Done when:
  - `grep "en inglés" README.md` returns 0 on line 3
  - `grep "Eye of the World" README.md` ≥ 1 (initial corpus example preserved)
  - `grep "idioma\|multi.*idioma\|cualquier idioma" README.md` ≥ 1 (multi-language framing)
- Est. lines: ~2 (1-line replace)

**TE11 [DOC] `README.md` — add `## Referencias metodológicas` section**
- File: `README.md`
- Content contract: Design §5.3 new section (after `## Siguiente especificación recomendada`; links to `docs/constitution.md`, `AGENTS.md`, `docs/glossary.md`, `docs/adr/README.md`, `docs/definition-of-done.md`)
- REQ-DOCS-074, REQ-DOCS-075 / AC-084, AC-085
- Done when:
  - `grep "Referencias metodológicas" README.md` ≥ 1
  - `grep "constitution\|AGENTS\|glossary\|adr/README\|definition-of-done" README.md` ≥ 5
  - Repo-tree diagram, `## Flujo obligatorio`, `## Alcance del paquete`, `## Siguiente especificación recomendada` sections unchanged
- Est. lines: ~12

**TE12 [DOC] `AGENTS.md` — generalize §4 MWE clause (OQ-10)**
- File: `AGENTS.md`
- Content contract: Design §5.4 §4 amendment (single bullet rewrite: phrasal verbs named as English instance of "expresiones multipalabra específicas del idioma"; separate-modeling rule preserved; abstract MWE concept first; final ES wording chosen by apply per design §5.4 example intent)
- REQ-DOCS-06A / AC-071
- Done when:
  - `grep "expresiones multipalabra específicas del idioma" AGENTS.md` ≥ 1
  - `grep "phrasal verbs y expresiones multipalabra deben modelarse separadamente" AGENTS.md` returns 0 (old clause replaced)
  - Separate-modeling rule still present (MWEs ≠ single-word lemmas)
  - §1–§3, §5–§9, §11 body text unchanged
- Est. lines: ~3 (1-line rewrite)

**TE13 [DOC] `AGENTS.md` — add §10 traceability-matrix DoD gate line**
- File: `AGENTS.md`
- Content contract: Design §5.4 §10 additive change; spec §6.4 exact wording: `"- La matriz de trazabilidad se ha actualizado con los identificadores de requisito, criterio de aceptación, prueba y tarea correspondientes."`
- REQ-DOCS-043 / AC-043
- Done when:
  - `grep "matriz de trazabilidad se ha actualizado" AGENTS.md` passes (exact wording from spec §6.4)
- Est. lines: +1

**TE14 [DOC] `AGENTS.md` — add `## Referencias` cross-reference section**
- File: `AGENTS.md`
- Content contract: Design §5.4 new `## Referencias` section (in this order: `docs/constitution.md`, `docs/adr/README.md`, `docs/architecture/architecture-baseline.md`, `docs/glossary.md`, `docs/traceability-matrix.md`, `docs/definition-of-done.md`, `docs/decisions-log.md`)
- REQ-DOCS-070, REQ-DOCS-075 / AC-080, AC-085
- Done when:
  - `grep "constitution\|adr/README\|architecture-baseline\|glossary\|traceability-matrix\|definition-of-done\|decisions-log" AGENTS.md` ≥ 7
- Est. lines: ~12

**TE15 [DOC] Coordinated verification pass — all 4 amendment files**
- File: all 4 (`docs/constitution.md`, `docs/product-vision.md`, `README.md`, `AGENTS.md`)
- Content contract: Design §5.5 coordination invariant restatement; A-7 re-scan
- REQ-DOCS-06B / AC-072
- Done when: All items in §6.4 verification checklist pass; A-7 re-scan `grep -r "inglés" docs README.md AGENTS.md` returns only descriptive-context matches, no scope-defining occurrences outside OQ-10 canonicalized contexts
- Est. lines: 0

### 6.4 Verification checklist for Slice E

- [ ] All 4 files (`docs/constitution.md`, `docs/product-vision.md`, `README.md`, `AGENTS.md`) contain their respective changes
- [ ] `grep "Versión.*2.0.0" docs/constitution.md` passes; `grep "Fecha de aprobación.*2026-07-15"` passes
- [ ] `grep "Registro de enmiendas" docs/constitution.md` passes; Art. XII body text byte-identical
- [ ] `grep "vocabulario inglés" docs/constitution.md docs/product-vision.md README.md AGENTS.md` returns 0 (no residual English-only scope claims)
- [ ] OQ-10 canonical wording `"expresiones multipalabra específicas del idioma"` appears in all 9 target files: constitution (preamble area by intent), product-vision §10/§12, AGENTS.md §4, glossary abstract entry, ADR-0008, ADR-0009, architecture-baseline invariants, decisions-log ADR-0008/0009 rows
- [ ] `grep "matriz de trazabilidad se ha actualizado" AGENTS.md` passes (exact spec §6.4 wording)
- [ ] Cross-references from amendment files point to Slice A–D artifacts (all targets must exist)
- [ ] `grep -r "inglés" docs README.md AGENTS.md` returns only descriptive-context matches (A-7 re-scan passes)
- [ ] Bidirectionality: `grep "constitution" docs/adr/README.md` ≥ 1; `grep "adr/README" docs/constitution.md` ≥ 1 (both directions of all major cross-ref pairs present)
- [ ] §8 "Fuera de alcance inicial" in `docs/product-vision.md` unchanged: `grep "Traducción automática masiva" docs/product-vision.md` ≥ 1

---

## 7. Cross-slice dependencies

| Dependency | Explanation |
|------------|-------------|
| A → B | ADR index references `openspec/config.yaml` (ADR-0004 context); registry must exist before ADR-0004 is written |
| B → C | ADR-0008/0009 reference ADR-0005/0006; decisions-log Wave 2 appends to Wave 1 rows created in Slice B |
| C → D | Traceability-matrix references ADR files (B+C); DoD extract references glossary (C); `overview.md` footer references `architecture-baseline.md` (C) |
| A–D → E | Amendment cross-references (constitution → ADR index, baseline, glossary, DoD; AGENTS.md → traceability-matrix, DoD, decisions-log) all require those target files to exist |
| B self | `docs/adr/README.md` index is updated in TB08 after ADRs 0002–0006 are written (TB03–TB07) |
| C self | `docs/adr/README.md` index is updated in TC05 after ADRs 0007–0010 are written (TC01–TC04) |

**Mandatory execution order**: A → B → C → D → E. No slice may begin until all tasks in the preceding slice are verified complete.

---

## 8. Sizing forecast

| Slice | Est. lines | Budget (≤ 400) | Verdict |
|-------|------------|-----------------|---------|
| A | ~120 | 400 | ✅ Fits |
| B | ~520 | 400 | ⚠️ Exceeds — expected; chained delivery approved |
| C | ~800 | 400 | ⚠️ Exceeds — expected; chained delivery approved |
| D | ~140 | 400 | ✅ Fits |
| E | ~150–250 | 400 | ✅ Fits (atomic 4-file amendment) — but see note |
| **Total** | **~1730–1830** | 2000 (aggregate) | Chained plan absorbs budget safely per slice |

**Slice E atomicity note**: Slice E is estimated at ~150–250 lines across 4 files — well within the 400-line budget. However, because the slice cannot be split (REQ-DOCS-06B coordination invariant), if the actual diff exceeds 400 lines, apply MUST request a `size:exception` from the user before committing Slice E. Flag: `size:exception` (conditional on actual diff count; pre-authorized if ≤ 400 lines).

**Slices B and C** each exceed 400 lines individually — this is expected and pre-approved under the chained-slice delivery strategy. Each is reviewed as an independent PR-equivalent scope.

---

## 9. Review-workload forecast

```
Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: Low per slice (A, D, E); High aggregate (~1730–1830 lines total)
Estimated changed lines: ~1730–1830 total
```

**Notes for orchestrator's Review Workload Guard**:
- Decision already resolved: user pre-approved chained-slice plan (ask-always strategy + user confirmation prior to this tasks file).
- Slice partition A → B → C → D → E is the confirmed chain.
- Slices B and C individually exceed 400 lines — accepted as the minimum granularity for each slice (cannot split ADR waves further without violating cross-reference order).
- Slice E is atomic by spec contract; cannot be split regardless of line count.

### Suggested Work Units

| Unit | Goal | Slice | Focused test command | Runtime harness | Rollback boundary |
|------|------|-------|---------------------|-----------------|-------------------|
| 1 | SDD bootstrap | A | `python -c "import yaml; yaml.safe_load(open('openspec/config.yaml'))"` && `grep -c "sdd-" .atl/skill-registry.md` | Inspect files in terminal | Delete `openspec/config.yaml`; revert `.atl/skill-registry.md` SDD rows |
| 2 | ADR foundation + decisions-log Wave 1 | B | `grep -c "Status.*Accepted" docs/adr/0002-hexagonal-split.md docs/adr/0003-tdd-mandatory.md docs/adr/0004-sdd-openspec.md docs/adr/0005-local-first.md docs/adr/0006-pos-per-occurrence.md` | Open `docs/adr/README.md` in browser/viewer | Delete ADR-0002..0006; delete `docs/decisions-log.md`; revert `docs/adr/README.md` |
| 3 | ADR Wave 2 + baseline + glossary | C | `grep -c "mermaid" docs/architecture/architecture-baseline.md` && `grep -c "^### " docs/glossary.md` | Mermaid preview (VSCode / any Markdown viewer) | Delete ADR-0007..0010; delete `architecture-baseline.md`, `glossary.md`; revert decisions-log to Wave 1 state |
| 4 | Traceability + DoD | D | `grep "Pasando" docs/traceability-matrix.md` && `grep "canónica" docs/definition-of-done.md` | Inspect files | Delete `traceability-matrix.md`, `definition-of-done.md`; revert `overview.md` footer |
| 5 | Amendment payload (atomic) | E | `grep "2.0.0" docs/constitution.md` && `grep "expresiones multipalabra específicas del idioma" AGENTS.md docs/product-vision.md` && `grep "matriz de trazabilidad se ha actualizado" AGENTS.md` | Diff the 4 files against pre-apply state | Revert all 4 files to pre-Slice-E state atomically |

---

## 10. Apply-phase guidance

### Skills to load (apply agent)

For all slices:
- `/Users/isildur/.config/opencode/skills/_shared/SKILL.md`
- `/Users/isildur/.config/opencode/skills/sdd-apply/SKILL.md`
- `/Users/isildur/.config/opencode/skills/cognitive-doc-design/SKILL.md`
- `/Users/isildur/.config/opencode/skills/work-unit-commits/SKILL.md`

For Slice E specifically:
- Re-read design §5 (diff intents for all 4 amendment files) before writing any file.

### Apply-progress continuity

Apply agent MUST search Engram for previous apply-progress before starting any slice:
```
mem_search: "sdd/docs-methodology-overhaul/apply" or "apply-progress docs-methodology-overhaul"
```
If a previous partial apply is found, resume from the last completed task within the slice — do not restart from TA01.

### Language reminders

- **EN artifacts**: `openspec/config.yaml`, `.atl/skill-registry.md`, all ADRs (0002–0010), `docs/adr/README.md`, `docs/adr/_template.md`, `docs/architecture/architecture-baseline.md`, `docs/decisions-log.md`, `docs/traceability-matrix.md` (scaffold)
- **ES artifacts**: `docs/glossary.md`, `docs/definition-of-done.md`, `docs/constitution.md`, `docs/product-vision.md`, `README.md`, `AGENTS.md`
- **OQ-10 canonical wording** (invariant across all artifacts):
  - ES: `"expresiones multipalabra específicas del idioma"` — NO synonyms, NO abbreviations
  - EN: `"language-specific multiword expressions"` — NO synonyms

### Verification rerun instructions

After each slice, apply agent MUST run (or simulate) the slice's verification checklist before reporting slice complete. Specifically:
- Slice A: YAML parse + grep skill-registry
- Slice B: ADR status/date grep per file + decisions-log seed rows check
- Slice C: Mermaid count + glossary entry count + OQ-10 wording grep + decisions-log 26-row check
- Slice D: traceability column check + DoD canonical statement check + overview.md footer grep
- Slice E: Full §6.4 checklist including A-7 re-scan

---

## 11. Open items carried to apply

| OQ | Description | Status | Action in apply |
|----|-------------|--------|-----------------|
| OQ-1 | Manual-corrections UX (day-one vs deferred) | Open — not resolved | Surfaced in `docs/decisions-log.md` ADR-0007 row as unresolved product decision; ADR-0007 records the invariant only |
| OQ-2 | Language detection strategy | Open — future ADR | `docs/decisions-log.md` row for ADR-0008 notes OQ-2 as deferred |
| OQ-3 | Translation provider strategy | Open — future ADR | `docs/decisions-log.md` row for ADR-0008 notes OQ-3 as deferred; constitution Art. IV.5 consent model required |
| OQ-4 | NLP library selection per language | Open — future ADR | `docs/decisions-log.md` row for ADR-0008 notes OQ-4 as deferred |

These OQs do NOT block any slice. They are surfaced in the decisions-log as "future ADR" placeholders.

---

## 12. Skill resolution

| Skill | Status | Path |
|-------|--------|------|
| `_shared` | Loaded (support reference) | `/Users/isildur/.config/opencode/skills/_shared/SKILL.md` |
| `sdd-tasks` | Loaded (executor, this phase) | `/Users/isildur/.config/opencode/skills/sdd-tasks/SKILL.md` |
| `cognitive-doc-design` | Loaded | `/Users/isildur/.config/opencode/skills/cognitive-doc-design/SKILL.md` |
| `work-unit-commits` | Loaded | `/Users/isildur/.config/opencode/skills/work-unit-commits/SKILL.md` |

**Skill resolution result**: `paths-injected` — all four loaded from exact `SKILL.md` paths. No fallback required.

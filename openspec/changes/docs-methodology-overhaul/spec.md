# Spec — Documentation & Methodology Overhaul (docs-methodology-overhaul)

## 0. Metadata

| Field | Value |
|-------|-------|
| Change slug | `docs-methodology-overhaul` |
| Capability code | `DOCS` |
| Requirement prefix | `REQ-DOCS-###` (zero-padded, 3-digit, sequential from 001) |
| Related exploration | `openspec/changes/docs-methodology-overhaul/explore.md` |
| Related proposal | `openspec/changes/docs-methodology-overhaul/proposal.md` |
| Governing constitution version at spec time | `1.0.0` |
| Constitution version after this change | `2.0.0` (MAJOR — see §7 amendment payload) |
| Spec version | 2.0 (supersedes v1, Engram #2254) |
| First vertical slice reference | "upload a `.txt` file and view a lemma list with frequency" (translation deferred post-MVP) |
| Language policy | EN methodology; ES product-facing (see §7 amendment payload for the four-file coordinated change) |
| Artifact store | openspec + engram |
| Repo state assumption | Not git-tracked yet — no PR/branch mechanics in scope |

Language-policy split by artifact family:

| Family | Language | Rationale |
|--------|----------|-----------|
| SDD/OpenSpec wiring, ADRs, architecture-baseline, decisions-log, traceability-matrix, skill-registry | EN | Methodology surface consumed by agents and tooling. |
| Constitution, product-vision, glossary, definition-of-done | ES | Product-facing artifacts already established in Spanish; audience is the user. |
| AGENTS.md | ES | Existing agent contract; **amended as part of §7 amendment payload** (MWE clause generalization). |
| README.md | ES | **Amended as part of §7 amendment payload** (line 3 English-only scope claim generalized). |

---

## 1. Requirements catalog

Requirements are grouped by family. Each row is atomic, testable, and traced to a source and to acceptance criteria in §11.

### 1.1 Family A — SDD / OpenSpec wiring

| ID | Statement | Source | Acceptance (§11) | Priority |
|----|-----------|--------|------------------|----------|
| REQ-DOCS-001 | An `openspec/config.yaml` file MUST exist at repo root providing the SDD context bootstrap: project name, stack, test/lint/typecheck commands, persistence mode, strict_tdd flag, skill registry path, and change-slug convention. | Proposal §5.1; Exploration §3 (P0 gap); Wellforge init pattern | AC-001 | P0 |
| REQ-DOCS-002 | `openspec/config.yaml` MUST include an inline comment block encoding the gitignore policy for `openspec/changes/` to be applied when the repo is git-initialized. | User decision OQ-5 (locked); Proposal §5.1, §11 concern #1 | AC-002 | P0 |
| REQ-DOCS-003 | `openspec/config.yaml` MUST include a `rules` section keyed by phase (`proposal`, `specs`, `design`, `tasks`, `apply`, `verify`, `archive`) mirroring the Wellforge/Synaptiq shape and referencing project invariants (RFC 2119 keywords for specs, hierarchical numbered tasks, mandatory TDD in apply). | Openspec convention `_shared/openspec-convention.md`; Wellforge/Synaptiq baseline pattern | AC-003 | P0 |
| REQ-DOCS-004 | `.atl/skill-registry.md` MUST list, at minimum, the SDD skill suite (`sdd-init`, `sdd-explore`, `sdd-propose`, `sdd-spec`, `sdd-design`, `sdd-tasks`, `sdd-apply`, `sdd-verify`, `sdd-archive`, `sdd-onboard`, `skill-registry`) with correct triggers, scope, and absolute `SKILL.md` paths. | Proposal §5.1; Exploration §2.6 | AC-004 | P0 |
| REQ-DOCS-005 | `.atl/skill-registry.md` MUST preserve the existing 11 user-scoped skills already indexed; adding SDD skills MUST NOT remove existing entries. | Current `.atl/skill-registry.md` state; regression-safety principle | AC-005 | P0 |
| REQ-DOCS-006 | `.atl/skill-registry.md` MUST retain the auto-generated header comment and loading-protocol section verbatim so `gentle-ai skill-registry refresh` regeneration remains idempotent-friendly. | Current `.atl/skill-registry.md` §Contract, §Loading protocol | AC-006 | P0 |

### 1.2 Family B — Architecture commitment layer

| ID | Statement | Source | Acceptance (§11) | Priority |
|----|-----------|--------|------------------|----------|
| REQ-DOCS-010 | `docs/adr/README.md` MUST exist providing the ADR index, status vocabulary (`Proposed`, `Accepted`, `Superseded`, `Deprecated`), numbering convention (global sequential, zero-padded 4-digit), and authoring rules. | Proposal §5.2; User decision Q4 (locked); Wellforge/Cairn ADR patterns | AC-010 | P0 |
| REQ-DOCS-011 | `docs/adr/_template.md` (or `docs/adr/0000-template.md`) MUST exist providing the canonical ADR skeleton with fields: Status, Date, Context, Decision, Consequences (positive/negative), Alternatives considered, References. | Proposal §5.2; Wellforge/Cairn ADR templates | AC-011 | P0 |
| REQ-DOCS-012 | Existing `docs/adr/0001-monorepo-and-stack.md` MUST remain unmodified in content (dated 2026-07-15, status Aceptado). Cross-reference footers MAY be appended without altering the decision text. | Current ADR-0001; retroactive-fidelity principle (Proposal risk R-2) | AC-012 | P0 |
| REQ-DOCS-013 | Seed ADRs ADR-0002 through ADR-0010 MUST exist as file skeletons conforming to `_template.md`, each with a one-line thesis grounded in a specific clause of AGENTS.md, constitution, or product-vision (see §4). | Proposal §5.2 seed catalog; User decision on 10-ADR count (locked with wave split) | AC-013 | P0 |
| REQ-DOCS-014 | Foundational seed ADRs (ADR-0002 through ADR-0006) MUST carry the date `2026-07-15` (constitution approval date). Contextual seed ADRs (ADR-0007 through ADR-0010) MUST carry today's date (`2026-07-16`). | User decision OQ-6 (locked); Proposal §11 concern #3 | AC-014 | P0 |
| REQ-DOCS-015 | All seed ADRs MUST carry status `Accepted` because they codify decisions already in force per AGENTS.md and constitution. Any ADR that describes an unresolved choice MUST NOT be included in this change and MUST be flagged as candidate for a future cycle. | Grounding principle: ADRs record decisions, not proposals; Proposal §11 concern #2 | AC-015 | P0 |
| REQ-DOCS-016 | Seed ADRs MUST be split into two delivery waves per the delivery strategy: **Wave 1** = ADR-0002 to ADR-0006 (5 foundational); **Wave 2** = ADR-0007 to ADR-0010 (4 contextual). Wave assignment MUST be recorded in the ADR catalog (§4). | User decision (R-6 mitigation applied preventively); Proposal §7 sizing verdict | AC-016 | P0 |
| REQ-DOCS-017 | `docs/architecture/architecture-baseline.md` MUST exist as a committed-state snapshot distinct from `docs/architecture/overview.md`. It MUST include at least three Mermaid diagrams: (a) system context, (b) hexagonal layers, (c) linguistic data flow (form → normalization → lemma → occurrence with contextual POS). | Proposal §5.2; User decision Q7 (locked); Wellforge baseline pattern | AC-017 | P0 |
| REQ-DOCS-018 | `docs/architecture/architecture-baseline.md` MUST explicitly enumerate committed invariants: local-first processing, hexagonal split (domain/application/infrastructure/api), SQLite for MVP, spaCy as first NLP adapter (replaceable via port), manual-corrections precedence, POS-per-occurrence, multiword expressions modeled separately from single-word lemmas (with phrasal verbs as the English instance — see ADR-0009), provenance stored for automatic results. | AGENTS.md §4, §5; Constitution Art. V, VII; Exploration §1.5 | AC-018 | P0 |
| REQ-DOCS-019 | `docs/decisions-log.md` MUST exist as a chronological table with columns: date, decision, category, ADR/spec reference, motivation, consequences. | Proposal §5.2; Synaptiq `12-Log-de-Decisiones` pattern | AC-019 | P0 |
| REQ-DOCS-020 | `docs/decisions-log.md` MUST include at minimum the seed entries: constitution adoption, ADR-0001 (monorepo/stack), SPEC-001 decisions DEC-001..006, each seed ADR (0002–0010), the language-policy decision, the Engineering Playbook deferral trigger, and this docs-methodology-overhaul change itself. | Proposal §5.2 + §11 concern #2; Constitution and SPEC-001 as historical anchors | AC-020 | P0 |
| REQ-DOCS-021 | The Engineering Playbook deferral entry in `docs/decisions-log.md` MUST include an explicit revisit trigger: **"After first vertical slice ships end-to-end (upload a `.txt` file and view a lemma list with frequency)."** | User decision Q3 (locked); Proposal §11 concern #2 | AC-021 | P0 |

### 1.3 Family C — Domain legibility

| ID | Statement | Source | Acceptance (§11) | Priority |
|----|-----------|--------|------------------|----------|
| REQ-DOCS-030 | `docs/glossary.md` MUST exist in Spanish and define every core linguistic-domain term used in AGENTS.md §4 and constitution Art. V. | Proposal §5.3; Exploration §1.3 (P0 gap); User decision on language policy (product-facing = ES) | AC-030 | P0 |
| REQ-DOCS-031 | Each glossary entry MUST include: term (ES), category label (concept / entity / attribute / process / relation), one-line definition target, and at least one cross-reference to a usage site (spec file, ADR, or AGENTS.md section). | Proposal §5.3; cognitive-doc-design recognition-over-recall pattern | AC-031 | P0 |
| REQ-DOCS-032 | The glossary MUST cover at minimum the 13 terms enumerated in §5.1 below (the abstract MWE entry counts as one canonical term). Additional terms discovered during design/apply MAY be added; MUST NOT be removed. | AGENTS.md §4; Constitution Art. V; Proposal §5.3 | AC-032 | P0 |
| REQ-DOCS-033 | Every glossary entry MUST carry a multi-language-impact note stating whether the term is language-agnostic or language-specific in interpretation. | User decision on multi-language day-one (locked); Proposal §2 | AC-033 | P1 |
| REQ-DOCS-034 | The glossary MUST include a canonical abstract entry "**expresión multipalabra específica del idioma**" (or the Spanish wording finalized per OQ-10) that names phrasal verbs (English), locuciones/perífrasis verbales (Spanish), and separable verbs (German) as **language-specific instances**, not as canonical siblings. The single-word phrasal-verb entry MUST be re-positioned as an example instance of this abstraction. | Constitution amendment (REQ-DOCS-060 series); AGENTS.md §4 generalization; ADR-0009 retitled thesis | AC-034 | P0 |

### 1.4 Family D — Traceability formalization

| ID | Statement | Source | Acceptance (§11) | Priority |
|----|-----------|--------|------------------|----------|
| REQ-DOCS-040 | `docs/traceability-matrix.md` MUST exist as a Markdown table maintained manually, providing a cross-spec view of requirements. | Proposal §5.4; User decision Q5 (locked) | AC-040 | P0 |
| REQ-DOCS-041 | The traceability matrix schema MUST use the columns defined in §6.1 below. | Proposal §5.4; Wellforge requirement-map pattern | AC-041 | P0 |
| REQ-DOCS-042 | The traceability matrix MUST seed at least one non-`Pendiente` example row (worked example) so the update workflow is unambiguous. | Proposal risk R-4 mitigation; Exploration §1.4 (traceability staleness) | AC-042 | P0 |
| REQ-DOCS-043 | `AGENTS.md` §10 MUST be extended with a hard DoD gate line explicitly naming the traceability matrix — the exact wording is defined in §6.4 below. | Proposal §5.4; User decision (locked); Exploration §1.4 | AC-043 | P0 |
| REQ-DOCS-044 | The traceability matrix update rules MUST be documented inside the matrix file itself (when to add/modify/remove a row, who owns updates). | Proposal §5.4; Anti-staleness principle | AC-044 | P1 |

### 1.5 Family E — Definition of Done extraction

| ID | Statement | Source | Acceptance (§11) | Priority |
|----|-----------|--------|------------------|----------|
| REQ-DOCS-050 | `docs/definition-of-done.md` MUST exist in Spanish as a product-facing summary that quotes or links Constitution Art. XI and AGENTS.md §10. | Proposal §5.5; User decision Q8 (locked) | AC-050 | P0 |
| REQ-DOCS-051 | `docs/definition-of-done.md` MUST include an explicit statement that Constitution Art. XI is canonical in case of conflict. | User decision Q8 (locked); Proposal §5.5 | AC-051 | P0 |
| REQ-DOCS-052 | `docs/definition-of-done.md` MUST NOT duplicate the constitution text verbatim beyond the necessary quote block; it MUST reference the constitution for full authority. | Proposal risk R-5 (drift mitigation); anti-duplication principle | AC-052 | P1 |

### 1.6 Family F — Constitution + amendment payload (v1.0.0 → v2.0.0 MAJOR, four coordinated files)

The amendment payload is a **coordinated multi-file change** across `docs/constitution.md`, `docs/product-vision.md`, `README.md`, and `AGENTS.md`. See §7 for the full payload spec. All files MUST ship together; partial applies are forbidden.

| ID | Statement | Source | Acceptance (§11) | Priority |
|----|-----------|--------|------------------|----------|
| REQ-DOCS-060 | `docs/constitution.md` preamble MUST be generalized to remove "vocabulario inglés" as sole scope. English MUST be framed as **one supported language among many**, not as the exclusive scope. The exact diff intent is defined in §7.2 below. | User decision (locked, v2.0.0 MAJOR); Proposal §5.6; §7.2 | AC-060 | P0 |
| REQ-DOCS-061 | `docs/constitution.md` MUST gain an explicit **Fecha de aprobación: 2026-07-15** line in the header. | User decision (locked, item 13); Constitution currently dateless | AC-061 | P0 |
| REQ-DOCS-062 | `docs/constitution.md` version field MUST bump from `1.0.0` to **`2.0.0` (MAJOR)**. Rationale (multi-language expansion + user-targeting generalization + MWE abstraction span four files and change conceptual scope; this is not a compatible extension) MUST be recorded in the amendment record per Art. XII procedure. | User decision (locked, v2.0.0 MAJOR); Constitution Art. XII procedure | AC-062 | P0 |
| REQ-DOCS-063 | `docs/constitution.md` MUST gain an amendment record entry per Art. XII: date `2026-07-16`, change summary, motivation, consequences, previous version `1.0.0`, new version `2.0.0`. The record MUST live either as a new numbered section at the end of the constitution or under Art. XII (implementation choice deferred to design). | Constitution Art. XII procedure | AC-063 | P0 |
| REQ-DOCS-064 | The amendment MUST NOT modify Art. IV (legality/copyright), Art. V (linguistic model integrity), Art. VII (architecture), or the body text of any other invariant article. The change is scope-widening, not invariant-weakening. | User decision (locked); §7.5 | AC-064 | P0 |
| REQ-DOCS-06C | `README.md` line 3 MUST be generalized to remove the "en inglés" scope claim. *The Eye of the World* MUST remain as an example of the initial corpus. The line MUST frame the app as multi-language. Exact diff intent in §7.4. | User decision (locked, v2.0.0 payload); §7.4 | AC-066 | P0 |
| REQ-DOCS-066 | `docs/product-vision.md` §4 "Usuario principal" MUST be generalized from "Persona adulta que lee literatura en inglés..." to a formulation equivalent to "Persona adulta que lee literatura en el idioma que estudia..." (final Spanish wording chosen in design). | User decision (locked, v2.0.0 payload); §7.3 | AC-067 | P0 |
| REQ-DOCS-067 | `docs/product-vision.md` §10 "Escenario principal" step 6 "Revisa phrasal verbs" MUST be generalized to reference **expresiones multipalabra específicas del idioma** (final Spanish wording chosen in design). | User decision (locked, v2.0.0 payload); §7.3 | AC-068 | P0 |
| REQ-DOCS-068 | `docs/product-vision.md` §12 "Roadmap" item 7 "Phrasal verbs" MUST be generalized similarly to reference expresiones multipalabra específicas del idioma. | User decision (locked, v2.0.0 payload); §7.3 | AC-069 | P0 |
| REQ-DOCS-069 | `docs/product-vision.md` §8 "Fuera de alcance inicial" MUST remain **unchanged**. Translation stays out of MVP scope. | User decision (locked); §7.3 | AC-070 | P0 |
| REQ-DOCS-06A | `AGENTS.md` §4 clause "Los phrasal verbs y expresiones multipalabra deben modelarse separadamente" MUST be generalized so phrasal verbs are named as **one instance** of "expresiones multipalabra específicas del idioma", preserving the separate-modeling rule (MWEs remain distinct from single-word lemmas). | User decision (locked, v2.0.0 payload); §7.5 | AC-071 | P0 |
| REQ-DOCS-06B | The four files listed above (`docs/constitution.md`, `docs/product-vision.md`, `README.md`, `AGENTS.md`) MUST ship in a **single coordinated amendment**. No partial applies allowed; verify phase MUST fail if any of the four is missing its change. | Coordination invariant; §7.6 | AC-072 | P0 |

### 1.7 Family G — Cross-references

| ID | Statement | Source | Acceptance (§11) | Priority |
|----|-----------|--------|------------------|----------|
| REQ-DOCS-070 | `AGENTS.md` MUST gain cross-reference footers pointing to: ADR index, architecture-baseline, glossary, traceability-matrix, definition-of-done, decisions-log, constitution. | Proposal §5.6; Exploration §1.4 (Constitution vs AGENTS.md drift) | AC-080 | P0 |
| REQ-DOCS-071 | `docs/constitution.md` MUST gain a cross-reference footer pointing to: ADR index, architecture-baseline, glossary, definition-of-done. | Bidirectionality (§10); Cross-reference contract | AC-081 | P0 |
| REQ-DOCS-072 | `docs/product-vision.md` MUST gain a cross-reference footer pointing to: constitution, glossary. | Bidirectionality (§10); Product-doc navigability | AC-082 | P1 |
| REQ-DOCS-073 | `docs/architecture/overview.md` MUST gain a cross-reference footer pointing to: architecture-baseline, ADR index. | Bidirectionality (§10); Baseline is the committed complement to overview | AC-083 | P1 |
| REQ-DOCS-074 | `README.md` MUST gain a `## Referencias metodológicas` section pointing to: constitution, AGENTS.md, glossary, ADR index, definition-of-done. Language of README stays ES; content addition is additive. | Discoverability; cognitive-doc-design signposting | AC-084 | P1 |
| REQ-DOCS-075 | Every cross-reference added by this change MUST be bidirectional: if file A links to file B for a topic, file B MUST link back to A for that topic where applicable (see §10 map). | Cross-reference contract; anti-drift | AC-085 | P0 |

### 1.8 Requirement count summary

| Family | Count |
|--------|-------|
| A — SDD/OpenSpec wiring | 6 |
| B — Architecture commitment | 12 |
| C — Domain legibility | 5 |
| D — Traceability formalization | 5 |
| E — Definition of Done extraction | 3 |
| F — Constitution + amendment payload (four-file coordinated) | 12 |
| G — Cross-references | 6 |
| **Total** | **49** |

---

## 2. Artifact catalog

Every artifact traces to ≥1 requirement; every requirement is satisfied by ≥1 artifact.

| # | Path | Language | Status | Purpose | Satisfies REQs |
|---|------|----------|--------|---------|----------------|
| 1 | `openspec/config.yaml` | EN | created | SDD bootstrap: project, stack, commands, persistence, strict_tdd, rules, gitignore-policy comment | REQ-DOCS-001, 002, 003 |
| 2 | `.atl/skill-registry.md` | EN | modified | Add SDD skill suite while preserving existing 11 entries and header/protocol | REQ-DOCS-004, 005, 006 |
| 3 | `docs/adr/README.md` | EN | created | ADR index, status vocabulary, numbering convention, authoring rules | REQ-DOCS-010 |
| 4 | `docs/adr/_template.md` | EN | created | Canonical ADR template with all required fields | REQ-DOCS-011 |
| 5 | `docs/adr/0001-monorepo-and-stack.md` | ES | unchanged (may receive cross-ref footer only) | Existing ADR-0001, content preserved | REQ-DOCS-012 |
| 6 | `docs/adr/0002-hexagonal-split.md` | EN | created (Wave 1) | Records hexagonal split codified in AGENTS.md §5 and constitution Art. VII | REQ-DOCS-013..016 |
| 7 | `docs/adr/0003-tdd-mandatory.md` | EN | created (Wave 1) | Records strict TDD workflow codified in AGENTS.md §3 and constitution Art. II | REQ-DOCS-013..016 |
| 8 | `docs/adr/0004-sdd-openspec.md` | EN | created (Wave 1) | Records SDD + OpenSpec as planning method | REQ-DOCS-013..016 |
| 9 | `docs/adr/0005-local-first.md` | EN | created (Wave 1) | Records local-first processing invariant from constitution Art. IV.4–5 | REQ-DOCS-013..016 |
| 10 | `docs/adr/0006-pos-per-occurrence.md` | EN | created (Wave 1) | Records POS-per-occurrence linguistic model from constitution Art. V.2–3 | REQ-DOCS-013..016 |
| 11 | `docs/adr/0007-manual-corrections-precedence.md` | EN | created (Wave 2) | Records manual-corrections precedence from constitution Art. V.8–9 | REQ-DOCS-013..016 |
| 12 | `docs/adr/0008-multi-language-scope.md` | EN | created (Wave 2) | Records three-part multi-language decision: (a) any-language corpora, (b) targeting via "reads literature in the language they study", (c) language-specific linguistic phenomena abstracted as "language-specific multiword expressions" | REQ-DOCS-013..016 |
| 13 | `docs/adr/0009-mwe-language-specific-instances.md` | EN | created (Wave 2) | **Title: "Multiword expressions as language-specific instances"**. Records that phrasal verbs are the English instance of an abstract MWE concept; Spanish uses locuciones/perífrasis; German uses separable verbs; domain stores `mwe_kind` with the language-specific value; MWEs remain first-class and separate from single-word lemmas. | REQ-DOCS-013..016 |
| 14 | `docs/adr/0010-documentation-language-policy.md` | EN | created (Wave 2) | Records EN methodology / ES product-facing language policy | REQ-DOCS-013..016 |
| 15 | `docs/architecture/architecture-baseline.md` | EN | created | Committed-state snapshot with three Mermaid diagrams and enumerated invariants | REQ-DOCS-017, 018 |
| 16 | `docs/decisions-log.md` | EN | created | Chronological decisions table seeded with historical + this-cycle entries | REQ-DOCS-019, 020, 021 |
| 17 | `docs/glossary.md` | ES | created | Product-facing glossary of linguistic-domain terms, including the abstract MWE entry | REQ-DOCS-030..034 |
| 18 | `docs/traceability-matrix.md` | EN scaffold, rows in ES | created | Cross-spec Markdown matrix with worked example row | REQ-DOCS-040, 041, 042, 044 |
| 19 | `AGENTS.md` §4 update | ES | amended (part of §7 payload) | Generalize phrasal-verb clause to name it as one instance of language-specific MWEs | REQ-DOCS-06A, 06B |
| 20 | `AGENTS.md` §10 update | ES | amended (additive) | Add hard DoD gate line for traceability-matrix | REQ-DOCS-043 |
| 21 | `AGENTS.md` cross-reference footer | ES | amended (additive) | Point to ADR index, baseline, glossary, matrix, DoD, decisions-log, constitution | REQ-DOCS-070, 075 |
| 22 | `docs/definition-of-done.md` | ES | created | Product-facing DoD summary quoting constitution Art. XI + AGENTS.md §10 | REQ-DOCS-050, 051, 052 |
| 23 | `docs/constitution.md` | ES | amended (v1.0.0 → v2.0.0 MAJOR) | Preamble generalized to multi-language scope, approval date added, version bump, amendment record | REQ-DOCS-060..064, 06B |
| 24 | `docs/constitution.md` cross-reference footer | ES | amended (additive) | Point to ADR index, baseline, glossary, DoD | REQ-DOCS-071, 075 |
| 25 | `docs/product-vision.md` amendment payload | ES | amended (§4, §10, §12; §8 explicitly untouched) | Generalize user framing (§4), MWE wording (§10 step 6, §12 item 7); §8 remains as-is | REQ-DOCS-066..069, 06B |
| 26 | `docs/product-vision.md` cross-reference footer | ES | amended (additive) | Point to constitution, glossary | REQ-DOCS-072, 075 |
| 27 | `docs/architecture/overview.md` cross-reference footer | ES | amended (additive) | Point to baseline, ADR index | REQ-DOCS-073, 075 |
| 28 | `README.md` line 3 amendment | ES | amended (part of §7 payload) | Generalize English-only scope claim; keep *The Eye of the World* as example initial corpus | REQ-DOCS-06C, 06B |
| 29 | `README.md` § Referencias metodológicas | ES | amended (additive) | Point to constitution, AGENTS.md, glossary, ADR index, DoD | REQ-DOCS-074, 075 |

**Artifact count**: 29 touch-points across 23 distinct files.

---

## 3. Artifact contracts

One subsection per artifact. Skeletons and non-negotiable properties only — content is spec/design phase output.

### 3.1 `openspec/config.yaml` (REQ-DOCS-001..003)

**Skeleton headings** (YAML top-level keys):

```yaml
schema: spec-driven
project: wheel-of-words
context: |
  Tech stack: {detected}
  Architecture: {detected}
  Testing: {detected}
  Style: {detected}
stack: {...}
test_commands: {...}
persistence_mode: hybrid
strict_tdd: true
skill_registry_path: .atl/skill-registry.md
change_slug_convention: kebab-case
rules:
  proposal: [...]
  specs: [...]
  design: [...]
  tasks: [...]
  apply: {...}
  verify: {...}
  archive: [...]
```

**Non-negotiable properties**:
- Valid YAML (parseable by any YAML 1.2 parser).
- Comment block explicitly encoding the gitignore policy for `openspec/changes/` (REQ-DOCS-002).
- `rules.specs` MUST include RFC 2119 keyword rule.
- `rules.apply.tdd` MUST be `true` (constitution Art. II mandates it).
- `strict_tdd: true` at top level (mirror of `rules.apply.tdd`).

**Language**: EN (methodology artifact).

### 3.2 `.atl/skill-registry.md` (REQ-DOCS-004..006)

**Skeleton preserved** (from current file): `# Skill Registry — wheel-of-words`, `## Sources scanned`, `## Contract`, `## Skills` (table), `## Loading protocol`.
**Non-negotiable properties**:
- Header auto-generation comment preserved verbatim.
- `Last updated` date bumped to change date.
- Table adds rows for all 11 SDD skills (see §8) without removing existing rows.
- Alphabetical ordering within the Skills table.
- All paths absolute.

### 3.3 `docs/adr/README.md` (REQ-DOCS-010)

**Skeleton headings**:
```
# ADR index — wheel-of-words
## Status vocabulary
## Numbering convention
## Authoring rules
## Index
```

**Non-negotiable properties**:
- Status vocabulary enumerated: `Proposed`, `Accepted`, `Superseded`, `Deprecated`.
- Numbering convention: global sequential, zero-padded 4-digit (`ADR-NNNN`).
- Index table columns: ID, title, status, date, wave.
- Language: EN.

### 3.4 `docs/adr/_template.md` (REQ-DOCS-011)

**Skeleton headings** (mandatory fields):
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

**Non-negotiable properties**:
- All headings above MUST be present in the template.
- Language: EN.

### 3.5 Seed ADRs 0002–0010 (REQ-DOCS-013..016)

Each seed ADR MUST:
- Conform to `_template.md`.
- Carry Status = `Accepted`.
- Carry the date per REQ-DOCS-014 (Wave 1 = 2026-07-15; Wave 2 = 2026-07-16).
- Ground its Context in the specific quote/clause listed in §4.
- Cross-reference to the constitution/AGENTS.md clause it grounds in.
- Language: EN.

**ADR-0009 specific contract**: title MUST be **"Multiword expressions as language-specific instances"**. Thesis MUST cover: phrasal verbs are the English instance; Spanish analogs are locuciones/perífrasis verbales; German analogs include separable verbs (Trennbare Verben); the domain model stores `mwe_kind` with the language-specific value; the abstract "MWE" concept remains first-class and separate from single-word lemma modeling.

**ADR-0008 specific contract**: thesis MUST cover three parts: (a) libros analizados pueden ser de cualquier idioma; (b) targeting del usuario se define por "lee literatura en el idioma que estudia", no por el idioma específico; (c) fenómenos lingüísticos específicos del idioma se modelan como categoría abstracta "expresiones multipalabra específicas del idioma".

### 3.6 `docs/architecture/architecture-baseline.md` (REQ-DOCS-017, 018)

**Skeleton headings**:
```
# Architecture Baseline — wheel-of-words
**Date**: 2026-07-16
**Status**: Committed
## Purpose (baseline vs overview distinction)
## Committed invariants (enumerated)
## System context diagram (Mermaid)
## Hexagonal layers diagram (Mermaid)
## Linguistic data flow diagram (Mermaid)
## What is deferred
## References
```

**Non-negotiable properties**:
- Three Mermaid code fences MUST parse without syntax errors.
- Committed invariants list MUST match the enumeration in REQ-DOCS-018, including the abstract MWE framing (phrasal verbs cited as English instance).
- Language: EN.

### 3.7 `docs/decisions-log.md` (REQ-DOCS-019..021)

**Skeleton headings**:
```
# Decisions log — wheel-of-words
## How this log works
## Log
| Date | Decision | Category | Ref | Motivation | Consequences |
```

**Non-negotiable properties**:
- Seed rows enumerated in §4.3.
- Engineering Playbook deferral entry MUST include verbatim trigger from REQ-DOCS-021 (first-slice = "upload a `.txt` file and view a lemma list with frequency"; translation NOT part of first-slice).
- Language: EN.

### 3.8 `docs/glossary.md` (REQ-DOCS-030..034)

**Skeleton headings**:
```
# Glosario del dominio lingüístico
## Cómo usar este glosario
## Categorías
## Términos
```

**Non-negotiable properties**:
- Each entry heading is the term in Spanish.
- Each entry body: category label + one-line definition + cross-references + multi-language note.
- Entries listed alphabetically.
- The abstract "expresión multipalabra específica del idioma" entry MUST list phrasal verbs (English), locuciones/perífrasis verbales (Spanish), and separable verbs (German) as **example instances**, not as canonical sibling entries.
- The phrasal-verb entry MUST be re-positioned as an instance-example of the abstract MWE entry.
- Language: ES.

### 3.9 `docs/traceability-matrix.md` (REQ-DOCS-040..044)

**Skeleton headings**:
```
# Matriz de trazabilidad — wheel-of-words
## Propósito
## Reglas de actualización
## Matriz
| REQ-ID | Criterio de aceptación | Archivo(s) de prueba | Tarea(s) | Estado |
```

**Non-negotiable properties**:
- Column set matches §6.1.
- One worked-example row seeded (§6.2).
- Update rules explicitly described in-file (§6.3).

### 3.10 `docs/definition-of-done.md` (REQ-DOCS-050..052)

**Skeleton headings**:
```
# Definición de Terminado — Wheel Vocabulary
## Alcance y jerarquía (constitución es canónica)
## Criterios (referencia constitución Art. XI)
## Criterios operativos (referencia AGENTS.md §10)
## Puerta de trazabilidad
## Referencias
```

**Non-negotiable properties**:
- Explicit statement: "Constitución Art. XI es la fuente canónica en caso de conflicto."
- Quote or link (not duplicate) constitution Art. XI and AGENTS.md §10.
- Language: ES.

### 3.11 `docs/constitution.md` (amended v1.0.0 → v2.0.0) (REQ-DOCS-060..064, 06B)

**Amendment touches**:
- Preamble: generalized to remove "vocabulario inglés" as sole scope; English framed as one supported language among many (see §7.2).
- Header block: add `**Fecha de aprobación:** 2026-07-15`.
- Version bump: `1.0.0` → `2.0.0` MAJOR.
- Amendment record per Art. XII (see §7.2).

**Non-negotiable properties**:
- No modification to Art. I, II, III, IV, V, VI, VII, VIII, IX, X, XI body text.
- Art. XII body text unchanged; only appended amendment record entry OR new adjacent `## Registro de enmiendas` section.
- Language preserved: ES.

### 3.12 `docs/product-vision.md` amendment payload (REQ-DOCS-066..069, 06B)

**Amendment touches**:
- §4 "Usuario principal": generalize target from "literatura en inglés" to "literatura en el idioma que estudia" (final Spanish wording chosen in design).
- §10 "Escenario principal" step 6: generalize "Revisa phrasal verbs" to "Revisa expresiones multipalabra específicas del idioma" (or the wording finalized per OQ-10).
- §12 "Roadmap" item 7: generalize "Phrasal verbs" similarly.
- §8 "Fuera de alcance inicial": **NO CHANGE**. Translation remains out of MVP scope.

**Non-negotiable properties**:
- §1, §2, §3, §5, §6, §7, §8, §9, §11 body text: unchanged.
- Language preserved: ES.

### 3.13 `AGENTS.md` (amended) (REQ-DOCS-043, 06A, 06B, 070, 075)

**Amendment touches**:
- §4 clause "Los phrasal verbs y expresiones multipalabra deben modelarse separadamente" → generalized to name phrasal verbs as one instance of "expresiones multipalabra específicas del idioma", preserving the separate-modeling rule.
- §10 gains one bullet with the exact wording from §6.4 (traceability-matrix DoD gate).
- New `## Referencias` section with links to: constitution, ADR index, architecture-baseline, glossary, traceability-matrix, definition-of-done, decisions-log.

**Non-negotiable properties**:
- No modification to §1, §2, §3, §5, §6, §7, §8, §9, §11 body text.
- Language preserved: ES.

### 3.14 `README.md` (amended) (REQ-DOCS-06C, 074, 075, 06B)

**Amendment touches**:
- Line 3: generalized to remove "en inglés" scope claim; keep *The Eye of the World* as example initial corpus; frame as multi-language.
- New `## Referencias metodológicas` section linking to constitution, AGENTS.md, glossary, ADR index, DoD.

**Non-negotiable properties**:
- Repo-tree diagram (§Contenido): unchanged.
- Flow diagram: unchanged.
- Alcance del paquete, siguiente especificación recomendada: unchanged.
- Language preserved: ES.

### 3.15 Cross-reference footers on `architecture/overview.md` (REQ-DOCS-073, 075)

**Amendment touches** (additive footer only):
- `architecture/overview.md`: `## Referencias` section linking to architecture-baseline, ADR index.

**Non-negotiable properties**:
- Additive only. No body-text rewrites. Language preserved: ES.

---

## 4. ADR seed catalog

### 4.1 Wave assignment and grounding

| ADR ID | Title | Thesis (one line) | Status | Date | Grounding quote/clause | Wave |
|--------|-------|-------------------|--------|------|------------------------|------|
| ADR-0001 | Monorepositorio y stack inicial | (Existing — unchanged) | Aceptado | 2026-07-15 | (Existing) | — (pre-existing) |
| ADR-0002 | Hexagonal split into `domain` / `application` / `infrastructure` / `api` | Backend organised in four layers with strict dependency direction. | Accepted | 2026-07-15 | AGENTS.md §5; Constitution Art. VII.1–4 | 1 |
| ADR-0003 | TDD mandatory with strict RED → GREEN → REFACTOR | Every behavior begins with a failing test; refactor requires green suite. | Accepted | 2026-07-15 | AGENTS.md §3; Constitution Art. II.1–4 | 1 |
| ADR-0004 | SDD + OpenSpec as planning method | All features flow through spec → acceptance → plan → test-plan → tasks → traceability before code. | Accepted | 2026-07-15 | AGENTS.md §1; Constitution Art. I.1–5 | 1 |
| ADR-0005 | Local-first processing, no third-party data egress by default | Local processing is the default; sending book content to third parties requires explicit consent. | Accepted | 2026-07-15 | Constitution Art. IV.4–5; AGENTS.md §4 | 1 |
| ADR-0006 | POS-per-occurrence linguistic model | Contextual POS is stored per occurrence and aggregated; no single global POS per lemma. | Accepted | 2026-07-15 | Constitution Art. V.2–3; AGENTS.md §4 | 1 |
| ADR-0007 | Manual corrections precedence and reprocessing safety | Manual corrections override automatic results and MUST survive reprocessing. | Accepted | 2026-07-16 | Constitution Art. V.8–9; AGENTS.md §4 | 2 |
| ADR-0008 | Multi-language support scope, from day one | (a) Corpora may be in **any language** legally provided by the user; (b) user targeting is defined as "reads literature in the language they study", not by a specific language; (c) language-specific linguistic phenomena are modeled as an abstract category "language-specific multiword expressions", instantiated per language. | Accepted | 2026-07-16 | User decision this session; Constitution amendment v2.0.0 (REQ-DOCS-060 series) | 2 |
| ADR-0009 | **Multiword expressions as language-specific instances** | Phrasal verbs are the English instance of an abstract MWE concept; Spanish analogs are locuciones/perífrasis verbales; German analogs include separable verbs; the domain stores `mwe_kind` with the language-specific value. MWEs remain first-class and separate from single-word lemma modeling. | Accepted | 2026-07-16 | Constitution Art. V.6 (post-amendment reading); AGENTS.md §4 (post-amendment); Constitution amendment v2.0.0 | 2 |
| ADR-0010 | Documentation language policy: methodology EN, product-facing ES | Methodology artifacts default to English; product-facing artifacts default to Spanish. | Accepted | 2026-07-16 | User decision this session (locked); Proposal §5 language mapping | 2 |

**Seed ADR count**: 9 new ADRs (0002–0010) + 1 existing (0001) = 10 total.
**Wave split**: Wave 1 = 5 ADRs (0002–0006); Wave 2 = 4 ADRs (0007–0010).

### 4.2 Candidate ADRs deferred to future cycles

Recorded for completeness so future ADR authors do not re-discover them. **Do NOT create in this change.**

| Candidate | Reason to defer |
|-----------|-----------------|
| Language detection strategy | OQ-2 open; strategy undecided (bundled model vs API vs heuristic) |
| Translation provider strategy | OQ-3 open; requires consent-model design (constitution Art. IV.5) |
| NLP library selection per language | OQ-4 open; depends on multi-language coverage requirements |
| OpenAPI as contract source of truth | Partially captured in ADR-0001 alternatives |
| Alembic as migration tool | Captured in ADR-0001 stack listing |
| SQLite as MVP persistence | Captured in ADR-0001 |
| Docker Compose optional | Captured in ADR-0001 alternatives |
| Manual-corrections UX shape (day-one vs deferred) | OQ-1 open |

### 4.3 Decisions-log seed rows (REQ-DOCS-020, 021)

Rows the log MUST contain at creation time, in chronological order:

| Date | Decision | Category | Ref |
|------|----------|----------|-----|
| 2026-07-15 | Constitution v1.0.0 adopted | governance | `docs/constitution.md` |
| 2026-07-15 | ADR-0001: Monorepo + stack | architecture | `docs/adr/0001-monorepo-and-stack.md` |
| 2026-07-15 | SPEC-001 fundación técnica decisions DEC-001..006 | product/architecture | `specs/001-project-foundation/decisions.md` |
| 2026-07-15 | ADR-0002 hexagonal split | architecture | `docs/adr/0002-hexagonal-split.md` |
| 2026-07-15 | ADR-0003 TDD mandatory | methodology | `docs/adr/0003-tdd-mandatory.md` |
| 2026-07-15 | ADR-0004 SDD + OpenSpec | methodology | `docs/adr/0004-sdd-openspec.md` |
| 2026-07-15 | ADR-0005 local-first | architecture/privacy | `docs/adr/0005-local-first.md` |
| 2026-07-15 | ADR-0006 POS-per-occurrence | linguistic-model | `docs/adr/0006-pos-per-occurrence.md` |
| 2026-07-16 | ADR-0007 manual corrections precedence | linguistic-model | `docs/adr/0007-manual-corrections-precedence.md` |
| 2026-07-16 | ADR-0008 multi-language scope (three-part: any-language corpora + user-targeting-by-study-language + abstract MWE category) | product/architecture | `docs/adr/0008-multi-language-scope.md` |
| 2026-07-16 | ADR-0009 Multiword expressions as language-specific instances | linguistic-model | `docs/adr/0009-mwe-language-specific-instances.md` |
| 2026-07-16 | ADR-0010 documentation language policy | methodology | `docs/adr/0010-documentation-language-policy.md` |
| 2026-07-16 | Constitution amended to v2.0.0 (MAJOR): multi-language scope + approval date + four-file coordinated payload | governance | `docs/constitution.md` §amendments |
| 2026-07-16 | Engineering Playbook deferred; trigger = **after first vertical slice ships end-to-end (upload a `.txt` file and view a lemma list with frequency)** | methodology | this change proposal §4 non-goals |
| 2026-07-16 | docs-methodology-overhaul cycle executed | governance | `openspec/changes/docs-methodology-overhaul/` |

---

## 5. Glossary catalog

### 5.1 Required terms (REQ-DOCS-032, 034)

The glossary MUST cover, at minimum, these 13 terms sourced from AGENTS.md §4 and constitution Art. V (post-amendment). The abstract MWE entry is canonical; phrasal verb is repositioned as an instance.

| Term (ES) | Category | One-line definition target | Cross-refs | Multi-language note |
|-----------|----------|---------------------------|------------|---------------------|
| Token | concept | Unidad léxica primaria extraída durante la tokenización, previa a la normalización. | AGENTS.md §4; Constitution Art. V.1 | Language-agnostic; segmentation rules vary by language |
| Forma textual | attribute | Cadena exacta tal como aparece en el texto original, sin transformación. | AGENTS.md §4; Constitution Art. V.1 | Language-agnostic |
| Forma normalizada | attribute | Cadena tras aplicar normalización determinista. | AGENTS.md §4; Constitution Art. V.1 | Normalization rules are language-specific |
| Lema | entity | Forma canónica que agrupa formas flexionadas equivalentes. | AGENTS.md §4; Constitution Art. V.1, V.4 | Lemmatization models are language-specific |
| Categoría gramatical contextual | attribute | POS asignado a una aparición concreta, no al lema global. | AGENTS.md §4; Constitution Art. V.2–3 | Tagsets vary by language and NLP model |
| Aparición | entity | Instancia individual de una forma/lema en el texto. | AGENTS.md §4; Constitution Art. V.3 | Language-agnostic |
| **Expresión multipalabra específica del idioma** (abstract entry, wording per OQ-10) | entity (abstract) | Categoría abstracta que agrupa fenómenos léxicos multipalabra propios de cada idioma; se instancia con `mwe_kind`. Ejemplos: phrasal verbs (inglés), locuciones y perífrasis verbales (español), verbos separables (alemán). | AGENTS.md §4 (post-amendment); Constitution Art. V.6 (post-amendment); ADR-0008; ADR-0009 | Abstract concept; instances are language-specific |
| Phrasal verb (instancia inglesa) | entity (instance) | Verbo compuesto por verbo + partícula(s); instancia inglesa de la expresión multipalabra específica del idioma. | AGENTS.md §4; Constitution Art. V.6; ADR-0009 | English-specific instance |
| Expresión multipalabra | entity | Unidad léxica compuesta por dos o más tokens tratados como un solo lema. Concepto general del que la entrada abstracta anterior es una especialización lingüística. | AGENTS.md §4; Constitution Art. V.6 | Language-agnostic pattern; instances are language-specific |
| Procedencia | attribute | Metadatos que registran fuente, versión, fecha y confianza de un resultado automático. | AGENTS.md §4; Constitution Art. V.7 | Language-agnostic |
| Puntuación de confianza | attribute | Nivel numérico de certeza asociado a un resultado automático incierto. | AGENTS.md §4; Constitution Art. V.7 | Language-agnostic |
| Corrección manual | process | Ajuste realizado por el usuario que prevalece sobre el resultado automático. | AGENTS.md §4; Constitution Art. V.8–9 | Language-agnostic |
| Reprocesamiento | process | Nueva ejecución del pipeline lingüístico sin sobrescribir correcciones manuales. | AGENTS.md §4; Constitution Art. V.9 | Language-agnostic |

---

## 6. Traceability matrix schema

### 6.1 Columns definition (REQ-DOCS-041)

Columns: `REQ ID | Statement | Acceptance criterion ref | Test file(s) | Task(s) | Status`

| Column | Type | Description |
|--------|------|-------------|
| REQ ID | string | `REQ-<feature>-<n>` identifier. |
| Statement | string | One-line summary of the requirement. |
| Acceptance criterion ref | string | AC-ID reference or path to spec acceptance section. |
| Test file(s) | string | Path(s) to test file(s) or test-ID(s). |
| Task(s) | string | T-ID reference(s). |
| Status | enum | `Pendiente` \| `En progreso` \| `Cumplido` \| `Bloqueado` |

Column names are English scaffold (methodology artifact language); status vocabulary is Spanish to match SPEC-001 conventions. This schema was ratified after Slice D apply.

### 6.2 Worked-example row (REQ-DOCS-042)

```
| REQ-DOCS-004 | AC-004 | (manual review of .atl/skill-registry.md diff) | (this change's Wave-A tasks) | Pasando |
```

### 6.3 Update rules (REQ-DOCS-044)

1. Add a row when a new `REQ-<feature>-<n>` is created.
2. Update `Estado` when the corresponding task closes.
3. Move `Estado` to `Obsoleto` — do NOT delete — when a requirement is superseded.
4. `Bloqueado` requires a linked reason.
5. Ownership: the person closing the referenced task is responsible for the row update.

### 6.4 DoD gate wording for AGENTS.md §10 (REQ-DOCS-043)

Exact bullet to add to `AGENTS.md` §10 (verbatim, Spanish):

```
- La matriz de trazabilidad se ha actualizado con los identificadores de requisito, criterio de aceptación, prueba y tarea correspondientes.
```

---

## 7. Constitution + amendment payload (v1.0.0 → v2.0.0 MAJOR)

The amendment is a **coordinated four-file payload**. Any partial apply is a spec violation.

### 7.1 Files touched

| File | Change kind | Requirements |
|------|-------------|--------------|
| `docs/constitution.md` | Preamble generalization, date add, version bump, amendment record | REQ-DOCS-060..064 |
| `docs/product-vision.md` | §4 user targeting, §10 step 6 MWE wording, §12 item 7 MWE wording; §8 untouched | REQ-DOCS-066..069 |
| `README.md` | Line 3 English-only scope claim removed; example corpus retained | REQ-DOCS-06C |
| `AGENTS.md` | §4 phrasal-verb clause generalized to name it as one instance of language-specific MWEs | REQ-DOCS-06A |
| Coordination invariant | All four ship together; no partial applies | REQ-DOCS-06B |

### 7.2 Constitution changes

**Preamble** (current lines 8–11):
```
Wheel Vocabulary es una aplicación web destinada a extraer, clasificar, consultar y estudiar vocabulario inglés procedente de obras literarias aportadas legalmente por el usuario.

La constitución define principios no negociables. Las especificaciones pueden evolucionar, pero ninguna feature puede contradecir estas reglas sin una enmienda explícita.
```

**Amendment intent** (design phase writes final Spanish prose):
- Scope covers vocabulary in **any human language** legally provided by the user.
- English is framed as **one supported language among many** — no longer as the sole scope, and no longer as the "first-class" exclusive default. English MAY still be mentioned as the first-implemented language for continuity with existing artifacts.
- No invariant is weakened. Art. IV (copyright/privacy), Art. V (linguistic model), Art. VII (architecture), and all other articles remain **textually unchanged**.

**Header additions**:
- Add: `**Fecha de aprobación:** 2026-07-15` immediately below the existing status line.
- Bump: `**Versión:** 1.0.0` → `**Versión:** 2.0.0`.

**Amendment record entry (Art. XII procedure)**:

| Field | Value |
|-------|-------|
| Fecha | 2026-07-16 |
| Cambio | Generalización del preámbulo para cubrir vocabulario en cualquier idioma aportado legalmente por el usuario. Incorporación de fecha de aprobación. Coordinación con cambios en README, product-vision y AGENTS.md. |
| Motivación | La aplicación se diseña multi-idioma desde el primer ciclo. El cambio no es una ampliación aditiva simple: reformula el alcance conceptual del proyecto (usuario, corpus y modelado lingüístico) coordinadamente en cuatro archivos. |
| Consecuencias | (1) ADR-0008 codifica el alcance multi-idioma en tres partes. (2) ADR-0009 reformula MWEs como instancias específicas del idioma. (3) README, product-vision, AGENTS.md ajustan su lenguaje coordinadamente. (4) Detección de idioma, selección de modelo NLP por idioma y proveedor de traducción quedan como decisiones abiertas. (5) Ningún artículo invariante se debilita. |
| Versión anterior | 1.0.0 |
| Versión nueva | 2.0.0 (MAJOR) |

**Version-bump verdict**: `v2.0.0-major`.

**Rationale**:
- Art. XII procedure: incompatible → major; compatible extension → minor; editorial → patch.
- The change touches **four files simultaneously** and reformulates conceptual scope (user targeting, corpus scope, MWE abstraction). It is not a compatible extension of the constitution alone — it re-frames the product across the entire documentation contract.
- Multi-language expansion + user-targeting generalization + MWE abstraction across four files is **not** a compatible extension.

### 7.3 `docs/product-vision.md` changes

- **§4 "Usuario principal"**: current "Persona adulta que lee literatura en inglés, desea ampliar vocabulario..." → generalize to "Persona adulta que lee literatura en el idioma que estudia, desea ampliar vocabulario..." (or equivalent Spanish wording chosen in design).
- **§10 "Escenario principal" step 6**: current "Revisa phrasal verbs" → generalize to reference "expresiones multipalabra específicas del idioma" (final wording per OQ-10).
- **§12 "Roadmap" item 7**: current "Phrasal verbs" → generalize similarly.
- **§8 "Fuera de alcance inicial"**: **NO CHANGE**. Translation stays out of MVP scope.
- **§1, §2, §3, §5, §6, §7, §9, §11 body text**: unchanged.

### 7.4 `README.md` change

- **Line 3**: current "aplicación web de análisis de vocabulario literario en inglés, comenzando por *The Eye of the World* como primer corpus" → generalize to remove "en inglés" as a scope claim. *The Eye of the World* MUST remain as an example initial corpus. Frame the app as multi-language. Final Spanish wording chosen in design.
- Repo-tree diagram, flow diagram, alcance section, siguiente especificación: **unchanged**.

### 7.5 `AGENTS.md` change

- **§4** clause "Los phrasal verbs y expresiones multipalabra deben modelarse separadamente" → generalize so phrasal verbs are named as **one instance** of "expresiones multipalabra específicas del idioma", preserving the separate-modeling rule (MWEs remain distinct from single-word lemmas).
- **§1, §2, §3, §5, §6, §7, §8, §9, §11 body text**: unchanged.

Explicit non-modifications (REQ-DOCS-064):
- Art. I, II, III, **IV (Legalidad, privacidad y derechos de autor — critical invariant)**, **V (Integridad del modelo lingüístico — critical invariant, ONLY the phrasal-verb reading is generalized via ADR-0009, article text unchanged)**, VI, **VII (Arquitectura — critical invariant)**, VIII, IX, X, XI body text.
- Art. XII body text (only appended amendment record entry).

### 7.6 Coordination invariant (REQ-DOCS-06B)

All four files MUST ship in one coordinated amendment. Verify phase MUST fail if any of the four is missing its change. The apply plan (in `sdd-tasks`) MUST group these four amendments into a single slice.

---

## 8. Skill-registry contract

### 8.1 Minimum entries required (REQ-DOCS-004)

The updated `.atl/skill-registry.md` `## Skills` table MUST include at least the SDD skill suite, in addition to preserving the 11 existing user-scoped skills.

| Skill | Trigger / description | Scope | Absolute path |
|-------|-----------------------|-------|---------------|
| `sdd-init` | Initialize SDD context, testing capabilities, registry, and persistence. | user | `/Users/isildur/.config/opencode/skills/sdd-init/SKILL.md` |
| `sdd-explore` | Explore SDD ideas before committing to a change. | user | `/Users/isildur/.config/opencode/skills/sdd-explore/SKILL.md` |
| `sdd-propose` | Create an SDD change proposal with intent, scope, and approach. | user | `/Users/isildur/.claude/skills/sdd-propose/SKILL.md` |
| `sdd-spec` | Write SDD delta specs with requirements and scenarios. | user | `/Users/isildur/.config/opencode/skills/sdd-spec/SKILL.md` |
| `sdd-design` | Create the SDD technical design and architecture approach. | user | `/Users/isildur/.config/opencode/skills/sdd-design/SKILL.md` |
| `sdd-tasks` | Break an SDD change into implementation tasks. | user | `/Users/isildur/.config/opencode/skills/sdd-tasks/SKILL.md` |
| `sdd-apply` | Implement SDD tasks from specs and design. | user | `/Users/isildur/.config/opencode/skills/sdd-apply/SKILL.md` |
| `sdd-verify` | Execute tests and prove implementation matches specs, design, and tasks. | user | `/Users/isildur/.config/opencode/skills/sdd-verify/SKILL.md` |
| `sdd-archive` | Archive a completed SDD change by syncing delta specs. | user | `/Users/isildur/.config/opencode/skills/sdd-archive/SKILL.md` |
| `sdd-onboard` | Walk users through the SDD workflow on the real codebase. | user | `/Users/isildur/.config/opencode/skills/sdd-onboard/SKILL.md` |
| `skill-registry` | Index available skills by trigger and path. | user | `/Users/isildur/.config/opencode/skills/skill-registry/SKILL.md` |

### 8.2 Ordering rule

Rows MUST be alphabetically sorted by skill name (case-insensitive).

### 8.3 Update policy

Regenerate via `gentle-ai skill-registry refresh --force` whenever:
- A new skill is installed under any scanned source.
- A skill's `SKILL.md` moves to a new path.
- A skill's frontmatter `description` (trigger text) changes materially.

---

## 9. `openspec/config.yaml` contract

### 9.1 Required top-level fields (REQ-DOCS-001, 003)

- `schema: spec-driven`
- `project: wheel-of-words`
- `context: |` (multiline block)
- `stack:` (object)
- `test_commands:` (object)
- `persistence_mode: hybrid`
- `strict_tdd: true`
- `skill_registry_path: .atl/skill-registry.md`
- `change_slug_convention: kebab-case`
- `rules:` (object keyed by phase)

### 9.2 `rules` sub-keys (REQ-DOCS-003)

At minimum:
- `rules.proposal`: `["Include rollback plan for risky changes", "Docs-only changes MAY omit rollback"]`
- `rules.specs`: `["Use Given/When/Then for scenarios", "Use RFC 2119 keywords (MUST, SHALL, SHOULD, MAY)", "Requirement IDs follow REQ-<feature>-<n>"]`
- `rules.design`: `["Include sequence diagrams for complex flows", "Document architecture decisions with rationale (link ADR)"]`
- `rules.tasks`: `["Group by phase (Fase A, Fase B, ...)", "Use T<n> [TIPO] descripción format", "TDD order: TEST → IMPL → REFACTOR"]`
- `rules.apply.tdd: true`
- `rules.apply.test_command: "make test"` (placeholder)
- `rules.verify.test_command: "make test"` / `rules.verify.build_command: "make lint && make typecheck"`
- `rules.verify.coverage_threshold: 80` (per constitution Art. II)
- `rules.archive`: `["Warn before merging destructive deltas", "Confirm traceability matrix updated before archive"]`

### 9.3 Gitignore-policy comment block (REQ-DOCS-002)

```yaml
# When repo is git-initialized:
#   - commit openspec/config.yaml (this file)
#   - commit openspec/specs/ (baseline specs)
#   - gitignore openspec/changes/ (ephemeral SDD planning artifacts; re-hydrate from Engram if needed)
```

### 9.4 Change-slug convention

- Kebab-case (`docs-methodology-overhaul`, `spec-002-txt-import`, etc.).
- No trailing dates in the slug; dates belong to the archive-phase directory rename.

---

## 10. Cross-reference contract

Bidirectional cross-reference map.

| From file | Must link to | Requirement |
|-----------|-------------|-------------|
| `AGENTS.md` | constitution, ADR index, architecture-baseline, glossary, traceability-matrix, definition-of-done, decisions-log | REQ-DOCS-070 |
| `docs/constitution.md` | ADR index, architecture-baseline, glossary, definition-of-done | REQ-DOCS-071 |
| `docs/product-vision.md` | constitution, glossary | REQ-DOCS-072 |
| `docs/architecture/overview.md` | architecture-baseline, ADR index | REQ-DOCS-073 |
| `README.md` | constitution, AGENTS.md, glossary, ADR index, definition-of-done | REQ-DOCS-074 |
| `docs/adr/README.md` | constitution, architecture-baseline, decisions-log | derived from REQ-DOCS-010 |
| `docs/adr/*.md` (each ADR) | constitution/AGENTS.md clause grounding, decisions-log entry | derived from REQ-DOCS-013 |
| `docs/architecture/architecture-baseline.md` | ADR index, glossary, overview | derived from REQ-DOCS-017 |
| `docs/glossary.md` | constitution Art. V, AGENTS.md §4 | derived from REQ-DOCS-030 |
| `docs/definition-of-done.md` | constitution Art. XI, AGENTS.md §10, traceability-matrix | derived from REQ-DOCS-050 |
| `docs/decisions-log.md` | ADR index (per-row), constitution amendments section | derived from REQ-DOCS-019 |
| `docs/traceability-matrix.md` | AGENTS.md §10, per-spec traceability files | derived from REQ-DOCS-040 |

**Bidirectionality check (REQ-DOCS-075)**: for every A → B link above, either B already contains A in its cross-references or B MUST be updated to include A.

---

## 11. Acceptance criteria

### Family A

- **AC-001 (REQ-DOCS-001)**: Given the repo, When a YAML parser loads `openspec/config.yaml`, Then it succeeds and the parsed document contains keys `project`, `stack`, `test_commands`, `persistence_mode`, `strict_tdd`, `skill_registry_path`, `change_slug_convention`, `rules`.
- **AC-002 (REQ-DOCS-002)**: Given `openspec/config.yaml`, When a human reads the top of the file, Then a comment block explicitly states the gitignore policy for `openspec/changes/`.
- **AC-003 (REQ-DOCS-003)**: Given the parsed config, Then `rules` has sub-keys `proposal`, `specs`, `design`, `tasks`, `apply`, `verify`, `archive`; `rules.apply.tdd` is `true`; `rules.specs` mentions RFC 2119.
- **AC-004 (REQ-DOCS-004)**: Given `.atl/skill-registry.md`, When the Skills table is scanned, Then every skill name in §8.1 appears with correct scope and absolute path.
- **AC-005 (REQ-DOCS-005)**: Given a diff of `.atl/skill-registry.md` before/after, Then every previously listed skill row is present.
- **AC-006 (REQ-DOCS-006)**: Given `.atl/skill-registry.md`, Then the header auto-generation comment and `## Loading protocol` section are byte-identical (except `Last updated` date).

### Family B

- **AC-010 (REQ-DOCS-010)**: Given `docs/adr/README.md`, Then it contains status vocabulary, numbering convention, authoring rules, and index; status vocabulary enumerates exactly `Proposed`, `Accepted`, `Superseded`, `Deprecated`.
- **AC-011 (REQ-DOCS-011)**: Given `docs/adr/_template.md`, Then it contains headings for Status, Date, Context, Decision, Consequences (Positive/Negative), Alternatives considered, References.
- **AC-012 (REQ-DOCS-012)**: Given `docs/adr/0001-monorepo-and-stack.md`, Then the decision text body is byte-identical to its pre-change version.
- **AC-013 (REQ-DOCS-013)**: Given the 9 seed ADR files, Then each conforms to `_template.md` and its Context section grounds in §4.1.
- **AC-014 (REQ-DOCS-014)**: Given the seed ADR front matter, Then ADR-0002..0006 dates are `2026-07-15` and ADR-0007..0010 dates are `2026-07-16`.
- **AC-015 (REQ-DOCS-015)**: Given the seed ADR front matter, Then every seed ADR status equals `Accepted`.
- **AC-016 (REQ-DOCS-016)**: Given `docs/adr/README.md` index, Then the index shows Wave 1 for ADR-0002..0006 and Wave 2 for ADR-0007..0010.
- **AC-017 (REQ-DOCS-017)**: Given `docs/architecture/architecture-baseline.md`, Then it contains three Mermaid code fences (system-context, hexagonal-layers, linguistic-data-flow) that parse.
- **AC-018 (REQ-DOCS-018)**: Given `docs/architecture/architecture-baseline.md`, Then the "Committed invariants" section enumerates local-first, hexagonal split, SQLite MVP, spaCy first adapter, manual-corrections precedence, POS-per-occurrence, MWEs modeled separately (with phrasal verbs cited as the English instance), provenance stored.
- **AC-019 (REQ-DOCS-019)**: Given `docs/decisions-log.md`, Then it contains the table with columns Date, Decision, Category, Ref, Motivation, Consequences.
- **AC-020 (REQ-DOCS-020)**: Given `docs/decisions-log.md`, Then every seed row in §4.3 is present.
- **AC-021 (REQ-DOCS-021)**: Given `docs/decisions-log.md`, Then the Engineering Playbook deferral row includes the exact revisit-trigger string: "After first vertical slice ships end-to-end (upload a `.txt` file and view a lemma list with frequency)".

### Family C

- **AC-030 (REQ-DOCS-030)**: Given `docs/glossary.md`, Then the file exists and is written in Spanish.
- **AC-031 (REQ-DOCS-031)**: Given each glossary entry, Then it contains category label, one-line definition, and at least one cross-reference link.
- **AC-032 (REQ-DOCS-032)**: Given the glossary, Then every term in §5.1 has a dedicated entry.
- **AC-033 (REQ-DOCS-033)**: Given each glossary entry, Then it contains an explicit multi-language-impact note.
- **AC-034 (REQ-DOCS-034)**: Given the glossary, Then the abstract "expresión multipalabra específica del idioma" entry lists phrasal verbs (English), locuciones/perífrasis verbales (Spanish), and separable verbs (German) as example instances; the phrasal-verb entry is positioned as an instance-example, not a canonical sibling.

### Family D

- **AC-040 (REQ-DOCS-040)**: Given `docs/traceability-matrix.md`, Then it exists as a Markdown file with a table.
- **AC-041 (REQ-DOCS-041)**: Given the matrix, Then the columns are exactly those in §6.1.
- **AC-042 (REQ-DOCS-042)**: Given the matrix, Then at least one row has `Estado` != `Pendiente`.
- **AC-043 (REQ-DOCS-043)**: Given `AGENTS.md` §10, Then it contains the exact bullet defined in §6.4.
- **AC-044 (REQ-DOCS-044)**: Given the matrix file, Then it contains a "Reglas de actualización" section describing the five rules from §6.3.

### Family E

- **AC-050 (REQ-DOCS-050)**: Given `docs/definition-of-done.md`, Then the file exists in Spanish and quotes or links Constitution Art. XI and AGENTS.md §10.
- **AC-051 (REQ-DOCS-051)**: Given the DoD file, Then it contains an explicit sentence stating "Constitución Art. XI es canónica en caso de conflicto." (or semantically equivalent).
- **AC-052 (REQ-DOCS-052)**: Given the DoD file, Then it does not verbatim-duplicate the constitution beyond the reference block.

### Family F

- **AC-060 (REQ-DOCS-060)**: Given `docs/constitution.md`, When the preamble is read, Then it no longer scopes to "vocabulario inglés" alone; English is framed as one supported language among many.
- **AC-061 (REQ-DOCS-061)**: Given the constitution header, Then it includes `**Fecha de aprobación:** 2026-07-15`.
- **AC-062 (REQ-DOCS-062)**: Given the constitution header, Then version reads `2.0.0`.
- **AC-063 (REQ-DOCS-063)**: Given the constitution, Then an amendment record entry exists with Fecha=2026-07-16, Cambio, Motivación, Consecuencias, Versión anterior=1.0.0, Versión nueva=2.0.0 (matching §7.2 values).
- **AC-064 (REQ-DOCS-064)**: Given a diff of the constitution before/after, Then no body text of Art. I–XI is modified; Art. XII may only be extended.
- **AC-066 (REQ-DOCS-06C)**: Given `README.md`, Then line 3 no longer claims English-only scope; *The Eye of the World* remains as an example initial corpus.
- **AC-067 (REQ-DOCS-066)**: Given `docs/product-vision.md` §4, Then the user framing is generalized (no "literatura en inglés" as sole scope).
- **AC-068 (REQ-DOCS-067)**: Given `docs/product-vision.md` §10 step 6, Then the wording references "expresiones multipalabra específicas del idioma" (or the final OQ-10 wording).
- **AC-069 (REQ-DOCS-068)**: Given `docs/product-vision.md` §12 item 7, Then the wording is generalized similarly.
- **AC-070 (REQ-DOCS-069)**: Given `docs/product-vision.md` §8, Then it is byte-identical to its pre-change version.
- **AC-071 (REQ-DOCS-06A)**: Given `AGENTS.md` §4, Then the phrasal-verb clause names phrasal verbs as one instance of "expresiones multipalabra específicas del idioma", and the separate-modeling rule is preserved.
- **AC-072 (REQ-DOCS-06B)**: Given the four files in the amendment payload, Then all four contain their respective changes in a single coordinated apply; verify phase fails if any single file is missing its change.

### Family G

- **AC-080 (REQ-DOCS-070)**: Given `AGENTS.md`, Then a cross-reference section links to constitution, ADR index, architecture-baseline, glossary, traceability-matrix, definition-of-done, decisions-log.
- **AC-081 (REQ-DOCS-071)**: Given `docs/constitution.md`, Then a cross-reference footer links to ADR index, architecture-baseline, glossary, definition-of-done.
- **AC-082 (REQ-DOCS-072)**: Given `docs/product-vision.md`, Then a cross-reference footer links to constitution and glossary.
- **AC-083 (REQ-DOCS-073)**: Given `docs/architecture/overview.md`, Then a cross-reference footer links to architecture-baseline and ADR index.
- **AC-084 (REQ-DOCS-074)**: Given `README.md`, Then a `## Referencias metodológicas` section links to constitution, AGENTS.md, glossary, ADR index, definition-of-done.
- **AC-085 (REQ-DOCS-075)**: Given the cross-reference map in §10, When any A → B link is checked, Then B contains the reciprocal reference back to A.

---

## 12. Definition of Done for this change

The change is done when:

- Every requirement in §1 has its acceptance criterion in §11 met and verified.
- The traceability matrix (REQ-DOCS-040) contains a row per REQ-DOCS-### with `Estado = Pasando`.
- The constitution amendment has been applied and the version line reads `2.0.0`; amendment record is present per §7.2 with previous=1.0.0 / new=2.0.0.
- The four-file amendment payload (constitution, product-vision, README, AGENTS.md) has shipped in a single coordinated apply.
- The first-vertical-slice reference throughout the repo reads "upload a `.txt` file and view a lemma list with frequency". No occurrence of the old translation-in-first-slice formulation (which used an arrow-to-translation phrasing) remains.
- `AGENTS.md` §10 contains the exact bullet defined in §6.4.
- `AGENTS.md` §4 phrasal-verb clause is generalized per REQ-DOCS-06A.
- Cross-reference map in §10 is bidirectionally consistent.
- Every artifact file matches the language declared in §0 and §2.
- All artifacts persisted to both filesystem (`openspec/` and `docs/`) and Engram (topic keys `sdd/docs-methodology-overhaul/{spec,design,tasks,apply,verify,archive}`).
- No file outside the artifact catalog (§2) has been modified.

---

## 13. Assumptions

Assumptions that, if wrong, would require re-opening this spec:

- **A-1**: No file outside the four covered by the §7 payload (`constitution`, `product-vision`, `README`, `AGENTS.md`) contains a load-bearing "inglés"/"English-only" scope claim requiring generalization. Design MUST re-scan; if additional files are found, spec re-amends and their generalization joins the coordinated payload.
- **A-2**: The existing 11 skill entries in `.atl/skill-registry.md` correctly resolve on the developer's machine.
- **A-3**: `gentle-ai skill-registry refresh --force` is available on the developer's machine.
- **A-4**: The `hybrid` persistence mode chosen in `openspec/config.yaml` matches the orchestrator's active mode.
- **A-5**: The delivery-strategy split (Wave 1 = 5 foundational ADRs, Wave 2 = 4 contextual ADRs) will be reflected in `sdd-tasks` slice planning.
- **A-6**: `docs/adr/_template.md` naming (vs `0000-template.md`) is a cosmetic choice.
- **A-7**: No other file uses "inglés" as a hard constraint beyond the four in §7 (constitution, README, product-vision, AGENTS.md). Design MUST re-scan; if additional files are found, this spec is re-opened and its amendment payload extended.
- **A-8**: Retitling ADR-0009 from "Phrasal verbs and multiword expressions modeled separately" to "Multiword expressions as language-specific instances" does not conflict with existing spec references. Design MUST verify by grep across the repo (no other artifacts should reference the old title in a load-bearing way; if found, update coordinated).

---

## 14. Open items carried forward to design/tasks

- **OQ-1**: Manual-corrections UX day-one vs deferred — remains open.
- **OQ-2**: Language detection strategy — future ADR after first multi-language slice.
- **OQ-3**: Translation provider strategy — future ADR; must respect constitution Art. IV.5 consent invariant.
- **OQ-4**: NLP library selection per language — future ADR.
- **OQ-8**: Choice between extending Art. XII in-place vs appending a new `## Registro de enmiendas` section — resolve in design; both satisfy REQ-DOCS-063.
- **OQ-9**: Whether `docs/adr/_template.md` or `docs/adr/0000-template.md` is the preferred name — resolve in design.
- **OQ-10 (new)**: Canonical Spanish wording of "multiword expressions specific to the language" — design chooses between "expresiones multipalabra específicas del idioma" (long, explicit) or a shorter phrase (e.g., "expresiones multipalabra por idioma"). The chosen wording MUST be used consistently across constitution amendment, product-vision §10 step 6 and §12 item 7, AGENTS.md §4, glossary abstract entry, and ADR-0008/0009.

Items previously carried but now resolved by this spec:
- OQ-5 (gitignore) — captured as comment block in `openspec/config.yaml` per REQ-DOCS-002.
- OQ-6 (retroactive dating) — resolved by REQ-DOCS-014.
- OQ-7 (constitution amendment) — resolved by REQ-DOCS-060..064 and §7 payload.

---

## 15. Skill resolution

| Skill | Status | Role in this phase |
|-------|--------|--------------------|
| `_shared` | Loaded (support reference) | Governs artifact retrieval and persistence contract. |
| `sdd-spec` | Loaded (executor) | Governs this phase. |
| `cognitive-doc-design` | Loaded | Applied throughout: tables over prose, checklist ACs, chunking by family, signposting. |

**Skill resolution result**: `paths-injected` — all skills loaded from the exact paths provided by the orchestrator.

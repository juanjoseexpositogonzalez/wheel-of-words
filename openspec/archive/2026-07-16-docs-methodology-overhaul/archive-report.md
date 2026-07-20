# Archive Report — docs-methodology-overhaul

## 0. Metadata

- **Change slug**: docs-methodology-overhaul
- **Cycle window**: 2026-07-15 (planning) to 2026-07-20 (verify v2 fix round completion and archive).
- **Branch**: docs-methodology-overhaul (off main at 007dcf9).
- **Commits on branch**: 2de7be3..fc0a769 (8 commits).
- **Final HEAD before archive**: fc0a769.
- **Spec version consumed**: 2.0.
- **Constitution**: v1.0.0 → v2.0.0 MAJOR (amendment landed atomically in Slice E commit 43f89a9).
- **Verify verdict**: archive-ready (44/44 AC PASS, 0 regressions, 0 CRITICAL, 0 WARNING, 1 SUGGESTION non-blocking v2-D1).
- **Delta specs synced**: none. This cycle produced only new methodology and product-facing docs; no capability spec was modified. Sync operation skipped per archive-phase rules for openspec mode with zero delta specs.

---

## 1. Executive summary

The docs-methodology-overhaul SDD cycle successfully bootstrapped a complete methodology documentation layer for wheel-of-words. All 49 requirements landed across five chained slices (A–E) plus one fix round, delivered as eight commits spanning 1730–1830 lines of new and amended files. The cycle's centerpiece — a coordinated Constitution amendment (v1.0.0 → v2.0.0 MAJOR) — expanded the project's scope from English-only to multi-language framing while preserving all core linguistic invariants (POS-per-occurrence, manual-corrections precedence, multiword expressions as language-specific abstractions). Verification round 2 confirms 44/44 acceptance criteria PASS with zero regressions. The cycle's chained-slice strategy kept cognitive load low and per-slice review scope manageable, despite the aggregate line count. Ready for merge to main and for the next SDD cycle.

---

## 2. Commit trail

| SHA | Subject | Slice | Lines net |
|-----|---------|-------|-----------|
| 2de7be3 | docs(sdd): plan docs-methodology-overhaul cycle | Plan | ~50 |
| fd93edd | docs(sdd): apply slice A — SDD/OpenSpec bootstrap | A | ~120 |
| d2e2ca0 | docs(sdd): apply slice B — foundational commitment layer (ADRs 0002–0006 + log) | B | ~500–600 |
| 3a33722 | docs(sdd): apply slice C part 1 — Wave 2 ADRs + decisions-log Wave 2 | C | ~200–250 |
| d423a09 | docs(sdd): apply slice C part 2 — architecture baseline + glossary | C | ~400–500 |
| 4708b0e | docs(sdd): apply slice D — traceability matrix + DoD extract + overview cross-refs | D | ~140 |
| 43f89a9 | docs(sdd): apply slice E — atomic v1.0.0 → v2.0.0 amendment payload | E | ~150–200 |
| fc0a769 | docs(sdd): apply verify round 1 fixes — 7 warnings + 5 suggestions | Fix | ~100 |

**Total commits on branch**: 8 (including planning) across ~1730–1830 net lines.

---

## 3. Deliverables landed

### SDD / OpenSpec wiring (Slice A)
- `openspec/config.yaml` (93 lines) — Bootstrap SDD context for agents; project, stack, test commands, persistence mode, strict_tdd flag, skill registry path, rules by phase.
- `.atl/skill-registry.md` (+15 net lines) — Added 10 SDD skills (sdd-init, sdd-explore, sdd-propose, sdd-spec, sdd-design, sdd-tasks, sdd-apply, sdd-verify, sdd-archive, sdd-onboard) + skill-registry meta-skill in dedicated SDD section; preserved 11 existing user skills; regenerated cache.

### Architecture commitment layer (Slices B–C)
- `docs/adr/README.md` (59 lines) — ADR index with status vocabulary, numbering convention, authoring rules.
- `docs/adr/_template.md` (39 lines) — Canonical ADR template: Status, Date, Context, Decision, Consequences ±, Alternatives.
- `docs/adr/0001-monorepo-and-stack.md` — Preserved unchanged (existing).
- `docs/adr/0002-hexagonal-split.md` (61 lines) — Wave 1: hexagonal split (domain/application/infrastructure/api).
- `docs/adr/0003-tdd-mandatory.md` (68 lines) — Wave 1: TDD as mandatory workflow.
- `docs/adr/0004-sdd-openspec.md` (61 lines) — Wave 1: SDD + OpenSpec as planning method.
- `docs/adr/0005-local-first.md` (56 lines) — Wave 1: Local-first processing invariant.
- `docs/adr/0006-pos-per-occurrence.md` (63 lines) — Wave 1: POS-per-occurrence linguistic model.
- `docs/adr/0007-manual-corrections-precedence.md` (Wave 2) — Manual corrections precedence over NLP results.
- `docs/adr/0008-multi-language-scope.md` (Wave 2) — Multi-language support from day one; language detection and translation provider strategies flagged as future ADRs (OQ-2, OQ-3).
- `docs/adr/0009-mwe-language-specific-instances.md` (Wave 2) — Multiword expressions as language-specific instances (phrasal verbs as English instance).
- `docs/adr/0010-documentation-language-policy.md` (Wave 2) — EN methodology / ES product-facing language policy.
- `docs/architecture/architecture-baseline.md` (200+ lines) — Committed-state snapshot: 3 Mermaid diagrams (system context, hexagonal layers, linguistic data flow) + 9 enumerated committed invariants.
- `docs/decisions-log.md` (70+ lines) — Chronological decisions table: 26 rows spanning constitution adoption, ADR-0001, SPEC-001 decisions, all 10 seed ADRs, language-policy decision, Engineering Playbook deferral trigger, methodology-overhaul cycle.

### Domain legibility (Slice C)
- `docs/glossary.md` (70+ lines, ES) — Product-facing glossary: 14 entries covering token, forma textual, forma normalizada, lema, categoría gramatical contextual, aparición, expresión multipalabra específica del idioma (abstract entry naming phrasal verbs as English instance + locuciones/perífrasis as Spanish instances), confidence score, corrección manual, reprocesamiento, procedencia. Each entry has ≥1 cross-reference to usage site.

### Traceability formalization (Slice D)
- `docs/traceability-matrix.md` (68 lines, EN scaffold) — Cross-spec requirement matrix: columns REQ-id, criterio de aceptación, archivo(s) de prueba, tarea(s), estado. Seeded with 5 rows (REQ-DOCS-001, REQ-DOCS-002, REQ-DOCS-003, REQ-DOCS-004, REQ-DOCS-043 worked example + 8 additional rows added in fix round).
- `AGENTS.md` §10 update (1 line) — Added hard DoD gate: *"La matriz de trazabilidad se ha actualizado con los identificadores de requisito, criterio de aceptación, prueba y tarea correspondientes."* (exact spec §6.4 wording).

### Definition of Done extraction (Slice D)
- `docs/definition-of-done.md` (80 lines, ES) — Product-facing DoD summary quoting Constitution Art. XI + AGENTS.md §10; notes constitution is canonical in case of conflict.

### Constitution and amendment payload (Slice E, atomic 4-file coordinated)
- `docs/constitution.md` (+26 net lines) — Version 1.0.0 → **2.0.0 MAJOR**; added approval date (2026-07-15); generalized preamble from "vocabulario inglés" to multi-language framing (English as first-implemented); added `## Registro de enmiendas` section per Art. XII procedure (entry: 2026-07-16, scope: multi-language expansion + MWE abstraction); added cross-reference footer (ADR index, architecture-baseline, glossary, definition-of-done).
- `docs/product-vision.md` (6 line changes) — Generalized §4 user targeting (§4: "en inglés" → "en el idioma que estudia"); generalized §10 step 6 and §12 item 7 MWE wording ("phrasal verbs" → "expresiones multipalabra específicas del idioma"); §8 "Fuera de alcance inicial" (translation out of MVP) explicitly preserved; added cross-reference footer (constitution, glossary).
- `README.md` (+15 net lines) — Generalized line 3 scope claim (removed English-only qualifier, retained *The Eye of the World* as initial corpus example, framed as multi-language vocabulary analysis); added `## Referencias metodológicas` section (links: constitution, AGENTS.md, glossary, ADR index, definition-of-done).
- `AGENTS.md` (+16 net lines) — Generalized §4 MWE clause: phrasal verbs named as English instance of "expresiones multipalabra específicas del idioma" (separate-modeling rule preserved); added §10 DoD gate line (exact spec §6.4 wording); added `## Referencias` cross-reference footer (constitution, ADR index, architecture-baseline, glossary, traceability-matrix, definition-of-done, decisions-log).

### Cross-references (Slices D–E)
- Added bidirectional cross-reference footers across all four amendment files + architecture overview, ensuring navigability between related artifacts.

---

## 4. Requirements coverage

- **Total requirements**: 49 REQ-DOCS-*** in spec v2.
- **Requirement families**:
  - Family A (SDD/OpenSpec wiring): 6 REQs
  - Family B (Architecture commitment): 12 REQs
  - Family C (Domain legibility): 5 REQs
  - Family D (Traceability formalization): 5 REQs
  - Family E (Definition of Done extraction): 3 REQs
  - Family F (Constitution + amendment payload): 12 REQs
  - Family G (Cross-references): 6 REQs
- **Acceptance criteria**: 44 ACs derived from 49 REQs (some REQs share ACs; coordination invariant REQ-DOCS-06B spans multiple ACs).
- **Final verification result**: 44/44 PASS (verify-report-v2, Engram #2349).
- **Regressions**: 0.
- **CRITICAL issues**: 0.
- **WARNING issues**: 0 (all 7 from v1 fixed in fix round).
- **SUGGESTION issues**: 1 non-blocking (v2-D1: AGENTS.md gate wording enhanced with embedded backtick path; AC-043 PASS; improvement, not a defect).

---

## 5. Divergences reconciled

| # | Divergence | From | Status | Verdict | Evidence |
|---|-----------|------|--------|---------|----------|
| 1 | Skill-registry ordering (SDD section in phase order vs alphabetical) | Slice A apply vs design §3.2 | Ratified in fix round | Accept & update design | apply-progress #2263, design §3.2 retroactively noted as improved in v1 |
| 2 | skill-registry meta-skill excluded | Slice A apply vs spec §8.1 | Fixed in fix round | Added to registry outside SDD section | apply-progress #2263, fix-round #2347 FIX-1 |
| 3 | 14 glossary entries vs design's 13 | Slice C apply vs design §3.5 | Ratified in fix round | Accept (both MWE forms are distinct canonical entries) | apply-progress #2263 Slice C, spec §5.1 ≥13 constraint satisfied |
| 4 | ADR-0008 short title vs design's longer | Slice C apply vs design §3.3 | Ratified in fix round | Accept & note in design ratification | apply-progress #2263 Slice C |
| 5 | Traceability matrix vocabulary (Cumplido vs Pasando) | Slice D apply vs design §4.1 | Resolved in fix round | Accept Cumplido (natural Spanish); SPEC-001 uses only Pendiente (acceptable constraint scope) | apply-progress #2263 Slice D, design §4.1 updated to endorse 6-column EN scaffold |
| 6a | Product-vision cross-ref footer missing | Slice E locked-decision #10 vs design §5.2 | Fixed in fix round | Added footer (spec REQ-DOCS-072 mandates it; locked decision was overreach) | fix-round #2347 FIX-3 |
| 6b | AGENTS.md §10 gate wording drift | Slice E apply wording vs spec §6.4 exact wording | Fixed in fix round | Applied spec §6.4 exact wording | fix-round #2347 FIX-2 |

**Summary**: 6 divergences (all discovered in verify-report v1). 7 WARNING fixes + 5 SUGGESTION ratifications applied in fix round (commit fc0a769). No divergences remain open; all are reconciled with spec/design updates or artifact corrections.

---

## 6. Open questions carried forward

- **OQ-1**: Manual-corrections UX (day-one vs deferred). Constitution mandates the invariant; implementation timing is a product decision. Documented in decisions-log ADR-0007 row; remains open for future product planning.
- **OQ-2**: Language detection strategy (bundled model vs external API vs heuristic-first). Documented in decisions-log ADR-0008 row as deferred to a future ADR.
- **OQ-3**: Translation provider strategy (local model vs API, per Constitution Art. IV.5 consent requirement). Documented in decisions-log ADR-0008 row as deferred to a future ADR.
- **OQ-4**: NLP library selection per language (spaCy vs Stanza vs mixed by language coverage). Documented in decisions-log ADR-0008 row as deferred to a future ADR.

---

## 7. Constitution amendment ratification

- **Version bump**: v1.0.0 → **v2.0.0 MAJOR** (effective 2026-07-16, approved date 2026-07-15).
- **Scope**: Multi-language expansion + user-targeting generalization + MWE abstraction span four files (constitution, product-vision, README, AGENTS.md) and change conceptual scope; classified as MAJOR per semantic versioning.
- **Files touched atomically** (Slice E commit 43f89a9): constitution, product-vision, README, AGENTS.md (all 4 required for coordination invariant REQ-DOCS-06B).
- **Coordination invariant** (REQ-DOCS-06B): Verified in both verify rounds (Engram #2292 verify-report, Engram #2349 verify-report-v2). All 4 files present and coordinated. No partial applies accepted.
- **Constitutional invariants preserved**:
  - **Art. IV** (legality/copyright): Body text byte-identical. Preamble generalization does not weaken scope; English-only removal is scope-widening, not constraint-weakening.
  - **Art. V** (linguistic model integrity): Body text byte-identical. 9 clauses unchanged. Art. V.6 (MWE modeling) preserved in intent; preamble reading context shifts from English-only to multi-language, but the clause's separate-modeling rule is strengthened (all language-specific MWEs now explicitly abstracted).
  - **Art. VII** (architecture/hexagonal): Body text byte-identical. 7 clauses unchanged. Art. VII.5 (linguistic rules not duplicated in frontend) carries through unchanged.
- **Amendment record** (per Art. XII procedure): Recorded in new `## Registro de enmiendas` section. Entry: Fecha=2026-07-16, Cambio=multi-language expansion + MWE abstraction, Motivación=align scope with product vision (multi-language support from day one), Versión anterior=1.0.0, Versión nueva=2.0.0.

---

## 8. Post-cycle decisions queued for user

The following decisions are NOT part of this cycle but arise from its artifacts and should be resolved before merge:

1. **Gitignore of `openspec/changes/`** — Deferred until first archive completes (this one). Recommendation from exploration: commit `openspec/config.yaml` + `openspec/specs/` (baseline); gitignore `openspec/changes/` (ephemeral SDD planning artifacts). User must decide and implement gitignore rule before first real SDD cycle's apply phase.

2. **Merge `docs-methodology-overhaul` into `main`** — User must decide: fast-forward or `--no-ff` (atomic amendment record is preserved in either case). No CI/workflow constraints detected.

3. **Engineering Playbook adoption trigger** — Spec §4, decision-log row, and proposal §11 concern #2 define the trigger: *"After first vertical slice ships end-to-end (upload a `.txt` file and view a lemma list with frequency)."* This cycle is methodology/docs only (no vertical slice implementation); trigger remains pending until that slice ships.

4. **v2-D1 SUGGESTION (non-blocking)** — Verify-report-v2 §2 flags an enhancement: AGENTS.md §10 gate wording was enriched with an embedded backtick path `(docs/traceability-matrix.md)` during fix round. AC-043 PASS; enhancement is an improvement. User can leave as-is or trim to exact spec wording. Non-blocking; no action required.

---

## 9. Engram observation trail

| Topic | ID | Artifact | Phase | Status |
|-------|----|---------|----|--------|
| sdd/docs-methodology-overhaul/explore | #2243 | explore.md | Exploration | Complete |
| sdd/docs-methodology-overhaul/proposal | #2251 | proposal.md | Proposal | Complete |
| sdd/docs-methodology-overhaul/spec | #2254 | spec.md (v2.0) | Spec | Complete (upserted from v1) |
| sdd/docs-methodology-overhaul/design | #2259 | design.md | Design | Complete |
| sdd/docs-methodology-overhaul/tasks | #2261 | tasks.md | Tasks | Complete |
| sdd/docs-methodology-overhaul/apply-progress | #2263 | (Engram only) | Apply | Complete (upserted A..E) |
| sdd/docs-methodology-overhaul/slice-a-divergences | #2271 | (Engram only) | Discovery | Reconciled in fix round |
| sdd/docs-methodology-overhaul/verify-report | #2292 | verify-report.md | Verify v1 | Complete (needs-fix-round verdict) |
| sdd/docs-methodology-overhaul/fix-round-1 | #2347 | (Engram only) | Fix | Complete (7 WARNINGs + 5 SUGGESTIONs applied) |
| sdd/docs-methodology-overhaul/verify-report-v2 | #2349 | verify-report-v2.md | Verify v2 | Complete (archive-ready verdict) |
| sdd/docs-methodology-overhaul/archive-report | (new) | archive-report.md | Archive | This observation (new ID TBD) |
| wheel-of-words/git-workflow | #2262 | (Engram only) | Decision | Captured during apply |

**Traceability**: All nine SDD phase observations linked via topic_key for cycle continuity. Archive-report observation completes the cycle audit trail.

---

## 10. Lessons learned

1. **Chained slices kept regressions at zero**: The strategy of five manageable slices (A–E) plus a one-round fix phase meant each slice's scope was focused and reviewable. Despite 1730–1830 net lines across the cycle, no regressions were introduced in verify round 2 (0 regressions, up from 0 in v1). The fix round was surgical: 7 WARNINGs corrected, 5 SUGGESTIONs ratified; no new issues created.

2. **Apply prompt overrides can drift from spec/design**: Slice E encountered two deviations (product-vision footer missing, AGENTS.md §10 gate wording). Both arose from explicit "locked decisions" in the apply prompt that conflicted with spec requirements. Verify caught them cleanly. Lesson: when apply intentionally overrides a spec/design decision, apply MUST add a follow-up task or design-patch so downstream phases know the spec is stale. This did not happen; verify had to reconcile retroactively.

3. **Constitutional amendment requires coordination gates**: REQ-DOCS-06B coordination invariant proved essential. A partial apply of the v2.0.0 amendment (e.g., constitution updated but AGENTS.md MWE clause not updated) would have broken the amendment's coherence. The "all-four-files-atomic" gate prevented that risk.

4. **Language-policy decision must come first**: In this cycle, ADR-0010 (documentation language policy) should have been written before all other ADRs so language choices in every artifact downstream would be unambiguous. Language drift was caught and corrected in verify, but could have been prevented by grounding the policy early.

5. **Retroactive ADRs feel formulaic but are necessary**: Writing 10 ADRs for already-made decisions (especially in a batch) risks them feeling like retroactive rationalization. Mitigation: ground each ADR in direct quotes from AGENTS.md or constitution; use accurate historical dates (Wave 1 dated to constitution approval, Wave 2 to amendment date); explain consequences and alternatives fully. Applied successfully here.

---

## 11. Cycle closure statement

**docs-methodology-overhaul is complete and archived on 2026-07-16.**

- ✅ **All 49 requirements landed** across five chained slices (A–E) plus one fix round.
- ✅ **All 44 acceptance criteria PASS** (verify-report-v2: 44/44 PASS, 0 regressions, 0 CRITICAL, 0 WARNING, 1 non-blocking SUGGESTION).
- ✅ **Constitution amendment v2.0.0 ratified** — multi-language expansion + MWE abstraction landed atomically across 4 files (constitution, product-vision, README, AGENTS.md).
- ✅ **Coordination invariant (REQ-DOCS-06B) verified** — all 4 amendment files present and coherent.
- ✅ **All SDD artifacts archived** — explore, proposal, spec, design, tasks, both verify reports, archive-report persisted to `openspec/archive/2026-07-16-docs-methodology-overhaul/`.
- ✅ **Engram observation trail complete** — all 11 observations (including archive-report, new) linked via topic_key for cycle traceability.

**Ready for**:
1. User resolution of post-cycle decisions (gitignore policy, merge strategy, Engineering Playbook trigger).
2. Merge `docs-methodology-overhaul` → `main`.
3. Next SDD cycle (first vertical slice: upload `.txt` → lemma list with frequency).

---

## 12. Skill resolution

| Skill | Status | Role in archive phase |
|-------|--------|----------------------|
| `_shared` | Loaded (support reference) | Shared SDD phase references (sdd-phase-common.md, openspec-convention.md). |
| `sdd-archive` | Loaded (executor, this phase) | Primary skill governing archive phase: spec sync (skipped — zero delta), file copy, archive-report creation, Engram persistence, commit. |
| `cognitive-doc-design` | Loaded | Applied to archive-report structure: lead-with-answer (metadata + executive summary first), progressive disclosure (deliverables → requirements → divergences → decisions → lessons), recognition-over-recall (tables, bulleted lists), signposting (numbered sections, cross-ref map). |

**Skill resolution result**: `paths-injected` — all three loaded from their `SKILL.md` paths. No fallback required.

---

## Appendix A. File inventory

All files in `openspec/archive/2026-07-16-docs-methodology-overhaul/`:

| File | Bytes | Lines | Purpose |
|------|-------|-------|---------|
| explore.md | ~24 KB | 435 | Exploration phase: gap analysis, reference patterns, open questions |
| proposal.md | ~13 KB | 189 | Proposal phase: problem statement, scope, goals, acceptance criteria |
| spec.md | ~48 KB | 857 | Spec v2.0: 49 REQs across 7 families, artifact catalog, contracts |
| design.md | ~41 KB | 868 | Design v1.0: content contracts, diff intents, ADR outlines, amendment payload |
| tasks.md | ~25 KB | 691 | Tasks: 41 tasks across 5 slices + 1 fix phase, chained dependencies, guidance |
| verify-report.md | ~18 KB | (varies) | Verify round 1: 44 ACs, 6 FAILs (needs-fix-round), 10 drift items, 7 WARNING fixes |
| verify-report-v2.md | ~16 KB | (varies) | Verify round 2: 44 ACs PASS, 0 FAILs, 0 regressions, 1 SUGGESTION, archive-ready |
| archive-report.md | This file | — | Archive phase: full cycle summary, deliverables, divergence reconciliation, post-cycle decisions |

**Total archived**: 8 files covering the full SDD cycle from exploration through archive.

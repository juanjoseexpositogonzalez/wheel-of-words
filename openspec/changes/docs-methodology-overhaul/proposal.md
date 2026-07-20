# Proposal — Documentation & Methodology Overhaul

**Change slug:** `docs-methodology-overhaul`
**Date:** 2026-07-16
**Artifact store:** openspec + engram
**Preceded by:** `openspec/changes/docs-methodology-overhaul/explore.md`
**Scope:** Documentation and methodology ONLY. No code, no package layout, no infrastructure decisions.
**Post-spec-v2 note:** The following user decisions locked after this proposal was written and are already reflected in `spec.md` v2.0: (a) translation removed from first vertical slice; (b) ADR-0009 retitled to "Multiword expressions as language-specific instances"; (c) constitution amendment escalated to v2.0.0 MAJOR with four-file coordinated payload; (d) ADR wave split 5+4 (foundational 2026-07-15, contextual 2026-07-16). This proposal has been updated in place to match spec v2; where deeper redesign is needed the spec is authoritative.

---

## 1. Problem statement

wheel-of-words already has a strong constitution, a complete SPEC-001 suite, and a functional `AGENTS.md` — but the methodology surface around them is incomplete. Agents starting a new session cannot bootstrap SDD context (no `openspec/config.yaml`), cannot dispatch SDD phases (skill registry lists 0 SDD skills out of 10 available), and cannot navigate architectural intent (1 ADR exists for ~10 implicit decisions). The linguistic domain has 12+ load-bearing terms that are used across the constitution and specs without a single canonical definition, and the traceability matrix — despite being present — has no Definition-of-Done gate to keep it alive. The gaps are all documentation and methodology gaps, not code gaps.

## 2. Business/product intent (context, not scope)

| Item | Value |
|------|-------|
| Audience | Personal use. No auth, no multi-tenancy, no external contributors expected. |
| First vertical slice | Upload `.txt` → lemma list with frequency. Translation deferred post-MVP. Informs doc examples only. |
| Language coverage | Multi-language from day one. Language detection and per-language NLP model selection remain OPEN. Translation is out of MVP scope. |
| Load-bearing invariants | Constitution Art. IV, V, VII and AGENTS.md §4 remain sacred: POS-per-occurrence, manual-corrections precedence, multiword expressions specific to the language modeled separately (phrasal verbs as English instance — see ADR-0009), no copyrighted books in repo, local-first processing. |

## 3. Goals of THIS change

1. **Methodology infrastructure** — Any future agent session can dispatch SDD phases without going blind. `openspec/config.yaml` + populated skill registry give the bootstrap.
2. **Architectural commitment layer** — ADRs + baseline + decisions log capture the decisions already implicit in AGENTS.md and constitution.
3. **Domain-legibility layer** — Glossary defines the 12+ linguistic terms so no agent misinterprets `lemma` vs `form` vs `occurrence`.
4. **Traceability formalization** — `REQ-<feature>-<n>` becomes enforceable via a hard DoD gate in AGENTS.md §10.

## 4. Non-goals (explicit)

- No code changes anywhere in the repo.
- No decisions about Python package layout, FastAPI shape, or backend/frontend split.
- No infrastructure choices (persistence flavor, message bus, NLP library, translation provider).
- No git/PR workflow — repo isn't a git repo yet; deferred to a future cycle.
- No Engineering Playbook forking — deferred until after the first real SDD cycle produces lessons worth codifying.
- No `docs/governance/` — personal audience, contributor governance is premature.
- No Obsidian companion — docs-in-repo only.
- No content design for ADRs, glossary, or baseline — those are spec/design phase deliverables.

## 5. Scope — what will exist after this change

Deliverables enumerated by artifact family. Purpose + language + status only. Content design belongs to `sdd-spec` / `sdd-design`.

### 5.1 SDD / OpenSpec wiring

| Artifact | Language | Status | Purpose |
|----------|----------|--------|---------|
| `openspec/config.yaml` | EN | New | Bootstrap SDD context: project metadata, stack, test commands, persistence mode, skill registry path, strict_tdd flag. |
| `.atl/skill-registry.md` | EN | Updated | Add all SDD skills (`sdd-init`, `sdd-explore`, `sdd-propose`, `sdd-spec`, `sdd-design`, `sdd-tasks`, `sdd-apply`, `sdd-verify`, `sdd-archive`, `sdd-onboard`) with correct triggers and absolute paths. |
| Gitignore advisory note | EN | New (advisory only) | Document intent: when repo becomes git-tracked, commit `openspec/config.yaml` + `openspec/specs/`; gitignore `openspec/changes/` (ephemeral SDD planning). |

### 5.2 Architecture commitment layer

| Artifact | Language | Status | Purpose |
|----------|----------|--------|---------|
| `docs/adr/README.md` | EN | New | ADR index with status vocabulary (`Proposed`, `Accepted`, `Superseded`, `Deprecated`) and authoring rules. |
| `docs/adr/_template.md` | EN | New | Canonical ADR template (Context, Decision, Status, Date, Consequences ±, Alternatives). |
| Seed ADRs (~10, placeholder titles) | EN | New | Enumerated below. Content is spec-phase work; only the file skeletons and titles land here. |
| `docs/architecture/architecture-baseline.md` | EN | New | Committed-state snapshot with three Mermaid diagrams: (a) system context, (b) hexagonal layers, (c) linguistic data flow (form → normalization → lemma → occurrence with POS). |
| `docs/decisions-log.md` | EN | New | Chronological log of decisions referencing ADRs. Uses actual decision dates where recoverable, current date only for genuinely new decisions. |

**Candidate seed ADR titles** (final list refined in `sdd-spec`):

| # | Title | Grounded in |
|---|-------|-------------|
| ADR-0001 | Monorepo and stack (Python/FastAPI/SQLite/React/Vite) | Already exists |
| ADR-0002 | Hexagonal split: `domain` / `application` / `infrastructure` / `api` | AGENTS.md §5, Constitution Art. VII |
| ADR-0003 | TDD as mandatory workflow with strict RED → GREEN → REFACTOR | AGENTS.md §3, Constitution Art. II |
| ADR-0004 | SDD + OpenSpec as planning method | New with this change |
| ADR-0005 | Local-first processing, no third-party data egress by default | Constitution Art. IV.4–5 |
| ADR-0006 | POS-per-occurrence linguistic model (no single global POS per lemma) | Constitution Art. V.2–3, AGENTS.md §4 |
| ADR-0007 | Manual corrections precedence and survival across reprocessing | Constitution Art. V.8–9, AGENTS.md §4 |
| ADR-0008 | Multi-language support from day one (detection strategy TBD → spawns future ADR) | User decision this session |
| ADR-0009 | Multiword expressions as language-specific instances | Constitution Art. V.6 (post-amendment); ADR-0008 |
| ADR-0010 | Documentation language policy: methodology EN, product-facing ES | User decision this session |

### 5.3 Domain-legibility layer

| Artifact | Language | Status | Purpose |
|----------|----------|--------|---------|
| `docs/glossary.md` | ES | New | Defines: token, forma textual, forma normalizada, lema, categoría gramatical contextual, aparición, phrasal verb, expresión multipalabra, procedencia, puntuación de confianza, corrección manual, reprocesamiento. Each entry cross-references at least one usage site (spec, ADR, or AGENTS.md). |

### 5.4 Traceability formalization

| Artifact | Language | Status | Purpose |
|----------|----------|--------|---------|
| `docs/traceability-matrix.md` | EN scaffold (rows in referenced-spec language) | New | Columns: REQ-id, criterio de aceptación, archivo(s) de prueba, tarea(s), estado. Cross-spec view; per-spec `traceability.md` remains authoritative for a single feature. |
| `AGENTS.md` §10 update | ES | Updated | Add hard DoD gate: "La matriz de trazabilidad se ha actualizado con las pruebas y tareas correspondientes." |

### 5.5 Definition of Done extraction

| Artifact | Language | Status | Purpose |
|----------|----------|--------|---------|
| `docs/definition-of-done.md` | ES | New | Short, product-facing DoD summary that quotes and links Constitution Art. XI and AGENTS.md §10. Constitution remains canonical in case of conflict. |

### 5.6 Constitution and AGENTS.md touch-points

| Touch-point | Type | Purpose |
|-------------|------|---------|
| AGENTS.md → ADR index | Cross-reference add | Point agents to `docs/adr/README.md`. |
| AGENTS.md → architecture baseline | Cross-reference add | Point to `docs/architecture/architecture-baseline.md`. |
| AGENTS.md → glossary | Cross-reference add | Point to `docs/glossary.md`. |
| AGENTS.md → traceability matrix | Cross-reference add | Point to `docs/traceability-matrix.md`. |
| AGENTS.md → DoD extract | Cross-reference add | Point to `docs/definition-of-done.md` while keeping constitution canonical. |
| AGENTS.md §10 | Update | Traceability-matrix gate (see 5.4). |
| Constitution language-policy article | **Flag only** | If no article governs documentation language, propose a minor amendment (Art. XII procedure). Do NOT draft the amendment here. |

## 6. Acceptance criteria

Each criterion is objectively verifiable.

- [ ] `openspec/config.yaml` exists, is valid YAML, and includes at minimum: `project`, `stack`, `test_commands`, `persistence_mode`, `strict_tdd`, `skill_registry_path`.
- [ ] `.atl/skill-registry.md` lists at minimum the 10 SDD skills (`sdd-init`, `sdd-explore`, `sdd-propose`, `sdd-spec`, `sdd-design`, `sdd-tasks`, `sdd-apply`, `sdd-verify`, `sdd-archive`, `sdd-onboard`) with correct triggers and absolute paths, and the cache file is regenerated.
- [ ] `docs/adr/README.md` exists with status vocabulary and authoring rules.
- [ ] `docs/adr/_template.md` exists and matches the schema (Context / Decision / Status / Date / Consequences ± / Alternatives).
- [ ] Every ADR file conforms to `_template.md` and has status ∈ {Proposed, Accepted, Superseded, Deprecated}.
- [ ] `docs/architecture/architecture-baseline.md` renders at least three Mermaid diagrams that parse without syntax errors.
- [ ] `docs/glossary.md` defines all 12 core terms and each definition has ≥1 cross-reference to a usage site.
- [ ] `docs/traceability-matrix.md` exists and has at least one non-"Pendiente" row demonstrating the update workflow.
- [ ] `AGENTS.md` §10 explicitly names the traceability matrix as a hard DoD gate.
- [ ] `docs/definition-of-done.md` exists, quotes Constitution Art. XI verbatim (or by reference), and states constitution is canonical.
- [ ] AGENTS.md contains cross-reference footers to ADR index, architecture baseline, glossary, traceability matrix, and DoD.
- [ ] Constitution and AGENTS.md do not contradict each other on: TDD cycle, DoD, architecture layers, documentation language policy.
- [ ] `docs/decisions-log.md` exists with at least the decisions already made (constitution adoption, ADR-0001, SPEC-001 decisions, this methodology overhaul).

## 7. Rough sizing

| Slice | Deliverables | Est. lines | Verdict |
|-------|-------------|------------|---------|
| A | `openspec/config.yaml` + `.atl/skill-registry.md` update + cache | ~120 | Fits budget alone. |
| B | `docs/adr/README.md` + `docs/adr/_template.md` + 10 ADR skeletons | ~450–600 | At/over budget alone. |
| C | `docs/architecture/architecture-baseline.md` + `docs/glossary.md` + `docs/decisions-log.md` | ~500–700 | Over budget. |
| D | `docs/traceability-matrix.md` + `docs/definition-of-done.md` + AGENTS.md §10 update + cross-reference footers | ~200 | Fits budget. |
| **Total** | ~15 new files + AGENTS.md edits | **~1300–1600** | **Chained-required.** |

**Sizing verdict:** `chained-required`. Even without code, doc volume exceeds the 400-line review budget by 3–4×. Slice plan materializes in `sdd-tasks`, not here. Order recommended: A → B → C → D so agents get SDD bootstrap first, then commitment layer, then domain legibility, then enforcement.

## 8. Open questions carried into spec/design phase

| # | Question | Owner |
|---|----------|-------|
| OQ-1 | Manual corrections UX: day-one or deferred? Constitution mandates the invariant; ship-time is undecided. | User → surface at spec |
| OQ-2 | Language detection strategy for multi-language input (bundled model vs external API vs heuristic-first). | Future ADR |
| OQ-3 | Translation provider strategy (local model vs API, per Constitution Art. IV.5 consent requirement). | Future ADR |
| OQ-4 | NLP library selection per language (spaCy vs Stanza vs mixed by language coverage). | Future ADR |
| OQ-5 | OpenSpec `changes/` gitignore policy — decide when repo becomes git-tracked. | Deferred until git init |
| OQ-6 | Retroactive ADR dating convention — use today's date, or backdate to actual decision date (e.g. constitution approval date for foundational ADRs)? | Resolve in `sdd-spec` |
| OQ-7 | Constitution amendment to formalize the documentation language policy (Art. XII procedure) — draft in this cycle or defer? | Resolve in `sdd-spec` |

## 9. Risks

| # | Risk | Mitigation |
|---|------|------------|
| R-1 | Copying Synaptiq/Rust patterns verbatim (NATS, outbox, workspaces) leaks irrelevant infra vocabulary into wheel-of-words docs. | Enforce in spec review: every deliverable must trace to a wheel-of-words invariant, not a reference-project pattern. |
| R-2 | Seed ADRs written in a batch feel formulaic and retroactive. | Ground each ADR in a direct quote or clause reference from AGENTS.md or the constitution; use accurate historical dates where recoverable (OQ-6). |
| R-3 | Language drift — bilingual policy (methodology EN, product ES) risks inconsistent application. | Land policy as ADR-0010 up-front; every doc file gets a language-tag comment header noting which policy applies. |
| R-4 | Traceability DoD gate added but never enforced because no code exists yet. | Document the gate now; enforcement kicks in with first real implementation cycle. Include one worked-example row in the matrix. |
| R-5 | Constitution vs AGENTS.md drift — two overlapping docs, no cross-references. | Cross-reference footer in AGENTS.md + explicit "constitution is canonical" note in DoD extract. |
| R-6 | 10 ADRs at once is heavy for the spec phase — potential over-scoping. | If sizing pressure hits during `sdd-tasks`, split seed ADRs into two waves: foundational (5) in this change, contextual (5) in a follow-up. |
| R-7 | Deferring the Engineering Playbook means the first cycle happens without codified lessons. | Accepted trade-off — playbooks written before real cycles are fiction. Capture lessons in Engram and revisit after cycle 1. |

## 10. Recommendation

**Proceed to `sdd-spec` after user review of this proposal.** The chained-slice plan (A → B → C → D from §7) will be materialized in `sdd-tasks`, not here. `sdd-spec` should:

1. Decide seed ADR count (10 vs foundational-5 first).
2. Resolve OQ-6 (ADR dating convention) and OQ-7 (constitution amendment scope).
3. Confirm the language-policy ADR (ADR-0010) as the first ADR to write, since it governs every other artifact in this change.

## 11. Concerns for the user

Three items in the locked decisions that deserve a second look before spec starts:

1. **OpenSpec `changes/` gitignore policy is deferred until git init (OQ-5), but the recommendation from exploration (commit `config.yaml` + `specs/`, gitignore `changes/`) should be captured somewhere durable now** — otherwise it gets forgotten. Suggest an advisory note inside `openspec/config.yaml` comments.
2. **Deferring the Engineering Playbook (Q3 = defer) is reasonable, but there is no explicit trigger defined for revisiting it.** Suggest: "extract playbook notes after first vertical slice ships end-to-end." Without a trigger, deferral becomes indefinite.
3. **Retroactive ADR dating (OQ-6) resolved in spec v2**: foundational ADRs (0002–0006, wave 1) dated 2026-07-15 (constitution approval date); contextual ADRs (0007–0010, wave 2) dated 2026-07-16.

## 12. Skill resolution

| Skill | Status | Role in this proposal |
|-------|--------|-----------------------|
| `_shared` | Loaded (support reference) | Confirmed not invokable. |
| `sdd-propose` | Loaded (direct read as executor) | Governs this phase. |
| `cognitive-doc-design` | Loaded | Applied throughout: lead-with-answer sections, tables over prose for enumeration, checklists for acceptance criteria, chunking by artifact family. |

**Skill resolution result:** `paths-injected` — all three loaded from their `SKILL.md` paths. No fallback required.

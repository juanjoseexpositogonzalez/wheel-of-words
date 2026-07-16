# Exploration — Documentation & Methodology Overhaul

**Change:** docs-methodology-overhaul  
**Date:** 2026-07-15  
**Artifact store:** openspec + engram  
**Scope:** Documentation and methodology ONLY — no code, no Python package layout, no backend/frontend implementation shape.

---

## 1. Current State of wheel-of-words

### 1.1 Repo Inventory

| Path | Purpose | Status |
|------|---------|--------|
| `AGENTS.md` | Agent + contributor rules: methodology, TDD cycle, domain constraints, architecture layers, test types, req/task conventions, DoD, final report | Strong. In Spanish. Covers the essential contract. |
| `README.md` | Package overview, repo tree, mandatory flow diagram, scope statement, next-spec pointer | Adequate but minimal. No onboarding depth (no setup, no commands, no dev flow). |
| `docs/constitution.md` | 12-article project constitution (SDD, TDD, vertical slices, copyright, linguistic model, reproducibility, architecture, quality, accessibility, observability, DoD, amendments) | Excellent. The strongest single artifact. Versioned (`1.0.0`). |
| `docs/product-vision.md` | Product vision: problem, vision, user, value prop, MVP objectives, out-of-scope, success metrics, main scenario, risks, roadmap | Strong. Well-structured. |
| `docs/architecture/overview.md` | Architecture overview: context diagram (text), monorepo shape, domain entities, use cases, infra adapters, frontend, persistence, processing states, security, evolution | Good starter. ASCII diagrams only. No baseline commitment document. |
| `docs/adr/0001-monorepo-and-stack.md` | ADR-0001: monorepo + full stack decision (Python/FastAPI/SQLite/React/Vite/Playwright/GitHub Actions) | Acceptable structure. One ADR. Missing: ADR template, ADR index, ADRs for many other decisions already made. |
| `specs/001-project-foundation/spec.md` | SPEC-001 full spec (18 functional + 6 non-functional reqs, in `REQ-001-NNN` format) | High quality. Atomic, verifiable reqs. |
| `specs/001-project-foundation/acceptance.md` | 15 Gherkin acceptance scenarios (AC-001 to AC-015) | High quality. Properly linked to reqs. |
| `specs/001-project-foundation/plan.md` | Technical plan: strategy, proposed directory structure, backend/frontend/contract/CI/security details | Good. But directories in `apps/api/` and `apps/web/` don't match `docs/architecture/overview.md` which shows `apps/api/` and `apps/web/`. Consistent here. |
| `specs/001-project-foundation/test-plan.md` | Test plan: pyramid, per-layer test IDs with req references | Good. Proper test-ID naming. |
| `specs/001-project-foundation/tasks.md` | 62 tasks in `T<n> [TYPE] desc` format, grouped in 7 phases | High quality. Correct `[TEST] → [IMPL] → [REFACTOR]` ordering. |
| `specs/001-project-foundation/decisions.md` | 6 spec-level decisions (DEC-001 to DEC-006) | Minimal. Flat prose, no date, no alternatives, no links to ADRs. |
| `specs/001-project-foundation/traceability.md` | Traceability matrix: req → acceptance → test → tasks → status | Present. Table format. All rows "Pendiente". |
| `templates/feature-spec-template.md` | Reusable spec template (21 sections) | Good bones. Covers all spec sections. No ADR template. No acceptance template. No task template. |
| `.atl/skill-registry.md` | Skill registry: sources, contract, skills table with trigger/scope/path | Well-formed. 11 skills indexed. Missing SDD skills (sdd-explore, sdd-propose, sdd-spec, sdd-design, sdd-tasks, sdd-apply, sdd-verify, sdd-archive, sdd-init, sdd-onboard). Only lists user-scoped skills; no project-scoped skills. |
| `.atl/.skill-registry.cache.json` | Cache fingerprint for registry refresh | Present. |

### 1.2 What's Strong Today

1. **Constitution** — 12 articles covering every non-negotiable invariant. This is the strongest foundation document. Versioned, amendment-aware.
2. **SPEC-001 suite** — The seven spec files (spec, acceptance, plan, test-plan, tasks, decisions, traceability) are thorough and internally consistent. The `REQ-<feature>-<n>` and `T<n> [TYPE]` conventions are already established.
3. **AGENTS.md** — Comprehensive agent contract. Covers the mandatory workflow, TDD cycle, domain constraints (copyright, POS-per-occurrence, manual corrections, phrasal verbs), architecture layers, test pyramid, req/task formats, DoD, and final report format.
4. **Product vision** — Complete and well-structured. Explicit roadmap of 10 milestones.
5. **Architecture overview** — Domain entities and use cases are explicitly named. Adapter boundaries are clear. NLP models treated as replaceable adapters.
6. **Skill registry** — `.atl/` structure exists and the registry format is functional (matches Synaptiq/Wellforge pattern).
7. **Linguistic domain constraints** — The constitution (Art. V) and AGENTS.md are unusually specific about linguistic model invariants: POS per occurrence, manual corrections precedence, confidence scores, phrasal verbs as separate entities. This is a project-specific strength.

### 1.3 What's Missing

**Governance layer:**
- No `docs/governance/` directory (issue policy, branch policy, label catalog, PR template, docs-only work policy, repository setup).
- No `DEFINITION_OF_DONE.md` at repo root (currently buried in `docs/constitution.md` Art. XI and AGENTS.md §10).
- No `ALLIANCE.md` or `PROJECT_CONTEXT.md` (meta-contract for agents — who owns what, how to escalate, trust model).
- No `CONTRIBUTING.md`.
- No PR template (`.github/pull_request_template.md`).

**Architecture documentation:**
- No committed `architecture-baseline.md` (a lightweight "this is the architecture we have committed to" doc, separate from `overview.md` which is forward-looking).
- No SVG/Mermaid diagrams — only ASCII art in `overview.md`.
- No `docs/glossary.md` (critical for a linguistic-domain project with 15+ technical terms: token, form, lemma, occurrence, POS, confidence, phrasal verb, etc.).
- No `docs/flows/` — no explicit happy-path and error-path flows for the main user scenario.
- No `docs/slices/` or equivalent (not strictly required for the Python/feature-based layout, but no vertical-slice tracking mechanism exists).

**ADR set:**
- Only 1 ADR (`0001-monorepo-and-stack.md`). Many more decisions have already been made implicitly (local-first processing, spaCy as first NLP adapter, Alembic for migrations, hypothesis for property testing, OpenAPI as contract truth, optional Docker) that lack ADRs.
- No `docs/adr/0000-template.md` — no canonical ADR template in the repo.
- No `docs/adr/README.md` index.

**Decisions log:**
- The per-spec `decisions.md` files exist but are flat, dateless, and don't link to ADRs. There is no project-level chronological decisions log (what was decided, when, why, who was affected) — analogous to the `12-Log-de-Decisiones.md` Obsidian file for Synaptiq or the Cairn `Decision Log`.

**Traceability:**
- The traceability matrix exists for SPEC-001 but is "Pendiente" across all rows — it has never been updated post-implementation. No convention for updating it after a task is completed.
- No `docs/requirements/` directory with feature-level requirement maps.

**SDD/OpenSpec:**
- No `openspec/` directory (being created by this exploration).
- No `openspec/config.yaml`.
- The `.atl/skill-registry.md` is missing the SDD skills (sdd-init, sdd-explore, sdd-propose, sdd-spec, sdd-design, sdd-tasks, sdd-apply, sdd-verify, sdd-archive, sdd-onboard).

**Methodology:**
- No Engineering Playbook reference (even a lightweight Python-flavored edition). The AGENTS.md captures rules but not the reasoning or evolution record behind them.
- No formal lessons-learned artifact after each cycle.
- No `docs/testing/` directory with a separate testing strategy document (it exists in AGENTS.md §6 but is not extracted as a standalone navigable document).

**Templates:**
- `templates/feature-spec-template.md` is the only template. Missing: ADR template, acceptance template (Gherkin scaffolding), task-list template, traceability template, test-plan template, decisions template.

### 1.4 What's Contradictory or Ambiguous

1. **Architecture overview vs. plan directory layout:**  
   `docs/architecture/overview.md` §3 states `apps/api/` and `apps/web/` as the monorepo layout.  
   `specs/001-project-foundation/plan.md` §2 also states `apps/api/` and `apps/web/`.  
   These agree — but neither cross-references the other. If the layout changes, both files will drift silently.

2. **Spec-level decisions.md vs. ADRs:**  
   `docs/adr/0001-monorepo-and-stack.md` captures architectural decisions formally (context, decision, consequences, alternatives). The spec-level `specs/001-project-foundation/decisions.md` captures DEC-001 to DEC-006 informally (one-line entries, no date, no alternatives, no consequences). These overlap (DEC-002 SQLite = partially covered in ADR-0001) but use different formats and are not cross-referenced. A developer reading one won't find the other.

3. **Language of docs:**  
   AGENTS.md, constitution.md, product-vision.md, architecture/overview.md, ADR-0001, and all spec files are in **Spanish**. AGENTS.md heading says "Instrucciones de desarrollo para agentes y colaboradores." The language domain contract for SDD artifacts is English. This is an unresolved tension: the project was started in Spanish but the SDD tooling defaults to English. Neither AGENTS.md nor the constitution explicitly declares the documentation language.

4. **AGENTS.md §5 Architecture vs. plan.md §2 directory layout:**  
   AGENTS.md §5 lists four logical layers: `domain`, `application`, `infrastructure`, `api`.  
   `plan.md` §2 proposes physical path `apps/api/src/wheel_vocab/{domain,application,infrastructure,api}`.  
   These are consistent in intent but the word `apps/api/` is a monorepo wrapper, not a conflict — yet AGENTS.md doesn't mention the `apps/` monorepo wrapper, which could confuse an agent reading only AGENTS.md.

5. **Coverage targets declared vs. not enforced:**  
   `docs/constitution.md` Art. II establishes coverage targets: "Dominio y aplicación: 90% o superior. Cobertura global: 80% o superior." AGENTS.md §6 does not repeat these numbers and doesn't link to the constitution. The spec template doesn't reference them either. No CI enforcement or DoD check references them.

### 1.5 Domain-Specific Constraints from AGENTS.md (and Constitution)

These are hard invariants that any methodology overhaul must preserve and make discoverable:

| Constraint | Source | Implication for docs |
|---|---|---|
| No copyrighted books in repo | AGENTS.md §4, Constitution Art. IV | Tests must use synthetic/public-domain text. Doc examples must use synthetic fragments. |
| User provides books legally | AGENTS.md §4 | Legal disclaimer needed in user-facing docs. |
| No text sent to third parties without consent | AGENTS.md §4, Constitution Art. IV.5 | Architecture docs must show data-flow boundaries explicitly. |
| Local-first by default | AGENTS.md §4, Constitution Art. IV.4 | Architecture baseline must state this explicitly as an invariant, not just a preference. |
| Separate: text form, normalized form, lemma, contextual POS | AGENTS.md §4, Constitution Art. V | Glossary must define these terms precisely. Domain model doc must show relationships. |
| No single global POS per lemma | AGENTS.md §4, Constitution Art. V.2 | Any doc showing the data model must reflect this (POS is per-occurrence, aggregated). |
| Manual corrections prevail over automatic results | AGENTS.md §4, Constitution Art. V.8 | Architecture baseline must name this as an invariant. ADR needed for this decision. |
| Reprocessing never silently overwrites manual corrections | AGENTS.md §4, Constitution Art. V.9 | This is a behavioral invariant that must appear in the processing architecture section. |
| Automatic results store provenance (source, version, date, confidence) | AGENTS.md §4, Constitution Art. V.7 | Data model docs must show provenance fields. |
| Phrasal verbs modeled as multiword expressions separately | AGENTS.md §4, Constitution Art. V.6 | Domain model doc must explicitly show this entity. |
| Linguistic rules not duplicated in frontend | AGENTS.md §4, Constitution Art. VII.5 | Architecture baseline must state this boundary. |

---

## 2. Reference Patterns from Synaptiq.AI + Wellforge.AI

### 2.1 Engineering Playbook v8

**What it is:**  
A versioned, living knowledge corpus stored in Obsidian (`003-Arquitectura de Software/003-Engineering Playbook/`), organized in sections: hexagonal architecture, vertical-slice architecture, pull-request guide, slice contract, operating contract, issue system, conventional commits. Exists in Spanish (source of truth) and English (synced). Currently at v8.1.

**Why it exists:**  
After each project cycle, lessons learned are codified into the playbook. The playbook is not project-specific — it governs how ALL projects in the ecosystem are run. After Synaptiq cycle 2, 8 lessons were absorbed (fail-fast in adapters, PR round-by-round, force-push posture, ordered refinement gating, worktree cleanup, drafts aging, cross-refs in slice contract, multi-level closure). It's the "anti-amnesia" artifact.

**Concrete artifacts:**
- `core/architecture/02-hexagonal-architecture.md` — fail-fast in adapters, port purity
- `core/architecture/04-vertical-slice-architecture.md` — slice-level design
- `core/governance/01-conventional-commits.md` — commit typing
- `core/governance/03-pull-request-guide.md` — PR lifecycle, review rounds, force-push
- `core/governance/06-operating-contract.md` — ordered refinement gating, worktree cleanup
- `core/governance/07-issue-system.md` — issue hierarchy, governance rules
- `core/documentation/03-slice-contract.md` — slice contract meta-template, closure posture
- `agents/AGENTS-rust.md` / `agents/AGENTS-replicate.md` — agent-specific rules
- `case-studies/` — per-project retrospectives

**For wheel-of-words:**  
The playbook exists outside the repo. The project doesn't have a pointer to it or a lightweight Python-flavored adaptation. A "Python-flavored operating contract" section should exist in `docs/governance/` or as a lightweight project-specific excerpt.

### 2.2 SDD + OpenSpec Setup

**What it is:**  
OpenSpec is the artifact store for SDD phases. When initialized, it creates:
- `openspec/config.yaml` — project metadata, stack, persistence mode, test commands, strict_tdd flag, skill registry path
- `.atl/skill-registry.md` — indexed list of skills available to agents

Engram stores the SDD init record (project name, stack, test commands, layers, conventions, persistence mode, session config). The combination of OpenSpec (filesystem artifacts) + Engram (context memory) enables agents to pick up context across sessions without re-reading the entire repo.

**Why it exists:**  
Without it, every agent session re-discovers the same facts about stack, test commands, and conventions. With it, `sdd-init` runs once, agents read `openspec/config.yaml` and `.atl/skill-registry.md`, and can immediately start SDD phases.

**Concrete artifacts:**
- `openspec/config.yaml` — single source of SDD context
- `openspec/changes/<change-name>/` — per-change SDD artifacts (explore, proposal, spec, design, tasks, apply, verify, archive)
- `openspec/specs/` — baseline specs
- `.atl/skill-registry.md` + `.atl/.skill-registry.cache.json`

**For wheel-of-words:**  
`openspec/` doesn't exist yet (this exploration is creating it). `openspec/config.yaml` is absent. The `.atl/` registry exists but doesn't list SDD skills. This gap means agents have no reliable SDD context bootstrap.

### 2.3 ADR Set + Architecture Baseline Document

**What it is (Wellforge.AI pattern):**

**Architecture baseline:** `docs/architecture/architecture-baseline.md` — a snapshot document stating "this is the architecture we have committed to as of [date]." It's distinct from the ARD or overview: it's a commitment record. It explicitly names what IS committed vs. what is deferred. Wellforge committed: PostgreSQL as system of record, NATS as transport (not truth), outbox pattern for restart-safety, DB-backed slice state.

**ADR set:** `docs/adr/` with:
- `README.md` — ADR index, status definitions (Proposed → Accepted → Superseded/Deprecated)
- `0000-template.md` — canonical ADR template
- Per-ADR files named `NNNN-<slug>.md` with: Status, Date, Context, Decision, Consequences (positive/negative), Alternatives considered.

Synaptiq had 4 ADRs at commit time (all Proposed → standard evolution path). Wellforge had at least 6 ADRs committed (ADR-006 was slice orchestration). Cairn immediately created `doc/adr/README.md` + `doc/adr/0000-template.md` even before implementation started.

**Why it exists:**  
ADRs capture the "why" behind decisions that would otherwise disappear into commit history. The architecture baseline captures the "what is now committed" so future agents/developers don't have to re-derive it. Together they form the authoritative record of architectural choices.

**Concrete artifacts:**
- `docs/adr/README.md` — index + status definitions + authoring rules
- `docs/adr/0000-template.md` — ADR template
- `docs/adr/NNNN-<slug>.md` — per-decision ADR
- `docs/architecture/architecture-baseline.md` — committed state snapshot (with SVG diagram in Wellforge)

### 2.4 Decisions Log

**What it is:**  
A chronological, project-level log of architectural and product decisions. In Synaptiq, this lived in Obsidian as `12-Log-de-Decisiones.md` — a timeline of 20 decisions from 2026-06-15 to 2026-06-23, each with: date, decision, WHY, consequences. In Cairn, it's `Decision Log` in Obsidian. For repos-without-Obsidian, this becomes `docs/decisions-log.md` or similar.

**Why it exists:**  
The per-spec `decisions.md` files capture spec-scoped decisions. The ADR set captures architectural decisions. Neither captures the cross-cutting, chronological "why did we choose X at time T" story. The decisions log is the human narrative that makes the ADRs navigable. It's especially important for linguistic-domain projects where decisions about POS modeling, lemma grouping, confidence thresholds, etc. accumulate quickly.

**Concrete artifacts:**
- `docs/decisions-log.md` — chronological table: date, decision, category (architecture/product/methodology), rationale, linked ADR or spec

### 2.5 Traceability Matrix (REQ-`<feature>`-`<n>`)

**What it is:**  
The convention `REQ-<feature>-<n>` is already in use in wheel-of-words (`REQ-001-001` through `REQ-001-018`). In Wellforge, requirements live in `docs/requirements/` with per-slice requirement maps. Synaptiq had a `master-final-project-requirement-map.md` (provisional) mapping requirement families → artifacts → issues → evidence.

**Why it exists:**  
Without a traceability matrix, a team cannot answer: "Is REQ-003-007 tested?" or "Which requirements does PR #42 satisfy?" The matrix is the audit trail.

**Gap in wheel-of-words:**  
The matrix exists for SPEC-001 but all rows are "Pendiente." There's no convention for what "complete" looks like in a traceability row, no DoD check referencing the matrix, and no `docs/requirements/` directory for cross-spec requirement maps.

**Concrete artifacts (reference pattern):**
- `specs/<NNN>-<name>/traceability.md` — per-spec (already exists)
- `docs/requirements/requirement-map.md` — cross-spec requirement index
- Update convention: traceability updated as part of task closure (T062 already calls this out)

### 2.6 Skill Registry

**What it is:**  
`.atl/skill-registry.md` — an indexed table of skills available to agents, with: skill name, trigger/description, scope (user/project), and `SKILL.md` path. The loading protocol is part of the file: match trigger → pass path to subagent → subagent reads `SKILL.md` before work.

**Reference pattern (Synaptiq):**  
Synaptiq had 25 skills (4 repo-local + 21 user-level). Wellforge's registry was updated as of 2026-06-28.

**Current state in wheel-of-words:**  
11 skills indexed — all user-scoped, none project-scoped. **Missing the entire SDD skill suite:**
- `sdd-init`, `sdd-explore`, `sdd-propose`, `sdd-spec`, `sdd-design`, `sdd-tasks`, `sdd-apply`, `sdd-verify`, `sdd-archive`, `sdd-onboard`
Also missing: `skill-registry` (for regeneration), `judgment-day`, and any project-specific skills.

**Why it matters:**  
Without the SDD skills in the registry, an orchestrator agent reading only the registry will not select the correct skills for SDD phase work. The registry is the dispatch table; if it's incomplete, dispatching is blind.

**Concrete artifacts:**
- `.atl/skill-registry.md` — updated to include all SDD skills + any project-specific skills

### 2.7 Issue System / Governance

**What it is (Wellforge pattern):**  
`docs/governance/` directory with:
- `issue-policy.md` — when to create issues, what they must contain, how to close them
- `issue-approval.md` — who approves what before work starts
- `branch-policy.md` — branch naming, worktree rules, deletion after merge
- `label-catalog.md` — canonical label taxonomy (surface/status/type labels)
- `docs-only-work.md` — when to skip issues for docs changes
- `repository-setup.md` — one-time setup guide

Synaptiq's `core/governance/07-issue-system.md` in the Engineering Playbook defines the full issue lifecycle: hierarchy (epic → feature → task), governance gates (approve before work), label discipline, and escalation paths. The Playbook rule "Regla menos uno" (pre-flight check before proposing a governance system): don't add process unless the problem is real.

**For wheel-of-words:**  
No `docs/governance/` exists. The project has no GitHub-linked issue workflow documented. AGENTS.md mentions TDD order but not the issue-before-work gate. Since wheel-of-words is currently a solo project (not a multi-contributor setup), the full Wellforge governance weight is likely overkill. A lighter `docs/governance/` with issue-policy and branch-policy is sufficient.

**Concrete artifacts:**
- `docs/governance/` — lightweight governance directory (2-3 files, not 6)

### 2.8 Documentation Style (Diagrams, Obsidian-companion, Denseness Rules)

**What it is (reference pattern):**

**Obsidian companion:** Synaptiq and Cairn used Obsidian as an external architecture knowledge base (hub note + linked notes per topic: architecture synthesis, decisions log, slice map, changelog). This is external to the repo and personal. Wellforge used only repo-based docs (engram mode, no Obsidian reference documented).

**Diagrams:** Wellforge committed SVG diagrams to `docs/assets/diagrams/`. Synaptiq used ASCII art in `doc/` and visual "editorial sheet" style (sepia paper, hand-drawn pen-like strokes) for mermaid/SVG artifacts. Both used text-first for embedded diagrams in Markdown files.

**Cognitive-doc-design rules (from loaded skill):**
- Lead with the answer (decision/action first, context after)
- Progressive disclosure (happy path → details → edge cases → references)
- Chunking (small sections, short flat lists)
- Signposting (headings, callouts, summaries)
- Recognition over recall (tables, checklists, examples, templates)
- Review empathy (verifiable intent without reconstructing the story)

**Denseness rules from Obsidian 040 (Engineering Playbook):**  
Documentation files should have: one concern per document (no omnibus files), a one-paragraph executive summary at the top, explicit "out of scope" sections, and internal cross-references rather than copy-paste content.

**For wheel-of-words:**  
Current docs are reasonably dense but lack: executive summaries at the top of most files, explicit cross-references between related files, Mermaid diagrams (only ASCII), and a `docs/assets/` directory for diagram assets. The constitution and spec files are well-structured. The architecture overview needs a Mermaid context diagram.

---

## 3. Gap Analysis

| Pattern | Current state in wheel-of-words | Gap | Priority | Rough effort |
|---|---|---|---|---|
| `openspec/config.yaml` | Does not exist | No SDD context bootstrap for agents | P0 | XS (1h) |
| SDD skills in `.atl/skill-registry.md` | 11 skills, 0 SDD skills | Agents cannot dispatch SDD phases | P0 | XS (30m) |
| ADR template (`docs/adr/0000-template.md`) | Does not exist | No canonical template; ADRs will drift in format | P0 | XS (30m) |
| ADR index (`docs/adr/README.md`) | Does not exist | ADRs are undiscoverable | P0 | XS (30m) |
| Missing ADRs for implicit decisions | 1 ADR exists, ~10 implicit decisions | Decisions are invisible | P0 | S (3-4h) |
| Architecture baseline (`docs/architecture/architecture-baseline.md`) | Does not exist | No committed-state snapshot; `overview.md` is aspirational | P0 | S (2h) |
| Decisions log (`docs/decisions-log.md`) | Does not exist | No chronological narrative of why decisions were made | P0 | S (1-2h) |
| `docs/glossary.md` | Does not exist | Critical for linguistic domain: 15+ terms undefined at doc level | P0 | S (2h) |
| `openspec/config.yaml` — full init | Does not exist | SDD phases cannot start properly | P0 | XS (1h) |
| `DEFINITION_OF_DONE.md` at repo root | Buried in constitution Art. XI and AGENTS.md §10 | Not discoverable; agents reading only root files miss it | P1 | XS (30m) |
| `docs/testing/testing-strategy.md` | Testing rules in AGENTS.md §6 only | Not a standalone navigable doc; pyramid/layers not diagrammed | P1 | S (1-2h) |
| Templates: ADR, acceptance, task-list, test-plan | Only `feature-spec-template.md` | Spec artifacts will drift in format | P1 | S (2-3h) |
| `docs/governance/` (lightweight) | Does not exist | No issue/branch policy; no label catalog | P1 | S (2h) |
| Cross-references between docs | Minimal; no file links each other | Silent drift between related docs | P1 | XS–S (1h) |
| Mermaid/SVG diagrams | ASCII art only | Context diagram is hard to read for new contributors | P1 | S (2h) |
| `docs/requirements/requirement-map.md` | Traceability per-spec only | No cross-spec view | P1 | S (1h) |
| Obsidian companion | Not applicable (out of scope for repo) | — | P2 | N/A |
| Decisions log per spec (`decisions.md`) — enriched format | Flat one-liners, no dates/links | Format inconsistent with ADRs | P2 | XS (1h) |
| Engineering Playbook Python adaptation | No reference | Playbook rules exist in Engram/Obsidian, not in repo | P2 | M (4-8h) |
| `CONTRIBUTING.md` | Does not exist | New contributor entry point absent | P2 | XS (1h) |
| `ALLIANCE.md` / `PROJECT_CONTEXT.md` | Does not exist | Agent trust model / meta-contract absent | P2 | XS (1h) |
| Lesson-learned artifact after each cycle | Not defined | Playbook never gets updated from project learnings | P2 | XS (30m per cycle) |
| `docs/flows/` (happy path + error flows) | No explicit flows | Main scenario described in product-vision only | P2 | S (2-3h) |

---

## 4. Recommended Scope for the Change Proposal

### 4.1 Must-Have (P0)

These gaps make SDD phases and agent work unreliable without them:

1. **`openspec/config.yaml`** — Bootstrap SDD context for all future phases. Minimal config: project name, stack (Python/FastAPI/React/SQLite/spaCy), test commands, strict_tdd, persistence mode, skill registry path.

2. **Update `.atl/skill-registry.md`** — Add all SDD skills (sdd-init, sdd-explore, sdd-propose, sdd-spec, sdd-design, sdd-tasks, sdd-apply, sdd-verify, sdd-archive, sdd-onboard, skill-registry). Run `gentle-ai skill-registry refresh --force` after.

3. **`docs/adr/README.md`** — ADR index with status definitions and authoring rules.

4. **`docs/adr/0000-template.md`** — Canonical ADR template (Context, Decision, Status, Date, Consequences +/-, Alternatives).

5. **ADRs for existing implicit decisions** — At minimum:
   - ADR-0002: local-first processing as invariant
   - ADR-0003: manual corrections precedence over NLP results
   - ADR-0004: POS per occurrence, not per lemma
   - ADR-0005: spaCy as first NLP adapter (replaceable via port)
   - ADR-0006: OpenAPI as frontend-backend contract source of truth

6. **`docs/architecture/architecture-baseline.md`** — Committed architecture snapshot: what is decided now vs. deferred. Include: local-first, hexagonal layers, SQLite MVP, spaCy as first adapter, correction-precedence invariant.

7. **`docs/glossary.md`** — Define the core linguistic-domain terms: token, text form, normalized form, lemma, occurrence, POS (contextual), confidence score, phrasal verb, multiword expression, learning status, manual correction, processing run, provenance.

8. **`docs/decisions-log.md`** — Chronological table of project decisions from inception to present (15-20 entries minimum, covering constitution adoption, ADR-0001, SPEC-001 decisions).

### 4.2 Should-Have (P1)

These significantly improve the quality and navigability of the methodology:

9. **`DEFINITION_OF_DONE.md`** at repo root — Extract and formalize from constitution Art. XI + AGENTS.md §10. Link back to constitution.

10. **`docs/testing/testing-strategy.md`** — Extract testing rules from AGENTS.md §6 into a standalone document. Include: test pyramid diagram (Mermaid), layer descriptions, property-based testing invariants, linguistic regression convention.

11. **Extended template set** — Add: `templates/adr-template.md`, `templates/acceptance-template.md`, `templates/task-list-template.md`, `templates/test-plan-template.md`, `templates/decisions-template.md` (enriched format with date, alternatives, links).

12. **`docs/governance/` (lightweight — 2 files):**
    - `docs/governance/issue-policy.md` — when to create issues, what they must contain, lifecycle
    - `docs/governance/branch-policy.md` — branch naming, delete after merge

13. **Cross-references** — Add explicit cross-reference footers to: constitution.md → ADR index, overview.md → baseline + ADR index, AGENTS.md → constitution, glossary, testing-strategy.

14. **Mermaid context diagram** — Replace ASCII context diagram in `architecture/overview.md` with embedded Mermaid diagram.

15. **`docs/requirements/requirement-map.md`** — Cross-spec requirement index (initially just maps SPEC-001 REQs; expands with each new spec).

### 4.3 Nice-to-Have (P2 — Defer)

16. **Obsidian companion** — External to repo; personal knowledge base. Not needed for repo health.

17. **Engineering Playbook Python adaptation** — A `docs/playbook-notes.md` capturing the Python-flavored lessons after each cycle. Low priority until cycle 2 completes.

18. **`CONTRIBUTING.md`** — Useful for open-source projects; currently solo project.

19. **`ALLIANCE.md` / `PROJECT_CONTEXT.md`** — Agent meta-contract. Add when multi-agent workflows become regular.

20. **`docs/flows/`** — Explicit flows (happy path, error path, import flow, export flow). Defer until SPEC-002+ are written and the domain is better understood in implementation.

21. **Lesson-learned artifact convention** — Define the format after SPEC-001 is fully implemented.

22. **Enriched per-spec `decisions.md` format** — Migrate existing DEC-001..006 to enriched format with dates, alternatives, ADR links.

### 4.4 Explicitly Out of Scope

- **Code directory structure** — No changes to `apps/`, Python package layout, `src/wheel_vocab/`, or any code files. This is a separate SDD cycle.
- **Backend/frontend implementation shape** — No changes to FastAPI routes, SQLAlchemy models, React components, etc.
- **Python package layout choices** — `uv` workspace config, `pyproject.toml` contents, package naming — all deferred.
- **Infrastructure decisions** — NATS, pgvector, Docling, outbox pattern — not applicable to this Python local-first domain.
- **CI pipeline changes** — No `.github/workflows/` changes.
- **AGENTS.md rewrites** — AGENTS.md is authoritative; changes should be additive (cross-references) not rewrites.
- **README.md rewrite** — Significant README expansion belongs after the first vertical slice is implemented and the setup process is real.
- **Obsidian vault contents** — External to repo; out of scope.

---

## 5. Open Questions for the User

1. **Documentation language:** AGENTS.md and all current docs are in Spanish. The SDD language domain contract defaults to English for technical artifacts. For this project's documentation, do you want:
   - **Option A:** Keep Spanish for all docs (matches current convention and AGENTS.md tone).
   - **Option B:** English for new methodology artifacts (ADRs, architecture baseline, glossary, governance), Spanish for product-facing docs (constitution, product-vision, specs).
   - **Option C:** Declare a policy in the constitution (amendment) and follow it consistently.
   *This decision affects the proposal and every subsequent SDD phase.*

2. **Obsidian vs. docs-in-repo:** Do you want an Obsidian companion for wheel-of-words (like Synaptiq's `001-Proyectos/Synaptiq.AI/` set), or docs-in-repo only? The exploration assumes docs-in-repo only (scope constraint confirmed), but confirming this avoids future drift.

3. **Engineering Playbook reference:** Do you want a lightweight Python-flavored playbook excerpt in `docs/` (e.g., `docs/playbook-notes.md`) from day one, or add it after the first cycle completes and there are real lessons to capture?

4. **ADR numbering:** Global sequential (ADR-0001, ADR-0002...) or per-capability (ADR-NLP-001, ADR-ARCH-001...)? Current ADR-0001 uses global sequential — recommend continuing that convention, but confirming avoids confusion.

5. **Traceability matrix format:** Current format is a Markdown table in `traceability.md`. Alternatives: YAML (machine-readable, harder to read inline), generated from spec annotations (requires tooling), or keep Markdown. Recommend keeping Markdown — is that acceptable?

6. **Governance weight:** Wellforge has a full `docs/governance/` with 6 files. For a solo project, 2 files (issue-policy, branch-policy) seem sufficient. Do you want the minimal 2-file version, or the full 6-file set anticipating future contributors?

7. **Architecture baseline format:** Text-only Markdown (like AGENTS.md), or Markdown + embedded Mermaid diagram? Wellforge committed an SVG diagram separately. For wheel-of-words, an embedded Mermaid context diagram in the baseline is the lowest-friction approach — is that acceptable?

8. **`DEFINITION_OF_DONE.md` vs. staying in constitution:** Extracting DoD to a root-level file increases discoverability. But it risks the constitution and DoD drifting. Preferred approach: extract to `DEFINITION_OF_DONE.md`, add a cross-reference in the constitution, and note that the constitution is canonical in case of conflict.

---

## 6. Risks

- **Language drift:** If the documentation language question (Q1) is not resolved before the proposal, some artifacts may be written in English and some in Spanish, creating a bilingual mess that's harder to fix later than to avoid.

- **Copying Synaptiq/Rust patterns verbatim:** Synaptiq's doc structure (`doc/slices/`, three-level refinement convention, NATS/outbox references) is Rust-workspace and infrastructure-heavy. Importing it blindly into a Python/FastAPI project will confuse contributors and create irrelevant governance overhead. The adaptation must be deliberate.

- **ADR proliferation:** Creating many ADRs at once (for already-made decisions) risks them all being dated the same day and feeling like retroactive rationalization. Recommend: write ADRs as if "we are deciding now," but date them accurately relative to when the decision was actually made (use project start date for foundational decisions).

- **OpenSpec artifacts in Git:** Synaptiq established a firm rule (Engram #1671): OpenSpec artifacts must NOT be committed to the repo. For wheel-of-words, the question of whether `openspec/` is committed or gitignored must be decided explicitly. If committed, `openspec/changes/` contains SDD planning artifacts that may be redundant with `specs/`. Recommend: add `openspec/changes/` to `.gitignore` (agent working directory) but commit `openspec/config.yaml` and `openspec/specs/` (baseline).

- **Traceability staleness:** The existing traceability matrix is "Pendiente" for all rows despite the spec being complete. If the convention for updating it is not formalized before implementation starts, it will remain stale indefinitely. The DoD check must explicitly reference traceability.

- **Constitution amendment vs. AGENTS.md update:** AGENTS.md and the constitution overlap significantly (TDD cycle, DoD, architecture). If a new rule is added only to one, they will drift. A cross-reference convention must be established.

---

## 7. Skill Resolution

| Skill | Status | Role in this exploration |
|---|---|---|
| `sdd-explore` | ✅ Loaded (path read directly as executor) | Primary skill governing this phase |
| `cognitive-doc-design` | ✅ Loaded | Applied to report structure: lead-with-answer, chunking, recognition-over-recall (tables), signposting (section headers) |
| `_shared` | ✅ Loaded (support reference) | Confirmed not invokable; noted shared reference role |

**Skill resolution result:** `paths-injected` — all three skills loaded from their `SKILL.md` paths. No fallback required.

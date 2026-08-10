# Decisions log — wheel-of-words

This log is the chronological record of binding decisions made in this project. Each row records what was decided, why, its category, and where to find the authoritative record. New entries are appended in ascending date order. Within the same date, entries are grouped by category: governance → architecture → linguistic-model → methodology → product.

See [`docs/adr/README.md`](adr/README.md) for the ADR index that this log cross-references.

---

## Update rules

1. Add a row when a decision is made and the authoritative artifact (ADR, spec, constitution section) is committed.
2. Chronological order (ascending by date) is mandatory; do not insert rows out of order.
3. Within the same date, group by category: governance → architecture → linguistic-model → methodology → product.
4. The `Ref` column MUST point to the authoritative artifact, not a planning note.
5. Do not delete rows. If a decision is superseded, add the superseding row with a `Ref` pointing to the new ADR or amendment.

---

## Log

| Date | Decision | Category | Ref | Motivation | Consequence |
|------|----------|----------|-----|------------|-------------|
| 2026-07-15 | Constitution v1.0.0 adopted | Governance | [`docs/constitution.md`](constitution.md) | Establish non-negotiable principles for the project | 12 articles govern all future features; no feature may contradict them without a formal amendment |
| 2026-07-15 | Monorepo + Python/FastAPI/SQLite/React/Vite stack | Architecture | [`docs/adr/0001-monorepo-and-stack.md`](adr/0001-monorepo-and-stack.md) | Consolidate MVP delivery in one repository; Python suits NLP; SQLite enables local-first | Coordinated CI, shared OpenAPI contract, two dependency ecosystems to maintain |
| 2026-07-15 | SPEC-001 DEC-001: React with Vite (no SSR, no Node backend) | Product | [`specs/001-project-foundation/decisions.md`](../specs/001-project-foundation/decisions.md) | No SSR needed; Vite reduces complexity | Frontend remains a static SPA; no server-side rendering concern for MVP |
| 2026-07-15 | SPEC-001 DEC-002: SQLite as MVP persistence | Architecture | [`specs/001-project-foundation/decisions.md`](../specs/001-project-foundation/decisions.md) | Favors local-first, minimal installation, future migration via SQLAlchemy | SQLite file is the single persistence artifact; migration to PostgreSQL possible later |
| 2026-07-15 | SPEC-001 DEC-003: FastAPI factory pattern | Architecture | [`specs/001-project-foundation/decisions.md`](../specs/001-project-foundation/decisions.md) | Enables configuration injection and isolated testing | Application factory required for all FastAPI instantiation; no module-level app object |
| 2026-07-15 | SPEC-001 DEC-004: OpenAPI as backend-frontend contract | Architecture | [`specs/001-project-foundation/decisions.md`](../specs/001-project-foundation/decisions.md) | Contract derived from OpenAPI spec; frontend type-safe clients generated from it | Backend changes that break the OpenAPI schema break the frontend; contract is the boundary |
| 2026-07-15 | SPEC-001 DEC-005: No fictitious domain in SPEC-001 | Product | [`specs/001-project-foundation/decisions.md`](../specs/001-project-foundation/decisions.md) | SPEC-001 creates layers only; linguistic entities arrive with functional requirements | Domain entities (Lexeme, Occurrence, MWE, etc.) deferred to first functional feature spec |
| 2026-07-15 | SPEC-001 DEC-006: Docker Compose optional | Architecture | [`specs/001-project-foundation/decisions.md`](../specs/001-project-foundation/decisions.md) | Native commands are the primary path; Docker Compose is reproducibility support | Docker not required for development; CI may use it; contributors can use native tooling |
| 2026-07-15 | Hexagonal layer split (domain / application / infrastructure / api) | Architecture | [`docs/adr/0002-hexagonal-split.md`](adr/0002-hexagonal-split.md) | Enforce Constitution Art. VII; domain must be framework-free | Domain stays testable without infrastructure; NLP and DB are swappable via ports |
| 2026-07-15 | TDD mandatory RED → GREEN → REFACTOR | Process | [`docs/adr/0003-tdd-mandatory.md`](adr/0003-tdd-mandatory.md) | Enforce Constitution Art. II; no implementation without a failing test first | Higher upfront effort per feature; continuous behavioral validation from day one |
| 2026-07-15 | SDD + OpenSpec as planning method | Process | [`docs/adr/0004-sdd-openspec.md`](adr/0004-sdd-openspec.md) | Enforce Constitution Art. I; 7 pre-code artifacts required before any implementation | Every feature ships with explore/proposal/spec/design/tasks; traceability is structural |
| 2026-07-15 | Local-first processing, no default third-party egress | Privacy | [`docs/adr/0005-local-first.md`](adr/0005-local-first.md) | Enforce Constitution Art. IV.4–5; book text must not leave the device without consent | NLP models run locally; cloud integrations require explicit consent UI gate |
| 2026-07-15 | POS-per-occurrence linguistic model | Domain | [`docs/adr/0006-pos-per-occurrence.md`](adr/0006-pos-per-occurrence.md) | Enforce Constitution Art. V.2–3; a lemma may have multiple grammatical categories | POS stored on each Occurrence, not on Lexeme; homographs handled correctly per token |
| 2026-07-16 | Constitution amended to v2.0.0 (MAJOR): multi-language scope, approval date, four-file coordinated payload | Governance | [`docs/constitution.md §Registro de enmiendas`](constitution.md) (Slice E) | Multi-language scope (ADR-0008) requires MAJOR bump per Art. XII; incompatible change | Four-file coordinated amendment payload lands in Slice E; pre-amendment files still at v1.0.0 scope until then |
| 2026-07-16 | Manual corrections take precedence; reprocessing is non-destructive | Domain | [`docs/adr/0007-manual-corrections-precedence.md`](adr/0007-manual-corrections-precedence.md) | Constitution Art. V.8–9 already invariant; codify the implementation constraint | Reprocessing safe by default; ManualCorrection entity is first-class; OQ-1 (UX shape) deferred |
| 2026-07-16 | Multi-language scope from day one — three-part decision | Product/Architecture | [`docs/adr/0008-multi-language-scope.md`](adr/0008-multi-language-scope.md) | User decision this cycle; escalates constitution to v2.0.0 MAJOR | 4-file amendment payload lands in Slice E; OQ-2/3/4 deferred to future ADRs |
| 2026-07-16 | MWE as language-specific instances; mwe_kind field; phrasal verbs = English instance | Domain | [`docs/adr/0009-mwe-language-specific-instances.md`](adr/0009-mwe-language-specific-instances.md) | Direct consequence of ADR-0008; abstract MWE category needed for multi-language model | mwe_kind attribute in MultiwordExpression domain entity; new languages add mwe_kind values, not schema changes |
| 2026-07-16 | Documentation language policy — methodology EN, product-facing ES | Methodology | [`docs/adr/0010-documentation-language-policy.md`](adr/0010-documentation-language-policy.md) | Match SDD tooling defaults; methodology artifacts consumed by agents benefit from EN | Bilingual repo with clear per-file language policy enforced at review time |
| 2026-07-16 | Engineering Playbook adoption deferred | Methodology | `openspec/changes/docs-methodology-overhaul/proposal.md §4` | Playbooks written before real development cycles are speculative | Revisit trigger: "After first vertical slice ships end-to-end (upload a .txt file and view a lemma list with frequency)" |
| 2026-07-16 | Language policy for product-facing artifacts: ES; for methodology: EN | Methodology | [`docs/adr/0010-documentation-language-policy.md`](adr/0010-documentation-language-policy.md) | Consistency with ADR-0010 decision | AGENTS.md classified as ES; mixed artifacts follow scaffold language |
| 2026-07-16 | ADR template filename: `_template.md` (not `0000-template.md`) | Methodology | `openspec/changes/docs-methodology-overhaul/design.md §2.2 (OQ-9)` | Prevents template from appearing as indexed ADR entry; underscore-prefix is more discoverable | docs/adr/_template.md is the canonical authoring skeleton; not indexed in README |
| 2026-07-16 | Amendment log placement: new `## Registro de enmiendas` section after Art. XII | Governance | `openspec/changes/docs-methodology-overhaul/design.md §2.1 (OQ-8)` | Separates procedure (Art. XII) from history (amendment record); named section is linkable | Art. XII body text unchanged; amendment history grows in its own section |
| 2026-07-16 | Canonical ES wording for language-specific MWE: "expresiones multipalabra específicas del idioma" | Methodology | `openspec/changes/docs-methodology-overhaul/design.md §2.3 (OQ-10)` | Consistent term across 9 files; option 1 is most explicit and unambiguous | Glossary abstract entry and ADR-0008/0009 use this string verbatim; no synonyms permitted |
| 2026-07-16 | Architecture baseline committed | Architecture | [`docs/architecture/architecture-baseline.md`](architecture/architecture-baseline.md) | Freeze the current architectural intent as a committed-state snapshot | Living overview.md remains the forward-looking doc; baseline is the point-in-time commitment |
| 2026-07-16 | Glossary landed with 13 canonical entries | Documentation | [`docs/glossary.md`](glossary.md) | Domain legibility; 13 load-bearing terms disambiguated in Spanish for product-facing use | OQ-10 canonical wording applied as abstract MWE entry heading; phrasal verb repositioned as instance |
| 2026-07-16 | docs-methodology-overhaul SDD cycle executed | Governance | [`openspec/changes/docs-methodology-overhaul/`](../openspec/changes/docs-methodology-overhaul/) | Lift the methodology surface (ADRs, architecture baseline, glossary, traceability, DoD, constitution amendment) to Synaptiq/Wellforge level | 5 slices A..E; ~1700–1830 lines aggregate; Wave 1 ADRs (0002–0006) in Slice B; Wave 2 (0007–0010) in Slice C |

---

> Log seeded through 2026-07-16. Future decisions append chronologically.

# ADR-0010 — Documentation language policy: methodology EN, product-facing ES

Status: Accepted

Date: 2026-07-16

## Context

Prior to the docs-methodology-overhaul cycle, no file in the repository declared a documentation language policy. All existing documents — `docs/constitution.md`, `docs/product-vision.md`, `AGENTS.md`, and the pre-existing `docs/adr/0001-monorepo-and-stack.md` — were written in Spanish. This was a natural outcome of the project's Spanish-speaking audience, but it created an unresolved tension: SDD tooling (skill descriptions, OpenSpec config keys, ADR templates from the gentle-ai ecosystem) defaults to English, and agent sessions that process English-first tooling artifacts while reading Spanish methodology docs introduced unnecessary translation overhead.

The exploration phase (docs-methodology-overhaul §1.4) identified this tension as a first-class risk: without a declared language policy, each new artifact would be written in whatever language felt natural at the time, producing a bilingual repo with no rule governing the boundary.

During this cycle, the decision was made to split the artifact family into two groups with distinct language assignments:

- **Methodology artifacts**: consumed primarily by agents, tooling, and developers. Benefit from English-first phrasing to align with SDD tooling defaults and industry-standard ADR practice.
- **Product-facing artifacts**: consumed primarily by the product owner and end user. Established in Spanish; continuity and audience relevance require maintaining Spanish.

This ADR self-referentially demonstrates the policy: the ADR itself is a methodology artifact and is therefore written in English.

## Decision

1. **Methodology artifacts default to English**: `openspec/config.yaml`, `.atl/skill-registry.md`, all ADR files (`docs/adr/*.md`), `docs/architecture/architecture-baseline.md`, `docs/decisions-log.md`, and `docs/traceability-matrix.md` are written in English.

2. **Product-facing artifacts stay in Spanish**: `docs/constitution.md`, `docs/product-vision.md`, `docs/glossary.md`, `docs/definition-of-done.md`, `README.md`, and `AGENTS.md` are written in Spanish.

3. **`AGENTS.md` is classified as a product-facing/contractual artifact** (existing Spanish contract; amendments preserve Spanish). Its audience includes both agents (who parse it for instructions) and the project owner (who authors it). Spanish is maintained.

4. **Mixed artifacts** (e.g., traceability matrix with an English scaffold and Spanish requirement IDs) follow the scaffold language. Cross-references to Spanish artifact titles or IDs are acceptable within an English document.

5. **Code identifiers and inline comments** default to English regardless of the language of the surrounding document. This follows the language-domain contract of the SDD tooling.

This policy is enforced by code review and agent instructions; violations are corrected at review time, not at write time.

## Consequences

### Positive

- Every contributor and agent knows which language to use before writing a new file; the decision is not per-file ad hoc.
- ADR-0010 is self-referential proof that the policy is coherent and immediately applicable.
- Aligns with SDD tooling defaults, reducing friction for agent-assisted development.
- Product-facing artifacts remain in the language of their audience without retrofitting.

### Negative

- The EN/ES boundary requires active enforcement; a new contributor who does not read ADR-0010 may write a methodology artifact in Spanish or a product-facing artifact in English.
- Bilingual repos are less searchable than single-language repos — full-text search tools may miss matches when the query language does not match the document language.
- Future contributors unfamiliar with the dual-language model may need onboarding before they can contribute confidently.

## Alternatives considered

- **All-Spanish** — Rejected: SDD tooling is English-first; methodology artifacts produced by agents (skill registry entries, OpenSpec config) arrive in English by default. Converting them all to Spanish would require systematic translation and introduce drift between tooling defaults and project practice.
- **All-English** — Rejected: the product-facing artifacts (constitution, product-vision, README, AGENTS.md) are already established in Spanish and their audience is the Spanish-speaking project owner. Translating them to English would lose the intended audience alignment with no compensating benefit.
- **Declare the policy in a constitution amendment** — Rejected: this ADR is sufficient and more appropriately scoped. A constitution amendment would be proportionate only if the language policy were itself a non-negotiable constitutional invariant. As a methodology decision it belongs in the ADR layer; the constitution governs product principles, not documentation formatting.

## References

- [`openspec/config.yaml`](../../openspec/config.yaml) — persistence_mode, language-domain contract
- [`docs/adr/README.md`](README.md) — Authoring rule 7: "Language: EN (methodology artifact per ADR-0010)"
- [`docs/glossary.md`](../glossary.md) — ES policy (product-facing artifact)
- `openspec/changes/docs-methodology-overhaul/proposal.md §5` — Language mapping table from exploration

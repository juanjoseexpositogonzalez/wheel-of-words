# ADR-0004 — SDD + OpenSpec as the planning method for all features

Status: Accepted

Date: 2026-07-15

## Context

AGENTS.md §1 sets a hard gate before any code can be written:

> "Ninguna funcionalidad debe implementarse directamente desde una petición informal. Antes de modificar código deben existir, como mínimo: 1. Una especificación de la feature. 2. Requisitos identificados de forma única. 3. Criterios de aceptación observables. 4. Un plan técnico. 5. Un plan de pruebas. 6. Una lista de tareas ordenada. 7. Una matriz de trazabilidad inicial."

Constitution Art. I reinforces this at the constitutional level:
- Art. I.1: "Toda feature debe disponer de una especificación antes de su implementación."
- Art. I.2: "Los requisitos deben estar numerados y ser verificables."
- Art. I.3: "Las decisiones técnicas no deben confundirse con requisitos de producto."
- Art. I.4: "Las ambigüedades deben resolverse en la especificación, no ocultarse en el código."
- Art. I.5: "Las modificaciones deben actualizar especificación, aceptación, pruebas, tareas y trazabilidad."

The SDD (Specification-Driven Development) methodology operationalizes these rules via a phased artifact set: explore → proposal → spec → design → tasks → apply → verify → archive. The OpenSpec format stores these artifacts as Markdown files under `openspec/changes/<slug>/`, making them human-readable, version-controlled, and machine-parseable by agent sessions.

Two infrastructure artifacts bootstrap each agent session:
- `openspec/config.yaml`: project name, stack, test commands, persistence mode, strict_tdd flag, skill registry path, change-slug convention, and phase rules. Created in Slice A of this cycle.
- `.atl/skill-registry.md`: dispatch table mapping trigger phrases to SDD skill paths, enabling any agent to find the right skill without re-reading the full repo. Also updated in Slice A.

The SDD methodology is the mechanism by which Constitution Art. I is operationalized across every feature cycle. Without it, the constitutional requirement for pre-implementation specifications has no enforcement surface.

## Decision

All features and changes to this repository MUST go through the full SDD artifact sequence — explore, proposal, spec, design, tasks — before any implementation (apply) begins. The seven pre-code artifacts listed in AGENTS.md §1 are not optional.

`openspec/` is the artifact store under version control. Engram is the persistence backend for agent memory across sessions. Hybrid persistence mode (`persistence_mode: hybrid` in `openspec/config.yaml`) is active: both the filesystem and Engram are written.

Each change produces the full SDD artifact set: the eight phases are explore, proposal, spec, design, tasks, apply, verify, and archive. No phase may be skipped. Deviations require an explicit exception recorded in the artifact for that phase.

## Consequences

### Positive

- Agent sessions can bootstrap from `openspec/config.yaml` without reading the entire repository — the project stack, commands, and skill registry are immediately available.
- Traceability is structural from day one: every REQ-ID has a spec, every spec has an acceptance criterion, every criterion maps to a test, every test maps to a task.
- The SDD archive phase preserves the decision record so future sessions can reason about why a choice was made, not just what was chosen.

### Negative

- Non-trivial overhead per feature: even small changes require a proposal and spec before coding begins.
- Planning is non-negotiable even for obvious fixes — the methodology does not distinguish trivial from complex; every change goes through the gate.

## Alternatives considered

- **Informal task management (GitHub issue → code)** — Rejected: AGENTS.md §1 explicitly forbids implementing from informal requests. The constitutional requirement for pre-implementation specifications has no enforcement surface in an issue-to-code workflow.
- **Kanban-only planning (cards without artifacts)** — Rejected: kanban boards provide no traceability to numbered requirements, no acceptance criteria surface, and no DoD enforcement. The traceability matrix cannot be populated from kanban state.

## References

- [`AGENTS.md §1 — Metodología obligatoria`](../../AGENTS.md#1-metodología-obligatoria)
- [`AGENTS.md §7 — Convenciones para requisitos`](../../AGENTS.md#7-convenciones-para-requisitos)
- [`AGENTS.md §8 — Convenciones para tareas`](../../AGENTS.md#8-convenciones-para-tareas)
- [`docs/constitution.md` Art. I](../constitution.md#artículo-i--desarrollo-dirigido-por-especificaciones)
- [`openspec/config.yaml`](../../openspec/config.yaml) — SDD bootstrap artifact
- [`.atl/skill-registry.md`](../../.atl/skill-registry.md) — skill dispatch table

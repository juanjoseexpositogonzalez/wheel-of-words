# ADR-0002 — Hexagonal split into domain / application / infrastructure / api

Status: Accepted

Date: 2026-07-15

## Context

AGENTS.md §5 states verbatim: "El backend se divide en: `domain`, `application`, `infrastructure`, `api`." This is not a suggestion — it is the codified architecture rule that every agent and contributor must follow. The same section lists the dependency and responsibility constraints for each layer.

Constitution Art. VII operationalizes the hexagonal split in four binding clauses:
- Art. VII.1: "El dominio no depende de frameworks."
- Art. VII.2: "Los casos de uso residen en aplicación."
- Art. VII.3: "Persistencia, NLP, importación y exportación son adaptadores."
- Art. VII.4: "La API HTTP no contiene reglas de negocio."

At the time this ADR is written, no production code directory (`apps/`) exists yet. The decision precedes implementation and fixes the intent so that the first line of backend code goes into the right layer. Writing code first and sorting layers retroactively is the failure mode this ADR prevents.

A specific structural consequence of the hexagonal model is the NLP adapter port. The `LinguisticAnalyzer` port (named in `docs/architecture/overview.md` §8) lives in the `domain` or `application` layer as a pure interface; spaCy is a `infrastructure` implementation. This means swapping the NLP engine in the future requires only a new adapter, with zero changes to domain logic.

## Decision

The backend MUST use exactly four named layers: `domain`, `application`, `infrastructure`, and `api`.

Dependency direction is strictly one-way inward:
- `infrastructure` and `api` depend on `application`.
- `application` depends on `domain`.
- `domain` depends on nothing outside the Python standard library.

Concretely:
- `domain` has zero imports from FastAPI, SQLAlchemy, spaCy, or any third-party library.
- `application` orchestrates use cases via ports (interfaces); it does not import infrastructure classes directly.
- `infrastructure` implements the ports: SQLAlchemy repositories, spaCy adapter, TXT/EPUB extractors, Anki exporter.
- `api` adapts HTTP (FastAPI routes, Pydantic schemas, error mapping) to application use-case calls; it contains no business rules.

## Consequences

### Positive

- Domain purity enables unit testing without any infrastructure dependency (no database, no NLP model, no network).
- NLP engine and persistence are swappable via their ports without touching domain logic.
- Aligns exactly with Constitution Art. VII.1–4, making the architecture verifiable against the constitution.
- Frontend-backend contract remains at the `api` layer boundary, reinforcing Constitution Art. VII.5 (no duplicated linguistic rules in the frontend).

### Negative

- More boilerplate for simple operations: even a trivial query requires a use case, a port, and a repository.
- The port/adapter boundary requires ongoing discipline to maintain; it is easy to add a shortcut import and break layer isolation silently.

## Alternatives considered

- **Flat module structure** — Rejected: linguistic-domain logic bleeds into infrastructure code, making unit tests infrastructure-dependent. This directly violates Constitution Art. VII.1.
- **Three-layer architecture (domain / service / data, no explicit api layer)** — Rejected: Constitution Art. VII.4 explicitly requires the API layer to be free of business rules. A merged service+api layer cannot satisfy this invariant without the explicit separation.

## References

- [`AGENTS.md §5 — Arquitectura`](../../AGENTS.md#5-arquitectura)
- [`docs/constitution.md` Art. VII](../constitution.md#artículo-vii--arquitectura)
- [`docs/architecture/overview.md §4 — Backend`](../architecture/overview.md#4-backend)
- [`docs/architecture/architecture-baseline.md`](../architecture/architecture-baseline.md) (landing in Slice C)
- [ADR-0001 — Monorepo y stack inicial](0001-monorepo-and-stack.md)

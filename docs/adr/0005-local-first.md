# ADR-0005 — Local-first processing; no third-party data egress by default

Status: Accepted

Date: 2026-07-15

## Context

Constitution Art. IV encodes the privacy and data-handling invariants for this project. Two clauses are directly binding for this decision:

- Art. IV.4: "El procesamiento local será la opción predeterminada."
- Art. IV.5: "El contenido completo de una obra no se enviará a terceros sin consentimiento explícito."

AGENTS.md §4 mirrors these constraints in operational terms:

> "El texto del libro no debe enviarse a terceros sin consentimiento explícito."
> "El procesamiento local será la opción predeterminada."

These are not UX preferences — they are architectural constraints with legal and ethical weight. The user imports books that may be copyrighted works provided under their personal-use license. Sending the full text to a cloud NLP service without consent could constitute a contract violation, a copyright infringement, or a privacy breach depending on jurisdiction and the terms of the original work.

The implication for architecture is direct: the NLP adapter (`LinguisticAnalyzer` port, named in `docs/architecture/overview.md §8`) MUST have a local-running default implementation. spaCy, the first NLP adapter selected in ADR-0001, runs locally. Translation APIs and cloud NLP services (e.g., OpenAI, Google Cloud NLP) are third parties; they cannot receive book content without an explicit user consent gate.

## Decision

All NLP processing MUST run on the user's machine by default. The local-first invariant is not a configuration option; it is the default that cannot be silently overridden by a configuration flag.

Sending book content to any third party — including cloud NLP services, translation APIs, or analytics endpoints — MUST require explicit user consent surfaced in the UI before the first byte of content is transmitted. This constraint applies to all NLP backends, all export paths, and all integration points. It is grounded in Constitution Art. IV.5.

The architecture baseline MUST name local-first processing as a committed invariant. Any future ADR that proposes a cloud-NLP integration MUST reference this ADR, propose a consent gate design, and demonstrate that the default remains local.

## Consequences

### Positive

- Privacy by default: the user's literary data stays on their machine without any action required.
- No network dependency for core NLP functionality; the application works fully offline.
- Full alignment with Constitution Art. IV.4–5 and AGENTS.md §4 constraints.
- Eliminates a class of legal risk (copyright egress without consent) at the architectural level.

### Negative

- Heavy NLP models (spaCy language models) must be bundled, downloaded on first use, or managed by the user; this adds installation friction.
- Cloud offload for computationally expensive operations (e.g., large EPUB files) is not available without first implementing and surfacing a consent UX gate.

## Alternatives considered

- **Cloud-first NLP by default** — Rejected: directly violates Constitution Art. IV.4–5. The constitution frames local processing as the default, not an option. An ADR cannot override the constitution.
- **Opt-in local mode (cloud by default, user switches to local)** — Rejected: this inverts the consent model mandated by the constitution. Art. IV.4 says local is the *default*. Requiring the user to explicitly opt into privacy is not compliant with the constitutional intent.

## References

- [`docs/constitution.md` Art. IV.4–5](../constitution.md#artículo-iv--legalidad-privacidad-y-derechos-de-autor)
- [`AGENTS.md §4 — Restricciones del dominio`](../../AGENTS.md#4-restricciones-del-dominio)
- [`docs/architecture/overview.md §8 — Adaptadores`](../architecture/overview.md#8-adaptadores)
- [`docs/architecture/architecture-baseline.md`](../architecture/architecture-baseline.md) (landing in Slice C)
- [ADR-0001 — Monorepo y stack inicial](0001-monorepo-and-stack.md) — spaCy selected as first local NLP adapter

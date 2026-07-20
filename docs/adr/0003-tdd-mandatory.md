# ADR-0003 — TDD mandatory with strict RED → GREEN → REFACTOR

Status: Accepted

Date: 2026-07-15

## Context

AGENTS.md §3 defines the TDD cycle in binding terms across three phases:

> **RED**: "La prueba debe expresar un único comportamiento relevante. La prueba debe fallar antes de implementar. El fallo debe ser comprensible y estar relacionado con la ausencia del comportamiento. No se acepta una prueba que falle por errores de sintaxis, configuración o fixtures defectuosas."
>
> **GREEN**: "Implementar la solución mínima correcta. No anticipar funcionalidades futuras. No introducir abstracciones sin uso real."
>
> **REFACTOR**: "Eliminar duplicación. Mejorar nombres. Reducir acoplamiento. Mantener interfaces coherentes. Preservar todos los comportamientos y pruebas en verde."

Constitution Art. II reinforces this at the constitutional level:
- Art. II.1: "Cada comportamiento nuevo debe comenzar con una prueba que falle."
- Art. II.2: "La prueba debe fallar por la ausencia del comportamiento."
- Art. II.3: "La implementación inicial será la mínima suficiente."
- Art. II.4: "La refactorización se realiza con la suite relevante en verde."
- Art. II.5: "Todo defecto corregido incorpora una prueba de regresión."

Constitution Art. II also sets quantitative coverage targets: domain and application layers ≥ 90%; global coverage ≥ 80%. These are signals, not substitutes for meaningful tests (Art. II.6).

AGENTS.md §2 states the mandatory work order: identify the requirement → write or update the test → run it (expect failure) → confirm it fails for the expected reason → implement the minimum solution → run the affected test → run the related suite → refactor → run all quality controls → update documentation and traceability.

No implementation may precede a failing test. This is not a recommendation; it is a constitutional constraint.

## Decision

Every new behavior introduced to the codebase MUST begin with a RED test that expresses exactly that behavior and fails because the behavior is absent.

The minimum sufficient implementation is written to turn the RED test GREEN. No additional abstraction, no anticipatory scaffolding, no feature branching inside the implementation.

Refactoring is permitted only when the full relevant test suite is green. Refactoring that breaks a passing test is a regression, not a refactor.

Every bug fix MUST add a regression test that reproduces the defect before the fix is applied. Fixing without a regression test is forbidden.

Coverage targets (domain/application ≥ 90%, global ≥ 80%) are enforced in CI as a quality gate, but they do not substitute for behavior-specific tests. A 100% covered codebase with vacuous tests is non-compliant.

## Consequences

### Positive

- Domain invariants are continuously validated; the test suite is the living specification of behavior.
- Regression safety: every bug that gets fixed cannot silently reappear.
- Forces clarity about expected behavior before any implementation decision is made.
- Aligns with `openspec/config.yaml` `strict_tdd: true` flag, enabling agent sessions to verify TDD compliance programmatically.

### Negative

- Higher upfront effort per feature: writing a meaningful failing test requires understanding the requirement fully before touching production code.
- Test infrastructure (fixtures, factories, in-memory repositories) must be maintained alongside domain code; this is a non-trivial overhead.

## Alternatives considered

- **Test-after approach** — Rejected: Constitution Art. II.1 explicitly forbids writing implementation before tests. An ADR cannot override the constitution; it can only record why this choice is right.
- **Property-based testing only (Hypothesis)** — Rejected: property tests complement behavior-specific unit tests but do not replace them. AGENTS.md §6 lists property-based testing as one of several test types, not the sole method. Behavioral specificity is required to detect and express domain invariants that cannot be easily captured as mathematical properties.

## References

- [`AGENTS.md §2 — Orden obligatorio de trabajo`](../../AGENTS.md#2-orden-obligatorio-de-trabajo)
- [`AGENTS.md §3 — Ciclo TDD`](../../AGENTS.md#3-ciclo-tdd)
- [`AGENTS.md §6 — Pruebas`](../../AGENTS.md#6-pruebas)
- [`docs/constitution.md` Art. II](../constitution.md#artículo-ii--desarrollo-dirigido-por-pruebas)
- [`openspec/config.yaml`](../../openspec/config.yaml) — `strict_tdd: true`
- [`docs/architecture/architecture-baseline.md`](../architecture/architecture-baseline.md) (landing in Slice C)

# ADR index — wheel-of-words

Architecture Decision Records document the binding decisions that shape this repository. Each ADR records the context that forced a choice, the decision taken, its consequences, and the alternatives rejected. ADRs are grounded in the project constitution (`docs/constitution.md`) and AGENTS.md; together they form the permanent decision record that specs and design docs must not contradict.

---

## Status vocabulary

| Status | Meaning |
|--------|---------|
| `Proposed` | Under consideration; not yet binding. Superseded by `Accepted` once the decision is ratified. |
| `Accepted` | Decision is in force. All subsequent work must conform. |
| `Superseded` | Replaced by a later ADR (link to successor required in the ADR body). |
| `Deprecated` | No longer applicable; reason for deprecation required in the ADR body. |

---

## Numbering convention

ADRs are numbered globally and sequentially. Numbers are zero-padded to four digits: `ADR-0001`, `ADR-0002`, etc. There are no per-capability or per-domain prefixes. Filename convention: `<NNNN>-<kebab-title>.md` (e.g., `0003-tdd-mandatory.md`). The authoring skeleton (prefixed with an underscore) is **not** assigned a number and does not appear in the index below.

---

## Authoring rules

1. **Ground the Context** in a specific clause or verbatim quote from a binding artifact (constitution Art. X.Y, AGENTS.md §N, or a named spec). Do not write Context from memory alone.
2. **Decision must be actionable.** Write it as an active-voice statement ("We adopt X") or a declarative commitment ("X is the chosen approach"). Descriptions are not decisions.
3. **Status must be set at creation.** Promote it via a diff if it changes; do not leave the field blank.
4. **Date must reflect when the decision was effectively made**, not when the file was created. Historical accuracy takes precedence.
5. **Consequences must enumerate both positives and negatives.** An ADR with only positives is incomplete.
6. **One ADR per discrete decision.** If decisions are co-dependent, write sibling ADRs and link them.
7. **Language: EN** (methodology artifact per ADR-0010).

---

## Index

| ADR | Title | Status | Date | Wave |
|-----|-------|--------|------|------|
| [ADR-0001](0001-monorepo-and-stack.md) | Monorepositorio y stack inicial | Accepted | 2026-07-15 | — |
| [ADR-0002](0002-hexagonal-split.md) | Hexagonal split into domain / application / infrastructure / api | Accepted | 2026-07-15 | 1 |
| [ADR-0003](0003-tdd-mandatory.md) | TDD mandatory with strict RED → GREEN → REFACTOR | Accepted | 2026-07-15 | 1 |
| [ADR-0004](0004-sdd-openspec.md) | SDD + OpenSpec as the planning method for all features | Accepted | 2026-07-15 | 1 |
| [ADR-0005](0005-local-first.md) | Local-first processing; no third-party data egress by default | Accepted | 2026-07-15 | 1 |
| [ADR-0006](0006-pos-per-occurrence.md) | POS assigned per occurrence; no single global POS per lemma | Accepted | 2026-07-15 | 1 |
| [ADR-0007](0007-manual-corrections-precedence.md) | Manual corrections take precedence and survive reprocessing | Accepted | 2026-07-16 | 2 |
| [ADR-0008](0008-multi-language-scope.md) | Multi-language scope from day one | Accepted | 2026-07-16 | 2 |
| [ADR-0009](0009-mwe-language-specific-instances.md) | Multiword expressions as language-specific instances | Accepted | 2026-07-16 | 2 |
| [ADR-0010](0010-documentation-language-policy.md) | Documentation language policy: methodology EN, product-facing ES | Accepted | 2026-07-16 | 2 |

---

## Cross-references

- Constitution: [`docs/constitution.md`](../constitution.md)
- Architecture baseline (committed-state snapshot, landing in Slice C): [`docs/architecture/architecture-baseline.md`](../architecture/architecture-baseline.md)
- Decisions log: [`docs/decisions-log.md`](../decisions-log.md)

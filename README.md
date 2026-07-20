<p align="center">
  <img src="docs/assets/banner.svg" alt="Wheel of Words — Turn the books you read into the words you learn." width="100%" />
</p>

<p align="center">
  <em>Turn the books you read into the words you learn.</em>
</p>

<p align="center">
  <img alt="Status" src="https://img.shields.io/badge/status-pre--alpha-8a7a55?style=flat-square" />
  <img alt="Methodology" src="https://img.shields.io/badge/methodology-SDD%20%2B%20TDD-b98a3b?style=flat-square" />
  <img alt="Architecture" src="https://img.shields.io/badge/architecture-domain--driven-b98a3b?style=flat-square" />
  <img alt="Deployment" src="https://img.shields.io/badge/deployment-local--first-b98a3b?style=flat-square" />
  <img alt="License" src="https://img.shields.io/badge/license-TBD-8a7a55?style=flat-square" />
</p>

---

## Overview

**Wheel of Words** is a local-first web application that turns a book you own into a corpus of vocabulary you can study.

It extracts words, groups inflected forms under a lemma, records the part of speech in context, distinguishes proper nouns and multi-word expressions (phrasal verbs, idioms, separable verbs), lets you review and correct the automatic output, and exports the words you want to keep as spaced-repetition cards (Anki).

The project is built under a strict methodology stack — Specification-Driven Development, Test-Driven Development, domain-driven architecture, and small vertical slices — because vocabulary tooling that ships wrong linguistics is worse than no tool at all.

> **Naming note.** The canonical project name in the current [Constitution](docs/constitution.md) is *Wheel Vocabulary* and is explicitly declared provisional in the [Product Vision](docs/product-vision.md). *Wheel of Words* is the working public name adopted for the repository and README. A formal rename, if ratified, will go through a constitutional amendment cycle.

## Status

This repository does **not** yet contain application code. It contains the full methodological and specification foundation the code will be built on.

| Layer | Status |
|-------|--------|
| Constitution (v2.0.0) | Ratified |
| Product vision | Approved |
| Architecture baseline | Approved |
| SDD / OpenSpec bootstrap | Complete |
| ADRs 0001–0006 | Ratified |
| Glossary, DoD, traceability matrix | Live |
| First vertical slice (`SPEC-002` — import a `.txt` and see a frequency list) | Not started |
| Backend / frontend code | Not started |

The next planned work is `SPEC-002`: import a `.txt` file and show an alphabetical list of unique words with their frequency. That will be the first vertical slice with visible user value.

## Non-negotiable principles

These are enforced by the [Constitution](docs/constitution.md). Any feature that contradicts them requires an explicit amendment; it cannot be silently overridden.

- **No copyrighted books ship with this repository.** Test fixtures use synthetic, self-authored, or public-domain text only. Any book you analyze must be one you legally own.
- **Local-first processing by default.** Book text is not sent to third parties without explicit user consent.
- **Linguistic form is not identity.** The surface form, the normalized form, the lemma, and the part of speech in context are stored separately. Lemmas do not carry a single global part of speech.
- **Manual corrections beat automatic output.** Reprocessing never silently overwrites a human correction. Automatic results carry provenance and a confidence signal.
- **Multi-word expressions are first-class.** Phrasal verbs, idioms, and separable verbs are modeled distinctly from single-word lemmas — never flattened into them.
- **Linguistic rules live on the server.** The frontend consumes API contracts; it does not re-implement domain logic.

## Methodology at a glance

```text
Constitution
     ↓
Specification  ────►  Acceptance criteria
     ↓                        ↓
Technical plan  ────►  Test plan
     ↓                        ↓
Tasks  ─────────────►  RED → GREEN → REFACTOR
                              ↓
                    Validation  ·  Traceability
```

No behavior is written without a failing test first. No specification changes silently: contradictions are recorded, resolved, and the requirement / acceptance / test / task chain is updated in lockstep. The [Definition of Done](docs/definition-of-done.md) is the gate before any task is closed.

## Architecture at a glance

The backend is layered and dependency-inverted:

```text
domain           ← pure linguistic model, no framework imports
application      ← use cases, ports/interfaces
infrastructure   ← persistence, NLP (spaCy/Stanza), importers, exporters (Anki)
api              ← HTTP adapter (FastAPI)
```

The frontend consumes API contracts and stays out of the domain. Side effects live at the edges. Full details in the [Architecture Baseline](docs/architecture/architecture-baseline.md).

## Repository layout

```text
.
├── AGENTS.md                          # Mandatory instructions for agents and collaborators
├── README.md                          # You are here
├── docs/
│   ├── constitution.md                # Non-negotiable rules (v2.0.0)
│   ├── product-vision.md              # Problem, users, scope, non-goals
│   ├── definition-of-done.md          # Gate before closing any task
│   ├── traceability-matrix.md         # REQ ↔ AC ↔ Test ↔ Task
│   ├── decisions-log.md               # Chronological decision record
│   ├── glossary.md                    # Domain terminology
│   ├── architecture/
│   │   ├── overview.md
│   │   └── architecture-baseline.md
│   ├── adr/                           # Architecture Decision Records (0001–0006)
│   └── assets/
│       └── banner.svg
├── openspec/
│   ├── config.yaml
│   └── changes/                       # SDD change cycles (proposal → spec → design → tasks → apply → verify → archive)
├── specs/
│   └── 001-project-foundation/        # SPEC-001 — project foundation (pre-SDD baseline)
└── templates/
    └── feature-spec-template.md       # Reusable specification skeleton
```

## Contributing

Before touching this project, read — in this order:

1. [AGENTS.md](AGENTS.md) — mandatory development protocol.
2. [docs/constitution.md](docs/constitution.md) — the rules you cannot bend.
3. [docs/product-vision.md](docs/product-vision.md) — what we are building and for whom.
4. [docs/architecture/architecture-baseline.md](docs/architecture/architecture-baseline.md) — how the code is organized.
5. [docs/definition-of-done.md](docs/definition-of-done.md) — when a task is actually finished.

Then pick a specification, write a failing test, and go from there.

## References

- [Constitution](docs/constitution.md) — canonical source in case of conflict.
- [Product Vision](docs/product-vision.md)
- [ADR index](docs/adr/README.md)
- [Architecture Baseline](docs/architecture/architecture-baseline.md)
- [Glossary](docs/glossary.md)
- [Definition of Done](docs/definition-of-done.md)
- [Traceability Matrix](docs/traceability-matrix.md)
- [Decisions Log](docs/decisions-log.md)

## License

License to be defined before the first public release. Until then, all rights reserved by the authors. This repository does not distribute any third-party copyrighted content; test fixtures are synthetic, self-authored, or public-domain.

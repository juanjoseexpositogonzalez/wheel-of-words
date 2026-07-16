# Traceability Matrix — wheel-of-words

## Purpose

This file provides a cross-spec view of requirements, acceptance criteria, test
files, tasks, and status across the entire repository. It complements the
per-spec `traceability.md` files (which remain the source of truth for
feature-scoped rows). This top-level matrix helps agents and reviewers navigate
the full requirement landscape without opening every spec directory.

---

## Column schema

| Column | Type | Description |
|--------|------|-------------|
| REQ ID | string | `REQ-<feature>-<n>` identifier — matches the format in each spec |
| Statement (short) | string | One-line summary of the requirement |
| Acceptance criterion ref | string | AC-ID reference or path to spec acceptance section |
| Test file(s) | string | Path(s) to test file(s) or test-plan IDs |
| Task(s) | string | T-ID reference(s) from the corresponding tasks file |
| Status | enum | `Pendiente` · `En progreso` · `Cumplido` · `Bloqueado` |

---

## Matrix

| REQ ID | Statement (short) | Acceptance criterion ref | Test file(s) | Task(s) | Status |
|--------|--------------------|--------------------------|--------------|---------|--------|
| REQ-001-001 | Backend FastAPI arrancable mediante un comando documentado | `specs/001-project-foundation/acceptance.md#AC-001` | `specs/001-project-foundation/test-plan.md` (API-BE-001) | T014–T016 | Pendiente |
| REQ-001-002 | `GET /api/v1/health` devuelve `{"status":"ok","service":"wheel-vocabulary-api","version":"0.1.0"}` | `specs/001-project-foundation/acceptance.md#AC-001` | `specs/001-project-foundation/test-plan.md` (UT-BE-003, API-BE-001) | T012–T016 | Pendiente |
| REQ-001-007 | El dominio no contiene imports de frameworks; arquitectura hexagonal validable | `specs/001-project-foundation/acceptance.md#AC-007` | `specs/001-project-foundation/test-plan.md` (UT-BE-001, UT-BE-002) | T004–T010 | Pendiente |
| REQ-DOCS-010 | `docs/adr/README.md` con índice, vocabulario de estado, convención de numeración y reglas de autoría | `openspec/changes/docs-methodology-overhaul/spec.md#AC-010` | N/A — inspección | TB01 | Cumplido |
| REQ-DOCS-030 | `docs/glossary.md` en español con todos los términos canónicos del dominio lingüístico (≥ 13 entradas) | `openspec/changes/docs-methodology-overhaul/spec.md#AC-030` | N/A — inspección | TC07, TC08 | Cumplido |
| REQ-DOCS-060 | Preámbulo de la constitución generalizado: eliminar "inglés" como único ámbito; framing multi-idioma | `openspec/changes/docs-methodology-overhaul/spec.md#AC-060` | N/A — inspección | TE02 | Cumplido |
| REQ-DOCS-062 | Constitución bumpeada a v2.0.0 (MAJOR) con sección de registro de enmiendas | `openspec/changes/docs-methodology-overhaul/spec.md#AC-062` | N/A — inspección | TE01, TE03 | Cumplido |
| REQ-DOCS-06C | `README.md` línea 3 generalizada: eliminar "en inglés" como calificador de ámbito | `openspec/changes/docs-methodology-overhaul/spec.md#AC-066` | N/A — inspección | TE08 | Cumplido |
| REQ-DOCS-066 | `docs/product-vision.md` §4 usuario generalizado: "en el idioma que estudia" | `openspec/changes/docs-methodology-overhaul/spec.md#AC-067` | N/A — inspección | TE04 | Cumplido |
| REQ-DOCS-06A | `AGENTS.md` §4 cláusula MWE generalizada con wording OQ-10 canónico | `openspec/changes/docs-methodology-overhaul/spec.md#AC-071` | N/A — inspección | TE09 | Cumplido |
| REQ-DOCS-06B | Invariante de coordinación: los cuatro archivos de enmienda aterrizan atómicamente en un único commit | `openspec/changes/docs-methodology-overhaul/spec.md#AC-072` | N/A — git log | TE01..TE13 | Cumplido |
| REQ-DOCS-043 | `AGENTS.md` §10 puerta DoD de trazabilidad añadida | `openspec/changes/docs-methodology-overhaul/spec.md#AC-043` | N/A — inspección | TE10 | Cumplido |

---

## Update rules

### Reglas de actualización

1. **Añadir fila** cuando se introduce un nuevo `REQ-<feature>-<n>` en cualquier
   spec o change. La fila debe incluir todos los campos; Status inicial = `Pendiente`.

2. **Actualizar Estado** cuando la aceptación del requisito se demuestra:
   cambia de `Pendiente` / `En progreso` a `Cumplido`. El agente o desarrollador
   que cierra la tarea referenciada es responsable de la actualización.

3. **Nunca eliminar filas.** Cuando un requisito queda obsoleto o es
   reemplazado, marcar `Bloqueado` o añadir una nota en la columna Statement
   con la referencia al requisito sucesor. El estado histórico se preserva.

4. **`Bloqueado` requiere razón:** la columna Statement (o una nota en la misma
   fila) debe indicar qué bloquea el requisito y quién debe desbloquearlo.

5. **Responsabilidad de fila:** la persona o agente que cierra la tarea
   referenciada en Task(s) actualiza el Estado en esta matriz. Los ficheros
   `traceability.md` por spec siguen siendo la fuente de verdad para las filas
   de su feature; esta matriz agrega filas de alcance cruzado o landmark.

---

## Notes

Additional rows will be added as new REQ-* IDs land. The four amendment REQs
(Family F, Slice E) will appear as `Pendiente` here until Slice E lands, then
flip to `Cumplido`. The Slice A + C divergences flagged for verify are
separately tracked in Engram observation #2271.

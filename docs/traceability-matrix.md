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
| REQ-001-001 | Backend FastAPI arrancable mediante un comando documentado | `specs/001-project-foundation/acceptance.md#AC-001` | `apps/api/tests/api/test_health.py` | TA10, TB110–TB111 | Cumplido |
| REQ-001-002 | `GET /api/v1/health` devuelve el contrato documentado | `specs/001-project-foundation/acceptance.md#AC-001` | `apps/api/tests/api/test_health.py` | TB107–TB111 | Cumplido |
| REQ-001-003 | Frontend React + TypeScript arrancable mediante un comando documentado | `specs/001-project-foundation/acceptance.md#AC-002` | `apps/web/e2e/status.spec.ts` | TA06–TA10, TC11 | Cumplido |
| REQ-001-004 | Frontend muestra carga, disponible, no disponible y reintento | `specs/001-project-foundation/acceptance.md#AC-003,AC-004` | `apps/web/tests/components/StatusPage.test.tsx` | TC03–TC11 | Cumplido |
| REQ-001-005 | Backend conecta SQLite mediante URL configurable | `specs/001-project-foundation/acceptance.md#AC-005` | `apps/api/tests/integration/test_engine.py` | TB201–TB202 | Cumplido |
| REQ-001-006 | Alembic configurado con migración inicial verificable | `specs/001-project-foundation/acceptance.md#AC-006` | `apps/api/tests/integration/test_alembic.py` | TB205–TB207 | Cumplido |
| REQ-001-007 | Configuración por entorno con valores de ejemplo seguros | `specs/001-project-foundation/acceptance.md#AC-007` | `apps/api/tests/unit/test_settings.py` | TA11, TB101–TB102 | Cumplido |
| REQ-001-008 | Superficie de comandos unificada para instalar, desarrollar, probar y migrar | `specs/001-project-foundation/acceptance.md#AC-008` | `apps/api/tests/unit/test_traceability.py` | TA10, TD06 | Cumplido |
| REQ-001-009 | Suite con pruebas backend unitarias, API y SQLite | `specs/001-project-foundation/acceptance.md#AC-009` | `apps/api/tests/{unit,api,integration}/` | TB101–TB112, TB201–TB208 | Cumplido |
| REQ-001-010 | Pruebas frontend cubren carga, disponible, no disponible y reintento | `specs/001-project-foundation/acceptance.md#AC-010` | `apps/web/tests/components/StatusPage.test.tsx` | TC03–TC10 | Cumplido |
| REQ-001-011 | Playwright valida el estado integrado de salud | `specs/001-project-foundation/acceptance.md#AC-011` | `apps/web/e2e/status.spec.ts` | TD01–TD02 | Cumplido |
| REQ-001-012 | Backend pasa Ruff y mypy con configuración acordada | `specs/001-project-foundation/acceptance.md#AC-012` | `.github/workflows/ci.yml` | TA02, TD03, TD09 | Cumplido |
| REQ-001-013 | Frontend pasa TypeScript estricto y ESLint | `specs/001-project-foundation/acceptance.md#AC-012` | `.github/workflows/ci.yml` | TA06–TA08, TD03, TD09 | Cumplido |
| REQ-001-014 | GitHub Actions ejecuta instalación, calidad, pruebas, E2E y migraciones | `specs/001-project-foundation/acceptance.md#AC-012` | `apps/api/tests/unit/test_ci_workflow.py` | TD03, TD09 | Cumplido |
| REQ-001-015 | Capas backend hexagonales con fronteras de framework | `docs/adr/0002-hexagonal-split.md#decision` | inspección estructural de `apps/api/src/wheel_vocabulary/{domain,application,infrastructure,api}/` | TA04, TD04–TD05 | Cumplido |
| REQ-001-016 | README explica requisitos, instalación, arranque, pruebas, calidad, migraciones y estructura | `specs/001-project-foundation/acceptance.md#AC-015` | `apps/api/tests/unit/test_traceability.py` | TD06 | Cumplido |
| REQ-001-017 | El repositorio no incluye texto de libros protegido | `specs/001-project-foundation/acceptance.md#AC-013` | inspección de contenido versionado | TA12, TD09 | Cumplido |
| REQ-001-018 | Entornos, bases locales, importaciones, cobertura, cachés y secretos están ignorados | `specs/001-project-foundation/acceptance.md#AC-007` | `.gitignore` | TA12 | Cumplido |
| REQ-CI-001 | Backend CI jobs install locked development tooling independently | `openspec/changes/fix-pr5-ci-tooling/specs/001-project-foundation/spec.md#AC-CI-001` | `apps/api/tests/unit/test_ci_workflow.py` | TC01, TC03, TC05–TC06 | En progreso |
| REQ-CI-002 | Frontend CI uses the repository-root lockfile and frozen installs | `openspec/changes/fix-pr5-ci-tooling/specs/001-project-foundation/spec.md#AC-CI-002` | `apps/api/tests/unit/test_ci_workflow.py` | TC02, TC04–TC06 | En progreso |
| REQ-CI-003 | E2E CI prepares locked backend and frontend dependencies | `openspec/changes/fix-pr5-ci-tooling/specs/001-project-foundation/spec.md#AC-CI-003` | `apps/api/tests/unit/test_ci_workflow.py` | TC01, TC03, TC05–TC06 | En progreso |
| REQ-CI-004 | CI repair does not mask unrelated functional E2E failures | `openspec/changes/fix-pr5-ci-tooling/specs/001-project-foundation/spec.md#AC-CI-004` | `apps/api/tests/unit/test_ci_workflow.py`, `apps/web/e2e/status.spec.ts` | TC02, TC04, TC06 | En progreso |
| REQ-DOCS-004 | Skill registry lists all SDD phase skills | `openspec/changes/docs-methodology-overhaul/spec.md#AC-004` | N/A — inspección | TA02 | Cumplido |
| REQ-DOCS-010 | `docs/adr/README.md` con índice, vocabulario de estado, convención de numeración y reglas de autoría | `openspec/changes/docs-methodology-overhaul/spec.md#AC-010` | N/A — inspección | TB01 | Cumplido |
| REQ-DOCS-030 | `docs/glossary.md` en español con todos los términos canónicos del dominio lingüístico (≥ 13 entradas) | `openspec/changes/docs-methodology-overhaul/spec.md#AC-030` | N/A — inspección | TC07, TC08 | Cumplido |
| REQ-DOCS-060 | Preámbulo de la constitución generalizado: eliminar "inglés" como único ámbito; framing multi-idioma | `openspec/changes/docs-methodology-overhaul/spec.md#AC-060` | N/A — inspección | TE02 | Cumplido |
| REQ-DOCS-062 | Constitución bumpeada a v2.0.0 (MAJOR) con sección de registro de enmiendas | `openspec/changes/docs-methodology-overhaul/spec.md#AC-062` | N/A — inspección | TE01, TE03 | Cumplido |
| REQ-DOCS-06C | `README.md` línea 3 generalizada: eliminar "en inglés" como calificador de ámbito | `openspec/changes/docs-methodology-overhaul/spec.md#AC-066` | N/A — inspección | TE08 | Cumplido |
| REQ-DOCS-066 | `docs/product-vision.md` §4 usuario generalizado: "en el idioma que estudia" | `openspec/changes/docs-methodology-overhaul/spec.md#AC-067` | N/A — inspección | TE04 | Cumplido |
| REQ-DOCS-06A | `AGENTS.md` §4 cláusula MWE generalizada con wording OQ-10 canónico | `openspec/changes/docs-methodology-overhaul/spec.md#AC-071` | N/A — inspección | TE09 | Cumplido |
| REQ-DOCS-06B | Invariante de coordinación: los cuatro archivos de enmienda aterrizan atómicamente en un único commit | `openspec/changes/docs-methodology-overhaul/spec.md#AC-072` | N/A — git log | TE01..TE13 | Cumplido |
| REQ-DOCS-043 | `AGENTS.md` §10 puerta DoD de trazabilidad añadida | `openspec/changes/docs-methodology-overhaul/spec.md#AC-043` | N/A — inspección | TE10 | Cumplido |
| REQ-TESTHYG-001 | Las pruebas de integración liberan cada motor SQLAlchemy que abren; la suite no emite `ResourceWarning` | issue #14 — criterios de aceptación | `apps/api/tests/integration/conftest.py`, `apps/api/tests/integration/{test_alembic,test_base,test_engine}.py`, filtro en `apps/api/pyproject.toml` | TH01–TH03 | Cumplido |


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

La familia `REQ-TESTHYG-*` cubre higiene de la suite de pruebas (fugas de
recursos y avisos de obsolescencia de dependencias). Deliberadamente no usa el
rango `REQ-001-*`: `apps/api/tests/unit/test_traceability.py` exige exactamente
una fila por cada `REQ-001-001`…`REQ-001-018`, así que ampliar ese rango
rompería esa comprobación.

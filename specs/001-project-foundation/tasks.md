# SPEC-001 — Tareas

## Fase A — Repositorio

- [ ] T001 [SPEC] Aprobar SPEC-001.
- [ ] T002 [DOC] Crear README inicial.
- [ ] T003 [IMPL] Crear monorepositorio.
- [ ] T004 [IMPL] Añadir `.gitignore`.
- [ ] T005 [IMPL] Añadir `.env.example`.
- [ ] T006 [IMPL] Crear Makefile.
- [ ] T007 [SECURITY] Verificar exclusión de datos, libros, bases y secretos.

## Fase B — Backend TDD

- [ ] T008 [TEST] Prueba de configuración válida.
- [ ] T009 [IMPL] Configurar Python con `uv`.
- [ ] T010 [IMPL] Implementar `Settings`.
- [ ] T011 [REFACTOR] Centralizar nombres y versión.
- [ ] T012 [TEST] Prueba de `HealthResponse`.
- [ ] T013 [IMPL] Implementar `HealthResponse`.
- [ ] T014 [TEST] Prueba roja de `GET /api/v1/health`.
- [ ] T015 [IMPL] Implementar factory y ruta.
- [ ] T016 [REFACTOR] Separar router y factory.
- [ ] T017 [TEST] Prueba de SQLite temporal.
- [ ] T018 [IMPL] Configurar SQLAlchemy.
- [ ] T019 [REFACTOR] Extraer factories de engine y sesión.
- [ ] T020 [TEST] Prueba de migración desde base vacía.
- [ ] T021 [MIGRATION] Configurar Alembic.
- [ ] T022 [MIGRATION] Crear migración inicial.
- [ ] T023 [TEST] Añadir downgrade si procede.
- [ ] T024 [IMPL] Crear capas del backend.
- [ ] T025 [DOC] Documentar límites de capas.

## Fase C — Frontend TDD

- [ ] T026 [IMPL] Inicializar React + TypeScript + Vite.
- [ ] T027 [TEST] Prueba del estado loading.
- [ ] T028 [IMPL] Implementar `BackendStatus` mínimo.
- [ ] T029 [TEST] Prueba del estado available.
- [ ] T030 [IMPL] Implementar consulta de salud.
- [ ] T031 [TEST] Prueba del estado unavailable.
- [ ] T032 [IMPL] Implementar manejo de error.
- [ ] T033 [TEST] Prueba de reintento.
- [ ] T034 [IMPL] Implementar reintento.
- [ ] T035 [TEST] Pruebas de accesibilidad.
- [ ] T036 [REFACTOR] Separar cliente HTTP y presentación.

## Fase D — Contrato e integración

- [ ] T037 [TEST] Validación de contrato HealthResponse.
- [ ] T038 [IMPL] Generación o consumo de tipos OpenAPI.
- [ ] T039 [TEST] Prueba integrada frontend-backend.

## Fase E — E2E

- [ ] T040 [E2E] Configurar Playwright.
- [ ] T041 [E2E] Prueba roja del estado integrado.
- [ ] T042 [IMPL] Configurar servidores de Playwright.
- [ ] T043 [E2E] Hacer pasar el flujo.
- [ ] T044 [REFACTOR] Eliminar esperas y estabilizar selectores.

## Fase F — Calidad y CI

- [ ] T045 [IMPL] Configurar Ruff.
- [ ] T046 [IMPL] Configurar mypy.
- [ ] T047 [IMPL] Configurar TypeScript estricto.
- [ ] T048 [IMPL] Configurar linter frontend.
- [ ] T049 [CI] Workflow backend.
- [ ] T050 [CI] Workflow frontend.
- [ ] T051 [CI] Verificación de migraciones.
- [ ] T052 [CI] Workflow E2E.
- [ ] T053 [CI] Configurar cachés.
- [ ] T054 [CI] Artefactos de fallo.

## Fase G — Cierre

- [ ] T055 [DOC] Completar README.
- [ ] T056 [DOC] Documentar migraciones.
- [ ] T057 [TEST] Ejecutar suite completa.
- [ ] T058 [SECURITY] Revisar secretos y contenido protegido.
- [ ] T059 [DOC] Completar trazabilidad.
- [ ] T060 [SPEC] Revisar aceptación.
- [ ] T061 [REFACTOR] Eliminar elementos no utilizados.
- [ ] T062 [DOC] Registrar decisiones finales.

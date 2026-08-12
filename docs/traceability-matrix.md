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
| REQ-CI-001 | Backend CI jobs install locked development tooling independently | `openspec/archive/2026-08-10-fix-pr5-ci-tooling/specs/001-project-foundation/spec.md#AC-CI-001` | `apps/api/tests/unit/test_ci_workflow.py` | TC01, TC03, TC05–TC06 | Cumplido |
| REQ-CI-002 | Frontend CI uses the repository-root lockfile and frozen installs | `openspec/archive/2026-08-10-fix-pr5-ci-tooling/specs/001-project-foundation/spec.md#AC-CI-002` | `apps/api/tests/unit/test_ci_workflow.py` | TC02, TC04–TC06 | Cumplido |
| REQ-CI-003 | E2E CI prepares locked backend and frontend dependencies | `openspec/archive/2026-08-10-fix-pr5-ci-tooling/specs/001-project-foundation/spec.md#AC-CI-003` | `apps/api/tests/unit/test_ci_workflow.py` | TC01, TC03, TC05–TC06 | Cumplido |
| REQ-CI-004 | CI repair does not mask unrelated functional E2E failures | `openspec/archive/2026-08-10-fix-pr5-ci-tooling/specs/001-project-foundation/spec.md#AC-CI-004` | `apps/api/tests/unit/test_ci_workflow.py`, `apps/web/e2e/status.spec.ts` | TC02, TC04, TC06 | Cumplido |
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
| REQ-TESTHYG-002 | El cliente HTTP de pruebas usa el transporte soportado por `starlette.testclient` (`httpx2`); cero `StarletteDeprecationWarning` | issue #15 — criterios de aceptación | `apps/api/tests/api/test_health.py`, `apps/api/tests/api/test_health_security.py` | TH04 | Cumplido |
| REQ-TESTHYG-003 | El filtro `filterwarnings` convierte en error ambas clases de aviso para que no puedan reaparecer en silencio | issues #14 y #15 — criterios de aceptación | `apps/api/pyproject.toml` (`[tool.pytest.ini_options]`) | TH05 | Cumplido |
| REQ-002-005 | Tokenización y `normalize()` puras y genéricas de idioma, sin frameworks ni literales ISO-639 en `domain/` | `openspec/changes/text-import/specs/002-text-import/spec.md` — AC-002-06, AC-002-07 | `apps/api/tests/unit/test_tokenizer.py`, `apps/api/tests/unit/test_normalizer.py`, `apps/api/tests/unit/test_domain_isolation.py` | T1A01–T1A03, T1A04–T1A06, T1A10 | Cumplido |
| REQ-002-015 | `normalize` es idempotente: `normalize(normalize(x))` equivale a `normalize(x)` | `openspec/changes/text-import/specs/002-text-import/spec.md` — AC-002-20 | `apps/api/tests/unit/test_normalizer.py::test_normalize_is_idempotent` | T1A04–T1A06 | Cumplido |
| REQ-002-016 | El conjunto de formas normalizadas, sus frecuencias y sus formas de visualización no dependen del orden de entrada | `openspec/changes/text-import/specs/002-text-import/spec.md` — AC-002-21 | `apps/api/tests/unit/test_frequency.py::test_aggregation_is_order_independent_hypothesis` | T1A07–T1A09 | Cumplido |
| REQ-002-017 | Las frecuencias nunca son negativas: toda fila listada tiene un entero `>= 1` | `openspec/changes/text-import/specs/002-text-import/spec.md` — AC-002-22 | `apps/api/tests/unit/test_frequency.py::test_frequencies_are_never_negative_hypothesis` | T1A07–T1A09 | Cumplido |
| REQ-002-006 | Agregación por forma normalizada con frecuencia y orden (§2.4) | `openspec/changes/text-import/specs/002-text-import/spec.md` — AC-002-08, AC-002-09 | `apps/api/tests/unit/test_frequency.py::test_repeated_forms_collapse_with_frequency_and_sum`, `apps/api/tests/api/test_imports.py::test_rows_arrive_already_ordered_by_the_grouping_key`, `apps/api/tests/api/test_imports.py::test_get_imports_returns_the_ordered_table_with_the_persisted_id`, `::test_get_imports_diacritic_insensitive_order` | T1A07–T1A09 (leg de dominio); T1B13–T1B16 (leg de respuesta `POST`); T211–T212 (leg de lectura `GET`) | Cumplido — cerrado en el corte 2: la ruta `GET /api/v1/imports/{id}` reutiliza `domain.frequency.build_table()`, la misma implementación que la ruta de importación (spec §1.2, requisito transversal) |
| REQ-002-018 | Cada grupo muestra una forma de superficie real, elegida de forma determinista (D1–D3) | `openspec/changes/text-import/specs/002-text-import/spec.md` — AC-002-23, AC-002-24 | `apps/api/tests/unit/test_frequency.py::test_majority_and_tie_break_display_form`, `apps/api/tests/api/test_imports.py::test_each_row_carries_both_the_grouping_key_and_the_display_form`, `::test_get_imports_returns_the_ordered_table_with_the_persisted_id` | T1A07–T1A09 (leg de dominio); T1B15–T1B16 (`display_form` en la respuesta `POST`); T202 (sin columna nueva), T211–T212 (leg de lectura `GET`) | Cumplido — cerrado en el corte 2: `0002_book_occurrence` no añade columna para `display_form` (AC-002-24); se deriva por agregación sobre `Occurrence.raw_text`, ya persistido por REQ-002-010 |
| REQ-002-001 | La importación solo acepta subida multiparte de un `.txt`; se rechaza ruta de sistema de archivos, URL o texto en línea | `openspec/changes/text-import/specs/002-text-import/spec.md` — AC-002-01 | `apps/api/tests/api/test_imports.py`, `apps/api/tests/api/test_imports_cors.py` | T1B15–T1B17 | Cumplido |
| REQ-002-002 | Validación de extensión y tipo de contenido antes de decodificar o tokenizar un solo byte | `openspec/changes/text-import/specs/002-text-import/spec.md` — AC-002-02 | `apps/api/tests/unit/test_import_text.py`, `apps/api/tests/api/test_imports.py` | T1B10, T1B13–T1B14 | Cumplido |
| REQ-002-003 | Límite de tamaño configurable (`MAX_IMPORT_SIZE_BYTES`, 4 MiB por defecto) aplicado durante la lectura | `openspec/changes/text-import/specs/002-text-import/spec.md` — AC-002-03, AC-002-04 | `apps/api/tests/unit/test_settings.py`, `apps/api/tests/unit/test_import_text.py`, `apps/api/tests/api/test_imports.py` | T1B01–T1B02, T1B11, T1B13–T1B14 | Cumplido |
| REQ-002-004 | Decodificación UTF-8 estricta con rechazo accionable; BOM inicial tolerado y eliminado | `openspec/changes/text-import/specs/002-text-import/spec.md` — AC-002-05 | `apps/api/tests/unit/test_text_extraction.py`, `apps/api/tests/api/test_imports.py` | T1B06–T1B07 | Cumplido |
| REQ-002-012 | Un archivo vacío o solo con separadores importa correctamente con cero formas únicas | `openspec/changes/text-import/specs/002-text-import/spec.md` — AC-002-17 | `apps/api/tests/unit/test_import_text.py::test_a_content_free_upload_succeeds_with_zero_forms`, `apps/api/tests/api/test_imports.py::test_a_content_free_upload_is_a_success_with_a_zero_state` | T1B12–T1B14 | Cumplido |
| REQ-002-007 | Ni la clave de agrupación ni la forma mostrada se llaman «lemma» ni «lexeme» | `openspec/changes/text-import/specs/002-text-import/spec.md` — AC-002-10 | `apps/api/tests/unit/test_no_lemma_naming.py` (leg de backend + leg de columnas persistidas, `test_persisted_columns_contain_no_lemma_naming`); `apps/web/tests/contracts/no-lemma-naming.test.ts` (leg de frontend, incluye el describe `findViolations (remediation — pins the comment exemption directly)`) | T1B20 (leg de backend); T1C14 (leg de frontend); T217 (leg de columnas persistidas) | Cumplido — cerrado en el corte 2: el leg de columnas persistidas (T217) comprueba, con el mismo criterio AST, tanto `infrastructure/persistence/models.py` como la migración `0002_book_occurrence.py` (fuera de `_PACKAGE_ROOT`, así que el escaneo de código fuente no la alcanza por sí solo), más los nombres de columna reflejados desde `Base.metadata` en tiempo de ejecución. Los tres legs están ahora unificados en el mismo criterio estructural (AST para Python/TypeScript, JSON para el schema y el OpenAPI servido, metadata reflejada para las columnas persistidas) |
| REQ-002-013 | Ningún registro de log contiene texto importado; los fallos se identifican por código e `import_id` | `openspec/changes/text-import/specs/002-text-import/spec.md` — AC-002-18 | `apps/api/tests/api/test_imports_logging.py` (leg de importación); `apps/api/tests/integration/test_book_repository.py::test_a_persistence_failure_during_create_logs_code_and_no_raw_text`, `::test_reading_an_unknown_import_logs_the_attempted_id` (leg de lectura y persistencia) | T1B18–T1B19 (leg de importación); T213–T214 (leg de lectura y persistencia) | Cumplido — cerrado en el corte 2: un fallo de persistencia durante `ImportText.create` se traduce a `PersistenceFailedError` (código `PERSISTENCE_FAILURE`, sin detalle de la excepción original) y una lectura `GET` con `id` desconocido registra `code=IMPORT_NOT_FOUND import_id=<id>` — nunca texto importado (spec §1.2, requisito transversal) |
| REQ-002-014 | El frontend no duplica ninguna regla lingüística: renderiza exactamente lo que devuelve la API, sin tokenizar, normalizar, ordenar ni derivar la forma mostrada | `openspec/changes/text-import/specs/002-text-import/spec.md` — AC-002-19 | `apps/web/tests/components/FrequencyTable.test.tsx::test_renders_received_order_and_display_form_verbatim`, `::test_frequency_column_is_not_colour_only`, `apps/web/tests/contracts/no-linguistic-rules.test.ts::test_import_modules_have_no_linguistic_rules` | T1C05–T1C09 | Cumplido |
| REQ-002-008 | Persistir `Book` + `Occurrence` (una fila por token emitido) vía repositorio y migración verificable | `openspec/changes/text-import/specs/002-text-import/spec.md` — AC-002-11, AC-002-12 | `apps/api/tests/integration/test_alembic_0002.py::test_upgrade_and_downgrade_book_occurrence`, `apps/api/tests/integration/test_book_repository.py::test_frequency_pairs_survives_a_new_session_against_the_same_database`, `::test_create_batches_occurrence_inserts_at_the_configured_size` | T201–T204, T207–T209 | Cumplido |
| REQ-002-009 | `content_hash` criptográfico (SHA-256, minúsculas, hex) en `Book`, calculado sobre los bytes crudos antes de decodificar | `openspec/changes/text-import/specs/002-text-import/spec.md` — AC-002-13 | `apps/api/tests/integration/test_book_repository.py::test_content_hash_matches_an_independently_computed_sha256`, `::test_a_one_byte_difference_changes_the_hash` | T206 | Cumplido |
| REQ-002-010 | `pos` reservado por aparición, siempre `None`, nunca global; `raw_text`/`normalized_text` permanecen columnas distintas | `openspec/changes/text-import/specs/002-text-import/spec.md` — AC-002-14 | `apps/api/tests/integration/test_occurrence_pos.py::test_every_persisted_occurrence_has_pos_none`, `::test_raw_text_and_normalized_text_stay_separate_values` | T205 | Cumplido |
| REQ-002-011 | Eliminar una importación y sus datos derivados, con confirmación explícita en la UI; el borrado es permanente, nunca lógico | `openspec/changes/text-import/specs/002-text-import/spec.md` — AC-002-15, AC-002-16 | `apps/api/tests/integration/test_delete_import.py`, `apps/api/tests/api/test_imports_cors.py::test_a_delete_preflight_is_allowed`, `apps/api/tests/unit/test_no_soft_delete.py`, `apps/web/tests/components/DeleteImportButton.test.tsx`, `apps/web/e2e/delete-import.spec.ts` | T301–T310 | Cumplido — corte 3, cierre de SPEC-002: `SqlAlchemyBookRepository.delete()` emite dos sentencias `DELETE` explícitas en una transacción (`occurrence` luego `book`), nunca `ON DELETE CASCADE` (design §6.2); la UI exige confirmación explícita antes de emitir la petición (Art. IX.5, rama de confirmación) |


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

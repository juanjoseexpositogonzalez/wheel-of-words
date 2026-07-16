# SPEC-001 — Plan de pruebas

## 1. Objetivos

Verificar que la fundación se instala, arranca, configura, prueba de forma aislada, integra frontend/API/SQLite y se reproduce en CI.

## 2. Pirámide

```text
          E2E
       Integración
  Unitarias y contrato
```

## 3. Backend

### UT-BE-001 — Configuración válida

Requisito: REQ-001-007. Construir configuración con valores de prueba.

### UT-BE-002 — Configuración inválida

Requisito: REQ-001-007. Una URL inválida produce error de validación.

### UT-BE-003 — Respuesta de salud

Requisito: REQ-001-002. Verificar el modelo sin servidor real.

### API-BE-001 — Endpoint de salud

Requisitos: REQ-001-001, REQ-001-002. Comprobar código 200, JSON y campos.

### INT-BE-001 — SQLite temporal

Requisito: REQ-001-005. Crear base temporal y ejecutar consulta trivial.

### INT-BE-002 — Migración upgrade

Requisito: REQ-001-006. Aplicar desde base vacía hasta `head`.

### INT-BE-003 — Migración downgrade

Requisito: REQ-001-006. Revertir cuando el diseño lo permita.

## 4. Frontend

### UT-FE-001 — Loading

Muestra “Comprobando estado”.

### UT-FE-002 — Available

Simular 200 y comprobar “Backend disponible”.

### UT-FE-003 — Unavailable

Simular error y comprobar “Backend no disponible”.

### UT-FE-004 — Retry

El botón provoca una nueva consulta.

### A11Y-FE-001 — Accesibilidad

Texto visible, región de estado y botón con nombre accesible.

## 5. Contrato

### CONTRACT-001 — HealthResponse

Requisitos: REQ-001-002, REQ-001-004. Validar que el frontend acepta el esquema OpenAPI.

## 6. E2E

### E2E-001 — Estado integrado

1. Arrancar API.
2. Arrancar web.
3. Abrir `/`.
4. Ver nombre.
5. Ver “Backend disponible”.

El error de backend se cubre obligatoriamente a nivel de componente y puede añadirse a E2E cuando no complique la estabilidad.

## 7. CI

- Ruff, mypy, pytest y cobertura.
- TypeScript, linter y Vitest.
- Alembic sobre base vacía.
- Playwright con Chromium y artefactos solo en fallo.

## 8. Datos de prueba

- Cadenas sintéticas.
- Bases temporales.
- Puertos configurables.
- Variables de entorno de prueba.
- Sin textos protegidos.

## 9. Criterios de salida

- Todas las pruebas obligatorias pasan.
- No hay tests ignorados sin justificación.
- No hay red pública.
- Se alcanzan umbrales de cobertura.
- E2E es estable en ejecuciones repetidas.

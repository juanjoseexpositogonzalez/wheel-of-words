# SPEC-001 — Fundación técnica del proyecto

**Estado:** Lista para implementación  
**Prioridad:** Crítica  
**Tipo:** Enabler técnico  
**Versión:** 1.0.0

## 1. Resumen

Crear la base técnica reproducible sobre la que se desarrollarán los cortes verticales posteriores. No implementa todavía análisis de libros; garantiza que backend, frontend, persistencia, calidad y CI estén integrados desde el inicio.

## 2. Objetivo

Al completar la feature, un desarrollador podrá clonar, instalar, arrancar, probar, comprobar calidad, aplicar migraciones y ejecutar un flujo E2E siguiendo únicamente la documentación.

## 3. Alcance

- Monorepositorio.
- Backend FastAPI.
- Frontend React + TypeScript + Vite.
- SQLite con SQLAlchemy y Alembic.
- Endpoint de salud.
- Pantalla de estado.
- Pruebas unitarias, integración y E2E mínimas.
- Ruff, mypy, Vitest, Testing Library y Playwright.
- Makefile.
- Variables de entorno de ejemplo.
- GitHub Actions.
- Documentación de arranque.

## 4. Fuera de alcance

- Importación de libros.
- Tokenización o lematización.
- Categorías gramaticales.
- Phrasal verbs.
- Anki.
- Autenticación.
- Despliegue de producción.
- PostgreSQL.

## 5. Actores

- **Desarrollador:** configura, ejecuta y valida.
- **Usuario técnico:** verifica que web y API están operativas.
- **CI:** ejecuta validaciones en cada cambio.

## 6. Suposiciones

- Linux, macOS o WSL.
- Python 3.12 o superior.
- Node.js LTS y pnpm.
- Git.
- Docker opcional.

## 7. Requisitos funcionales

### REQ-001-001 — Backend arrancable

Debe existir una aplicación FastAPI arrancable mediante un comando documentado.

### REQ-001-002 — Endpoint de salud

El backend expondrá `GET /api/v1/health` con respuesta mínima:

```json
{
  "status": "ok",
  "service": "wheel-vocabulary-api",
  "version": "0.1.0"
}
```

### REQ-001-003 — Frontend arrancable

Debe existir una aplicación React + TypeScript arrancable mediante un comando documentado.

### REQ-001-004 — Estado integrado

El frontend consultará el endpoint de salud y mostrará:

- Comprobando estado.
- Backend disponible.
- Backend no disponible.

En error deberá ofrecer reintento.

### REQ-001-005 — Persistencia configurable

El backend se conectará a SQLite mediante una URL configurable.

### REQ-001-006 — Migraciones

Alembic estará configurado y existirá una migración inicial verificable.

### REQ-001-007 — Configuración

La configuración se leerá de variables de entorno y habrá `.env.example` sin secretos.

### REQ-001-008 — Comandos unificados

Existirán comandos equivalentes a:

```text
make install
make dev
make test
make lint
make typecheck
make format
make e2e
make migrate
```

### REQ-001-009 — Pruebas backend

Existirán al menos una prueba unitaria, una prueba de API y una integración con SQLite temporal.

### REQ-001-010 — Pruebas frontend

Existirán pruebas de componente para disponibilidad, carga, error y reintento.

### REQ-001-011 — Prueba end-to-end

Playwright abrirá la aplicación y verificará el estado integrado.

### REQ-001-012 — Calidad Python

El backend pasará Ruff y mypy con configuración estricta acordada.

### REQ-001-013 — Calidad TypeScript

El frontend pasará TypeScript y su linter.

### REQ-001-014 — Integración continua

GitHub Actions ejecutará instalación, lint, tipado, pruebas backend, pruebas frontend, E2E y migraciones en cada pull request.

### REQ-001-015 — Separación de capas

El backend incluirá:

```text
domain/
application/
infrastructure/
api/
```

sin introducir lógica de dominio ficticia.

### REQ-001-016 — Documentación

El README explicará requisitos, instalación, arranque, pruebas, calidad, migraciones y estructura.

### REQ-001-017 — Ausencia de material protegido

El repositorio no contendrá textos de libros protegidos.

### REQ-001-018 — Seguridad mínima

Se ignorarán `.env`, bases locales, archivos importados, cobertura, cachés, secretos y exportaciones generadas.

## 8. Requisitos no funcionales

### REQ-001-NF-001 — Reproducibilidad

Las dependencias estarán bloqueadas mediante lockfiles.

### REQ-001-NF-002 — Feedback rápido

Las pruebas unitarias deben ofrecer feedback rápido en una máquina normal.

### REQ-001-NF-003 — Determinismo

Las pruebas no dependerán de red pública.

### REQ-001-NF-004 — Compatibilidad

La aplicación funcionará al menos en Chromium reciente durante el MVP.

### REQ-001-NF-005 — Accesibilidad

La pantalla de estado utilizará texto visible y regiones accesibles, no solo color.

### REQ-001-NF-006 — Mantenibilidad

La configuración estará centralizada y documentada.

## 9. Regla transversal

Ningún dato de prueba contendrá fragmentos extensos de obras protegidas.

## 10. Estados del frontend

```text
idle → loading → available
                 └→ unavailable
```

## 11. Errores

Si el backend no responde, el frontend mostrará un estado comprensible, no lanzará una excepción no controlada, permitirá reintentar y conservará la página utilizable.

## 12. Criterio global de aceptación

Un clon limpio debe ejecutar el flujo completo siguiendo únicamente el README, con todos los controles pasando localmente y en CI.

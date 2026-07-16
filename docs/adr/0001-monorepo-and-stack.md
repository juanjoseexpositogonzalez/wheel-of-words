# ADR-0001 — Monorepositorio y stack inicial

**Estado:** Aceptado  
**Fecha:** 2026-07-15

## Contexto

El producto necesita backend Python para NLP, API web, frontend tipado, persistencia local y pruebas unitarias, integración y E2E.

## Decisión

### Repositorio

Monorepositorio.

### Backend

- Python 3.12 o superior.
- FastAPI.
- Pydantic.
- SQLAlchemy 2.
- Alembic.
- SQLite.
- spaCy como primer adaptador NLP.
- `uv`.
- pytest.
- Hypothesis.
- Ruff.
- mypy.

### Frontend

- React.
- TypeScript.
- Vite.
- TanStack Query.
- Vitest.
- Testing Library.
- Playwright.
- pnpm.

### Automatización

- Makefile.
- Docker Compose opcional.
- GitHub Actions.

## Consecuencias positivas

- Python encaja con NLP.
- React/Vite reduce complejidad.
- SQLite favorece local-first.
- El monorepo simplifica cambios verticales.
- OpenAPI coordina contratos.

## Consecuencias negativas

- Dos ecosistemas de dependencias.
- CI de monorepo requiere disciplina.
- SQLite puede quedarse corto para concurrencia multiusuario.
- spaCy no resolverá todos los casos literarios.

## Alternativas consideradas

- **Next.js:** no se necesita SSR ni backend Node.
- **Streamlit:** limita evolución y control de interfaz.
- **PostgreSQL inicial:** complejidad innecesaria para local-first.
- **Stanza:** se conserva como posible adaptador alternativo.

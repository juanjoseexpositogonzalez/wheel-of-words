# SPEC-001 — Plan técnico

## 1. Estrategia

Implementar una fundación mínima pero completa, evitando lógica ficticia.

Orden:

1. Estructura.
2. Tooling backend.
3. Endpoint de salud.
4. Tooling frontend.
5. Pantalla de estado.
6. Persistencia y migración.
7. Integración.
8. E2E.
9. CI.
10. Documentación.

## 2. Estructura propuesta

```text
wheel-vocabulary/
├── apps/
│   ├── api/
│   │   ├── pyproject.toml
│   │   ├── src/wheel_vocab/
│   │   │   ├── domain/
│   │   │   ├── application/
│   │   │   ├── infrastructure/
│   │   │   ├── api/
│   │   │   ├── config.py
│   │   │   └── main.py
│   │   ├── migrations/
│   │   └── tests/
│   └── web/
│       ├── package.json
│       ├── src/
│       └── tests/
├── specs/
├── docs/
├── .github/workflows/ci.yml
├── .env.example
├── .gitignore
├── Makefile
└── README.md
```

## 3. Backend

### Configuración

Utilizar `pydantic-settings` con `app_name`, `app_version`, `environment`, `database_url`, `cors_origins` y `log_level`.

### Factory

```python
def create_app(settings: Settings | None = None) -> FastAPI:
    ...
```

Facilita inyección, pruebas y aislamiento.

### Salud

`GET /api/v1/health`, sin dependencias externas en esta versión.

### Persistencia

- SQLAlchemy 2.
- Factories de engine y sesión.
- SQLite de desarrollo.
- SQLite temporal para integración.
- Alembic con migración inicial.

La migración inicial puede crear `app_metadata`; no se crearán entidades de dominio ficticias.

## 4. Frontend

Componentes iniciales:

- `App`
- `BackendStatus`
- `RetryButton`

Estado tipado:

```typescript
type BackendState =
  | { status: "loading" }
  | { status: "available"; version: string }
  | { status: "unavailable"; message: string };
```

El cliente HTTP será pequeño y tipado. TanStack Query puede gestionar consulta y reintento.

## 5. Contrato

```typescript
interface HealthResponse {
  status: "ok";
  service: string;
  version: string;
}
```

OpenAPI será la fuente de verdad.

## 6. Pruebas

Backend: configuración, modelo de salud, endpoint, SQLite y migraciones.

Frontend: loading, available, unavailable, retry y accesibilidad.

E2E: abrir aplicación, ver nombre y backend disponible.

## 7. CI

Trabajos:

1. `backend-quality`
2. `backend-tests`
3. `frontend-quality`
4. `frontend-tests`
5. `migration-check`
6. `e2e`

Usar caché de `uv` y pnpm.

## 8. Seguridad

- `.env` y `data/` ignorados.
- No registrar secretos ni contenido de libros.
- No exponer traceback en producción.
- CORS configurable.

## 9. Observabilidad

Logging estructurado básico con nivel, timestamp, servicio, entorno y mensaje.

## 10. Riesgos

- **E2E inestable:** esperar condiciones visibles, no usar sleeps.
- **Configuración duplicada:** centralizar y validar.
- **Monorepo lento:** jobs paralelos y cachés.

## 11. Entregables

Backend y frontend arrancables, endpoint y pantalla integrados, migración inicial, suites, CI y README.

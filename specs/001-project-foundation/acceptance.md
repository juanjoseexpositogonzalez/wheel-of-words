# SPEC-001 — Criterios de aceptación

## AC-001 — Arranque del backend

```gherkin
Scenario: El backend arranca correctamente
  Given un clon limpio con dependencias instaladas
  When el desarrollador ejecuta el comando documentado
  Then FastAPI queda disponible
  And GET /api/v1/health responde 200
  And la respuesta contiene status "ok"
```

## AC-002 — Arranque del frontend

```gherkin
Scenario: El frontend arranca correctamente
  Given un clon limpio con dependencias instaladas
  When el desarrollador ejecuta el comando documentado
  Then la aplicación web queda disponible
  And muestra el nombre del producto
```

## AC-003 — Backend disponible

```gherkin
Scenario: El frontend detecta el backend
  Given el frontend está arrancado
  And el backend está arrancado
  When el usuario abre la pantalla inicial
  Then ve "Backend disponible"
```

## AC-004 — Backend no disponible

```gherkin
Scenario: El frontend gestiona un fallo de conexión
  Given el frontend está arrancado
  And el backend no está disponible
  When el usuario abre la pantalla inicial
  Then ve "Backend no disponible"
  And la interfaz no queda bloqueada
  And existe una acción de reintento
```

## AC-005 — Base de datos aislada

```gherkin
Scenario: La API usa una base de prueba aislada
  Given una base SQLite temporal
  When se inicializa la aplicación de prueba
  Then las migraciones pueden aplicarse
  And la prueba no modifica la base de desarrollo
```

## AC-006 — Migración inicial

```gherkin
Scenario: Alembic aplica el esquema inicial
  Given una base de datos vacía
  When se ejecuta la migración hasta head
  Then la operación termina sin error
  And Alembic registra la revisión aplicada
```

## AC-007 — Configuración segura

```gherkin
Scenario: El repositorio contiene configuración de ejemplo segura
  Given el repositorio
  Then existe .env.example
  And no contiene credenciales reales
  And .env está ignorado por Git
```

## AC-008 — Comandos unificados

```gherkin
Scenario Outline: Los comandos principales están disponibles
  Given un entorno configurado
  When se ejecuta "<command>"
  Then termina con el resultado documentado

  Examples:
    | command        |
    | make test      |
    | make lint      |
    | make typecheck |
    | make format    |
    | make migrate   |
```

## AC-009 — Suite backend

```gherkin
Scenario: La suite backend pasa
  Given las dependencias instaladas
  When se ejecutan las pruebas backend
  Then todas pasan
  And se genera informe de cobertura
```

## AC-010 — Suite frontend

```gherkin
Scenario: La suite frontend pasa
  Given las dependencias instaladas
  When se ejecutan las pruebas frontend
  Then todas pasan
```

## AC-011 — Flujo E2E

```gherkin
Scenario: La aplicación integrada muestra el estado del backend
  Given frontend y backend están arrancados
  When Playwright abre la aplicación
  Then el nombre del producto es visible
  And "Backend disponible" es visible
```

## AC-012 — CI

```gherkin
Scenario: Una pull request válida pasa la integración continua
  Given una rama con todos los controles correctos
  When se abre una pull request
  Then GitHub Actions ejecuta todas las validaciones
  And todos los trabajos terminan correctamente
```

## AC-013 — Protección de contenido

```gherkin
Scenario: El repositorio no incluye libros
  Given el contenido versionado
  Then no existen EPUB, PDF o TXT de obras protegidas
  And los directorios de importación están ignorados
```

## AC-014 — Accesibilidad mínima

```gherkin
Scenario: El estado es perceptible sin depender del color
  Given la pantalla de estado
  Then el estado se expresa mediante texto
  And el control de reintento tiene nombre accesible
```

## AC-015 — Documentación suficiente

```gherkin
Scenario: Un desarrollador nuevo sigue el README
  Given un clon limpio
  When sigue los pasos documentados
  Then instala dependencias
  And arranca la aplicación
  And ejecuta pruebas y controles de calidad
```

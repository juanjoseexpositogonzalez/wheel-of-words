# Visión general de arquitectura

## 1. Objetivo

Definir una arquitectura inicial modular para análisis lingüístico, persistencia, API web y exportación, sin complejidad prematura.

## 2. Vista de contexto

```text
Usuario
  │
  ▼
Aplicación web
  │ HTTP/JSON
  ▼
API FastAPI
  ├── Casos de uso
  ├── Dominio
  ├── Persistencia SQLite
  ├── Procesamiento NLP
  └── Exportadores
```

## 3. Monorepositorio

```text
apps/
├── api/
└── web/
```

Ventajas: contratos coordinados, CI unificada, cambios verticales y versionado conjunto durante el MVP.

## 4. Backend

### Dominio

Entidades previstas:

- `Book`
- `Chapter`
- `ProcessingRun`
- `Lexeme`
- `WordForm`
- `Occurrence`
- `PartOfSpeech`
- `MultiwordExpression`
- `LearningStatus`
- `ManualCorrection`
- `ExportSelection`

### Aplicación

Casos de uso previstos:

- `CreateBook`
- `ImportText`
- `AnalyzeBook`
- `ListLexemes`
- `SearchVocabulary`
- `CorrectAnalysis`
- `ChangeLearningStatus`
- `ExportVocabulary`

### Infraestructura

- Repositorios SQLAlchemy.
- Extracción TXT y EPUB.
- Analizador spaCy.
- Exportadores CSV/TSV y Anki.
- Hashing de archivos.

### API

Validación HTTP, serialización, OpenAPI, mapeo de errores y autorización futura.

## 5. Frontend

Tecnología inicial:

- React.
- TypeScript.
- Vite.
- TanStack Query.
- React Router.
- Testing Library.
- Vitest.
- Playwright.

Responsabilidades: importación, estado de procesamiento, tabla, filtros, correcciones, selección y exportación. No contiene reglas lingüísticas.

## 6. Persistencia

SQLite en el MVP por instalación sencilla, operación local y backups simples. SQLAlchemy y Alembic permitirán migrar a PostgreSQL.

## 7. Procesamiento

Estados:

```text
pending
running
succeeded
failed
cancelled
```

Cada ejecución guardará identificador, versiones, configuración, tiempos, estado, error sanitizado y métricas.

## 8. Adaptadores

- `LinguisticAnalyzer`
- `BookRepository`
- `TextExtractor`
- `VocabularyExporter`

## 9. Seguridad

- Validar extensión y contenido.
- Límites de tamaño configurables.
- No confiar en nombres de archivo.
- Archivos fuera del árbol público.
- No ejecutar contenido importado.
- Sanitizar logs.
- No versionar secretos.

## 10. Evolución

Debe permitir añadir EPUB, modelos NLP alternativos, PostgreSQL, trabajos en segundo plano, autenticación e interfaz de escritorio.

## Referencias

Este documento es el mapa vivo de la arquitectura. Se complementa con:

- `docs/architecture/architecture-baseline.md` — estado comprometido en un momento del tiempo (incluye diagramas Mermaid y lista de invariantes con referencias a los ADR).
- `docs/adr/README.md` — índice de decisiones arquitectónicas versionadas.
- `docs/glossary.md` — vocabulario de dominio (13+ términos canónicos).
- `docs/decisions-log.md` — log cronológico de decisiones del proyecto.
- `docs/traceability-matrix.md` — matriz de trazabilidad cruzada entre especificaciones.
- `docs/definition-of-done.md` — extracto navegable de la Definición de Terminado (la Constitución sigue siendo canónica).

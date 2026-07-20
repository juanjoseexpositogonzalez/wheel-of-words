# Wheel Vocabulary — Paquete inicial SDD + TDD

Este paquete define el marco de trabajo para construir una aplicación web de análisis de vocabulario literario en el idioma que el lector estudia. El inglés es la primera lengua soportada y *The Eye of the World* es el corpus inicial aportado legalmente por el usuario.

## Contenido

```text
.
├── AGENTS.md
├── README.md
├── docs/
│   ├── constitution.md
│   ├── product-vision.md
│   ├── architecture/overview.md
│   └── adr/0001-monorepo-and-stack.md
├── specs/001-project-foundation/
│   ├── spec.md
│   ├── acceptance.md
│   ├── plan.md
│   ├── test-plan.md
│   ├── tasks.md
│   ├── decisions.md
│   └── traceability.md
└── templates/feature-spec-template.md
```

## Flujo obligatorio

```text
Constitución
    ↓
Especificación
    ↓
Criterios de aceptación
    ↓
Plan técnico
    ↓
Plan de pruebas
    ↓
Tareas
    ↓
RED → GREEN → REFACTOR
    ↓
Validación y trazabilidad
```

## Alcance del paquete

Este ZIP no contiene todavía código de la aplicación. Fija:

- Las reglas no negociables del proyecto.
- La visión y el alcance del producto.
- La arquitectura inicial.
- Las instrucciones para agentes y desarrolladores.
- La especificación completa de la primera feature: la fundación técnica.
- Una plantilla reutilizable para especificaciones futuras.

## Siguiente especificación recomendada

```text
SPEC-002 — Importar un archivo TXT y mostrar una lista alfabética
de palabras únicas con su frecuencia.
```

Esa especificación será el primer corte vertical con valor visible para el usuario.

---

## Referencias metodológicas

- [Instrucciones de agentes y colaboradores](AGENTS.md)
- [Constitución del proyecto](docs/constitution.md)
- [Visión de producto](docs/product-vision.md)
- [Índice de ADR](docs/adr/README.md)
- [Baseline arquitectónica](docs/architecture/architecture-baseline.md)
- [Glosario](docs/glossary.md)
- [Definición de terminado](docs/definition-of-done.md)
- [Matriz de trazabilidad](docs/traceability-matrix.md)
- [Log de decisiones](docs/decisions-log.md)

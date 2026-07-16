# Instrucciones de desarrollo para agentes y colaboradores

## 1. Metodología obligatoria

Este proyecto utiliza simultáneamente:

- Specification-Driven Development, SDD.
- Test-Driven Development, TDD.
- Entregas mediante cortes verticales pequeños.
- Arquitectura dirigida por el dominio con pragmatismo.

Ninguna funcionalidad debe implementarse directamente desde una petición informal. Antes de modificar código deben existir, como mínimo:

1. Una especificación de la feature.
2. Requisitos identificados de forma única.
3. Criterios de aceptación observables.
4. Un plan técnico.
5. Un plan de pruebas.
6. Una lista de tareas ordenada.
7. Una matriz de trazabilidad inicial.

## 2. Orden obligatorio de trabajo

Para cada comportamiento:

1. Identificar el requisito correspondiente.
2. Escribir o actualizar la prueba.
3. Ejecutar la prueba.
4. Confirmar que falla por la razón esperada.
5. Implementar la solución mínima que satisfaga la prueba.
6. Ejecutar la prueba afectada.
7. Ejecutar la suite relacionada.
8. Refactorizar sin modificar el comportamiento observable.
9. Ejecutar todos los controles de calidad.
10. Actualizar documentación y trazabilidad.

No se debe escribir primero una implementación completa para añadir las pruebas posteriormente.

## 3. Ciclo TDD

### RED

- La prueba debe expresar un único comportamiento relevante.
- La prueba debe fallar antes de implementar.
- El fallo debe ser comprensible y estar relacionado con la ausencia del comportamiento.
- No se acepta una prueba que falle por errores de sintaxis, configuración o fixtures defectuosas.

### GREEN

- Implementar la solución mínima correcta.
- No anticipar funcionalidades futuras.
- No introducir abstracciones sin uso real.
- Mantener el código tipado y legible.

### REFACTOR

- Eliminar duplicación.
- Mejorar nombres.
- Reducir acoplamiento.
- Mantener interfaces coherentes.
- Preservar todos los comportamientos y pruebas en verde.

## 4. Restricciones del dominio

- No incluir libros protegidos por derechos de autor en el repositorio.
- Utilizar textos sintéticos, propios o de dominio público en pruebas.
- El usuario debe aportar legalmente cualquier libro analizado.
- El texto del libro no debe enviarse a terceros sin consentimiento explícito.
- El procesamiento local será la opción predeterminada.
- Mantener separadas la forma textual, la forma normalizada, el lema y la categoría gramatical contextual.
- No asignar necesariamente una única categoría gramatical global a cada lema.
- Conservar la categoría de cada aparición.
- Las correcciones manuales prevalecen sobre resultados automáticos.
- El reprocesamiento nunca debe sobrescribir silenciosamente una corrección manual.
- Los resultados automáticos deben guardar su procedencia.
- Cuando exista incertidumbre, se debe guardar una puntuación o nivel de confianza.
- Las expresiones multipalabra específicas del idioma (por ejemplo, phrasal verbs en inglés, locuciones y perífrasis verbales en español, verbos separables en alemán) deben modelarse separadamente de los lemas de una sola palabra.
- Las reglas lingüísticas no deben duplicarse en el frontend.

## 5. Arquitectura

El backend se divide en:

```text
domain
application
infrastructure
api
```

Reglas:

- `domain` no depende de FastAPI, SQLAlchemy, spaCy ni bibliotecas web.
- `application` orquesta casos de uso y depende de puertos o interfaces.
- `infrastructure` implementa persistencia, NLP, importadores y exportadores.
- `api` adapta HTTP al modelo de aplicación.
- El frontend consume contratos de API; no replica reglas de dominio.
- Los efectos secundarios deben permanecer en los bordes.
- Las transformaciones lingüísticas puras deben favorecer funciones puras.
- Los datos se validan en los límites del sistema.
- Las excepciones deben traducirse a errores significativos.

## 6. Pruebas

### Unitarias

Deben cubrir reglas de dominio, transformaciones, validaciones, estados e invariantes. No deben necesitar red, servidor HTTP, base de datos real o modelos NLP pesados.

### Integración

Deben cubrir persistencia, migraciones, API con repositorios reales de prueba, integración con spaCy o Stanza, importación de archivos y exportación a Anki.

### Contrato

Deben comprobar que frontend y backend comparten modelos compatibles.

### End-to-end

Deben probar flujos críticos completos con Playwright.

### Regresión lingüística

Cada error lingüístico corregido debe añadir una fixture mínima y una prueba de regresión.

### Property-based testing

Usar Hypothesis para invariantes como:

- Normalizar dos veces equivale a normalizar una vez.
- Las frecuencias nunca son negativas.
- El orden de entrada no altera el conjunto de lemas.
- Una selección vacía no produce tarjetas.
- Las correcciones manuales sobreviven al reprocesamiento.

## 7. Convenciones para requisitos

Formato:

```text
REQ-<feature>-<número>
```

Cada requisito debe ser atómico, verificable, no ambiguo y trazable a pruebas y tareas.

## 8. Convenciones para tareas

Formato:

```text
T<numero> [TIPO] descripción
```

Tipos admitidos: `[SPEC]`, `[TEST]`, `[IMPL]`, `[REFACTOR]`, `[DOC]`, `[MIGRATION]`, `[E2E]`, `[CI]`, `[SECURITY]`.

En tareas TDD, el orden debe ser:

```text
[TEST] → [IMPL] → [REFACTOR]
```

## 9. Cambios de especificación

Cuando aparezca una ambigüedad o contradicción:

1. No inventar silenciosamente el comportamiento.
2. Registrar el problema.
3. Proponer una resolución concreta.
4. Actualizar especificación y aceptación.
5. Actualizar pruebas.
6. Actualizar trazabilidad.
7. Continuar con la especificación corregida.

## 10. Definición de terminado

Una tarea o feature no está terminada hasta que:

- Los requisitos están actualizados.
- Los criterios de aceptación son verificables.
- Las pruebas relevantes están en verde.
- El tipado estático y el linter están en verde.
- El formateador no produce cambios pendientes.
- Las migraciones afectadas están verificadas.
- La documentación y la trazabilidad están actualizadas.
- No se ha incorporado material protegido.
- No existen errores conocidos ocultados.
- La matriz de trazabilidad (`docs/traceability-matrix.md`) se ha actualizado con las filas correspondientes a los requisitos trabajados.

## 11. Informe final obligatorio

Al finalizar una tarea, indicar:

- Requisitos implementados.
- Pruebas añadidas o modificadas.
- Archivos principales afectados.
- Decisiones técnicas.
- Comandos de validación ejecutados.
- Limitaciones o trabajo pendiente.

---

## Referencias del proyecto

- [Constitución](docs/constitution.md) — fuente canónica en caso de conflicto.
- [Visión de producto](docs/product-vision.md)
- [Índice de ADR](docs/adr/README.md)
- [Baseline arquitectónica](docs/architecture/architecture-baseline.md)
- [Glosario](docs/glossary.md)
- [Definición de terminado (extracto)](docs/definition-of-done.md)
- [Matriz de trazabilidad](docs/traceability-matrix.md)
- [Log de decisiones](docs/decisions-log.md)

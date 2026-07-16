# Definición de Terminado — Wheel Vocabulary

## Alcance y jerarquía

Este archivo es un extracto navegable de la Definición de Terminado del
proyecto. Su propósito es hacer visible el criterio de terminado en la raíz de
`docs/` sin duplicar ni reemplazar la fuente canónica.

**La Constitución Art. XI es la fuente canónica en caso de conflicto entre
este documento y cualquier otra definición.** Cuando este archivo y la
Constitución difieran, la Constitución prevalece. Cuando este archivo y
AGENTS.md §10 difieran, AGENTS.md §10 prevalece solo si añade una restricción
operativa adicional que no contradiga la Constitución; si contradice la
Constitución, la Constitución gana.

---

## Criterios de terminado (referencia Constitución Art. XI)

Según la Constitución ([`docs/constitution.md`](constitution.md#artículo-xi-definición-de-terminado)),
una feature está terminada cuando cumple **todos** los siguientes puntos:

- Los requisitos están actualizados y reflejados en la especificación vigente.
- Los criterios de aceptación son verificables y están trazados a pruebas.
- Las pruebas relevantes están en verde (unitarias, integración, E2E según corresponda).
- El tipado estático y el linter están en verde.
- El formateador no produce cambios pendientes.
- Las migraciones afectadas están verificadas y no rompen el esquema existente.
- La documentación y la trazabilidad están actualizadas.
- No se ha incorporado material protegido por derechos de autor.
- No existen errores conocidos ocultados.

---

## Criterios operativos (referencia AGENTS.md §10)

[AGENTS.md §10](../AGENTS.md#10-definición-de-terminado) complementa la
Constitución con criterios operativos para el ciclo de trabajo diario:

- Los requisitos están actualizados.
- Los criterios de aceptación son verificables.
- Las pruebas relevantes están en verde.
- El tipado estático y el linter están en verde.
- El formateador no produce cambios pendientes.
- Las migraciones afectadas están verificadas.
- La documentación y la trazabilidad están actualizadas.
- No se ha incorporado material protegido.
- No existen errores conocidos ocultados.

**Regla adicional (se añadirá canónicamente en AGENTS.md §10 con Slice E):**

- La matriz de trazabilidad se ha actualizado con los identificadores de
  requisito, criterio de aceptación, prueba y tarea correspondientes.

Esta regla vive canónicamente en AGENTS.md §10 y se agregará allí en Slice E.
Se cita aquí para completitud e inmediata aplicabilidad.

---

## Puerta de trazabilidad

La [`docs/traceability-matrix.md`](traceability-matrix.md) es una puerta dura
de la Definición de Terminado. Ninguna tarea que introduzca o cierre un
requisito puede marcarse como terminada si la fila correspondiente no ha sido
actualizada en la matriz con los identificadores de requisito, criterio de
aceptación, prueba y tarea.

---

## Referencias

- [`docs/constitution.md`](constitution.md) — fuente canónica de la Definición
  de Terminado (Art. XI). En caso de conflicto, la Constitución prevalece.
- [`AGENTS.md`](../AGENTS.md) — criterios operativos §10; en caso de conflicto
  con este archivo, AGENTS.md prevalece solo si añade restricciones compatibles
  con la Constitución.
- [`docs/traceability-matrix.md`](traceability-matrix.md) — matriz de
  trazabilidad cruzada; puerta dura de la Definición de Terminado.
- [`docs/adr/README.md`](adr/README.md) — índice de decisiones arquitectónicas.
- [`docs/architecture/architecture-baseline.md`](architecture/architecture-baseline.md) — estado comprometido de la arquitectura.

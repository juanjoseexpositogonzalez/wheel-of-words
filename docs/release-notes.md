# Notas de versión — wheel-of-words

Registro de **consecuencias de producto** conocidas y aceptadas con conocimiento de causa, por
capability. Dirigido a quien usa o revisa la aplicación, no solo a quien la implementa —
complementa `docs/decisions-log.md` (decisiones técnicas internas) y `docs/adr/` (arquitectura):
este archivo documenta EFECTOS observables, no el razonamiento de diseño que los produjo.

## Reglas de actualización

1. Cada entrada de capability se añade en orden cronológico ascendente; no se reordenan entradas
   existentes.
2. No se eliminan entradas. Si una consecuencia deja de aplicar (por ejemplo, porque una
   capability posterior la resuelve), se añade una entrada nueva que referencia y cierra la
   anterior — nunca se edita la entrada original para que parezca que nunca existió.
3. Cada entrada indica: qué ocurre, por qué se aceptó, y qué requisito o ADR lo autoriza.
4. Esta obligación es explícita en la especificación: `openspec/changes/lemmatization-pos/specs/003-lemmatization-pos/spec.md`
   §5 `AMB-2` cierra con «Record it as such in the release notes» — antes de este fichero, ningún
   artefacto del repositorio cumplía esa instrucción (`verify-report.md` WARNING-1).

---

## SPEC-003 — Lematización y categoría gramatical (`lemmatization-pos`)

### La precisión de la anotación es menor de lo publicado por el modelo, por una interacción entre capabilities

`002-text-import` descarta todo token sin al menos una letra (`tokenizer.py::_contains_letter`,
regla T6): el flujo de tokens persistido **no contiene ningún signo de puntuación**. El etiquetador
POS (`en_core_web_sm`) recibe por tanto prosa sin punto final de frase, sin coma, sin comillas. La
métrica `tag_acc: 0.973` de la ficha del modelo se midió sobre OntoNotes **con** puntuación; la
precisión real sobre este flujo es medible­mente inferior, concentrada en los puntos donde un verbo
al final de una cláusula linda con un sujeto capitalizado de la frase siguiente.

Esto no es un defecto — es la consecuencia irreversible de una decisión ya tomada en `002-text-import`
(no re-tokenizar, no inyectar puntuación sintética: `REQ-003-013` prohíbe la re-subida del texto
original, así que no hay un camino barato para revertirlo). Ver `design.md` §P2 para las tres
alternativas consideradas y por qué se aceptó la señal degradada.

**Consecuencia para quien usa la aplicación:** la categoría gramatical (`pos`) mostrada puede ser
incorrecta con más frecuencia cerca de los límites de frase que en un corpus con puntuación
completa, especialmente en verbos en cláusulas finales seguidos de un sujeto propio. `pos_confidence`
es precisamente el canal por el que esta incertidumbre se hace visible al usuario (§5 AMB-2, PV-2).

### La confianza es siempre visible pero no es accionable en este ciclo

`pos_confidence`/`lemma_confidence` se muestran en toda aparición anotada, incluido un marcador
explícito de «no informada» cuando el analizador no reporta una — nunca una celda vacía. Pero
**ningún camino de corrección manual existe todavía**: esa capability llega con SPEC-004. Durante un
ciclo, un usuario puede ver que una clasificación es incierta y no puede hacer nada al respecto
dentro de la aplicación.

Esto se aceptó explícitamente (`REQ-003-009` C6, spec §5 `AMB-2`, `product-vision.md` PV-2): ninguna
capa puede filtrar, ordenar, ni aplicar un umbral sobre la confianza en esta capability, así que no
se hornea ninguna semántica prematura sobre un valor que todavía no es accionable. La alternativa
— ocultar la confianza hasta que sea accionable — se consideró peor: retrasaría el esquema de
procedencia, forzaría una segunda migración, y dejaría que SPEC-004 introdujera almacenamiento,
precedencia y UX simultáneamente.

**Consecuencia para quien usa la aplicación:** la interfaz no debe implicar, ni hoy implica, que se
puede actuar sobre la confianza — no hay control de filtro, orden, ni umbral en la vista de
anotación (`AnnotationTable.tsx`). Es meramente informativa hasta SPEC-004.

### Ningún filtro de nombres propios se envía en esta capability

`PROPN` se persiste y se muestra como cualquier otra etiqueta gramatical — sin filtro, sin
supresión, sin caso especial. Excluir nombres propios de la lista de vocabulario (`product-vision.md`
§10, paso 4: «Excluye nombres propios») queda deliberadamente fuera de alcance hasta el ítem 6 del
roadmap (`product-vision.md` §12: «Nombres propios y términos ficticios»).

Aplicar un filtro heurístico de nombres propios en esta capability habría anticipado el diseño de
esa capability futura con una heurística no revisada (spec §6 `PV-4`).

**Consecuencia para quien usa la aplicación:** nombres de personajes y lugares aparecerán en la
lista de apariciones anotadas junto con el resto del vocabulario hasta que el ítem 6 del roadmap
entregue un filtro diseñado explícitamente.

### `lemma_confidence` es siempre `NULL` para inglés — por diseño, no por omisión

El lematizador de `en_core_web_sm` es un componente basado en reglas y tablas de consulta
(`default_config={"mode": "rule"}`), determinista, y no expone ninguna probabilidad. Derivar un
valor de `pos_confidence` (que sí es un valor probabilístico real, obtenido del propio *forward
pass* del etiquetador) habría sido fabricar un número que el modelo nunca produjo (spec §2.3 C3).

**Consecuencia para quien usa la aplicación:** la columna «Confianza del lema» mostrará siempre «No
informada» para inglés — esto es honestidad sobre lo que el modelo puede y no puede reportar, no una
funcionalidad pendiente ni un error.

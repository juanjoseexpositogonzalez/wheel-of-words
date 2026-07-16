# Glosario del dominio lingüístico

## Propósito

Este glosario define los términos de dominio usados en Wheel Vocabulary. Su objetivo es eliminar ambigüedades entre desarrolladores, agentes y la persona propietaria del proyecto: cada término tiene una definición canónica, única, y trazable a las fuentes de autoridad del proyecto (Constitución, AGENTS.md, ADRs).

Para añadir o modificar una entrada, actualizar primero el ADR o artículo de la constitución correspondiente y luego reflejar el cambio aquí. Este glosario es un artefacto orientado al producto y se redacta en español.

Véase también: [`docs/constitution.md` Artículo V](constitution.md#artículo-v--integridad-del-modelo-lingüístico) y [`AGENTS.md §4 — Restricciones del dominio`](../AGENTS.md#4-restricciones-del-dominio).

---

## Cómo usar este glosario

Cada entrada incluye:

- **Categoría**: concepto | entidad | atributo | proceso | relación
- **Definición**: una oración completa en español.
- **Referencias**: al menos un enlace a la fuente de autoridad (constitución, AGENTS.md, ADR).
- **Impacto multiidioma**: si el término es independiente del idioma o específico de uno.

Las entradas están en orden alfabético. Busca por el nombre exacto del término tal como aparece en el dominio.

---

## Términos

### Aparición

- **Categoría**: entidad
- **Definición**: Instancia individual de una forma textual en una posición concreta del corpus, portadora de su propio POS contextual y referencia al lema correspondiente.
- **Referencias**: [`AGENTS.md §4`](../AGENTS.md#4-restricciones-del-dominio); [`docs/constitution.md` Art. V.3](constitution.md#artículo-v--integridad-del-modelo-lingüístico); [`docs/adr/0006-pos-per-occurrence.md`](adr/0006-pos-per-occurrence.md)
- **Impacto multiidioma**: Concepto independiente del idioma. Toda aparición, sea en inglés, español o alemán, sigue el mismo modelo de entidad.

---

### Categoría gramatical contextual

- **Categoría**: atributo
- **Definición**: Categoría gramatical (POS) asignada a una aparición concreta en su contexto sintáctico; no es una propiedad global del lema sino de cada aparición individual.
- **Referencias**: [`AGENTS.md §4`](../AGENTS.md#4-restricciones-del-dominio) — "No asignar necesariamente una única categoría gramatical global a cada lema. Conservar la categoría de cada aparición."; [`docs/constitution.md` Art. V.2–3](constitution.md#artículo-v--integridad-del-modelo-lingüístico); [`docs/adr/0006-pos-per-occurrence.md`](adr/0006-pos-per-occurrence.md)
- **Impacto multiidioma**: Concepto independiente del idioma. Los conjuntos de etiquetas POS (tagsets) varían por idioma y modelo NLP, pero el principio de asignación por aparición se aplica en todos los idiomas soportados.

---

### Corpus

- **Categoría**: entidad
- **Definición**: Colección completa de texto procesado junto con el modelo derivado: tokens, apariciones, lemas, expresiones multipalabra y correcciones manuales asociadas a una obra o conjunto de obras.
- **Referencias**: [`docs/constitution.md` Art. V](constitution.md#artículo-v--integridad-del-modelo-lingüístico); [`docs/architecture/overview.md §4`](architecture/overview.md#4-backend); [`docs/adr/0005-local-first.md`](adr/0005-local-first.md)
- **Impacto multiidioma**: Concepto independiente del idioma. Un corpus puede contener obras en cualquier idioma soportado por el adaptador NLP correspondiente.

---

### Corrección manual

- **Categoría**: entidad y proceso
- **Definición**: Modificación realizada por el usuario sobre el resultado automático de un campo de una aparición; prevalece sobre el resultado automático y persiste a través de reprocesamiento.
- **Referencias**: [`AGENTS.md §4`](../AGENTS.md#4-restricciones-del-dominio) — "Las correcciones manuales prevalecen sobre resultados automáticos. El reprocesamiento nunca debe sobrescribir silenciosamente una corrección manual."; [`docs/constitution.md` Art. V.8–9](constitution.md#artículo-v--integridad-del-modelo-lingüístico); [`docs/adr/0007-manual-corrections-precedence.md`](adr/0007-manual-corrections-precedence.md)
- **Impacto multiidioma**: Concepto independiente del idioma. La entidad `ManualCorrection` opera igual independientemente del idioma del corpus.

---

### Expresión multipalabra

- **Categoría**: entidad
- **Definición**: Unidad léxica compuesta por dos o más palabras cuya interpretación semántica va más allá de la suma de sus partes; se modela de forma separada a los lemas de una sola palabra.
- **Referencias**: [`AGENTS.md §4`](../AGENTS.md#4-restricciones-del-dominio); [`docs/constitution.md` Art. V.6](constitution.md#artículo-v--integridad-del-modelo-lingüístico); [`docs/adr/0009-mwe-language-specific-instances.md`](adr/0009-mwe-language-specific-instances.md)
- **Impacto multiidioma**: Patrón independiente del idioma. Las instancias concretas son específicas de cada idioma — véase la entrada siguiente.

---

### Expresión multipalabra específica del idioma

- **Categoría**: entidad (abstracta)
- **Definición**: Categoría abstracta que agrupa las unidades léxicas multipalabra cuya forma y comportamiento dependen del idioma concreto; cada idioma instancia esta categoría con sus propios fenómenos lingüísticos, identificados mediante el atributo `mwe_kind`.
- **Referencias**: [`AGENTS.md §4`](../AGENTS.md#4-restricciones-del-dominio); [`docs/constitution.md` Art. V.6](constitution.md#artículo-v--integridad-del-modelo-lingüístico); [`docs/adr/0008-multi-language-scope.md`](adr/0008-multi-language-scope.md); [`docs/adr/0009-mwe-language-specific-instances.md`](adr/0009-mwe-language-specific-instances.md)
- **Impacto multiidioma**: Concepto abstracto e independiente del idioma. Las instancias son específicas de cada idioma:
  - Inglés → phrasal verbs (`mwe_kind: "phrasal_verb"`)
  - Español → locuciones y perífrasis verbales (`mwe_kind: "locución_verbal"`, `"perífrasis_verbal"`)
  - Alemán → verbos separables / Trennbare Verben (`mwe_kind: "trennbares_verb"`)
  - Otros idiomas → instancias equivalentes, añadidas al incorporar cada adaptador NLP.

> Nota: el término canónico en español para esta categoría abstracta es exactamente **"expresiones multipalabra específicas del idioma"** (resolución OQ-10, design §2.3). No se aceptan sinónimos ni abreviaciones en los artefactos del proyecto.

---

### Forma normalizada

- **Categoría**: atributo
- **Definición**: Cadena de texto resultante de aplicar un proceso de normalización determinista a la forma textual (tipicamente: minúsculas, tratamiento de diacríticos y puntuación según las reglas del idioma).
- **Referencias**: [`AGENTS.md §4`](../AGENTS.md#4-restricciones-del-dominio) — "Mantener separadas la forma textual, la forma normalizada, el lema y la categoría gramatical contextual."; [`docs/constitution.md` Art. V.1](constitution.md#artículo-v--integridad-del-modelo-lingüístico)
- **Impacto multiidioma**: Las reglas de normalización varían por idioma (por ejemplo, el tratamiento de la diéresis en alemán o las tildes en español difieren de las reglas del inglés).

---

### Forma textual

- **Categoría**: atributo
- **Definición**: Cadena exacta de caracteres tal como aparece en el texto original, sin ninguna transformación.
- **Referencias**: [`AGENTS.md §4`](../AGENTS.md#4-restricciones-del-dominio); [`docs/constitution.md` Art. V.1](constitution.md#artículo-v--integridad-del-modelo-lingüístico)
- **Impacto multiidioma**: Concepto independiente del idioma. La forma textual conserva la codificación original del texto fuente.

---

### Lema

- **Categoría**: entidad
- **Definición**: Forma canónica que agrupa las formas flexionadas de la misma palabra; es la forma de búsqueda en un diccionario (por ejemplo, "correr" agrupa "corro", "corrí", "corriendo").
- **Referencias**: [`AGENTS.md §4`](../AGENTS.md#4-restricciones-del-dominio); [`docs/constitution.md` Art. V.1, V.4](constitution.md#artículo-v--integridad-del-modelo-lingüístico); [`docs/adr/0006-pos-per-occurrence.md`](adr/0006-pos-per-occurrence.md)
- **Impacto multiidioma**: Los modelos de lematización son específicos del idioma. El concepto de lema es universal; su cómputo depende del adaptador NLP activo para cada idioma.

---

### Phrasal verb (instancia inglesa)

- **Categoría**: entidad (instancia)
- **Definición**: Instancia inglesa de la expresión multipalabra específica del idioma: verbo compuesto por un verbo base y una o más partículas cuyo significado conjunto es distinto del significado literal de sus componentes (por ejemplo, "give up", "look into"). Véase también: [Expresión multipalabra específica del idioma](#expresión-multipalabra-específica-del-idioma).
- **Referencias**: [`AGENTS.md §4`](../AGENTS.md#4-restricciones-del-dominio); [`docs/constitution.md` Art. V.6](constitution.md#artículo-v--integridad-del-modelo-lingüístico); [`docs/adr/0009-mwe-language-specific-instances.md`](adr/0009-mwe-language-specific-instances.md)
- **Impacto multiidioma**: Instancia específica del inglés. En el modelo de dominio corresponde a `mwe_kind: "phrasal_verb"`. Es la instancia inglesa de la categoría abstracta "expresión multipalabra específica del idioma".

---

### Procedencia

- **Categoría**: atributo
- **Definición**: Metadatos que registran la fuente, la versión del modelo, la fecha de procesamiento y la puntuación de confianza de un resultado automático, de modo que pueda auditarse o compararse con una corrección manual posterior.
- **Referencias**: [`AGENTS.md §4`](../AGENTS.md#4-restricciones-del-dominio) — "Los resultados automáticos deben guardar su procedencia."; [`docs/constitution.md` Art. V.7](constitution.md#artículo-v--integridad-del-modelo-lingüístico); [`docs/adr/0007-manual-corrections-precedence.md`](adr/0007-manual-corrections-precedence.md)
- **Impacto multiidioma**: Concepto independiente del idioma.

---

### Puntuación de confianza

- **Categoría**: atributo
- **Definición**: Valor numérico que expresa el grado de certeza del pipeline NLP sobre un resultado automático concreto; permite priorizar la revisión manual de los resultados más inciertos.
- **Referencias**: [`AGENTS.md §4`](../AGENTS.md#4-restricciones-del-dominio) — "Cuando exista incertidumbre, se debe guardar una puntuación o nivel de confianza."; [`docs/constitution.md` Art. V.7](constitution.md#artículo-v--integridad-del-modelo-lingüístico)
- **Impacto multiidioma**: Concepto independiente del idioma.

---

### Reprocesamiento

- **Categoría**: proceso
- **Definición**: Re-ejecución del pipeline NLP sobre un corpus ya procesado; DEBE preservar todas las correcciones manuales existentes y NO DEBE sobrescribir silenciosamente ningún campo que tenga una corrección manual asociada.
- **Referencias**: [`AGENTS.md §4`](../AGENTS.md#4-restricciones-del-dominio) — "El reprocesamiento nunca debe sobrescribir silenciosamente una corrección manual."; [`docs/constitution.md` Art. V.9](constitution.md#artículo-v--integridad-del-modelo-lingüístico); [`docs/adr/0007-manual-corrections-precedence.md`](adr/0007-manual-corrections-precedence.md)
- **Impacto multiidioma**: Concepto independiente del idioma.

---

### Token

- **Categoría**: concepto
- **Definición**: Unidad léxica mínima extraída durante la tokenización, antes de cualquier normalización; el punto de entrada de cada palabra o signo al pipeline de análisis lingüístico.
- **Referencias**: [`AGENTS.md §4`](../AGENTS.md#4-restricciones-del-dominio); [`docs/constitution.md` Art. V.1](constitution.md#artículo-v--integridad-del-modelo-lingüístico)
- **Impacto multiidioma**: Concepto independiente del idioma. Las reglas de segmentación (tokenización) varían por idioma y modelo NLP: el inglés separa por espacios y puntuación estándar, el alemán por palabras compuestas, el chino o japonés por carácter o sílaba morfológica.

# Constitución del proyecto Wheel Vocabulary

**Versión:** 1.0.0  
**Estado:** Aprobada para el inicio del proyecto  
**Ámbito:** Todo el repositorio, todas las features y todos los colaboradores

## Preámbulo

Wheel Vocabulary es una aplicación web destinada a extraer, clasificar, consultar y estudiar vocabulario inglés procedente de obras literarias aportadas legalmente por el usuario.

La constitución define principios no negociables. Las especificaciones pueden evolucionar, pero ninguna feature puede contradecir estas reglas sin una enmienda explícita.

## Artículo I — Desarrollo dirigido por especificaciones

1. Toda feature debe disponer de una especificación antes de su implementación.
2. Los requisitos deben estar numerados y ser verificables.
3. Las decisiones técnicas no deben confundirse con requisitos de producto.
4. Las ambigüedades deben resolverse en la especificación, no ocultarse en el código.
5. Las modificaciones deben actualizar especificación, aceptación, pruebas, tareas y trazabilidad.

## Artículo II — Desarrollo dirigido por pruebas

1. Cada comportamiento nuevo debe comenzar con una prueba que falle.
2. La prueba debe fallar por la ausencia del comportamiento.
3. La implementación inicial será la mínima suficiente.
4. La refactorización se realiza con la suite relevante en verde.
5. Todo defecto corregido incorpora una prueba de regresión.
6. La cobertura es una señal, no un sustituto de pruebas significativas.

Objetivos iniciales:

```text
Dominio y aplicación: 90 % o superior
Cobertura global:     80 % o superior
```

## Artículo III — Cortes verticales y valor observable

1. Las features se entregarán en cortes verticales pequeños.
2. Cada corte debe producir un resultado observable o verificable.
3. Se evitarán fases horizontales largas sin valor integrado.
4. Cada corte atravesará únicamente las capas necesarias.

## Artículo IV — Legalidad, privacidad y derechos de autor

1. Ningún libro protegido se incluirá en el repositorio.
2. Las pruebas utilizarán textos sintéticos, propios o de dominio público.
3. El usuario aportará legalmente los archivos analizados.
4. El procesamiento local será la opción predeterminada.
5. El contenido completo de una obra no se enviará a terceros sin consentimiento explícito.
6. Las exportaciones no incluirán fragmentos extensos protegidos.
7. Los ejemplos de tarjetas se generarán preferentemente de forma original.
8. La aplicación permitirá eliminar los datos importados.

## Artículo V — Integridad del modelo lingüístico

1. Se distinguirán token, forma textual, forma normalizada, lema, aparición y categoría contextual.
2. Un lema puede tener múltiples categorías gramaticales.
3. La categoría se registra por aparición y se agrega posteriormente.
4. Las formas flexionadas se conservan al agrupar por lema.
5. Los nombres propios y términos ficticios se modelan separadamente.
6. Los phrasal verbs se modelan como expresiones multipalabra.
7. Los resultados automáticos guardan fuente, versión, fecha y confianza cuando proceda.
8. Una corrección manual prevalece sobre el resultado automático.
9. El reprocesamiento no borra silenciosamente correcciones manuales.

## Artículo VI — Reproducibilidad

1. Cada ejecución registra versiones de aplicación, modelos, reglas y esquema.
2. El mismo archivo, configuración y versión producen resultados equivalentes.
3. Los archivos se identifican mediante hash criptográfico.
4. Las migraciones están versionadas.
5. Los tests no dependen de servicios no controlados.

## Artículo VII — Arquitectura

1. El dominio no depende de frameworks.
2. Los casos de uso residen en aplicación.
3. Persistencia, NLP, importación y exportación son adaptadores.
4. La API HTTP no contiene reglas de negocio.
5. El frontend no duplica reglas lingüísticas.
6. Se evitará la abstracción especulativa.
7. Se favorecerán funciones puras para transformaciones.

## Artículo VIII — Calidad del código

1. Python y TypeScript utilizarán tipado estricto.
2. El proyecto dispone de formateador, linter, comprobador de tipos, pruebas y CI.
3. Las excepciones no se ignoran.
4. Los errores de usuario son comprensibles.
5. No se aceptan secretos en el repositorio.

## Artículo IX — Accesibilidad y experiencia

1. La interfaz será navegable por teclado.
2. Los formularios tendrán etiquetas accesibles.
3. Carga, éxito y error serán perceptibles.
4. Las tablas no dependerán exclusivamente del color.
5. Las acciones destructivas pedirán confirmación o serán reversibles.
6. Las operaciones largas mostrarán progreso o estado.

## Artículo X — Observabilidad y fallos

1. Importación y análisis tendrán estados explícitos.
2. Los fallos registrarán contexto suficiente sin contenido sensible.
3. Se distinguirá error de usuario, formato, procesamiento e interno.
4. Los fallos parciales no dejarán datos inconsistentes.
5. Las operaciones reintentables serán idempotentes cuando sea razonable.

## Artículo XI — Definición de terminado

Una feature está terminada cuando cumple requisitos, pasa pruebas, lint y tipos, verifica migraciones, actualiza documentación y trazabilidad, revisa privacidad y copyright y no introduce deuda oculta.

## Artículo XII — Enmiendas

Toda enmienda documentará cambio, motivación, consecuencias, fecha y versión. Cambios incompatibles incrementan versión mayor; ampliaciones compatibles, versión menor; correcciones editoriales, parche.
